"""Loopback redirect handler that captures the OAuth ``code``.

Bungie redirects the browser to the app's registered redirect URI
(``https://localhost:7777/callback?code=...&state=...``). This module runs a
tiny local server to catch that single request, validate the ``state`` nonce,
and hand the ``code`` back to the manager.

Bungie requires an **https** redirect, so the server needs a TLS cert. Pass
``certfile``/``keyfile`` (a self-signed pair is fine for local use). The
URL-parsing logic is split out as a pure function so it can be unit-tested
without binding a socket or terminating TLS.
"""

from __future__ import annotations

import ssl
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

from ..envelope import AuthError


def parse_callback(path_or_url: str, expected_state: str) -> str:
    """Extract and validate the auth ``code`` from a redirect path or full URL.

    Accepts either the raw request path (``/callback?code=..&state=..``) or a
    full URL pasted by the user. Raises ``AuthError`` on a state mismatch or a
    Bungie-reported error.
    """
    query = parse_qs(urlparse(path_or_url).query)

    if "error" in query:
        raise AuthError(f"Authorization failed: {query['error'][0]}")

    state = query.get("state", [None])[0]
    if state != expected_state:
        raise AuthError("State mismatch — possible CSRF; aborting.")

    code = query.get("code", [None])[0]
    if not code:
        raise AuthError("No authorization code in callback.")
    return code


def wait_for_code(
    host: str,
    port: int,
    expected_state: str,
    *,
    certfile: str | None = None,
    keyfile: str | None = None,
    timeout: float = 300.0,
) -> str:
    """Block until the browser hits the redirect, then return the auth code.

    Runs a single-shot local server. If ``certfile``/``keyfile`` are given the
    socket is wrapped in TLS (required to match Bungie's https redirect URI).
    """
    captured: dict[str, object] = {}

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802 (stdlib naming)
            try:
                captured["code"] = parse_callback(self.path, expected_state)
                body = b"VaultPilot: authorization received. You can close this tab."
                status = 200
            except AuthError as exc:
                captured["error"] = exc
                body = f"VaultPilot: {exc}".encode()
                status = 400
            self.send_response(status)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *_args) -> None:  # silence stdlib request logging
            pass

    server = HTTPServer((host, port), Handler)
    if certfile and keyfile:
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ctx.load_cert_chain(certfile=certfile, keyfile=keyfile)
        server.socket = ctx.wrap_socket(server.socket, server_side=True)
    server.timeout = timeout

    thread = threading.Thread(target=server.handle_request)
    thread.start()
    thread.join(timeout)
    server.server_close()

    if "error" in captured:
        raise captured["error"]  # type: ignore[misc]
    if "code" not in captured:
        raise AuthError("Timed out waiting for the OAuth redirect.")
    return captured["code"]  # type: ignore[return-value]
