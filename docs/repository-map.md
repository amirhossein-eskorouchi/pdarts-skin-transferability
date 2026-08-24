# Repository map

## Scientific authority

| Area | Purpose | Authority |
|---|---|---|
| `docs/specification/` | Scientific questions, datasets, labels, experiments, and unresolved issues | Scientific specification |
| `results/publication_record/` | Manuscript-reported values | Canonical publication record |
| `docs/lineage/` | Archive identity, source decisions, attribution, and sanitization | Provenance record |
| `reference_implementations/historical/` | Sanitized historical project-specific code | Historical evidence only |
| `src/pdarts_skin/` | Supported independently authored utilities | Maintained software |
| `configs/` | Dataset and reproduction experiment contracts | Runtime specification |
| `results/reproduction/` | Future regenerated summaries | Reproduction namespace |

## Maintained code

The supported package is `src/pdarts_skin/`.

It must remain independent of restricted copied P-DARTS source.

## Historical code

Historical files preserve project behavior but may contain obsolete structure,
duplicated workflows, or unresolved runtime assumptions.

They must not be imported by maintained package modules.

## Generated documentation

Markdown tables under `results/publication_record/tables/` are generated from
canonical CSV records.

The CSV files remain the machine-readable source of truth.

## Private external material

The following remain outside Git:

- original PDARTS archive;
- datasets;
- real split manifests;
- checkpoints;
- NumPy arrays;
- experiment logs;
- manuscript PDFs; and
- nested source archives.

## Validation ownership

| Validator | Responsibility |
|---|---|
| `validate_data_contracts.py` | Dataset, label, and fictional-manifest contracts |
| `validate_experiment_configs.py` | Experiment configuration boundaries |
| `validate_publication_record.py` | Canonical result identity and provenance |
| `build_publication_tables.py --check` | Generated-table freshness |
| `audit_repository.py` | Repository-wide release boundary |
| `unittest` | Maintained behavioral tests |
