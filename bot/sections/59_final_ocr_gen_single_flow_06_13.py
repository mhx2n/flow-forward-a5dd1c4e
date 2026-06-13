# ──────────────────────────────────────────────────────────────────────────────
# Section: 59_final_ocr_gen_single_flow_06_13
# Final single-flow override:
#   • one OCR result card only (no duplicate action-card spam)
#   • source-image MCQs stay selectable separately for CSV/channel post
#   • missing answers are AI-verified before buffering
#   • .gen / .gen med|eng|engg|ver|std [N] uses a direct, non-forged flow
# DO NOT import directly — exec'd in shared namespace by bot/__main__.py.
# ──────────────────────────────────────────────────────────────────────────────

_SRC_STORE_59_KEY = "_source_mcq_action_store_59"
_GEN59_STORE_KEY = "_pending_gen_flow_59"


def _src_store_59(context) -> Dict[str, Any]:
    bd = context.application.bot_data
    if _SRC_STORE_59_KEY not in bd:
        bd[_SRC_STORE_59_KEY] = {}
    return bd[_SRC_STORE_59_KEY]


def _g59_store(context) -> Dict[str, Any]:
    bd = context.application.bot_data
    if _GEN59_STORE_KEY not in bd:
        bd[_GEN59_STORE_KEY] = {}
    return bd[_GEN59_STORE_KEY]


def _mode_count_59(text: str, args) -> Tuple[Optional[str], Optional[int], List[str]]:
    raw = str(text or "").strip().lower()
    toks = [str(x or "").strip().lower() for x in (args or []) if str(x or "").strip()]
    if not toks:
        parts = re.split(r"\s+", raw)
        toks = [p for p in parts[1:] if p] if parts and re.match(r"^[./]?gen(?:@\w+)?$", parts[0]) else []
    alias = {
        "med": "med", "medical": "med", "mbbs": "med", "dental": "med",
        "eng": "eng", "engg": "eng", "engineering": "eng", "buet": "eng",
        "ver": "ver", "versity": "ver", "varsity": "ver", "university": "ver", "univ": "ver",
        "std": "std", "standard": "std", "hsc": "std",
    }
    mode = None
    cleaned: List[str] = []
    count = None
    for t in toks:
        tt = re.sub(r"[^0-9a-z]+", "", t)
        if tt in alias:
            mode = alias[tt]
            continue
        m = re.search(r"\d{1,4}", tt)
        if m and count is None:
            count = max(1, min(500, int(m.group(0))))
            cleaned.append(str(count))
            continue
        cleaned.append(t)
    return mode, count, cleaned


def _source_hash_59(ocr_ctx: Dict[str, Any], mode: str = "std") -> str:
    try:
        base = _ocr_source_hash(ocr_ctx)
    except Exception:
        base = hashlib.md5(str(ocr_ctx or {}).encode("utf-8", "ignore")).hexdigest()
    return f"{mode}:{base}"


def _opts_59(it: Dict[str, Any]) -> List[str]:
    return [str((it or {}).get(f"option{i}") or "").strip() for i in range(1, 6) if str((it or {}).get(f"option{i}") or "").strip()]


def _apply_visible_answer_marks_59(it: Dict[str, Any]) -> Dict[str, Any]:
    o = dict(it or {})
    opts = _opts_59(o)
    if not opts:
        return o
    if int(o.get("answer", 0) or 0) <= 0:
        for idx, opt in enumerate(opts, start=1):
            if re.search(r"(^|\s)(?:✓|✔|✅|☑|⊙|●|◉|\[\s*ans\s*\])", opt, flags=re.I):
                o["answer"] = idx
                break
    for idx, opt in enumerate(opts, start=1):
        clean = re.sub(r"(?:✓|✔|✅|☑|⊙|●|◉)", "", opt).strip()
        o[f"option{idx}"] = clean
    return o


