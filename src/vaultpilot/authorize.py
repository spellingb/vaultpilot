"""Interactive CLI to mint a Bungie token. Run this on your own machine.

    python -m vaultpilot.authorize            # manual paste (default, no TLS cert)
    python -m vaultpilot.authorize --serve     # auto loopback (needs https cert)

Manual mode sidesteps the one awkward part of the loopback flow: Bungie requires
an *https* redirect, which means a TLS cert for a local server. In manual mode you
just open the printed URL, approve, and paste the redirected ``localhost`` URL
back here — VaultPilot pulls the ``code`` out of it. Tokens are saved to
``TOKEN_STORE_PATH`` (default ``.tokens.json``), gitignored.
"""

from __future__ import annotations

import argparse
import webbrowser

from .auth.callback import parse_callback, wait_for_code
from .auth.manager import OAuthManager
from .auth.oauth import OAuthConfig
from .auth.token_store import FileTokenStore
from .config import load_settings
from .envelope import AuthError


def _build_manager(settings) -> OAuthManager:
    config = OAuthConfig(
        client_id=settings.bungie_client_id,
        client_secret=settings.bungie_client_secret,
        api_key=settings.bungie_api_key,
        redirect_uri=settings.bungie_redirect_uri,
    )
    return OAuthManager(config, FileTokenStore(settings.token_store_path))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Authorize VaultPilot against Bungie.")
    parser.add_argument("--serve", action="store_true",
                        help="Run a local https callback server instead of manual paste.")
    parser.add_argument("--certfile", help="TLS cert for --serve (https redirect).")
    parser.add_argument("--keyfile", help="TLS key for --serve.")
    args = parser.parse_args(argv)

    settings = load_settings()
    missing = [n for n in ("bungie_api_key", "bungie_client_id", "bungie_client_secret")
               if not getattr(settings, n)]
    if missing:
        print(f"Missing credentials in .env: {', '.join(missing)}")
        return 1

    mgr = _build_manager(settings)
    authorize_url, state = mgr.start_authorization()

    print("\nOpen this URL in your browser and approve access:\n")
    print(f"  {authorize_url}\n")
    try:
        webbrowser.open(authorize_url)
    except Exception:  # pragma: no cover - environment dependent
        pass

    try:
        if args.serve:
            print(f"Waiting for redirect on {settings.bungie_redirect_uri} ...")
            code = wait_for_code(
                settings.oauth_callback_host, settings.oauth_callback_port, state,
                certfile=args.certfile, keyfile=args.keyfile,
            )
        else:
            pasted = input("After approving, paste the full redirect URL here:\n  ").strip()
            code = parse_callback(pasted, expected_state=state)

        token = mgr.complete_authorization(code)
    except AuthError as exc:
        print(f"\nAuthorization failed: {exc}")
        return 1

    print("\nSuccess — token saved.")
    print(f"  membership_id: {token.membership_id}")
    print(f"  access token expires: {token.access_expires_at.isoformat()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
