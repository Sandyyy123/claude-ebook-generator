"""Thin Claude API client with a deterministic offline fallback.

Real calls use the Anthropic Messages API (claude-opus-4-8 / claude-sonnet-4-6).
When ANTHROPIC_API_KEY is absent (CI, demo, reviewer cloning the repo), every
call returns shaped placeholder text so `python -m ebook.main --demo` still
produces a full PDF without network or credits.
"""
from __future__ import annotations

import os
import textwrap

MODEL_DRAFT = os.getenv("EBOOK_MODEL", "claude-sonnet-4-6")
MODEL_OUTLINE = os.getenv("EBOOK_OUTLINE_MODEL", "claude-opus-4-8")

try:
    import anthropic  # type: ignore

    _HAS_SDK = True
except ImportError:  # pragma: no cover - demo path
    _HAS_SDK = False


def _live(system: str, user: str, max_tokens: int, temperature: float, model: str) -> str:
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    msg = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return "".join(block.text for block in msg.content if block.type == "text")


def _demo(system: str, user: str) -> str:
    """Shaped offline output so the pipeline runs end-to-end with no key."""
    if "JSON" in system or "JSON" in user:
        return (
            '{"title":"The Practical Field Guide","subtitle":"A Demo Build",'
            '"chapters":[{"number":1,"title":"Foundations","summary":"Why this matters.",'
            '"sections":[{"title":"The Core Idea","brief":"Set the frame.","word_budget":900},'
            '{"title":"Common Pitfalls","brief":"What goes wrong.","word_budget":900}]},'
            '{"number":2,"title":"Putting It To Work","summary":"Application.",'
            '"sections":[{"title":"A Repeatable Method","brief":"Steps.","word_budget":900}]}]}'
        )
    return textwrap.fill(
        "This is demo prose generated without an API key so the renderer can be "
        "exercised end to end. In live mode this paragraph is written by Claude "
        "from the section brief, the chapter summary, and a rolling recap of "
        "everything written so far, which is what keeps voice and terminology "
        "consistent across a 250-page book.",
        width=90,
    )


def complete(
    system: str,
    user: str,
    max_tokens: int = 2000,
    temperature: float = 0.7,
    outline: bool = False,
) -> str:
    model = MODEL_OUTLINE if outline else MODEL_DRAFT
    if _HAS_SDK and os.getenv("ANTHROPIC_API_KEY"):
        return _live(system, user, max_tokens, temperature, model)
    return _demo(system, user)
