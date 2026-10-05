from docx import Document

path = r"D:\fileless malware\Fileless_Malware.docx"
out = r"D:\fileless malware\Fileless_Malware_extracted.txt"
doc = Document(path)

with open(out, "w", encoding="utf-8") as handle:
    for i, paragraph in enumerate(doc.paragraphs):
        text = paragraph.text.strip()
        if text:
            handle.write(f"{i:04d}: {text}\n")

print(out)
