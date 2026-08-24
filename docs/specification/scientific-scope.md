# Scientific Scope

## Study identity

**Title:** Understanding Knowledge Transferability in Differentiable
Architecture Search for Skin Lesion Diagnosis

The study investigates whether a neural cell discovered through
Progressive Differentiable Architecture Search on one skin-lesion
dataset can be transferred to another dataset with different acquisition
conditions, sample size, class balance, and image characteristics.

## Meaning of architecture transfer

Architecture transfer in this repository means:

1. search for a discrete cell structure on a source dataset;
2. preserve the discovered normal and reduction cells;
3. stack those cells to form an evaluation network;
4. initialize new model weights for the evaluation task;
5. train the transferred architecture from scratch on the target data.

The primary study does not define transferability as copying the trained
source-model weights to the target model.

## Principal source and targets

- Primary source: ISIC-2019 dermoscopic images.
- Primary target: PAD-UFES-20 smartphone-acquired clinical images.
- Additional target: DermaMNIST.
- Same-domain control: search and evaluation on ISIC-2019.
- Additional comparisons: searches conducted on PAD-UFES-20,
  ISIC-2019-SUB, and DermaMNIST in specified experiments.

## Research questions

### RQ1: Cross-dataset architecture transfer

Can P-DARTS cells discovered on ISIC-2019 be trained successfully on
PAD-UFES-20 and DermaMNIST?

### RQ2: Search depth and evaluation depth

How do the number of cells used during search and the number of cells
used during final evaluation affect source- and target-dataset
performance?

### RQ3: Search-evaluation depth gap

Is transfer performance governed by the absolute difference between
search depth and evaluation depth, or primarily by the evaluation
network depth itself?

### RQ4: Source-data properties

How do source-dataset size, quality, acquisition modality, and
information content affect the quality of discovered architectures?

### RQ5: Cell operations

How are pooling operations, skip connections, and convolutional
operations associated with architecture behavior on different target
datasets?

### RQ6: Resolution and metric consistency

Do architecture-transfer trends persist at 32x32 and 224x224
resolutions and across accuracy, weighted F1, TPR, TNR, and AUC?

### RQ7: Multiclass and binary diagnosis

How do transferred P-DARTS architectures behave in six-class and
binary diagnostic formulations, and how do they compare with selected
human-designed architectures?

## Contribution boundary

The study supports a foundational investigation of architecture
transferability in skin-lesion classification.

The repository must not present the study as proving:

- clinical readiness;
- dermatologist-level performance;
- prospective diagnostic validity;
- patient-level external validation;
- fairness across demographic groups;
- robustness to all devices and populations;
- superiority over all neural architecture search methods;
- superiority of architecture transfer over pretrained feature
  transfer;
- exact numerical reproduction from the current public repository.

## Interpretation boundary

The publication record, historical software behavior, and future
reproduction results are separate evidence layers.

A corrected or improved future workflow must not silently replace the
historical workflow used for the reported study.