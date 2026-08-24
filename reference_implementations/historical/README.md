# Historical skin-lesion research sources

This directory contains selectively published snapshots of project-specific
Python files from the private P-DARTS research archive.

These files document historical search, evaluation, dataset, transform, and
split workflows. They are not the maintained repository interface and are not
claimed to run independently from this directory.

## Release-only transformations

Each file was verified against its original archive SHA-256 before publication.

Only the following transformations were applied:

1. a historical provenance header was added;
2. the private HPC project root was replaced with `PROJECT_ROOT`;
3. the private Windows project root was replaced with `PROJECT_ROOT`;
4. the workstation account identifier in author metadata was replaced with
   `original project author (workstation identifier redacted)`; and
5. line endings were normalized to LF.

No upstream P-DARTS core source was copied.

The original archive identity is:

`f8b8e924d7e8cd98a5618831c634a656b6062629b54563e21e67df1b06bf3ae0`

Original hashes, sanitized hashes, and replacement counts are recorded in:

`docs/lineage/generated/historical_sanitization_manifest.csv`

## Directory roles

- `data/` contains historical dataset, transform, and split code.
- `search/` contains historical skin-lesion architecture-search drivers.
- `evaluation/` contains historical genotype evaluation and transfer drivers.

## Maintained-code boundary

Later batches will create maintained, configurable, and tested modules
separately. Historical files remain provenance evidence.

## Runtime status

Python syntax execution is deferred because a functional Python runtime is not
currently available on the preservation workstation.
