# ──────────────────────────────────────────────────────────────────────────────
# Section 61 (2026-06-13)
#   1) Strip "Option X is correct because" / "Option X সঠিক কারণ" framing
#      from explanations so the poll explanation goes straight into the topic.
#   2) Open .gen to regular users with an owner-customizable per-user limit.
#      Picker shows a doubling ladder (2, 4, 8, … up to user's limit) plus a
#      reply-with-number hint. Replying with a number inside the limit closes
#      (deletes) the picker message and starts generation immediately.
#   3) Owner commands:
#        .setgenlimit <user_id> <N>
#        .getgenlimit <user_id>
#        .resetgenlimit <user_id>
#      Staff (owner/admin) keep an unlimited 500-cap ladder.
# ──────────────────────────────────────────────────────────────────────────────

import re as _re61

# ─── 1. Strip "Option X is correct because" prefix ──────────────────────────

_OPTION_PREFIX_PATTERNS_61 = [
    _re61.compile(r"^\s*Option\s*[A-Ea-e0-9\u0995-\u09FF]{1,3}\s*(?:is\s+correct|correct)\s*(?:because|since)?\s*[,،:\-–—]?\s*", _re61.IGNORECASE),
    _re61.compile(r"^\s*(?:সঠিক\s*উত্তর|উত্তর)\s*[:\-]?\s*Option\s*[A-Ea-e0-9]{1,3}\s*(?:সঠিক)?\s*(?:কারণ|যেহেতু)?\s*[,،:\-–—]?\s*", _re61.IGNORECASE),
    _re61.compile(r"^\s*Option\s*[A-Ea-e0-9]{1,3}\s*সঠিক\s*(?:কারণ|যেহেতু)?\s*[,،:\-–—]?\s*", _re61.IGNORECASE),
    _re61.compile(r"^\s*(?:Answer|Ans)\s*[:\-]?\s*[A-Ea-e0-9]{1,3}\s*[,،:\-–—]?\s*", _re61.IGNORECASE),
    _re61.compile(r"^\s*[A-Ea-e]\s*\)\s*সঠিক\s*[,،:\-–—]?\s*"),
]

def _strip_option_prefix_61(text: str) -> str:
    s = str(text or "").strip()
    if not s:
        return s
    for _ in range(3):
        prev = s
        for pat in _OPTION_PREFIX_PATTERNS_61:
            s = pat.sub("", s, count=1).strip()
        if s == prev:
            break
    s = _re61.sub(r"^[\s,।:\-–—]+", "", s)
    if s:
        s = s[0].upper() + s[1:] if s[0].isascii() and s[0].isalpha() else s
    return s.strip()


try:
    _prev_buffer_add_61 = buffer_add  # type: ignore[name-defined]
except Exception:
    _prev_buffer_add_61 = None

def buffer_add(user_id, payload):  # noqa: F811
    try:
        if isinstance(payload, dict) and payload.get("explanation"):
            payload = dict(payload)
            payload["explanation"] = _strip_option_prefix_61(payload["explanation"])
    except Exception:
        pass
    if _prev_buffer_add_61 is None:
        raise RuntimeError("buffer_add unavailable")
    return _prev_buffer_add_61(user_id, payload)


# ─── 2. Per-user .gen generation limit ──────────────────────────────────────

DEFAULT_USER_GEN_LIMIT_61 = 10

def _gen_limit_key_61(uid: int) -> str:
    return f"user_gen_limit_{int(uid)}"

def get_user_gen_limit_61(uid: int) -> int:
    try:
        raw = get_setting(_gen_limit_key_61(uid), "").strip()
        if raw:
            return max(1, min(int(raw), 500))
    except Exception:
        pass
    try:
        raw = get_setting("user_gen_limit_default", "").strip()
        if raw:
            return max(1, min(int(raw), 500))
    except Exception:
        pass
    return DEFAULT_USER_GEN_LIMIT_61

def set_user_gen_limit_61(uid: int, value: int) -> None:
    set_setting(_gen_limit_key_61(uid), str(max(1, min(int(value), 500))))

def clear_user_gen_limit_61(uid: int) -> None:
    set_setting(_gen_limit_key_61(uid), "")


def _doubling_ladder_61(limit: int) -> List[int]:
    out: List[int] = []
    n = 2
    while n <= limit:
        out.append(n)
        n *= 2
    if not out or out[-1] != limit:
        out.append(limit)
    # dedupe while keeping order
    seen = set()
    dedup = []
    for v in out:
        if v not in seen:
            seen.add(v); dedup.append(v)
    return dedup[:8]


