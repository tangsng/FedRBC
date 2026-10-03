#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""评估指标：Accuracy / F1 / AUC。

说明：默认使用固定 0.5 决策阈值（softmax 输出）。本地训练已用类别加权
交叉熵（class-weighted CE）处理类别不平衡，softmax 概率已隐式编码先验，
无需事后阈值校准（事后调阈值会把 F1/Acc 一并破坏——见 2026-09-30 诊断）。
AUC 与阈值无关，反映模型判别能力本身。
"""
import numpy as np
import torch
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score

@torch.no_grad()
def evaluate(model, X, y, device, batch=1024, threshold=0.5):
    model.eval()
    probs_all = []
    for i in range(0, len(X), batch):
        xb = torch.from_numpy(X[i:i + batch]).to(device)
        logits = model(xb)
        probs_all.append(torch.softmax(logits, dim=1)[:, 1].cpu().numpy())
    probs = np.concatenate(probs_all)
    thr = float(threshold)
    pred = (probs >= thr).astype(np.int64)
    acc = accuracy_score(y, pred)
    f1 = f1_score(y, pred, average="binary", zero_division=0)
    try:
        auc = roc_auc_score(y, probs)
    except ValueError:
        auc = float("nan")
    return dict(acc=float(acc), f1=float(f1), auc=float(auc))
