# Change Tracking & Rescan: Plan and Next Steps

This doc captures the design decisions and implementation plan for: (1) recording user changes in the IDE, (2) sending them to the visualizer, and (3) rescannning the codebase and surfacing what changed.

---

## Goal (recap)

When the user makes changes in the IDE (edit file, move/rename, add/delete file, add/remove imports, etc.):

1. **Visualizer** rescans the codebase and updates the graph.
2. **User** is aware of what changed (signals/record of changes), eventually visible in a side panel (exact UX TBD later).

---

## Design decisions so far

### 1. Types of changes we want to record

We record these (implement in order: file → folder → dependency):

| Category   | Change types |
|-----------|---------------|
| **File**   | added, deleted, edited, renamed/moved (path changed) |
| **Folder** | added, deleted, renamed/moved |
| **Dependency** | import added, import removed |

### 2. Change recording scheme (hybrid)

- **Format:** Each change is an **event** with:
  - **Envelope (shared by all):** `type` (required), optional `timestamp` (and later workspace/session if needed).
  - **Payload (type-specific):** different fields depending on `type`; see below.
- **Rule:** One event per logical change; every event has the same envelope; payload shape varies by `type`.

#### Payload shapes (all change types)

Paths are relative to the workspace root unless we decide otherwise later.

**Envelope (every event):**

| Field       | Type   | Required | Description                |
|------------|--------|----------|----------------------------|
| `type`     | string | yes      | One of the values below.   |
| `timestamp`| number | no       | Unix time in milliseconds. |

**File events:**

| type             | Payload fields   | Description                    |
|------------------|------------------|--------------------------------|
| `file_added`     | `path`           | New file path.                 |
| `file_deleted`   | `path`           | Deleted file path.             |
| `file_body_edited` | `path` | File content was saved (body/code changed). Separate from import_added/import_removed. |
| `path_changed`   | `oldPath`, `newPath`, `kind`? | File renamed or moved. `kind`: `"renamed"` (same folder) or `"moved"` (different folder) for user understanding. |

**Folder events:**

| type                  | Payload fields   | Description                    |
|-----------------------|------------------|--------------------------------|
| `folder_added`        | `path`           | New folder path.               |
| `folder_deleted`      | `path`           | Deleted folder path.           |
| `folder_path_changed` | `oldPath`, `newPath`, `kind`? | Folder renamed or moved. `kind`: `"renamed"` or `"moved"` (same as path_changed). |

**Dependency events:**

| type             | Payload fields   | Description                          |
|------------------|------------------|--------------------------------------|
| `import_added`   | `fromFile`, `toFile` | File `fromFile` now imports `toFile`. |
| `import_removed` | `fromFile`, `toFile` | File `fromFile` no longer imports `toFile`. |

**Example events (JSON):**

```json
{ "type": "file_added", "timestamp": 1708450000000, "path": "src/NewComponent.tsx" }
{ "type": "file_deleted", "timestamp": 1708450001000, "path": "src/legacy/old.ts" }
{ "type": "file_body_edited", "timestamp": 1708450002000, "path": "src/App.tsx" }
{ "type": "path_changed", "timestamp": 1708450003000, "oldPath": "src/Button.tsx", "newPath": "src/ui/Button.tsx", "kind": "moved" }
{ "type": "folder_added", "timestamp": 1708450004000, "path": "src/features" }
{ "type": "folder_deleted", "timestamp": 1708450005000, "path": "src/legacy" }
{ "type": "folder_path_changed", "timestamp": 1708450006000, "oldPath": "src/widgets", "newPath": "src/components/widgets", "kind": "moved" }
{ "type": "import_added", "timestamp": 1708450007000, "fromFile": "src/App.tsx", "toFile": "src/utils/helper.ts" }
{ "type": "import_removed", "timestamp": 1708450008000, "fromFile": "src/App.tsx", "toFile": "src/utils/old.ts" }
```

**Bundle:** A list of events. When we send on save, we send an array of these objects, e.g. `[{ "type": "file_body_edited", "path": "src/App.tsx" }, ...]`.

### 3. When we record (Option C — discrete IDE events)

We **record** when discrete things happen in the IDE, not on every keystroke:

