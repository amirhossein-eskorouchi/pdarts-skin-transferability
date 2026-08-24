# Experiment Design

## Overview

The study separates architecture search from architecture evaluation.

During search, P-DARTS progressively increases the depth of the
supernetwork while pruning candidate operations. The resulting discrete
normal and reduction cells are then transferred to evaluation networks
of different depths.

Evaluation weights are initialized anew and trained on the applicable
target dataset.

## Primary search configurations

| Method | Search depth `n` | Progressive stage depths |
|---|---:|---|
| P-DARTS6 | 6 | 2, 4, 6 |
| P-DARTS8 | 8 | 4, 6, 8 |
| P-DARTS10 | 10 | 6, 8, 10 |
| DARTS6 | 6 | Non-progressive comparison |

The principal search configurations are repeated three times to obtain
three candidate architectures.

The maximum permitted number of skip connections is one per cell in the
skin-transferability P-DARTS experiments.

## Search-epoch provenance

The preserved successful run ledgers record:

- 25 epochs per progressive stage;
- three stages;
- 75 total search epochs.

The manuscript tables refer to 75 search epochs, but one prose sentence
states that 75 search epochs were used per stage.

Until an authoritative publication configuration resolves this wording,
the repository treats:

`25 epochs per stage × 3 stages = 75 total epochs`

as the historical implementation behavior, not as an unquestioned
publication specification.

## Evaluation depths

Discovered cells are stacked into evaluation networks with:

`m ∈ {2, 4, 6, 8, 10, 12, 14}`

The primary evaluation duration is 300 epochs.

A preliminary study compares selected combinations involving:

- 75 versus 150 search epochs;
- 300 versus 600 evaluation epochs.

Those preliminary settings must remain separate from the main
experiment matrix.

## Image resolution

Two transfer-evaluation resolutions are reported:

- 32×32;
- 224×224.

The lower resolution follows the computational scale traditionally used
in differentiable architecture-search studies.

The higher resolution assesses whether the observed architecture-depth
patterns persist when more image information is retained.

## Tasks

### Six-class classification

The principal ISIC-2019 to PAD-UFES-20 task uses the six-class
`isic_pad_six_class` schema.

DermaMNIST experiments use the separate
`dermamnist_archive_six_class` schema.

### Binary classification

The historical manuscript describes:

- malignant: MEL, BCC, SCC;
- benign: AK, BKL/SEK, NV.

The manuscript contains the abbreviation `SCK` in one binary-task
sentence. This is treated as a likely typographical variant of
BKL/SEK, but must remain flagged until the authoritative task mapping is
confirmed.

## Primary experiment families

### E1: Search and evaluation-depth comparison

- Search source: ISIC-2019.
- Methods: P-DARTS6, P-DARTS8, P-DARTS10, DARTS6.
- Targets: ISIC-2019 and PAD-UFES-20.
- Evaluation depths: 2 through 14 in increments of 2.
- Principal metric: accuracy.
- Replication: three candidate architectures per search configuration.

### E2: Search-source comparison

- Search sources: ISIC-2019, PAD-UFES-20, ISIC-2019-SUB.
- Search method: P-DARTS6.
- Target: PAD-UFES-20.
- Evaluation depths: 4, 6, 8, 10, 12, and 14.
- Purpose: separate source-data quality and size effects.

### E3: Cell-operation analysis

- Architectures: P-DARTS6, P-DARTS8, and P-DARTS10.
- Search sources: ISIC-2019, ISIC-2019-SUB, PAD-UFES-20.
- Outputs: average normal- and reduction-cell pooling counts.

### E4: Multi-target transfer at 32×32

- Search source: ISIC-2019.
- Search method: P-DARTS6.
- Targets: PAD-UFES-20 and DermaMNIST.
- Metrics: accuracy, weighted F1, TPR, TNR, and AUC.

### E5: Multi-target transfer at 224×224

The E4 design is repeated at 224×224 to evaluate resolution effects.

### E6: Direct DermaMNIST search control

- Search source: DermaMNIST.
- Target: DermaMNIST.
- Resolution: 32×32.
- Purpose: compare transferred cells with cells searched directly on
  the target dataset.

### E7: Binary classification

- Search source: ISIC-2019.
- Search method: P-DARTS6.
- Targets: ISIC-2019 and PAD-UFES-20.
- Task: malignant-versus-benign classification.

### E8: Human-designed architecture comparison

- Target: PAD-UFES-20.
- Tasks: multiclass and binary.
- Comparators: InceptionNet, DenseNet, ResNet,
  Vision Transformer, and VGGNet.
- Baselines are described as trained from scratch under a controlled
  structural comparison.

## Metrics

The reported metric set includes:

- test accuracy;
- macro F1 where available;
- weighted F1;
- true positive rate;
- true negative rate;
- one-vs-rest ROC AUC;
- precision-recall AUC in available run artifacts;
- Brier score in available run artifacts;
- expected calibration error in available run artifacts.

Only metrics explicitly associated with the publication record should
be presented as publication results.

## Statistical analyses

The manuscript reports:

- Spearman rank correlation between source- and target-task rankings;
- Spearman correlation between accuracy and weighted F1/AUC;
- paired Wilcoxon signed-rank tests for resolution comparisons;
- rank-biserial correlation as an effect size;
- two-sample t-tests comparing transferred and directly searched
  architectures.

The implementation and aggregation unit for each statistical test must
be reconstructed before the tests are advertised as executable.