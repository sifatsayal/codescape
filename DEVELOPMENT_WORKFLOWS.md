# Development Workflows: Visualizer UI vs Extension

Use this guide to decide **what kind of change** you’re making and **where to work** so you get a fast feedback loop in Cursor.

---

## Current development focus: browser popup

**For now, we are developing on the browser popup (external browser) channel**, not the embedded webview. When making extension or integration changes, focus on the flow that:

- Runs **Codebase Visualizer: Visualize Codebase** (opens visualization in your default browser)
- Uses `visualizeInBrowser()` in `extension.ts` and `startServer()` in `pythonBridge.ts`

The embedded panel (Visualize Codebase (Embedded) / `webviewPanel.ts` / `generateHTML()`) is out of scope for current development. Keep this in mind when adding features or fixing bugs.

---

## The two types of changes

### 1. **Visualizer UI changes**

**What it is:** Anything that changes how the **visualization itself** looks or behaves—the graph, styling, layout, interactions, or the HTML/JS/CSS that the user sees in the browser or embedded panel.

**Examples:**  
- Tweaking the graph (colors, fonts, node size, D3 layout)  
- Changing the header, stats, or controls  
- Adding or changing UI elements in the visualization  
- Fixing a bug in how the graph renders or responds to clicks  

**Where to work:**  
- **Repo location:** `visualizer/` (Python package at the **repo root**).  
- **Main file:** `visualizer/ui.py` (HTML/CSS/JS generation).  
- Also relevant: `visualizer/server.py`, `visualizer/graph.py`, and other modules under `visualizer/`.

**Fast feedback loop:**  
1. From the **repo root**, run: `python -m visualizer` or `python visualize_codebase.py`.  
2. Open the URL it prints in your browser.  
3. Edit files in `visualizer/` (e.g. `ui.py`).  
4. **Restart the Python process** (Ctrl+C, then run the command again).  
5. **Refresh the browser** to see changes.  
No need to reload the Cursor extension for Visualizer UI–only changes.

---

### 2. **Extension changes**

**What it is:** Anything that changes how the **VS Code / Cursor integration** works—commands, settings, how the extension talks to Python, or **registering actions that run from the IDE** (e.g. when the user saves a file or selects something in the sidebar).

**Current focus:** Extension work is centered on the **browser popup** flow (command **Visualize Codebase** → `visualizeInBrowser()` → `pythonBridge.startServer()`). The embedded webview flow is not in scope for now.

**Examples:**  
- Adding or changing a command or setting  
- **Registering IDE-triggered actions** (e.g. on save, on file or folder selection in the sidebar)  
- Changing how the extension finds or invokes Python (`pythonPath`, `visualizerRepoPath`, etc.)  
- Fixing a bug in the extension host side (TypeScript/Node) for the browser flow  

**Where to work:**  
- **Repo location:** `vscode-extension/` (the VS Code/Cursor extension).  
- **Main files for browser flow:** `vscode-extension/src/extension.ts` (especially `visualizeInBrowser()`), `vscode-extension/src/pythonBridge.ts` (`checkEnvironment()`, `startServer()`).  
- Also: `vscode-extension/package.json` (commands, settings, activation).  
- *Embedded flow (out of scope for now):* `webviewPanel.ts`, `generateHTML()` in `pythonBridge.ts`.

**Fast feedback loop:**  
1. Open the **`vscode-extension`** folder in Cursor (or have it as the active workspace).  
2. In a terminal: `cd vscode-extension && npm run watch` (leave it running).  
3. Press **F5** (or **Run → Start Debugging**) to launch the **Extension Development Host** window.  
4. In that second window, run **Codebase Visualizer: Visualize Codebase** (browser popup) to test.  
5. After changing extension code (TS/JS): in the **Extension Development Host** window, run **Developer: Reload Window** (`Cmd+Shift+P` / `Ctrl+Shift+P`).  
No need to repackage or reinstall the `.vsix` for day-to-day extension development.

---

## Quick decision guide

| If you’re changing…                         | Type            | Work in           |
|--------------------------------------------|-----------------|--------------------|
| Graph look, layout, colors, interactions   | Visualizer UI   | `visualizer/`      |
| Header, stats, controls in the viz         | Visualizer UI   | `visualizer/`      |
| Commands, settings, Python path, webview   | Extension       | `vscode-extension/` |
| IDE actions (on save, sidebar selection)   | Extension       | `vscode-extension/` |

---

## Summary

- **Visualizer UI** → Edit under `visualizer/`, run Python from repo root, restart process + refresh browser.  
- **Extension** → Edit under `vscode-extension/`, use `npm run watch` + F5, then **Developer: Reload Window** in the Extension Development Host to see changes.  
- **Channel focus** → Develop and test using the **browser popup** (Visualize Codebase), not the embedded panel.

Using the right workflow for the type of change keeps your feedback loop fast in Cursor.
