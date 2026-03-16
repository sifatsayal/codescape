# How to Run and Debug the Extension (Change Tracking / Visualizer)

This explains how to get the **Extension Development Host** and **Visualize Codebase** flow running so you can test the extension (including change tracking, rescan, side panel) from this branch. Assumes you're working from the same repo/branch (e.g. `taralyn-extension` or main with these changes).

---

## Prerequisites

- **Node/npm** (for the VS Code extension in `vscode-extension/`)
- **Python 3** (for the visualizer in `visualizer/`); `python3` on PATH or set `codebaseVisualizer.pythonPath` in settings
- **Repo open at root:** Open the **win26-Team22** folder (the repo root) in Cursor/VS Code, not only `vscode-extension`. The extension expects to find the visualizer at the repo root when not pip-installed (see `codebaseVisualizer.visualizerRepoPath`).

---

## 1. Make F5 work from the repo root (one-time)

To **Launch Extension** with **F5** while the **repo root** is your workspace (so the extension can spawn the visualizer from this repo):

1. Create a `.vscode` folder at the **repo root** (`win26-Team22/.vscode`) if it doesn’t exist.
2. Add or merge a **`launch.json`** with a "Launch Extension" config that uses the `vscode-extension` folder:

**Path:** `win26-Team22/.vscode/launch.json`

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Launch Extension",
      "type": "extensionHost",
      "request": "launch",
      "args": [
        "--extensionDevelopmentPath=${workspaceFolder}/vscode-extension"
      ]
    }
  ]
}
```

3. With the **repo root** as your workspace folder, **F5** (or **Run → Start Debugging**) will open a second window: the **Extension Development Host** with your extension loaded.

---

## 2. Daily debugging workflow

1. **Open the repo root**  
   Open **win26-Team22** in Cursor (File → Open Folder → select the repo root).

2. **Start the extension compiler**  
   In a terminal:
   ```bash
   cd vscode-extension && npm run watch
   ```
   Leave this running so TypeScript recompiles on save.

3. **Launch the Extension Development Host**  
   Press **F5** (or Run → Start Debugging). A **new window** opens; that’s where the extension runs.

4. **In the new window (Extension Development Host)**  
   - Open a **folder** (any project you want to visualize), e.g. File → Open Folder → your app.
   - Run **Codebase Visualizer: Visualize Codebase** (Command Palette: `Cmd+Shift+P` / `Ctrl+Shift+P` → “Visualize Codebase”).  
   - The visualizer starts (Python server) and opens in your **browser** (with `?path=...` in the URL).
   - To test **change tracking:** make edits (add/remove file, folder, or import), then **save (Cmd+S)**. The extension POSTs to the visualizer; the side panel in the browser should show “Last Cmd+S” and the change list (see `CHANGE_TRACKING_BACKEND.md`).

5. **After changing extension code (TS/JS)**  
   In the **Extension Development Host** window: **Developer: Reload Window** (Command Palette). You don’t need to stop F5 or repackage the extension for normal iteration.

---

## 3. Optional: Visualizer repo path

If the visualizer isn’t pip-installed and the extension can’t find it, set the path in the **Extension Development Host**:

- **File → Preferences → Settings** (or open settings JSON).
- Find **Codebase Visualizer: Visualizer Repo Path** (`codebaseVisualizer.visualizerRepoPath`).
- Set it to the **absolute path** to the win26-Team22 repo (e.g. `C:\...\win26-Team22` or `/Users/.../win26-Team22`).

Then reload the Extension Development Host window and try **Visualize Codebase** again.

---

## 4. More detail

- **Extension vs visualizer UI:** See **`DEVELOPMENT_WORKFLOWS.md`** for when to work in `vscode-extension/` vs `visualizer/`, and the browser-popup vs embedded flow.
- **Change tracking APIs and rescan:** See **`CHANGE_TRACKING_BACKEND.md`** for how recording, send-on-save, and server APIs work (and that rescan isn’t fully working/tested yet).

---

## Quick checklist

- [ ] Repo root (win26-Team22) open in Cursor  
- [ ] `.vscode/launch.json` with "Launch Extension" (see above)  
- [ ] `cd vscode-extension && npm run watch` running  
- [ ] F5 → new window (Extension Development Host)  
- [ ] In new window: open a folder → **Visualize Codebase** → test changes + Cmd+S in browser side panel  
