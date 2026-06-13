"""Centralised configuration for প্রবাহ bot.

Edit values here (or set the matching environment variables) instead of
touching the section files. Values defined here are injected into the
shared runtime namespace by ``bot/__main__.py`` *before* any section is
executed, so every section sees the same ``BOT_TOKEN`` / ``OWNER_ID``.
"""
from __future__ import annotations

import os

# ─── Required ────────────────────────────────────────────────────────────────
# Telegram bot token from @BotFather. Prefer the env var on production hosts
# (Render / Pella / Fly / etc.) so the value is not committed to git.
BOT_TOKEN: str = os.getenv(
    "BOT_TOKEN",
    "8373412574:AAHr9YtdIxVfxfNz6LTdYrfJepO47S2OmB4",
).strip()

# Numeric Telegram user id of the bot owner. Accepts a single int or a
# comma-separated string of multiple owner ids (the original normaliser in
# section 01 handles both shapes).
OWNER_ID: int | str = os.getenv("OWNER_ID", "8535385246").strip() or 8535385246
try:
    OWNER_ID = int(OWNER_ID)  # keep as int when possible
except (TypeError, ValueError):
    pass  # leave as comma-separated string; section 01 will normalise


def as_runtime_globals() -> dict:
    """Return the config values that must be present in the shared
    namespace before any section executes."""
    return {
        "BOT_TOKEN": BOT_TOKEN,
        "OWNER_ID": OWNER_ID,
    }