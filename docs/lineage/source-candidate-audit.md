# Source-candidate audit

## Archive identity

- Archive: `PDARTS(1).zip`
- SHA-256: `f8b8e924d7e8cd98a5618831c634a656b6062629b54563e21e67df1b06bf3ae0`
- Audit method: ZIP entries were read and hashed without extraction.
- Source files copied into the repository: no.

## Candidate summary

| Candidate category | Count |
|---|---:|
| Python source files | 25 |
| Nested source archives | 2 |
| Total source candidates | 27 |
| Candidates containing Windows absolute-path indicators | 4 |
| Candidates containing Unix absolute-path indicators | 10 |
| Candidates requiring credential-reference review | 0 |
| Candidates exposing an apparent command-line interface | 18 |
| Candidates currently requiring release review | 21 |
| Duplicate source-path groups | 0 |
| Duplicate full-file SHA-256 groups | 0 |

## Interpretation

This audit identifies source candidates; it does not approve publication.

Absolute-path indicators identify portability and privacy review requirements.
They do not by themselves prove that a file contains private data.

Credential-reference indicators are conservative text-pattern matches. Each
match requires human review before publication and must not be interpreted as
confirmation that an actual credential is present.

Nested source archives require separate upstream, revision, license, and
local-modification review. They will not be copied into the public repository.

Duplicate hashes identify byte-identical candidates and may reveal repeated
upstream cores or duplicated historical implementations. Duplicate content will
not be republished unnecessarily.

## Machine-readable records

- `generated/source_candidates.csv` contains one row per source candidate,
  its archive path, full-file SHA-256, Batch 1 classification, preliminary
  scientific role, review indicators, and pending disposition.
- `generated/source_candidate_summary.json` records the audit identity and
  validation totals.

All candidates remain `REVIEW_REQUIRED` until the file-level lineage review
assigns a supported final disposition.
