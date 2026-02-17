"""HTTP server module for serving visualizations."""
import http.server
import socketserver
import socket

def create_handler(html_content):
    """Create a custom HTTP handler class with the HTML content."""
    class VisualizationHandler(http.server.SimpleHTTPRequestHandler):
        """Custom HTTP handler to serve the visualization HTML."""
        
        def do_GET(self):
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


def start_server(html_content, port=8000):
    """Start a local web server to serve the visualization."""
    handler_class = create_handler(html_content)
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
