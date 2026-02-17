"""HTTP server module for serving visualizations."""
import http.server
import json
import platform
import subprocess
import socketserver
import socket
from urllib.parse import parse_qs, urlparse


def _run_folder_picker():
    """Run the system folder picker; return the selected path or None if cancelled/unsupported."""
    system = platform.system()
    try:
        if system == "Darwin":
            # macOS: AppleScript choose folder
            result = subprocess.run(
                [
                    "osascript",
                    "-e",
                    'return POSIX path of (choose folder with prompt "Choose repository folder")',
                ],
                capture_output=True,
                text=True,
                timeout=120,
            )
            if result.returncode == 0 and result.stdout:
                return result.stdout.strip()
            return None
        if system == "Windows":
            # Windows: PowerShell folder browser
            script = """
Add-Type -AssemblyName System.Windows.Forms
$dialog = New-Object System.Windows.Forms.FolderBrowserDialog
$dialog.Description = "Choose repository folder"
$dialog.ShowDialog() | Out-Null
if ($dialog.SelectedPath) { $dialog.SelectedPath }
"""
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", script],
                capture_output=True,
                text=True,
                timeout=120,
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
            return None
        if system == "Linux":
            # Linux: zenity or kdialog
            for cmd, args in [
                ("zenity", ["zenity", "--file-selection", "--directory", "--title=Choose repository folder"]),
                ("kdialog", ["kdialog", "--getexistingdirectory", ".", "Choose repository folder"]),
            ]:
                try:
                    result = subprocess.run(
                        args,
                        capture_output=True,
                        text=True,
                        timeout=120,
                    )
                    if result.returncode == 0 and result.stdout:
                        return result.stdout.strip()
                    break
                except FileNotFoundError:
                    continue
            return None
        return None
    except (subprocess.TimeoutExpired, Exception):
        return None


def create_handler(html_content, load_repo_callback=None):
    """Create a custom HTTP handler class with the HTML content.
    If load_repo_callback is set, GET /api/load?path=... will call it and return JSON."""
    class VisualizationHandler(http.server.SimpleHTTPRequestHandler):
        """Custom HTTP handler to serve the visualization HTML."""

        def do_GET(self):
            parsed = urlparse(self.path)
            if parsed.path == '/api/browse':
                path = _run_folder_picker()
                if path:
                    self._send_json(200, {'path': path})
                else:
                    self._send_json(200, {'path': '', 'cancelled': True})
                return
            if parsed.path == '/api/load' and load_repo_callback is not None:
                query = parse_qs(parsed.query)
                path_list = query.get('path')
                path = path_list[0].strip() if path_list else ''
                if not path:
                    self._send_json(400, {'error': 'Missing path parameter'})
                    return
                try:
                    data = load_repo_callback(path)
                    if isinstance(data, dict) and 'error' in data:
                        self._send_json(400, data)
                    else:
                        self._send_json(200, data)
                except Exception as e:
                    self._send_json(500, {'error': str(e)})
                return
            if self.path == '/' or self.path == '/index.html':
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                content_bytes = html_content.encode('utf-8')
                self.send_header('Content-Length', str(len(content_bytes)))
                self.end_headers()
                self.wfile.write(content_bytes)
            else:
                self.send_response(404)
                self.end_headers()

        def _send_json(self, status, data):
            body = json.dumps(data).encode('utf-8')
            self.send_response(status)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format, *args):
            # Suppress default logging
            pass

    return VisualizationHandler


def get_local_ip():
    """Get the local IP address for network access."""
    try:
        # Connect to a remote address to determine local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return None


def find_available_port(start=8000, max_tries=20):
    """Find an available port starting from start. Returns None if none found."""
    for i in range(max_tries):
        port = start + i
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("0.0.0.0", port))
                return port
        except OSError:
            continue
    return None


def start_server(html_content, port=8000, load_repo_callback=None):
    """Start a local web server to serve the visualization.
    If load_repo_callback(path_str) is provided, GET /api/load?path=... returns graph JSON for that repo."""
    handler_class = create_handler(html_content, load_repo_callback=load_repo_callback)
    # Allow reusing the port so restarts don't leave it in TIME_WAIT
    socketserver.TCPServer.allow_reuse_address = True

    # Bind to 0.0.0.0 to allow network access
    with socketserver.TCPServer(("0.0.0.0", port), handler_class) as httpd:
        local_ip = get_local_ip()
        print(f"🌐 Server running!")
        print(f"   Local:  http://localhost:{port}/")
        if local_ip:
            print(f"   Network: http://{local_ip}:{port}/")
            print(f"   Share this link with others on your network!")
        print(f"   Press Ctrl+C to stop the server")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Server stopped.")
