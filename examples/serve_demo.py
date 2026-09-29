"""Serve the demo shop and a fake tracker on your own machine.

    python examples/serve_demo.py [--port 8411] [--tracker-port 8412]

Two local origins, so the browser sees two different sites:

    http://127.0.0.1:8411/examples/demo-shop/           tracker loaded only through the banner
    http://127.0.0.1:8411/examples/demo-shop/ungated.html  same page, tracker loaded directly
    http://localhost:8412/tracker.js                     "Demo Analytics", a fake tracker

The first-party server serves the repository root, so pages use the real
consent-banner-lite files. In .html files, {{TRACKER}} is replaced by the
tracker's origin. Nothing here talks to the internet. Stop with Ctrl+C.
"""

from __future__ import annotations

import argparse
import mimetypes
import secrets
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

REPO = Path(__file__).resolve().parent.parent
TRACKER_ROOT = REPO / "examples" / "fake-tracker"
GIF = (
    b"GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!\xf9\x04\x01\x00"
    b"\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"
)


def _handler(root: Path, replacements: dict[str, str], hits: list[str] | None, quiet: bool):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):
            if not quiet:
                print(f"{self.headers.get('Host', '?')} {self.command} {self.path}")

        def do_GET(self):
            if hits is not None:
                hits.append(self.path)
            path = urlsplit(self.path).path
            if path == "/collect" and hits is not None:
                self.send_response(200)
                self.send_header("Content-Type", "image/gif")
                self.send_header("Set-Cookie", f"da_uid={secrets.token_hex(8)}; Max-Age=31536000; Path=/; SameSite=None; Secure")
                self.send_header("Content-Length", str(len(GIF)))
                self.end_headers()
                self.wfile.write(GIF)
                return
            if path.endswith("/"):
                path += "index.html"
            file = (root / path.lstrip("/")).resolve()
            if root not in file.parents or not file.is_file():
                self.send_error(404)
                return
            body = file.read_bytes()
            if file.suffix == ".html":
                text = body.decode("utf-8")
                for key, value in replacements.items():
                    text = text.replace(key, value)
                body = text.encode("utf-8")
            ctype = mimetypes.guess_type(file.name)[0] or "application/octet-stream"
            if file.suffix == ".js":
                ctype = "text/javascript"
            if ctype.startswith("text/"):
                ctype += "; charset=utf-8"
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    return Handler


class Demo:
    """Both servers, started in background threads."""

    def __init__(self, port: int = 0, tracker_port: int = 0, quiet: bool = True):
        self.tracker_hits: list[str] = []
        self._tracker = ThreadingHTTPServer(("127.0.0.1", tracker_port), _handler(TRACKER_ROOT, {}, self.tracker_hits, quiet))
        self.tracker_url = f"http://localhost:{self._tracker.server_address[1]}"
        self._site = ThreadingHTTPServer(("127.0.0.1", port), _handler(REPO, {"{{TRACKER}}": self.tracker_url}, None, quiet))
        self.site_url = f"http://127.0.0.1:{self._site.server_address[1]}"
        for server in (self._tracker, self._site):
            threading.Thread(target=server.serve_forever, daemon=True).start()

    def close(self) -> None:
        for server in (self._site, self._tracker):
            server.shutdown()
            server.server_close()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--port", type=int, default=8411)
    ap.add_argument("--tracker-port", type=int, default=8412)
    args = ap.parse_args()
    demo = Demo(args.port, args.tracker_port, quiet=False)
    print(f"demo shop (gated):   {demo.site_url}/examples/demo-shop/")
    print(f"demo shop (ungated): {demo.site_url}/examples/demo-shop/ungated.html")
    print(f"fake tracker:        {demo.tracker_url}/tracker.js")
    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        demo.close()


if __name__ == "__main__":
    main()
