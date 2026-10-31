"""
Markdown to Word (.docx) Converter for Capstone Project Report
Converts GitHub Flavored Markdown (tables, headings, images, callouts, code blocks)
into a beautifully styled, publication-ready Microsoft Word document (.docx).
"""

import re
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import parse_xml, OxmlElement
from docx.oxml.ns import nsdecls, qn

# Color Palette (Corporate / Medical Bioinformatic Theme)
COLOR_NAVY = RGBColor(30, 58, 138)       # #1E3A8A - Primary Header
COLOR_BLUE = RGBColor(37, 99, 235)       # #2563EB - Secondary Header
COLOR_SLATE = RGBColor(55, 65, 81)       # #374151 - Subheaders
COLOR_TEXT = RGBColor(31, 41, 55)        # #1F2937 - Body Text
COLOR_MUTED = RGBColor(107, 114, 128)    # #6B7280 - Captions / Footers
COLOR_CODE = RGBColor(17, 24, 39)        # #111827 - Code font
COLOR_RED = RGBColor(185, 28, 28)        # #B91C1C - Resistant highlights
COLOR_GREEN = RGBColor(22, 101, 52)      # #166534 - Susceptible highlights

HEX_HEADER_BG = "1E3A8A"
HEX_ZEBRA_BG = "F8FAFC"
HEX_CODE_BG = "F1F5F9"
HEX_QUOTE_BG = "EFF6FF"
HEX_BORDER = "CBD5E1"


def set_cell_shading(cell, color_hex: str):
    """Set background color of a table cell."""
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{color_hex}"/>')
    tc_pr.append(shd)


def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    """Set inner cell padding in dxa (1 pt = 20 dxa)."""
    tc_pr = cell._tc.get_or_add_tcPr()
    tc_mar = parse_xml(
        f'<w:tcMar {nsdecls("w")}>'
        f'<w:top w:w="{top}" w:type="dxa"/>'
        f'<w:bottom w:w="{bottom}" w:type="dxa"/>'
        f'<w:left w:w="{left}" w:type="dxa"/>'
        f'<w:right w:w="{right}" w:type="dxa"/>'
        f'</w:tcMar>'
    )
    tc_pr.append(tc_mar)


def add_inline_formatted_text(paragraph, text: str):
    """Parse bold, italic, inline code, and URLs in text."""
    # Pattern to match **bold**, *italic*, `code`, and plain text
    tokens = re.split(r'(\*\*.*?\*\*|\*.*?\*|`.*?`)', text)
    for token in tokens:
        if not token:
            continue
        if token.startswith('**') and token.endswith('**') and len(token) >= 4:
            run = paragraph.add_run(token[2:-2])
            run.bold = True
            run.font.color.rgb = COLOR_TEXT
        elif token.startswith('*') and token.endswith('*') and len(token) >= 2:
            run = paragraph.add_run(token[1:-1])
            run.italic = True
            run.font.color.rgb = COLOR_TEXT
        elif token.startswith('`') and token.endswith('`') and len(token) >= 2:
            run = paragraph.add_run(token[1:-1])
            run.font.name = 'Consolas'
            run.font.size = Pt(9.5)
            run.font.color.rgb = RGBColor(194, 24, 91)
        else:
            run = paragraph.add_run(token)
            run.font.color.rgb = COLOR_TEXT


def setup_document_styles(doc):
    """Configure default margins, typography, and header/footer."""
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)

        # Header
        header = section.header
        hp = header.paragraphs[0]
        hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        hrun = hp.add_run("Capstone Project Report | ProkBERT-AMR Genomic Prediction")
        hrun.font.name = "Calibri"
        hrun.font.size = Pt(8.5)
        hrun.font.color.rgb = COLOR_MUTED

        # Footer
        footer = section.footer
        fp = footer.paragraphs[0]
        fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        frun = fp.add_run("Antimicrobial Resistance Research & Genomic AI • Confidential / Academic Submission")
        frun.font.name = "Calibri"
        frun.font.size = Pt(8.5)
        frun.font.color.rgb = COLOR_MUTED

    # Default Style Font
    normal_style = doc.styles['Normal']
    normal_style.font.name = 'Calibri'
    normal_style.font.size = Pt(11)
    normal_style.font.color.rgb = COLOR_TEXT


