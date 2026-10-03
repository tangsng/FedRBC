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
    attack: scaling / sign_flip / sybil / noise
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
