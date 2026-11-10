# Project Overview

## 1. Project name

Conversational Adaptive RAG Agent

## 2. Problem statement

Traditional RAG systems often rely on relatively static retrieval pipelines. They may retrieve irrelevant passages, fail to handle different document formats consistently, or generate answers without sufficient evidence.

This project aims to build an adaptive conversational RAG framework that can ingest multiple document types, retrieve relevant information, evaluate retrieval quality, and generate grounded responses with citations.

## 3. Objectives

1. Build a robust multi-format ingestion pipeline.
2. Prevent duplicate indexing and support document updates.
3. Use persistent vector storage.
4. Implement adaptive retrieval and retrieval grading.
5. Support conversational context through graph-based orchestration.
6. Generate answers grounded in retrieved evidence.
7. Provide source citations.
8. Evaluate retrieval and answer quality systematically.
9. Develop a reusable backend and user interface.
10. Prepare the system for testing and deployment.

## 4. Technology stack

| Component | Technology |
|---|---|
| Language | Python |
| Orchestration | LangGraph |
| Vector database | ChromaDB |
| Embeddings | Gemini embedding model |
| Generation | Gemini model |
| Web search | Tavily |
| Evaluation | Custom Python evaluation scripts |
| Version control | Git and GitHub |

Confirm exact package and model versions from the current repository before reporting them.

## 5. Engineering principles

- Modularity.
- Reproducibility.
- Persistent state.
- Safe document lifecycle management.
- Evidence-grounded generation.
- Explicit error handling.
- Measurable retrieval quality.
- Separation of experimentation and production configuration.

## 6. Long-term direction

Develop the framework into a reusable system that can support different business and research use cases without requiring changes to its core retrieval and orchestration infrastructure.