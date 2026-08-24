# ============================================================================
# HISTORICAL RESEARCH SOURCE - NOT THE MAINTAINED IMPLEMENTATION
#
# Private archive source: PDARTS/Github/master/skin_transforms.py
# Original SHA-256: dbcd25375c81220a8c7b8fce966a662aaaa09160112f5dee344771f8d7874acd
#
# This snapshot preserves historical project behavior. Release-blocking
# workstation roots were replaced with PROJECT_ROOT. A workstation identifier
# in author metadata was replaced with a descriptive attribution.
# ============================================================================
"""
skin_transforms.py
===================

Minimal image transformations used for the skin lesion datasets.  The
manuscript specifies that only horizontal and vertical flips should be
applied as data augmentation and that images should be resized to a
CIFAR‑like resolution.  This module provides a small
configuration dataclass and helper functions to build train and
evaluation transforms accordingly.

The default normalisation uses ImageNet statistics, which are a good
starting point for RGB CNNs.  You can disable normalisation by
setting ``normalize=False`` in the ``TransformConfig``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

try:
    import torchvision.transforms as T
except ImportError as e:
    raise ImportError('torchvision is required for skin_transforms.py') from e


# ImageNet per‑channel normalisation values
IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD  = (0.229, 0.224, 0.225)


@dataclass(frozen=True)
class TransformConfig:
    image_size: int = 32
    hflip: bool = True
    vflip: bool = True
    normalize: bool = True
    mean: Tuple[float, float, float] = IMAGENET_MEAN
    std: Tuple[float, float, float] = IMAGENET_STD


def build_train_transform(cfg: TransformConfig) -> T.Compose:
    """Construct the training transform pipeline."""
    tfms = [T.Resize((cfg.image_size, cfg.image_size))]
    if cfg.hflip:
        tfms.append(T.RandomHorizontalFlip(p=0.5))
    if cfg.vflip:
        tfms.append(T.RandomVerticalFlip(p=0.5))
    tfms.append(T.ToTensor())
    if cfg.normalize:
        tfms.append(T.Normalize(mean=cfg.mean, std=cfg.std))
    return T.Compose(tfms)


def build_eval_transform(cfg: TransformConfig) -> T.Compose:
    """Construct the evaluation/validation transform pipeline."""
    tfms = [T.Resize((cfg.image_size, cfg.image_size)), T.ToTensor()]
    if cfg.normalize:
        tfms.append(T.Normalize(mean=cfg.mean, std=cfg.std))
    return T.Compose(tfms)


if __name__ == '__main__':
    # Simple smoke test to verify output shapes
    from PIL import Image
    import numpy as np
    cfg = TransformConfig(image_size=32, normalize=True)
    train_t = build_train_transform(cfg)
    eval_t = build_eval_transform(cfg)
    fake_img = Image.fromarray((np.random.rand(64, 64, 3) * 255).astype('uint8'), mode='RGB')
    x_train = train_t(fake_img)
    x_eval = eval_t(fake_img)
    print('Train tensor shape:', tuple(x_train.shape), 'dtype:', x_train.dtype)
    print('Eval tensor shape:', tuple(x_eval.shape), 'dtype:', x_eval.dtype)
    print('Train min/max:', float(x_train.min()), float(x_train.max()))
