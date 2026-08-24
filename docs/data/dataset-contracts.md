# Dataset contracts

## Common manifest fields

Every maintained image manifest uses these fields:

| Field | Meaning |
|---|---|
| `sample_id` | Dataset-local, nonidentifying sample key |
| `image_path` | Relative path below a user-supplied dataset root |
| `label_id` | Integer experiment label |
| `patient_id` | Grouping key when available; blank only when permitted |
| `dataset_id` | Stable repository dataset identifier |
| `split` | `train`, `validation`, or `test` |
| `split_mode` | Explicit split-generation protocol |

Absolute image paths are prohibited in public or generated portable manifests.

## Dataset identifiers

| Dataset | Identifier | Experiment class 5 |
|---|---|---|
| ISIC 2019 | `isic_2019` | SCC |
| PAD-UFES-20 | `pad_ufes_20` | SCC |
| DermaMNIST aligned task | `dermamnist` | VASC |

The class-5 difference is intentional and must not be silently remapped.

## Data-root handling

Dataset roots are runtime inputs. They must be supplied through configuration,
command-line arguments, or environment-specific files excluded from Git.

Maintained code must not include personal workstation defaults.

## Validation expectations

A valid manifest must:

1. use the configured dataset identifier;
2. use only configured label IDs;
3. use only relative image paths;
4. use one declared split mode;
5. contain unique sample IDs within a dataset;
6. include patient IDs when patient-grouped splitting is requested; and
7. keep each patient in exactly one partition under patient-grouped mode.
