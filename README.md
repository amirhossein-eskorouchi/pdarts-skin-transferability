<!-- PUBLICATION-LAYER-BEGIN -->

# P-DARTS Skin Transferability

Architecture transferability with Progressive Differentiable Architecture Search for skin lesion diagnosis.

[![Python 3.10-3.12](https://img.shields.io/badge/python-3.10--3.12-blue.svg)](https://www.python.org/)
[![DOI](https://img.shields.io/badge/DOI-10.1080%2F24725579.2026.2622416-blue.svg)](https://doi.org/10.1080/24725579.2026.2622416)
[![CI](https://github.com/amirhossein-eskorouchi/pdarts-skin-transferability/actions/workflows/ci.yml/badge.svg)](https://github.com/amirhossein-eskorouchi/pdarts-skin-transferability/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

This repository reconstructs, documents, and tests the computational workflow associated with the following peer-reviewed study:

> A. Vo, L. He, A. Eskorouchi, and H. Wang, “Understanding knowledge transferability in differentiable architecture search for skin lesion diagnosis,” *IISE Transactions on Healthcare Systems Engineering*, vol. 16, no. 1, pp. 71–90, 2026. https://doi.org/10.1080/24725579.2026.2622416

The project investigates whether architectures discovered through Progressive Differentiable Architecture Search can transfer effectively across ISIC-2019, PAD-UFES-20, and DermaMNIST skin-lesion classification settings.

> **Research-use notice:** This repository is research software. It is not intended for clinical diagnosis, treatment decisions, patient care, or deployment as a medical device.

## Publication

**Anh Vo, Lu He, Amirhossein Eskorouchi, and Haifeng Wang**

**Understanding knowledge transferability in differentiable architecture search for skin lesion diagnosis**

*IISE Transactions on Healthcare Systems Engineering*, Volume 16, Issue 1, pages 71–90, 2026.

- [DOI: 10.1080/24725579.2026.2622416](https://doi.org/10.1080/24725579.2026.2622416)
- [Full article on Taylor & Francis](https://www.tandfonline.com/doi/full/10.1080/24725579.2026.2622416)
- [Abstract and publication details](https://www.tandfonline.com/doi/abs/10.1080/24725579.2026.2622416)
- [Citation instructions](docs/CITATION.md)
- [Citation File Format](CITATION.cff)
- [BibTeX citation](CITATION.bib)

The article PDF is not redistributed in this repository. Use the DOI or publisher links to access the authorized publication.

## Citation

If you use this repository, its scientific records, or the associated methodology, please cite the publication above.

Machine-readable citation metadata is available in:

- [CITATION.cff](CITATION.cff)
- [CITATION.bib](CITATION.bib)
- [docs/CITATION.md](docs/CITATION.md)

## Documentation

| Topic | Document |
|---|---|
| Scientific specification | [docs/specification/README.md](docs/specification/README.md) |
| Scientific scope | [docs/specification/scientific-scope.md](docs/specification/scientific-scope.md) |
| Data and labels | [docs/specification/data-and-labels.md](docs/specification/data-and-labels.md) |
| Experiment design | [docs/specification/experiment-design.md](docs/specification/experiment-design.md) |
| Data boundary | [docs/data/README.md](docs/data/README.md) |
| Dataset contracts | [docs/data/dataset-contracts.md](docs/data/dataset-contracts.md) |
| Split protocols | [docs/data/split-protocols.md](docs/data/split-protocols.md) |
| Source lineage | [docs/lineage/README.md](docs/lineage/README.md) |
| Upstream attribution | [docs/lineage/upstream-attribution.md](docs/lineage/upstream-attribution.md) |
| Reproducibility | [docs/reproducibility/README.md](docs/reproducibility/README.md) |
| Environment | [docs/reproducibility/environment.md](docs/reproducibility/environment.md) |
| Publication results | [docs/results/README.md](docs/results/README.md) |
| Result interpretation | [docs/results/interpretation.md](docs/results/interpretation.md) |
| Maintained software | [docs/software/README.md](docs/software/README.md) |
| Repository map | [docs/repository-map.md](docs/repository-map.md) |
| Limitations | [docs/limitations.md](docs/limitations.md) |
| Contributing | [CONTRIBUTING.md](CONTRIBUTING.md) |
| Security | [SECURITY.md](SECURITY.md) |
| Changelog | [CHANGELOG.md](CHANGELOG.md) |

## License

Independently authored repository content is available under the [MIT License](LICENSE).

Historical snapshots and references to third-party P-DARTS material retain their original provenance and licensing boundaries. Review [upstream attribution](docs/lineage/upstream-attribution.md) before reusing historical or upstream-derived material.

<!-- PUBLICATION-LAYER-END -->

## Repository details

A provenance-first repository for studying architecture transferability with
Progressive Differentiable Architecture Search in skin-lesion diagnosis.

The scientific question is whether a cell architecture searched on one
skin-lesion dataset can transfer to another dataset when the architecture is
retained but all target-training weights are newly initialized.

## Repository status

This repository currently provides:

- a verified inventory of the private research archive;
- an explicit scientific specification;
- machine-readable publication-result records;
- dataset, label, and split contracts;
- sanitized historical project-specific workflows;
- documented upstream P-DARTS attribution and licensing boundaries;
- independently authored data-validation and analysis utilities;
- priority reproduction experiment configurations;
- tests and continuous integration; and
- deterministic human-readable publication tables.

The repository does not claim exact numerical reproduction of the manuscript.

## Scientific boundary

Architecture transfer means:

1. search or select an architecture on a source dataset;
2. transfer the architecture structure;
3. initialize new weights for the target task; and
4. train and evaluate on the target dataset.

Source-trained model weights are not transferred.

## Datasets

The scientific record covers:

- ISIC 2019;
- PAD-UFES-20; and
- DermaMNIST.

No research images, patient-level records, or real image manifests are stored
in Git. Users must obtain datasets from their authorized distributors.

Dataset-specific class semantics are explicit:

- class 5 is SCC for ISIC 2019 and PAD-UFES-20;
- class 5 is VASC for the aligned DermaMNIST task.

## Important split limitation

Historical PAD-UFES-20 manifests use image-level splitting and contain
patient-overlap risk.

The repository distinguishes:

- `historical_image_level`, for behavioral reconstruction; and
- `patient_grouped`, for new leakage-resistant PAD-UFES-20 experiments.

Results from these modes must not be pooled or presented as equivalent.

## Canonical publication record

Manuscript-reported values are stored in:

    results/publication_record/

They carry the provenance status:

    manuscript_reported_not_regenerated

Future regenerated values belong only in:

    results/reproduction/

Selected preserved headline values include:

| Task | Target | Resolution | Reported accuracy |
|---|---|---:|---:|
| Multiclass P-DARTS6 mean | PAD-UFES-20 | 32 | 62.32% |
| Multiclass best individual run | PAD-UFES-20 | 32 | 63.70% |
| Binary best individual run | PAD-UFES-20 | 32 | 97.71% |
| Multiclass P-DARTS6 mean | DermaMNIST | 224 | 79.48% |
| Multiclass P-DARTS6 mean | PAD-UFES-20 | 224 | 69.06% |

These are publication records, not outputs generated by the maintained package.

## Upstream P-DARTS boundary

The private archive contains ten outer Python files that are byte-identical to
bundled P-DARTS core files.

They are not republished here.

The official P-DARTS repository uses a custom license restricting the software
to noncommercial testing and evaluation. The exact Git revision represented by
the private bundles is unresolved.

See:

- `docs/lineage/upstream-attribution.md`;
- `docs/lineage/generated/upstream_reference_files.csv`; and
- `docs/lineage/utils-compatibility-difference.md`.

## Maintained package

The independently authored package is `pdarts_skin`.

It provides:

- dataset-configuration loading;
- portable manifest validation;
- patient-leakage checks;
- deterministic patient-group assignment;
- classification metrics;
- publication-record validation; and
- command-line manifest validation.

It does not contain copied P-DARTS architecture-search code.

## Installation

Create a virtual environment and install the maintained package:

    python -m venv .venv
    python -m pip install --upgrade pip
    python -m pip install -e .
    python -m pip install -r requirements-dev.txt

Or use Conda:

    conda env create -f environment.yml
    conda activate pdarts-skin-maintained

## Validation

Run:

    python scripts/validate_data_contracts.py
    python scripts/validate_experiment_configs.py
    python scripts/validate_publication_record.py
    python scripts/build_publication_tables.py --check
    python scripts/audit_repository.py
    python -m unittest discover -s tests -v

GitHub Actions runs the maintained validation suite on Python 3.10, 3.11, and
3.12.

## Repository map

- `configs/`: dataset and experiment contracts;
- `docs/`: scientific, data, lineage, software, result, and reproducibility
  documentation;
- `examples/`: fictional interface examples;
- `reference_implementations/`: sanitized historical project-specific code;
- `results/publication_record/`: immutable manuscript-reported records;
- `results/reproduction/`: namespace for future regenerated summaries;
- `schemas/`: machine-readable JSON schemas;
- `scripts/`: validators, auditors, and table builders;
- `src/pdarts_skin/`: maintained package;
- `tests/`: standard-library tests; and
- `.github/workflows/`: continuous integration.

See `docs/repository-map.md` for the detailed ownership and authority map.

## Historical source warning

Files below `reference_implementations/historical/` are provenance evidence.

They are not the maintained interface, are not guaranteed to run independently,
and contain release-only sanitization documented by original and public
SHA-256 values.

## Contributing

See `CONTRIBUTING.md`.

Do not submit datasets, patient identifiers, checkpoints, private manifests,
credentials, or restricted upstream source.

## Citation

See `CITATION.cff`.

## License

Independently authored repository content is released under the MIT License.

Third-party datasets, publications, and upstream software remain governed by
their own terms. The MIT License does not relicense external materials.
