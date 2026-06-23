"""Stage 3 - render to a print-ready PDF.

The inline tags emitted in stage 2 ([[CALLOUT]], [[TABLE]], [[CHECKLIST]]) are
parsed into styled HTML, wrapped in a paged.css print stylesheet (cover page,
running headers, chapter breaks), and converted to PDF. WeasyPrint is the
default engine; if it is not installed the same HTML is written to disk so the
output is always inspectable.
"""
from __future__ import annotations

import html
import re
from pathlib import Path

from .chapter import Chapter, Section
from .outline import Outline

CALLOUT_RE = re.compile(r"\[\[CALLOUT:(tip|warning|note)\|(.+?)\]\]", re.S)
TABLE_RE = re.compile(r"\[\[TABLE\|(.+?)\]\]", re.S)
CHECKLIST_RE = re.compile(r"\[\[CHECKLIST\|(.+?)\]\]", re.S)

PAGE_CSS = """
@page { size: 6in 9in; margin: 0.75in 0.7in;
  @bottom-center { content: counter(page); font-size: 9pt; color: #666; } }
@page :first { margin: 0; }
body { font-family: Georgia, "Times New Roman", serif; font-size: 11pt; line-height: 1.55; color: #1a1a1a; }
.cover { height: 9in; display: flex; flex-direction: column; justify-content: center;
  align-items: center; text-align: center; background: linear-gradient(160deg,#1f2a44,#0d1226);
  color: #fff; page-break-after: always; }
.cover h1 { font-size: 30pt; margin: 0 0.6in; }
.cover h2 { font-size: 15pt; font-weight: normal; color: #b9c2e0; margin-top: 0.2in; }
.chapter { page-break-before: always; }
.chapter h1 { font-size: 20pt; border-bottom: 2px solid #1f2a44; padding-bottom: 6pt; }
h2.section { font-size: 14pt; color: #1f2a44; margin-top: 16pt; }
.callout { border-left: 4px solid; padding: 8pt 12pt; margin: 10pt 0; border-radius: 4px; }
.callout.tip { border-color:#16a34a; background:#f0fdf4; }
.callout.warning { border-color:#d97706; background:#fffbeb; }
.callout.note { border-color:#2563eb; background:#eff6ff; }
table { border-collapse: collapse; width: 100%; margin: 10pt 0; font-size: 10pt; }
th, td { border: 1px solid #cbd5e1; padding: 5pt 8pt; text-align: left; }
th { background: #1f2a44; color: #fff; }
ul.check { list-style: none; padding-left: 0; }
ul.check li::before { content: "\\2610  "; }
"""


def _render_callout(m: re.Match) -> str:
    kind, text = m.group(1), html.escape(m.group(2).strip())
    return f'<div class="callout {kind}">{text}</div>'


def _render_table(m: re.Match) -> str:
    parts = m.group(1).split("||")
    header = parts[0].split(";")
    rows = [p.split(";") for p in parts[1:]]
    thead = "".join(f"<th>{html.escape(h.strip())}</th>" for h in header)
    body = "".join(
        "<tr>" + "".join(f"<td>{html.escape(c.strip())}</td>" for c in r) + "</tr>" for r in rows
    )
    return f"<table><thead><tr>{thead}</tr></thead><tbody>{body}</tbody></table>"


def _render_checklist(m: re.Match) -> str:
    items = "".join(f"<li>{html.escape(i.strip())}</li>" for i in m.group(1).split(";"))
    return f'<ul class="check">{items}</ul>'


def _to_html(text: str) -> str:
    text = CALLOUT_RE.sub(_render_callout, text)
    text = TABLE_RE.sub(_render_table, text)
    text = CHECKLIST_RE.sub(_render_checklist, text)
    paras = []
    for block in text.split("\n\n"):
        block = block.strip()
        if not block:
            continue
        if block.startswith("<"):
            paras.append(block)
        else:
            paras.append(f"<p>{html.escape(block)}</p>")
    return "\n".join(paras)


def build_html(book: Outline, rendered: list[tuple[Chapter, list[tuple[Section, str]]]]) -> str:
    body = [
        f'<div class="cover"><h1>{html.escape(book.title)}</h1>'
        f'<h2>{html.escape(book.subtitle)}</h2></div>'
    ]
    for ch, sections in rendered:
        body.append(f'<div class="chapter"><h1>Chapter {ch.number}: {html.escape(ch.title)}</h1>')
        for sec, text in sections:
            body.append(f'<h2 class="section">{html.escape(sec.title)}</h2>')
            body.append(_to_html(text))
        body.append("</div>")
    return f"<!doctype html><html><head><meta charset='utf-8'><style>{PAGE_CSS}</style></head><body>{''.join(body)}</body></html>"


def render_pdf(book: Outline, rendered, out_path: str) -> str:
    doc_html = build_html(book, rendered)
    out = Path(out_path)
    try:
        from weasyprint import HTML  # type: ignore

        HTML(string=doc_html).write_pdf(str(out))
        return str(out)
    except ImportError:
        fallback = out.with_suffix(".html")
        fallback.write_text(doc_html, encoding="utf-8")
        return str(fallback)
