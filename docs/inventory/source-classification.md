# Source Archive Classification

## Audited source archive

- Archive: `PDARTS(1).zip`
- Size: `350.86 MB`
- Files: `774`
- Directories: `71`
- SHA-256: `f8b8e924d7e8cd98a5618831c634a656b6062629b54563e21e67df1b06bf3ae0`

The original archive remains unchanged and outside the Git repository.

## Preliminary classification summary

| Classification | Files | Meaning |
|---|---:|---|
| `PRESERVE_PRIVATE` | 605 | Retain in the immutable research archive; do not publish directly. |
| `PUBLISH_AS_HISTORICAL` | 10 | Candidate historical source, subject to provenance and licensing review. |
| `MIGRATE_TO_MAINTAINED` | 15 | Historical logic that may be rebuilt as configurable maintained software. |
| `EXTRACT_CANONICAL_RESULT` | 116 | Compact result or genotype requiring manuscript reconciliation. |
| `DOCUMENT_ONLY` | 2 | Cite or link through an authorized public source instead of committing the file. |
| `EXCLUDE_GENERATED` | 7 | Generated cache or disposable repository noise. |
| `REVIEW_REQUIRED` | 19 | Requires a manual decision before any public use. |

## Governing rule

The preliminary classification is an audit aid, not final authorization
to publish a file.

No historical implementation, dataset record, result artifact, model
checkpoint, manuscript, or figure enters the public repository until its
provenance, licensing, privacy, and scientific role have been verified.

## Public repository strategy

The repository will contain:

1. a reusable and configurable implementation;
2. selected provenance-safe historical source;
3. canonical genotypes and compact result tables;
4. experiment configurations;
5. dataset acquisition and preparation instructions;
6. tests, validation, and reproducibility documentation.

The repository will not directly contain:

1. the original source ZIP;
2. raw dataset images;
3. raw PAD-UFES-20 patient metadata by default;
4. workstation-specific split manifests;
5. the complete checkpoint archive;
6. intermediate NumPy arrays;
7. detailed raw logs;
8. reviewer-response material;
9. Python bytecode or caches.

## Next review

Batch 2 will reconcile the paper, thesis, code, genotypes, ledgers, and
available outputs into a canonical scientific specification.