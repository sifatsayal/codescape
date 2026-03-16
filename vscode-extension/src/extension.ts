import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs';
import * as http from 'http';
import { PythonBridge } from './pythonBridge';
import { WebviewPanel } from './webviewPanel';

let pythonBridge: PythonBridge | null = null;
let webviewPanel: WebviewPanel | null = null;

/** Pending change events to send on next save (Cmd+S). See CHANGE_TRACKING_PLAN.md. */
const pendingChanges: ChangeEvent[] = [];
/** Port of the last-started visualizer server (browser flow); used to POST /api/rescan on save. */
let lastServerPort: number | null = null;
/** When we last sent the pending bundle (Cmd+S); shown in visualizer side panel. */
let lastSendTimestamp: number | null = null;

/** Change event envelope + payload (hybrid scheme). file_body_edited = content changed (separate from import_added/import_removed). */
type ChangeEvent =
  | { type: 'file_added'; path: string; timestamp?: number }
  | { type: 'file_deleted'; path: string; timestamp?: number }
  | { type: 'file_body_edited'; path: string; timestamp?: number }
  | { type: 'path_changed'; oldPath: string; newPath: string; timestamp?: number; kind?: 'renamed' | 'moved' }
  | { type: 'folder_added'; path: string; timestamp?: number }
  | { type: 'folder_deleted'; path: string; timestamp?: number }
  | { type: 'folder_path_changed'; oldPath: string; newPath: string; timestamp?: number; kind?: 'renamed' | 'moved' }
  | { type: 'import_added'; fromFile: string; toFile: string; timestamp?: number }
  | { type: 'import_removed'; fromFile: string; toFile: string; timestamp?: number };

/** Last known import specifiers per file (workspace-relative path -> set of specifier strings). Used to diff on save and emit import_added/import_removed. */
const previousImportsByFile = new Map<string, Set<string>>();
/** Workspace-relative paths we've seen as directories (create/rename). Used to emit folder_deleted vs file_deleted on delete. */
const knownFolders = new Set<string>();

/** Extract import/require specifiers from document text (JS/TS). Returns deduplicated list. */
function getImportSpecifiersFromText(text: string): string[] {
  const specifiers = new Set<string>();
  // from 'x' | from "x"; require('x'); import 'x'; export ... from 'x'
  const re = /(?:from\s+['"]([^'"]+)['"])|(?:require\s*\(\s*['"]([^'"]+)['"]\s*\))|(?:import\s+['"]([^'"]+)['"])/g;
  let m: RegExpExecArray | null;
  while ((m = re.exec(text)) !== null) {
    const spec = m[1] ?? m[2] ?? m[3];
    if (spec) specifiers.add(spec);
  }
  return Array.from(specifiers);
}

/** Returns workspace-relative path for uri (forward slashes), or null if not under a workspace folder. */
function getWorkspaceRelativePath(uri: vscode.Uri): string | null {
  const folder = vscode.workspace.getWorkspaceFolder(uri);
  if (!folder) return null;
  const rel = path.relative(folder.uri.fsPath, uri.fsPath);
  const normalized = (rel || '.').replace(/\\/g, '/');
  return normalized;
}

let hasShownVisualizerHintOnce = false;

/** POST pending changes to visualizer /api/rescan (triggers rescan); server stores for side panel. Uses Node http so it works reliably in the extension host. */
function sendPendingChangesToVisualizer(): Promise<void> {
  return new Promise((resolve) => {
    if (lastServerPort === null) {
      if (!hasShownVisualizerHintOnce && pendingChanges.length > 0) {
        hasShownVisualizerHintOnce = true;
        vscode.window.showInformationMessage(
          'To see changes in the Codebase Visualizer when you save, open it from the command palette: "Codebase Visualizer: Visualize Codebase".',
          { modal: false }
        );
      }
      resolve();
      return;
    }
    const sendTime = Date.now();
    const bundle = pendingChanges.slice();
    const body = JSON.stringify({ changes: bundle, lastSendTimestamp: sendTime });
    const req = http.request(
      {
        hostname: 'localhost',
        port: lastServerPort,
        path: '/api/rescan',
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Content-Length': Buffer.byteLength(body, 'utf-8'),
        },
      },
      (res) => {
        if (res.statusCode === 200) {
          lastSendTimestamp = sendTime;
          pendingChanges.length = 0;
        }
        res.resume();
        resolve();
      }
    );
    req.on('error', () => resolve());
    req.setTimeout(5000, () => {
      req.destroy();
      resolve();
    });
    req.write(body, 'utf-8');
    req.end();
  });
}

