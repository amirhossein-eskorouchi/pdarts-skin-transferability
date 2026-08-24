# Upstream P-DARTS attribution and release boundary

## Identified upstream project

The bundled core source is associated with the official P-DARTS implementation:

- Repository: https://github.com/chenxin061/pdarts
- Paper: Xin Chen, Lingxi Xie, Jun Wu, and Qi Tian, *Progressive
  Differentiable Architecture Search: Bridging the Depth Gap between Search and
  Evaluation*, ICCV 2019.
- License: https://github.com/chenxin061/pdarts/blob/master/LICENSE

The official P-DARTS repository also states that its implementation is based on
DARTS.

## License boundary

The official P-DARTS license provides the software for noncommercial testing
and evaluation and reserves rights not expressly granted.

Therefore, this repository does not republish the ten byte-identical P-DARTS
core files found in the private research archive.

The exact upstream Git revision represented by the bundled ZIP files cannot be
established because those bundles contain no authoritative Git metadata.

## Byte-identical private-archive counterparts

| Outer private-archive source | Bundled counterpart |
|---|---|
| `PDARTS/Github/master/genotypes.py` | `pdarts-master/genotypes.py` |
| `PDARTS/Github/master/model.py` | `pdarts-master/model.py` |
| `PDARTS/Github/master/model_search.py` | `pdarts-master/model_search.py` |
| `PDARTS/Github/master/operations.py` | `pdarts-master/operations.py` |
| `PDARTS/Github/master/test.py` | `pdarts-master/test.py` |
| `PDARTS/Github/master/test_imagenet.py` | `pdarts-master/test_imagenet.py` |
| `PDARTS/Github/master/train_cifar.py` | `pdarts-master/train_cifar.py` |
| `PDARTS/Github/master/train_imagenet.py` | `pdarts-master/train_imagenet.py` |
| `PDARTS/Github/master/train_search.py` | `pdarts-master/train_search.py` |
| `PDARTS/Github/master/visualize.py` | `pdarts-master/visualize.py` |

## Public representation

These files are represented through hashes, attribution, scientific interface
documentation, and links to the official repository and license. They are not
copied into `src/` or `reference_implementations/`.

## Maintained implementation requirement

Future maintained code must use an authorized dependency, separately obtained
permission, or an independently implemented interface based on the scientific
specification. It must not copy the upstream source.
