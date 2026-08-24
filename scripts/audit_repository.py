"""Repository-wide release-boundary audit."""

from __future__ import annotations

import csv
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = (
    "LICENSE",
    "CITATION.cff",
    "README.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "CHANGELOG.md",
    "pyproject.toml",
    "docs/specification/README.md",
    "docs/data/README.md",
    "docs/lineage/upstream-attribution.md",
    "docs/reproducibility/README.md",
    "results/publication_record/headline_results.csv",
    "results/reproduction/README.md",
    "src/pdarts_skin/__init__.py",
)

FORBIDDEN_SUFFIXES = {
    ".zip",
    ".pt",
    ".pth",
    ".ckpt",
    ".npy",
    ".npz",
    ".pyc",
    ".pdf",
    ".dcm",
}

PRIVATE_PATTERNS = (
    re.compile(
        r"/data/home/[A-Za-z0-9_.-]+/",
        re.IGNORECASE,
    ),
    re.compile(
        r"[A-Za-z]:\\Users\\[^\\\r\n]+",
        re.IGNORECASE,
    ),
    re.compile(
        r"D:\\IISE Transactions(?:\\|$)",
        re.IGNORECASE,
    ),
)

PRIVACY_AUDIT_SOURCE_FILES = {
    "audit_repository.py",
    "audit_source_archive.py",
}

PUBLICATION_PROVENANCE = "manuscript_reported_not_regenerated"


def fail(message: str) -> None:
    raise ValueError(message)


def repository_files() -> list[Path]:
    """Return only files tracked by Git.

    Runtime validation may create untracked bytecode, cache, coverage, or build
    artifacts. Those files are protected by .gitignore but are not part of the
    repository release boundary and must not cause a tracked-content audit to
    fail.
    """

    completed = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    relative_paths = [
        value
        for value in completed.stdout.decode("utf-8").split("\0")
        if value
    ]

    return [
        ROOT / relative_path
        for relative_path in relative_paths
    ]


def validate_required_files() -> None:
    for relative in REQUIRED_FILES:
        path = ROOT / relative

        if not path.is_file():
            fail(f"missing required file: {relative}")

        if path.stat().st_size == 0:
            fail(f"required file is empty: {relative}")


def validate_boundaries(files: list[Path]) -> None:
    for path in files:
        if path.suffix.lower() in FORBIDDEN_SUFFIXES:
            fail(f"forbidden file type: {path.relative_to(ROOT)}")

        if path.stat().st_size > 5 * 1024 * 1024:
            fail(f"file exceeds 5 MB: {path.relative_to(ROOT)}")

        if path.suffix.lower() not in {
            ".md",
            ".py",
            ".json",
            ".csv",
            ".toml",
            ".yml",
            ".yaml",
            ".cff",
            "",
        }:
            continue

        try:
            text = path.read_text(encoding="utf-8-sig")
        except UnicodeDecodeError:
            fail(f"expected text file is not UTF-8: {path.relative_to(ROOT)}")

        if "reference_implementations" in path.parts:
            continue

        if path.name in PRIVACY_AUDIT_SOURCE_FILES:
            continue

        for pattern in PRIVATE_PATTERNS:
            if pattern.search(text):
                fail(
                    f"private-path pattern found: {path.relative_to(ROOT)}"
                )


def validate_publication_record() -> None:
    root = ROOT / "results" / "publication_record"

    expected_counts = {
        "headline_results.csv": 10,
        "architecture_comparison.csv": 12,
        "statistical_results.csv": 17,
        "transfer_comparison_pvalues.csv": 12,
    }

    for filename, expected in expected_counts.items():
        with (root / filename).open(
            newline="",
            encoding="utf-8-sig",
        ) as handle:
            rows = list(csv.DictReader(handle))

        if len(rows) != expected:
            fail(
                f"{filename}: expected {expected} rows, found {len(rows)}"
            )

        if any(
            row.get("provenance_status") != PUBLICATION_PROVENANCE
            for row in rows
        ):
            fail(f"{filename}: invalid publication provenance")


def validate_historical_headers() -> None:
    historical = (
        ROOT
        / "reference_implementations"
        / "historical"
    )

    python_files = sorted(historical.rglob("*.py"))

    if len(python_files) != 14:
        fail(
            f"expected 14 historical Python files, found {len(python_files)}"
        )

    for path in python_files:
        text = path.read_text(encoding="utf-8-sig")

        if "HISTORICAL RESEARCH SOURCE" not in text:
            fail(
                f"historical provenance header missing: "
                f"{path.relative_to(ROOT)}"
            )


def validate_upstream_boundary() -> None:
    forbidden_modules = {
        "genotypes.py",
        "model.py",
        "model_search.py",
        "operations.py",
        "train_search.py",
        "utils.py",
    }

    maintained = ROOT / "src" / "pdarts_skin"

    present = {
        path.name
        for path in maintained.glob("*.py")
    }

    copied = present & forbidden_modules

    if copied:
        fail(
            f"restricted upstream-like modules in maintained package: "
            f"{sorted(copied)}"
        )


def main() -> int:
    files = repository_files()

    validate_required_files()
    validate_boundaries(files)
    validate_publication_record()
    validate_historical_headers()
    validate_upstream_boundary()

    print(f"[OK] Repository files audited: {len(files)}")
    print("[OK] Required release files are present.")
    print("[OK] Forbidden binary-material check passed.")
    print("[OK] Five-megabyte file-size boundary passed.")
    print("[OK] Private-path scan passed.")
    print("[OK] Publication-result provenance passed.")
    print("[OK] Historical-source headers passed.")
    print("[OK] Restricted upstream-source boundary passed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError) as exc:
        print(f"[FAIL] {exc}", file=sys.stderr)
        raise SystemExit(1)
