# Judged Retrieval Cutoff Analysis

- Queries: **16**
- Judgements: **80**
- Relevant chunks in judged Top-5 pool: **19**
- Label method: **LLM-assisted relevance judgements**

| Cutoff | Relevant | Irrelevant | Precision@K | Coverage of judged relevant | HitRate@K | MRR@K |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 16 | 0 | 1.0000 | 0.8421 | 1.0000 | 1.0000 |
| 2 | 18 | 14 | 0.5625 | 0.9474 | 1.0000 | 1.0000 |
| 3 | 19 | 29 | 0.3958 | 1.0000 | 1.0000 | 1.0000 |
| 4 | 19 | 45 | 0.2969 | 1.0000 | 1.0000 | 1.0000 |
| 5 | 19 | 61 | 0.2375 | 1.0000 | 1.0000 | 1.0000 |

## Interpretation and limitations

`Coverage of judged relevant` is the proportion of the relevant chunks labelled within this Top-5 pool that are retained by a smaller cutoff. It is **not corpus-level Recall@K**, because relevance outside the judged Top-5 results has not been exhaustively assessed.

MRR@K and HitRate@K are 1.0 for all cutoffs in this dataset because the original rank-1 results were seeded as relevant before the additional LLM-assisted labelling. Treat these values as descriptive of the current labels, not as an independent validation of ranking quality.

The judgement set is small (16 queries across four target documents) and uses LLM-assisted labels. Audit the seeded rank-1 labels before using these metrics to select production retrieval settings.
