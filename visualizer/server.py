"""HTTP server module for serving visualizations."""
import http.server
import json
import os
import platform
import subprocess
import socketserver
import socket
from pathlib import Path
from urllib.parse import parse_qs, urlparse


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


def _git_diff_for_path(repo_path, relative_path):
    """Return git diff (working tree vs HEAD) for one file, or None."""
    repo_path = Path(repo_path).resolve()
    if not repo_path.is_dir() or not relative_path:
        return None
    try:
        result = subprocess.run(
            ["git", "diff", "HEAD", "--", relative_path],
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
        return "File modified (no diff available)."
    api_key = os.environ.get("OPENAI_API_KEY")
    if api_key:
        summary = _openai_one_line_summary(diff, api_key)
        if summary:
            return summary
    return "File modified."


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

    class VisualizationHandler(http.server.SimpleHTTPRequestHandler):
        """Custom HTTP handler to serve the visualization HTML."""

        def do_GET(self):
            parsed = urlparse(self.path)
            if parsed.path == '/api/browse':
                path = _run_folder_picker()
                if path:
                    self._send_json(200, {'path': path})
                else:
                    self._send_json(200, {'path': '', 'cancelled': True})
                return
            if parsed.path == '/api/last_changes':
                self._send_json(200, {
                    'lastSendTimestamp': last_send_timestamp,
                    'changes': list(last_changes),
                })
                return
            if parsed.path == '/api/initial_path':
                self._send_json(200, {'path': initial_repo_path} if initial_repo_path else {'path': None})
                return
            if parsed.path == '/api/git_status':
                repo = initial_repo_path
                if not repo:
                    self._send_json(200, {'modified': [], 'added': [], 'deleted': [], 'renamed': []})
                    return
                self._send_json(200, _git_status_paths(repo))
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
                repo = initial_repo_path
                if not repo:
                    self._send_json(400, {'error': 'No repo path (start visualizer with --repo)'})
                    return
                description = _describe_file_change_with_ai(repo, path, status)
                self._send_json(200, {'description': description})
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


def find_available_port(start=8000, max_tries=20):
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
