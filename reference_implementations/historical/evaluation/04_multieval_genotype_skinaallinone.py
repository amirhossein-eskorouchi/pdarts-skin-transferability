# ============================================================================
# HISTORICAL RESEARCH SOURCE - NOT THE MAINTAINED IMPLEMENTATION
#
# Private archive source: PDARTS/Github/master/04_multieval_genotype_skinaallinone.py
# Original SHA-256: 7fe2c4322fe5ce0121fc2514b6a017ea9560552db139f1ff176de13f2c1be756
#
# This snapshot preserves historical project behavior. Release-blocking
# workstation roots were replaced with PROJECT_ROOT. A workstation identifier
# in author metadata was replaced with a descriptive attribution.
# ============================================================================
# -*- coding: utf-8 -*-
"""
04_eval_genotype_skin_BATCH.py

Evaluate (train from scratch) FIXED genotype(s) at evaluation depth m on a dataset split.

UPDATED (drop-in):
- Supports looping over multiple genotype*.txt (genotype0/1/2...) via:
    * --genotype_list (comma-separated paths), OR
    * --genotype_dir  (auto-discovers genotype*.txt recursively), OR
    * default single --genotype_txt
- Supports looping over m in {2,4,6,8,10,12,14} via:
    * --eval_depth_list 2,4,6,8,10,12,14
  If you don't pass eval_depth_list, it will run ALL depths by default (2..14 step 2),
  so you can "hit run once" without extra CLI args.

Manuscript alignment:
- Use T1(train) / T2(val) / T3(test) on TARGET dataset for transfer evaluation
  (or S1/S2/S3 when source=target).
- m ? {2,4,6,8,10,12,14} controls evaluation network depth (cells).
- Resize to 32x32 and only RandomHorizontalFlip/RandomVerticalFlip augmentations.
- 300 evaluation epochs (default).

Saves EVERYTHING needed for reviewer responses:
  * accuracy, macro/weighted F1
  * TPR/TNR: binary-style (positive_class) if num_classes==2; macro-averaged if num_classes>2
  * ROC-AUC / PR-AUC: binary if num_classes==2; multiclass OvR macro + micro when num_classes>2
  * confusion matrix + per-class metrics
  * ROC curves & PR curves to CSV (best-effort)
  * full test + val predictions (y_true, y_pred, probs, confidence)
  * calibration metrics: ECE + Brier score
  * consistent master ledger: save_root/_EVAL_LEDGER.csv

IMPORTANT FIXES (PyTorch 2.6+):
- Avoids torch.load UnpicklingError by saving/loading WEIGHTS-ONLY checkpoints for eval:
    * best_weights.pt / last_weights.pt (safe to load with default torch.load)
  Optionally also saves full checkpoints:
    * best_full.pt / last_full.pt (not used for evaluation)

Skip/resume behavior:
- --skip_existing only skips runs that already have test_metrics.json (i.e., fully completed runs)
"""

import argparse
import csv
import json
import logging
import time
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import torch
import torch.nn as nn
import torch.backends.cudnn as cudnn

# IMPORTANT: uses the *final* model definition (not model_search)
from model import NetworkCIFAR
from genotypes import Genotype  # for eval(genotype_str)

from skin_csv_dataset import SkinCSVImageDataset
from skin_transforms import TransformConfig, build_train_transform, build_eval_transform


# ----------------------- USER-FRIENDLY DEFAULTS -----------------------
DEFAULT_TRAIN_CSV = "PROJECT_ROOT/output/splits/D1_train.csv"
DEFAULT_VAL_CSV   = "PROJECT_ROOT/output/splits/D2_val.csv"
DEFAULT_TEST_CSV  = "PROJECT_ROOT/output/splits/D3_test.csv"

DEFAULT_SAVE_ROOT = "PROJECT_ROOT/output/eval_runs/0final/imagesize224task2/D/genotype2"
DEFAULT_RUN_NAME  = "EVAL_target"

DEFAULT_GENOTYPE_TXT = "PROJECT_ROOT/output/search_runs/genotype/0final/Image_size224/genotype2.txt"

# NEW: if you want directory auto-discovery by default, set this.
# Leave as "" if you prefer to pass --genotype_dir explicitly.
DEFAULT_GENOTYPE_DIR = ""
# ---------------------------------------------------------------------


# Fixed schema ledger so it never breaks later
EVAL_LEDGER_FIELDS = [
    "timestamp",
    "status",                # OK / SKIPPED / FAIL
    "elapsed_sec",
    "run_dir",

    "run_name",
    "dataset_tag",
    "train_csv",
    "val_csv",
    "test_csv",

    "genotype_txt",
    "genotype_id",           # short hash
    "eval_depth_m",
    "epochs",
    "seed",

    "image_size",
    "batch_size",
    "workers",

    "learning_rate",
    "learning_rate_min",
    "momentum",
    "weight_decay",
    "grad_clip",

    "init_channels",
    "drop_path_prob",
    "auxiliary",
    "auxiliary_weight",

    "positive_class",

    # Best val
    "best_val_acc_top1",

    # Test summary
    "test_acc_top1",
    "test_macro_f1",
    "test_weighted_f1",
    "test_tpr",
    "test_tnr",
    "test_roc_auc_ovr_macro",
    "test_roc_auc_ovr_micro",
    "test_pr_auc_macro",
    "test_pr_auc_micro",
    "test_brier",
    "test_ece",

    "device",
    "torch_version",
    "cuda_available",

    "error",
]


