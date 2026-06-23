"""Stage 2 - section-by-section chapter generation with a rolling memory.

The consistency problem in a 250-page book is drift: voice, terminology and
facts wander over dozens of independent calls. We fix it with a compact running
"story bible" - a rolling recap plus a locked glossary - injected into every
section prompt. Each section is generated against its brief, its chapter
summary, and that shared memory, so chapter 12 still sounds like chapter 1.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .llm import complete
from .outline import Chapter, Outline, Section
from .templates import BookTemplate


@dataclass
class BookMemory:
    """Shared state threaded through every section call."""

    glossary: dict[str, str] = field(default_factory=dict)
    recap: str = ""

    def update(self, chapter_title: str, section_title: str, text: str) -> None:
        # Keep the recap bounded; we summarize rather than accumulate raw text.
        tail = text.strip().split(".")
        snippet = ".".join(tail[:2]).strip()
        self.recap = (self.recap + f" [{chapter_title}/{section_title}] {snippet}.")[-1800:]


SECTION_SYSTEM = (
    "You are a single author writing one continuous non-fiction book. Maintain a "
    "consistent voice, reuse the locked glossary terms exactly, and never "
    "re-introduce concepts already covered. Write clean prose; mark any callout, "
    "table or checklist with the inline tags described."
)

# Inline tags the renderer understands. Asking Claude for tags (not raw HTML)
# keeps the model output portable across PDF, EPUB and HTML back-ends.
TAG_GUIDE = (
    "Use [[CALLOUT:type|text]] for tips/warnings (type = tip|warning|note), "
    "[[TABLE|header1;header2||r1c1;r1c2||r2c1;r2c2]] for tables, and "
    "[[CHECKLIST|item1;item2;item3]] for checklists. Otherwise write plain paragraphs."
)


def _section_prompt(book: Outline, ch: Chapter, sec: Section, mem: BookMemory) -> str:
    glossary = "; ".join(f"{k}={v}" for k, v in mem.glossary.items()) or "(none yet)"
    return (
        f"Book: {book.title} - {book.subtitle}\n"
        f"Chapter {ch.number}: {ch.title} - {ch.summary}\n"
        f"Section: {sec.title}\nBrief: {sec.brief}\n"
        f"Target length: ~{sec.word_budget} words.\n\n"
        f"Locked glossary (reuse verbatim): {glossary}\n"
        f"Recap of the book so far: {mem.recap or '(this is the opening)'}\n\n"
        f"{TAG_GUIDE}\n\nWrite the section now."
    )


def write_section(book: Outline, ch: Chapter, sec: Section, mem: BookMemory) -> str:
    text = complete(
        system=SECTION_SYSTEM,
        user=_section_prompt(book, ch, sec, mem),
        max_tokens=max(1200, int(sec.word_budget * 1.6)),
        temperature=0.7,
    )
    mem.update(ch.title, sec.title, text)
    return text


def write_book(book: Outline, tpl: BookTemplate) -> list[tuple[Chapter, list[tuple[Section, str]]]]:
    mem = BookMemory(glossary=dict(tpl.glossary))
    rendered: list[tuple[Chapter, list[tuple[Section, str]]]] = []
    for ch in book.chapters:
        sections = [(sec, write_section(book, ch, sec, mem)) for sec in ch.sections]
        rendered.append((ch, sections))
    return rendered
