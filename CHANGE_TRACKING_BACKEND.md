# Change Tracking Backend — For Frontend / Cursor

This doc describes the **current backend process** for change tracking and rescan so frontend folks (or Cursor) can read it and understand how the extension, server, and data flow work. See also `CHANGE_TRACKING_PLAN.md` for design and payload shapes.

---

## Heads up

**The rescan flow (updating the graph and counts in the UI after Cmd+S) is not fully working and tested yet.** The side panel correctly receives and shows the list of changes and "Last Cmd+S", but the main visualization (graph nodes, folder counts, dependency links) may not reliably update after a rescan. Right now, adding and deleting folders and files works as expected. Imports / dependencies do not. Have not tested changing paths. Use this doc to integrate with the APIs and to debug or finish the rescan behavior.

---

## Overview

1. **Extension (VS Code)** records change events in the IDE and keeps a **pending list**.
2. On **save (Cmd+S)** the extension **POSTs** that list (and a timestamp) to the visualizer server.
3. The **Python server** stores the changes and timestamp, runs a **rescan** of the repo (same as initial load: files, folders, imports), and can return the new graph.
4. The **browser (visualizer UI)** can **GET** the stored changes and timestamp, and can **GET** a fresh graph (rescan) to update the visualization.

---

## 1. Recording (extension)

- **Where:** `vscode-extension/src/extension.ts`
- **Subscriptions:**
  - `onDidCreateFiles` → file/folder added (we distinguish folder via `knownFolders` / `fs.stat`).
  - `onDidDeleteFiles` → file/folder deleted.
  - `onDidRenameFiles` → file/folder path_changed / folder_path_changed (with optional `kind`: `'renamed'` | `'moved'`).
  - `onDidSaveTextDocument` → we record import diff (import_added / import_removed) using a per-file baseline; we do **not** send `file_body_edited` to the frontend (it’s filtered out before send).
- **State:**
  - `pendingChanges`: array of change events.
  - `previousImportsByFile`: last known import specifiers per file (for import diff on save).
  - `knownFolders`: paths we’ve seen as directories (for folder vs file on delete/rename).
  - `lastServerPort`: port of the visualizer server (set when “Visualize Codebase” runs; cleared when the server process exits).
  - `lastSendTimestamp`: time of last successful send (used for “Last Cmd+S” in the UI).

---

## 2. Send on save (extension → server)

- **Trigger:** Every save (e.g. Cmd+S) in the Extension Development Host.
- **Action:** Call `sendPendingChangesToVisualizer()`.
- **Request:**
  - **Method/URL:** `POST http://localhost:<lastServerPort>/api/rescan`
  - **Body (JSON):** `{ "changes": [ ... ], "lastSendTimestamp": <number> }`
  - `changes`: current pending list (includes `file_body_edited` so the visualizer can show changed files).
  - `lastSendTimestamp`: current time (ms).
- **If `lastServerPort` is null** (no visualizer running), the function no-ops and resolves.
- **On 200:** extension sets `lastSendTimestamp` and clears `pendingChanges`.
- **Implementation:** Node `http.request` (not `fetch`) for reliability in the extension host; 5s timeout.

---

## 3. Server APIs (Python visualizer)

- **Where:** `visualizer/server.py` (handler created in `create_handler`).
- **In-memory state:**
  - `last_changes`: list of change objects (last payload from POST /api/rescan).
  - `last_send_timestamp`: number from the last POST body (“Last Cmd+S”).
  - `initial_repo_path`: repo path the server was started with (e.g. by the extension or CLI).

### Endpoints

| Method   | Path                    | Purpose                                                                                                                                                                                        |
| -------- | ----------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **POST** | `/api/rescan`           | Accept `{ "changes", "lastSendTimestamp" }`, update `last_changes` and `last_send_timestamp`, run full rescan for `initial_repo_path`, return new graph JSON (or 400/500).                     |
| **GET**  | `/api/last_changes`     | Return `{ "lastSendTimestamp": <number\|null>, "changes": [ ... ] }` for the side panel.                                                                                                       |
| **GET**  | `/api/rescan`           | Run same full scan as initial load (files, folders, imports) for `initial_repo_path` and return graph JSON. 400 if no initial path. Used by the browser to refresh the graph after a new save. |
| **GET**  | `/api/initial_path`     | Return `{ "path": "<initial_repo_path>" }` or `{ "path": null }`. Lets the UI know the repo path when the page was opened without `?path=`.                                                    |
| **GET**  | `/api/load?path=<path>` | Run full scan for the given `path` and return graph JSON. Used by “Load repo” in the UI.                                                                                                       |

