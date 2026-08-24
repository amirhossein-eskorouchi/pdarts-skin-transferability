# File-level source-lineage decisions

## Decision summary

| Final disposition | Candidates |
|---|---:|
| PUBLISH_AS_HISTORICAL | 14 |
| UPSTREAM_REFERENCE_ONLY | 10 |
| REIMPLEMENT_FROM_SPECIFICATION | 1 |
| PRESERVE_PRIVATE | 2 |
| **Total** | **27** |

These decisions replace the preliminary Batch 1 source classifications for
Batch 3 migration purposes. Batch 1 classifications remain preserved as the
original archive-level triage record.

## Project-specific historical sources

The following 14 project-specific files may be published only as reviewed,
sanitized historical snapshots. They are evidence of the original research
workflow, not the maintained repository interface.

| Private archive source | Planned historical destination |
|---|---|
| `PDARTS/Github/master/01_skin_csv_dataset.py` | `reference_implementations/historical/data/01_skin_csv_dataset.py` |
| `PDARTS/Github/master/02_skin_transforms.py` | `reference_implementations/historical/data/02_skin_transforms.py` |
| `PDARTS/Github/master/03_run_search_skin.py` | `reference_implementations/historical/search/03_run_search_skin.py` |
| `PDARTS/Github/master/03_run_search_skinTask2 - Copy.py` | `reference_implementations/historical/search/03_run_search_skinTask2 - Copy.py` |
| `PDARTS/Github/master/03_run_search_skinTask2.py` | `reference_implementations/historical/search/03_run_search_skinTask2.py` |
| `PDARTS/Github/master/04_multieval_genotype_skin.py` | `reference_implementations/historical/evaluation/04_multieval_genotype_skin.py` |
| `PDARTS/Github/master/04_multieval_genotype_skin_g0allm.py` | `reference_implementations/historical/evaluation/04_multieval_genotype_skin_g0allm.py` |
| `PDARTS/Github/master/04_multieval_genotype_skinaallinone.py` | `reference_implementations/historical/evaluation/04_multieval_genotype_skinaallinone.py` |
| `PDARTS/Github/master/04_OnenSevenmTwodataset.py` | `reference_implementations/historical/evaluation/04_OnenSevenmTwodataset.py` |
| `PDARTS/Github/master/Derma_split.py` | `reference_implementations/historical/data/Derma_split.py` |
| `PDARTS/Github/master/skin_csv_dataset.py` | `reference_implementations/historical/data/skin_csv_dataset.py` |
| `PDARTS/Github/master/skin_transforms.py` | `reference_implementations/historical/data/skin_transforms.py` |
| `PDARTS/Github/master/splits.py` | `reference_implementations/historical/data/splits.py` |
| `PDARTS/split to classes.py` | `reference_implementations/historical/data/split to classes.py` |

Before publication, each snapshot must pass:

1. exact archive SHA-256 verification;
2. credential and sensitive-identifier review;
3. absolute-path and private-directory review;
4. syntax validation;
5. sanitization limited to release-blocking local defaults;
6. a machine-readable patch manifest;
7. post-sanitization SHA-256 recording; and
8. a header that identifies the file as historical.

The original archived bytes remain preserved only by the private archive and
the Batch 1/Batch 3 hash records.

## Upstream-reference-only sources

The following 10 outer files are byte-identical to bundled P-DARTS core files
and will not be copied into the public repository.

| Outer archive source | Bundled counterpart |
|---|---|
| `PDARTS/Github/master/genotypes.py` | `pdarts-master/genotypes.py` |
| `PDARTS/Github/master/model.py` | `pdarts-master/model.py` |
| `PDARTS/Github/master/model_search.py` | `pdarts-master/model_search.py` |
| `PDARTS/Github/master/operations.py` | `pdarts-master/operations.py` |
| `PDARTS/Github/master/test.py` | `pdarts-master/test.py` |
| `PDARTS/Github/master/test_imagenet.py` | `pdarts-master/test_imagenet.py` |
| `PDARTS/Github/master/train_cifar.py` | `pdarts-master/train_cifar.py` |
| `PDARTS/Github/master/train_imagenet.py` | `pdarts-master/train_imagenet.py` |
| `PDARTS/Github/master/train_search.py` | `pdarts-master/train_search.py` |
| `PDARTS/Github/master/visualize.py` | `pdarts-master/visualize.py` |

Their public representation will be provenance documentation identifying the
upstream project, closest verifiable source, licensing status, and required
interfaces. If the exact revision or license remains unresolved, implementation
will proceed through an approved dependency or a separately documented clean
implementation.

## Modified upstream-related utility

PDARTS/Github/master/utils.py shares its basename with the bundled P-DARTS
utility but differs in content.

Final disposition: REIMPLEMENT_FROM_SPECIFICATION.

The file will not be copied directly. The exact difference must first be
recorded, including whether it is a compatibility repair, behavioral change, or
version drift. Only the required behavior may then enter the maintained package
with focused tests and explicit attribution.

## Private nested archives

The following nested archives remain outside public Git:

- `PDARTS/Github/pdarts-master - Copy.zip`
- `PDARTS/Github/pdarts-master.zip`

They are lineage evidence, not distributable repository artifacts.

## Maintained implementation boundary

No archived experiment driver becomes maintained merely through historical
publication. Later batches will construct maintained modules and workflows from:

- the frozen scientific specification;
- reviewed project-specific behavior;
- explicit P-DARTS interfaces;
- configuration-driven paths;
- reproducibility requirements; and
- automated tests.

This separation prevents historical workstation assumptions, duplicated
scripts, and unresolved upstream code from becoming the repository's supported
software interface.

## Machine-readable decision record

generated/source_lineage_decisions.csv contains one final Batch 3 disposition
for each of the 27 source candidates.
