# Canonical Scientific Specification

This directory defines the scientific behavior and claims that the
maintained repository must preserve.

## Purpose

The repository studies architecture transferability in Progressive
Differentiable Architecture Search for skin lesion diagnosis.

The principal workflow is architecture transfer rather than conventional
pretrained-weight transfer:

1. search for a discrete neural cell on a source dataset;
2. transfer the discovered cell structure to a target dataset;
3. initialize the target model with new weights;
4. train the transferred architecture from scratch;
5. evaluate how source data, search depth, evaluation depth, cell
   operations, image resolution, and target-dataset properties affect
   performance.

## Authority hierarchy

When project artifacts disagree, use the following order of authority:

1. finalized publication record;
2. final thesis record;
3. preserved experiment configurations and successful run ledgers;
4. historical implementation behavior;
5. presentation material;
6. exploratory, failed, incomplete, or duplicate run artifacts.

No exploratory output should silently replace a publication-record value.

## Required specification layers

Batch 2 will document:

- research questions and contribution boundaries;
- source and target datasets;
- experiment-specific label schemas;
- data-splitting behavior;
- architecture-search configurations;
- architecture-evaluation configurations;
- transferability comparisons;
- image-resolution experiments;
- binary and multiclass tasks;
- evaluation metrics;
- statistical analyses;
- canonical publication results;
- incomplete or unresolved provenance.

## Reproducibility boundary

The attached research archive does not contain the complete run-level
record for every table and figure in the publication.

Therefore, the repository distinguishes:

1. publication-record preservation;
2. available-run provenance;
3. behavioral software reconstruction;
4. exact numerical reproduction.

The repository must not claim exact numerical reproduction until the
required data, configurations, genotypes, random states, and run-level
records have been reconciled and successfully rerun.