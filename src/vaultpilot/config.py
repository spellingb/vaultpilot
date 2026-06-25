"""Environment / settings loading.

Values come from environment variables (and a local ``.env`` file, which is
gitignored). No secrets are required to run in mock mode (M0/M1) — they only
matter once real Bungie integration lands in M2.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- Bungie credentials (unused in mock mode; required from M2 on) ---
    bungie_api_key: str = ""
    bungie_client_id: str = ""
    bungie_client_secret: str = ""

    # --- OAuth ---
    # NOTE: Bungie does NOT accept a dynamic `scope` parameter in the authorize
    # URL — granted scope is fixed by the app's checkboxes. This is documentation
    # only. VaultPilot is read + act, so the app must have BOTH read and
    # move/equip scopes enabled.
    bungie_redirect_uri: str = "https://localhost:7777/callback"
    bungie_oauth_scope: str = "ReadDestinyInventoryAndVault,MoveEquipDestinyItems"
    oauth_callback_host: str = "localhost"
    oauth_callback_port: int = 7777

    # --- Local storage ---
    token_store_path: str = ".tokens.json"

    # --- Server ---
    mcp_server_name: str = "vaultpilot"
    log_level: str = "INFO"


def load_settings() -> Settings:
    """Load settings from the environment / .env file."""
    return Settings()
