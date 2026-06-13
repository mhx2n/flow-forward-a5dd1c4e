# ──────────────────────────────────────────────────────────────────────────────
# Section 60 (2026-06-13)
#   1) Sanitize explanations to remove "পাঠ্য/উদ্দীপক/প্রদত্ত/Option X সঠিক"
#      style framing so explanations focus on the topic itself.
#   2) Per-user OCR daily-limit override (.setuserlimit / .getuserlimit /
#      .resetuserlimit) — owner only.
#   3) `.cmds` / `.commands` — list every currently-active bot command.
#   Channel post throttle is bumped to 2.0s in section 53 & 59 directly so
#   Telegram won't flood-block during bulk posts.
# ──────────────────────────────────────────────────────────────────────────────

import re as _re60

# ─── 1. Explanation sanitizer ────────────────────────────────────────────────

_EXPL_BAD_PATTERNS_60 = [
    _re60.compile(r"^\s*Option\s*[A-Ea-e\u0995-\u09FF]\s*সঠিক\s*[,،]?\s*কারণ\s*", _re60.IGNORECASE),
    _re60.compile(r"^\s*সঠিক\s*উত্তর\s*[:\-]?\s*Option\s*[A-Ea-e]\s*[,،]?\s*কারণ\s*", _re60.IGNORECASE),
    _re60.compile(r"পাঠ্য\s*অনুসারে\s*[,،]?\s*"),
    _re60.compile(r"পাঠ্য\s*থেকে\s*জানা\s*যায়\s*[,،]?\s*"),
    _re60.compile(r"পাঠ্য\s*থেকে\s*[,،]?\s*"),
    _re60.compile(r"উদ্দীপকের\s*তথ্য\s*অনুযায়ী\s*[,،]?\s*"),
    _re60.compile(r"উদ্দীপক\s*অনুযায়ী\s*[,،]?\s*"),
    _re60.compile(r"উদ্দীপক\s*থেকে\s*[,،]?\s*"),
    _re60.compile(r"উদ্দীপকে\s*উল্লেখিত\s*[,،]?\s*"),
    _re60.compile(r"উদ্দীপকে\s*[,،]?\s*"),
    _re60.compile(r"প্রদত্ত\s*সমাধান\s*অনুযায়ী\s*[,،]?\s*"),
    _re60.compile(r"প্রদত্ত\s*তথ্য\s*অনুযায়ী\s*[,،]?\s*"),
    _re60.compile(r"প্রদত্ত\s*অনুচ্ছেদ\s*অনুযায়ী\s*[,،]?\s*"),
    _re60.compile(r"প্রদত্ত\s*[,،]?\s*"),
    _re60.compile(r"According\s+to\s+the\s+(passage|text|stimulus)\s*[,،]?\s*", _re60.IGNORECASE),
]

def _sanitize_explanation_60(text: str) -> str:
    s = str(text or "").strip()
    if not s:
        return s
    for _ in range(4):
        prev = s
        for pat in _EXPL_BAD_PATTERNS_60:
            s = pat.sub("", s, count=1).strip()
        if s == prev:
            break
    # Capitalize Bangla sentence — strip stray leading punctuation
    s = _re60.sub(r"^[\s,।:\-–—]+", "", s)
    return s.strip()


try:
    _prev_buffer_add_60 = buffer_add  # type: ignore[name-defined]
except Exception:
    _prev_buffer_add_60 = None


def buffer_add(user_id, payload):  # noqa: F811
    try:
        if isinstance(payload, dict):
            expl = payload.get("explanation")
            if expl:
                payload = dict(payload)
                payload["explanation"] = _sanitize_explanation_60(expl)
    except Exception:
        pass
    if _prev_buffer_add_60 is None:
        raise RuntimeError("buffer_add unavailable")
    return _prev_buffer_add_60(user_id, payload)


# ─── 2. Per-user OCR daily limit override ────────────────────────────────────

