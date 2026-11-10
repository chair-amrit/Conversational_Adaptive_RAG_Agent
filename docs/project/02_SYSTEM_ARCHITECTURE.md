# System Architecture

## 1. Architecture overview

The system has three major areas:

1. Document ingestion and indexing.
2. Retrieval and conversational orchestration.
3. Answer generation and evaluation.

## 2. Ingestion and indexing

Known capabilities:

- PDF, DOCX, PPTX, TXT, Markdown, CSV, XLSX, JSON and HTML ingestion.
- Multiple document ingestion.
- Text extraction and chunking.
- Gemini embeddings.
- Persistent ChromaDB storage.
- Content hashing.
- Deterministic chunk IDs.
- Duplicate detection.
- Safe update and stale-chunk cleanup.
- Document deletion by source.

Known storage configuration:
- Collection: `my_rag_multiformat`.
- Persistence directory: `./chroma_db`.
- Earlier documented chunk size: 500.
- Earlier documented overlap: 90.

Verify the latest implementation before treating these values as current.

## 3. Conversational orchestration

The documented LangGraph workflow includes:

- Route.
- Rewrite.
- Retrieve.
- Grade.
- Generate.

A permission-gated web-search path uses Tavily, followed by web answer generation and saving.

The graph uses checkpointing with MemorySaver and a documented thread ID of `chat1`.

Verify the latest graph implementation and state schema before modifying it.

## 4. Answer generation

The system generates answers using retrieved context and supports source citations.

The answer-generation prompt, citation schema, and exact model configuration must be taken from the current implementation.

## 5. Main source files

| File | Known responsibility |
|---|---|
| `main.py` | CLI and LangGraph execution |
| `rag_utils.py` | Ingestion, vector store and retrieval utilities |
| `llm_utils.py` | LLM and answer-generation utilities |

Other modules may exist. Inspect the repository before assuming this is the complete structure.

## 6. Architecture improvement priorities

- Retrieval quality.
- Answer faithfulness.
- Citation reliability.
- Test coverage.
- API separation.
- Observability.
- Deployment readiness.

Do not redesign the architecture without identifying a concrete requirement or measured problem.