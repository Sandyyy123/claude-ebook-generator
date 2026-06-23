"""CLI entry point: topic -> outline -> chapters -> print-ready PDF.

    python -m ebook.main --topic "Intermittent Fasting for Beginners" \
        --type guide --pages 220 --out fasting.pdf

Runs fully offline with --demo (no API key, no credits) so a reviewer can clone
and produce a real PDF in one command.
"""
from __future__ import annotations

import argparse
import sys

from .chapter import write_book
from .outline import build_outline
from .pdf_builder import render_pdf
from .templates import TEMPLATES, get_template


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Claude-powered e-book generator")
    p.add_argument("--topic", default="A Practical Field Guide", help="book topic")
    p.add_argument("--type", default="guide", choices=list(TEMPLATES), help="book template")
    p.add_argument("--pages", type=int, default=250, help="target page count")
    p.add_argument("--out", default="ebook.pdf", help="output PDF path")
    p.add_argument("--demo", action="store_true", help="force offline demo mode")
    args = p.parse_args(argv)

    if args.demo:
        import os

        os.environ.pop("ANTHROPIC_API_KEY", None)
        args.pages = min(args.pages, 12)  # keep the demo fast

    tpl = get_template(args.type)
    print(f"[1/3] Outlining '{args.topic}' as a {tpl.label} (~{args.pages} pages)...")
    outline = build_outline(args.topic, tpl, args.pages)
    print(f"      {len(outline.chapters)} chapters, est. {outline.est_pages} pages, "
          f"{outline.total_words} words budgeted.")

    print("[2/3] Writing chapters section by section (rolling memory on)...")
    rendered = write_book(outline, tpl)
    n_sections = sum(len(s) for _, s in rendered)
    print(f"      {n_sections} sections written.")

    print("[3/3] Rendering print-ready PDF...")
    path = render_pdf(outline, rendered, args.out)
    print(f"Done -> {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
