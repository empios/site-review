"""Local static server for fixture sites (maps /a -> a.html, /loop -> redirect loop)."""
import functools
import http.server
import threading
from pathlib import Path


class Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        if self.path.startswith("/loop"):
            self.send_response(301)
            self.send_header("Location", "/loop")
            self.end_headers()
            return
        if self.path.startswith("/status/"):
            code = int(self.path.split("/")[2])
            body = b"<html><head><title>Blocked</title></head><body>Access denied</body></html>"
            self.send_response(code)
            self.send_header("Content-Type", "text/html")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        p = self.path.split("?")[0]
        if p not in ("/",) and "." not in Path(p).name:
            self.path = p + ".html"
        return super().do_GET()


class Server:
    def __init__(self, root: Path):
        h = functools.partial(Handler, directory=str(root))
        self.httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), h)
        self.base = f"http://127.0.0.1:{self.httpd.server_address[1]}"
        self.t = threading.Thread(target=self.httpd.serve_forever, daemon=True)

    def __enter__(self):
        self.t.start()
        return self

    def __exit__(self, *a):
        self.httpd.shutdown()
        self.httpd.server_close()
