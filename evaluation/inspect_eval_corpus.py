from langchain_chroma import Chroma

db = Chroma(
    collection_name="my_rag_multiformat",
    persist_directory="./chroma_db"
)

data = db.get(
    include=["documents", "metadatas"]
)

selected_files = {
    "rag_service_design.html",
    "quant_strategy_spec.json",
    "project_atlas_kickoff.pptx",
    "dabstep_task_registry.xlsx",
}

items = []

for doc_id, document, metadata in zip(
    data["ids"],
    data["documents"],
    data["metadatas"]
):
    if metadata.get("file_name") in selected_files:
        items.append((metadata, doc_id, document))

items.sort(
    key=lambda item: (
        item[0].get("file_name", ""),
        item[0].get("chunk_index", 0)
    )
)

for metadata, doc_id, document in items:
    print("\n" + "=" * 75)
    print("FILE:", metadata.get("file_name"))
    print("CHUNK INDEX:", metadata.get("chunk_index"))
    print("CHUNK ID:", doc_id)
    print("CONTENT:")
    print(document)