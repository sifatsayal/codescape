# How to Test the Visualizer on Any Codebase

## ✅ Quick Test (Current Repo)

```bash
# Test on the current Supabase repo
python -m visualizer --repo .

# Or generate HTML file
python -m visualizer --repo . --output my-visualization.html --no-server
```

## 🧪 Test on Any Other Repository

### Option 1: Test on Another Local Repo

```bash
# Point at any repository on your machine
python -m visualizer --repo /path/to/any/repo

# Example: Test on a Node.js project
python -m visualizer --repo ~/projects/my-nodejs-app

# Example: Test on a Python project  
python -m visualizer --repo ~/projects/my-python-app
```

### Option 2: Test on a Cloned GitHub Repo

```bash
# Clone any repo
git clone https://github.com/user/repo.git /tmp/test-repo

# Visualize it
python -m visualizer --repo /tmp/test-repo --output test-output.html --no-server

# Open the HTML file in your browser
open test-output.html  # macOS
# or
xdg-open test-output.html  # Linux
```

### Option 3: Test with Custom Config

Create a `.visualizer.json` file in the repo you want to test:

```json
{
  "codeExtensions": {
    ".ts": "TypeScript",
    ".js": "JavaScript",
    ".py": "Python"
  },
  "skipDirs": ["node_modules", ".git", "dist"],
  "sourceDirs": ["src", "lib", "app"],
  "maxFiles": 2000,
  "maxDepth": 6
}
```

Then run:
```bash
python -m visualizer --repo /path/to/repo
# It will automatically find and use .visualizer.json
```

## 📋 Test Commands Reference

```bash
# Basic usage
python -m visualizer --repo <path>

# Generate HTML file (no server)
python -m visualizer --repo <path> --output output.html --no-server

# Use specific port
python -m visualizer --repo <path> --port 9000

# Use custom config file
python -m visualizer --repo <path> --config /path/to/config.json
```

## ✅ Verification

After running, you should see:
- ✅ Scanning messages
- ✅ Import extraction progress
- ✅ Metrics computation
- ✅ HTML file generated (if using --output)
- ✅ Server started on localhost (if not using --no-server)

Then open the visualization in your browser!

## 🐛 Troubleshooting

**Port already in use?**
- The visualizer auto-finds available ports (8000, 8001, etc.)
- Or specify: `--port 9000`

**Large repo taking too long?**
- Adjust `maxFiles` in config: `{"maxFiles": 1000}`

**Permission errors?**
- Make sure the repo path is readable: `ls -la /path/to/repo`

## 🎯 Next Steps

1. **Test on a small repo** - Verify basic functionality
2. **Test on a medium repo** - Check performance  
3. **Test on different languages** - Python, JS, Go, etc.
4. **Create custom configs** - Tune for specific repo structures
