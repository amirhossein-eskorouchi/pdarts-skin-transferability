# ============================================================================
# HISTORICAL RESEARCH SOURCE - NOT THE MAINTAINED IMPLEMENTATION
#
# Private archive source: PDARTS/Github/master/03_run_search_skinTask2.py
# Original SHA-256: 668ce3caa6417b79a3f64334fd228c24afb8b4e8bd08af0b5c3823b6a349ecb1
#
# This snapshot preserves historical project behavior. Release-blocking
# workstation roots were replaced with PROJECT_ROOT. A workstation identifier
# in author metadata was replaced with a descriptive attribution.
# ============================================================================
# -*- coding: utf-8 -*-
"""
Created on Sat Dec 20 15:16:15 2025

@author: original project author (workstation identifier redacted)
"""

# -*- coding: utf-8 -*-
"""
032_run_search_skin_BATCH_TASK2_8.py

Task 2 (Search side): Run P-DARTS with n=6 and 75 search epochs using a high-resolution
fixed input size (start with 256x256).

What this script enforces by default (Task 2 - Search):
- n = 6
- total search epochs = 75  (implemented as epochs_per_stage=25 across 3 stages)
- image_size = 256
- save_root default points to a "256" folder so runs are not mixed with 32/256 runs

Notes:
- True "native resolution per image" is not feasible in standard mini-batch training.
  We interpret "original resolution" as: avoid aggressive 32x32; use a high fixed size (256)
  with your transforms handling resize/crop consistently across datasets.
- Evaluation (m=4,6,8,10,12,14 and 300 eval epochs) is handled in your eval script,
  not here.

Typical runs:
  # Single run (seed 0)
  python 032_run_search_skin_BATCH_TASK2_256.py --seed 0

  # Batch seeds (3 genotypes) for n=6
  python 032_run_search_skin_BATCH_TASK2_256.py --seeds 0,1,2

  # If you want to override paths
  python 032_run_search_skin_BATCH_TASK2_256.py \
      --train_csv /path/to/S1_train.csv --val_csv /path/to/S2_val.csv \
      --save_root /path/to/output/search_runs/256
"""

import argparse
import copy
import csv
import json
import logging
import time
import traceback
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.backends.cudnn as cudnn

from model_search import Network
from genotypes import PRIMITIVES, Genotype
import utils

from skin_csv_dataset import SkinCSVImageDataset
from skin_transforms import TransformConfig, build_train_transform, build_eval_transform


# ----------------------- USER-FRIENDLY DEFAULTS (TASK 2) -----------------------
DEFAULT_TRAIN_CSV = "PROJECT_ROOT/output/splits/S1_train.csv"
DEFAULT_VAL_CSV   = "PROJECT_ROOT/output/splits/S2_val.csv"
DEFAULT_SAVE_ROOT = "PROJECT_ROOT/output/search_runs/genotype/224"

DEFAULT_RUN_NAME  = "ISIC_search_task2_224"
# -----------------------------------------------------------------------------


LEDGER_FIELDS = [
    "timestamp",
    "run_dir",
    "run_name",
    "dataset_tag",
    "train_csv",
    "val_csv",
    "search_depth_n",
    "stage_layers",
    "epochs_per_stage",
    "total_search_epochs",
    "seed",
    "image_size",
    "batch_size",
    "learning_rate",
    "learning_rate_min",
    "momentum",
    "weight_decay",
    "arch_learning_rate",
    "arch_weight_decay",
    "init_channels",
    "add_width",
    "dropout_rate",
    "eps_no_arch",
    "grad_clip",
    "report_freq",
    "gpu",
    "device",
    "torch_version",
    "cuda_available",
    "genotype",
]

