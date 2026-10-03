#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Dirichlet Non-IID 数据划分（Eq. 22: q_i ~ Dir(alpha * 1)）。"""
import numpy as np

def dirichlet_partition(y, n_clients, alpha=0.5, seed=42, min_size=50):
    """按标签对样本索引做 Dirichlet 划分，返回 list[np.ndarray]（每客户端索引）。
    alpha 越小 Non-IID 程度越高。min_size 逐级降级（50->20->1）；
    极端 alpha 重试仍失败时，对大客户端轮转再平衡，保证无空客户端（如实记录）。"""
    rng = np.random.default_rng(seed)
    n_classes = int(y.max()) + 1
    for ms in (min_size, 20, 1):
        for attempt in range(200):
            idx_by_cls = [np.where(y == c)[0] for c in range(n_classes)]
            for a in idx_by_cls:
                rng.shuffle(a)
            parts = [[] for _ in range(n_clients)]
            for c in range(n_classes):
                props = rng.dirichlet([alpha] * n_clients)
                cuts = (np.cumsum(props) * len(idx_by_cls[c])).astype(int)[:-1]
                for i, seg in enumerate(np.split(idx_by_cls[c], cuts)):
                    parts[i].extend(seg.tolist())
            sizes = [len(p) for p in parts]
            if min(sizes) >= ms:
                if ms < min_size:
                    print("[partition] alpha=%.2f: min_size 降级 %d->%d (实际最小客户端 %d 样本)"
                          % (alpha, min_size, ms, min(sizes)))
                return [np.array(sorted(p), dtype=np.int64) for p in parts]
    # 再平衡兜底：从最大客户端匀样本给空客户端
    print("[partition] alpha=%.2f: 重试未达 min_size=1，启用大客户端再平衡" % alpha)
    parts_sets = [set(p) for p in parts]
    for i in range(n_clients):
        while len(parts_sets[i]) < 1:
            j = max(range(n_clients), key=lambda t: len(parts_sets[t]) if t != i else -1)
            donor = list(parts_sets[j])
            give = donor[:max(1, len(donor) // 10)]
            parts_sets[j] -= set(give)
            parts_sets[i] |= set(give)
    return [np.array(sorted(p), dtype=np.int64) for p in parts_sets]

def partition_stats(parts, y):
    n_classes = int(y.max()) + 1
    stats = []
    for i, idx in enumerate(parts):
        cnt = np.bincount(y[idx], minlength=n_classes)
        stats.append(dict(client=i, size=len(idx), **{"cls%d" % c: int(cnt[c]) for c in range(n_classes)}))
    return stats
