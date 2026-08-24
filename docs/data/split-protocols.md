# Split protocols

## Historical publication record

The publication and available-archive counts are preserved in
`results/publication_record/data_partitions.csv`.

Known publication totals are:

| Dataset | Train | Validation | Test | Total |
|---|---:|---:|---:|---:|
| ISIC 2019 | 13,909 | 5,962 | 4,968 | 24,839 |
| PAD-UFES-20 | 1,286 | 552 | 460 | 2,298 |

Available archived manifests differ by one image in adjacent partitions:

| Dataset | Train | Validation | Test | Total |
|---|---:|---:|---:|---:|
| ISIC 2019 | 13,910 | 5,961 | 4,968 | 24,839 |
| PAD-UFES-20 | 1,287 | 552 | 459 | 2,298 |
| DermaMNIST | 2,723 | 1,167 | 1,980 | 5,870 |

These discrepancies remain provenance issues and must not be silently resolved.

## Historical image-level mode

Identifier: `historical_image_level`

This mode exists only to reconstruct historical behavior. It does not guarantee
patient separation.

Archived PAD-UFES-20 manifests contain patient overlap between partitions.
Therefore, results using this mode must carry a leakage-risk warning.

## Patient-grouped mode

Identifier: `patient_grouped`

This is the required mode for new PAD-UFES-20 experiments when patient IDs are
available.

Requirements:

- one patient may appear in only one partition;
- partition assignment must be deterministic from a recorded seed;
- stratification behavior must be documented;
- the generated manifest must record the split mode;
- class coverage must be checked after grouping; and
- counts must be reported as newly generated results, not publication results.

## Reproducibility record

Every generated split should record:

- dataset identifier and source version;
- manifest SHA-256;
- split mode;
- seed;
- grouping field;
- stratification field;
- train/validation/test counts;
- class counts by partition; and
- generation timestamp and software revision.