def _g61_count_kb(tok: str, limit: int) -> InlineKeyboardMarkup:
    nums = _doubling_ladder_61(limit)
    rows: List[List[InlineKeyboardButton]] = []
    row: List[InlineKeyboardButton] = []
    for n in nums:
        row.append(InlineKeyboardButton(str(n), callback_data=f"g59:cnt:{n}:{tok}"))
        if len(row) == 3:
            rows.append(row); row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton("✖ Cancel", callback_data=f"g59:x:x:{tok}")])
    return InlineKeyboardMarkup(rows)


def _count_hint_text_61(mode: str, limit: int, is_staff: bool) -> str:
    base = f"Mode: <b>{h((mode or 'std').upper())}</b>"
    if is_staff:
        return base + "\n\n💬 রিপ্লাই করে যেকোনো সংখ্যা (1-500) দিতে পারো।"
    return (
        base
        + f"\n\n🎯 তোমার লিমিট: <b>{limit}</b>"
        + f"\n💬 এই মেসেজে রিপ্লাই করে 1–{limit} এর মধ্যে যেকোনো সংখ্যা দিতে পারো — সংখ্যা দিলেই এই মেসেজ মুছে গিয়ে জেনারেট শুরু হবে।"
    )


def _is_staff_61(uid: int) -> bool:
    try:
        return bool(is_owner(uid) or is_admin(uid))
    except Exception:
        return False


# Override cmd_gen so non-staff also get the picker (capped).
try:
    _prev_cmd_gen_61 = cmd_gen  # type: ignore[name-defined]
except Exception:
    _prev_cmd_gen_61 = None


async def cmd_gen(update: Update, context: ContextTypes.DEFAULT_TYPE):  # noqa: F811
    ensure_user(update)
    if not update.message or not update.effective_user:
        raise ApplicationHandlerStop
    uid = int(update.effective_user.id)
    if is_banned(uid):
        raise ApplicationHandlerStop
    is_staff = _is_staff_61(uid)
    reply_msg = update.message.reply_to_message
    if not reply_msg:
        await safe_reply(update, usage_box("gen", "[med|eng|engg|ver|std] [count]", "Reply to an OCR image/PDF/result, then run .gen or .gen med 20."))
        raise ApplicationHandlerStop
    mode, count, _ = _mode_count_59(update.message.text or "", list(context.args or []))
    ocr_ctx = await _resolve_ocr_ctx_59(update, context, reply_msg, uid)
    if not ocr_ctx:
        await warn(update, "No OCR Context", "Reply to an OCR-scanned image/PDF/result first.")
        raise ApplicationHandlerStop

    limit = 500 if is_staff else get_user_gen_limit_61(uid)

    # If explicit count provided, clamp + run directly.
    if count is not None:
        count = max(1, min(int(count), limit))
        status = None
        with contextlib.suppress(Exception):
            status = await update.message.reply_text(ui_box_html("Generating", f"Mode: <b>{h((mode or 'std').upper())}</b>\nCount: <code>{count}</code>", emoji="⏳"), parse_mode=ParseMode.HTML)
        added, dup = await _generate_to_buffer_59(update, context, ocr_ctx, uid, count, mode or "std")
        with contextlib.suppress(Exception):
            if status:
                await status.edit_text(ui_box_html("Generated → Buffer", f"Added: <code>{added}</code>\nDuplicates skipped: <code>{dup}</code>\nBuffered total: <code>{buffer_count(uid)}</code>", emoji="✅"), parse_mode=ParseMode.HTML)
        if added > 0:
            await _send_pb_action_card(context, update.message.chat_id, uid, added)
        raise ApplicationHandlerStop

    tok = uuid.uuid4().hex[:10]
    entry = {"uid": uid, "chat_id": update.message.chat_id, "mode": mode or "", "ocr_ctx": ocr_ctx, "ts": time.time(), "limit": limit, "is_staff": is_staff, "picker_msg_id": None}
    _g59_store(context)[tok] = entry

    if not mode:
        sent = await context.bot.send_message(
            chat_id=update.message.chat_id,
            text=ui_box_html("Generation Mode", "কোন standard এ new unique MCQ বানাবে?", emoji="🧠"),
            parse_mode=ParseMode.HTML,
            reply_markup=_g59_mode_kb(tok),
        )
    else:
        sent = await context.bot.send_message(
            chat_id=update.message.chat_id,
            text=ui_box_html("How many MCQs?", _count_hint_text_61(mode, limit, is_staff), emoji="🔢"),
            parse_mode=ParseMode.HTML,
            reply_markup=_g61_count_kb(tok, limit),
        )
    with contextlib.suppress(Exception):
        entry["picker_msg_id"] = sent.message_id
    raise ApplicationHandlerStop


