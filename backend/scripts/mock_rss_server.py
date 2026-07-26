"""本地 mock RSS HTTP server · 替代 RSSHub（国内 Docker 拉不动）。

serve backend/mock_rss/*.xml on port 1200.

用法：
  cd backend && ./.venv/bin/python scripts/mock_rss_server.py &
"""
import http.server
import socketserver
from pathlib import Path

MOCK_DIR = Path(__file__).parent.parent / "mock_rss"
PORT = 1200


class MockRSSHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # /rss/<slug>.xml
        if self.path.startswith("/rss/"):
            slug = self.path[len("/rss/"):]
            xml_path = MOCK_DIR / slug
            if not xml_path.exists():
                self.send_error(404, f"Mock RSS not found: {slug}")
                return
            content = xml_path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "application/rss+xml; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        elif self.path == "/" or self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(f"Mock RSS server · {len(list(MOCK_DIR.glob('*.xml')))} sources\n".encode())
        else:
            self.send_error(404, "Use /rss/<slug>.xml")

    def log_message(self, fmt, *args):
        pass  # 静音


if __name__ == "__main__":
    with socketserver.TCPServer(("0.0.0.0", PORT), MockRSSHandler) as httpd:
        print(f"Mock RSS server on :{PORT} · {MOCK_DIR}")
        httpd.serve_forever()