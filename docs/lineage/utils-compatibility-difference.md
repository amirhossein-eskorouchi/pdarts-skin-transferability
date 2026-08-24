# Historical utils.py difference

## Compared files

| Role | Path | SHA-256 |
|---|---|---|
| Bundled P-DARTS utility | `PDARTS/Github/pdarts-master.zip` → `pdarts-master/utils.py` | `e5b80251f41060bdf9cc19e6aeb9596b68d97e26735526f8426073bf440acbcc` |
| Local outer utility | `PDARTS/Github/master/utils.py` | `6e6e855c44bef47d9e2c5ce52b79f2b131862d8e0b9e783cab54c7cbff64e075` |

## Exact verified differences

### Compatibility repair

Bundled expression:

`.view(-1)`

Local expression:

`.reshape(-1)`

This is a tensor-contiguity compatibility repair. Both expressions request a
one-dimensional representation, while `reshape` can accommodate a
non-contiguous tensor.

### Formatting-only change

Bundled expression:

`100.0/batch_size`

Local expression:

`100.0 / batch_size`

This whitespace change has no behavioral effect.

After normalizing these two edits, the files are text-identical. No additional
difference was detected.

## Final disposition

`REIMPLEMENT_FROM_SPECIFICATION`

The full local utility is not republished because it is otherwise derived from
the bundled P-DARTS source. Only required behavior may enter maintained code,
with attribution and focused tests.
