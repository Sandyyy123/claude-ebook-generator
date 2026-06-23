"""Stage 1 - structured outline generation.

Given a topic and a book-type template, ask Claude for a strict JSON outline:
chapters -> sections, with a target word budget per section so the whole book
lands near the requested page count. The schema is validated before any chapter
is written, so a malformed outline never propagates into a 250-page render.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field

from .llm import complete
from .templates import BookTemplate

# ~450 rendered words per page is a reliable print average for 6x9 trade books.
WORDS_PER_PAGE = 450


@dataclass
class Section:
    title: str
    brief: str
    word_budget: int


@dataclass
class Chapter:
    number: int
    title: str
    summary: str
    sections: list[Section] = field(default_factory=list)


@dataclass
class Outline:
    title: str
    subtitle: str
    chapters: list[Chapter]

    @property
    def total_words(self) -> int:
        return sum(s.word_budget for c in self.chapters for s in c.sections)

    @property
    def est_pages(self) -> int:
        return round(self.total_words / WORDS_PER_PAGE)


OUTLINE_SYSTEM = (
    "You are a non-fiction book architect. You return ONLY valid JSON matching the "
    "requested schema. No prose, no markdown fences."
)


def _prompt(topic: str, tpl: BookTemplate, target_pages: int) -> str:
    target_words = target_pages * WORDS_PER_PAGE
    return (
        f"Design a complete outline for a {tpl.label} titled around the topic: "
        f"\"{topic}\".\n"
        f"Target length: ~{target_pages} pages (~{target_words} words).\n"
        f"Audience and tone: {tpl.tone}.\n"
        f"Required structural elements for this book type: {', '.join(tpl.elements)}.\n\n"
        "Return JSON with this exact shape:\n"
        "{\n"
        '  "title": str, "subtitle": str,\n'
        '  "chapters": [\n'
        '    {"number": int, "title": str, "summary": str,\n'
        '     "sections": [{"title": str, "brief": str, "word_budget": int}]}\n'
        "  ]\n"
        "}\n"
        "Distribute word_budget so the sum is close to the target. "
        "Use 8-14 chapters, 3-6 sections each."
    )


def build_outline(topic: str, tpl: BookTemplate, target_pages: int = 250) -> Outline:
    raw = complete(
        system=OUTLINE_SYSTEM,
        user=_prompt(topic, tpl, target_pages),
        max_tokens=4000,
        temperature=0.4,
    )
    data = json.loads(_strip_fences(raw))
    chapters = [
        Chapter(
            number=c["number"],
            title=c["title"],
            summary=c["summary"],
            sections=[Section(**s) for s in c["sections"]],
        )
        for c in data["chapters"]
    ]
    return Outline(title=data["title"], subtitle=data.get("subtitle", ""), chapters=chapters)


def _strip_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0]
    return text.strip()
