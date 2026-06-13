# প্রবাহ — Professional Ultra Quiz Bot

The original `Pro_mongo_finalsexxes.py` (~25,600 lines) has been split into
an ordered set of section files under `bot/sections/`. **Behaviour is
identical** — sections are executed in the original order inside a single
shared globals namespace, so the dozens of late "FINAL OVERRIDE / PATCH"
sections still monkey-patch the earlier definitions exactly as before.

## Layout

```
bot/
├── config.py            # BOT_TOKEN, OWNER_ID — edit here (or use env vars)
├── __main__.py          # Entry point — `python -m bot`
├── __init__.py
├── requirements.txt
└── sections/
    ├── 00_header_imports.py
    ├── 01_config.py
    ├── 02_render_health_server.py
    ├── …                                (48 ordered files total)
    └── 47_elevenlabs_voice_to_text_06_04.py
```

Each section file maps to a clearly named chunk of the original script —
core router, OCR patches, group/topic patches, MongoDB backup, ElevenLabs
voice-to-text, etc. The filename prefix (`00_`, `01_`, …) **is** the load
order; do not rename without renumbering.

## Configuration

`bot/config.py` reads the following env vars (with the original hard-coded
values as fallbacks):

| Env var      | Purpose                              |
| ------------ | ------------------------------------ |
| `BOT_TOKEN`  | Telegram bot token from @BotFather   |
| `OWNER_ID`   | Numeric owner id (or comma-separated)|

All other runtime settings (Gemini / Perplexity / Mistral / ElevenLabs
keys, MongoDB URI, etc.) are still read from environment variables exactly
as in the original script — see the relevant section file or use the
matching in-bot `/setkey`, `/elevenlabs`, `/mistral`, … commands.

## Install & run

```bash
pip install -r bot/requirements.txt
# from the project root:
python -m bot
```

## Why this layout instead of `handlers/`, `services/`, `db/`?

The original script defines the same function name up to 4–5 times across
chronological "PATCH" blocks; only the last redefinition wins at runtime,
and many patches wrap earlier definitions (e.g. `_prev_main_elevenlabs = main; def main(): …; _prev_main_elevenlabs()`).
Re-architecting that into conventional `handlers/services/db` modules
without a full test harness would silently break behaviour. The
section-based layout gives you a professional, browsable file structure
*and* a 100% behaviour-preserving execution model. Once you have a test
rig in place we can iteratively collapse the patches into clean modules.

## How to edit

- Tweak a feature: edit the **last** section file that touches it (later
  sections override earlier ones — that's how the original works too).
- Add a brand-new feature: create `bot/sections/48_<your_slug>.py`. It is
  exec'd after every existing patch, so it can safely reference (and
  override) anything defined earlier.
- Never `import` a section file directly — they share globals via the
  runner, not via Python's normal import system.