- **File edited** → when the user **saves** the document (Cmd+S / Ctrl+S).
- **File created / deleted / renamed** → when the IDE reports those (we subscribe to VS Code’s file-system events).

We **leverage VS Code’s APIs** for listening; no custom file watchers needed. The extension will subscribe to:

- `vscode.workspace.onDidSaveTextDocument` → record a `file_edited` event.
- `vscode.workspace.onDidCreateFiles` → record `file_added` (and later folder if we distinguish).
- `vscode.workspace.onDidDeleteFiles` → record `file_deleted` (and later folder).
- `vscode.workspace.onDidRenameFiles` → record `path_changed` (rename/move).

So: **we are listening and watching via VS Code’s built-in events.**

### 4. When we send (Option D — bundle on trigger)

- We **accumulate** recorded events in a **pending change list** (in the extension).
- We **send** that list to the visualizer as a **bundle** when a **trigger** fires.
- **Trigger:** **Cmd+S (save)** — when the user saves, we send the current pending bundle (and trigger rescan). This is the natural “I’m done with this change” moment.

Flow:

1. User creates/renames/deletes files or saves an edit → we **record** one event per occurrence into the pending list.
2. User hits Cmd+S (or saves any document) → we **send** the pending list to the visualizer, then clear (or archive) the list and trigger a rescan.

(If the trigger is “on save,” we’ll define precisely: e.g. “on any `onDidSaveTextDocument`, send current pending list and rescan” — and whether we clear the list after send or keep a history for the side panel.)

---

## Implementation order (high level)

1. **Step 1: General plan and architecture** ✅ (this doc)
   - Change types ✅  
   - Recording scheme ✅  
   - When to record (Option C) ✅  
   - When to send (Option D, trigger = Cmd+S) ✅  

2. **Step 2: Rescan function** ✅
   - Implement in the **visualizer** (Python): a way to rescan the entire codebase and update the graph (e.g. same as current “run analysis” but callable/triggered when we receive a change bundle).
   - For now: just “rescan and update”; later we can add change-tracking/diffing for UX (highlight what changed, etc.).
   - **Implemented:** Server accepts `initial_repo_path` when started (CLI passes repo path). **POST /api/rescan** with optional body `{"changes": [...]}` rescans that repo, stores the change bundle in memory for later (e.g. side panel), and returns the new graph JSON. Extension will call this on save (Step 3).

3. **Step 3: Register and record changes (most basic form)**
   - **Extension:** Subscribe to VS Code events (save, create, delete, rename).
   - **Extension:** Maintain a pending change list; on each event, append one change record (envelope + payload).
   - **Extension:** On save (trigger), send the pending bundle to the visualizer (e.g. via Python bridge), then clear or archive the list.
   - **Visualizer:** Receive the bundle (and trigger rescan); optionally persist or expose “last received changes” for the side panel (even in a minimal, machine-readable form at first).

---

## Next steps (concrete)

1. **Lock payload shapes** ✅ — Hybrid scheme with shared envelope (`type`, optional `timestamp`) and type-specific payloads; all change types (file, folder, dependency) defined above.
2. **Step 2:** ✅ Rescan path — POST /api/rescan on running server; optional body with changes; returns new graph JSON. CLI passes initial_repo_path. Extension will POST bundle on save. (Previously: how does it get triggered from the extension? e.g. “extension sends bundle → Python receives → rescan → update graph”). Browser flow: server is already running; we need a way to tell it “rescan now” (e.g. HTTP endpoint or similar).
3. **Step 3:** In the extension: wire up VS Code listeners, pending list, and “on save → send bundle + rescan.”

---

## Open decisions (to resolve as we implement)

- After sending on save: **clear** pending list only, or **archive** somewhere so the side panel can show “what was sent last”?
- For “path_changed”: do we get both old and new paths from `onDidRenameFiles`? (Yes — VS Code’s event provides old and new URIs.)
- Rescan in browser flow: server is long-lived; we need an explicit “rescan” mechanism (e.g. POST to a small endpoint, or the extension starts a one-off Python call that tells the server to rescan — Done: POST /api/rescan.)

---

*Last updated: Step 2 (rescan) implemented — POST /api/rescan, initial_repo_path passed from CLI.*