BATCH_LEDGER_FIELDS = [
    "batch_timestamp",
    "batch_name",
    "status",              # OK / SKIPPED / FAIL
    "elapsed_sec",
    "run_dir",
    "run_name",
    "dataset_tag",
    "train_csv",
    "val_csv",
    "search_depth_n",
    "seed",
    "epochs_per_stage",
    "image_size",
    "batch_size",
    "gpu",
    "genotype",
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


def _append_csv_row(path_csv: Path, fieldnames: List[str], row: Dict[str, Any]) -> None:
    path_csv.parent.mkdir(parents=True, exist_ok=True)
    exists = path_csv.exists()
    with path_csv.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        if not exists:
            w.writeheader()
        w.writerow(row)


def genotype_to_dict(g: Genotype) -> Dict[str, Any]:
    def _edge_list(x):
        return [{"op": op, "input": int(i)} for (op, i) in x]

    return {
        "normal": _edge_list(g.normal),
        "normal_concat": [int(i) for i in list(g.normal_concat)],
        "reduce": _edge_list(g.reduce),
        "reduce_concat": [int(i) for i in list(g.reduce_concat)],
    }


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser("P-DARTS search on skin lesion datasets (Task2 preset: n=6, 75 epochs, 224)")

    # Data / output
    p.add_argument("--train_csv", type=str, default=DEFAULT_TRAIN_CSV)
    p.add_argument("--val_csv", type=str, default=DEFAULT_VAL_CSV)
    p.add_argument("--save_root", type=str, default=DEFAULT_SAVE_ROOT)

    p.add_argument("--run_name", type=str, default=DEFAULT_RUN_NAME)
    p.add_argument("--dataset_tag", type=str, default="ISIC2019")

    # ---------- Single-run args (Task 2) ----------
    # Task 2 requires P-DARTS6 => lock to 6 by default; still allow choices for debugging if you want.
    p.add_argument("--search_depth_n", type=int, choices=[6], default=6)

    # 75 search epochs => 25 per stage * 3 stages
    p.add_argument("--epochs_per_stage", type=int, default=25)

    # Data settings (Task 2 starts with 224)
    p.add_argument("--image_size", type=int, default=224)
    p.add_argument("--batch_size", type=int, default=16)
    p.add_argument("--workers", type=int, default=2)

    # Optim hyperparams (keep manuscript defaults unless you intentionally change)
    p.add_argument("--learning_rate", type=float, default=0.025)
    p.add_argument("--learning_rate_min", type=float, default=0.0)
    p.add_argument("--momentum", type=float, default=0.9)
    p.add_argument("--weight_decay", type=float, default=3e-4)

    p.add_argument("--arch_learning_rate", type=float, default=6e-4)
    p.add_argument("--arch_weight_decay", type=float, default=1e-3)

    # P-DARTS stage parameters
    p.add_argument("--init_channels", type=int, default=16)
    p.add_argument("--add_width", type=int, nargs=3, default=[0, 0, 0])
    p.add_argument("--dropout_rate", type=float, nargs=3, default=[0.0, 0.0, 0.0])

    # When to start updating architecture params α
    p.add_argument("--eps_no_arch", type=int, nargs=3, default=[10, 10, 10])

    # Misc
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--gpu", type=int, default=0)
    p.add_argument("--grad_clip", type=float, default=5.0)
    p.add_argument("--report_freq", type=int, default=50)

    # Optional debug
    p.add_argument("--debug_shapes", action="store_true")
    p.add_argument("--deterministic", action="store_true",
                   help="If set, uses deterministic cudnn settings (slower but reproducible).")

    # ---------- Batch args ----------
    p.add_argument("--batch", action="store_true",
                   help="Enable batch mode: loop over --search_depth_list and --seeds.")
    p.add_argument("--batch_name", type=str, default="task2_search_224",
                   help="Name used in _BATCH_LEDGER.csv")

    # For Task 2 search, n is only 6; keep the argument but default to "6"
    p.add_argument("--search_depth_list", type=str, default="6",
                   help="Comma-separated list of n values to run in batch mode. For Task2 use: 6")

    # Seeds define how many genotypes you will generate (3 seeds => 3 genotypes)
    p.add_argument("--seeds", type=str, default="1,2",
                   help="Comma-separated list of seeds (2 seeds => 2 genotypes).")

    p.add_argument("--skip_existing", action="store_true",
                   help="If set, skip a run if a matching run already exists (by run signature).")
    p.add_argument("--continue_on_error", action="store_true",
                   help="If set, continue remaining runs even if one run fails.")
    p.add_argument("--dry_run", action="store_true",
                   help="Print planned runs and exit without executing.")

    return p.parse_args()


def _parse_int_list_csv(s: str) -> List[int]:
    out: List[int] = []
    for part in str(s).split(","):
        part = part.strip()
        if not part:
            continue
        out.append(int(part))
    return out


def build_dataloaders(train_csv: str, val_csv: str, cfg: TransformConfig,
                      batch_size: int, workers: int, use_cuda: bool):
    train_t = build_train_transform(cfg)
    val_t = build_eval_transform(cfg)

    train_ds = SkinCSVImageDataset(train_csv, transform=train_t)
    val_ds = SkinCSVImageDataset(val_csv, transform=val_t)
    num_classes = train_ds.num_classes

    train_loader = torch.utils.data.DataLoader(
        train_ds,
        batch_size=batch_size,
        shuffle=True,
        num_workers=workers,
        pin_memory=use_cuda,
        drop_last=False
    )
    val_loader = torch.utils.data.DataLoader(
        val_ds,
        batch_size=batch_size,
        shuffle=False,
        num_workers=workers,
        pin_memory=use_cuda,
        drop_last=False
    )
    return train_loader, val_loader, num_classes


# ---------------------- Helpers (unchanged logic) ----------------------

def get_min_k(probs_1d: np.ndarray, k: int) -> List[int]:
    w = copy.deepcopy(probs_1d)
    idxs: List[int] = []
    for _ in range(k):
        i = int(np.argmin(w))
        idxs.append(i)
        w[i] = 1.0
    return idxs


def get_min_k_no_zero(probs_1d: np.ndarray, active_global_idxs: List[int], k: int) -> List[int]:
    w = copy.deepcopy(probs_1d)
    out: List[int] = []

    zf = 0 in active_global_idxs  # 'none' global index is 0
    if zf:
        w = w[1:]
        out.append(0)
        k -= 1

    for _ in range(k):
        i = int(np.argmin(w))
        w[i] = 1.0
        if zf:
            i += 1
        out.append(i)
    return out


def logging_switches(switches):
    for e, sw in enumerate(switches):
        ops = [PRIMITIVES[j] for j, on in enumerate(sw) if on]
        logging.info("Edge %02d active ops: %s", e, ops)


def parse_network(switches_normal, switches_reduce) -> Genotype:
    def _parse(switches):
        gene = []
        n_in = 2
        start = 0
        steps = 4
        for _ in range(steps):
            end = start + n_in
            for j in range(start, end):
                for k, on in enumerate(switches[j]):
                    if on:
                        gene.append((PRIMITIVES[k], j - start))
            start = end
            n_in += 1
        return gene

    concat = range(2, 6)
    return Genotype(
        normal=_parse(switches_normal), normal_concat=concat,
        reduce=_parse(switches_reduce), reduce_concat=concat
    )


def _edges_for_cell_steps():
    return [
        [0, 1],
        [2, 3, 4],
        [5, 6, 7, 8],
        [9, 10, 11, 12, 13],
    ]


def enforce_max_one_skip_per_cell(switches, probs_global):
    if "skip_connect" not in PRIMITIVES:
        return switches
    SKIP_IDX = PRIMITIVES.index("skip_connect")

    skip_edges = []
    for e in range(len(switches)):
        active_ops = [j for j, on in enumerate(switches[e]) if on]
        if len(active_ops) == 1 and active_ops[0] == SKIP_IDX:
            skip_edges.append(e)

    if len(skip_edges) <= 1:
        return switches

    skip_strength = [(e, float(probs_global[e][SKIP_IDX])) for e in skip_edges]
    skip_strength.sort(key=lambda x: x[1], reverse=True)
    keep_edge = skip_strength[0][0]
    drop_edges = [e for e, _ in skip_strength[1:]]

    for e in drop_edges:
        cand = probs_global[e].copy()
        cand[0] = -1.0
        cand[SKIP_IDX] = -1.0
        best = int(np.argmax(cand))
        for j in range(len(PRIMITIVES)):
            switches[e][j] = (j == best)

    for j in range(len(PRIMITIVES)):
        switches[keep_edge][j] = (j == SKIP_IDX)

    return switches


def _final_ops_csv(path_csv: Path, switches: List[List[bool]]) -> None:
    with path_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["edge", "selected_op", "selected_op_idx"])
        for e, sw in enumerate(switches):
            active = [j for j, on in enumerate(sw) if on]
            if len(active) == 1:
                j = active[0]
                w.writerow([e, PRIMITIVES[j], j])
            elif len(active) == 0:
                w.writerow([e, "", ""])
            else:
                w.writerow([e, "|".join(PRIMITIVES[j] for j in active),
                            "|".join(map(str, active))])


