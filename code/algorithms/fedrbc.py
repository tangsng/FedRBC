#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FedRBC 聚合规则（§5.2, Eq. 5-10），含自适应门控增强：
  s_i = cos(Delta_i, Delta_root)                          (Eq. 5)
  clip: bar_Delta_i = Delta_i * min(1, tau_c/||Delta_i||)     (Eq. 7)
  soft-gating: phi(Delta_i) = bar_Delta_i * max(0, s_i)^p      (Eq. 8)
  q_i = p_i * r_i / sum_j p_j * r_j                       (Eq. 9)
  w_{t+1} = w_t + eta_g * sum_i q_i * phi(Delta_i)        (Eq. 10)

根本性创新（改进 D）：声誉熵驱动的自适应门控（Reputation-Entropy Adaptive Gating）。
  攻击强度在线估计 rho_t = 1 - H_bar(r)，其中 H_bar(r) 是声誉向量的归一化熵。
  - 高攻击（声誉两极分化，熵低，rho→1）：收紧裁剪、硬化门控 → 逼近 FLTrust 高强度鲁棒性
  - 低攻击（声誉一致，熵高，rho→0）：放松裁剪、软化门控 → 逼近 TrimmedMean 干净场景精度
  - tau_c(rho) = tau_lo + (tau_hi - tau_lo) * rho      （攻击越强裁剪越紧）
  - gate_p(rho) = p_lo + (p_hi - p_lo) * rho            （攻击越强门控越硬）

