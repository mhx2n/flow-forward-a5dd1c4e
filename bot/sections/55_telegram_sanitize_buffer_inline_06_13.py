# ──────────────────────────────────────────────────────────────────────────────
# Section: 55_telegram_sanitize_buffer_inline_06_13
# Fixes (all errorless / no-ops on failure):
#   1) Sanitize LaTeX-ish tokens (sqrt{}, hat{}, vec{}, &amp;, Rightarrow,
#      leftharpoons, begin{vmatrix}, text{}, frac{}, etc.) to clean
#      Telegram-friendly plain text — applied ONLY when sending polls.
#      CSV export keeps the raw LaTeX-style text (untouched buffer).
#   2) Do NOT auto-clear buffer after channel post — manual /clear via
#      the action card's 🧹 Clear Buffer button only.
#   3) "🔁 More Generate (+5)" edits the same offer card INLINE — no
#      flood of "More from Page 1" messages. Counts accumulate.
#   4) Stronger MCQ-extraction hint for right-column / side-box answers
#      (e.g. a lone "(b)" on the same row as the question end).
# DO NOT import this file directly — exec'd in shared namespace by bot/__main__.py.
# ──────────────────────────────────────────────────────────────────────────────


# =========================================================================
# 1) Telegram-friendly text sanitizer (LaTeX / HTML-entity / token cleanup)
# =========================================================================

_GREEK_MAP = {
    "alpha": "α", "beta": "β", "gamma": "γ", "delta": "δ", "epsilon": "ε",
    "zeta": "ζ", "eta": "η", "theta": "θ", "iota": "ι", "kappa": "κ",
    "lambda": "λ", "mu": "μ", "nu": "ν", "xi": "ξ", "pi": "π", "rho": "ρ",
    "sigma": "σ", "tau": "τ", "upsilon": "υ", "phi": "φ", "chi": "χ",
    "psi": "ψ", "omega": "ω",
    "Alpha": "Α", "Beta": "Β", "Gamma": "Γ", "Delta": "Δ", "Theta": "Θ",
    "Lambda": "Λ", "Pi": "Π", "Sigma": "Σ", "Phi": "Φ", "Omega": "Ω",
}

_SYMBOL_MAP = {
    "Rightarrow": "⇒", "Leftarrow": "⇐", "Leftrightarrow": "⇔",
    "rightarrow": "→", "leftarrow": "←", "leftrightarrow": "↔",
    "leftharpoons": "⇌", "rightharpoons": "⇌",
    "rightleftharpoons": "⇌", "leftrightharpoons": "⇌",
    "times": "×", "div": "÷", "cdot": "·", "ast": "∗",
    "pm": "±", "mp": "∓",
    "leq": "≤", "geq": "≥", "neq": "≠", "approx": "≈", "equiv": "≡",
    "ll": "≪", "gg": "≫",
    "infty": "∞", "partial": "∂", "nabla": "∇",
    "int": "∫", "sum": "Σ", "prod": "∏",
    "in": "∈", "notin": "∉", "subset": "⊂", "supset": "⊃",
    "cup": "∪", "cap": "∩", "emptyset": "∅",
    "forall": "∀", "exists": "∃",
    "to": "→", "iff": "⇔", "implies": "⇒",
    "circ": "°", "degree": "°",
    "ldots": "…", "cdots": "⋯", "vdots": "⋮", "dots": "…",
    "quad": " ", "qquad": "  ",
}

_HAT_MAP = {
    "i": "î", "j": "ĵ", "k": "k̂", "n": "n̂", "r": "r̂",
    "x": "x̂", "y": "ŷ", "z": "ẑ", "u": "û", "v": "v̂",
}