def _switches_to_jsonable(switches: List[List[bool]]) -> List[List[int]]:
    return [[j for j, on in enumerate(sw) if on] for sw in switches]


def expand_probs_to_global(probs_local: np.ndarray, switches_snapshot: List[List[bool]]) -> np.ndarray:
    num_edges = len(switches_snapshot)
    P = len(PRIMITIVES)
    if probs_local.shape[0] != num_edges:
        raise ValueError(f"probs_local has {probs_local.shape[0]} edges but switches has {num_edges}")

    out = np.zeros((num_edges, P), dtype=np.float32)
    for e in range(num_edges):
        active_global = [j for j, on in enumerate(switches_snapshot[e]) if on]
        K = len(active_global)
        if probs_local.shape[1] != K:
            raise ValueError(f"Edge {e}: probs_local K={probs_local.shape[1]} but switches has {K} active ops.")
        for k, j_global in enumerate(active_global):
            out[e, j_global] = float(probs_local[e, k])
    return out


def train_one_epoch(train_queue, valid_queue, model, network_params,
                    criterion, optimizer_w, optimizer_a,
                    grad_clip: float, report_freq: int, train_arch: bool,
                    device: torch.device):
    objs = utils.AvgrageMeter()
    top1 = utils.AvgrageMeter()
    top5 = utils.AvgrageMeter()

    valid_iter = iter(valid_queue)
    model.train()

    # support both DataParallel and plain model
    arch_owner = model.module if isinstance(model, nn.DataParallel) else model

    for step, (x, y) in enumerate(train_queue):
        x = x.to(device, non_blocking=True)
        y = y.to(device, non_blocking=True)

        if train_arch:
            try:
                xs, ys = next(valid_iter)
            except StopIteration:
                valid_iter = iter(valid_queue)
                xs, ys = next(valid_iter)

            xs = xs.to(device, non_blocking=True)
            ys = ys.to(device, non_blocking=True)

            optimizer_a.zero_grad()
            logits_a = model(xs)
            loss_a = criterion(logits_a, ys)
            loss_a.backward()
            nn.utils.clip_grad_norm_(arch_owner.arch_parameters(), grad_clip)
            optimizer_a.step()

        optimizer_w.zero_grad()
        logits = model(x)
        loss = criterion(logits, y)
        loss.backward()
        nn.utils.clip_grad_norm_(network_params, grad_clip)
        optimizer_w.step()

        prec1, prec5 = utils.accuracy(logits, y, topk=(1, 5))
        n = x.size(0)
        objs.update(loss.item(), n)
        top1.update(prec1.item(), n)
        top5.update(prec5.item(), n)

        if step % report_freq == 0:
            logging.info("TRAIN step=%03d loss=%.4e top1=%.3f top5=%.3f",
                         step, objs.avg, top1.avg, top5.avg)

    return top1.avg, objs.avg


