# ──────────────────────────────────────────────────────────────────────────────
# Section 62 (2026-06-13)
#   Privacy fix: the "🎯 Quiz Actions" card (Post to Channel / Export CSV /
#   Clear Buffer / addchannel tip) is an owner/admin-only surface. Regular
#   users were seeing it after a successful .gen → buffer flow, which exposes
#   private buffer/channel commands. Suppress the card for non-staff users.
#   They still get the "✅ Generated → Buffer" confirmation from .gen.
# ──────────────────────────────────────────────────────────────────────────────

try:
    _prev_send_pb_action_card_62 = _send_pb_action_card  # type: ignore[name-defined]
except Exception:
    _prev_send_pb_action_card_62 = None


def _is_staff_62(uid: int) -> bool:
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


async def _send_pb_action_card(context, chat_id: int, uid: int, added: int):  # noqa: F811
    # Hide the private Quiz Actions card from regular users.
    if not _is_staff_62(int(uid or 0)):
        return
    if _prev_send_pb_action_card_62 is None:
        return
    return await _prev_send_pb_action_card_62(context, chat_id, uid, added)

# ===== END SECTION 62 =====