def _tg_plain_text(s: str) -> str:
    if not s:
        return ""
    t = str(s)
    # HTML entities first
    t = (t.replace("&amp;", "&")
           .replace("&lt;", "<")
           .replace("&gt;", ">")
           .replace("&quot;", '"')
           .replace("&apos;", "'")
           .replace("&nbsp;", " "))
    # Inline math delimiters $...$ and \( \)
    t = re.sub(r"\\\(|\\\)|\\\[|\\\]", "", t)
    t = re.sub(r"\$(.+?)\$", r"\1", t, flags=re.DOTALL)
    # \begin{...} ... \end{...}  → keep inner content, drop wrapper
    t = re.sub(r"\\?begin\s*\{[^}]*\}", "", t)
    t = re.sub(r"\\?end\s*\{[^}]*\}", "", t)
    # Common LaTeX wrappers
    t = re.sub(r"\\?sqrt\s*\{([^{}]*)\}", lambda m: f"√({m.group(1).strip()})", t)
    t = re.sub(r"\\?sqrt\s*\(([^()]*)\)", lambda m: f"√({m.group(1).strip()})", t)
    t = re.sub(r"\\?sqrt\s+([0-9A-Za-zα-ωΑ-Ω]+)", lambda m: f"√{m.group(1)}", t)
    t = re.sub(r"\\?frac\s*\{([^{}]*)\}\s*\{([^{}]*)\}",
               lambda m: f"({m.group(1).strip()})/({m.group(2).strip()})", t)
    t = re.sub(r"\\?hat\s*\{([^{}]*)\}",
               lambda m: _HAT_MAP.get(m.group(1).strip(), m.group(1).strip() + "\u0302"), t)
    t = re.sub(r"\\?vec\s*\{([^{}]*)\}", lambda m: m.group(1).strip() + "\u20d7", t)
    t = re.sub(r"\\?(?:text|mathrm|mathbf|mathit|operatorname)\s*\{([^{}]*)\}",
               lambda m: m.group(1), t)
    t = re.sub(r"\\?(?:overline|underline|bar)\s*\{([^{}]*)\}", lambda m: m.group(1), t)
    # Greek + symbols (with or without leading backslash, word-boundary safe)
    def _greek_repl(m):
        name = m.group(1)
        return _GREEK_MAP.get(name, m.group(0))
    t = re.sub(r"\\?\b(" + "|".join(re.escape(k) for k in _GREEK_MAP.keys()) + r")\b",
               _greek_repl, t)
    def _sym_repl(m):
        name = m.group(1)
        return _SYMBOL_MAP.get(name, m.group(0))
    t = re.sub(r"\\?\b(" + "|".join(re.escape(k) for k in _SYMBOL_MAP.keys()) + r")\b",
               _sym_repl, t)
    # Subscript/superscript braces  _{xyz} → _(xyz), ^{xyz} → ^(xyz)
    t = re.sub(r"_\{([^{}]*)\}", r"_(\1)", t)
    t = re.sub(r"\^\{([^{}]*)\}", r"^(\1)", t)
    # Strip any leftover \word backslash commands
    t = re.sub(r"\\([A-Za-z]+)\s*", r"\1 ", t)
    # Collapse single-token braces  {x} → x
    for _ in range(3):
        t = re.sub(r"\{([^{}]*)\}", r"\1", t)
    # Cleanup whitespace
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\s*\n\s*", "\n", t).strip()
    return t


def _sanitize_item_for_poll(it: Dict[str, Any]) -> Dict[str, Any]:
    o = dict(it or {})
    for k in ("questions", "option1", "option2", "option3", "option4", "option5", "explanation"):
        if k in o and o[k] is not None:
            try:
                o[k] = _tg_plain_text(o.get(k) or "")
            except Exception:
                pass
    return o


# =========================================================================
# 2) Replacement cb_pba — sanitizes polls; does NOT auto-clear buffer
# =========================================================================

_prev_cb_pba_55 = cb_pba