@torch.no_grad()
def validate(valid_queue, model, criterion, report_freq: int, device: torch.device):
    objs = utils.AvgrageMeter()
    top1 = utils.AvgrageMeter()
    top5 = utils.AvgrageMeter()

    model.eval()
    for step, (x, y) in enumerate(valid_queue):
        x = x.to(device, non_blocking=True)
        y = y.to(device, non_blocking=True)

        logits = model(x)
        loss = criterion(logits, y)
        prec1, prec5 = utils.accuracy(logits, y, topk=(1, 5))

        n = x.size(0)
        objs.update(loss.item(), n)
        top1.update(prec1.item(), n)
        top5.update(prec5.item(), n)

        if step % report_freq == 0:
            logging.info("VALID step=%03d loss=%.4e top1=%.3f top5=%.3f",
                         step, objs.avg, top1.avg, top5.avg)

    return top1.avg, objs.avg


# ---------------------- Core search (single run) ----------------------

def _make_run_dir(args: argparse.Namespace) -> Path:
    slug = (
        f"{_safe_slug(args.run_name)}"
        f"__{_safe_slug(args.dataset_tag)}"
        f"__n{args.search_depth_n}"
        f"__seed{args.seed}"
        f"__img{args.image_size}"
        f"__bs{args.batch_size}"
        f"__lr{args.learning_rate}"
        f"__wd{args.weight_decay}"
        f"__archlr{args.arch_learning_rate}"
        f"__eps{args.epochs_per_stage}x3"
    )
    ts = _now_stamp()
    return Path(args.save_root) / f"{slug}__{ts}"


def _find_existing_run_dir(save_root: Path, signature_prefix: str) -> Optional[Path]:
    if not save_root.exists():
        return None
    matches = [p for p in save_root.glob(f"{signature_prefix}__*") if p.is_dir()]
    if not matches:
        return None
    matches.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    return matches[0]


