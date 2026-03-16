"""HTTP server module for serving visualizations."""
import http.server
import json
import os
import platform
import subprocess
import socketserver
import socket
import time
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from visualizer.guide import generate_tour_steps


def _load_dotenv(file_path):
    """Load KEY=value lines from file_path into os.environ (no external deps)."""
    path = Path(file_path)
    if not path.is_file():
        return
    try:
        with open(path, encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, _, value = line.partition("=")
                    key = key.strip()
                    if key:
                        value = value.strip().strip("'\"")
                        os.environ.setdefault(key, value)
    except Exception:
        pass


def _git_status_paths(repo_path):
    """Run git status --porcelain in repo_path; return dict with modified, added, deleted, renamed (paths relative, forward slashes)."""
    repo_path = Path(repo_path).resolve()
    if not repo_path.is_dir():
        return {"modified": [], "added": [], "deleted": [], "renamed": []}
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=str(repo_path),
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            return {"modified": [], "added": [], "deleted": [], "renamed": []}
        modified, added, deleted, renamed = [], [], [], []
        for line in result.stdout.splitlines():
            line = line.strip()
            if len(line) < 4:
                continue
            xy = line[:2]
            rest = line[3:].strip().replace("\\", "/")
            if " -> " in rest:
                old, new = rest.split(" -> ", 1)
                renamed.append({"oldPath": old.strip(), "newPath": new.strip()})
                continue
            if "M" in xy:
                modified.append(rest)
            elif "A" in xy or xy == "??":
                added.append(rest)
            elif "D" in xy:
                deleted.append(rest)
            elif "R" in xy:
                continue
        return {"modified": modified, "added": added, "deleted": deleted, "renamed": renamed}
    except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
        return {"modified": [], "added": [], "deleted": [], "renamed": []}


def _git_diff_line_stats(repo_path):
    """Return (additions, deletions) for repo working tree vs HEAD, or (0, 0) on error."""
    repo_path = Path(repo_path).resolve()
    if not repo_path.is_dir():
        return (0, 0)
    try:
        result = subprocess.run(
            ["git", "diff", "HEAD", "--numstat"],
            cwd=str(repo_path),
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode != 0 or not result.stdout:
            return (0, 0)
        total_add = 0
        total_del = 0
        for line in result.stdout.strip().splitlines():
            parts = line.split(None, 2)
            if len(parts) >= 2:
                try:
                    add = int(parts[0]) if parts[0] != "-" else 0
                    total_add += add
                except ValueError:
                    pass
                try:
                    dele = int(parts[1]) if parts[1] != "-" else 0
                    total_del += dele
                except ValueError:
                    pass
        return (total_add, total_del)
    except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
        return (0, 0)


def _git_diff_for_path(repo_path, relative_path):
    """Return git diff (working tree vs HEAD) for one file, or None."""
    repo_path = Path(repo_path).resolve()
    if not repo_path.is_dir() or not relative_path:
        return None
    path = (relative_path or "").strip().replace("\\", "/")
    if not path:
        return None
    # If path is absolute, make it relative to repo so git diff works
    try:
        path_obj = Path(path)
        if path_obj.is_absolute() or (len(path) > 1 and path[1] == ":"):
            try:
                resolved = (repo_path / path).resolve() if not path_obj.is_absolute() else path_obj.resolve()
                path = str(resolved.relative_to(repo_path)).replace("\\", "/")
            except (ValueError, OSError):
                pass
        elif path.startswith("/"):
            path = path.lstrip("/")
    except Exception:
        pass
    try:
        result = subprocess.run(
            ["git", "diff", "HEAD", "--", path],
            cwd=str(repo_path),
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode == 0 and result.stdout:
            return result.stdout.strip()
        return None
    except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
        return None


def _openai_one_line_summary(prompt_text, api_key, max_chars=2000):
    """Send prompt to OpenAI and return one short sentence summary, or None on failure."""
    if not api_key or not prompt_text:
        return None
    try:
        import urllib.request
        truncated = prompt_text[:max_chars] + ("..." if len(prompt_text) > max_chars else "")
        req = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=json.dumps({
                "model": "gpt-4o-mini",
                "messages": [{
                    "role": "user",
                    "content": "In one short sentence (under 15 words), summarize what changed for a developer. Be specific and technical.\n\n" + truncated,
                }],
                "max_tokens": 60,
            }).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer " + api_key,
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            choices = result.get("choices", [])
            if choices and choices[0].get("message", {}).get("content"):
                return choices[0]["message"]["content"].strip()
    except Exception:
        pass
    return None


def _describe_file_change_with_ai(repo_path, relative_path, status):
    """Return a one-line description of the change to this file. Uses git diff + OpenAI when available."""
    path = (relative_path or "").replace("\\", "/").strip()
    if not path:
        return "Unknown file."
    status = (status or "M").upper()
    if status == "A":
        return "New file added."
    if status == "D":
        return "File deleted."
    if status == "R":
        return "File renamed or moved."
    diff = _git_diff_for_path(repo_path, path)
    if not diff:
        return "File modified."
    api_key = os.environ.get("OPENAI_API_KEY")
    if api_key:
        summary = _openai_one_line_summary(diff, api_key)
        if summary:
            return summary
    return "File modified."


def _summarize_file_with_ai(repo_path, relative_path):
    """Return a 2–3 sentence summary of what this file does and its role in the codebase."""
    path = (relative_path or "").replace("\\", "/").strip()
    if not path:
        return None
    repo = Path(repo_path).resolve()
    full_path = (repo / path).resolve()
    try:
        print(f"[summarize_file] repo={repo} relative={path} full={full_path}")
    except Exception:
        pass
    try:
        if not full_path.is_file():
            try:
                print(f"[summarize_file] Not a file: {full_path}")
            except Exception:
                pass
            return None
        with open(full_path, encoding="utf-8", errors="ignore") as f:
            content = f.read()
    except Exception:
        return None
    if not content:
        return None
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        try:
            print("[summarize_file] OPENAI_API_KEY not set")
        except Exception:
            pass
        return None
    try:
        import urllib.request
        max_chars = 6000
        truncated = content[:max_chars] + ("..." if len(content) > max_chars else "")
        prompt = (
            "In exactly one short sentence (plain English), state what this file does. "
            "Be direct and technical. No filler phrases like 'this file serves as' or 'this document provides'. "
            "One sentence only.\n\n"
            f"File path: {path}\n\n"
            f"File contents:\n{truncated}"
        )
        req = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=json.dumps(
                {
                    "model": "gpt-4o-mini",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 160,
                }
            ).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer " + api_key,
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=20) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            choices = result.get("choices", [])
            if choices and choices[0].get("message", {}).get("content"):
                return choices[0]["message"]["content"].strip()
    except Exception:
        return None


# Mode-specific prompts for /api/ai_file_mode (sidebar AI summary).
_AI_FILE_MODE_PROMPTS = {
    "overview": "In 2 sentences max, what does this file do? Be direct. No filler.",
    "how_it_works": "List 3-4 bullet points explaining how this file works internally. Each bullet max 10 words. No intros or conclusions.",
    "impact": "List the files that import this one and what breaks if it changes. Be specific. If no dependents, say so in one line.",
    "edit_safely": "List 3-5 specific things to watch out for before editing this file. Bullet points only. Max 8 words each.",
    "read_next": "List 3 files to read next with one line each explaining why. Format: filename — reason",
}


def _ai_file_mode(repo_path, relative_path, mode, inbound_paths, outbound_paths):
    """Return AI-generated text for the given file and mode. Uses gpt-4o-mini."""
    path = (relative_path or "").replace("\\", "/").strip()
    if not path or mode not in _AI_FILE_MODE_PROMPTS:
        return None
    repo = Path(repo_path).resolve()
    full_path = (repo / path).resolve()
    try:
        if not full_path.is_file():
            return None
        with open(full_path, encoding="utf-8", errors="ignore") as f:
            content = f.read()
    except Exception:
        return None
    if not content:
        return None
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return None
    prompt_template = _AI_FILE_MODE_PROMPTS[mode]
    inbound_str = ", ".join(inbound_paths[:50]) if inbound_paths else "(none)"
    outbound_str = ", ".join(outbound_paths[:50]) if outbound_paths else "(none)"
    max_chars = 12000
    truncated = content[:max_chars] + ("..." if len(content) > max_chars else "")
    prompt = (
        f"{prompt_template}\n\n"
        f"File path: {path}\n\n"
        f"Inbound dependencies (files that import this file): {inbound_str}\n"
        f"Outbound dependencies (files this file imports): {outbound_str}\n\n"
    )
    if mode in ("impact", "edit_safely", "read_next"):
        inbound_list = "\n".join(f"  - {p}" for p in inbound_paths[:50]) if inbound_paths else "  (none)"
        outbound_list = "\n".join(f"  - {p}" for p in outbound_paths[:50]) if outbound_paths else "  (none)"
        prompt += (
            f"Actual inbound files (use these names in your response):\n{inbound_list}\n\n"
            f"Actual outbound files (use these names in your response):\n{outbound_list}\n\n"
        )
    prompt += f"File contents:\n{truncated}"
    try:
        import urllib.request
        req = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=json.dumps(
                {
                    "model": "gpt-4o-mini",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 1024,
                }
            ).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer " + api_key,
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            choices = result.get("choices", [])
            if choices and choices[0].get("message", {}).get("content"):
                return choices[0]["message"]["content"].strip()
    except Exception:
        return None
    return None


def _guide_goal_recommend(repo_path, goal, node_ids):
    """Return 3 file recommendations for the given goal based on tour node contents. Uses gpt-4o-mini."""
    repo = Path(repo_path).resolve()
    file_contents = []
    for nid in (node_ids or [])[:10]:
        rel = (nid or "").replace("\\", "/").strip()
        if not rel:
            continue
        full = (repo / rel).resolve()
        try:
            if full.is_file():
                with open(full, encoding="utf-8", errors="ignore") as f:
                    content = f.read()
            else:
                content = ""
        except Exception:
            content = ""
        truncated = content[:4000] + ("..." if len(content) > 4000 else "")
        file_contents.append({"nodeId": rel, "content": truncated})
    if not file_contents:
        return []
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return []
    goal_lower = (goal or "").strip().lower()
    if goal_lower == "fix a bug":
        prompt = (
            "A developer wants to fix a bug but doesn't know where it is yet. Based on these key files, "
            "recommend the 3 files most likely to contain bugs or be fragile — files with high complexity, "
            "many dependencies, or tricky logic. Return ONLY a valid JSON array of 3 objects with: "
            "nodeId (file path, must be an existing path in this repo), reason (max 10 words, why this file is worth checking). No filler.\n\n"
        )
    else:
        prompt = (
            f"A developer wants to {goal} in this codebase. Based on these key files, "
            "recommend exactly 3 files to start with. Return ONLY a valid JSON array of 3 objects with: "
            "nodeId (file path, must be an existing path in this repo), reason (max 10 words, direct and specific). No filler.\n\n"
        )
    for fc in file_contents:
        prompt += f"--- File: {fc['nodeId']} ---\n{fc['content']}\n\n"
    prompt += "Return ONLY the JSON array, no markdown or extra text."
    try:
        import urllib.request
        req = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=json.dumps({
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 400,
            }).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer " + api_key,
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=25) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            choices = result.get("choices", [])
            if not choices or not choices[0].get("message", {}).get("content"):
                return []
            raw = choices[0]["message"]["content"].strip()
            raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            arr = json.loads(raw)
            if not isinstance(arr, list) or len(arr) < 3:
                return []
            out = []
            for i, obj in enumerate(arr[:3]):
                if not isinstance(obj, dict):
                    continue
                nid = (obj.get("nodeId") or "").replace("\\", "/").strip()
                reason = str(obj.get("reason") or "")[:80]
                if nid:
                    out.append({"nodeId": nid, "reason": reason})
            return out[:3]
    except Exception:
        return []


def _describe_change_rule_based(change):
    """Return a short human-readable description of a change event (rule-based, no LLM)."""
    if not change or not isinstance(change, dict):
        return "Unknown change."
    t = change.get("type", "")
    path = change.get("path", "")
    old_path = change.get("oldPath", "")
    new_path = change.get("newPath", "")
    from_file = change.get("fromFile", "")
    to_file = change.get("toFile", "")
    kind = change.get("kind", "")
    kind_suffix = f" ({kind})" if kind else ""
    if t == "file_added":
        return f"File added: {path}" if path else "File added."
    if t == "file_deleted":
        return f"File deleted: {path}" if path else "File deleted."
    if t == "file_body_edited":
        return f"File edited: {path}" if path else "File edited."
    if t == "path_changed":
        return f"File moved: {old_path} → {new_path}{kind_suffix}" if (old_path or new_path) else "File path changed."
    if t == "folder_added":
        return f"Folder added: {path}" if path else "Folder added."
    if t == "folder_deleted":
        return f"Folder deleted: {path}" if path else "Folder deleted."
    if t == "folder_path_changed":
        return f"Folder moved: {old_path} → {new_path}{kind_suffix}" if (old_path or new_path) else "Folder path changed."
    if t == "import_added":
        return f"Import added: {from_file} → {to_file}" if (from_file or to_file) else "Import added."
    if t == "import_removed":
        return f"Import removed: {from_file} → {to_file}" if (from_file or to_file) else "Import removed."
    return f"Change: {t}"


def _run_folder_picker():
    """Run the system folder picker; return the selected path or None if cancelled/unsupported."""
    system = platform.system()
    try:
        if system == "Darwin":
            # macOS: AppleScript choose folder
            result = subprocess.run(
                [
                    "osascript",
                    "-e",
                    'return POSIX path of (choose folder with prompt "Choose repository folder")',
                ],
                capture_output=True,
                text=True,
                timeout=120,
            )
            if result.returncode == 0 and result.stdout:
                return result.stdout.strip()
            return None
        if system == "Windows":
            # Windows: PowerShell folder browser
            script = """
Add-Type -AssemblyName System.Windows.Forms
$dialog = New-Object System.Windows.Forms.FolderBrowserDialog
$dialog.Description = "Choose repository folder"
$dialog.ShowDialog() | Out-Null
if ($dialog.SelectedPath) { $dialog.SelectedPath }
"""
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", script],
                capture_output=True,
                text=True,
                timeout=120,
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
            return None
        if system == "Linux":
            # Linux: zenity or kdialog
            for cmd, args in [
                ("zenity", ["zenity", "--file-selection", "--directory", "--title=Choose repository folder"]),
                ("kdialog", ["kdialog", "--getexistingdirectory", ".", "Choose repository folder"]),
            ]:
                try:
                    result = subprocess.run(
                        args,
                        capture_output=True,
                        text=True,
                        timeout=120,
                    )
                    if result.returncode == 0 and result.stdout:
                        return result.stdout.strip()
                    break
                except FileNotFoundError:
                    continue
            return None
        return None
    except (subprocess.TimeoutExpired, Exception):
        return None


def create_handler(html_content, load_repo_callback=None, initial_repo_path=None):
    """Create a custom HTTP handler class with the HTML content.
    If load_repo_callback is set, GET /api/load?path=... will call it and return JSON.
    If initial_repo_path is set, POST /api/rescan rescans that repo and returns new graph JSON (body optional: {"changes": [...]})."""
    # Store last received changes and timestamp for visualizer side panel
    last_changes = []
    last_send_timestamp = None  # from extension "Last Cmd+S"
    # History of Cmd+S batches: each entry is { "timestamp": ts, "changes": [...] }. Newest at end. Used so "Git working tree" shows previous changes (each keeping its description).
    change_batches = []
    _MAX_CHANGE_BATCHES = 50
    # Track the currently active repo path (updated by /api/load). Fall back to initial_repo_path.
    current_repo_path = initial_repo_path
    # Cache descriptions by (repo, path, batch_ts) so each Cmd+S batch's change keeps its own description. batch_ts None = latest.
    file_description_cache = {}
    description_cache_by_batch = {}

    class VisualizationHandler(http.server.SimpleHTTPRequestHandler):
        """Custom HTTP handler to serve the visualization HTML."""

        def do_GET(self):
            nonlocal current_repo_path
            parsed = urlparse(self.path)
            if parsed.path == '/api/browse':
                path = _run_folder_picker()
                if path:
                    self._send_json(200, {'path': path})
                else:
                    self._send_json(200, {'path': '', 'cancelled': True})
                return
            if parsed.path == '/api/last_changes':
                repo = current_repo_path or initial_repo_path
                def path_from_change(ch):
                    if not isinstance(ch, dict):
                        return None
                    return (ch.get('path') or ch.get('newPath') or ch.get('toFile') or ch.get('fromFile') or '').strip().replace('\\', '/').lstrip('/')
                def enrich_batch(b):
                    ts = b.get('timestamp')
                    out = []
                    for ch in b.get('changes', []):
                        c = dict(ch)
                        p = path_from_change(c)
                        if p and repo:
                            key = (repo, p, ts)
                            if key in description_cache_by_batch:
                                c['description'] = description_cache_by_batch[key]
                        out.append(c)
                    return {'timestamp': ts, 'changes': out}
                batches_for_client = [enrich_batch(b) for b in change_batches]
                line_add, line_del = _git_diff_line_stats(repo) if repo else (0, 0)
                self._send_json(200, {
                    'lastSendTimestamp': last_send_timestamp,
                    'changes': list(last_changes),
                    'batches': batches_for_client,
                    'linesAdded': line_add,
                    'linesDeleted': line_del,
                })
                return
            if parsed.path == '/api/initial_path':
                self._send_json(200, {'path': initial_repo_path} if initial_repo_path else {'path': None})
                return
            if parsed.path == '/api/git_status':
                repo = current_repo_path or initial_repo_path
                if not repo:
                    self._send_json(200, {'modified': [], 'added': [], 'deleted': [], 'renamed': []})
                    return
                self._send_json(200, _git_status_paths(repo))
                return
            if parsed.path == '/api/summarize_file':
                query = parse_qs(parsed.query)
                path_list = query.get('path')
                path = (path_list[0] if path_list else '').strip().replace('\\', '/')
                if not path:
                    self._send_json(400, {'error': 'Missing path parameter'})
                    return
                repo = current_repo_path or initial_repo_path
                if not repo:
                    self._send_json(400, {'error': 'No repo path (start visualizer with --repo)'})
                    return
                summary = _summarize_file_with_ai(repo, path)
                try:
                    full_path = (Path(repo).resolve() / path).resolve()
                    exists = full_path.is_file()
                    print(f"[summarize_file endpoint] path={path} full_path={full_path} exists={exists} summary={repr(summary)}")
                except Exception:
                    pass
                if not summary:
                    summary = 'No summary available.'
                self._send_json(200, {'summary': summary})
                return
            if parsed.path == '/api/ai_file_mode':
                query = parse_qs(parsed.query)
                path_list = query.get('path')
                path = (path_list[0] if path_list else '').strip().replace('\\', '/')
                mode_list = query.get('mode')
                mode = (mode_list[0] if mode_list else '').strip().lower()
                inbound_raw = (query.get('inbound') or [None])[0] or ''
                outbound_raw = (query.get('outbound') or [None])[0] or ''
                def split_paths(s):
                    return [p.strip() for p in str(s).replace(',', '|').split('|') if p.strip()]
                inbound_paths = split_paths(inbound_raw)
                outbound_paths = split_paths(outbound_raw)
                if not path or not mode:
                    self._send_json(400, {'error': 'Missing path or mode parameter'})
                    return
                if mode not in _AI_FILE_MODE_PROMPTS:
                    self._send_json(400, {'error': 'Invalid mode'})
                    return
                repo = current_repo_path or initial_repo_path
                if not repo:
                    self._send_json(400, {'error': 'No repo path (start visualizer with --repo)'})
                    return
                result_text = _ai_file_mode(repo, path, mode, inbound_paths, outbound_paths)
                if not result_text:
                    result_text = 'No summary available.'
                self._send_json(200, {'result': result_text})
                return
            if parsed.path == '/api/rescan':
                # Same as initial load: full scan (files, folders, imports) for the repo we started with
                if not initial_repo_path or load_repo_callback is None:
                    self._send_json(400, {'error': 'Rescan not available (no initial repo path)'})
                    return
                try:
                    graph_data = load_repo_callback(initial_repo_path)
                    if isinstance(graph_data, dict) and 'error' in graph_data:
                        self._send_json(400, graph_data)
                    else:
                        self._send_json(200, graph_data)
                except Exception as e:
                    self._send_json(500, {'error': str(e)})
                return
            if parsed.path == '/api/load' and load_repo_callback is not None:
                query = parse_qs(parsed.query)
                path_list = query.get('path')
                path = path_list[0].strip() if path_list else ''
                if not path:
                    self._send_json(400, {'error': 'Missing path parameter'})
                    return
                try:
                    data = load_repo_callback(path)
                    if isinstance(data, dict) and 'error' in data:
                        self._send_json(400, data)
                    else:
                        # Update the active repo path when a new repo is successfully loaded.
                        current_repo_path = path
                        self._send_json(200, data)
                except Exception as e:
                    self._send_json(500, {'error': str(e)})
                return
            if self.path == '/' or self.path == '/index.html':
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                content_bytes = html_content.encode('utf-8')
                self.send_header('Content-Length', str(len(content_bytes)))
                self.end_headers()
                self.wfile.write(content_bytes)
            else:
                self.send_response(404)
                self.end_headers()

        def do_POST(self):
            nonlocal last_send_timestamp
            nonlocal current_repo_path
            parsed = urlparse(self.path)
            if parsed.path == '/api/rescan':
                if not initial_repo_path or load_repo_callback is None:
                    self._send_json(400, {'error': 'Rescan not available (no initial repo path)'})
                    return
                # Optional body: {"changes": [...], "lastSendTimestamp": number}
                changes = []
                content_length = int(self.headers.get('Content-Length', 0) or 0)
                if content_length > 0:
                    try:
                        body = self.rfile.read(content_length).decode('utf-8')
                        data = json.loads(body) if body.strip() else {}
                        changes = data.get('changes', [])
                        ts = data.get('lastSendTimestamp')
                        if ts is not None:
                            last_send_timestamp = ts
                    except (json.JSONDecodeError, ValueError):
                        self._send_json(400, {'error': 'Invalid JSON body'})
                        return
                last_changes.clear()
                last_changes.extend(changes)
                if changes:
                    batch_ts = last_send_timestamp if last_send_timestamp is not None else time.time()
                    change_batches.append({'timestamp': batch_ts, 'changes': list(changes)})
                    if len(change_batches) > _MAX_CHANGE_BATCHES:
                        change_batches.pop(0)
                try:
                    graph_data = load_repo_callback(initial_repo_path)
                    if isinstance(graph_data, dict) and 'error' in graph_data:
                        self._send_json(400, graph_data)
                    else:
                        self._send_json(200, graph_data)
                except Exception as e:
                    self._send_json(500, {'error': str(e)})
                return
            if parsed.path == '/api/describe_change':
                content_length = int(self.headers.get('Content-Length', 0) or 0)
                if content_length <= 0:
                    self._send_json(400, {'error': 'Missing body'})
                    return
                try:
                    body = self.rfile.read(content_length).decode('utf-8')
                    data = json.loads(body) if body.strip() else {}
                    change = data.get('change')
                except (json.JSONDecodeError, ValueError) as e:
                    self._send_json(400, {'error': 'Invalid JSON: ' + str(e)})
                    return
                description = _describe_change_rule_based(change)
                if change and initial_repo_path:
                    t = change.get('type', '')
                    path = change.get('path') or change.get('newPath') or change.get('toFile')
                    if path:
                        path = path.strip().replace('\\', '/')
                        status = 'M'
                        if t in ('file_added', 'folder_added'):
                            status = 'A'
                        elif t in ('file_deleted', 'folder_deleted'):
                            status = 'D'
                        elif t in ('path_changed', 'folder_path_changed'):
                            status = 'R'
                        ai_desc = _describe_file_change_with_ai(initial_repo_path, path, status)
                        if ai_desc and ai_desc != 'File modified.':
                            description = ai_desc
                        if change_batches:
                            batch_ts = change_batches[-1]['timestamp']
                            description_cache_by_batch[(initial_repo_path, path, batch_ts)] = description
                self._send_json(200, {'description': description})
                return
            if parsed.path == '/api/describe_file_change':
                content_length = int(self.headers.get('Content-Length', 0) or 0)
                if content_length <= 0:
                    self._send_json(400, {'error': 'Missing body'})
                    return
                try:
                    body = self.rfile.read(content_length).decode('utf-8')
                    data = json.loads(body) if body.strip() else {}
                    path = (data.get('path') or '').strip().replace('\\', '/')
                    status = (data.get('status') or 'M').upper()
                except (json.JSONDecodeError, ValueError) as e:
                    self._send_json(400, {'error': 'Invalid JSON: ' + str(e)})
                    return
                if not path:
                    self._send_json(400, {'error': 'Missing path'})
                    return
                repo = current_repo_path or initial_repo_path
                if not repo:
                    self._send_json(400, {'error': 'No repo path (start visualizer with --repo)'})
                    return
                batch_ts = data.get('batchTimestamp')
                if batch_ts is None and change_batches:
                    batch_ts = change_batches[-1]['timestamp']
                cache_key = (repo, path, batch_ts) if batch_ts is not None else (repo, path, None)
                if cache_key in description_cache_by_batch:
                    self._send_json(200, {'description': description_cache_by_batch[cache_key]})
                    return
                if (repo, path) in file_description_cache and batch_ts is None:
                    self._send_json(200, {'description': file_description_cache[(repo, path)]})
                    return
                description = _describe_file_change_with_ai(repo, path, status)
                path_norm = (path or "").strip().replace("\\", "/").lstrip("/").lower()
                changes_to_search = last_changes if batch_ts is None and last_changes else []
                if not changes_to_search and batch_ts is not None:
                    for b in change_batches:
                        if b.get('timestamp') == batch_ts:
                            changes_to_search = b.get('changes', [])
                            break
                if changes_to_search and (description == "File modified." or "no diff" in description.lower()):
                    for ch in changes_to_search:
                        if not isinstance(ch, dict):
                            continue
                        for key in ("path", "newPath", "toFile", "fromFile", "oldPath"):
                            p = (ch.get(key) or "").strip().replace("\\", "/").lstrip("/").lower()
                            if not p:
                                continue
                            if p == path_norm or p.endswith("/" + path_norm) or path_norm.endswith("/" + p):
                                description = _describe_change_rule_based(ch)
                                break
                        else:
                            continue
                        break
                if "no diff" in description.lower():
                    description = "File modified."
                if batch_ts is not None:
                    description_cache_by_batch[(repo, path, batch_ts)] = description
                else:
                    file_description_cache[(repo, path)] = description
                self._send_json(200, {'description': description})
                return
            if parsed.path == '/api/generate_tour':
                content_length = int(self.headers.get('Content-Length', 0) or 0)
                if content_length <= 0:
                    self._send_json(400, {'error': 'Missing body'})
                    return
                try:
                    body = self.rfile.read(content_length).decode('utf-8')
                    data = json.loads(body) if body.strip() else {}
                    nodes = data.get('nodes', data.get('graphData', {}).get('nodes', []))
                    links = data.get('links', data.get('graphData', {}).get('links', []))
                except (json.JSONDecodeError, ValueError) as e:
                    self._send_json(400, {'error': 'Invalid JSON: ' + str(e)})
                    return
                repo = current_repo_path or initial_repo_path
                if not repo:
                    self._send_json(400, {'error': 'No repo path (start visualizer with --repo)'})
                    return
                try:
                    steps = generate_tour_steps(repo, {'nodes': nodes, 'links': links})
                    self._send_json(200, steps)
                except Exception as e:
                    self._send_json(500, {'error': str(e)})
                return
            if parsed.path == '/api/guide_goal':
                content_length = int(self.headers.get('Content-Length', 0) or 0)
                if content_length <= 0:
                    self._send_json(400, {'error': 'Missing body'})
                    return
                try:
                    body = self.rfile.read(content_length).decode('utf-8')
                    data = json.loads(body) if body.strip() else {}
                    goal = (data.get('goal') or '').strip()
                    node_ids = data.get('nodeIds') or data.get('node_ids') or []
                except (json.JSONDecodeError, ValueError) as e:
                    self._send_json(400, {'error': 'Invalid JSON: ' + str(e)})
                    return
                if not goal:
                    self._send_json(400, {'error': 'Missing goal'})
                    return
                repo = current_repo_path or initial_repo_path
                if not repo:
                    self._send_json(400, {'error': 'No repo path'})
                    return
                try:
                    recs = _guide_goal_recommend(repo, goal, node_ids)
                    self._send_json(200, recs)
                except Exception as e:
                    self._send_json(500, {'error': str(e)})
                return
            self.send_response(404)
            self.end_headers()

        def _send_json(self, status, data):
            body = json.dumps(data).encode('utf-8')
            self.send_response(status)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format, *args):
            # Suppress default logging
            pass

    return VisualizationHandler