def _user_limit_key_60(uid: int) -> str:
    return f"mistral_user_limit_{int(uid)}"

def get_user_ocr_limit_override_60(uid: int):
    try:
        raw = get_setting(_user_limit_key_60(uid), "").strip()
        if not raw:
            return None
        return max(0, min(int(raw), 10000))
    except Exception:
        return None

def set_user_ocr_limit_override_60(uid: int, value: int) -> None:
    set_setting(_user_limit_key_60(uid), str(max(0, min(int(value), 10000))))

def clear_user_ocr_limit_override_60(uid: int) -> None:
    set_setting(_user_limit_key_60(uid), "")


try:
    _prev_remaining_quota_60 = _remaining_user_ocr_quota  # type: ignore[name-defined]
except Exception:
    _prev_remaining_quota_60 = None

def _remaining_user_ocr_quota(user_id: int) -> int:  # noqa: F811
    override = get_user_ocr_limit_override_60(user_id)
    if override is None:
        if _prev_remaining_quota_60 is not None:
            return _prev_remaining_quota_60(user_id)
        return 0
    if override <= 0:
        return 0
    try:
        used = _get_user_ocr_usage(int(user_id))
    except Exception:
        used = 0
    return max(0, override - used)


async def cmd_setuserlimit_60(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id if update.effective_user else 0
    if not _is_owner_id(uid):
        with contextlib.suppress(Exception):
            await update.effective_message.reply_text("Owner only.")
        return
    args = (context.args or [])
    if len(args) < 2:
        with contextlib.suppress(Exception):
            await update.effective_message.reply_text(
                "Usage: .setuserlimit <user_id> <daily_limit>\n"
                "Example: .setuserlimit 12345678 50"
            )
        return
    try:
        target_uid = int(args[0])
        limit = int(args[1])
    except Exception:
        with contextlib.suppress(Exception):
            await update.effective_message.reply_text("Invalid user_id or limit.")
        return
    set_user_ocr_limit_override_60(target_uid, limit)
    with contextlib.suppress(Exception):
        await update.effective_message.reply_text(
            f"✅ Per-user OCR daily limit set:\nuser_id: <code>{target_uid}</code>\nlimit: <code>{limit}</code>",
            parse_mode=ParseMode.HTML,
        )

async def cmd_getuserlimit_60(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id if update.effective_user else 0
    if not _is_owner_id(uid):
        return
    args = (context.args or [])
    if not args:
        with contextlib.suppress(Exception):
            await update.effective_message.reply_text("Usage: .getuserlimit <user_id>")
        return
    try:
        target_uid = int(args[0])
    except Exception:
        return
    override = get_user_ocr_limit_override_60(target_uid)
    try:
        used = _get_user_ocr_usage(target_uid)
    except Exception:
        used = 0
    if override is None:
        try:
            base = get_mistral_user_daily_limit()
        except Exception:
            base = 3
        msg = f"user_id: <code>{target_uid}</code>\nUsing global limit: <code>{base}</code>\nUsed today: <code>{used}</code>"
    else:
        msg = f"user_id: <code>{target_uid}</code>\nCustom limit: <code>{override}</code>\nUsed today: <code>{used}</code>"
    with contextlib.suppress(Exception):
        await update.effective_message.reply_text(msg, parse_mode=ParseMode.HTML)

async def cmd_resetuserlimit_60(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id if update.effective_user else 0
    if not _is_owner_id(uid):
        return
    args = (context.args or [])
    if not args:
        with contextlib.suppress(Exception):
            await update.effective_message.reply_text("Usage: .resetuserlimit <user_id>")
        return
    try:
        target_uid = int(args[0])
    except Exception:
        return
    clear_user_ocr_limit_override_60(target_uid)
    with contextlib.suppress(Exception):
        await update.effective_message.reply_text(
            f"✅ Cleared custom limit for <code>{target_uid}</code> — now using global default.",
            parse_mode=ParseMode.HTML,
        )


# ─── 3. .cmds — list every active command ────────────────────────────────────

_CMDS_LIST_60 = """\
<b>📋 প্রবাহ — Active Commands</b>

<b>🟢 Basic</b>
• /start /help /ping /uptime /myid /whoami
• /done — export buffer to CSV
• /clear — clear buffer
• /filter — manage admin filters

<b>📤 Channel & Post</b>
• /addchannel /listchannels /removechannel /setprefix
• .p &lt;N&gt; [keep] — post N quizzes from buffer
• Action card buttons after .gen: 📤 Post / 🎯 Choose / 📂 CSV / 🧹 Clear

<b>🎯 Quiz Generation (Owner/Admin)</b>
• .gen — reply to OCR page → opens mode picker (Med/Eng/Ver/Std)
• .gen &lt;N&gt; — generate N MCQs to buffer
• .gen med [N] / .gen eng [N] / .gen ver [N] / .gen std [N]
• 📌 Source MCQ button — export/post only the original questions
• /explain on|off — toggle explanation in poll

<b>📷 OCR</b>
• Reply to image/PDF with .ocr or .gen
• .howmark / .markhelp — how to mark correct answer for OCR

<b>👥 Access & Admins</b>
• /addadmin /removeadmin /admins /adminpanel /banned
• /grantall /revokeall — owner gives an admin full channel view

<b>🎚️ Limits (Owner)</b>
• /ocrlimit &lt;N&gt; — set GLOBAL per-user daily OCR limit
• .setuserlimit &lt;user_id&gt; &lt;N&gt; — custom limit for ONE user
• .getuserlimit &lt;user_id&gt; — show user's current limit/usage
• .resetuserlimit &lt;user_id&gt; — drop custom limit

<b>🤖 AI Keys (Owner)</b>
• /gemini add|list|remove
• /mistral add|list|remove

<b>💬 Messaging</b>
• /ask /reply /broadcast — inline or reply-aware

<b>ℹ️ Info</b>
• .cmds / .commands — this list

<i>Note: channel posting now waits 2 seconds between each quiz to avoid Telegram flood-block.</i>
"""

async def cmd_cmds_60(update: Update, context: ContextTypes.DEFAULT_TYPE):
    with contextlib.suppress(Exception):
        await update.effective_message.reply_text(
            _CMDS_LIST_60, parse_mode=ParseMode.HTML, disable_web_page_preview=True
        )


# ─── Dot-command dispatcher (matches .setuserlimit etc.) ────────────────────

_DOT_RE_60 = _re60.compile(r"^\.(setuserlimit|getuserlimit|resetuserlimit|cmds|commands)\b\s*(.*)$", _re60.IGNORECASE)

async def _dot_dispatch_60(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if not msg or not msg.text:
        return
    m = _DOT_RE_60.match(msg.text.strip())
    if not m:
        return
    cmd = m.group(1).lower()
    rest = (m.group(2) or "").strip()
    context.args = rest.split() if rest else []
    if cmd == "setuserlimit":
        await cmd_setuserlimit_60(update, context)
    elif cmd == "getuserlimit":
        await cmd_getuserlimit_60(update, context)
    elif cmd == "resetuserlimit":
        await cmd_resetuserlimit_60(update, context)
    elif cmd in ("cmds", "commands"):
        await cmd_cmds_60(update, context)


_prev_build_app_60 = build_app

def build_app() -> Application:
    app = _prev_build_app_60()
    with contextlib.suppress(Exception):
        app.add_handler(CommandHandler(["cmds", "commands"], cmd_cmds_60))
        app.add_handler(CommandHandler("setuserlimit", cmd_setuserlimit_60))
        app.add_handler(CommandHandler("getuserlimit", cmd_getuserlimit_60))
        app.add_handler(CommandHandler("resetuserlimit", cmd_resetuserlimit_60))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, _dot_dispatch_60), group=-400)
    return app

# ===== END SECTION 60 =====