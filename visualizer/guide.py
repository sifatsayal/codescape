"""Generate AI-guided tour steps for the codebase visualization."""
import json
import os
from pathlib import Path


def generate_tour_steps(repo_path, graph_data):
    """
    Generate 5 tour steps from the top 5 most important (by PageRank) file nodes.
    Uses OpenAI gpt-4o-mini to produce titles and explanations. On failure returns
    a fallback list with generic titles.
    """
    nodes = graph_data.get("nodes") or []
    links = graph_data.get("links") or []

    file_nodes = [n for n in nodes if n.get("type") == "file"]
    file_nodes_sorted = sorted(
        file_nodes,
        key=lambda n: float(n.get("pagerank") or 0),
        reverse=True,
    )
    top5 = file_nodes_sorted[:5]
    if not top5:
        return []

    node_ids = []
    for n in top5:
        nid = n.get("id") or n.get("path") or ""
        if nid:
            node_ids.append(nid)

    repo = Path(repo_path).resolve()
    file_contents = []
    for nid in node_ids:
        rel_path = (nid or "").replace("\\", "/").strip()
        full_path = (repo / rel_path).resolve()
        content = ""
        try:
            if full_path.is_file():
                with open(full_path, encoding="utf-8", errors="ignore") as f:
                    content = f.read()
        except Exception:
            pass
        max_chars = 4000
        truncated = content[:max_chars] + ("..." if len(content) > max_chars else "")
        file_contents.append({"nodeId": rel_path, "content": truncated})

    all_paths = [n.get("id") or n.get("path") for n in file_nodes if (n.get("id") or n.get("path"))]
    repo_structure = "\n".join(sorted(set(all_paths))[:200])

    prompt = (
        "You are a senior developer giving a new teammate a quick tour of this codebase. "
        "Generate a 5-step guided tour. Return ONLY a valid JSON array with exactly 5 objects. "
        "Each object must have: nodeId (the file path), title (max 5 words), explanation (2-3 sentences).\n\n"
        "Rules for the explanation:\n"
        "- Write like you're talking to a person, not writing docs\n"
        "- Be specific about what the file actually does\n"
        "- Include one practical tip like 'if X breaks, start here' or 'don't touch this unless you understand Y first'\n"
        "- No filler phrases like 'this file serves as' or 'this module is responsible for'\n"
        "- Max 40 words per explanation\n\n"
        "Repo file list (sample):\n"
        f"{repo_structure}\n\n"
    )
    for fc in file_contents:
        prompt += f"--- File: {fc['nodeId']} ---\n{fc['content']}\n\n"

    prompt += "Return ONLY the JSON array, no markdown or extra text."

    api_key = os.environ.get("OPENAI_API_KEY")
    if api_key:
        try:
            import urllib.request
            req = urllib.request.Request(
                "https://api.openai.com/v1/chat/completions",
                data=json.dumps(
                    {
                        "model": "gpt-4o-mini",
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": 1500,
                    }
                ).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": "Bearer " + api_key,
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=45) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                choices = result.get("choices", [])
                if choices and choices[0].get("message", {}).get("content"):
                    raw = choices[0]["message"]["content"].strip()
                    raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
                    steps = json.loads(raw)
                    if isinstance(steps, list) and len(steps) >= 5:
                        valid = []
                        id_set = {nid for nid in node_ids}
                        for i, s in enumerate(steps[:5]):
                            if not isinstance(s, dict):
                                continue
                            node_id = (s.get("nodeId") or node_ids[i] if i < len(node_ids) else "").replace("\\", "/")
                            if node_id not in id_set and node_ids:
                                node_id = node_ids[i]
                            valid.append({
                                "nodeId": node_id,
                                "title": str(s.get("title") or ("Step " + str(i + 1)))[:60],
                                "explanation": str(s.get("explanation") or "Key file in the codebase.")[:500],
                            })
                        if len(valid) == 5:
                            return valid
        except Exception:
            pass

    fallback_titles = ["Entry Point", "Core Logic", "UI Layer", "Config", "Where to Start"]
    return [
        {
            "nodeId": node_ids[i],
            "title": fallback_titles[i] if i < len(fallback_titles) else "Step " + str(i + 1),
            "explanation": "An important file in this codebase. Explore the sidebar for details.",
        }
        for i in range(min(5, len(node_ids)))
    ]