def _now_stamp() -> str:
    return time.strftime("%Y%m%d-%H%M%S")


def _safe_slug(s: str) -> str:
    keep = []
    for ch in str(s):
        if ch.isalnum() or ch in ("-", "_", "."):
            keep.append(ch)
        else:
            keep.append("_")
    return "".join(keep)


def _write_json(path: Path, obj: Dict[str, Any]) -> None:
    path.write_text(json.dumps(obj, indent=2, sort_keys=True), encoding="utf-8")


def _append_ledger_row(ledger_csv: Path, row: Dict[str, Any]) -> None:
    ledger_csv.parent.mkdir(parents=True, exist_ok=True)
    exists = ledger_csv.exists()
    with ledger_csv.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=EVAL_LEDGER_FIELDS, extrasaction="ignore")
        if not exists:
            w.writeheader()
        w.writerow(row)


def _genotype_id(genotype_str: str) -> str:
    import hashlib
    h = hashlib.sha1(genotype_str.encode("utf-8")).hexdigest()
    return h[:10]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser("Evaluate genotype(s) (P-DARTS) on skin lesion datasets (batch enabled)")

    # Data splits
    p.add_argument("--train_csv", type=str, default=DEFAULT_TRAIN_CSV)
    p.add_argument("--val_csv", type=str, default=DEFAULT_VAL_CSV)
    p.add_argument("--test_csv", type=str, default=DEFAULT_TEST_CSV)

    # Output / bookkeeping
    p.add_argument("--save_root", type=str, default=DEFAULT_SAVE_ROOT)
    p.add_argument("--run_name", type=str, default=DEFAULT_RUN_NAME)
    p.add_argument("--dataset_tag", type=str, default="TARGET")

    # Genotype input (single or batch)
    p.add_argument("--genotype_txt", type=str, default=DEFAULT_GENOTYPE_TXT,
                   help="Path to one genotype.txt (or genotype0.txt etc).")
    p.add_argument("--genotype_list", type=str, default="",
                   help="Comma-separated list of genotype*.txt paths (batch).")
    p.add_argument("--genotype_dir", type=str, default=DEFAULT_GENOTYPE_DIR,
                   help="If set, discovers all genotype*.txt under this directory recursively (batch). "
                        "Set to empty string to disable auto-discovery by default.")

    # Evaluation depths
    p.add_argument("--eval_depth_m", type=int, choices=[2, 4, 6, 8, 10, 12, 14], default=4)
    p.add_argument("--eval_depth_list", type=str, default="",
                   help="Comma-separated list of m values for batch, e.g. 2,4,6,8,10,12,14")

    # Manuscript settings
    p.add_argument("--image_size", type=int, default=224)
    p.add_argument("--epochs", type=int, default=300)

    # Training hyperparams (PDARTS/DARTS-style defaults)
    p.add_argument("--batch_size", type=int, default=64)
    p.add_argument("--workers", type=int, default=2)
    p.add_argument("--learning_rate", type=float, default=0.025)
    p.add_argument("--learning_rate_min", type=float, default=0.0)
    p.add_argument("--momentum", type=float, default=0.9)
    p.add_argument("--weight_decay", type=float, default=3e-4)
    p.add_argument("--grad_clip", type=float, default=5.0)

    # Model size knobs (DARTS evaluation commonly uses init_channels=36)
    p.add_argument("--init_channels", type=int, default=36)
    p.add_argument("--drop_path_prob", type=float, default=0.3)

    # Auxiliary head (optional)
    p.add_argument("--auxiliary", action="store_true", default=False)
    p.add_argument("--auxiliary_weight", type=float, default=0.4)

    # Binary reporting control
    p.add_argument("--positive_class", type=int, default=1,
                   help="If num_classes==2, treat this class index as the positive class for TPR/TNR and AUCs.")

    # Repeats / device
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--seed_list", type=str, default="",
                   help="Comma-separated list of seeds for batch repeats, e.g. 0,1,2")

    p.add_argument("--gpu", type=int, default=0)
    p.add_argument("--report_freq", type=int, default=50)

    # Batch controls
    p.add_argument("--batch", action="store_true",
                   help="Enable batch mode if you provided genotype_list/dir or eval_depth_list or seed_list.")
    p.add_argument("--skip_existing", action="store_true", default=True,
                   help="Skip a run ONLY IF its test_metrics.json already exists (default True).")
    p.add_argument("--continue_on_error", action="store_true", default=True,
                   help="Continue remaining runs if one fails (default True).")
    p.add_argument("--dry_run", action="store_true", default=False,
                   help="Print planned runs and exit.")

    return p.parse_args()


def _parse_int_list_csv(s: str) -> List[int]:
    out: List[int] = []
    for part in str(s).split(","):
        part = part.strip()
        if part:
            out.append(int(part))
    return out


def _parse_str_list_csv(s: str) -> List[str]:
    out: List[str] = []
    for part in str(s).split(","):
        part = part.strip()
        if part:
            out.append(part)
    return out


