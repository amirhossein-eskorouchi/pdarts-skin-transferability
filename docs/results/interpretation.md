# Scientific interpretation boundaries

## Architecture transfer

The study evaluates architecture transfer, not pretrained-weight transfer.

The architecture is selected on a source dataset, rebuilt for the target task,
initialized with new weights, and trained on target data.

## Reported performance

The canonical record includes individual-run values, means, dispersions,
architecture comparisons, correlations, hypothesis-test p-values, and effect
sizes.

These aggregation types must not be treated as interchangeable.

## Statistical caution

A nonsignificant p-value does not establish equivalence.

Correlation estimates based on seven evaluation depths have limited sample
size and should be interpreted with their reported p-values and context.

## Resolution comparisons

The 32-pixel and 224-pixel comparisons preserve the manuscript-reported
Wilcoxon results and rank-biserial effect sizes.

They remain reported results until independently regenerated.

## PAD split limitation

Historical PAD-UFES-20 results use the historical image-level split definition,
which contains patient-overlap risk.

Future patient-grouped results must be labeled separately and must not be
pooled with the historical publication record.