def convert_markdown_to_docx(md_path: Path, output_path: Path):
    """Parse complete Markdown file and render styled Word document."""
    print(f"Reading {md_path}...")
    with open(md_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    doc = docx.Document()
    setup_document_styles(doc)

    in_code_block = False
    code_lines = []
    in_table = False
    table_lines = []

    def flush_table():
        nonlocal in_table, table_lines
        if not table_lines:
            in_table = False
            return

        # Parse table cells
        rows = []
        for line in table_lines:
            line_str = line.strip()
            if not line_str.startswith('|'):
                continue
            cells = [c.strip() for c in line_str.strip('|').split('|')]
            # Skip separator line like |---|---|
            if all(re.match(r'^:?-+:?$', c) for c in cells if c):
                continue
            rows.append(cells)

        if rows:
            num_cols = max(len(r) for r in rows)
            table = doc.add_table(rows=len(rows), cols=num_cols)
            table.alignment = WD_TABLE_ALIGNMENT.CENTER
            table.style = 'Table Grid'

            for r_idx, row_cells in enumerate(rows):
                is_header = (r_idx == 0)
                row = table.rows[r_idx]
                # Avoid row split across pages
                tr_pr = row._tr.get_or_add_trPr()
                tr_pr.append(parse_xml(f'<w:cantSplit {nsdecls("w")}/>'))
                if is_header:
                    tr_pr.append(parse_xml(f'<w:tblHeader {nsdecls("w")}/>'))

                for c_idx in range(num_cols):
                    cell = row.cells[c_idx]
                    set_cell_margins(cell, top=120, bottom=120, left=160, right=160)
                    cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER

                    cell_text = row_cells[c_idx] if c_idx < len(row_cells) else ""
                    # Header styling
                    if is_header:
                        set_cell_shading(cell, HEX_HEADER_BG)
                        p = cell.paragraphs[0]
                        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                        p.paragraph_format.space_before = Pt(2)
                        p.paragraph_format.space_after = Pt(2)
                        run = p.add_run(cell_text)
                        run.bold = True
                        run.font.name = 'Calibri'
                        run.font.size = Pt(9.5)
                        run.font.color.rgb = RGBColor(255, 255, 255)
                    else:
                        # Zebra striping for data rows
                        if r_idx % 2 == 1:
                            set_cell_shading(cell, HEX_ZEBRA_BG)
                        p = cell.paragraphs[0]
                        p.paragraph_format.space_before = Pt(2)
                        p.paragraph_format.space_after = Pt(2)

                        # Right-align numeric columns, left-align text
                        if re.match(r'^-?\d+(\.\d+)?%?$', cell_text.strip()):
                            p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
                        else:
                            p.alignment = WD_ALIGN_PARAGRAPH.LEFT

                        # Highlight resistant vs susceptible
                        clean_text = cell_text.replace('**', '').strip()
                        if clean_text in ['1.0000', '100.0%']:
                            run = p.add_run(cell_text.replace('**', ''))
                            run.bold = True
                            run.font.color.rgb = COLOR_GREEN
                        elif '**' in cell_text:
                            run = p.add_run(cell_text.replace('**', ''))
                            run.bold = True
                            run.font.color.rgb = COLOR_NAVY
                        else:
                            run = p.add_run(cell_text)
                            run.font.color.rgb = COLOR_TEXT
                        run.font.name = 'Calibri'
                        run.font.size = Pt(9.5)

            doc.add_paragraph().paragraph_format.space_after = Pt(4)

        table_lines = []
        in_table = False

    def flush_code_block():
        nonlocal in_code_block, code_lines
        if not code_lines:
            in_code_block = False
            return

        code_text = "".join(code_lines).strip('\n')
        # Check if mermaid diagram
        if code_lines and "flowchart" in code_lines[0]:
            # Add callout note for flowchart
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(6)
            p.paragraph_format.space_after = Pt(6)
            run = p.add_run("[System Architecture Workflow Chart: Illustrated in figures/architecture_pipeline.png]")
            run.italic = True
            run.bold = True
            run.font.color.rgb = COLOR_BLUE
        else:
            # Monospace code block in shaded container
            tbl = doc.add_table(rows=1, cols=1)
            tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
            tbl.style = 'Table Grid'
            cell = tbl.cell(0, 0)
            set_cell_shading(cell, HEX_CODE_BG)
            set_cell_margins(cell, top=140, bottom=140, left=180, right=180)
            p = cell.paragraphs[0]
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.line_spacing = 1.05
            run = p.add_run(code_text)
            run.font.name = 'Consolas'
            run.font.size = Pt(8.5)
            run.font.color.rgb = COLOR_CODE

            doc.add_paragraph().paragraph_format.space_after = Pt(4)

        code_lines = []
        in_code_block = False

    i = 0
    n_lines = len(lines)
    while i < n_lines:
        raw_line = lines[i]
        line = raw_line.rstrip('\r\n')
        stripped = line.strip()

        # Handle Fenced Code Blocks (```)
        if stripped.startswith('```'):
            if in_code_block:
                flush_code_block()
            else:
                if in_table:
                    flush_table()
                in_code_block = True
                code_lines = []
            i += 1
            continue

        if in_code_block:
            code_lines.append(raw_line)
            i += 1
            continue

        # Handle Markdown Tables (|)
        if stripped.startswith('|') and stripped.endswith('|'):
            in_table = True
            table_lines.append(line)
            i += 1
            continue
        elif in_table:
            flush_table()

        # Empty lines
        if not stripped:
            i += 1
            continue

        # Horizontal Rule (---)
        if stripped in ['---', '***', '___']:
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(6)
            p.paragraph_format.space_after = Pt(6)
            # Add thin decorative horizontal line
            pBdr = parse_xml(f'<w:pBdr {nsdecls("w")}><w:bottom w:val="single" w:sz="6" w:space="1" w:color="{HEX_BORDER}"/></w:pBdr>')
            p._p.get_or_add_pPr().append(pBdr)
            i += 1
            continue

        # Headings (#)
        if stripped.startswith('#'):
            h_match = re.match(r'^(#{1,6})\s+(.*)', stripped)
            if h_match:
                level = len(h_match.group(1))
                h_text = h_match.group(2).strip()

                if level == 1:
                    h = doc.add_paragraph()
                    h.paragraph_format.space_before = Pt(18)
                    h.paragraph_format.space_after = Pt(6)
                    h.paragraph_format.keep_with_next = True
                    run = h.add_run(h_text)
                    run.font.name = 'Calibri'
                    run.font.size = Pt(22)
                    run.bold = True
                    run.font.color.rgb = COLOR_NAVY
                    # Bottom border for Document Main Heading
                    pBdr = parse_xml(f'<w:pBdr {nsdecls("w")}><w:bottom w:val="single" w:sz="12" w:space="4" w:color="{HEX_HEADER_BG}"/></w:pBdr>')
                    h._p.get_or_add_pPr().append(pBdr)

                elif level == 2:
                    h = doc.add_paragraph()
                    h.paragraph_format.space_before = Pt(14)
                    h.paragraph_format.space_after = Pt(4)
                    h.paragraph_format.keep_with_next = True
                    run = h.add_run(h_text)
                    run.font.name = 'Calibri'
                    run.font.size = Pt(15)
                    run.bold = True
                    run.font.color.rgb = COLOR_BLUE

                elif level == 3:
                    h = doc.add_paragraph()
                    h.paragraph_format.space_before = Pt(10)
                    h.paragraph_format.space_after = Pt(3)
                    h.paragraph_format.keep_with_next = True
                    run = h.add_run(h_text)
                    run.font.name = 'Calibri'
                    run.font.size = Pt(12.5)
                    run.bold = True
                    run.font.color.rgb = COLOR_SLATE

                else:
                    h = doc.add_paragraph()
                    h.paragraph_format.space_before = Pt(8)
                    h.paragraph_format.space_after = Pt(2)
                    h.paragraph_format.keep_with_next = True
                    run = h.add_run(h_text)
                    run.font.name = 'Calibri'
                    run.font.size = Pt(11)
                    run.bold = True
                    run.font.color.rgb = COLOR_SLATE

                i += 1
                continue

        # Images (![alt](path))
        img_match = re.search(r'!\[(.*?)\]\((.*?)\)', stripped)
        if img_match:
            alt_text = img_match.group(1)
            img_rel_path = img_match.group(2)
            img_file = PROJECT_ROOT / img_rel_path

            if img_file.exists():
                p_img = doc.add_paragraph()
                p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p_img.paragraph_format.space_before = Pt(8)
                p_img.paragraph_format.space_after = Pt(2)
                try:
                    p_img.add_run().add_picture(str(img_file), width=Inches(6.0))
                except Exception as e:
                    p_img.add_run(f"[Image file: {img_file.name}]").italic = True

                if alt_text:
                    p_cap = doc.add_paragraph()
                    p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    p_cap.paragraph_format.space_before = Pt(0)
                    p_cap.paragraph_format.space_after = Pt(8)
                    cap_run = p_cap.add_run(f"Figure: {alt_text}")
                    cap_run.font.name = 'Calibri'
                    cap_run.font.size = Pt(9.5)
                    cap_run.font.color.rgb = COLOR_MUTED
                    cap_run.italic = True
            else:
                p_err = doc.add_paragraph()
                p_err.add_run(f"[{alt_text} — Image location: {img_rel_path}]").italic = True

            i += 1
            continue

        # Blockquotes (> )
        if stripped.startswith('>'):
            quote_text = stripped[1:].strip()
            tbl = doc.add_table(rows=1, cols=1)
            tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
            tbl.style = 'Table Grid'
            cell = tbl.cell(0, 0)
            set_cell_shading(cell, HEX_QUOTE_BG)
            set_cell_margins(cell, top=120, bottom=120, left=160, right=160)
            # Left vertical blue accent bar
            tc_bdr = parse_xml(
                f'<w:tcBorders {nsdecls("w")}>'
                f'<w:left w:val="single" w:sz="24" w:space="0" w:color="{HEX_HEADER_BG}"/>'
                f'<w:top w:val="none"/>'
                f'<w:bottom w:val="none"/>'
                f'<w:right w:val="none"/>'
                f'</w:tcBorders>'
            )
            cell._tc.get_or_add_tcPr().append(tc_bdr)
            p = cell.paragraphs[0]
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(0)
            add_inline_formatted_text(p, quote_text)
            doc.add_paragraph().paragraph_format.space_after = Pt(3)
            i += 1
            continue

        # Bullet Lists (- or *)
        if stripped.startswith(('- ', '* ')):
            p = doc.add_paragraph(style='List Bullet')
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.line_spacing = 1.15
            add_inline_formatted_text(p, stripped[2:])
            i += 1
            continue

        # Numbered Lists (1. )
        num_match = re.match(r'^(\d+)\.\s+(.*)', stripped)
        if num_match:
            p = doc.add_paragraph(style='List Number')
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.line_spacing = 1.15
            add_inline_formatted_text(p, num_match.group(2))
            i += 1
            continue

        # Standard Paragraph
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(5)
        p.paragraph_format.line_spacing = 1.15
        add_inline_formatted_text(p, stripped)

        i += 1

    # Flush any trailing tables or code blocks
    if in_table:
        flush_table()
    if in_code_block:
        flush_code_block()

    print(f"Saving Word Document to {output_path}...")
    doc.save(str(output_path))
    print(f"Document saved successfully! Size: {output_path.stat().st_size:,} bytes")


def main():
    print("=" * 70)
    print("MARKDOWN TO WORD (.DOCX) CONVERSION")
    print("=" * 70)

    report_md = PROJECT_ROOT / "CAPSTONE_PROJECT_REPORT.md"
    report_docx = PROJECT_ROOT / "CAPSTONE_PROJECT_REPORT.docx"
    if report_md.exists():
        convert_markdown_to_docx(report_md, report_docx)

    readme_md = PROJECT_ROOT / "README.md"
    readme_docx = PROJECT_ROOT / "README.docx"
    if readme_md.exists():
        convert_markdown_to_docx(readme_md, readme_docx)

    print("\n" + "=" * 70)
    print("ALL DOCUMENTS CONVERTED TO WORD SUCCESSFULLY!")
    print(f"1. Master Report: {report_docx}")
    print(f"2. Project Readme: {readme_docx}")
    print("=" * 70)


if __name__ == "__main__":
    main()