async def cb_pba(update: Update, context: ContextTypes.DEFAULT_TYPE):  # noqa: F811
    q = update.callback_query
    if not q or not q.data:
        return
    parts = q.data.split(":")
    if len(parts) < 3 or parts[0] != "pba":
        return
    action = parts[1]
    # Only intercept the "post" action — delegate the rest to previous impl
    if action != "post":
        await _prev_cb_pba_55(update, context)
        raise ApplicationHandlerStop

    token = parts[-1]
    store = _pb_store(context)
    entry = store.get(token)
    if not entry:
        with contextlib.suppress(Exception):
            await q.answer("Expired", show_alert=False)
        raise ApplicationHandlerStop
    uid = int(entry.get("uid") or 0)
    caller = q.from_user.id if q.from_user else 0
    if caller != uid:
        with contextlib.suppress(Exception):
            await q.answer("Not for you", show_alert=False)
        raise ApplicationHandlerStop
    chat_id = int(entry.get("chat_id") or q.message.chat_id)

    if len(parts) < 4:
        with contextlib.suppress(Exception):
            await q.answer("Bad data")
        raise ApplicationHandlerStop
    try:
        cid = int(parts[2])
    except Exception:
        with contextlib.suppress(Exception):
            await q.answer("Bad channel")
        raise ApplicationHandlerStop
    ch = None
    try:
        ch = channel_get_by_id_for_user(uid, cid)
    except Exception:
        pass
    if not ch:
        with contextlib.suppress(Exception):
            await q.answer("Channel not found", show_alert=True)
        raise ApplicationHandlerStop
    items = buffer_list(uid, limit=MAX_BUFFERED_QUESTIONS) or []
    if not items:
        with contextlib.suppress(Exception):
            await q.answer("Buffer empty", show_alert=True)
        raise ApplicationHandlerStop
    with contextlib.suppress(Exception):
        await q.answer(f"Posting {len(items)}…")
    with contextlib.suppress(Exception):
        await q.edit_message_text(
            ui_box_html("Posting to Channel",
                        f"<b>{h(ch.title)}</b>\nPosting <code>{len(items)}</code> quiz(es)…",
                        emoji="📤"),
            parse_mode=ParseMode.HTML,
        )
    target_chat_id = ch.channel_chat_id
    _reply_kw: Dict[str, Any] = {}
    try:
        _anchor_chat, _anchor_msg = _get_topic_anchor(uid)
        if _anchor_msg:
            if _anchor_chat == target_chat_id:
                _reply_kw = _make_reply_params(_anchor_msg)
            else:
                _reply_kw = _make_reply_params(_anchor_msg, chat_id=_anchor_chat)
    except Exception:
        _reply_kw = {}

    posted = 0
    failed = 0
    ch_prefix = (getattr(ch, "prefix", "") or "").strip()
    for _, raw_it in items:
        try:
            it = _sanitize_item_for_poll(raw_it)  # Telegram-friendly only
            opts: List[str] = []
            for k in ("option1", "option2", "option3", "option4", "option5"):
                v = str(it.get(k) or "").strip()
                if v:
                    opts.append(v)
            ans = int(it.get("answer", 0) or 0)
            if not (1 <= ans <= len(opts)):
                failed += 1
                continue
            qtext = str(it.get("questions") or "").strip()
            if ch_prefix and not qtext.startswith(ch_prefix):
                qtext = f"{ch_prefix}\n{qtext}"
            expl = ""
            if explain_mode_on(uid):
                expl = _trim_expl_for_poll(str(it.get("explanation") or ""))
            kw: Dict[str, Any] = dict(
                chat_id=target_chat_id,
                question=qtext[:300],
                options=opts[:10],
                type=Poll.QUIZ,
                correct_option_id=ans - 1,
                is_anonymous=True,
                explanation=expl if expl else None,
                explanation_parse_mode=ParseMode.HTML if expl else None,
            )
            if _reply_kw:
                kw.update(_reply_kw)
            await context.bot.send_poll(**kw)
            posted += 1
            await asyncio.sleep(0.4)
        except RetryAfter as ra:
            await asyncio.sleep(float(getattr(ra, "retry_after", 2)) + 1.0)
        except Exception as e:
            failed += 1
            db_log("WARN", "pba_post_failed_v55", {"user_id": uid, "error": str(e)})
    # IMPORTANT: do NOT clear buffer — manual clear via 🧹 button only.
    with contextlib.suppress(Exception):
        await context.bot.send_message(
            chat_id=chat_id,
            text=ui_box_html(
                "✅ Posted",
                f"Channel: <b>{h(ch.title)}</b>\n"
                f"Posted: <code>{posted}</code>\n"
                f"Failed: <code>{failed}</code>\n"
                f"Buffer kept: <code>{buffer_count(uid)}</code> (use 🧹 Clear Buffer to wipe).",
                emoji="📤",
            ),
            parse_mode=ParseMode.HTML,
        )
    raise ApplicationHandlerStop


# =========================================================================
# 3) "🔁 More Generate" → inline edit of the offer card (no message flood)
# =========================================================================

_prev_cb_genq_55 = cb_genq