def run_search_once(args: argparse.Namespace) -> Tuple[Path, str]:
    use_cuda = torch.cuda.is_available()
    if use_cuda:
        torch.cuda.set_device(args.gpu)
        device = torch.device(f"cuda:{args.gpu}")
    else:
        device = torch.device("cpu")

    # Seeds
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    if use_cuda:
        torch.cuda.manual_seed(args.seed)
        torch.cuda.manual_seed_all(args.seed)

    # CUDNN
    if args.deterministic:
        cudnn.benchmark = False
        cudnn.deterministic = True
    else:
        cudnn.benchmark = True

    # Task2: n=6 -> stage_layers = [2,4,6]
    stage_layers = [args.search_depth_n - 4, args.search_depth_n - 2, args.search_depth_n]
    if stage_layers[0] < 2:
        raise ValueError("search_depth_n must be >= 6 for stages [n-4,n-2,n].")

    total_search_epochs = int(args.epochs_per_stage) * 3
    if total_search_epochs != 75:
        logging.warning("Task2 expected total_search_epochs=75; got %d (epochs_per_stage=%d).",
                        total_search_epochs, int(args.epochs_per_stage))

    run_dir = _make_run_dir(args)
    run_dir.mkdir(parents=True, exist_ok=True)

    # Logging per run
    try:
        logging.basicConfig(
            filename=str(run_dir / "search.log"),
            level=logging.INFO,
            format="%(asctime)s %(message)s",
            datefmt="%m/%d %I:%M:%S %p",
            force=True,
        )
    except TypeError:
        logging.basicConfig(
            filename=str(run_dir / "search.log"),
            level=logging.INFO,
            format="%(asctime)s %(message)s",
            datefmt="%m/%d %I:%M:%S %p",
        )
    logging.getLogger().addHandler(logging.StreamHandler())

    logging.info("Run dir: %s", run_dir)
    logging.info("Device: %s", device)
    logging.info("Args: %s", args)
    logging.info("Stage layers: %s", stage_layers)
    logging.info("Total search epochs (per run): %d", total_search_epochs)

    # Save run args
    args_dict = vars(args).copy()
    args_dict["stage_layers"] = stage_layers
    args_dict["total_search_epochs"] = total_search_epochs
    args_dict["device"] = str(device)
    args_dict["torch_version"] = torch.__version__
    args_dict["cuda_available"] = bool(use_cuda)
    _write_json(run_dir / "run_args.json", args_dict)

    # Data
    cfg = TransformConfig(image_size=args.image_size, normalize=True)
    train_q, valid_q, num_classes = build_dataloaders(
        args.train_csv, args.val_csv, cfg, args.batch_size, args.workers, use_cuda
    )
    logging.info("Num classes: %d", num_classes)

    # P-DARTS pruning schedule
    num_to_drop = [3, 2, 2]

    switches = [[True for _ in range(len(PRIMITIVES))] for _ in range(14)]
    switches_normal = copy.deepcopy(switches)
    switches_reduce = copy.deepcopy(switches)

    switches_normal_bk: Optional[List[List[bool]]] = None
    switches_reduce_bk: Optional[List[List[bool]]] = None
    last_model_switches_normal: Optional[List[List[bool]]] = None
    last_model_switches_reduce: Optional[List[List[bool]]] = None

    criterion = nn.CrossEntropyLoss().to(device)

    model = None
    for sp in range(3):
        layers = int(stage_layers[sp])
        C = int(args.init_channels + args.add_width[sp])
        drop_prob = float(args.dropout_rate[sp])
        eps_no_arch = int(args.eps_no_arch[sp])

        logging.info("=" * 80)
        logging.info("Stage %d / 3 : layers=%d  C=%d  p_drop=%g  eps_no_arch=%d",
                     sp + 1, layers, C, drop_prob, eps_no_arch)

        model = Network(
            C, num_classes, layers, criterion,
            switches_normal=switches_normal,
            switches_reduce=switches_reduce,
            p=drop_prob
        )

        if use_cuda:
            model = nn.DataParallel(model).to(device)
        else:
            model = model.to(device)

        logging.info("Params: %.2fMB", utils.count_parameters_in_MB(model))

        network_params = []
        for name, p_ in model.named_parameters():
            if ("alphas_normal" in name) or ("alphas_reduce" in name):
                continue
            network_params.append(p_)

        optimizer_w = torch.optim.SGD(
            network_params,
            lr=args.learning_rate,
            momentum=args.momentum,
            weight_decay=args.weight_decay,
        )
        optimizer_a = torch.optim.Adam(
            model.module.arch_parameters() if use_cuda else model.arch_parameters(),
            lr=args.arch_learning_rate,
            betas=(0.5, 0.999),
            weight_decay=args.arch_weight_decay,
        )
        scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
            optimizer_w, float(args.epochs_per_stage), eta_min=args.learning_rate_min
        )

        for ep in range(args.epochs_per_stage):
            lr = optimizer_w.param_groups[0]["lr"]

            if ep < eps_no_arch:
                train_arch = False
                p_drop = drop_prob * (args.epochs_per_stage - ep - 1) / args.epochs_per_stage
            else:
                train_arch = True
                p_drop = drop_prob * np.exp(-(ep - eps_no_arch) * 0.2)

            if use_cuda:
                model.module.p = float(p_drop)
                model.module.update_p()
            else:
                model.p = float(p_drop)
                model.update_p()

            logging.info("Stage %d epoch %d/%d  lr=%.4e  train_arch=%s  p=%.4f",
                         sp + 1, ep + 1, args.epochs_per_stage, lr, train_arch, float(p_drop))

            train_acc, train_loss = train_one_epoch(
                train_q, valid_q,
                model,
                network_params, criterion,
                optimizer_w, optimizer_a,
                args.grad_clip, args.report_freq, train_arch, device
            )
            logging.info("Train: acc=%.3f loss=%.4e", train_acc, train_loss)

            if (args.epochs_per_stage - (ep + 1)) < 5:
                val_acc, val_loss = validate(valid_q, model, criterion, args.report_freq, device)
                logging.info("Valid: acc=%.3f loss=%.4e", val_acc, val_loss)

            scheduler.step()

        utils.save(model, str(run_dir / f"stage{sp+1}_weights.pt"))

        arch_param = (model.module.arch_parameters() if use_cuda else model.arch_parameters())
        normal_prob_local = F.softmax(arch_param[0], dim=-1).detach().cpu().numpy()
        reduce_prob_local = F.softmax(arch_param[1], dim=-1).detach().cpu().numpy()

        switches_normal_before = copy.deepcopy(switches_normal)
        switches_reduce_before = copy.deepcopy(switches_reduce)

        normal_prob_global = expand_probs_to_global(normal_prob_local, switches_normal_before)
        reduce_prob_global = expand_probs_to_global(reduce_prob_local, switches_reduce_before)

        np.save(run_dir / f"arch_probs_stage{sp+1}_normal_local.npy", normal_prob_local)
        np.save(run_dir / f"arch_probs_stage{sp+1}_reduce_local.npy", reduce_prob_local)
        np.save(run_dir / f"arch_probs_stage{sp+1}_normal_global.npy", normal_prob_global)
        np.save(run_dir / f"arch_probs_stage{sp+1}_reduce_global.npy", reduce_prob_global)

        if args.debug_shapes:
            logging.info("DEBUG stage%d: normal_local=%s reduce_local=%s", sp+1, normal_prob_local.shape, reduce_prob_local.shape)
            logging.info("DEBUG stage%d: normal_global=%s reduce_global=%s", sp+1, normal_prob_global.shape, reduce_prob_global.shape)

        if sp == 2:
            last_model_switches_normal = copy.deepcopy(switches_normal_before)
            last_model_switches_reduce = copy.deepcopy(switches_reduce_before)

        # Prune using LOCAL probs
        for e in range(14):
            idxs_n = [j for j, on in enumerate(switches_normal[e]) if on]
            idxs_r = [j for j, on in enumerate(switches_reduce[e]) if on]

            if sp == 2:
                drop_n_local = get_min_k_no_zero(normal_prob_local[e, :], idxs_n, num_to_drop[sp])
                drop_r_local = get_min_k_no_zero(reduce_prob_local[e, :], idxs_r, num_to_drop[sp])
            else:
                drop_n_local = get_min_k(normal_prob_local[e, :], num_to_drop[sp])
                drop_r_local = get_min_k(reduce_prob_local[e, :], num_to_drop[sp])

            for di in drop_n_local:
                switches_normal[e][idxs_n[di]] = False
            for di in drop_r_local:
                switches_reduce[e][idxs_r[di]] = False

        logging.info("After pruning stage %d:", sp + 1)
        logging.info("Normal switches:")
        logging_switches(switches_normal)
        logging.info("Reduce switches:")
        logging_switches(switches_reduce)

        _write_json(run_dir / f"stage{sp+1}_switches_normal.json",
                    {"active_ops": _switches_to_jsonable(switches_normal)})
        _write_json(run_dir / f"stage{sp+1}_switches_reduce.json",
                    {"active_ops": _switches_to_jsonable(switches_reduce)})

        if sp == 2:
            switches_normal_bk = copy.deepcopy(switches_normal)
            switches_reduce_bk = copy.deepcopy(switches_reduce)

    assert model is not None
    assert switches_normal_bk is not None and switches_reduce_bk is not None
    assert last_model_switches_normal is not None and last_model_switches_reduce is not None

    arch_param = (model.module.arch_parameters() if use_cuda else model.arch_parameters())
    normal_prob_local_final = F.softmax(arch_param[0], dim=-1).detach().cpu().numpy()
    reduce_prob_local_final = F.softmax(arch_param[1], dim=-1).detach().cpu().numpy()

    normal_prob = expand_probs_to_global(normal_prob_local_final, last_model_switches_normal)
    reduce_prob = expand_probs_to_global(reduce_prob_local_final, last_model_switches_reduce)

    # remove 'none' for selection
    normal_prob[:, 0] = 0.0
    reduce_prob[:, 0] = 0.0

    def keep_top2_edges(switches_in, probs_global_in):
        switches2 = copy.deepcopy(switches_in)
        edge_groups = _edges_for_cell_steps()
        keep_edges = []
        for group in edge_groups:
            scores = []
            for e in group:
                active_ops = [j for j, on in enumerate(switches2[e]) if on]
                best = max([probs_global_in[e][j] for j in active_ops]) if active_ops else 0.0
                scores.append(best)
            top2 = np.argsort(scores)[-2:]
            keep_edges.extend([group[int(top2[0])], group[int(top2[1])]])

        for e in range(14):
            if e not in keep_edges:
                for j in range(len(PRIMITIVES)):
                    switches2[e][j] = False
        return switches2

    switches_normal_final = keep_top2_edges(switches_normal_bk, normal_prob)
    switches_reduce_final = keep_top2_edges(switches_reduce_bk, reduce_prob)

    def keep_best_op_per_edge(switches_in, probs_global_in):
        sw2 = copy.deepcopy(switches_in)
        for e in range(14):
            active = [j for j, on in enumerate(sw2[e]) if on]
            if not active:
                continue
            best = max(active, key=lambda j: probs_global_in[e][j])
            for j in range(len(PRIMITIVES)):
                sw2[e][j] = (j == best)
        return sw2

    switches_normal_final = keep_best_op_per_edge(switches_normal_final, normal_prob)
    switches_reduce_final = keep_best_op_per_edge(switches_reduce_final, reduce_prob)

    switches_normal_final = enforce_max_one_skip_per_cell(switches_normal_final, normal_prob)
    switches_reduce_final = enforce_max_one_skip_per_cell(switches_reduce_final, reduce_prob)

    genotype = parse_network(switches_normal_final, switches_reduce_final)
    genotype_str = str(genotype)

    np.save(run_dir / "arch_probs_final_normal.npy", normal_prob)
    np.save(run_dir / "arch_probs_final_reduce.npy", reduce_prob)

    _write_json(run_dir / "final_switches_normal.json",
                {"active_ops": _switches_to_jsonable(switches_normal_final)})
    _write_json(run_dir / "final_switches_reduce.json",
                {"active_ops": _switches_to_jsonable(switches_reduce_final)})

    _final_ops_csv(run_dir / "final_ops_normal.csv", switches_normal_final)
    _final_ops_csv(run_dir / "final_ops_reduce.csv", switches_reduce_final)

    (run_dir / "genotype.txt").write_text(genotype_str + "\n", encoding="utf-8")
    _write_json(run_dir / "genotype.json", genotype_to_dict(genotype))

    logging.info("FINAL GENOTYPE (Task2 search, n=6, img=%d): %s", int(args.image_size), genotype_str)

    # per-run ledger
    ledger_csv = Path(args.save_root) / "_SEARCH_LEDGER.csv"
    row = {
        "timestamp": _now_stamp(),
        "run_dir": str(run_dir),
        "run_name": args.run_name,
        "dataset_tag": args.dataset_tag,
        "train_csv": args.train_csv,
        "val_csv": args.val_csv,
        "search_depth_n": args.search_depth_n,
        "stage_layers": ",".join(map(str, stage_layers)),
        "epochs_per_stage": args.epochs_per_stage,
        "total_search_epochs": total_search_epochs,
        "seed": args.seed,
        "image_size": args.image_size,
        "batch_size": args.batch_size,
        "learning_rate": args.learning_rate,
        "learning_rate_min": args.learning_rate_min,
        "momentum": args.momentum,
        "weight_decay": args.weight_decay,
        "arch_learning_rate": args.arch_learning_rate,
        "arch_weight_decay": args.arch_weight_decay,
        "init_channels": args.init_channels,
        "add_width": ",".join(map(str, args.add_width)),
        "dropout_rate": ",".join(map(str, args.dropout_rate)),
        "eps_no_arch": ",".join(map(str, args.eps_no_arch)),
        "grad_clip": args.grad_clip,
        "report_freq": args.report_freq,
        "gpu": args.gpu,
        "device": str(device),
        "torch_version": torch.__version__,
        "cuda_available": bool(use_cuda),
        "genotype": genotype_str,
    }
    _append_csv_row(ledger_csv, LEDGER_FIELDS, row)

    print("\n=== SEARCH COMPLETE ===")
    print("Run folder:", run_dir)
    print("Genotype:", genotype_str)
    print("=======================\n")

    return run_dir, genotype_str