function getPythonPath(): string {
  const raw = vscode.workspace.getConfiguration('codebaseVisualizer').get<string>('pythonPath');
  return raw && raw.trim() ? raw.trim() : 'python3';
}

function getPythonBridge(): PythonBridge {
  if (!pythonBridge) {
    pythonBridge = new PythonBridge(getPythonPath());
  }
  return pythonBridge;
}

export function activate(context: vscode.ExtensionContext) {
  console.log('Codebase Visualizer extension is now active');

  // Register command: Visualize Codebase (External Browser)
  const visualizeCommand = vscode.commands.registerCommand(
    'codebaseVisualizer.visualize',
    async () => {
      await visualizeInBrowser(context);
    }
  );

  // Register command: Visualize Codebase (Embedded Panel)
  const visualizePanelCommand = vscode.commands.registerCommand(
    'codebaseVisualizer.visualizeEmbedded',
    async () => {
      await visualizeInPanel(context);
    }
  );

  context.subscriptions.push(visualizeCommand);
  context.subscriptions.push(visualizePanelCommand);

  // --- Change recording (file_added / file_deleted / file_body_edited / path_changed / import_*). Send on save is wired later. ---
  context.subscriptions.push(
    vscode.workspace.onDidCreateFiles(async (e) => {
      for (const uri of e.files) {
        const relPath = getWorkspaceRelativePath(uri);
        if (relPath === null) continue;
        const now = Date.now();
        try {
          const stat = await vscode.workspace.fs.stat(uri);
          if (stat.type === vscode.FileType.Directory) {
            knownFolders.add(relPath);
            pendingChanges.push({ type: 'folder_added', path: relPath, timestamp: now });
          } else {
            pendingChanges.push({ type: 'file_added', path: relPath, timestamp: now });
          }
        } catch {
          pendingChanges.push({ type: 'file_added', path: relPath, timestamp: now });
        }
      }
    })
  );
  context.subscriptions.push(
    vscode.workspace.onDidDeleteFiles((e) => {
      for (const uri of e.files) {
        const relPath = getWorkspaceRelativePath(uri);
        if (relPath === null) continue;
        const now = Date.now();
        if (knownFolders.has(relPath)) {
          for (const p of Array.from(knownFolders)) {
            if (p === relPath || p.startsWith(relPath + path.sep)) knownFolders.delete(p);
          }
          pendingChanges.push({ type: 'folder_deleted', path: relPath, timestamp: now });
        } else {
          previousImportsByFile.delete(relPath);
          pendingChanges.push({ type: 'file_deleted', path: relPath, timestamp: now });
        }
      }
    })
  );
  context.subscriptions.push(
    vscode.workspace.onDidRenameFiles(async (e) => {
      for (const { oldUri, newUri } of e.files) {
        const oldPath = getWorkspaceRelativePath(oldUri);
        const newPath = getWorkspaceRelativePath(newUri);
        if (oldPath === null || newPath === null) continue;
        const now = Date.now();
        const oldDir = path.dirname(oldPath);
        const newDir = path.dirname(newPath);
        const kind: 'renamed' | 'moved' = oldDir === newDir ? 'renamed' : 'moved';
        try {
          const stat = await vscode.workspace.fs.stat(newUri);
          if (stat.type === vscode.FileType.Directory) {
            knownFolders.delete(oldPath);
            knownFolders.add(newPath);
            const prefix = oldPath + path.sep;
            for (const p of Array.from(knownFolders)) {
              if (p.startsWith(prefix)) {
                knownFolders.delete(p);
                knownFolders.add(path.join(newPath, p.slice(prefix.length)));
              }
            }
            pendingChanges.push({
              type: 'folder_path_changed',
              oldPath,
              newPath,
              timestamp: now,
              kind,
            });
          } else {
            pendingChanges.push({
              type: 'path_changed',
              oldPath,
              newPath,
              timestamp: now,
              kind,
            });
            const prev = previousImportsByFile.get(oldPath);
            if (prev !== undefined) {
              previousImportsByFile.set(newPath, prev);
              previousImportsByFile.delete(oldPath);
            }
          }
        } catch {
          pendingChanges.push({
            type: 'path_changed',
            oldPath,
            newPath,
            timestamp: now,
            kind,
          });
          const prev = previousImportsByFile.get(oldPath);
          if (prev !== undefined) {
            previousImportsByFile.set(newPath, prev);
            previousImportsByFile.delete(oldPath);
          }
        }
      }
    })
  );
  context.subscriptions.push(
    vscode.workspace.onDidSaveTextDocument(async (doc) => {
      const relPath = getWorkspaceRelativePath(doc.uri);
      if (relPath === null) return;

      const now = Date.now();
      pendingChanges.push({ type: 'file_body_edited', path: relPath, timestamp: now });

      const currentSpecifiers = new Set(getImportSpecifiersFromText(doc.getText()));
      const hadPriorBaseline = previousImportsByFile.has(relPath);
      const previous = previousImportsByFile.get(relPath) ?? new Set<string>();

      // Only diff imports when we have a prior baseline (we've seen this file saved before in this session).
      // Otherwise we'd report all current imports as "added" on first save (e.g. after removing one).
      if (hadPriorBaseline) {
        for (const spec of currentSpecifiers) {
          if (!previous.has(spec)) {
            pendingChanges.push({ type: 'import_added', fromFile: relPath, toFile: spec, timestamp: now });
          }
        }
        for (const spec of previous) {
          if (!currentSpecifiers.has(spec)) {
            pendingChanges.push({ type: 'import_removed', fromFile: relPath, toFile: spec, timestamp: now });
          }
        }
      }
      previousImportsByFile.set(relPath, currentSpecifiers);
      await sendPendingChangesToVisualizer();
    })
  );
}

