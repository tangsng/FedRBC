#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""聚合规则：FedAvg / FedProx / Krum / TrimmedMean / FLTrust / FedRBC。"""
import torch

# ---------- FedAvg（Eq. 3 对照） ----------
def agg_fedavg(deltas, weights, **kw):
    w = torch.tensor(weights, dtype=deltas.dtype, device=deltas.device)
    w = w / w.sum()
    return (deltas * w.unsqueeze(1)).sum(dim=0)

# ---------- Krum（Blanchard et al., 2017） ----------
def agg_krum(deltas, weights=None, n_byz=0, **kw):
    n = deltas.size(0)
    dists = torch.cdist(deltas, deltas) ** 2
    m = n - n_byz - 2
    m = max(1, min(m, n - 1))
    scores = dists.sort(dim=1).values[:, :m].sum(dim=1)
    idx = scores.argmin()
    return deltas[idx]

# ---------- Coordinate-wise Trimmed Mean（Yin et al., 2018） ----------
def agg_trimmed_mean(deltas, weights=None, trim_ratio=0.2, **kw):
    k = int(deltas.size(0) * trim_ratio)
    sorted_d, _ = deltas.sort(dim=0)
    if k > 0:
        sorted_d = sorted_d[k:-k]
    return sorted_d.mean(dim=0)

# ---------- FLTrust（Cao et al., NDSS 2021） ----------
def agg_fltrust(deltas, root_delta, **kw):
    cos = torch.nn.functional.cosine_similarity(deltas, root_delta.unsqueeze(0), dim=1)
    ts = torch.relu(cos)
    if ts.sum() <= 0:
        return torch.zeros_like(deltas[0])
    # 归一化客户端更新到 root 范数（FLTrust 原始做法）
    root_norm = root_delta.norm() + 1e-12
    normed = deltas / (deltas.norm(dim=1, keepdim=True) + 1e-12) * root_norm
    w = ts / ts.sum()
    return (normed * w.unsqueeze(1)).sum(dim=0)
