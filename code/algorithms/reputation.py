#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
链上声誉账本（ReputationLedger）：模拟智能合约的声誉存储与更新逻辑。
对应论文 §5.3，Eq. (11)-(12)。

状态：r_i in [0,1]，初始 r0=0.5，链上只读可审计（本实现保留全历史用于 Fig 2）。
更新规则（每轮对参与客户端）：
  - s_i >= theta_h:  正常分支  r <- (1-gamma)*r + gamma*g(s),  g(s)=(1+s)/2   (Eq. 11)
  - s_i <  theta_m:  惩罚分支  r <- (1-kappa*gamma)*r                            (Eq. 12a)
  - 未参与:          时间衰减  r <- r*(1-lambda_dec)                              (Eq. 12b)
"""
import numpy as np

class ReputationLedger:
    def __init__(self, n_clients, r0=0.5, gamma=0.3, kappa=2.0,
                 lambda_dec=0.01, theta_h=0.3, theta_m=0.0):
        self.r0 = r0
        self.r = np.full(n_clients, r0, dtype=np.float64)
        self.gamma, self.kappa = gamma, kappa
        self.lambda_dec = lambda_dec
        self.theta_h, self.theta_m = theta_h, theta_m
        self.history = [self.r.copy()]  # 含初始值

    @staticmethod
    def g(s):
        return 0.5 * (1.0 + float(s))

    def update(self, selected, scores, violations=None):
        """selected: 本轮参与客户端列表; scores: 对应证据分数 s_i（numpy）。
        violations 参数保留兼容但不再影响更新（v3 实验证明幅度违规入声誉会误伤
        Non-IID 下的 honest 大客户端；幅度防御由聚合时的裁剪+排除承担）。"""
        selected = list(selected)
        participated = set(selected)
        for i, s in zip(selected, scores):
            # NaN 防护：证据分数/声誉出现 NaN 时回退到无操作（保留上一轮声誉），
            # 避免 NaN 在链上状态中传播导致全局崩溃（数值稳定性修复）
            if not np.isfinite(s):
                continue
            if s >= self.theta_h:
                self.r[i] = (1 - self.gamma) * self.r[i] + self.gamma * self.g(s)
            elif s < self.theta_m:
                self.r[i] = (1 - self.kappa * self.gamma) * self.r[i]
            else:
                # 灰区（theta_m <= s < theta_h）：弱更新，不奖不罚
                self.r[i] = (1 - 0.5 * self.gamma) * self.r[i] + 0.5 * self.gamma * self.g(s)
            self.r[i] = float(np.clip(self.r[i], 0.0, 1.0))
        # 全局 NaN 防护：任何残留 NaN 回退到冷启动值 r0（保留上一轮无 NaN 的值）
        self.r = np.nan_to_num(self.r, nan=0.5, posinf=1.0, neginf=0.0)
        for i in range(len(self.r)):
            if i not in participated:
                self.r[i] = float(np.clip(self.r[i] * (1 - self.lambda_dec), 0.0, 1.0))
        self.history.append(self.r.copy())

    def weights(self):
        return self.r.copy()

    def reset(self):
        """无跨轮记忆消融：声誉向量重置回冷启动值 r0（历史记录保留供绘图）。"""
        self.r[:] = self.r0
        self.history.append(self.r.copy())
