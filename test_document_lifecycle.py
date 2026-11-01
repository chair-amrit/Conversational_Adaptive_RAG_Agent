New-Item -ItemType Directory -Force tests
@'
from pathlib import Path
from langchain_chroma import Chroma
from rag_utils import create_rag

COLLECTION = "my_rag_multiformat"
PERSIST_DIR = "./chroma_db"


def get_chunks(file_path):
    source = str(Path(file_path).resolve())
    db = Chroma(
        collection_name=COLLECTION,
        persist_directory=PERSIST_DIR,
    )
    return db.get(
        where={"source": source},
        include=["documents", "metadatas"],
    )


def test_document_update_replaces_old_content(tmp_path):
    file_path = tmp_path / "lifecycle_test.txt"
    file_path.write_text("Original lifecycle content.", encoding="utf-8")

    create_rag(str(file_path))
    file_path.write_text("Updated lifecycle content.", encoding="utf-8")
    create_rag(str(file_path))

    result = get_chunks(file_path)
    documents = result["documents"]

    assert any("Updated lifecycle content." in doc for doc in documents)
    assert not any("Original lifecycle content." in doc for doc in documents)


def test_unchanged_document_remains_indexed(tmp_path):
    file_path = tmp_path / "unchanged_test.txt"
    file_path.write_text("Stable lifecycle content.", encoding="utf-8")

    create_rag(str(file_path))
    before = get_chunks(file_path)

    create_rag(str(file_path))
    after = get_chunks(file_path)

    assert before["ids"] == after["ids"]
    assert before["documents"] == after["documents"]
'@ | Set-Content tests\test_document_lifecycle.py