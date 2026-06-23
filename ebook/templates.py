"""Reusable book-type templates.

Each template encodes the structural DNA of a book category: tone, the visual
elements the client asked for (tables, recipes, callouts), and a seed glossary
so terminology is locked from page one. New niches = new BookTemplate entries,
which is what makes the system scalable across brands.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class BookTemplate:
    key: str
    label: str
    tone: str
    elements: list[str]
    glossary: dict[str, str] = field(default_factory=dict)


TEMPLATES: dict[str, BookTemplate] = {
    "guide": BookTemplate(
        key="guide",
        label="informational guide",
        tone="clear, authoritative, reader-friendly for a general audience",
        elements=["callout boxes", "checklists", "summary tables", "key-takeaway boxes"],
    ),
    "cookbook": BookTemplate(
        key="cookbook",
        label="cookbook",
        tone="warm, practical, encouraging home cooks",
        elements=["recipe cards", "ingredient tables", "step checklists", "tip callouts"],
        glossary={"mise en place": "ingredients prepped and measured before cooking"},
    ),
    "handbook": BookTemplate(
        key="handbook",
        label="educational handbook",
        tone="instructional, structured, suitable for students and trainees",
        elements=["learning objectives", "worked examples", "review checklists", "comparison tables"],
    ),
    "resource": BookTemplate(
        key="resource",
        label="resource guide",
        tone="concise, scannable, reference-oriented",
        elements=["resource tables", "quick-reference checklists", "callout highlights"],
    ),
}


def get_template(key: str) -> BookTemplate:
    if key not in TEMPLATES:
        raise KeyError(f"Unknown template '{key}'. Available: {', '.join(TEMPLATES)}")
    return TEMPLATES[key]
