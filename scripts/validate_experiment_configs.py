"""Validate public experiment configurations without executing experiments."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = ROOT / "configs" / "experiments"

EXPECTED_IDS = {"E1", "E4", "E5"}
ALLOWED_DATASETS = {"isic_2019", "pad_ufes_20", "dermamnist"}
ALLOWED_RESOLUTIONS = {32, 224}
EXPERIMENT_ID = re.compile(r"^E[0-9]+[A-Z]?$")
ABSOLUTE_PATH = re.compile(r"(?:[A-Za-z]:[\\/]|/data/|/home/)")


def fail(message: str) -> None:
    raise ValueError(message)


def validate_config(path: Path) -> dict:
    config = json.loads(path.read_text(encoding="utf-8"))

    if config.get("schema_version") != 1:
        fail(f"{path}: unsupported schema_version")

    experiment_id = config.get("experiment_id", "")
    if not EXPERIMENT_ID.fullmatch(experiment_id):
        fail(f"{path}: invalid experiment_id")

    if config.get("result_namespace") != "reproduction":
        fail(f"{path}: result_namespace must be reproduction")

    if config.get("status") != "specified_not_executed":
        fail(f"{path}: initial status must be specified_not_executed")

    if config.get("source_dataset") not in ALLOWED_DATASETS:
        fail(f"{path}: invalid source_dataset")

    targets = config.get("target_datasets", [])
    if not targets or not set(targets) <= ALLOWED_DATASETS:
        fail(f"{path}: invalid target_datasets")

    if len(targets) != len(set(targets)):
        fail(f"{path}: duplicate target dataset")

    if config.get("resolution") not in ALLOWED_RESOLUTIONS:
        fail(f"{path}: unsupported resolution")

    seeds = config.get("seeds", [])
    if not seeds or len(seeds) != len(set(seeds)):
        fail(f"{path}: seeds must be nonempty and unique")

    if config.get("upstream_core_policy") != (
        "external_authorized_dependency_required"
    ):
        fail(f"{path}: invalid upstream core policy")

    serialized = json.dumps(config)
    if ABSOLUTE_PATH.search(serialized):
        fail(f"{path}: contains a local absolute path")

    evaluation = config.get("evaluation", {})
    if evaluation.get("initialization") != "new_weights_on_target":
        fail(f"{path}: target evaluation must use new weights")

    if evaluation.get("architecture_transfer_only") is False:
        fail(f"{path}: architecture-only transfer was disabled")

    return config


def main() -> int:
    paths = sorted(CONFIG_DIR.glob("*.json"))
    configs = [validate_config(path) for path in paths]

    identifiers = [config["experiment_id"] for config in configs]

    if set(identifiers) != EXPECTED_IDS:
        fail(
            f"expected experiment IDs {sorted(EXPECTED_IDS)}, "
            f"found {sorted(identifiers)}"
        )

    if len(identifiers) != len(set(identifiers)):
        fail("experiment IDs must be unique")

    e1 = next(
        config for config in configs
        if config["experiment_id"] == "E1"
    )

    if e1["search"]["progressive_stage_depths"] != [2, 4, 6]:
        fail("E1 must preserve P-DARTS6 progressive depths")

    if e1["search"]["epochs_per_stage"] != 25:
        fail("E1 archive-ledger epochs_per_stage must be 25")

    for config in configs:
        if config["evaluation"]["epochs"] != 300:
            fail(
                f"{config['experiment_id']}: evaluation epochs must be 300"
            )

        if config["evaluation"]["depths"] != [2, 4, 6, 8, 10, 12, 14]:
            fail(
                f"{config['experiment_id']}: evaluation depths are incomplete"
            )

    print(f"[OK] Experiment configurations: {len(configs)}")
    print(f"[OK] Experiment IDs: {', '.join(sorted(identifiers))}")
    print("[OK] Result namespace: reproduction")
    print("[OK] Architecture-only transfer boundary passed.")
    print("[OK] No local absolute paths detected.")
    print("[OK] Upstream dependency policy passed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"[FAIL] {exc}", file=sys.stderr)
        raise SystemExit(1)
