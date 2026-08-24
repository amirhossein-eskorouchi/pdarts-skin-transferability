# Data boundary

No research images, patient-level records, private manifests, or generated
dataset copies are stored in this repository.

This directory documents the public data interface required by the maintained
implementation.

## Datasets

The study uses three public external datasets:

- ISIC 2019;
- PAD-UFES-20; and
- DermaMNIST.

Users must obtain each dataset from its authorized distributor and comply with
the dataset's current access terms, licenses, and citation requirements.

## Repository boundary

The repository may contain:

- dataset configuration;
- label schemas;
- manifest schemas;
- split-generation logic;
- fictional example manifests;
- aggregate publication counts; and
- validation utilities.

The repository must not contain:

- downloaded images;
- patient identifiers;
- real image-level manifests;
- local dataset paths;
- credentials;
- transformed image copies;
- NumPy dataset arrays; or
- split files derived from private local storage.

## Split modes

Two split modes are distinguished:

- `historical_image_level`: preserves the historical experiment definition for
  behavioral reconstruction; and
- `patient_grouped`: the required leakage-resistant mode for new PAD-UFES-20
  experiments when patient identifiers are available.

Results from these modes must never be combined without an explicit split-mode
label.

## Configuration

Machine-readable dataset contracts are stored in `configs/datasets/`.
Schemas are stored in `schemas/`.

The files in `examples/manifests/` are fictional interface examples only.
They are not subsets of the research datasets.