# ---------------------- Batch driver ----------------------

def run_batch(args: argparse.Namespace) -> None:
    save_root = Path(args.save_root)
    save_root.mkdir(parents=True, exist_ok=True)

    ns = _parse_int_list_csv(args.search_depth_list)
    seeds = _parse_int_list_csv(args.seeds)

    # Task 2 guard: n must be 6
    ns = [n for n in ns if n == 6]
    if len(ns) == 0:
        raise ValueError("Task2 search expects n=6. Your --search_depth_list did not include 6.")

    batch_ts = _now_stamp()
    batch_ledger = save_root / "_BATCH_LEDGER.csv"
    planned = [(n, sd) for n in ns for sd in seeds]

    if args.dry_run:
        print("DRY RUN: planned runs:")
        for (n, sd) in planned:
            print(f"  n={n} seed={sd} img={args.image_size} eps_per_stage={args.epochs_per_stage}")
        print(f"Total planned: {len(planned)} runs")
        return

    for i, (n, sd) in enumerate(planned, start=1):
        t0 = time.time()

        run_args = copy.deepcopy(args)
        run_args.search_depth_n = int(n)
        run_args.seed = int(sd)

        signature_prefix = (
            f"{_safe_slug(run_args.run_name)}"
            f"__{_safe_slug(run_args.dataset_tag)}"
            f"__n{run_args.search_depth_n}"
            f"__seed{run_args.seed}"
            f"__img{run_args.image_size}"
            f"__bs{run_args.batch_size}"
            f"__lr{run_args.learning_rate}"
            f"__wd{run_args.weight_decay}"
            f"__archlr{run_args.arch_learning_rate}"
            f"__eps{run_args.epochs_per_stage}x3"
        )

        if args.skip_existing:
            existing = _find_existing_run_dir(save_root, signature_prefix)
            if existing is not None:
                elapsed = time.time() - t0
                _append_csv_row(batch_ledger, BATCH_LEDGER_FIELDS, {
                    "batch_timestamp": batch_ts,
                    "batch_name": args.batch_name,
                    "status": "SKIPPED",
                    "elapsed_sec": f"{elapsed:.2f}",
                    "run_dir": str(existing),
                    "run_name": run_args.run_name,
                    "dataset_tag": run_args.dataset_tag,
                    "train_csv": run_args.train_csv,
                    "val_csv": run_args.val_csv,
                    "search_depth_n": run_args.search_depth_n,
                    "seed": run_args.seed,
                    "epochs_per_stage": run_args.epochs_per_stage,
                    "image_size": run_args.image_size,
                    "batch_size": run_args.batch_size,
                    "gpu": run_args.gpu,
                    "genotype": "",
                    "error": "",
                })
                print(f"[{i}/{len(planned)}] SKIP existing: n={n} seed={sd} -> {existing}")
                continue

        print(f"[{i}/{len(planned)}] RUN: n={n} seed={sd} img={run_args.image_size} eps_per_stage={run_args.epochs_per_stage}")
        try:
            run_dir, genotype_str = run_search_once(run_args)
            elapsed = time.time() - t0
            _append_csv_row(batch_ledger, BATCH_LEDGER_FIELDS, {
                "batch_timestamp": batch_ts,
                "batch_name": args.batch_name,
                "status": "OK",
                "elapsed_sec": f"{elapsed:.2f}",
                "run_dir": str(run_dir),
                "run_name": run_args.run_name,
                "dataset_tag": run_args.dataset_tag,
                "train_csv": run_args.train_csv,
                "val_csv": run_args.val_csv,
                "search_depth_n": run_args.search_depth_n,
                "seed": run_args.seed,
                "epochs_per_stage": run_args.epochs_per_stage,
                "image_size": run_args.image_size,
                "batch_size": run_args.batch_size,
                "gpu": run_args.gpu,
                "genotype": genotype_str,
                "error": "",
            })
        except Exception as e:
            elapsed = time.time() - t0
            err = f"{type(e).__name__}: {e}"
            tb = traceback.format_exc()

            _append_csv_row(batch_ledger, BATCH_LEDGER_FIELDS, {
                "batch_timestamp": batch_ts,
                "batch_name": args.batch_name,
                "status": "FAIL",
                "elapsed_sec": f"{elapsed:.2f}",
                "run_dir": "",
                "run_name": run_args.run_name,
                "dataset_tag": run_args.dataset_tag,
                "train_csv": run_args.train_csv,
                "val_csv": run_args.val_csv,
                "search_depth_n": run_args.search_depth_n,
                "seed": run_args.seed,
                "epochs_per_stage": run_args.epochs_per_stage,
                "image_size": run_args.image_size,
                "batch_size": run_args.batch_size,
                "gpu": run_args.gpu,
                "genotype": "",
                "error": err,
            })
            print(f"[{i}/{len(planned)}] FAIL: n={n} seed={sd} -> {err}")
            print(tb)
            if not args.continue_on_error:
                raise

        # GPU cleanup between runs
        try:
            torch.cuda.empty_cache()
        except Exception:
            pass

    print("\nBATCH COMPLETE")
    print("Batch ledger:", str(batch_ledger))
    print("Per-run ledger:", str(Path(args.save_root) / "_SEARCH_LEDGER.csv"))


def main():
    args = parse_args()

    # AUTO-BATCH: if user provided multiple seeds, run batch automatically
    ns = _parse_int_list_csv(args.search_depth_list)
    seeds = _parse_int_list_csv(args.seeds)

    # Task2: force n=6 even if user typed something else
    ns = [n for n in ns if n == 6]
    if len(ns) == 0:
        ns = [6]
    args.search_depth_list = ",".join(map(str, ns))

    if (len(ns) > 1) or (len(seeds) > 1):
        run_batch(args)
    else:
        args.search_depth_n = 6
        args.seed = seeds[0] if seeds else args.seed
        run_search_once(args)


if __name__ == "__main__":
    main()