export function deactivate() {
  if (webviewPanel) {
    webviewPanel.dispose();
  }
}

/**
 * Phase 1: External Browser Approach
 * Spawns Python server and opens browser
 */
async function visualizeInBrowser(context: vscode.ExtensionContext) {
  const bridge = getPythonBridge();
  if (!bridge) {
    vscode.window.showErrorMessage('Python bridge not initialized');
    return;
  }

  // Get workspace folder
  const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
  if (!workspaceFolder) {
    vscode.window.showErrorMessage(
      'No workspace folder open. Please open a folder first.'
    );
    return;
  }

  const repoPath = workspaceFolder.uri.fsPath;
  const config = vscode.workspace.getConfiguration('codebaseVisualizer');
  const visualizerRepoPath = config.get<string>('visualizerRepoPath', '')?.trim() || undefined;

  // Check Python environment
  const statusBarItem = vscode.window.createStatusBarItem(
    vscode.StatusBarAlignment.Left,
    100
  );
  statusBarItem.text = '$(sync~spin) Checking Python environment...';
  statusBarItem.show();

  try {
    const envCheck = await bridge.checkEnvironment(visualizerRepoPath);
    if (!envCheck.available) {
      statusBarItem.dispose();
      vscode.window.showErrorMessage(
        `Python environment check failed: ${envCheck.error}`
      );
      return;
    }

    statusBarItem.text = '$(sync~spin) Starting visualizer server...';
    statusBarItem.show();

    // Start Python server (visualizes repoPath = current workspace folder)
    const { port, process } = await bridge.startServer(repoPath, undefined, undefined, visualizerRepoPath);
    lastServerPort = port;
    hasShownVisualizerHintOnce = false;

    statusBarItem.text = '$(check) Visualization ready!';
    statusBarItem.show();

    // Open browser with repo path so the page can refetch graph on rescan (path input is used for GET /api/load)
    const url = `http://localhost:${port}/?path=${encodeURIComponent(repoPath)}`;
    const autoOpen = vscode.workspace
      .getConfiguration('codebaseVisualizer')
      .get<boolean>('autoOpen', true);

    if (autoOpen) {
      vscode.env.openExternal(vscode.Uri.parse(url));
      vscode.window.showInformationMessage(
        `Codebase visualization opened at ${url}`
      );
    } else {
      vscode.window.showInformationMessage(
        `Visualization server running at ${url}. Click to open.`,
        'Open Browser'
      ).then((selection) => {
        if (selection === 'Open Browser') {
          vscode.env.openExternal(vscode.Uri.parse(url));
        }
      });
    }

    // Clean up status bar after 3 seconds
    setTimeout(() => {
      statusBarItem.dispose();
    }, 3000);

    // Handle process termination
    process.on('exit', () => {
      lastServerPort = null;
      vscode.window.showInformationMessage('Visualization server stopped');
    });
  } catch (error: any) {
    statusBarItem.dispose();
    vscode.window.showErrorMessage(
      `Failed to start visualizer: ${error.message}`
    );
  }
}

