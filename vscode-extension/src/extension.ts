import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs';
import { PythonBridge } from './pythonBridge';
import { WebviewPanel } from './webviewPanel';

let pythonBridge: PythonBridge | null = null;
let webviewPanel: WebviewPanel | null = null;

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

    statusBarItem.text = '$(check) Visualization ready!';
    statusBarItem.show();

    // Open browser
    const url = `http://localhost:${port}/`;
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
