import re


def format_response(text: str) -> str:
    """Post-processes Ollama output for clean, consistent Markdown formatting.

    This is a pure text transformation — it does NOT call any AI service.
    It runs after Ollama responds and is safe to use with streaming
    (applied to the fully accumulated text before saving to DB).
    """
    if not text:
        return ""

    # ── 1. Fix escaped newlines (some models output \\n as literal text) ──
    text = text.replace("\\n", "\n")

    # ── 2. Strip model reasoning / artifact tags ───────────────────────────
    # e.g. <think>...</think> emitted by reasoning-enabled Ollama models
    text = re.sub(r"<think>[\s\S]*?</think>", "", text, flags=re.IGNORECASE)
    # e.g. <|im_end|>, <|eot_id|> etc.
    text = re.sub(r"<\|[^|]*\|>", "", text)

    # ── 3. Normalize non-standard bullet characters → standard hyphen ──────
    text = re.sub(r"^[•▪○◦◆▸►➤✦✧]\s+", "- ", text, flags=re.MULTILINE)

    # ── 4. Fix bold markers with extra internal spaces: ** x ** → **x** ───
    text = re.sub(r"\*\*\s+(.+?)\s+\*\*", r"**\1**", text)

    # ── 5. Ensure code fence language tag is followed by a newline ─────────
    # Fixes: ```python def foo(): → ```python\ndef foo():
    text = re.sub(r"```(\w+)([^\n])", r"```\1\n\2", text)

    # ── 6. Collapse 3+ consecutive blank lines → max 2 ────────────────────
    text = re.sub(r"\n{3,}", "\n\n", text)

    # ── 7. Ensure a blank line before headings (improves Markdown rendering)
    text = re.sub(r"([^\n])\n(#{1,4} )", r"\1\n\n\2", text)

    return text.strip()
