#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Byzantine 攻击模拟。

数据层攻击（旧）：
  label_flip —— 二分类标签翻转

模型层攻击（新，仿真威胁模型，FedRBC 设计对抗目标）：
  scaling   —— 幅度放大：delta *= gamma
  sign_flip —— 方向翻转：delta *= -1
  sybil     —— 协同定向投毒：所有恶意客户端上传同一伪造 update
  noise     —— 高斯噪声：delta 替换为范数匹配的随机噪声

模型层攻击在 local_train 之后、聚合之前对 delta 注入。
"""
import numpy as np

def flip_labels(y, rng):
    return 1 - np.asarray(y)

def make_byzantine_set(n_clients, beta, seed):
    """返回恶意客户端索引集合。"""
    rng = np.random.default_rng(seed + 777)
    f = int(round(beta * n_clients))
    return set(rng.choice(n_clients, size=f, replace=False).tolist())

# ---------- 模型层攻击（对 delta 向量操作） ----------
def attack_scaling(delta, gamma=5.0):
    """幅度放大攻击：delta *= gamma。"""
    return delta * gamma

def attack_sign_flip(delta):
    """方向翻转攻击：delta *= -1。"""
    return -delta

def attack_noise(delta, rng, sigma_scale=1.0):
    """高斯噪声攻击：范数匹配的随机噪声替换原 delta。"""
    import torch
    n = delta.norm() + 1e-12
    noise = torch.randn_like(delta)
    noise = noise / (noise.norm() + 1e-12) * n * sigma_scale
    return noise

def apply_model_attacks(deltas, byz_local_idx, attack, rng, gamma=5.0, noise_sigma=1.0):
    """对本轮选中客户端的 delta 施加模型层攻击。

    deltas: (K, d) tensor，本轮选中客户端的 update
    byz_local_idx: 在选中列表中的恶意客户端位置列表
    attack: scaling / sign_flip / sybil / noise / lie
    noise_sigma: noise 攻击的范数倍数（1.0=隐蔽噪声；>2=激进噪声）
    返回：被篡改后的 deltas
    """
    import torch
    if not byz_local_idx:
        return deltas
    out = deltas.clone()
    if attack == "scaling":
        for i in byz_local_idx:
            out[i] = attack_scaling(out[i], gamma)
    elif attack == "sign_flip":
        for i in byz_local_idx:
            out[i] = attack_sign_flip(out[i])
    elif attack == "noise":
        for i in byz_local_idx:
            out[i] = attack_noise(out[i], rng, sigma_scale=noise_sigma)
    elif attack == "lie":
        out = attack_lie(out, byz_local_idx)
    elif attack == "sybil":
        # 协同定向投毒：所有恶意客户端共享同一伪造 update
        # 伪造方向 = 其余（honest）update 均值的反方向，幅度放大 gamma 倍
        honest = [i for i in range(deltas.size(0)) if i not in byz_local_idx]
        if honest:
            ref = deltas[honest].mean(dim=0)
            forged = -ref / (ref.norm() + 1e-12) * (deltas[honest].norm(dim=1).mean()) * gamma
        else:
            forged = torch.randn_like(deltas[0]) * gamma
        for i in byz_local_idx:
            out[i] = forged
    return out


# ---------- LIE 攻击（Baruch et al., "A Little Is Enough", 2019） ----------
def attack_lie(deltas, byz_local_idx):
    """协同隐蔽投毒：恶意 update = 逐坐标 mu - z*sigma。

    z 取标准正态上分位数，使被污染坐标落在诚实分布的边缘
    （Baruch 原文取 z 满足 #fails = K - f - (K-f)/2，常用近似 z = Phi^-1(1 - f/(2K))）。
    幅度小、方向轻度负偏，专门绕过坐标/均值类统计过滤器。
    """
    import torch
    from scipy.stats import norm as _norm
    K = deltas.size(0)
    f = len(byz_local_idx)
    if f == 0 or K <= f:
        return deltas
    z = float(_norm.ppf(1.0 - f / (2.0 * K)))          # f=3,K=10 -> z≈1.04
    mu = deltas.mean(dim=0)
    sigma = deltas.std(dim=0, unbiased=False)
    forged = mu - z * sigma
    out = deltas.clone()
    for i in byz_local_idx:
        out[i] = forged
    return out


# ---------- Backdoor 攻击（触发器 + 模型替换式投毒） ----------
# 触发器：固定 3 个特征位设为 TRIG_VAL（标准化空间 +4.0，罕见离群值，模拟协议字段违例）
TRIG_IDX = (0, 1, 2)
TRIG_VAL = 4.0

def make_backdoor_override(X, y, rng, frac=0.3, label_attack=1):
    """恶意客户端本地数据覆盖：frac 比例样本植入触发器并标记为攻击类。

    返回 (X_bd, y_bd)，供 FLEngine.local_train(data_override=...) 使用。
    """
    X = np.array(X, copy=True)
    y = np.asarray(y).copy()
    n = len(X)
    idx = rng.choice(n, size=max(1, int(frac * n)), replace=False)
    X[idx[:, None], list(TRIG_IDX)] = TRIG_VAL
    y[idx] = label_attack
    return X, y

def add_trigger(X):
    """给干净样本（numpy）植入触发器，用于 ASR 评估。"""
    X = np.array(X, copy=True)
    X[:, list(TRIG_IDX)] = TRIG_VAL
    return X
