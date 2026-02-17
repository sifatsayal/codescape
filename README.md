# Codebase Visualizer

A repo-agnostic tool for visualizing codebase structure, dependencies, and architectural patterns. Generate interactive D3.js visualizations of any codebase.

## Features

- 🔍 **Repo-Agnostic** - Works with any codebase (TypeScript, JavaScript, Python, Go, and more)
- 📊 **Dependency Analysis** - Extracts and visualizes file-to-file import relationships
- 📈 **Metrics** - Computes fan-in, fan-out, and PageRank for architectural insights
- 🎨 **Interactive UI** - Explore codebase structure with zoom, pan, and node selection
- ⚙️ **Configurable** - Customize via `.visualizer.json` config files

## Requirements

- **Python 3.11+** (no other dependencies required - uses Python standard library)

## Installation

No installation needed! Just clone this repository:

```bash
git clone <this-repo>
cd codebase-visualizer
```

## Quick Start

### Visualize Any Repository

```bash
# Visualize a repository (starts local server)
python -m visualizer --repo /path/to/your/repo

# Generate HTML file (no server)
python -m visualizer --repo /path/to/your/repo --output visualization.html --no-server

# Use custom port
python -m visualizer --repo /path/to/your/repo --port 9000
```

### Examples

```bash
# Visualize current directory
python -m visualizer --repo .

# Visualize a cloned GitHub repo
python -m visualizer --repo ~/projects/some-repo

# Generate and save to specific location
python -m visualizer --repo ~/projects/my-app --output ~/visualizations/my-app.html --no-server
```

## Configuration

Create a `.visualizer.json` file in your target repository to customize behavior:

```json
{
  "codeExtensions": {
    ".ts": "TypeScript",
    ".js": "JavaScript",
    ".py": "Python"
  },
  "skipDirs": [
    "node_modules",
    ".git",
    "dist",
    "build"
  ],
  "sourceDirs": [
    "src",
    "lib",
    "app"
  ],
  "maxFiles": 2000,
  "maxDepth": 6,
  "pagerankDamping": 0.85,
  "pagerankIterations": 20
}
```

The visualizer will automatically detect and use `.visualizer.json` if present, otherwise uses sensible defaults.

## Usage

### CLI Options

```bash
python -m visualizer --repo <path> [options]

Options:
  --repo, -r PATH     Path to target repository (required)
  --config, -c PATH   Path to config file (optional, auto-detected)
  --output, -o PATH   Save HTML to file instead of starting server
  --port, -p NUM      Port for local server (default: auto-find)
  --no-server         Generate HTML file only, do not start server
```

### Workflow

1. **Choose a target repository** - Any local codebase you want to visualize
2. **Run the visualizer** - Point it at the repository path
3. **Explore** - Open the generated HTML or use the local server

The visualizer **never writes to the repository** by default - all output goes to:
- Explicit `--output` path, or
- Temporary location (if using server mode)

## Output

The visualizer generates a self-contained HTML file with:
- Interactive D3.js graph visualization
- File/folder structure explorer
- Dependency graph with metrics
- Hotspots panel (most depended-on files)
- Search and navigation

The HTML file can be:
- Opened directly in a browser
- Deployed to GitHub Pages, Vercel, Netlify, etc.
- Shared with others

## Architecture

```
visualizer/
├── config.py      # Configuration management
├── scanner.py     # Repository scanner
├── parser.py      # Import parsers (JS, Python, Go)
├── graph.py       # Dependency graph builder
├── cli.py         # CLI entry point
└── __main__.py    # Module entry point
```

## Examples

### Visualize OpenClaw Repository

```bash
git clone https://github.com/openclaw/openclaw.git /tmp/openclaw
python -m visualizer --repo /tmp/openclaw --output openclaw.html --no-server
```

### Visualize with Custom Config

```bash
# Create config file
cat > /tmp/my-repo/.visualizer.json << EOF
{
  "sourceDirs": ["src", "lib"],
  "maxFiles": 1000
}
EOF

# Visualize
python -m visualizer --repo /tmp/my-repo
```

## Troubleshooting

**Port already in use?**
- The visualizer auto-finds available ports (8000, 8001, etc.)
- Or specify: `--port 9000`

**Large repository?**
- Adjust `maxFiles` in config: `{"maxFiles": 5000}`

**Permission errors?**
- Ensure the repository path is readable: `ls -la /path/to/repo`

## License

MIT License - see [LICENSE](LICENSE) file

## Contributing

Contributions welcome! This is a standalone tool - feel free to:
- Add support for more languages
- Improve import resolution
- Enhance visualization features
- Fix bugs