def build_loaders(train_csv: str, val_csv: str, test_csv: str,
                  image_size: int, batch_size: int, workers: int, use_cuda: bool):
    cfg = TransformConfig(image_size=image_size, normalize=True)
    train_t = build_train_transform(cfg)  # flips only
    eval_t = build_eval_transform(cfg)

    train_ds = SkinCSVImageDataset(train_csv, transform=train_t)
    val_ds   = SkinCSVImageDataset(val_csv,   transform=eval_t)
    test_ds  = SkinCSVImageDataset(test_csv,  transform=eval_t)

    num_classes = train_ds.num_classes

    train_loader = torch.utils.data.DataLoader(
        train_ds, batch_size=batch_size, shuffle=True,
        num_workers=workers, pin_memory=use_cuda, drop_last=False
    )
    val_loader = torch.utils.data.DataLoader(
        val_ds, batch_size=batch_size, shuffle=False,
        num_workers=workers, pin_memory=use_cuda, drop_last=False
    )
    test_loader = torch.utils.data.DataLoader(
        test_ds, batch_size=batch_size, shuffle=False,
        num_workers=workers, pin_memory=use_cuda, drop_last=False
    )
    return train_loader, val_loader, test_loader, num_classes


def load_genotype_from_txt(genotype_txt: str) -> Tuple[Genotype, str]:
    s = Path(genotype_txt).read_text(encoding="utf-8").strip()
    ctx = {"Genotype": Genotype, "range": range}
    geno = eval(s, ctx)  # noqa: S307 (trusted file produced by your own code)
    if not isinstance(geno, Genotype):
        raise ValueError("Parsed genotype is not a Genotype object.")
    return geno, str(geno)


def accuracy_topk(logits: torch.Tensor, targets: torch.Tensor, topk=(1,)) -> List[float]:
    with torch.no_grad():
        maxk = min(max(topk), logits.size(1))
        _, pred = logits.topk(maxk, 1, True, True)
        pred = pred.t()
        correct = pred.eq(targets.view(1, -1).expand_as(pred))
        res = []
        for k in topk:
            k = min(k, logits.size(1))
            correct_k = correct[:k].reshape(-1).float().sum(0)
            res.append((correct_k * (100.0 / targets.size(0))).item())
        return res


def confusion_matrix_np(y_true: np.ndarray, y_pred: np.ndarray, num_classes: int) -> np.ndarray:
    cm = np.zeros((num_classes, num_classes), dtype=np.int64)
    for t, p in zip(y_true, y_pred):
        ti = int(t); pi = int(p)
        if 0 <= ti < num_classes and 0 <= pi < num_classes:
            cm[ti, pi] += 1
    return cm


def _ece_from_probs(y_true: np.ndarray, y_prob: np.ndarray, n_bins: int = 15) -> Tuple[float, np.ndarray]:
    """
    Expected Calibration Error for multiclass using max probability.
    Returns (ece, table) where table columns are:
    bin_lo, bin_hi, count, avg_conf, avg_acc
    """
    y_pred = y_prob.argmax(axis=1)
    conf = y_prob.max(axis=1)
    acc = (y_pred == y_true).astype(np.float32)

    bins = np.linspace(0.0, 1.0, n_bins + 1)
    rows = []
    ece = 0.0
    N = len(y_true)
    for i in range(n_bins):
        lo, hi = bins[i], bins[i + 1]
        mask = (conf >= lo) & (conf < hi) if i < n_bins - 1 else (conf >= lo) & (conf <= hi)
        m = int(mask.sum())
        if m == 0:
            rows.append([lo, hi, 0, np.nan, np.nan])
            continue
        avg_conf = float(conf[mask].mean())
        avg_acc = float(acc[mask].mean())
        ece += (m / max(1, N)) * abs(avg_acc - avg_conf)
        rows.append([lo, hi, m, avg_conf, avg_acc])
    return float(ece), np.array(rows, dtype=np.float64)


def _brier_score(y_true: np.ndarray, y_prob: np.ndarray, num_classes: int) -> float:
    y_onehot = np.zeros((len(y_true), num_classes), dtype=np.float32)
    y_onehot[np.arange(len(y_true)), y_true.astype(int)] = 1.0
    return float(np.mean(np.sum((y_prob - y_onehot) ** 2, axis=1)))


