# Project Roadmap and Status

Status labels:
- DONE: Implemented and validated.
- PARTIAL: Implemented but needs further validation.
- IN PROGRESS: Currently being worked on.
- PENDING: Not started.

## Phase 1 — Core RAG framework

| Task | Status |
|---|---|
| Architecture review | DONE |
| FAISS to ChromaDB migration | DONE |
| Persistent vector storage | DONE |
| Multi-document ingestion | DONE |
| Multi-format ingestion | DONE |
| Content-hash duplicate detection | PARTIAL |
| Source citations | DONE |
| Retrieval grading | PARTIAL |
| Web-search fallback | PARTIAL |
| Safe document updates | DONE |
| Document deletion | DONE |

## Phase 2 — Retrieval quality and evaluation

| Task | Status |
|---|---|
| Fixed retrieval evaluation dataset | DONE |
| Initial retrieval baseline | DONE |
| Precision@K | DONE |
| Recall@K | DONE |
| MRR | DONE |
| Retrieval failure analysis | DONE |
| Repeated-chunk diagnostics | DONE |
| Source concentration analysis | DONE |
| Top-K cutoff evaluation | DONE |
| Independent blinded relevance audit | DONE |
| Controlled Top-3 vs Top-5 answer evaluation | IN PROGRESS |
| Retrieval improvements | PENDING |
| Before/after comparison | PENDING |

## Phase 3 — Framework strengthening

| Task | Status |
|---|---|
| Strengthen LangGraph workflow | PARTIAL |
| Comprehensive automated testing | PENDING |
| Error handling and observability | PENDING |
| Business-independent core | PENDING |
| Evaluate need for multi-agent architecture | PENDING |

## Phase 4 — Product development

| Task | Status |
|---|---|
| Define business use case | PENDING |
| Business-specific prototype | PENDING |
| FastAPI backend | PENDING |
| Frontend | PENDING |
| Integration testing | PENDING |

## Phase 5 — Production readiness

| Task | Status |
|---|---|
| Production hardening | PENDING |
| Dockerization | PENDING |
| Deployment | PENDING |
| Production validation | PENDING |
| User feedback and iteration | PENDING |

## Current priority

Finish Phase 2 before making significant retrieval configuration changes.

Next immediate task: complete the controlled Top-3 versus Top-5 answer-quality experiment.