# Override cb_g59 mode branch so the count keyboard uses the per-user ladder
# and the picker message id is tracked.
try:
    _prev_cb_g59_61 = cb_g59  # type: ignore[name-defined]
except Exception:
    _prev_cb_g59_61 = None

async def cb_g59(update: Update, context: ContextTypes.DEFAULT_TYPE):  # noqa: F811
    q = update.callback_query
    if not q or not q.data:
        return
    parts = q.data.split(":")
    if len(parts) != 4 or parts[0] != "g59":
        return
    action, val, tok = parts[1], parts[2], parts[3]
    entry = _g59_store(context).get(tok)
    if not entry:
        with contextlib.suppress(Exception):
            await q.answer("Expired", show_alert=False)
        raise ApplicationHandlerStop
    uid = int(entry.get("uid") or 0)
    if q.from_user and int(q.from_user.id) != uid:
        with contextlib.suppress(Exception):
            await q.answer("Not for you", show_alert=False)
        raise ApplicationHandlerStop
    if action == "mode":
        is_staff = bool(entry.get("is_staff"))
        limit = int(entry.get("limit") or (500 if is_staff else get_user_gen_limit_61(uid)))
        entry["mode"] = val
        _g59_store(context)[tok] = entry
        with contextlib.suppress(Exception):
            await q.edit_message_text(
                ui_box_html("How many MCQs?", _count_hint_text_61(val, limit, is_staff), emoji="🔢"),
                parse_mode=ParseMode.HTML,
                reply_markup=_g61_count_kb(tok, limit),
            )
        with contextlib.suppress(Exception):
            entry["picker_msg_id"] = q.message.message_id
        raise ApplicationHandlerStop
    if action == "cnt":
        limit = int(entry.get("limit") or 500)
        count = max(1, min(int(val), limit))
        # Re-write val so the inherited handler honours the clamp
        new_data = f"g59:cnt:{count}:{tok}"
        # Reuse previous handler logic for cancel + cnt
    if _prev_cb_g59_61 is None:
        raise ApplicationHandlerStop
    await _prev_cb_g59_61(update, context)


# Override msg_g59_count: enforce user limit + delete picker message.
try:
    _prev_msg_g59_count_61 = msg_g59_count  # type: ignore[name-defined]
except Exception:
    _prev_msg_g59_count_61 = None

async def msg_g59_count(update: Update, context: ContextTypes.DEFAULT_TYPE):  # noqa: F811
    if not update.message or not update.effective_user:
        return
    txt = str(update.message.text or "").strip()
    if not _re61.fullmatch(r"\d{1,4}", txt):
        return
    uid = int(update.effective_user.id)
    state = _g59_store(context)
    tok = None
    newest = -1.0
    for k, v in list(state.items()):
        if int(v.get("uid") or 0) == uid and float(v.get("ts") or 0) > newest:
            tok, newest = k, float(v.get("ts") or 0)
    if not tok:
        return
    entry = state.get(tok) or {}
    is_staff = bool(entry.get("is_staff")) or _is_staff_61(uid)
    limit = int(entry.get("limit") or (500 if is_staff else get_user_gen_limit_61(uid)))
    raw_n = int(txt)
    if raw_n < 1:
        return
    if raw_n > limit:
        with contextlib.suppress(Exception):
            await update.message.reply_text(
                ui_box_html("Limit Exceeded", f"তোমার সর্বোচ্চ লিমিট: <b>{limit}</b>\nএর মধ্যে একটি সংখ্যা দাও।", emoji="🚫"),
                parse_mode=ParseMode.HTML,
            )
        return
    count = raw_n
    mode = str(entry.get("mode") or "std")
    ocr_ctx = dict(entry.get("ocr_ctx") or {})
    chat_id = int(entry.get("chat_id") or update.message.chat_id)
    picker_id = entry.get("picker_msg_id")
    # Delete picker so it doesn't sit around
    if picker_id:
        with contextlib.suppress(Exception):
            await context.bot.delete_message(chat_id=chat_id, message_id=int(picker_id))
    state.pop(tok, None)
    status = None
    with contextlib.suppress(Exception):
        status = await update.message.reply_text(
            ui_box_html("Generating", f"Mode: <b>{h(mode.upper())}</b>\nCount: <code>{count}</code>", emoji="⏳"),
            parse_mode=ParseMode.HTML,
        )
    added, dup = await _generate_to_buffer_59(update, context, ocr_ctx, uid, count, mode)
    with contextlib.suppress(Exception):
        if status:
            await status.edit_text(
                ui_box_html("Generated → Buffer", f"Added: <code>{added}</code>\nDuplicates skipped: <code>{dup}</code>\nBuffered total: <code>{buffer_count(uid)}</code>", emoji="✅"),
                parse_mode=ParseMode.HTML,
            )
    if added > 0:
        await _send_pb_action_card(context, chat_id, uid, added)
    raise ApplicationHandlerStop


