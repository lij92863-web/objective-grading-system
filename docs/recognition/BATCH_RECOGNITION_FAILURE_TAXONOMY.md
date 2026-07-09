# Batch Recognition Failure Taxonomy

| Failure | Blocking | Review | Retryable | Manual Fix |
|---------|----------|--------|-----------|------------|
| image_quality | Yes | No | No | Yes |
| template_missing | Yes | No | No | Yes |
| roi_missing | Yes | No | No | Yes |
| identity_missing | Yes | No | No | Yes |
| identity_conflict | Yes | No | No | Yes |
| omr_ambiguous | No | Yes | No | Yes |
| qwen_malformed | No | Yes | Once | No |
| qwen_timeout | No | No | Yes | No |
| invalid_option | Yes | No | No | Yes |
| review_unresolved | Yes | Yes | No | Yes |