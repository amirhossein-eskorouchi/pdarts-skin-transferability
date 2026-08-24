# Security and sensitive-data policy

## Reporting

Please report security or sensitive-data concerns privately to the repository
maintainers rather than opening a public issue.

## Sensitive material

This repository must not contain:

- credentials, tokens, passwords, or private keys;
- patient or participant identifiers;
- protected health information;
- private image-level manifests;
- private dataset copies;
- personal workstation paths;
- unpublished confidential review material; or
- restricted third-party source distributed without authority.

## Supported software

Security fixes apply to the maintained package under `src/pdarts_skin/`.

Historical files under `reference_implementations/historical/` are provenance
evidence and are not a supported runtime interface.

## Research-artifact boundary

Checkpoints, predictions, NumPy arrays, logs, and large experiment artifacts
must remain outside Git.

If sensitive material is discovered, stop further publication, preserve the
necessary internal evidence, remove the public exposure through an appropriate
history-repair process, and rotate any affected credential.
