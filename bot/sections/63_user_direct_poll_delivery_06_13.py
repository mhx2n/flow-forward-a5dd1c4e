# ──────────────────────────────────────────────────────────────────────────────
# Section 63 (2026-06-13)
#   Regular users শুধু .gen চালালে সরাসরি কুইজ পোল পাবে inbox এ — কোনো
#   buffer/action-card flow নয়। Staff (owner/admin) আগের মতোই buffer + action
#   card পায়। Telegram rate-limit এড়াতে polls 2s gap এ পাঠানো হয়।
# ──────────────────────────────────────────────────────────────────────────────

import asyncio as _aio63
import contextlib as _ctx63


def _is_staff_63(uid: int) -> bool:
    try:
        if is_owner(int(uid)):
            return True
    except Exception:
        pass
    try:
        if is_admin(int(uid)):
            return True
    except Exception:
        pass
    return False


async def _send_user_polls_63(context, chat_id: int, uid: int) -> int:
    """Drain this user's buffer and send polls directly to their chat."""
    try:
        items = buffer_list(uid, limit=9999) or []
    except Exception:
        items = []
    if not items:
        return 0
    sent = 0
    ids_to_remove: List[int] = []
    for bid, raw in items:
        ids_to_remove.append(int(bid))
        try:
            it = _sanitize_item_for_poll(raw) if "_sanitize_item_for_poll" in globals() else dict(raw or {})
            opts = _opts_59(it)[:10]
            ans = int(it.get("answer", 0) or 0)
            if len(opts) < 2 or not (1 <= ans <= len(opts)):
                continue
            qtext = str(it.get("questions") or "").strip()
            expl = ""
            try:
                if explain_mode_on(uid):
                    expl = _trim_expl_for_poll(str(it.get("explanation") or ""))
            except Exception:
                expl = ""
            kw = dict(
                chat_id=chat_id,
                question=qtext[:300],
                options=opts,
                type=Poll.QUIZ,
                correct_option_id=ans - 1,
                is_anonymous=False,
                explanation=expl if expl else None,
                explanation_parse_mode=ParseMode.HTML if expl else None,
            )
            await context.bot.send_poll(**kw)
            sent += 1
            await _aio63.sleep(2.0)
        except RetryAfter as ra:
            await _aio63.sleep(float(getattr(ra, "retry_after", 2)) + 1.0)
            with _ctx63.suppress(Exception):
                await context.bot.send_poll(**kw)
                sent += 1
        except Exception as e:
            with _ctx63.suppress(Exception):
                db_log("WARN", "user_direct_poll_63_failed", {"user_id": uid, "error": str(e)})
    with _ctx63.suppress(Exception):
        buffer_remove_ids(uid, ids_to_remove)
    return sent


try:
    _prev_send_pb_action_card_63 = _send_pb_action_card  # type: ignore[name-defined]
except Exception:
    _prev_send_pb_action_card_63 = None


async def _send_pb_action_card(context, chat_id: int, uid: int, added: int):  # noqa: F811
    # Staff → keep the original action card flow.
    if _is_staff_63(int(uid or 0)):
        if _prev_send_pb_action_card_63 is None:
            return
        return await _prev_send_pb_action_card_63(context, chat_id, uid, added)
    # Regular user → directly deliver polls and skip the action card.
    try:
        sent = await _send_user_polls_63(context, int(chat_id), int(uid))
    except Exception as e:
        with _ctx63.suppress(Exception):
            db_log("WARN", "user_direct_poll_63_outer", {"user_id": uid, "error": str(e)})
        sent = 0
    with _ctx63.suppress(Exception):
        if sent > 0:
            await context.bot.send_message(
                chat_id=chat_id,
                text=ui_box_html("Quiz Delivered", f"পাঠানো হলো: <code>{sent}</code> টি কুইজ", emoji="🎯"),
                parse_mode=ParseMode.HTML,
            )

# ===== END SECTION 63 =====