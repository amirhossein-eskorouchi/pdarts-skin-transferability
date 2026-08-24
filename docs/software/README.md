# Maintained software boundary

The maintained package is `pdarts_skin`.

It provides independently authored utilities for:

- loading and validating dataset configurations;
- reading portable image manifests;
- enforcing dataset and label contracts;
- detecting patient leakage across partitions;
- deterministic patient-group assignment;
- dependency-free classification metrics; and
- command-line manifest validation.

## Deliberate exclusions

The maintained package does not contain:

- upstream P-DARTS core source;
- a copied DARTS or P-DARTS search network;
- private datasets or manifests;
- historical workstation paths;
- model checkpoints;
- claims of exact numerical reproduction; or
- the monolithic historical experiment drivers.

The upstream licensing and revision boundary is documented in
`docs/lineage/upstream-attribution.md`.

## Package layers

- `config.py`: dataset configuration contracts;
- `data.py`: manifest records and validation;
- `splits.py`: patient-group splitting and isolation;
- `metrics.py`: dependency-free classification metrics; and
- `cli.py`: manifest-validation command.

## Testing

Tests use only Python's standard library and fictional records.

When Python is available, run:

    python -m unittest discover -s tests -v

The deterministic patient assignment intentionally does not claim
class-stratified grouping. Class coverage must be evaluated after splitting.