- **Rescan implementation:** Both POST /api/rescan and GET /api/rescan call `load_repo_callback(initial_repo_path)` (in CLI terms: `build_graph_data_for_path`), which: loads config, runs `RepoScanner`, gets files/folders, runs `extract_imports_from_files`, builds `DependencyGraph`, returns `graph.build()`. So it is the same pipeline as the initial open.

---

## 4. Change event shapes (for `changes` array)

Paths are workspace-relative. Optional `timestamp` (ms) can be on any event.

| type                  | Payload fields                | Notes                                                           |
| --------------------- | ----------------------------- | --------------------------------------------------------------- |
| `file_added`          | `path`                        |                                                                 |
| `file_deleted`        | `path`                        |                                                                 |
| `file_body_edited`    | `path`                        | File content saved (sent so visualizer can highlight the file). |
| `path_changed`        | `oldPath`, `newPath`, `kind`? | `kind`: `'renamed'` \| `'moved'`                                |
| `folder_added`        | `path`                        |                                                                 |
| `folder_deleted`      | `path`                        |                                                                 |
| `folder_path_changed` | `oldPath`, `newPath`, `kind`? |                                                                 |
| `import_added`        | `fromFile`, `toFile`          |                                                                 |
| `import_removed`      | `fromFile`, `toFile`          |                                                                 |

Example:

```json
{ "type": "folder_added", "path": "src/lib/TEST" }
{ "type": "import_added", "fromFile": "src/App.tsx", "toFile": "src/utils/helper.ts" }
```

---

## 5. Browser / frontend flow (current)

- **Open:** Extension opens the visualizer at `http://localhost:<port>/?path=<repoPath>` so the path input is pre-filled.
- **Recent changes:** UI polls **GET /api/last_changes** (e.g. every 3s), shows “Last Cmd+S” and the list of changes (e.g. “Recent changes (taralyn's step)”).
- **Refetch after save:** When the poll sees a **new** `lastSendTimestamp`, the UI:
  - Tries **GET /api/rescan** first (same path as startup, full scan).
  - If 200: use response as new graph and call `updateGraphData(data)`.
  - If 400: fall back to path input or GET /api/initial_path, then **GET /api/load?path=...** (loadRepo).
- **Note:** As noted at the top, this refetch/rescan path is not fully working and tested; the graph/counts may not update reliably even though the change list and timestamp do.

---

## 6. File locations (quick reference)

| What                                                                                           | Where                                                                                           |
| ---------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| Recording, pending list, send on save                                                          | `vscode-extension/src/extension.ts`                                                             |
| POST /api/rescan, GET /api/last_changes, GET /api/rescan, GET /api/initial_path, GET /api/load | `visualizer/server.py`                                                                          |
| Full scan (files, folders, imports)                                                            | `visualizer/cli.py` (`build_graph_data_for_path`), used by server as `load_repo_callback`       |
| Side panel “Recent changes” + refetch on timestamp change                                      | `visualizer/ui.py` (inline JS: `loadRecentChanges`, GET /api/rescan, then fallback to loadRepo) |
| Design and payload spec                                                                        | `CHANGE_TRACKING_PLAN.md`                                                                       |

---

## 7. For Cursor / frontend

- To understand **what the backend sends and stores**, read: **payload shapes** (section 4), **POST /api/rescan** and **GET /api/last_changes** (section 3).
- To **consume** the list: use **GET /api/last_changes**; display `lastSendTimestamp` and `changes` in your UI.
- To **refresh the graph** after a save: use **GET /api/rescan** (or fallback **GET /api/load?path=...** with path from input or **GET /api/initial_path**). Expect that **rescan-based graph refresh is not fully working/tested yet** and may need debugging or fixes on either server or frontend.
