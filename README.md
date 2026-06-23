# claude-ebook-generator

A Claude-powered pipeline that turns a single topic into a **200-300 page, print-ready e-book PDF** with consistent voice, structured chapters, and rich visual elements (callout boxes, tables, checklists, recipe cards, cover page).

Built to solve the real problem with long-form AI books: **drift**. Voice, terminology, and facts wander across the dozens of model calls a long book requires. This pipeline keeps them locked with a rolling "story bible" injected into every section call.

## Pipeline

```
topic + book-type template
        │
        ▼
┌─────────────────────┐   strict JSON, validated
│ 1. Outline (Opus)   │   chapters → sections → word budgets
└─────────┬───────────┘
          ▼
┌─────────────────────┐   rolling memory: locked glossary + recap
│ 2. Chapters (Sonnet)│   section-by-section, voice stays consistent
└─────────┬───────────┘   inline tags: [[CALLOUT]] [[TABLE]] [[CHECKLIST]]
          ▼
┌─────────────────────┐   paged.css: cover, running headers, page breaks
│ 3. Render PDF       │   WeasyPrint → print-ready 6x9 PDF
└─────────────────────┘
```

## Why it stays consistent over 250 pages

- **Word-budgeted outline** — each section gets a target so the book lands near the requested page count instead of running short or long.
- **Locked glossary** — seeded per book type, reused verbatim in every section prompt.
- **Rolling recap** — a bounded summary of everything written so far rides along in each call, so chapter 12 still sounds like chapter 1.
- **Portable inline tags** — the model emits `[[TABLE|...]]`, not raw HTML, so the same output renders to PDF, EPUB, or HTML.

## Run it (no API key needed)

```bash
pip install -r requirements.txt
python -m ebook.main --demo --topic "Intermittent Fasting for Beginners" --type guide --out fasting.pdf
```

`--demo` runs fully offline with shaped placeholder text so you can produce a real PDF with zero credits. Drop in `ANTHROPIC_API_KEY` and remove `--demo` for live generation.

## Book types (reusable templates)

| key | book type | visual elements |
|-----|-----------|-----------------|
| `guide` | informational guide | callouts, checklists, summary tables |
| `cookbook` | cookbook | recipe cards, ingredient tables, tip callouts |
| `handbook` | educational handbook | learning objectives, worked examples, comparison tables |
| `resource` | resource guide | resource tables, quick-reference checklists |

New niche or brand = one new `BookTemplate` entry. That is what makes it scalable.

## Project layout

```
ebook/
  outline.py      Stage 1 - structured JSON outline (validated)
  chapter.py      Stage 2 - section generation + rolling BookMemory
  pdf_builder.py  Stage 3 - inline-tag → styled HTML → paged PDF
  templates.py    reusable book-type templates
  llm.py          Claude client + offline demo fallback
  main.py         CLI entry point
```

Demo build — illustrative of architecture and approach.
