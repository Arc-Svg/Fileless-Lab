from pathlib import Path
import re

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor


ROOT = Path(r"D:\fileless malware")
OUTPUT = ROOT / "Huong_dan_cai_dat_va_thuc_hien_lab_Fileless_Malware.docx"
SOURCES = [
    ROOT / "README.md",
    ROOT / "01-chuan-bi-moi-truong.md",
    ROOT / "02-lab-2-may-astaroth-style.md",
    ROOT / "03-detection-phong-thu.md",
    ROOT / "04-cleanup-va-viet-bao-cao.md",
]


def set_run_font(run, name="Times New Roman", size=None, bold=None, color=None):
    run.font.name = name
    run._element.rPr.rFonts.set(qn("w:ascii"), name)
    run._element.rPr.rFonts.set(qn("w:hAnsi"), name)
    run._element.rPr.rFonts.set(qn("w:eastAsia"), name)
    if size is not None:
        run.font.size = Pt(size)
    if bold is not None:
        run.bold = bold
    if color is not None:
        run.font.color.rgb = RGBColor.from_string(color)


def set_cell_shading(cell, fill):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = tc_pr.find(qn("w:shd"))
    if shd is None:
        shd = OxmlElement("w:shd")
        tc_pr.append(shd)
    shd.set(qn("w:fill"), fill)


def set_cell_text(cell, text, bold=False, monospace=False):
    cell.text = ""
    p = cell.paragraphs[0]
    run = p.add_run(text)
    set_run_font(run, "Consolas" if monospace else "Times New Roman", 9.5 if monospace else 11, bold=bold)
    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER


def set_table_borders(table):
    tbl = table._tbl
    tbl_pr = tbl.tblPr
    borders = tbl_pr.first_child_found_in("w:tblBorders")
    if borders is None:
        borders = OxmlElement("w:tblBorders")
        tbl_pr.append(borders)
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        tag = "w:" + edge
        element = borders.find(qn(tag))
        if element is None:
            element = OxmlElement(tag)
            borders.append(element)
        element.set(qn("w:val"), "single")
        element.set(qn("w:sz"), "6")
        element.set(qn("w:space"), "0")
        element.set(qn("w:color"), "D9D9D9")


def configure_styles(doc):
    styles = doc.styles
    for style_name in ["Normal", "Body Text"]:
        style = styles[style_name]
        style.font.name = "Times New Roman"
        style._element.rPr.rFonts.set(qn("w:ascii"), "Times New Roman")
        style._element.rPr.rFonts.set(qn("w:hAnsi"), "Times New Roman")
        style._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
        style.font.size = Pt(11)

    for style_name, size in [("Title", 18), ("Heading 1", 15), ("Heading 2", 13), ("Heading 3", 12)]:
        style = styles[style_name]
        style.font.name = "Times New Roman"
        style._element.rPr.rFonts.set(qn("w:ascii"), "Times New Roman")
        style._element.rPr.rFonts.set(qn("w:hAnsi"), "Times New Roman")
        style._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
        style.font.size = Pt(size)
        style.font.bold = True
        style.font.color.rgb = RGBColor(0, 0, 0)
        p_pr = style._element.get_or_add_pPr()
        p_bdr = p_pr.find(qn("w:pBdr"))
        if p_bdr is not None:
            p_pr.remove(p_bdr)

    styles["No Spacing"].font.name = "Times New Roman"
    styles["No Spacing"].font.size = Pt(11)


def add_code_block(doc, lines):
    text = "\n".join(lines).rstrip()
    if not text:
        return
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(3)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.left_indent = Inches(0.18)
    for i, line in enumerate(text.splitlines()):
        if i:
            p.add_run("\n")
        run = p.add_run(line)
        set_run_font(run, "Consolas", 9)


def add_rich_paragraph(doc, text, style=None):
    p = doc.add_paragraph(style=style)
    p.paragraph_format.space_after = Pt(5)
    parts = re.split(r"(`[^`]+`|\*\*[^*]+\*\*)", text)
    for part in parts:
        if not part:
            continue
        if part.startswith("`") and part.endswith("`"):
            run = p.add_run(part[1:-1])
            set_run_font(run, "Consolas", 9.5)
        elif part.startswith("**") and part.endswith("**"):
            run = p.add_run(part[2:-2])
            set_run_font(run, bold=True)
        else:
            run = p.add_run(part)
            set_run_font(run)
    return p


