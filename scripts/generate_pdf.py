#!/usr/bin/env python3
"""Generate a styled PDF from the E.G.G.S. Markdown handbook."""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    KeepTogether,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / "content" / "handbook.md"
DEFAULT_OUTPUT = ROOT / "dist" / "EGGS_Operations_Handbook.pdf"

INK = colors.HexColor("#20272A")
ORANGE = colors.HexColor("#F28C28")
DARK_ORANGE = colors.HexColor("#B9561B")
CREAM = colors.HexColor("#FFF8E8")
PALE = colors.HexColor("#F3E7D0")
STEEL = colors.HexColor("#52636A")
TEAL = colors.HexColor("#277A78")
LIGHT_TEAL = colors.HexColor("#DCEDEC")
WHITE = colors.white


def inline_markup(text: str) -> str:
    """Convert a small, safe subset of inline Markdown to ReportLab markup."""
    placeholders: list[str] = []

    def stash(value: str) -> str:
        placeholders.append(value)
        return f"@@MARKUP{len(placeholders) - 1}@@"

    text = re.sub(
        r"\[([^\]]+)\]\((https?://[^)]+)\)",
        lambda m: stash(
            f'<link href="{escape(m.group(2), {"\"": "&quot;"})}" '
            f'color="#277A78"><u>{escape(m.group(1))}</u></link>'
        ),
        text,
    )
    text = escape(text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"`([^`]+)`", r"<font name='Courier'>\1</font>", text)
    for index, value in enumerate(placeholders):
        text = text.replace(f"@@MARKUP{index}@@", value)
    return text


def parse_table(lines: list[str]) -> list[list[str]]:
    rows = []
    for line in lines:
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if cells and all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells):
            continue
        rows.append(cells)
    return rows


def collect_blocks(markdown: str) -> list[tuple[str, object]]:
    lines = markdown.replace("\r\n", "\n").splitlines()
    blocks: list[tuple[str, object]] = []
    i = 0
    paragraph: list[str] = []

    def flush_paragraph() -> None:
        if paragraph:
            blocks.append(("paragraph", " ".join(x.strip() for x in paragraph)))
            paragraph.clear()

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if not stripped:
            flush_paragraph()
            i += 1
            continue

        if stripped.startswith("|") and stripped.endswith("|"):
            flush_paragraph()
            table_lines = []
            while i < len(lines):
                candidate = lines[i].strip()
                if not (candidate.startswith("|") and candidate.endswith("|")):
                    break
                table_lines.append(candidate)
                i += 1
            blocks.append(("table", parse_table(table_lines)))
            continue

        heading = re.match(r"^(#{1,3})\s+(.+)$", stripped)
        if heading:
            flush_paragraph()
            blocks.append((f"h{len(heading.group(1))}", heading.group(2)))
            i += 1
            continue

        if stripped.startswith(">"):
            flush_paragraph()
            quote_lines = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                quote_lines.append(lines[i].strip()[1:].strip())
                i += 1
            blocks.append(("quote", " ".join(quote_lines)))
            continue

        if re.match(r"^[-*]\s+", stripped):
            flush_paragraph()
            items = []
            while i < len(lines):
                match = re.match(r"^[-*]\s+(.+)$", lines[i].strip())
                if not match:
                    break
                items.append(match.group(1))
                i += 1
            blocks.append(("bullets", items))
            continue

        if re.match(r"^\d+\.\s+", stripped):
            flush_paragraph()
            items = []
            while i < len(lines):
                match = re.match(r"^(\d+)\.\s+(.+)$", lines[i].strip())
                if not match:
                    break
                items.append((int(match.group(1)), match.group(2)))
                i += 1
            blocks.append(("numbers", items))
            continue

        paragraph.append(stripped)
        i += 1

    flush_paragraph()
    return blocks


