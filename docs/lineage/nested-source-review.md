# Nested-source lineage review

## Purpose

The private source archive contains two nested ZIP files that may represent
bundled upstream code, historical snapshots, or duplicated project source.
This review compares their Python files with the 25 outer Python source
candidates without extracting or publishing either nested archive.

The comparison establishes content relationships only. A filename or SHA-256
match does not independently establish authorship, upstream revision, or
license.

## Nested archive summary

| Nested archive | Files | Python files |
|---|---:|---:|
| `PDARTS/Github/pdarts-master - Copy.zip` | 11 | 11 |
| `PDARTS/Github/pdarts-master.zip` | 14 | 14 |

## Outer-to-nested comparison

| Comparison status | Outer Python files |
|---|---:|
| Exact basename and SHA-256 match | 12 |
| Same basename but different content | 1 |
| Exact SHA-256 under different basename | 0 |
| No nested Python counterpart | 12 |

Duplicate SHA-256 groups among nested Python entries:
11

## Exact bundled counterparts

- `PDARTS/Github/master/01_skin_csv_dataset.py`
- `PDARTS/Github/master/02_skin_transforms.py`
- `PDARTS/Github/master/genotypes.py`
- `PDARTS/Github/master/model.py`
- `PDARTS/Github/master/model_search.py`
- `PDARTS/Github/master/operations.py`
- `PDARTS/Github/master/test.py`
- `PDARTS/Github/master/test_imagenet.py`
- `PDARTS/Github/master/train_cifar.py`
- `PDARTS/Github/master/train_imagenet.py`
- `PDARTS/Github/master/train_search.py`
- `PDARTS/Github/master/visualize.py`

These files are byte-identical to files inside a bundled source archive.
They require upstream identification and licensing review before any public
migration. Republishing duplicate copies is not justified by this match alone.

## Possible locally modified counterparts

- `PDARTS/Github/master/utils.py`

These files share a basename with bundled Python source but differ in content.
They require line-level review to distinguish intentional project changes from
version drift or unrelated same-name files.

## Files without nested counterparts

- `PDARTS/Github/master/03_run_search_skin.py`
- `PDARTS/Github/master/03_run_search_skinTask2 - Copy.py`
- `PDARTS/Github/master/03_run_search_skinTask2.py`
- `PDARTS/Github/master/04_multieval_genotype_skin.py`
- `PDARTS/Github/master/04_multieval_genotype_skin_g0allm.py`
- `PDARTS/Github/master/04_multieval_genotype_skinaallinone.py`
- `PDARTS/Github/master/04_OnenSevenmTwodataset.py`
- `PDARTS/Github/master/Derma_split.py`
- `PDARTS/Github/master/skin_csv_dataset.py`
- `PDARTS/Github/master/skin_transforms.py`
- `PDARTS/Github/master/splits.py`
- `PDARTS/split to classes.py`

The absence of a nested counterpart supports project-specific review but does
not itself prove original authorship.

## Release decision

Both nested ZIP files remain `PRESERVE_PRIVATE`. They will not be committed,
expanded into the repository, or treated as dependency packages.

Outer Python files remain pending file-level disposition. Exact matches should
normally be represented through upstream attribution, dependency information,
or a patch record rather than duplicated publication. Modified counterparts
must have their changes documented before migration.

## Machine-readable evidence

- `generated/nested_source_inventory.csv` records every file inside the two
  nested source archives with its nested path, size, extension, and SHA-256.
- `generated/outer_to_nested_comparison.csv` records the relationship between
  each outer Python candidate and nested Python content.
