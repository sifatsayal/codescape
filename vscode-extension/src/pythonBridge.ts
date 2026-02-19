import { spawn, ChildProcess } from 'child_process';
import * as path from 'path';
import * as fs from 'fs';

export interface GraphData {
  nodes: any[];
  links: any[];
  rootName: string;
  hotspots: any[];
  maxDepth: number;
  maxMetrics: {
    fanIn: number;
    fanOut: number;
    pagerank: number;
  };
  stats: {
    totalFiles: number;
    totalFolders: number;
    codeFiles: number;
    totalLoc: number;
    totalDependencies: number;
  };
}

export interface PythonBridgeOptions {
  pythonPath: string;
  repoPath: string;
  configPath?: string;
}

export class PythonBridge {
  private pythonPath: string;
  private visualizerPath: string;
  /** Workspace root (parent of visualizer/) - use as cwd so "python -m visualizer" works */
  private workspaceRoot: string;

  constructor(pythonPath: string) {
    this.pythonPath = pythonPath;
    // Extension compiled output is in vscode-extension/out/; repo root is parent of vscode-extension
    const repoRoot = path.resolve(__dirname, '../..');
    this.visualizerPath = path.join(repoRoot, 'visualizer');
    this.workspaceRoot = repoRoot;
  }

  /**
   * Check if Python is available and visualizer can run.
   * If visualizerRepoPath is set, check that path has visualizer/. Else check pip-installed (python -m visualizer).
   */
  async checkEnvironment(visualizerRepoPath?: string): Promise<{ available: boolean; error?: string }> {
    return new Promise((resolve) => {
      const proc = spawn(this.pythonPath, ['--version']);
      let err = '';

      proc.stderr.on('data', (data) => { err += data.toString(); });
      proc.on('close', (code) => {
        if (code !== 0) {
          resolve({ available: false, error: `Python not found at ${this.pythonPath}. ${err}` });
          return;
        }

        if (visualizerRepoPath) {
          const initPath = path.join(visualizerRepoPath, 'visualizer', '__init__.py');
          if (!fs.existsSync(initPath)) {
            resolve({ available: false, error: `Visualizer not found at ${visualizerRepoPath}. Set the path to the folder that contains visualize_codebase.py and the visualizer/ folder.` });
            return;
          }
          resolve({ available: true });
          return;
        }

        // Check if visualizer is pip-installed
        const checkProc = spawn(this.pythonPath, ['-c', 'import visualizer'], { stdio: ['ignore', 'pipe', 'pipe'] });
        let checkErr = '';
        checkProc.stderr.on('data', (d) => { checkErr += d.toString(); });
        checkProc.on('close', (c) => {
          if (c !== 0) {
            resolve({
              available: false,
              error: "Visualizer not installed. Open the win26-Team22 folder and run: pip install -e .",
            });
            return;
          }
          resolve({ available: true });
        });
      });
    });
  }

  /**
   * Analyze repository and return graph data as JSON
   */
  async analyzeRepository(
    repoPath: string,
    configPath?: string,
    visualizerRepoPath?: string
  ): Promise<GraphData> {
    return new Promise((resolve, reject) => {
      const args = ['-m', 'visualizer', '--repo', repoPath, '--json'];
      if (configPath) {
        args.push('--config', configPath);
      }

      const cwd = visualizerRepoPath || this.workspaceRoot;

      const process = spawn(this.pythonPath, args, {
        cwd,
        stdio: ['ignore', 'pipe', 'pipe'],
      });

      let stdout = '';
      let stderr = '';
      let jsonStarted = false;
      let jsonBuffer = '';

      process.stdout.on('data', (data) => {
        const text = data.toString();
        stdout += text;
        
        // JSON output starts after progress messages
        // Look for opening brace to start capturing JSON
        if (!jsonStarted && text.includes('{')) {
          jsonStarted = true;
          const braceIndex = text.indexOf('{');
          jsonBuffer = text.substring(braceIndex);
        } else if (jsonStarted) {
          jsonBuffer += text;
        }
      });

      process.stderr.on('data', (data) => {
        stderr += data.toString();
      });

      process.on('close', (code) => {
        if (code !== 0) {
          reject(new Error(`Python process failed: ${stderr || stdout}`));
          return;
        }

        try {
          // Try to parse JSON from stdout
          // JSON might be mixed with progress messages, so try to extract it
          let jsonData: GraphData;
          
          if (jsonBuffer) {
            jsonData = JSON.parse(jsonBuffer);
          } else {
            // Fallback: try parsing entire stdout
            const jsonMatch = stdout.match(/\{[\s\S]*\}/);
            if (jsonMatch) {
              jsonData = JSON.parse(jsonMatch[0]);
            } else {
              throw new Error('No JSON found in output');
            }
          }
          
          resolve(jsonData);
        } catch (error: any) {
          reject(
            new Error(
              `Failed to parse JSON output: ${error.message}. Output: ${stdout.substring(0, 500)}`
            )
          );
        }
      });
    });
  }

  /**
   * Start Python visualizer server and return port.
   * repoPath = folder to visualize (current workspace). visualizerRepoPath = path to win26-Team22 if not pip-installed.
   */
  async startServer(
    repoPath: string,
    configPath?: string,
    port?: number,
    visualizerRepoPath?: string
  ): Promise<{ port: number; process: ChildProcess }> {
    return new Promise((resolve, reject) => {
      const args = ['-m', 'visualizer', '--repo', repoPath];
      if (port) {
        args.push('--port', port.toString());
      }
      if (configPath) {
        args.push('--config', configPath);
      }

      const cwd = visualizerRepoPath || repoPath;

      const process = spawn(this.pythonPath, args, {
        cwd,
        stdio: ['ignore', 'pipe', 'pipe'],
      });

      let stdout = '';
      let stderr = '';

      process.stdout.on('data', (data) => {
        stdout += data.toString();
        // Look for port number in output
        const portMatch = stdout.match(/Local URL:\s+http:\/\/localhost:(\d+)/);
        if (portMatch) {
          const detectedPort = parseInt(portMatch[1], 10);
          resolve({ port: detectedPort, process });
        }
      });

      process.stderr.on('data', (data) => {
        stderr += data.toString();
      });

      process.on('error', (error) => {
        reject(error);
      });

      // Timeout after 10 seconds
      setTimeout(() => {
        if (!stdout.includes('Local URL:')) {
          reject(new Error('Server startup timeout'));
        }
      }, 10000);
    });
  }

  /**
   * Generate HTML file and return path
   */
  async generateHTML(
    repoPath: string,
    outputPath: string,
    configPath?: string,
    visualizerRepoPath?: string
  ): Promise<string> {
    return new Promise((resolve, reject) => {
      const args = [
        '-m',
        'visualizer',
        '--repo',
        repoPath,
        '--output',
        outputPath,
        '--no-server',
      ];
      if (configPath) {
        args.push('--config', configPath);
      }

      const cwd = visualizerRepoPath || this.workspaceRoot;

      const process = spawn(this.pythonPath, args, {
        cwd,
        stdio: ['ignore', 'pipe', 'pipe'],
      });

      let stderr = '';

      process.stderr.on('data', (data) => {
        stderr += data.toString();
      });

      process.on('close', (code) => {
        if (code !== 0) {
          reject(new Error(`Failed to generate HTML: ${stderr}`));
          return;
        }

        if (fs.existsSync(outputPath)) {
          resolve(outputPath);
        } else {
          reject(new Error('HTML file was not created'));
        }
      });
    });
  }
}