def compute_metrics(y_true: np.ndarray, y_prob: np.ndarray, num_classes: int, positive_class: int) -> Dict[str, Any]:
    """
    - Always computes per-class precision/recall/specificity/F1 and macro/weighted F1.
    - If num_classes==2:
        * reports binary-style TPR/TNR using positive_class
        * reports binary ROC-AUC / PR-AUC using positive_class probability
    - If num_classes>2:
        * reports macro-averaged TPR/TNR
        * reports OvR macro/micro ROC-AUC and macro/micro PR-AUC when possible
    """
    y_pred = y_prob.argmax(axis=1)
    cm = confusion_matrix_np(y_true, y_pred, num_classes)

    tp = np.diag(cm).astype(np.float64)
    fn = cm.sum(axis=1) - tp
    fp = cm.sum(axis=0) - tp
    tn = cm.sum() - (tp + fn + fp)

    eps = 1e-12
    precision = tp / (tp + fp + eps)
    recall = tp / (tp + fn + eps)              # sensitivity / TPR per class
    specificity = tn / (tn + fp + eps)         # TNR per class
    f1 = 2 * precision * recall / (precision + recall + eps)

    support = cm.sum(axis=1).astype(np.float64)
    weights = support / max(1.0, support.sum())

    acc = float((y_pred == y_true).mean())
    macro_f1 = float(np.nanmean(f1))
    weighted_f1 = float(np.nansum(f1 * weights))

    # TPR/TNR reporting rule
    if num_classes == 2:
        pc = int(positive_class)
        pc = 0 if pc not in (0, 1) else pc
        tpr = float(recall[pc])
        tnr = float(specificity[pc])
    else:
        tpr = float(np.nanmean(recall))
        tnr = float(np.nanmean(specificity))

    out: Dict[str, Any] = {
        "accuracy": acc,
        "accuracy_pct": acc * 100.0,
        "macro_f1": macro_f1,
        "macro_f1_pct": macro_f1 * 100.0,
        "weighted_f1": weighted_f1,
        "weighted_f1_pct": weighted_f1 * 100.0,
        "tpr": tpr,
        "tnr": tnr,
        "per_class": [],
        "confusion_matrix": cm.tolist(),
        "roc_auc_ovr_macro": None,
        "roc_auc_ovr_micro": None,
        "pr_auc_macro": None,
        "pr_auc_micro": None,
        "ece": None,
        "brier": None,
        "ece_table": None,
    }

    for c in range(num_classes):
        out["per_class"].append({
            "class": int(c),
            "precision": float(precision[c]),
            "recall_sensitivity": float(recall[c]),
            "specificity": float(specificity[c]),
            "f1": float(f1[c]),
            "support": int(support[c]),
        })

    # AUCs (best-effort if sklearn is available)
    try:
        from sklearn.preprocessing import label_binarize
        from sklearn.metrics import roc_auc_score, average_precision_score

        classes = list(range(num_classes))
        if num_classes == 2:
            pc = int(positive_class)
            pc = 0 if pc not in (0, 1) else pc
            y_bin = (y_true == pc).astype(int)
            scores = y_prob[:, pc]
            out["roc_auc_ovr_macro"] = float(roc_auc_score(y_bin, scores))
            out["pr_auc_macro"] = float(average_precision_score(y_bin, scores))
        else:
            y_onehot = label_binarize(y_true, classes=classes)
            out["roc_auc_ovr_macro"] = float(roc_auc_score(y_onehot, y_prob, average="macro", multi_class="ovr"))
            out["roc_auc_ovr_micro"] = float(roc_auc_score(y_onehot, y_prob, average="micro"))
            out["pr_auc_macro"] = float(average_precision_score(y_onehot, y_prob, average="macro"))
            out["pr_auc_micro"] = float(average_precision_score(y_onehot, y_prob, average="micro"))
    except Exception:
        pass

    # Calibration: ECE + Brier
    ece, ece_table = _ece_from_probs(y_true, y_prob, n_bins=15)
    brier = _brier_score(y_true, y_prob, num_classes)
    out["ece"] = float(ece)
    out["brier"] = float(brier)
    out["ece_table"] = ece_table.tolist()

    return out


def save_confusion_matrix_csv(path: Path, cm: np.ndarray) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["true\\pred"] + [f"pred_{j}" for j in range(cm.shape[1])])
        for i in range(cm.shape[0]):
            w.writerow([f"true_{i}"] + list(map(int, cm[i].tolist())))


def save_per_class_metrics_csv(path: Path, metrics: Dict[str, Any]) -> None:
    rows = metrics.get("per_class", [])
    with path.open("w", newline="", encoding="utf-8") as f:
        if not rows:
            csv.writer(f).writerow(["class"])
            return
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for r in rows:
            w.writerow(r)


def save_predictions_csv(path: Path, y_true: np.ndarray, y_prob: np.ndarray) -> None:
    y_pred = y_prob.argmax(axis=1)
    conf = y_prob.max(axis=1)
    K = y_prob.shape[1]
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["y_true", "y_pred", "max_prob"] + [f"p_{i}" for i in range(K)])
        for yt, yp, cf, pr in zip(y_true.tolist(), y_pred.tolist(), conf.tolist(), y_prob.tolist()):
            w.writerow([yt, yp, cf] + list(map(float, pr)))


def save_calibration_csv(path: Path, metrics: Dict[str, Any]) -> None:
    table = metrics.get("ece_table", [])
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["bin_lo", "bin_hi", "count", "avg_conf", "avg_acc"])
        for row in table:
            w.writerow(row)


