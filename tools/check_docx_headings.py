from docx import Document

path = r"D:\fileless malware\Huong_dan_cai_dat_va_thuc_hien_lab_Fileless_Malware.docx"
out = r"D:\fileless malware\Huong_dan_headings_check.txt"
doc = Document(path)

with open(out, "w", encoding="utf-8") as handle:
    for i, paragraph in enumerate(doc.paragraphs):
        text = paragraph.text.strip()
        if text and paragraph.style.name in ("Title", "Heading 1", "Heading 2"):
            handle.write(f"{i:03d} | {paragraph.style.name} | {text}\n")

print(out)
