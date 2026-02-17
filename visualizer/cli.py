"""
CLI entry point for the codebase visualizer.

Usage:
    python -m visualizer --repo <path> [--output <file>] [--port <num>] [--no-server]
"""

import argparse
import json
import sys
import webbrowser
import time
import threading
from pathlib import Path

from .config import VisualizerConfig
from .scanner import RepoScanner
from .parser import extract_imports_from_files
from .graph import DependencyGraph


from .ui import generate_html
from .server import start_server, find_available_port, get_local_ip


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Visualize codebase structure',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Visualize current directory
  python -m visualizer --repo .
  
  # Visualize specific repo and save to file
  python -m visualizer --repo /path/to/repo --output visualization.html --no-server
  
  # Visualize with custom config
  python -m visualizer --repo /path/to/repo --config custom.json
        """
    )
    parser.add_argument(
        '--repo', '-r',
        type=str,
        default='.',
        help='Path to target repository (default: current directory)'
    )
    parser.add_argument(
        '--config', '-c',
        type=str,
        help='Path to config file (.visualizer.json). If not specified, looks for .visualizer.json in repo.'
    )
    parser.add_argument(
        '--output', '-o',
        type=str,
        help='Save HTML to file instead of starting server'
    )
    parser.add_argument(
        '--port', '-p',
        type=int,
        help='Port for local server (default: auto-find available port starting from 8000)'
    )
    parser.add_argument(
        '--no-server',
        action='store_true',
        help='Only generate HTML file, do not start server'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output graph data as JSON instead of HTML (for IDE integration)'
    )
    
    args = parser.parse_args()
    
    # Load configuration
    repo_path = Path(args.repo).resolve()
    if not repo_path.exists():
        if args.json:
            # For JSON output, write error to stderr and return error JSON
            error_json = json.dumps({"error": f"Repository path '{repo_path}' does not exist"})
            print(error_json, file=sys.stderr)
            return 1
        print(f"❌ Error: Repository path '{repo_path}' does not exist")
        return 1
    
    if args.config:
        config_path = Path(args.config).resolve()
        if not config_path.exists():
            if args.json:
                error_json = json.dumps({"error": f"Config file '{config_path}' does not exist"})
                print(error_json, file=sys.stderr)
                return 1
            print(f"❌ Error: Config file '{config_path}' does not exist")
            return 1
        config = VisualizerConfig.from_file(config_path, repo_path=repo_path)
    else:
        config = VisualizerConfig.load_for_repo(repo_path)
    
    # Suppress progress messages for JSON output
    if not args.json:
        print("🔮 Codebase Visualizer")
        print("=" * 40)
        print(f"📂 Repository: {repo_path}")
        if config.find_config_file():
            print(f"⚙️  Config: {config.find_config_file()}")
        else:
            print("⚙️  Config: Using defaults")
        print()
    
    # Scan repository
    scanner = RepoScanner(config)
    scan_result = scanner.scan()
    files = scan_result['files']
    folders = scan_result['folders']
    
    # Extract imports
    if not args.json:
        print("🔍 Extracting imports...")
    imports = extract_imports_from_files(files, config.repo_path, config)
    
    # Build dependency graph
    graph = DependencyGraph(config, files, folders, imports)
    data = graph.build()
    
    # Output JSON if requested (for IDE integration)
    if args.json:
        json_output = json.dumps(data, indent=2)
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(json_output)
            # Still print success message even for JSON mode when saving to file
            print(f"✅ JSON saved to: {output_path.absolute()}", file=sys.stderr)
        else:
            # Output pure JSON to stdout (no progress messages)
            print(json_output)
        return 0
    
    print(f"📈 Computed metrics for {len(files)} files")
    print(f"   Total dependencies: {data['stats']['totalDependencies']}")
    if data['hotspots']:
        print(f"   Top hotspot: {data['hotspots'][0]['name']} (fan-in: {data['hotspots'][0]['fanIn']})")
    
    # Generate HTML
    print("🎨 Generating visualization...")
    html = generate_html(data)
    
    # Save to file if output path is specified
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"✅ HTML saved to: {output_path.absolute()}")
        if args.no_server:
            return 0
        print(f"   (Also starting local server below)")
    
    # Start server unless --no-server is specified
    if args.no_server:
        print("ℹ️  Use --output to save HTML file for deployment")
        return 0
    
    # Determine port
    if args.port:
        port = args.port
    else:
        port = find_available_port(8000)
        if port is None:
            print("❌ Error: No available port found (tried 8000–8019). Stop other services using these ports.")
            return 1
        if port != 8000:
            print(f"   Port 8000 in use, using port {port} instead.")
    
    # Start server
    server_thread = threading.Thread(target=start_server, args=(html, port), daemon=True)
    server_thread.start()
    
    # Give server a moment to start
    time.sleep(1)
    
    local_url = f'http://localhost:{port}/'
    local_ip = get_local_ip()
    network_url = f'http://{local_ip}:{port}/' if local_ip else None
    
    print(f"📊 Opening visualization in browser...")
    print(f"   Local URL: {local_url}")
    if network_url:
        print(f"   Network URL: {network_url}")
        print(f"   Share the network URL with others on your network!")
    webbrowser.open(local_url)
    
    print("\n✨ Server is running! Explore your codebase visually.")
    print("   - Click nodes to see dependency edges")
    print("   - Check Hotspots panel for most important files")
    print(f"\n🌐 Access the visualization at:")
    print(f"   Local:  {local_url}")
    if network_url:
        print(f"   Network: {network_url}")
    print("   Press Ctrl+C to stop the server")
    
    # Keep the main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
        return 0


if __name__ == '__main__':
    sys.exit(main())