def _ai_fill_missing_answers_59(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out = [_apply_visible_answer_marks_59(dict(x or {})) for x in (items or [])]
    missing = []
    for idx, it in enumerate(out):
        opts = _opts_59(it)
        ans = int(it.get("answer", 0) or 0)
        if opts and not (1 <= ans <= len(opts)):
            missing.append((idx, it, opts))
    if not missing:
        return out
    payload = []
    for idx, it, opts in missing[:80]:
        payload.append({"idx": idx, "q": str(it.get("questions") or "")[:600], "options": opts[:5]})
    prompt = (
        "Return STRICT JSON only. Solve the MCQs and choose the correct option. "
        "Use Bangladesh HSC/admission-level science knowledge when needed. "
        "If the printed answer mark is absent, infer the academically correct answer from the question/options. "
        "JSON: {\"answers\":[{\"idx\":0,\"answer\":1,\"explanation\":\"short reason\"}]}\n\n"
        f"MCQS:\n{json.dumps(payload, ensure_ascii=False)}"
    )
    raw = None
    try:
        if GEMINI_API_KEYS:
            raw = call_gemini_text_rest(prompt, timeout_seconds=35, force_json=True)
    except Exception:
        raw = None
    if not raw:
        with contextlib.suppress(Exception):
            raw = gemini3_solve(prompt)
    data = None
    if raw:
        with contextlib.suppress(Exception):
            data = _extract_json_strict(raw)
    if isinstance(data, dict):
        for row in data.get("answers") or []:
            try:
                idx = int(row.get("idx"))
                ans = int(row.get("answer"))
                opts = _opts_59(out[idx])
                if 0 <= idx < len(out) and 1 <= ans <= len(opts):
                    out[idx]["answer"] = ans
                    if not str(out[idx].get("explanation") or "").strip():
                        out[idx]["explanation"] = _hard_trim_expl(str(row.get("explanation") or "AI verified answer.")) if "_hard_trim_expl" in globals() else str(row.get("explanation") or "AI verified answer.")[:180]
                    out[idx]["answer_checked"] = "ai"
            except Exception:
                continue
    # Last safety: a quiz poll cannot be posted without a correct_option_id.
    # This path should rarely run; it keeps export/post flows from breaking.
    for it in out:
        opts = _opts_59(it)
        ans = int(it.get("answer", 0) or 0)
        if opts and not (1 <= ans <= len(opts)):
            it["answer"] = 1
            it.setdefault("explanation", "AI answer check unavailable; please verify.")
    return out


def _clean_source_items_59(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    checked = _ai_fill_missing_answers_59(items or [])
    out: List[Dict[str, Any]] = []
    seen = set()
    for raw in checked:
        it = dict(raw or {})
        q = str(it.get("questions") or "").strip()
        opts = _opts_59(it)
        ans = int(it.get("answer", 0) or 0)
        if not q or len(opts) < 2 or not (1 <= ans <= len(opts)):
            continue
        if re.search(r"(উদ্দীপক|উদ্দীপকের|নিচের\s*চিত্র|উপরের\s*আলোকে|তথ্যের\s*আলোকে)", q):
            continue
        for i in range(5):
            it[f"option{i+1}"] = opts[i] if i < len(opts) else ""
        it["answer"] = ans
        it["type"] = int(it.get("type", 1) or 1)
        it["section"] = int(it.get("section", 1) or 1)
        it["source"] = "ocr_source_checked"
        with contextlib.suppress(Exception):
            it = _enforce_option_parity(it)
        fp = _fp_question(it) if "_fp_question" in globals() else hashlib.md5(q.lower().encode("utf-8", "ignore")).hexdigest()
        if fp in seen:
            continue
        seen.add(fp)
        out.append(it)
    return out


def _estimate_counts_fast_59(source_count: int, text: str = "") -> Dict[str, int]:
    n = max(0, int(source_count or 0))
    if n <= 0:
        base = 5 if len(str(text or "")) > 500 else 0
        return {"easy": max(0, base // 3), "medium": max(0, base // 3), "hard": max(0, base - 2 * (base // 3)), "ocr_checked": 0, "source_checked": 0}
    easy = max(1, round(n * 0.35))
    medium = max(1, round(n * 0.45))
    hard = max(0, n - easy - medium)
    return {"easy": easy, "medium": medium, "hard": hard, "ocr_checked": n, "source_checked": n}


def _genq_kb_59(token: str, counts: Dict[str, int]) -> InlineKeyboardMarkup:
    e, m, hd = int(counts.get("easy", 0)), int(counts.get("medium", 0)), int(counts.get("hard", 0))
    src = int(counts.get("source_checked", counts.get("ocr_checked", 0)) or 0)
    total = e + m + hd
    rows: List[List[InlineKeyboardButton]] = []
    first: List[InlineKeyboardButton] = []
    if total > 0:
        first.append(InlineKeyboardButton(f"✅ Generate ({total})", callback_data=f"genq:go:{token}"))
    if src > 0:
        first.append(InlineKeyboardButton(f"📌 Source MCQ ({src})", callback_data=f"genq:src:{token}"))
    if first:
        rows.append(first)
    diff: List[InlineKeyboardButton] = []
    if e > 0:
        diff.append(InlineKeyboardButton(f"🟢 Easy ({e})", callback_data=f"genq:ge:{token}"))
    if m > 0:
        diff.append(InlineKeyboardButton(f"🟡 Medium ({m})", callback_data=f"genq:gm:{token}"))
    if hd > 0:
        diff.append(InlineKeyboardButton(f"🔴 Hard ({hd})", callback_data=f"genq:gh:{token}"))
    if diff:
        rows.append(diff)
    rows.append([InlineKeyboardButton("🔁 More Generate (+5)", callback_data=f"genq:mo:{token}")])
    rows.append([InlineKeyboardButton("🔄 Re-check", callback_data=f"genq:re:{token}"), InlineKeyboardButton("🚫 Skip", callback_data=f"genq:no:{token}")])
    return InlineKeyboardMarkup(rows)


globals()["_genq_kb"] = _genq_kb_59
