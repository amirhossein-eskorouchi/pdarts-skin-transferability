# Publication-Result Provenance

## Status

The machine-readable files in this directory preserve values explicitly
reported in the available manuscript.

They are labeled:

`manuscript_reported_not_regenerated`

This means the values are part of the available scientific record, but
the maintained repository has not yet regenerated them.

## Included records

- `headline_results.csv`
- `architecture_comparison.csv`
- `statistical_results.csv`
- `transfer_comparison_pvalues.csv`
- `data_partitions.csv`
- `label_schemas.csv`
- `experiment_matrix.csv`

## Aggregation caution

The manuscript reports a mixture of:

- means across three discovered architectures;
- standard deviations across repeated evaluations;
- best individual runs;
- values aggregated by evaluation depth;
- statistics pooled across datasets and seeds;
- high-resolution entries with incomplete or unclear replication.

These aggregation types must not be treated as interchangeable.

## Statistical caution

The repository preserves the reported statistical values without yet
claiming that their exact input rows, aggregation units, or assumptions
have been reconstructed.

In particular:

- the resolution analysis reports a negative rank-biserial correlation
  as favoring 224×224 under the manuscript's stated convention;
- two-sample t-tests in Table 15 are preserved as reported;
- no Table 15 comparison reaches the conventional 0.05 threshold;
- nonsignificant tests must not be described as proving equivalence.

## Publication-version caution

The available manuscript is a peer-review package rather than a clean
final publisher version.

Before public release, citation metadata and numerical tables must be
checked against the final authorized publication record.