def save_curve_csvs(run_dir: Path, y_true: np.ndarray, y_prob: np.ndarray, num_classes: int, positive_class: int) -> None:
    """
    Saves curve CSVs (best-effort):
    - Binary: roc_curve.csv and pr_curve.csv
    - Multiclass: roc_curve_macro_micro.csv and pr_curve_macro_micro.csv (micro + per-class)
    """
    try:
        from sklearn.preprocessing import label_binarize
        from sklearn.metrics import roc_curve, precision_recall_curve

        if num_classes == 2:
            pc = int(positive_class)
            pc = 0 if pc not in (0, 1) else pc
            y_bin = (y_true == pc).astype(int)
            scores = y_prob[:, pc]

            fpr, tpr, _ = roc_curve(y_bin, scores)
            prec, rec, _ = precision_recall_curve(y_bin, scores)

            with (run_dir / "roc_curve.csv").open("w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(["fpr", "tpr"])
                for a, b in zip(fpr.tolist(), tpr.tolist()):
                    w.writerow([a, b])

            with (run_dir / "pr_curve.csv").open("w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(["recall", "precision"])
                for a, b in zip(rec.tolist(), prec.tolist()):
                    w.writerow([a, b])
            return

        classes = list(range(num_classes))
        y_onehot = label_binarize(y_true, classes=classes)

        fpr_micro, tpr_micro, _ = roc_curve(y_onehot.ravel(), y_prob.ravel())
        prec_micro, rec_micro, _ = precision_recall_curve(y_onehot.ravel(), y_prob.ravel())

        per_class_roc = []
        per_class_pr = []
        for c in range(num_classes):
            if y_onehot[:, c].sum() == 0 or y_onehot[:, c].sum() == len(y_true):
                continue
            fpr_c, tpr_c, _ = roc_curve(y_onehot[:, c], y_prob[:, c])
            prec_c, rec_c, _ = precision_recall_curve(y_onehot[:, c], y_prob[:, c])
            per_class_roc.append((c, fpr_c, tpr_c))
            per_class_pr.append((c, rec_c, prec_c))

        with (run_dir / "roc_curve_macro_micro.csv").open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["curve", "class", "x", "y"])  # ROC: x=fpr y=tpr
            for x, y in zip(fpr_micro.tolist(), tpr_micro.tolist()):
                w.writerow(["micro", "", x, y])
            for c, fpr_c, tpr_c in per_class_roc:
                for x, y in zip(fpr_c.tolist(), tpr_c.tolist()):
                    w.writerow(["class", c, x, y])

        with (run_dir / "pr_curve_macro_micro.csv").open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["curve", "class", "x", "y"])  # PR: x=recall y=precision
            for x, y in zip(rec_micro.tolist(), prec_micro.tolist()):
                w.writerow(["micro", "", x, y])
            for c, rec_c, prec_c in per_class_pr:
                for x, y in zip(rec_c.tolist(), prec_c.tolist()):
                    w.writerow(["class", c, x, y])

    except Exception:
        return


def train_one_epoch(loader, model, criterion, optimizer, device,
                    grad_clip: float, report_freq: int,
                    auxiliary: bool, auxiliary_weight: float) -> Tuple[float, float]:
    model.train()
    losses = []
    accs = []

    for step, (x, y) in enumerate(loader):
        x = x.to(device, non_blocking=True)
        y = y.to(device, non_blocking=True)

        optimizer.zero_grad()

        logits, logits_aux = model(x)
        loss = criterion(logits, y)
        if auxiliary and (logits_aux is not None):
            loss = loss + auxiliary_weight * criterion(logits_aux, y)

        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), grad_clip)
        optimizer.step()

        top1 = accuracy_topk(logits, y, topk=(1,))[0]
        losses.append(loss.item())
        accs.append(top1)

        if step % report_freq == 0:
            logging.info("TRAIN step=%04d loss=%.4e top1=%.3f",
                         step, float(np.mean(losses)), float(np.mean(accs)))

    return float(np.mean(accs)), float(np.mean(losses))


@torch.no_grad()
def evaluate(loader, model, criterion, device, report_freq: int) -> Tuple[float, float, np.ndarray, np.ndarray]:
    model.eval()
    losses = []
    accs = []

    all_probs = []
    all_y = []

    for step, (x, y) in enumerate(loader):
        x = x.to(device, non_blocking=True)
        y = y.to(device, non_blocking=True)

        logits, _ = model(x)
        loss = criterion(logits, y)

        probs = torch.softmax(logits, dim=1).detach().cpu().numpy()
        all_probs.append(probs)
        all_y.append(y.detach().cpu().numpy())

        top1 = accuracy_topk(logits, y, topk=(1,))[0]
        losses.append(loss.item())
        accs.append(top1)

        if step % report_freq == 0:
            logging.info("EVAL step=%04d loss=%.4e top1=%.3f",
                         step, float(np.mean(losses)), float(np.mean(accs)))

    all_probs = np.concatenate(all_probs, axis=0) if all_probs else np.zeros((0, 0))
    all_y = np.concatenate(all_y, axis=0) if all_y else np.zeros((0,), dtype=np.int64)
    return float(np.mean(accs)), float(np.mean(losses)), all_probs, all_y


def _make_run_dir(args: argparse.Namespace, genotype_id: str, m: int, seed: int) -> Path:
    ts = _now_stamp()
    slug = (
        f"{_safe_slug(args.run_name)}"
        f"__{_safe_slug(args.dataset_tag)}"
        f"__gid{genotype_id}"
        f"__m{m}"
        f"__seed{seed}"
        f"__img{args.image_size}"
        f"__bs{args.batch_size}"
        f"__lr{args.learning_rate}"
        f"__wd{args.weight_decay}"
        f"__ep{args.epochs}"
    )
    return Path(args.save_root) / f"{slug}__{ts}"


def _already_done_completed_only(save_root: Path, signature_prefix: str) -> Optional[Path]:
    """
    Skip only if the run folder exists AND it contains test_metrics.json (i.e., completed).
    This prevents "skipping" half-failed runs.
    """
    if not save_root.exists():
        return None
    matches = [p for p in save_root.glob(f"{signature_prefix}__*") if p.is_dir()]
    if not matches:
        return None
    matches = [p for p in matches if (p / "test_metrics.json").exists()]
    if not matches:
        return None
    matches.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return matches[0]


