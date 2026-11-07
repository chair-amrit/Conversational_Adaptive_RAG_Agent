# Technical Decision Log

## D001 — ChromaDB instead of FAISS

**Decision:** Use ChromaDB for persistent vector storage.

**Reason:** The system requires persistent collections and document lifecycle management.

**Trade-off:** Requires managing persistent storage and collection state.

**Status:** Adopted.

## D002 — Gemini embeddings

**Decision:** Use Gemini embeddings.

**Reason:** Existing project integration and embedding support.

**Status:** Adopted.

## D003 — Multi-format ingestion

**Decision:** Support PDF, DOCX, PPTX, TXT, Markdown, CSV, XLSX, JSON and HTML.

**Reason:** The framework should not be restricted to PDF documents.

**Status:** Implemented.

## D004 — Content hashing and deterministic chunk IDs

**Decision:** Use normalized content hashing and deterministic chunk identifiers.

**Reason:** Support duplicate detection, unchanged-file skipping and safer document updates.

**Status:** Implemented; continue testing edge cases.

## D005 — Safe document updates

**Decision:** Add new content, verify indexing, and only then remove stale chunks.

**Reason:** Avoid losing existing indexed content when embedding or indexing fails.

**Validation:** Tested unchanged files, expansion, shortening, deletion, repeated deletion and simulated embedding failure.

**Status:** Functionally validated.

## D006 — Adaptive LangGraph workflow

**Decision:** Use graph-based routing, rewriting, retrieval, grading and generation.

**Reason:** Provide a flexible retrieval and fallback workflow.

**Status:** Implemented; further strengthening pending.

## D007 — Retrieval evaluation methodology

**Decision:** Use a fixed 16-question dataset with judged relevance labels.

**Reason:** Enable repeatable retrieval evaluation.

**Limitation:** The dataset covers four target documents and is not a comprehensive representation of all possible queries.

**Status:** Adopted.

## D008 — Passage-level relevance

**Decision:** Count a chunk as relevant if it provides useful evidence for at least one part of a question.

**Reason:** Sliding-window chunk boundaries can divide evidence across multiple passages.

**Limitation:** Passage relevance does not establish that the retrieved context answers the entire question.

**Status:** Adopted for current evaluation.

## D009 — Do not immediately change production Top-K

**Decision:** Preserve the existing production retrieval configuration during controlled Top-3 vs Top-5 experimentation.

**Reason:** A higher precision metric does not automatically mean better generated answers.

**Status:** Active.

## Future decisions

Record new decisions using:

- Decision ID.
- Date.
- Problem.
- Alternatives considered.
- Selected option.
- Reason.
- Trade-offs.
- Validation evidence.
- Status.