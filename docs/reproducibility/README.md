# Reproducibility

This directory documents how future regenerated results remain separate from
the canonical publication record.

## Result namespaces

- `results/publication_record/`: manuscript-reported values preserved as
  scientific records;
- future `results/reproduction/`: values produced by maintained workflows; and
- historical archive outputs: private evidence that is not automatically a
  public reproduction result.

Every experiment configuration sets:

    "result_namespace": "reproduction"

Maintained workflows must never write into `results/publication_record/`.

## Initial reproducibility configurations

Three experiment configurations are currently provided:

- `E1`: P-DARTS6 search and evaluation-depth transfer;
- `E4`: 32-pixel multi-target architecture transfer; and
- `E5`: 224-pixel multi-target architecture transfer.

These records freeze important scientific intent without claiming that the
experiments have been rerun.

## Architecture-only transfer

The configured transfer protocol moves architecture structure only.

Target evaluation must:

- construct the transferred architecture;
- initialize new target-training weights;
- train on the target dataset; and
- avoid loading source-trained model weights.

## Upstream boundary

The experiment configurations require:

    external_authorized_dependency_required

No restricted upstream P-DARTS core source is bundled with the maintained
package.

## Validation

When Python is available, run:

    python scripts/validate_data_contracts.py
    python scripts/validate_experiment_configs.py
    python -m unittest discover -s tests -v

GitHub Actions runs these checks on Python 3.10, 3.11, and 3.12.