def run_eval_once(args: argparse.Namespace, genotype_txt: str, m: int, seed: int) -> Tuple[str, Path, Dict[str, Any]]:
    """
    Returns: (genotype_str, run_dir, metrics)
    """
    t0 = time.time()
    use_cuda = torch.cuda.is_available()
    if use_cuda:
        torch.cuda.set_device(args.gpu)
        device = torch.device(f"cuda:{args.gpu}")
    else:
        device = torch.device("cpu")

    # seeds: controls training randomness (DataLoader shuffle order, init, etc.)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if use_cuda:
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)

    cudnn.benchmark = True

    genotype, genotype_str = load_genotype_from_txt(genotype_txt)
    gid = _genotype_id(genotype_str)

    signature_prefix = (
        f"{_safe_slug(args.run_name)}"
        f"__{_safe_slug(args.dataset_tag)}"
        f"__gid{gid}"
        f"__m{m}"
        f"__seed{seed}"
        f"__img{args.image_size}"
        f"__bs{args.batch_size}"
        f"__lr{args.learning_rate}"
        f"__wd{args.weight_decay}"
        f"__ep{args.epochs}"
    )

    save_root = Path(args.save_root)
    save_root.mkdir(parents=True, exist_ok=True)

    if args.skip_existing:
        existing = _already_done_completed_only(save_root, signature_prefix)
        if existing is not None:
            metrics_path = existing / "test_metrics.json"
            metrics = {}
            if metrics_path.exists():
                try:
                    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
                except Exception:
                    metrics = {}
            return genotype_str, existing, metrics

    run_dir = _make_run_dir(args, gid, m, seed)
    run_dir.mkdir(parents=True, exist_ok=True)

    # logging
    logging.basicConfig(
        filename=str(run_dir / "eval.log"),
        level=logging.INFO,
        format="%(asctime)s %(message)s",
        datefmt="%m/%d %I:%M:%S %p",
        force=True,
    )
    logging.getLogger().addHandler(logging.StreamHandler())

    logging.info("Run dir: %s", run_dir)
    logging.info("Device: %s", device)
    logging.info("Genotype txt: %s", genotype_txt)
    logging.info("Genotype: %s", genotype_str)

    # Save args
    args_dict = vars(args).copy()
    args_dict["device"] = str(device)
    args_dict["torch_version"] = torch.__version__
    args_dict["cuda_available"] = bool(use_cuda)
    args_dict["genotype"] = genotype_str
    args_dict["genotype_txt"] = genotype_txt
    args_dict["genotype_id"] = gid
    args_dict["eval_depth_m"] = m
    args_dict["seed"] = seed
    _write_json(run_dir / "run_args.json", args_dict)

    # Data
    train_loader, val_loader, test_loader, num_classes = build_loaders(
        args.train_csv, args.val_csv, args.test_csv,
        image_size=args.image_size,
        batch_size=args.batch_size,
        workers=args.workers,
        use_cuda=use_cuda
    )
    logging.info("Num classes: %d", num_classes)

    # Model
    criterion = nn.CrossEntropyLoss().to(device)
    model = NetworkCIFAR(
        C=args.init_channels,
        num_classes=num_classes,
        layers=m,
        auxiliary=args.auxiliary,
        genotype=genotype
    ).to(device)

    optimizer = torch.optim.SGD(
        model.parameters(),
        lr=args.learning_rate,
        momentum=args.momentum,
        weight_decay=args.weight_decay
    )
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
        optimizer, T_max=float(args.epochs), eta_min=args.learning_rate_min
    )

    # Train history CSV
    history_csv = run_dir / "train_history.csv"
    with history_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["epoch", "lr", "drop_path_prob",
                    "train_acc_top1", "train_loss",
                    "val_acc_top1", "val_loss"])

    best_val = -1.0

    best_weights_path = run_dir / "best_weights.pt"
    last_weights_path = run_dir / "last_weights.pt"
    best_full_path = run_dir / "best_full.pt"
    last_full_path = run_dir / "last_full.pt"

    for epoch in range(args.epochs):
        lr = optimizer.param_groups[0]["lr"]
        model.drop_path_prob = args.drop_path_prob * (epoch / max(1, args.epochs - 1))

        logging.info("=" * 80)
        logging.info("Epoch %d/%d lr=%.4e drop_path=%.4f",
                     epoch + 1, args.epochs, lr, float(model.drop_path_prob))

        train_acc, train_loss = train_one_epoch(
            train_loader, model, criterion, optimizer, device,
            grad_clip=args.grad_clip,
            report_freq=args.report_freq,
            auxiliary=args.auxiliary,
            auxiliary_weight=args.auxiliary_weight
        )
        val_acc, val_loss, _, _ = evaluate(val_loader, model, criterion, device, report_freq=args.report_freq)

        with history_csv.open("a", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow([epoch + 1, lr, float(model.drop_path_prob),
                        train_acc, train_loss,
                        val_acc, val_loss])

        logging.info("Train: acc=%.3f loss=%.4e | Val: acc=%.3f loss=%.4e",
                     train_acc, train_loss, val_acc, val_loss)

        if val_acc > best_val:
            best_val = val_acc
            torch.save(model.state_dict(), best_weights_path)
            torch.save({
                "epoch": epoch + 1,
                "model_state": model.state_dict(),
                "optimizer_state": optimizer.state_dict(),
                "scheduler_state": scheduler.state_dict(),
                "best_val": best_val,
                "genotype": genotype_str,
                "args": args_dict,
            }, best_full_path)
            logging.info("Saved BEST checkpoint (val_acc=%.3f) -> %s", best_val, best_weights_path)

        scheduler.step()

    torch.save(model.state_dict(), last_weights_path)
    torch.save({
        "epoch": args.epochs,
        "model_state": model.state_dict(),
        "optimizer_state": optimizer.state_dict(),
        "scheduler_state": scheduler.state_dict(),
        "best_val": best_val,
        "genotype": genotype_str,
        "args": args_dict,
    }, last_full_path)
    logging.info("Saved LAST checkpoint -> %s", last_weights_path)

    # -------------------- EVALUATE USING BEST WEIGHTS --------------------
    weights_to_load = best_weights_path if best_weights_path.exists() else last_weights_path
    logging.info("Loading weights for evaluation: %s", weights_to_load)

    state = torch.load(weights_to_load, map_location=device)
    model.load_state_dict(state)
    model.eval()

    # Export val predictions (best model)
    _, _, val_probs, val_y = evaluate(val_loader, model, criterion, device, report_freq=args.report_freq)
    save_predictions_csv(run_dir / "val_predictions.csv", val_y, val_probs)

    # Test
    test_acc, test_loss, test_probs, test_y = evaluate(test_loader, model, criterion, device, report_freq=args.report_freq)
    save_predictions_csv(run_dir / "test_predictions.csv", test_y, test_probs)

    metrics = compute_metrics(test_y, test_probs, num_classes=num_classes, positive_class=args.positive_class)
    metrics["best_val_acc_top1"] = float(best_val)
    metrics["used_weights"] = str(weights_to_load.name)
    metrics["num_classes"] = int(num_classes)
    metrics["positive_class"] = int(args.positive_class)

    _write_json(run_dir / "test_metrics.json", metrics)
    cm = np.array(metrics["confusion_matrix"], dtype=np.int64)
    save_confusion_matrix_csv(run_dir / "confusion_matrix.csv", cm)
    save_per_class_metrics_csv(run_dir / "per_class_metrics.csv", metrics)
    save_calibration_csv(run_dir / "calibration_ece.csv", metrics)
    save_curve_csvs(run_dir, test_y, test_probs, num_classes=num_classes, positive_class=args.positive_class)

    summary_csv = run_dir / "test_metrics_summary.csv"
    with summary_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "used_weights",
            "best_val_acc_top1",
            "test_acc_top1",
            "macro_f1", "weighted_f1",
            "tpr", "tnr",
            "roc_auc_ovr_macro", "roc_auc_ovr_micro",
            "pr_auc_macro", "pr_auc_micro",
            "brier", "ece"
        ])
        w.writerow([
            metrics.get("used_weights"),
            metrics.get("best_val_acc_top1"),
            metrics.get("accuracy_pct"),
            metrics.get("macro_f1_pct"), metrics.get("weighted_f1_pct"),
            metrics.get("tpr"), metrics.get("tnr"),
            metrics.get("roc_auc_ovr_macro"), metrics.get("roc_auc_ovr_micro"),
            metrics.get("pr_auc_macro"), metrics.get("pr_auc_micro"),
            metrics.get("brier"), metrics.get("ece")
        ])

    logging.info("TEST: acc(top1)=%.3f loss=%.4e", test_acc, test_loss)
    logging.info(
        "TEST summary: acc=%.2f macroF1=%.2f weightedF1=%.2f tpr=%.4f tnr=%.4f rocAUC(macro)=%s prAUC(macro)=%s ece=%.4f brier=%.4f",
        metrics.get("accuracy_pct", float("nan")),
        metrics.get("macro_f1_pct", float("nan")),
        metrics.get("weighted_f1_pct", float("nan")),
        float(metrics.get("tpr", float("nan"))),
        float(metrics.get("tnr", float("nan"))),
        str(metrics.get("roc_auc_ovr_macro")),
        str(metrics.get("pr_auc_macro")),
        float(metrics.get("ece", float("nan"))),
        float(metrics.get("brier", float("nan"))),
    )

    elapsed = time.time() - t0
    metrics["_elapsed_sec"] = float(elapsed)
    return genotype_str, run_dir, metrics


