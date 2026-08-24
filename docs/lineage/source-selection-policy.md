# Source-selection and lineage policy

## Core rule

The private archive is never copied wholesale. Public migration is selective,
reviewed, and traceable to the preserved archive inventory and SHA-256 identity.

## Disposition classes

Every source candidate receives exactly one final disposition.

### `MIGRATE_TO_MAINTAINED`

Use when the scientific behavior should be represented in the maintained
package or maintained command-line workflows.

A maintained migration may involve refactoring, but the repository must record:

- the archive source path;
- the maintained destination;
- the scientific behavior being retained;
- intentional behavioral changes;
- removed workstation assumptions; and
- validation used to establish equivalence or compatibility.

### `PUBLISH_AS_HISTORICAL`

Use when a source file is scientifically important evidence but should not be
presented as the maintained implementation.

Historical publication requires:

- an explicit historical label;
- the original archive path;
- known authorship or derivation;
- known limitations;
- removal or parameterization of sensitive local paths;
- confirmation that no private data or credentials are embedded; and
- a release decision that permits public inclusion.

Formatting-only normalization must not silently change historical behavior.

### `UPSTREAM_REFERENCE_ONLY`

Use when a file is wholly or substantially derived from an external project
and the repository does not need to republish the full source.

The lineage record should identify the upstream project, file, revision when
known, license when known, and local differences. If revision or licensing is
unresolved, the source remains unpublished.

### `REIMPLEMENT_FROM_SPECIFICATION`

Use when required behavior is scientifically understood but the archived file
is unsuitable for direct migration because of coupling, quality, provenance,
or licensing concerns.

The new implementation must cite the scientific specification and document
which historical behavior it intentionally reproduces.

### `PRESERVE_PRIVATE`

Use for files that must remain outside public Git, including data manifests
that expose private structure, local paths that cannot be safely generalized,
credentials, unpublished sensitive material, or code with unresolved
publication authority.

### `EXCLUDE_GENERATED`

Use for caches, bytecode, generated logs, checkpoints, intermediate arrays, and
other non-source artifacts.

### `REVIEW_REQUIRED`

Use only as a temporary state when evidence is insufficient for a final
decision. The unresolved question and the evidence needed to resolve it must be
recorded.

## Maintained versus historical behavior

Maintained code is the supported repository interface. It should use
configuration rather than workstation paths, provide clear inputs and outputs,
and be testable without private data.

Historical code records what was used during the original research. It may
contain obsolete interfaces or implementation constraints, but it must not
contain credentials, private data, unsafe absolute paths, or misleading claims
of reproducibility.

Behavioral repairs must not be hidden. For example, replacing a tensor
contiguity-dependent `view` operation with `reshape` is a compatibility change
that must be documented even when numerical intent is unchanged.

## Upstream-derived code

P-DARTS and DARTS lineage must be treated explicitly. Similarity to public
upstream code does not establish permission to publish an unattributed copy.

Before republishing upstream-derived source, record:

- upstream repository or publication;
- upstream filename;
- revision or closest identifiable version;
- applicable license;
- local modifications; and
- reason republishing is necessary.

If the license or exact source revision cannot be established, prefer a
dependency, patch record, or clean reimplementation over copying the file.

## Public-release checks

Before any archived source enters Git, verify that it contains none of the
following:

- credentials, access tokens, or secrets;
- private dataset contents;
- participant or patient identifiers;
- personal workstation paths;
- unpublished confidential review material;
- generated checkpoints or numerical intermediates;
- embedded archives;
- ambiguous third-party ownership; or
- claims that exceed the available evidence.

## Traceability requirement

Each migrated, historical, reimplemented, or blocked source candidate must have
a machine-readable lineage record. The record must link the archive path to its
decision and, when applicable, its public destination.

The archive SHA-256 preserved in Batch 1 remains the identity anchor for all
lineage claims.
