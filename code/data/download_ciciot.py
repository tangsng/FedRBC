#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CICIoT2023 数据集下载与预处理（第二数据集，用于跨数据集泛化验证）。

出处：E. C. P. Neto et al., "CICIoT2023: A Real-Time Dataset and Benchmark for
Large-Scale Attacks in IoT Environment", Sensors, 2023, doi:10.3390/s23135941.
官方数据为多 part CSV（~13GB 未压缩，4500 万行）；本模块下载第一个 part
（part-00000，238,687 行，47 特征，多类 DDoS/DoS 攻击标签），作为规模与
WUSTL-EHMS 相当的降采样子集，二值化为 benign vs attack。

LFS 直链：GitHub LFS media URL（media.githubusercontent.com），已实测可用。
"""
import os, ssl, urllib.request, urllib.parse
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

PART_URL = ("https://media.githubusercontent.com/media/val-co/CIC-IoT-2023-Dataset/"
            "master/part-00000-363d1ba3-8ab5-4f96-bc25-4d5862db7cb9-c000.csv")
PART_NAME = "cici-iot-2023-part0.csv"


def download(data_dir):
    os.makedirs(data_dir, exist_ok=True)
    dst = os.path.join(data_dir, PART_NAME)
    if os.path.exists(dst) and os.path.getsize(dst) > 1000000:
        print("[data] CICIoT2023 已存在: %s (%.1f MB)" % (dst, os.path.getsize(dst) / 1e6))
        return dst
    ctx = ssl.create_default_context()
    try:
        import certifi; ctx = ssl.create_default_context(cafile=certifi.where())
    except Exception:
        pass
    print("[data] 尝试下载 CICIoT2023 part0: %s" % PART_URL)
    req = urllib.request.Request(PART_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=300, context=ctx) as r:
        blob = r.read()
    if len(blob) < 1000000:
        raise ValueError("文件过小(%d B)，疑似 LFS 指针或下载失败" % len(blob))
    with open(dst, "wb") as f:
        f.write(blob)
    print("[data] CICIoT2023 下载成功: %.1f MB" % (len(blob) / 1e6))
    return dst


def load_and_preprocess(csv_path, test_ratio=0.2, root_size=500, seed=42, max_rows=None,
                        balance=True):
    """返回 (X_tr, y_tr, X_te, y_te, X_root, y_root, scaler, feat_dim)。标签二值化。
    balance=True 时对多数类（攻击）降采样至与 benign 相近量级，避免 98% 攻击的
    极端失衡使二分类退化（CICIoT2023 整体 benign 仅 ~2.34%）。"""
    df = pd.read_csv(csv_path, nrows=max_rows) if max_rows else pd.read_csv(csv_path)
    df = df.dropna()
    label_col = "label"
    # 二值化：benign 类（"benigntraffic"/"benign" 等）→ 0，其余攻击类别 → 1
    lbl = df[label_col].astype(str).str.lower()
    benign_mask = lbl.str.contains("benign", na=False)
    y = (~benign_mask).astype(np.int64).values
    drop_cols = [label_col] + [c for c in df.columns
                               if c.strip().lower() in ("flownum", "srcaddr", "dstaddr",
                                                        "srcmac", "dstmac", "timestamp", "seq")]
    X = df.drop(columns=[c for c in drop_cols if c in df.columns])
    X = X.select_dtypes(include=[np.number]).astype(np.float32).values
    # 剔除常数列/无穷列
    std0 = X.std(axis=0)
    keep = np.isfinite(std0) & (std0 > 0)
    X = X[:, keep]
    X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)

    if balance:
        rng = np.random.default_rng(seed)
        benign_idx = np.where(y == 0)[0]
        attack_idx = np.where(y == 1)[0]
        if len(benign_idx) > 0 and len(attack_idx) > 0:
            # 攻击类降采样到 benign 的 3 倍（保留适度不平衡，与真实 IDS 场景一致）
            n_attack_keep = min(len(attack_idx), len(benign_idx) * 3)
            attack_keep = rng.choice(attack_idx, size=n_attack_keep, replace=False)
            keep_idx = np.sort(np.concatenate([benign_idx, attack_keep]))
            X, y = X[keep_idx], y[keep_idx]
            print("[data] CICIoT2023 平衡采样：benign=%d attack=%d (attack/benign≈%.1f)"
                  % (len(benign_idx), n_attack_keep, n_attack_keep / max(len(benign_idx), 1)))

    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=test_ratio, random_state=seed, stratify=y)
    scaler = StandardScaler().fit(X_tr)
    X_tr, X_te = scaler.transform(X_tr), scaler.transform(X_te)
    X_root, _, y_root, _ = train_test_split(
        X_tr, y_tr, train_size=root_size, random_state=seed, stratify=y_tr)
    print("[data] CICIoT2023 train=%d test=%d root=%d feat=%d | 攻击占比 train=%.2f test=%.2f"
          % (len(X_tr), len(X_te), len(X_root), X_tr.shape[1], y_tr.mean(), y_te.mean()))
    return (X_tr.astype(np.float32), y_tr, X_te.astype(np.float32), y_te,
            X_root.astype(np.float32), y_root, scaler, X_tr.shape[1])


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default=os.path.join(os.path.dirname(__file__), "..", "..", "data"))
    args = ap.parse_args()
    path = download(os.path.abspath(args.data_dir))
    load_and_preprocess(path)