def discover_genotypes(genotype_txt: str, genotype_list: str, genotype_dir: str) -> List[str]:
    """
    UPDATED:
    - genotype_list: explicit comma-separated list (highest priority)
    - genotype_dir: discovers genotype*.txt (matches genotype0.txt, genotype1.txt, ...)
    - fallback: genotype_txt (single)
    """
    paths: List[str] = []
    if genotype_list.strip():
        paths.extend(_parse_str_list_csv(genotype_list))

    if genotype_dir.strip():
        root = Path(genotype_dir)
        if root.exists():
            # IMPORTANT CHANGE: genotype*.txt (not only genotype.txt)
            for p in root.rglob("genotype*.txt"):
                if p.is_file():
                    paths.append(str(p))

    if not paths:
        paths = [genotype_txt]

    # de-dup keep order
    seen = set()
    out = []
    for p in paths:
        if p not in seen:
            out.append(p)
            seen.add(p)

    # Sort for stable order (genotype0, genotype1, genotype2, ...)
    try:
        out.sort(key=lambda x: Path(x).name)
    except Exception:
        pass

    return out


def main() -> None:
    args = parse_args()

    genotype_paths = discover_genotypes(args.genotype_txt, args.genotype_list, args.genotype_dir)

    # UPDATED DEFAULT BEHAVIOR:
    # If you do NOT pass --eval_depth_list, we will run ALL manuscript depths automatically.
    if args.eval_depth_list.strip():
        ms = _parse_int_list_csv(args.eval_depth_list)
    else:
        ms = [2, 4, 6, 8, 10, 12, 14]

    seeds = _parse_int_list_csv(args.seed_list) if args.seed_list.strip() else [args.seed]

    do_batch = args.batch or (len(genotype_paths) > 1) or (len(ms) > 1) or (len(seeds) > 1)
    planned = [(g, m, s) for g in genotype_paths for m in ms for s in seeds]

    if args.dry_run or do_batch:
        print("\nPlanned evaluations:")
        for g, m, s in planned:
            print(f"  genotype={g} | m={m} | seed={s}")
        print(f"Total planned: {len(planned)}")
        if args.dry_run:
            return
        print("Starting batch...\n")

    ledger_csv = Path(args.save_root) / "_EVAL_LEDGER.csv"
    ts = _now_stamp()

    for i, (gpath, m, s) in enumerate(planned, start=1):
        t0 = time.time()
        status = "OK"
        run_dir = ""
        genotype_str = ""
        metrics: Dict[str, Any] = {}
        err = ""

        print(f"[{i}/{len(planned)}] RUN genotype={Path(gpath).name} m={m} seed={s}")
        try:
            genotype_str, run_dir_path, metrics = run_eval_once(args, gpath, m, s)
            run_dir = str(run_dir_path)
        except Exception as e:
            status = "FAIL"
            err = f"{type(e).__name__}: {e}\n{traceback.format_exc()}"
            print(f"[{i}/{len(planned)}] FAIL -> {type(e).__name__}: {e}")
            if not args.continue_on_error:
                pass

        elapsed = time.time() - t0

        use_cuda = torch.cuda.is_available()
        device = f"cuda:{args.gpu}" if use_cuda else "cpu"

        gid = _genotype_id(genotype_str) if genotype_str else ""
        row = {
            "timestamp": ts,
            "status": status,
            "elapsed_sec": f"{elapsed:.2f}",
            "run_dir": run_dir,

            "run_name": args.run_name,
            "dataset_tag": args.dataset_tag,
            "train_csv": args.train_csv,
            "val_csv": args.val_csv,
            "test_csv": args.test_csv,

            "genotype_txt": gpath,
            "genotype_id": gid,
            "eval_depth_m": m,
            "epochs": args.epochs,
            "seed": s,

            "image_size": args.image_size,
            "batch_size": args.batch_size,
            "workers": args.workers,

            "learning_rate": args.learning_rate,
            "learning_rate_min": args.learning_rate_min,
            "momentum": args.momentum,
            "weight_decay": args.weight_decay,
            "grad_clip": args.grad_clip,

            "init_channels": args.init_channels,
            "drop_path_prob": args.drop_path_prob,
            "auxiliary": bool(args.auxiliary),
            "auxiliary_weight": args.auxiliary_weight,

            "positive_class": args.positive_class,

            "best_val_acc_top1": (metrics.get("best_val_acc_top1") if isinstance(metrics, dict) else None),

            "test_acc_top1": metrics.get("accuracy_pct") if isinstance(metrics, dict) else None,
            "test_macro_f1": metrics.get("macro_f1_pct") if isinstance(metrics, dict) else None,
            "test_weighted_f1": metrics.get("weighted_f1_pct") if isinstance(metrics, dict) else None,
            "test_tpr": metrics.get("tpr") if isinstance(metrics, dict) else None,
            "test_tnr": metrics.get("tnr") if isinstance(metrics, dict) else None,
            "test_roc_auc_ovr_macro": metrics.get("roc_auc_ovr_macro") if isinstance(metrics, dict) else None,
            "test_roc_auc_ovr_micro": metrics.get("roc_auc_ovr_micro") if isinstance(metrics, dict) else None,
            "test_pr_auc_macro": metrics.get("pr_auc_macro") if isinstance(metrics, dict) else None,
            "test_pr_auc_micro": metrics.get("pr_auc_micro") if isinstance(metrics, dict) else None,
            "test_brier": metrics.get("brier") if isinstance(metrics, dict) else None,
            "test_ece": metrics.get("ece") if isinstance(metrics, dict) else None,

            "device": device,
            "torch_version": torch.__version__,
            "cuda_available": bool(use_cuda),

            "error": err,
        }
        _append_ledger_row(ledger_csv, row)

        if status == "FAIL" and not args.continue_on_error:
            raise RuntimeError(err)

        try:
            torch.cuda.empty_cache()
        except Exception:
            pass

    print("\n=== ALL EVALUATIONS COMPLETE ===")
    print("Master ledger:", str(ledger_csv))
    print("===============================\n")


if __name__ == "__main__":
    main()
