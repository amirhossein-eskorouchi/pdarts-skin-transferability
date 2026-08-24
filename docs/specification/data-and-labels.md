# Data and Label Specification

## Data-distribution policy

Dataset images are not distributed through this repository.

Users should acquire each dataset from its authorized source and follow
the applicable license, terms of use, and citation requirements.

Raw dataset metadata and original absolute-path split manifests are not
published by default.

## Dataset roles

| Dataset | Study role | Acquisition characteristics |
|---|---|---|
| ISIC-2019 | Primary architecture-search source and same-dataset evaluation control | Primarily curated dermoscopic images |
| PAD-UFES-20 | Primary architecture-transfer target | Smartphone-acquired clinical images |
| ISIC-2019-SUB | Controlled source subset | ISIC subset constructed to approximate PAD-UFES-20 sample size and imbalance |
| DermaMNIST | Additional transfer target and direct-search control | Standardized benchmark derived from HAM10000 |

## Publication-reported sample counts

The manuscript reports that three ISIC-2019 categories were excluded,
leaving 24,839 images for the principal six-class experiment.

The publication reports:

| Dataset | Train | Validation | Test | Total |
|---|---:|---:|---:|---:|
| ISIC-2019 | 13,909 | 5,962 | 4,968 | 24,839 |
| PAD-UFES-20 | 1,286 | 552 | 460 | 2,298 |

The intended split proportions are:

- 20% test;
- 80% development;
- development divided into 70% training and 30% validation;
- approximately 56% training, 24% validation, and 20% testing overall.

## Preserved-manifest count discrepancy

The available archive manifests contain:

| Dataset | Train | Validation | Test | Total |
|---|---:|---:|---:|---:|
| ISIC-2019 | 13,910 | 5,961 | 4,968 | 24,839 |
| PAD-UFES-20 | 1,287 | 552 | 459 | 2,298 |
| DermaMNIST prepared subset | 2,723 | 1,167 | 1,980 | 5,870 |

The ISIC and PAD totals agree with the publication, but one sample is
assigned to a different partition in each archived manifest set.

This discrepancy must remain explicit until the exact publication-era
split files or split-generation state are authoritatively identified.

## Historical PAD-UFES-20 grouping behavior

The preserved PAD-UFES-20 split manifests appear to have been produced
through stratified image-level splitting rather than patient-grouped
splitting.

Patient identifiers derived from the preserved filenames overlap across
the historical partitions:

| Partition comparison | Overlapping patient identifiers |
|---|---:|
| Train and validation | 219 |
| Train and test | 173 |
| Validation and test | 103 |

This creates a potential patient-level leakage concern because multiple
images associated with the same patient can appear in different
partitions.

The repository will therefore support two explicitly named modes:

1. `historical_image_stratified`
   - preserves the historical experimental behavior;
   - is required when reconstructing the publication workflow;
   - carries an explicit leakage warning.

2. `patient_grouped`
   - keeps each patient in only one partition;
   - is the recommended design for future evaluations;
   - must not be presented as the split used for the published results.

## Experiment-specific label schemas

A single universal six-class label map is not safe for all experiments.

### ISIC-2019 and PAD-UFES-20 transfer schema

The principal source-target experiment uses six aligned clinical
categories:

| ID | Canonical abbreviation | Description |
|---:|---|---|
| 0 | AK | Actinic keratosis/intraepithelial carcinoma |
| 1 | BCC | Basal cell carcinoma |
| 2 | BKL | Benign keratosis-like lesion |
| 3 | MEL | Melanoma |
| 4 | NV | Melanocytic nevus |
| 5 | SCC | Squamous cell carcinoma |

PAD-UFES-20 historical labels require mappings such as:

- `ACK` to `AK`;
- `SEK` to `BKL`;
- `NEV` to `NV`.

### DermaMNIST aligned schema

The available DermaMNIST preparation record uses:

| ID | Canonical abbreviation | Original DermaMNIST category |
|---:|---|---|
| 0 | AK | AKIEC |
| 1 | BCC | BCC |
| 2 | BKL | BKL |
| 3 | MEL | MEL |
| 4 | NV | NV |
| 5 | VASC | Vascular lesion |

Dermatofibroma is excluded from this archived six-class DermaMNIST
mapping.

Therefore, class ID 5 is not semantically equivalent across the
ISIC/PAD and DermaMNIST experiment families:

- ISIC/PAD class 5: SCC;
- archived DermaMNIST class 5: VASC.

Code, configurations, metrics, and result tables must identify the
applicable schema explicitly.

## Split reproducibility requirements

Every maintained split workflow must record:

- dataset version;
- source download record;
- label schema;
- split mode;
- random seed;
- grouping key;
- stratification key;
- class counts per partition;
- sample counts per partition;
- manifest SHA-256;
- whether patient or lesion overlap exists.

Absolute workstation paths must never be treated as canonical sample
identifiers.