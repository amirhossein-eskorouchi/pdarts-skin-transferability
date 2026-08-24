# Limitations

## Reproduction status

The repository preserves publication values and historical evidence but does
not establish exact numerical reproduction.

## Upstream implementation

The P-DARTS core implementation is not redistributed.

Executing full neural architecture search requires an authorized upstream
implementation or an independently developed compatible implementation.

## Dataset access

Datasets are not bundled. Availability, licensing, preprocessing, and version
differences may affect future results.

## Historical PAD split

Historical PAD-UFES-20 partitions contain patient-overlap risk.

Future patient-grouped results answer a different, leakage-resistant
experimental question and must be reported separately.

## Environment uncertainty

The archive contains evidence from multiple Python, PyTorch, CUDA, operating
system, and hardware environments.

A single exact historical environment has not been established.

## Archive completeness

Available search and evaluation run directories do not cover the entire
publication experiment grid.

Missing runs must not be inferred as successfully completed.

## Statistical interpretation

Nonsignificant tests do not prove equivalence.

Several reported correlation analyses use only seven architecture depths and
should be interpreted cautiously.

## Maintained package scope

The maintained package currently covers reproducibility contracts, validation,
grouped splitting, metrics, and publication records.

It does not yet implement full GPU architecture search or training.
