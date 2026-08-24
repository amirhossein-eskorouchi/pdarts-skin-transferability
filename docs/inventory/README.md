# Source Archive Inventory

This directory records the provenance and classification of the original
P-DARTS skin-transferability research archive.

## Preservation rule

The original research archive remains outside the public Git repository.

The archive must not be modified, renamed, extracted into the repository,
or committed directly.

## Audit outputs

The archive-audit workflow will generate:

- `generated/source_archive_summary.json`
- `generated/source_archive_inventory.csv`

The summary records the archive SHA-256 digest, integrity result, archive
size, entry counts, extension counts, and top-level path counts.

The inventory records every archive member with its path, size, extension,
CRC-32 value, and preliminary review classification.

## Classification boundary

Archive entries will later be classified as:

- `PRESERVE_PRIVATE`
- `PUBLISH_AS_HISTORICAL`
- `MIGRATE_TO_MAINTAINED`
- `EXTRACT_CANONICAL_RESULT`
- `DOCUMENT_ONLY`
- `EXCLUDE_GENERATED`
- `REVIEW_REQUIRED`

No source file, dataset record, manuscript, checkpoint, or experimental
output should enter the public repository until that classification has
been completed.

## Important archive categories

The original archive includes:

- upstream P-DARTS source code;
- skin-transferability extensions;
- dataset metadata and split manifests;
- search and evaluation configurations;
- successful and failed run records;
- model checkpoints;
- numerical intermediates;
- manuscripts, thesis material, and presentation files.

Historical scientific behavior must be preserved before reusable code is
refactored or sanitized.