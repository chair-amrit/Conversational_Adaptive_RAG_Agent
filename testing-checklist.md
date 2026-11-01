@'
# RAG Regression Testing Checklist

## Document Ingestion

- [ ] Index a new text file.
- [x] Update an existing file and verify updated content.
- [x] Re-index an unchanged file and verify it is skipped.
- [ ] Update a long file and verify stale chunks are removed.
- [ ] Shorten a file and verify obsolete chunks are removed.
- [ ] Verify failed embedding operations preserve previous content.
- [ ] Verify document deletion removes all chunks for that source.

## Retrieval

- [ ] Verify retrieved chunks contain relevant information.
- [ ] Verify source metadata is preserved.
- [ ] Verify answers cite the retrieved sources.
- [ ] Verify web fallback behavior when local retrieval is insufficient.

## Reliability

- [ ] Test supported file formats.
- [ ] Test empty and malformed files.
- [ ] Test duplicate content across different filenames.
- [ ] Test retrieval after restarting the application.
'@ | Set-Content docs\testing-checklist.md