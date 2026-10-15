from rag_utils import delete_document

stale_sources = [
    r"D:\finetune.pdf",
    r"D:\min_project.pdf",
    r"D:\sample.docx",
    r"D:\notes.txt",
    r"D:\mycodes\langchain\prac_files\notes.md",
]

for source in stale_sources:
    print(f"\nChecking old source: {source}")
    delete_document(source)