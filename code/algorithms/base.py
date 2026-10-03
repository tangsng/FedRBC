#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""FL 仿真引擎：客户端本地训练 + 可插拔聚合规则 + Byzantine 攻击注入。"""
import copy, time
import numpy as np
import torch
import torch.nn as nn

from utils.metrics import evaluate
from utils.attack import flip_labels

class FLEngine:
    def __init__(self, model_fn, X_tr_parts, y_tr_parts, X_root, y_root,
                 X_te, y_te, device, byz_set=(), local_epochs=1, batch=32,
                 lr=0.01, momentum=0.9, weight_decay=0.0, prox_mu=0.0, seed=42):
        """
        model_fn: 无参函数返回新模型实例
        X_tr_parts/y_tr_parts: 每客户端数据（numpy 数组列表）
        byz_set: Byzantine 客户端索引集合（训练时标签翻转）
        prox_mu: FedProx 近端系数（0 = FedAvg）
        """
        self.model_fn, self.device = model_fn, device
        self.global_model = model_fn().to(device)
        self.X_parts, self.y_parts = X_tr_parts, y_tr_parts
        self.X_root = torch.from_numpy(X_root).to(device)
        self.y_root = torch.from_numpy(y_root).to(device)
        self.X_te, self.y_te = X_te, y_te
        self.byz_set = set(byz_set)
        self.E, self.batch, self.lr = local_epochs, batch, lr
        self.momentum, self.wd, self.prox_mu = momentum, weight_decay, prox_mu
        self.rng = np.random.default_rng(seed)
        self.crit = nn.CrossEntropyLoss()
        self.n_out = int(self.y_root.max().item()) + 1  # root 集分层覆盖全部类别

    # ---------- 客户端本地训练（Eq. 4） ----------
    def local_train(self, cid, epochs=None, data_override=None):
        model = copy.deepcopy(self.global_model)
        model.train()
        if data_override is not None:
            X, y = data_override
        else:
            X, y = self.X_parts[cid], self.y_parts[cid]
            if cid in self.byz_set:
                y = flip_labels(y, self.rng)  # label-flip 攻击
        X = torch.from_numpy(X).to(self.device)
        y = torch.from_numpy(np.asarray(y)).to(self.device)
        # 类别不平衡处理：按本地类频率倒数加权（sklearn 'balanced' 公式；单类客户端退化为均匀权重）
        cnt = torch.bincount(y, minlength=self.n_out).float()
        if (cnt > 0).all() and cnt.numel() == self.n_out:
            cw = (cnt.sum() / (self.n_out * cnt.clamp(min=1.0))).to(self.device)
            crit = nn.CrossEntropyLoss(weight=cw)
        else:
            crit = nn.CrossEntropyLoss()
        opt = torch.optim.SGD(model.parameters(), lr=self.lr,
                              momentum=self.momentum, weight_decay=self.wd)
        gparams = [p.detach().clone() for p in self.global_model.parameters()]
        E = epochs or self.E
        n = len(X)
        for _ in range(E):
            perm = torch.randperm(n, device=self.device)
            for i in range(0, n, self.batch):
                idx = perm[i:i + self.batch]
                opt.zero_grad()
                loss = crit(model(X[idx]), y[idx])
                if self.prox_mu > 0:  # FedProx 近端项
                    prox = sum(((p - gp) ** 2).sum() for p, gp in zip(model.parameters(), gparams))
                    loss = loss + 0.5 * self.prox_mu * prox
                loss.backward()
                opt.step()
        # 更新量 Delta = w_i - w_global（展平向量）
        delta = torch.cat([(p - gp).reshape(-1)
                           for p, gp in zip(model.parameters(), gparams)])
        return delta.detach()

    def root_update(self):
        """服务器 root 验证集上的参考更新 Delta_root（Eq. 6）。同样使用类别加权。"""
        model = copy.deepcopy(self.global_model)
        model.train()
        opt = torch.optim.SGD(model.parameters(), lr=self.lr, momentum=self.momentum)
        gparams = [p.detach().clone() for p in self.global_model.parameters()]
        n_cls = self.n_out
        cnt = torch.bincount(self.y_root, minlength=n_cls).float()
        if (cnt > 0).all():
            crit = nn.CrossEntropyLoss(weight=(cnt.sum() / (n_cls * cnt.clamp(min=1.0))).to(self.device))
        else:
            crit = nn.CrossEntropyLoss()
        n = len(self.X_root)
        for _ in range(self.E):
            perm = torch.randperm(n, device=self.device)
            for i in range(0, n, self.batch):
                idx = perm[i:i + self.batch]
                opt.zero_grad()
                crit(model(self.X_root[idx]), self.y_root[idx]).backward()
                opt.step()
        return torch.cat([(p - gp).reshape(-1)
                          for p, gp in zip(model.parameters(), gparams)]).detach()

    # ---------- 应用聚合结果（Eq. 10） ----------
    @torch.no_grad()
    def apply_update(self, agg_delta, eta_g=1.0):
        # 全局 NaN 防护：聚合结果含 NaN/Inf 时跳过本轮更新（保留上一轮模型），
        # 阻断 NaN 在全局模型中传播导致的全预测退化/崩溃（数值稳定性修复）
        if not torch.isfinite(agg_delta).all():
            return
        offset = 0
        for p in self.global_model.parameters():
            numel = p.numel()
            p.add_(eta_g * agg_delta[offset:offset + numel].view_as(p))
            offset += numel

    def evaluate(self, threshold=0.5):
        return evaluate(self.global_model, self.X_te, self.y_te, self.device,
                        threshold=threshold)

    def param_vector(self):
        return torch.cat([p.detach().reshape(-1) for p in self.global_model.parameters()])