理论支撑：自适应 Huber 稳健估计 / 迭代重加权（IRLS）；声誉熵作为攻击强度的
充分统计量（无偏在线估计，无需知道毒化比例 β）。
"""
import torch
import numpy as np

def evidence_scores(deltas, root_delta):
    """Eq. 5：方向一致性证据分数。"""
    return torch.nn.functional.cosine_similarity(deltas, root_delta.unsqueeze(0), dim=1)

def reputation_entropy(reputations):
    """声誉向量的归一化香农熵 H_bar(r) in [0,1]。
    r 归一化为概率分布后求熵，再除以 log(n) 归一化。
    返回：归一化熵（越高 = 声誉越均匀 = 攻击越弱）。"""
    import math
    r = reputations.clone().detach()
    s = r.sum()
    if s <= 1e-12:
        return 1.0  # 无信息 → 视为无攻击
    p = r / s
    p = p[p > 0]
    if p.numel() <= 1:
        return 0.0  # 完全集中于单一客户端 → 高度两极分化
    H = -(p * p.log()).sum()
    Hbar = H / math.log(p.numel())
    return float(Hbar)

def adaptive_controls(reputations, tau_lo, tau_hi, p_lo, p_hi):
    """改进 D 核心：由声誉熵推导攻击强度 rho，再映射到 (tau_c, gate_p)。"""
    rho = 1.0 - reputation_entropy(reputations)      # 攻击强度在线估计 [0,1]
    tau = tau_lo + (tau_hi - tau_lo) * rho
    gp = p_lo + (p_hi - p_lo) * rho
    return tau, gp, rho

def agg_fedrbc(deltas, root_delta, reputations, data_weights,
               tau_c=5.0, use_rep_weight=True, gate_p=1.0, round_idx=None,
               total_rounds=None, tau_c1=None, adaptive=False,
               tau_lo=2.0, tau_hi=6.0, p_lo=0.6, p_hi=1.4,
               root_align=False, rep_gate_alpha=0.0, tau_rel=None,
               z_thresh=None, soft_T=None, soft_T_anneal=None, **kw):
    """FedRBC 主聚合。

    参数：
      tau_c:        基础裁剪阈值（固定模式）
      tau_rel:      相对裁剪系数 κ（若给出，则 τ_c(t)=κ·‖Δ_root(t)‖，Eq. 7 修订版；
                    随训练进程自适应，对幅度放大攻击鲁棒）
      gate_p:       基础门控幂次（1.0=ReLU）
      adaptive:     是否启用改进 D（声誉熵自适应门控）
      root_align:    改进 E1：root-对齐范数归一化
      rep_gate_alpha: 改进 E2：声誉即时门控强度（0=关闭）
      use_rep_weight=False 即消融 A2。
    """
    s = evidence_scores(deltas, root_delta)                       # Eq. 5
    # NaN 防护：delta/root 全零或含 NaN 时 cosine 会 0/0，回退到 0 证据（中性）
    s = torch.nan_to_num(s, nan=0.0, posinf=1.0, neginf=-1.0)
    norms = deltas.norm(dim=1, keepdim=True) + 1e-12

    # 相对裁剪（优先）：τ_c = κ·median_j‖Δ_j‖（本轮范数中位数参照，
    # 对 ≤50% 恶意鲁棒，与 honest 范数量纲一致，避免 root 范数不可比问题）
    if tau_rel is not None:
        tau = tau_rel * (norms.median().item() + 1e-12)
        gp = gate_p
    elif adaptive:
        r_rep = torch.tensor(reputations, dtype=deltas.dtype, device=deltas.device)
        tau, gp, rho = adaptive_controls(r_rep, tau_lo, tau_hi, p_lo, p_hi)
    elif round_idx is not None and total_rounds is not None and tau_c1 is not None:
        tau = schedule_tau(round_idx, total_rounds, tau_c0=tau_c, tau_c1=tau_c1)
        gp = gate_p
    else:
        tau, gp = tau_c, gate_p

    clip_factor = torch.clamp(torch.tensor(tau, dtype=deltas.dtype,
                                           device=deltas.device) / norms, max=1.0)
    clipped = deltas * clip_factor                                # Eq. 7

    # 改进 E2：声誉即时门控（s' = s * r^alpha），在硬门控前压制低声誉客户
    if rep_gate_alpha > 0:
        r_rep = torch.tensor(reputations, dtype=deltas.dtype, device=deltas.device)
        s = s * (r_rep ** rep_gate_alpha)                          # 声誉加权证据分数

    # 改进 E1：root-对齐范数归一化（缩放 clipped 到 root 范数）
    if root_align:
        root_norm = root_delta.norm() + 1e-12
        clipped = clipped / (clipped.norm(dim=1, keepdim=True) + 1e-12) * root_norm

    pos = torch.relu(s)
    gate = pos if gp == 1.0 else pos ** gp
    # softmax 证据加权（soft_T 给出时启用）：证据以 exp(s/T) 进入权重 q（归一化），
    # 而非乘进 phi 的幅度（避免步长爆炸）；此时 phi 不再乘方向门控
    use_soft = soft_T is not None
    # 温度退火：训练后期将 T_s 从初始值升至 soft_T_anneal（缓解收敛后期 honest
    # 方向分散被过度压制导致的 quorum 整体抑制 / seed 崩溃，见 §5.7 no-attack 讨论）
    T_eff = soft_T
    if use_soft and soft_T_anneal is not None and round_idx is not None and total_rounds:
        frac = (round_idx - 1) / max(total_rounds - 1, 1)
        T_eff = soft_T + (soft_T_anneal - soft_T) * frac   # 线性退火
    # Layer-0 MAD 范数预过滤 + 防御模式仲裁（z_thresh 给出时启用）：
    # - 存在范数统计异常（|z|>z_thresh）→ 幅度攻击模式：异常者排除出聚合，
    #   且本轮关闭方向门控（幅度攻击方向不变，门控无价值且误伤 honest 方向分散）
    # - 无范数异常 → 方向攻击模式：保留方向门控（Eq. 8）
    v_mask = torch.ones(deltas.size(0), dtype=deltas.dtype, device=deltas.device)
    violations = np.zeros(deltas.size(0), dtype=bool)
    if z_thresh is not None:
        n1d = norms.squeeze(1)
        med = n1d.median()
        mad = (n1d - med).abs().median() + 1e-12
        z = (n1d - med).abs() / (1.4826 * mad)
        v_mask = (z <= z_thresh).to(deltas.dtype)
        violations = (z > z_thresh).detach().cpu().numpy()
        if int(violations.sum()) > 0 and not use_soft:
            gate = torch.ones_like(gate)   # 幅度模式：关闭方向门控
    if use_soft:
        gate = torch.ones_like(gate)       # softmax 模式下方向证据走 q，phi 不乘门控
    phi = clipped * gate.unsqueeze(1)                             # Eq. 8
    p = torch.tensor(data_weights, dtype=deltas.dtype, device=deltas.device)
    # Eq. 9 分子：q ∝ p·r·[exp(s/T)]·1[无违规]
    # 模式仲裁：MAD 异常（幅度攻击）时证据权重置 1——纯统计过滤+声誉加权
    # （幅度攻击方向不变，证据无区分度；均匀幸存加权等效统计过滤且信息无损）
    if use_soft and not (z_thresh is not None and int(violations.sum()) > 0):
        evidence_w = torch.exp(s / T_eff)                        # 证据指数权重（q 归一化消尺度）
    else:
        evidence_w = torch.ones_like(s)
    if use_rep_weight:
        r = torch.tensor(reputations, dtype=deltas.dtype, device=deltas.device)
        q = p * r * evidence_w * v_mask                           # Eq. 9 分子（含 Layer-0 与证据）
    else:
        q = p * evidence_w * v_mask
    if q.sum() <= 1e-12:
        return torch.zeros_like(deltas[0]), s.detach().cpu().numpy(), violations
    q = q / q.sum()
    return (phi * q.unsqueeze(1)).sum(dim=0), s.detach().cpu().numpy(), violations

def schedule_tau(t, total_rounds, tau_c0=5.0, tau_c1=2.0):
    """旧改进 A：自适应裁剪阈值退火（保留兼容）。"""
    t = max(1, min(t, total_rounds))
    if total_rounds <= 1:
        return tau_c1
    frac = (t - 1) / (total_rounds - 1)
    return tau_c1 + (tau_c0 - tau_c1) * (0.5 ** (4.0 * frac))