def build_styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        "TitleX", parent=styles["Title"], fontName="Helvetica-Bold",
        fontSize=25, leading=29, textColor=DARK_ORANGE, spaceAfter=14,
    ))
    styles.add(ParagraphStyle(
        "H1X", parent=styles["Heading1"], fontName="Helvetica-Bold",
        fontSize=18, leading=22, textColor=DARK_ORANGE,
        spaceBefore=10, spaceAfter=8,
    ))
    styles.add(ParagraphStyle(
        "H2X", parent=styles["Heading2"], fontName="Helvetica-Bold",
        fontSize=13.5, leading=17, textColor=TEAL,
        spaceBefore=9, spaceAfter=5,
    ))
    styles.add(ParagraphStyle(
        "H3X", parent=styles["Heading3"], fontName="Helvetica-Bold",
        fontSize=11, leading=14, textColor=INK,
        spaceBefore=7, spaceAfter=4,
    ))
    styles.add(ParagraphStyle(
        "BodyX", parent=styles["BodyText"], fontName="Helvetica",
        fontSize=9.2, leading=13, textColor=INK, spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        "ListX", parent=styles["BodyText"], fontName="Helvetica",
        fontSize=9, leading=12.5, textColor=INK,
        leftIndent=15, firstLineIndent=-10, spaceAfter=3,
    ))
    styles.add(ParagraphStyle(
        "QuoteX", parent=styles["BodyText"], fontName="Helvetica-BoldOblique",
        fontSize=9.5, leading=13, textColor=DARK_ORANGE,
        leftIndent=12, rightIndent=12, spaceAfter=8,
    ))
    styles.add(ParagraphStyle(
        "SmallX", parent=styles["BodyText"], fontName="Helvetica",
        fontSize=7.8, leading=10.5, textColor=INK,
    ))
    return styles


def header_footer(canvas, doc) -> None:
    width, height = letter
    canvas.saveState()
    canvas.setFillColor(INK)
    canvas.rect(0, height - 0.34 * inch, width, 0.34 * inch, fill=1, stroke=0)
    canvas.setFillColor(ORANGE)
    canvas.rect(0, height - 0.39 * inch, width, 0.05 * inch, fill=1, stroke=0)
    canvas.setFont("Helvetica-Bold", 7)
    canvas.setFillColor(CREAM)
    canvas.drawString(0.55 * inch, height - 0.225 * inch, "E.G.G.S. PLANETARY OPERATIONS")
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(STEEL)
    canvas.drawCentredString(width / 2, 0.30 * inch, f"Operations Handbook  |  Page {doc.page}")
    canvas.restoreState()


def render(markdown: str, output: Path) -> None:
    styles = build_styles()
    output.parent.mkdir(parents=True, exist_ok=True)
    doc = BaseDocTemplate(
        str(output),
        pagesize=letter,
        leftMargin=0.62 * inch,
        rightMargin=0.62 * inch,
        topMargin=0.62 * inch,
        bottomMargin=0.5 * inch,
        title="Efficiency Group for Guaranteed Satisfaction Operations Handbook",
        author="E.G.G.S. contributors",
    )
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="main")
    doc.addPageTemplates([PageTemplate(id="standard", frames=frame, onPage=header_footer)])

    story = []
    seen_title = False
    for kind, value in collect_blocks(markdown):
        if kind == "h1":
            if not seen_title:
                story.append(Spacer(1, 0.35 * inch))
                story.append(Paragraph(inline_markup(str(value)), styles["TitleX"]))
                seen_title = True
            else:
                story.extend([PageBreak(), Paragraph(inline_markup(str(value)), styles["H1X"])])
        elif kind == "h2":
            story.append(Paragraph(inline_markup(str(value)), styles["H1X"]))
        elif kind == "h3":
            story.append(Paragraph(inline_markup(str(value)), styles["H2X"]))
        elif kind == "paragraph":
            story.append(Paragraph(inline_markup(str(value)), styles["BodyX"]))
        elif kind == "quote":
            box = Table(
                [[Paragraph(inline_markup(str(value)), styles["QuoteX"])]],
                colWidths=[doc.width],
            )
            box.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), CREAM),
                ("BOX", (0, 0), (-1, -1), 0.8, ORANGE),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]))
            story.extend([KeepTogether(box), Spacer(1, 5)])
        elif kind in {"bullets", "numbers"}:
            for index, item in enumerate(value, 1):
                if kind == "bullets":
                    marker = "-"
                    item_text = item
                else:
                    marker = f"{item[0]}."
                    item_text = item[1]
                story.append(Paragraph(
                    f"<font color='#B9561B'><b>{marker}</b></font> {inline_markup(item_text)}",
                    styles["ListX"],
                ))
            story.append(Spacer(1, 3))
        elif kind == "table":
            rows = value
            if not rows:
                continue
            columns = max(len(row) for row in rows)
            normalized = [row + [""] * (columns - len(row)) for row in rows]
            data = [
                [Paragraph(inline_markup(cell), styles["SmallX"]) for cell in row]
                for row in normalized
            ]
            widths = [doc.width / columns] * columns
            table = Table(data, colWidths=widths, repeatRows=1)
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), INK),
                ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, CREAM]),
                ("GRID", (0, 0), (-1, -1), 0.35, STEEL),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]))
            story.extend([table, Spacer(1, 7)])

    doc.build(story)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    if not args.source.is_file():
        parser.error(f"source file not found: {args.source}")

    render(args.source.read_text(encoding="utf-8"), args.output)
    print(f"Generated {args.output.resolve()}")


if __name__ == "__main__":
    main()
