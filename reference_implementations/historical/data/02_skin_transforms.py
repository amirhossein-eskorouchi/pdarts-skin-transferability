# ============================================================================
# HISTORICAL RESEARCH SOURCE - NOT THE MAINTAINED IMPLEMENTATION
#
# Private archive source: PDARTS/Github/master/02_skin_transforms.py
# Original SHA-256: 71247518dee340a8b0525261a3413c66fb8ef41c9bc79750a1c0ffa2a2ed8a60
#
# This snapshot preserves historical project behavior. Release-blocking
# workstation roots were replaced with PROJECT_ROOT. A workstation identifier
# in author metadata was replaced with a descriptive attribution.
# ============================================================================
# -*- coding: utf-8 -*-
"""
Created on Wed Dec 17 11:08:03 2025

@author: original project author (workstation identifier redacted)
"""

# 02_skin_transforms.py
# Central transforms for skin lesion datasets (ISIC / PAD-UFES).
# Designed to be used by both search and evaluation scripts.

from __future__ import annotations
from dataclasses import dataclass
from typing import Tuple

import torch

try:
    import torchvision.transforms as T
except ImportError as e:
    raise ImportError("torchvision is required. Please install torchvision.") from e


# ImageNet normalization (common default for RGB CNN backbones)
IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD  = (0.229, 0.224, 0.225)


@dataclass(frozen=True)
class TransformConfig:
    image_size: int = 32
    # Manuscript mentions only flips; keep it minimal
    hflip: bool = True
    vflip: bool = True

    # Normalization is optional (can disable if you want strict “just ToTensor”)
    normalize: bool = True
    mean: Tuple[float, float, float] = IMAGENET_MEAN
    std: Tuple[float, float, float] = IMAGENET_STD


def build_train_transform(cfg: TransformConfig) -> T.Compose:
    tfms = [
        T.Resize((cfg.image_size, cfg.image_size)),
    ]
    if cfg.hflip:
        tfms.append(T.RandomHorizontalFlip(p=0.5))
    if cfg.vflip:
        tfms.append(T.RandomVerticalFlip(p=0.5))

    tfms.append(T.ToTensor())

    if cfg.normalize:
        tfms.append(T.Normalize(mean=cfg.mean, std=cfg.std))

    return T.Compose(tfms)


def build_eval_transform(cfg: TransformConfig) -> T.Compose:
    # No random augmentation for val/test
    tfms = [
        T.Resize((cfg.image_size, cfg.image_size)),
        T.ToTensor(),
    ]
    if cfg.normalize:
        tfms.append(T.Normalize(mean=cfg.mean, std=cfg.std))
    return T.Compose(tfms)


# --------------------------- SMOKE TEST ---------------------------
if __name__ == "__main__":
    from PIL import Image
    import numpy as np

    cfg = TransformConfig(image_size=32, normalize=True)

    train_t = build_train_transform(cfg)
    eval_t = build_eval_transform(cfg)

    # Fake image just to confirm pipeline output shape/type
    fake = Image.fromarray((np.random.rand(64, 64, 3) * 255).astype("uint8"), mode="RGB")

    x_train = train_t(fake)
    x_eval = eval_t(fake)

    print("Train tensor shape:", tuple(x_train.shape), "dtype:", x_train.dtype)
    print("Eval tensor shape:", tuple(x_eval.shape), "dtype:", x_eval.dtype)
    print("Train min/max:", float(x_train.min()), float(x_train.max()))
