# Extension API Design

## File Navigation API

The extension provides seamless integration between the visualization and VS Code's file system.

### Message Protocol

The webview communicates with the extension via `postMessage`:

#### From Webview to Extension

```typescript
// Open file in editor
vscode.postMessage({
  command: 'openFile',
  path: 'src/components/Button.tsx'
});

// Reveal file in explorer
vscode.postMessage({
  command: 'revealFile',
  path: 'src/components/Button.tsx'
});
```

#### From Extension to Webview

```typescript
// Update visualization data
webview.postMessage({
  command: 'updateGraph',
  data: { nodes: [...], links: [...] }
});

// Highlight specific node
webview.postMessage({
  command: 'highlightNode',
  nodeId: 'src/components/Button.tsx'
});
```

## Python Bridge API

### Methods

#### `checkEnvironment(): Promise<{available: boolean, error?: string}>`
Checks if Python and visualizer package are available.

#### `analyzeRepository(repoPath: string, configPath?: string): Promise<GraphData>`
Analyzes repository and returns graph data as JSON.

#### `startServer(repoPath: string, configPath?: string, port?: number): Promise<{port: number, process: ChildProcess}>`
Starts Python visualizer server and returns port number.

#### `generateHTML(repoPath: string, outputPath: string, configPath?: string): Promise<string>`
Generates HTML file and returns path.

## Extension Commands

### `codebaseVisualizer.visualize`
Opens visualization in external browser.

**Implementation:**
1. Spawns Python server
2. Opens browser with visualization
3. Handles server lifecycle

### `codebaseVisualizer.visualizeInPanel`
Shows visualization in embedded webview panel.

**Implementation:**
1. Generates HTML file
2. Creates/reveals webview panel
3. Loads HTML with IDE integration scripts
4. Handles file navigation messages

## Configuration API

### Settings

```json
{
  "codebaseVisualizer.pythonPath": "python3",
  "codebaseVisualizer.autoOpen": true
}
```

### Workspace-specific Config

The extension respects `.visualizer.json` files in the workspace, same as the CLI tool.

## Future API Extensions

### Real-time Updates

```typescript
// Watch for file changes
const watcher = vscode.workspace.createFileSystemWatcher('**/*.{ts,tsx,js,jsx}');
watcher.onDidChange(() => {
  // Incrementally update graph
  updateVisualization();
});
```

### Code Lens Integration

```typescript
// Register code lens provider
vscode.languages.registerCodeLensProvider('typescript', {
  provideCodeLenses(document) {
    return [
      new vscode.CodeLens(range, {
        command: 'codebaseVisualizer.showDependencies',
        title: `Used by ${fanIn} files`
      })
    ];
  }
});
```

### Sidebar Tree View

```typescript
// Register tree data provider
vscode.window.registerTreeDataProvider('codebaseVisualizer.dependencies', {
  getChildren(element) {
    // Return dependency tree nodes
  }
});
```

## Error Handling

All Python bridge methods return promises that reject with descriptive errors:

```typescript
try {
  const data = await pythonBridge.analyzeRepository(repoPath);
} catch (error) {
  vscode.window.showErrorMessage(`Analysis failed: ${error.message}`);
}
```

## Performance Considerations

- Large codebases: Use incremental analysis
- Caching: Cache graph data per workspace
- Background processing: Run analysis in background thread
- Progress reporting: Show progress for long operations
