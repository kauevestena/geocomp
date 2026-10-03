# SPDX-License-Identifier: GPL-2.0-or-later
"""A local product archive for the download tests: run as a separate process.

``python product_archive.py ROOT USER PASSWORD`` serves the files under ROOT on
an ephemeral port of 127.0.0.1 and prints the port. Paths under ``/private/``
need HTTP Basic credentials; ``/fail/`` answers 500; ``/redirect/`` answers 302
to the rest of the path, as GitHub does for a release download (P12c-6, the
engine installer); anything else is anonymous.

A process rather than a thread because the QGIS request blocks the interpreter
that issues it: a server sharing that interpreter could not answer. A 401
carries no ``WWW-Authenticate`` challenge, so the QGIS network stack never asks
anyone for a password -- a login is applied by reference or not at all, which
is what is being tested.
"""

from __future__ import annotations

import base64
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


def main() -> None:
    root, user, password = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
    expected = "Basic " + base64.b64encode(f"{user}:{password}".encode()).decode()

    class Handler(BaseHTTPRequestHandler):
        def _answer(self, body: bool) -> None:
            if self.path.startswith("/fail/"):
                self._status(500)
                return
            if self.path.startswith("/redirect/"):
                self.send_response(302)
                # Absolute, as GitHub's is: QGIS's blocking request does not
                # resolve a relative Location against the request.
                host, port = self.server.server_address[:2]
                self.send_header("Location", f"http://{host}:{port}{self.path[len('/redirect') :]}")
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            if self.path.startswith("/private/") and self.headers.get("Authorization") != expected:
                self._status(401)
                return
            path = root / self.path.lstrip("/")
            if not path.is_file():
                self._status(404)
                return
            data = path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            if body:
                self.wfile.write(data)

        def _status(self, code: int) -> None:
            self.send_response(code)
            self.send_header("Content-Length", "0")
            self.end_headers()

        def do_GET(self) -> None:
            self._answer(True)

        def do_HEAD(self) -> None:
            self._answer(False)

        def log_message(self, *args) -> None:
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    print(server.server_address[1], flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