async def cb_genq(update: Update, context: ContextTypes.DEFAULT_TYPE):  # noqa: F811
    q = update.callback_query
    if not q or not q.data:
        return
    parts = q.data.split(":")
    if len(parts) != 3 or parts[0] != "genq" or parts[1] != "mo":
        return await _prev_cb_genq_55(update, context)

    token = parts[2]
    store = _genq_store(context)
    entry = store.get(token)
    if not entry:
        with contextlib.suppress(Exception):
            await q.answer("Expired", show_alert=False)
        raise ApplicationHandlerStop
    uid = int(entry.get("uid") or 0)
    caller = q.from_user.id if q.from_user else 0
    if caller != uid:
        with contextlib.suppress(Exception):
            await q.answer("Not for you", show_alert=False)
        raise ApplicationHandlerStop
    text = str(entry.get("text") or "")
    page_idx = int(entry.get("page") or 0)
    counts = entry.get("counts") or {"easy": 0, "medium": 0, "hard": 0}
    seen: set = set(entry.get("seen_fp") or set())
    total_added_so_far = int(entry.get("more_added", 0) or 0)

    hint = ""
    if seen:
        hint = ("\n\n[STRICT: generate ONLY NEW unique MCQs, do NOT repeat any prior "
                "question, vary angle/sub-topic/wording.]")
    seed_text = (text + hint)[:6000]

    with contextlib.suppress(Exception):
        await q.answer("Generating more…")
    # Inline status — edit the same card
    with contextlib.suppress(Exception):
        await q.edit_message_text(
            ui_box_html(
                f"Generating MORE — Page {page_idx}",
                f"Producing 5 new unique MCQ(s)…\nPrior unique added: <code>{total_added_so_far}</code>",
                emoji="🔁",
            ),
            parse_mode=ParseMode.HTML,
        )

    try:
        items = await _run_blocking(
            _role_of(uid),
            _generate_mcqs_from_content,
            seed_text,
            easy=2, medium=2, hard=1,
            timeout=120,
        )
    except Exception as e:
        db_log("ERROR", "genq_more_failed_v55", {"user_id": uid, "error": str(e)})
        items = []

    added = 0
    for p in items or []:
        try:
            fp = _fp_question(p)
        except Exception:
            fp = uuid.uuid4().hex
        if fp in seen:
            continue
        if buffer_count(uid) >= MAX_BUFFERED_QUESTIONS:
            break
        pp = dict(p)
        if not explain_mode_on(uid):
            pp["explanation"] = ""
        try:
            buffer_add(uid, pp)
        except Exception:
            continue
        seen.add(fp)
        added += 1
    total_added_so_far += added
    entry["seen_fp"] = seen
    entry["more_added"] = total_added_so_far
    store[token] = entry

    # Restore the offer card inline with updated stats + buttons
    body = (
        f"📄 Page <code>{page_idx}</code>\n\n"
        f"Last batch added: <code>{added}</code> new unique MCQ(s)\n"
        f"Total MORE generated: <code>{total_added_so_far}</code>\n"
        f"Buffered now: <code>{buffer_count(uid)}</code>\n\n"
        "Tap 🔁 More Generate again, or use the action card to post / export."
    )
    with contextlib.suppress(Exception):
        await q.edit_message_text(
            ui_box_html(f"Generate from Page {page_idx}?", body, emoji="🧠"),
            parse_mode=ParseMode.HTML,
            reply_markup=_genq_kb(token, counts),
        )
    raise ApplicationHandlerStop


# =========================================================================
# 4) Stronger MCQ extraction — side-column answer hint
# =========================================================================

_prev_extract_mcq_items_master_55 = _extract_mcq_items_master

_SIDE_BOX_HINT = (
    "\n[SIDE-COLUMN ANSWER HINT]\n"
    "The OCR text may include answers that originally appeared in small RIGHT-SIDE BOXES,\n"
    "or as a lone letter such as '(b)', '(d)', 'b', 'd', '⓭' on its own line\n"
    "immediately after a question's last option. Treat such isolated letters as the\n"
    "correct-answer marker for the IMMEDIATELY PRECEDING MCQ on the same row/page.\n"
    "Match them by position (top-to-bottom). Never invent an answer — only use the\n"
    "marker if visually plausible.\n"
)


def _extract_mcq_items_master(chunk_text: str) -> List[Dict[str, Any]]:  # noqa: F811
    try:
        augmented = (_SIDE_BOX_HINT + "\n" + (chunk_text or "")).strip()
    except Exception:
        augmented = chunk_text or ""
    return _prev_extract_mcq_items_master_55(augmented)


# =========================================================================
# 5) Register handlers in a HIGH-PRIORITY group so they win over older ones
# =========================================================================

_prev_build_app_55 = build_app


def build_app() -> Application:
    app = _prev_build_app_55()
    # group=-1 → runs BEFORE the default group-0 handlers from sections 53/54.
    # Each new handler raises ApplicationHandlerStop after handling its case.
    with contextlib.suppress(Exception):
        app.add_handler(
            CallbackQueryHandler(cb_pba, pattern=r"^pba:(post|csv|clr|list|close):.+$"),
            group=-1,
        )
    with contextlib.suppress(Exception):
        app.add_handler(
            CallbackQueryHandler(cb_genq, pattern=r"^genq:(go|re|no|ge|gm|gh|mo):[0-9a-f]+$"),
            group=-1,
        )
    return app

# ===== END TELEGRAM SANITIZE + BUFFER + INLINE MORE-GENERATE =====