# ─── 3. Owner commands ──────────────────────────────────────────────────────

async def cmd_setgenlimit_61(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id if update.effective_user else 0
    if not _is_owner_id(uid):
        with contextlib.suppress(Exception):
            await update.effective_message.reply_text("Owner only.")
        return
    args = list(context.args or [])
    if len(args) < 2:
        with contextlib.suppress(Exception):
            await update.effective_message.reply_text("Usage: .setgenlimit <user_id> <N>\nExample: .setgenlimit 12345678 50")
        return
    try:
        target = int(args[0]); n = int(args[1])
    except Exception:
        with contextlib.suppress(Exception):
            await update.effective_message.reply_text("Invalid user_id or N.")
        return
    set_user_gen_limit_61(target, n)
    with contextlib.suppress(Exception):
        await update.effective_message.reply_text(
            f"✅ user <code>{target}</code> এর .gen লিমিট: <code>{max(1, min(n,500))}</code>",
            parse_mode=ParseMode.HTML,
        )

async def cmd_getgenlimit_61(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id if update.effective_user else 0
    if not _is_owner_id(uid):
        return
    args = list(context.args or [])
    if not args:
        with contextlib.suppress(Exception):
            await update.effective_message.reply_text("Usage: .getgenlimit <user_id>")
        return
    try:
        target = int(args[0])
    except Exception:
        return
    cur = get_user_gen_limit_61(target)
    with contextlib.suppress(Exception):
        await update.effective_message.reply_text(
            f"user_id: <code>{target}</code>\n.gen limit: <code>{cur}</code>",
            parse_mode=ParseMode.HTML,
        )

async def cmd_resetgenlimit_61(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id if update.effective_user else 0
    if not _is_owner_id(uid):
        return
    args = list(context.args or [])
    if not args:
        with contextlib.suppress(Exception):
            await update.effective_message.reply_text("Usage: .resetgenlimit <user_id>")
        return
    try:
        target = int(args[0])
    except Exception:
        return
    clear_user_gen_limit_61(target)
    with contextlib.suppress(Exception):
        await update.effective_message.reply_text(
            f"✅ <code>{target}</code> reset → default <code>{get_user_gen_limit_61(target)}</code>",
            parse_mode=ParseMode.HTML,
        )


_DOT_RE_61 = _re61.compile(r"^\.(setgenlimit|getgenlimit|resetgenlimit)\b\s*(.*)$", _re61.IGNORECASE)

async def _dot_dispatch_61(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if not msg or not msg.text:
        return
    m = _DOT_RE_61.match(msg.text.strip())
    if not m:
        return
    cmd = m.group(1).lower()
    rest = (m.group(2) or "").strip()
    context.args = rest.split() if rest else []
    if cmd == "setgenlimit":
        await cmd_setgenlimit_61(update, context)
    elif cmd == "getgenlimit":
        await cmd_getgenlimit_61(update, context)
    elif cmd == "resetgenlimit":
        await cmd_resetgenlimit_61(update, context)


_prev_build_app_61 = build_app

def build_app() -> Application:
    app = _prev_build_app_61()
    with contextlib.suppress(Exception):
        if "_register_dual_command" in globals():
            _register_dual_command(app, "gen", cmd_gen, group=-500)
        else:
            app.add_handler(CommandHandler("gen", cmd_gen), group=-500)
            app.add_handler(_build_dot_command_handler("gen", cmd_gen), group=-500)
    with contextlib.suppress(Exception):
        app.add_handler(CallbackQueryHandler(cb_g59, pattern=r"^g59:"), group=-500)
    with contextlib.suppress(Exception):
        app.add_handler(MessageHandler(filters.ChatType.PRIVATE & filters.TEXT & ~filters.COMMAND, msg_g59_count), group=-500)
    with contextlib.suppress(Exception):
        app.add_handler(CommandHandler("setgenlimit", cmd_setgenlimit_61))
        app.add_handler(CommandHandler("getgenlimit", cmd_getgenlimit_61))
        app.add_handler(CommandHandler("resetgenlimit", cmd_resetgenlimit_61))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, _dot_dispatch_61), group=-399)
    return app

# ===== END SECTION 61 =====