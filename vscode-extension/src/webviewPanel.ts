import * as vscode from 'vscode';
import * as path from 'path';

export class WebviewPanel {
  private panel: vscode.WebviewPanel | undefined;
  private context: vscode.ExtensionContext;

  constructor(context: vscode.ExtensionContext, repoPath: string) {
    this.context = context;
    this.createPanel(repoPath);
  }

  private createPanel(repoPath: string) {
    // Create webview panel
    this.panel = vscode.window.createWebviewPanel(
      'codebaseVisualizer',
      'Codebase Visualizer',
      vscode.ViewColumn.Beside,
      {
        enableScripts: true,
        retainContextWhenHidden: true,
        localResourceRoots: [
          vscode.Uri.file(path.join(this.context.extensionPath, 'media')),
        ],
      }
    );

    // Handle panel disposal
    this.panel.onDidDispose(
      () => {
        this.panel = undefined;
      },
      null,
      this.context.subscriptions
    );

    // Handle messages from webview
    this.panel.webview.onDidReceiveMessage(
      (message) => {
        switch (message.command) {
          case 'openFile':
            this.openFile(message.path);
            break;
          case 'revealFile':
            this.revealFile(message.path);
            break;
        }
      },
      null,
      this.context.subscriptions
    );
  }

  public setContent(htmlContent: string, repoPath: string) {
    if (!this.panel) {
      return;
    }

    // Inject IDE integration script into HTML
    const enhancedHTML = this.injectIDEScript(htmlContent, repoPath);

    this.panel.webview.html = enhancedHTML;
  }

  private injectIDEScript(htmlContent: string, repoPath: string): string {
    // Inject script before closing </body> tag
    const ideScript = `
      <script>
        (function() {
          const vscode = acquireVsCodeApi();
          const repoPath = ${JSON.stringify(repoPath)};
          
          // Override file navigation to open files in IDE
          const originalFocusFile = window.focusFile;
          if (typeof originalFocusFile === 'function') {
            window.focusFile = function(filePath) {
              // Send message to extension to open file
              vscode.postMessage({
                command: 'openFile',
                path: filePath
              });
            };
          }
          
          // Add click handler to file nodes
          document.addEventListener('click', function(e) {
            const node = e.target.closest('.node');
            if (node) {
              const nodeId = node.getAttribute('data-id');
              if (nodeId && nodeId.includes('.')) {
                // It's a file, not a folder
                e.preventDefault();
                vscode.postMessage({
                  command: 'openFile',
                  path: nodeId
                });
              }
            }
          });
          
          // Add right-click handler for reveal in explorer
          document.addEventListener('contextmenu', function(e) {
            const node = e.target.closest('.node');
            if (node) {
              const nodeId = node.getAttribute('data-id');
              if (nodeId) {
                e.preventDefault();
                vscode.postMessage({
                  command: 'revealFile',
                  path: nodeId
                });
              }
            }
          });
        })();
      </script>
    `;

    return htmlContent.replace('</body>', ideScript + '</body>');
  }

  private async openFile(filePath: string) {
    const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
    if (!workspaceFolder) {
      return;
    }

    const fullPath = path.join(workspaceFolder.uri.fsPath, filePath);
    const uri = vscode.Uri.file(fullPath);

    try {
      const document = await vscode.workspace.openTextDocument(uri);
      await vscode.window.showTextDocument(document);
    } catch (error) {
      vscode.window.showErrorMessage(`Could not open file: ${filePath}`);
    }
  }

  private async revealFile(filePath: string) {
    const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
    if (!workspaceFolder) {
      return;
    }

    const fullPath = path.join(workspaceFolder.uri.fsPath, filePath);
    const uri = vscode.Uri.file(fullPath);

    await vscode.commands.executeCommand('revealInExplorer', uri);
  }

  public reveal() {
    if (this.panel) {
      this.panel.reveal();
    }
  }

  public dispose() {
    if (this.panel) {
      this.panel.dispose();
    }
  }
}
