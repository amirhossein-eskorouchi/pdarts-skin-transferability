# Contributing

Contributions are welcome when they preserve the repository's scientific,
privacy, licensing, and provenance boundaries.

## Before contributing

Read:

- `docs/specification/README.md`;
- `docs/data/README.md`;
- `docs/lineage/source-selection-policy.md`;
- `docs/lineage/upstream-attribution.md`; and
- `docs/reproducibility/README.md`.

## Development setup

Install the maintained package:

    python -m venv .venv
    python -m pip install --upgrade pip
    python -m pip install -e .
    python -m pip install -r requirements-dev.txt

Run all checks:

    python scripts/validate_data_contracts.py
    python scripts/validate_experiment_configs.py
    python scripts/validate_publication_record.py
    python scripts/build_publication_tables.py --check
    python scripts/audit_repository.py
    python -m unittest discover -s tests -v

## Contribution rules

A contribution must not include:

- research images;
- patient or participant identifiers;
- real private manifests;
- local workstation paths;
- credentials or tokens;
- model checkpoints;
- NumPy intermediates;
- manuscript PDFs;
- embedded archives; or
- upstream P-DARTS source copied without appropriate authority.

## Result contributions

New experimental values must go below `results/reproduction/`.

They must include:

- experiment configuration;
- Git commit;
- environment record;
- dataset version;
- split mode;
- split-manifest SHA-256;
- seed;
- aggregation method; and
- explicit regenerated-result provenance.

Do not edit canonical publication values to match a new run.

## Historical files

Historical snapshots require:

- original archive path;
- original SHA-256;
- public destination;
- sanitization record;
- sanitized SHA-256; and
- an explicit historical-source header.

## Pull requests

Pull requests should explain:

- scientific purpose;
- files changed;
- provenance impact;
- privacy and licensing review;
- validation performed; and
- whether numerical behavior changed.