def add_table_from_markdown(doc, rows):
    parsed = []
    for row in rows:
        cells = [c.strip() for c in row.strip().strip("|").split("|")]
        parsed.append(cells)
    if len(parsed) < 2:
        return False
    header = parsed[0]
    body = [r for r in parsed[2:] if len(r) == len(header)]
    table = doc.add_table(rows=1, cols=len(header))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.style = "Table Grid"
    set_table_borders(table)
    for i, cell_text in enumerate(header):
        cell = table.rows[0].cells[i]
        set_cell_shading(cell, "D9EAF7")
        set_cell_text(cell, cell_text, bold=True)
    for row in body:
        cells = table.add_row().cells
        for i, cell_text in enumerate(row):
            set_cell_text(cells[i], cell_text)
    doc.add_paragraph()
    return True


def parse_markdown_into_doc(doc, markdown):
    lines = markdown.splitlines()
    in_code = False
    code_lines = []
    table_lines = []
    seen_first_h1 = False

    def flush_table():
        nonlocal table_lines
        if table_lines:
            add_table_from_markdown(doc, table_lines)
            table_lines = []

    for raw in lines:
        line = raw.rstrip()
        stripped = line.strip()

        if stripped.startswith("```"):
            if in_code:
                add_code_block(doc, code_lines)
                code_lines = []
                in_code = False
            else:
                flush_table()
                in_code = True
            continue

        if in_code:
            code_lines.append(line)
            continue

        if stripped.startswith("|") and stripped.endswith("|"):
            table_lines.append(stripped)
            continue
        else:
            flush_table()

        if not stripped:
            continue

        if stripped.startswith("# "):
            if seen_first_h1:
                doc.add_page_break()
            seen_first_h1 = True
            p = doc.add_paragraph(stripped[2:].strip(), style="Heading 1")
            p.paragraph_format.space_before = Pt(0)
            continue
        if stripped.startswith("## "):
            doc.add_paragraph(stripped[3:].strip(), style="Heading 2")
            continue
        if stripped.startswith("### "):
            doc.add_paragraph(stripped[4:].strip(), style="Heading 3")
            continue

        if stripped.startswith("- [ ]"):
            p = add_rich_paragraph(doc, "[ ] " + stripped[5:].strip())
            p.paragraph_format.left_indent = Inches(0.25)
            continue

        if stripped.startswith("- "):
            p = add_rich_paragraph(doc, stripped[2:].strip(), style="List Bullet")
            continue

        if re.match(r"^\d+\.\s+", stripped):
            content = re.sub(r"^\d+\.\s+", "", stripped)
            add_rich_paragraph(doc, content, style="List Number")
            continue

        if stripped.startswith(">"):
            p = add_rich_paragraph(doc, stripped.lstrip("> ").strip())
            p.paragraph_format.left_indent = Inches(0.25)
            p.paragraph_format.right_indent = Inches(0.15)
            continue

        add_rich_paragraph(doc, stripped)

    flush_table()
    if in_code and code_lines:
        add_code_block(doc, code_lines)


def build_docx():
    doc = Document()
    section = doc.sections[0]
    section.top_margin = Inches(0.75)
    section.bottom_margin = Inches(0.75)
    section.left_margin = Inches(0.85)
    section.right_margin = Inches(0.85)
    configure_styles(doc)

    title = doc.add_paragraph(style="Title")
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title.add_run("Hướng dẫn cài đặt và thực hiện lab Fileless Malware")
    set_run_font(run, size=18, bold=True)

    subtitle = doc.add_paragraph()
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = subtitle.add_run("Lab Astaroth-inspired trên hai máy với LNK, PowerShell và in-memory payload execution")
    set_run_font(run, size=11)

    intro = doc.add_paragraph()
    intro.paragraph_format.space_after = Pt(10)
    run = intro.add_run(
        "Tài liệu này gộp phần chuẩn bị môi trường, các bước thực hiện lab, cách quan sát log và hướng dẫn cleanup. "
        "Lab chỉ dùng payload vô hại trong mạng nội bộ, không mô phỏng đánh cắp dữ liệu, C2 thật hoặc bypass antivirus. "
        "Persistence được mô phỏng bằng Registry Run key dễ thấy, có mục đích retry và có hướng dẫn cleanup rõ ràng."
    )
    set_run_font(run)

    for source in SOURCES:
        parse_markdown_into_doc(doc, source.read_text(encoding="utf-8"))

    # Remove the page break that appears before the first imported H1 if it starts a blank page.
    # Kept simple: Word handles the first break without visual harm in most renderers.
    doc.save(OUTPUT)


if __name__ == "__main__":
    build_docx()
    print(OUTPUT)