def get_local_ip():
    """Get the local IP address for network access."""
    try:
        # Connect to a remote address to determine local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return None


def find_available_port(start=8000, max_tries=100):
    """Find an available port starting from start. Returns None if none found."""
    for i in range(max_tries):
        port = start + i
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("0.0.0.0", port))
                return port
        except OSError:
            continue
    return None


def start_server(html_content, port=8000, load_repo_callback=None, initial_repo_path=None):
    """Start a local web server to serve the visualization.
    If load_repo_callback(path_str) is provided, GET /api/load?path=... returns graph JSON for that repo.
    If initial_repo_path is set, POST /api/rescan rescans that repo and returns new graph JSON."""
    if initial_repo_path:
        repo = Path(initial_repo_path).resolve()
        _load_dotenv(repo / ".env.local")
        _load_dotenv(repo / ".env")
    _load_dotenv(Path.cwd() / ".env.local")
    _load_dotenv(Path.cwd() / ".env")
    handler_class = create_handler(
        html_content,
        load_repo_callback=load_repo_callback,
        initial_repo_path=str(initial_repo_path) if initial_repo_path else None,
    )
    # Allow reusing the port so restarts don't leave it in TIME_WAIT
    socketserver.TCPServer.allow_reuse_address = True

    # Bind to 0.0.0.0 to allow network access
    with socketserver.TCPServer(("0.0.0.0", port), handler_class) as httpd:
        local_ip = get_local_ip()
        print(f"🌐 Server running!")
        print(f"   Local:  http://localhost:{port}/")
        if local_ip:
            print(f"   Network: http://{local_ip}:{port}/")
            print(f"   Share this link with others on your network!")
        print(f"   Press Ctrl+C to stop the server")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Server stopped.")
