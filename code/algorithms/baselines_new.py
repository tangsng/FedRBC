#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
近年新基线聚合规则（按原论文核心思想忠实重实现，简化版）：

1. RAID (N11, 2026, Repu-Aggregation for IDS)：
   单轮声誉打分（基于 update 在 root 验证集上的 loss 改善）softmax 加权聚合。
   特点：声誉即时、无链上持久性、无方向门控、无幅度裁剪。

2. FedGT (N22, IEEE TIFS 2025, Malicious Client Identification)：
   恶意客户端硬识别（方向与 root 相反者排除）+ 安全聚合。
   特点：单轮硬识别无跨轮记忆、无幅度裁剪、无网络遏制（与 FedRBC 增量对照）。

3. FedGreed (N18, FLTA 2025, Loss-Based Greedy Selection)：
   按 reference-set loss 贪心选优，无恶意比例假设（仅作 Table 1 对比，不作主基线）。

4. EIFFeL (B5, CCS 2022)：
   坐标级对齐检验：对每维坐标取客户端值的 (beta, 1-beta) 分位区间，
   区间外值裁剪到边界，再逐坐标取均值（d-Clipped 共识聚合）。
"""
import torch

# ---------- 1. RAID（2026） ----------
def agg_raid(deltas, root_eval_fn, data_weights, **kw):
    """RAID：root 集 loss 改善打分 → softmax 加权。

    root_eval_fn(delta_i) -> float：应用单个 update 后 root 集 loss（越小越好）。
    为效率，RAID 打分用方向与 root 参考方向一致性近似原论文的 loss 改善评估。
    """
    # 由原论文描述：score_i = loss(w_t) - loss(w_t + delta_i)，经 softmax 加权。
    # 仿真中以余弦一致性近似（避免 K 次完整前向评估，忠实其"增益打分"思想）。
    root_delta = kw.get("root_delta")
    if root_delta is None:
        w = torch.ones(deltas.size(0), device=deltas.device)
        return (deltas * (w / w.sum()).unsqueeze(1)).sum(dim=0)
    cos = torch.nn.functional.cosine_similarity(deltas, root_delta.unsqueeze(0), dim=1)
    score = torch.softmax(cos / 0.5, dim=0)  # 温度 0.5 的 softmax 声誉权
    return (deltas * score.unsqueeze(1)).sum(dim=0)

# ---------- 2. FedGreed（FLTA 2025, Loss-Based Greedy Selection） ----------
def agg_fedgreed(deltas, data_weights, greedy_frac=0.5, **kw):
    """FedGreed：按 update 在服务器参考集上的 loss 改善排序，贪心选取
    loss 最小的客户端子集（不假设恶意比例）。仿真中以方向与 root 参考
    方向的一致性近似 loss 改善（更一致 → 更低 loss），忠实其"贪心选优"思想。

    关键区别（vs RAID）：RAID 是 softmax 软加权；FedGreed 是硬贪心选择
    —— 只保留最靠前的 greedy_frac 比例客户端，其余丢弃。
    """
    root_delta = kw.get("root_delta")
    if root_delta is None:
        w = torch.tensor(data_weights, dtype=deltas.dtype, device=deltas.device)
        return (deltas * (w / w.sum()).unsqueeze(1)).sum(dim=0)
    cos = torch.nn.functional.cosine_similarity(deltas, root_delta.unsqueeze(0), dim=1)
    K = deltas.size(0)
    n_keep = max(1, int(round(K * greedy_frac)))
    order = torch.argsort(cos, descending=True)
    keep = order[:n_keep]
    w = torch.zeros(K, dtype=deltas.dtype, device=deltas.device)
    w[keep] = 1.0
    w = w / w.sum()
    return (deltas * w.unsqueeze(1)).sum(dim=0)


# ---------- 4. FedGT（IEEE TIFS 2025, Malicious Client Identification） ----------
def agg_fedgt(deltas, data_weights, id_thresh=0.0, **kw):
    """FedGT：恶意客户端"识别"+ 安全聚合。通过安全聚合下的群体检验识别恶意
    客户端并硬性排除，剩余诚实客户端按数据量加权聚合。

    仿真中以方向证据 s=cos(Δ,Δ_root) 做硬识别：s < id_thresh（默认 0，即方向
    与 root 相反）判定为恶意并排除（硬过滤，无软加权）；识别后诚实集合按数据量
    加权（与原论文"识别后聚合"一致）。

    与 FedRBC 区别：FedGT 是单轮硬识别，无跨轮声誉持久性、无幅度裁剪、无网络
    遏制；FedRBC 在此之上增加几何门控、相对裁剪、链上声誉与 SDN 隔离。
    """
    root_delta = kw.get("root_delta")
    K = deltas.size(0)
    if root_delta is None:
        w = torch.tensor(data_weights, dtype=deltas.dtype, device=deltas.device)
        return (deltas * (w / w.sum()).unsqueeze(1)).sum(dim=0)
    cos = torch.nn.functional.cosine_similarity(deltas, root_delta.unsqueeze(0), dim=1)
    honest = cos >= id_thresh          # 硬识别：方向不一致者排除
    if honest.sum() == 0:
        honest = torch.ones_like(honest, dtype=torch.bool)
    w = torch.tensor(data_weights, dtype=deltas.dtype, device=deltas.device)
    w = w * honest.float()
    w = w / w.sum()
    return (deltas * w.unsqueeze(1)).sum(dim=0)

# ---------- 3. EIFFeL（CCS 2022） ----------
def agg_eiffel(deltas, trim_beta=0.2, **kw):
    """EIFFeL d-Clipped：逐坐标 (beta, 1-beta) 分位区间裁剪后取均值。"""
    lo = torch.quantile(deltas, trim_beta, dim=0, keepdim=True)
    hi = torch.quantile(deltas, 1.0 - trim_beta, dim=0, keepdim=True)
    clipped = torch.max(torch.min(deltas, hi), lo)
    return clipped.mean(dim=0)
