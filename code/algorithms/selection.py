#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
客户端选择策略（§5.4, Eq. 13-14）。
u_i: 综合效用（算力 x 链路质量，实验初始化时按 seed 生成并固定）
c_i: 单轮参与代价（时延模型：c_i = 传输 + 本地计算，与 u_i 负相关）
B: 单轮时延预算
"""
import numpy as np

def gen_client_profiles(n_clients, seed):
    """生成固定的客户端画像：u_i, c_i。返回 dict。"""
    rng = np.random.default_rng(seed + 131)
    compute = rng.uniform(0.4, 1.0, n_clients)      # 算力
    link = rng.uniform(0.3, 1.0, n_clients)          # 链路质量
    u = compute * link                               # 综合效用
    c = 1.0 / compute + 0.5 / link                   # 代价（时延，任意单位）
    return dict(u=u, c=c, compute=compute, link=link)

def random_select(n_clients, K, rng, **kw):
    return rng.choice(n_clients, size=K, replace=False).tolist()

def rep_aware_select(reputation, u, c, K, B, **kw):
    """Eq. 14 密度贪心：按 r_i*u_i/c_i 降序，预算 B 内取满 K 个（Prop 2）。"""
    n = len(reputation)
    density = reputation * u / np.maximum(c, 1e-9)
    order = np.argsort(-density)
    chosen, cost = [], 0.0
    for i in order:
        if len(chosen) >= K:
            break
        if cost + c[i] <= B:
            chosen.append(int(i)); cost += c[i]
    if len(chosen) < K:  # 预算不足时退化为按密度取前 K（保证可运行）
        for i in order:
            if int(i) not in chosen:
                chosen.append(int(i))
            if len(chosen) >= K:
                break
    return chosen[:K]
