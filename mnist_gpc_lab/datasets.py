"""MNIST loader for the GPC lab — balanced per-digit subsampling.

Reads the pickle already cached at
`/var/home/fraser/machine_learning/data/mnist/mnist.pkl.gz` (Theano-era
(train, valid, test) tuple of (X float32 [0,1] flattened 784, y int64), no
re-download). Exact-GP Laplace fitting is O(n^3) per Newton step * 10
one-vs-rest classes, so this lab intentionally uses a small balanced
subsample, not the full 60k train set (see LAB_PLAN.md's scope note).
"""

import gzip
import pickle

import numpy as np

_MNIST_PATH = "/var/home/fraser/machine_learning/data/mnist/mnist.pkl.gz"


def _load_raw():
    # Trusted local cache (standard Theano-era MNIST pickle, not fetched from
    # a remote/untrusted source at runtime) -- pickle.load is safe here.
    with gzip.open(_MNIST_PATH, "rb") as f:
        train, valid, test = pickle.load(f, encoding="latin1")
    return train, valid, test


def _balanced_subsample(X, y, per_class, rng):
    idx = []
    for c in range(10):
        cls_idx = np.flatnonzero(y == c)
        chosen = rng.choice(cls_idx, size=per_class, replace=False)
        idx.append(chosen)
    idx = np.concatenate(idx)
    rng.shuffle(idx)
    return X[idx], y[idx]


def load_mnist_subset(n_train_per_class=150, n_val_per_class=30,
                       n_test_per_class=100, seed=0):
    """Balanced (train, val, test) subsets: each a (X, y) pair.

    Train/val come from MNIST's own 50k training split, test from MNIST's
    own 10k test split (no cross-split leakage). X unchanged from the
    cached pickle (already float32 in [0,1], flattened 28x28 -> 784)."""
    rng = np.random.default_rng(seed)
    train_full, _valid_full, test_full = _load_raw()
    X_tr_all, y_tr_all = train_full
    X_te_all, y_te_all = test_full

    X_train, y_train = _balanced_subsample(X_tr_all, y_tr_all, n_train_per_class, rng)

    # val drawn from the remaining training pool (no overlap with X_train) --
    # re-derive the train indices deterministically (same seed/rng sequence)
    # to mask them out, rather than threading indices through _balanced_subsample.
    mask = np.ones(len(y_tr_all), dtype=bool)
    rng2 = np.random.default_rng(seed)
    train_idx = []
    for c in range(10):
        cls_idx = np.flatnonzero(y_tr_all == c)
        chosen = rng2.choice(cls_idx, size=n_train_per_class, replace=False)
        train_idx.append(chosen)
    train_idx = np.concatenate(train_idx)
    mask[train_idx] = False
    X_pool, y_pool = X_tr_all[mask], y_tr_all[mask]
    X_val, y_val = _balanced_subsample(X_pool, y_pool, n_val_per_class, rng)

    X_test, y_test = _balanced_subsample(X_te_all, y_te_all, n_test_per_class, rng)

    return (X_train, y_train), (X_val, y_val), (X_test, y_test)


if __name__ == "__main__":
    (Xtr, ytr), (Xv, yv), (Xte, yte) = load_mnist_subset()
    print("train", Xtr.shape, np.bincount(ytr))
    print("val  ", Xv.shape, np.bincount(yv))
    print("test ", Xte.shape, np.bincount(yte))