/**
 * Phase 2: Embedded Webview Panel Approach
 * Creates webview panel with embedded visualization
 */
async function visualizeInPanel(context: vscode.ExtensionContext) {
  const bridge = getPythonBridge();
  if (!bridge) {
    vscode.window.showErrorMessage('Python bridge not initialized');
    return;
  }

  const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
  if (!workspaceFolder) {
    vscode.window.showErrorMessage(
      'No workspace folder open. Please open a folder first.'
    );
    return;
  }

  const repoPath = workspaceFolder.uri.fsPath;
  const config = vscode.workspace.getConfiguration('codebaseVisualizer');
  const visualizerRepoPath = config.get<string>('visualizerRepoPath', '')?.trim() || undefined;

  try {
    // Check environment
    const envCheck = await bridge.checkEnvironment(visualizerRepoPath);
    if (!envCheck.available) {
      vscode.window.showErrorMessage(
        `Python environment check failed: ${envCheck.error}`
      );
      return;
    }

    // Generate HTML to temp file
    const tempDir = path.join(context.globalStorageUri.fsPath, 'visualizer');
    if (!fs.existsSync(tempDir)) {
      fs.mkdirSync(tempDir, { recursive: true });
    }
    const htmlPath = path.join(tempDir, 'visualization.html');

    vscode.window.withProgress(
      {
        location: vscode.ProgressLocation.Notification,
        title: 'Generating visualization...',
        cancellable: false,
      },
      async (progress) => {
        progress.report({ increment: 0, message: 'Analyzing codebase...' });

        await bridge.generateHTML(repoPath, htmlPath, undefined, visualizerRepoPath);

        progress.report({ increment: 50, message: 'Creating visualization...' });

        // Create or reveal webview panel
        if (!webviewPanel) {
          webviewPanel = new WebviewPanel(context, repoPath);
        } else {
          webviewPanel.reveal();
        }

        // Load HTML into webview
        const htmlContent = fs.readFileSync(htmlPath, 'utf-8');
        webviewPanel.setContent(htmlContent, repoPath);

        progress.report({ increment: 100, message: 'Complete!' });
      }
    );
  } catch (error: any) {
    vscode.window.showErrorMessage(
      `Failed to generate visualization: ${error.message}`
    );
  }
}
