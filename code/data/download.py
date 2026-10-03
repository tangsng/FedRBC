#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WUSTL-EHMS-2020 数据集下载与预处理。
数据集出处：Hady et al., "Intrusion Detection System for Healthcare Systems Using
Medical and Network Data: A Comparison Study", IEEE Access, 2020.
官方页面：https://www.cse.wustl.edu/~jain/ehms/index.html

数据流：44 个网络流特征 + label(0=normal, 1=attack)。
多镜像 fallback；全部失败时明确报错（不使用任何合成数据冒充真实数据）。
"""
import os, sys, ssl, zipfile, urllib.request, argparse
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

MIRRORS = [
    # 官方直链（2026-09-30 验证可用，3,946,888 bytes）
    ("https://www.cse.wustl.edu/~jain/ehms/ftp/wustl-ehms-2020_with_attacks_categories.csv",
     "wustl-ehms-2020.csv"),
]

def download(data_dir):
    os.makedirs(data_dir, exist_ok=True)
    dst = os.path.join(data_dir, "wustl-ehms-2020.csv")
    if os.path.exists(dst) and os.path.getsize(dst) > 10000:
        print("[data] 已存在: %s (%.1f MB)" % (dst, os.path.getsize(dst) / 1e6))
        return dst
    ctx = ssl.create_default_context()
    try:
        import certifi; ctx = ssl.create_default_context(cafile=certifi.where())
    except Exception:
        pass
    for url, name in MIRRORS:
        try:
            print("[data] 尝试下载: %s" % url)
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=60, context=ctx) as r:
                blob = r.read()
            if len(blob) < 10000:
                raise ValueError("文件过小(%d B)，疑似无效" % len(blob))
            with open(dst, "wb") as f:
                f.write(blob)
            print("[data] 下载成功: %.1f MB" % (len(blob) / 1e6))
            return dst
        except Exception as e:
            print("[data] 失败: %s" % str(e)[:120])
    raise RuntimeError(
        "WUSTL-EHMS-2020 所有镜像均下载失败。请手动从 "
        "https://www.cse.wustl.edu/~jain/ehms/index.html 或 Kaggle "
        "获取 wustl-ehms-2020.csv 并放入 %s" % data_dir)

def load_and_preprocess(csv_path, test_ratio=0.2, root_size=500, seed=42):
    """返回 (X_tr, y_tr, X_te, y_te, X_root, y_root, scaler, feat_dim)。
    root 集：服务器端小型干净验证集（FLTrust/FedRBC 用），从训练集划出。"""
    df = pd.read_csv(csv_path)
    df = df.dropna()
    label_col = None
    for c in df.columns:
        if c.strip().lower() in ("label", "class", "attack"):
            label_col = c; break
    assert label_col is not None, "未找到标签列: %s" % list(df.columns)
    # 丢弃明显非特征列（流标识等）
    drop_cols = [label_col] + [c for c in df.columns
                               if c.strip().lower() in ("flownum", "srcaddr", "dstaddr",
                                                        "srcmac", "dstmac", "timestamp", "seq")]
    y = df[label_col].astype(int).values
    # 统一为二分类 0/1
    y = (y > 0).astype(np.int64)
    X = df.drop(columns=[c for c in drop_cols if c in df.columns])
    X = X.select_dtypes(include=[np.number]).astype(np.float32).values
    # 剔除常数列/无穷列
    std0 = X.std(axis=0)
    keep = np.isfinite(std0) & (std0 > 0)
    X = X[:, keep]
    X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)

    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=test_ratio, random_state=seed, stratify=y)
    scaler = StandardScaler().fit(X_tr)
    X_tr, X_te = scaler.transform(X_tr), scaler.transform(X_te)
    # root 验证集（分层小样本）
    X_root, _, y_root, _ = train_test_split(
        X_tr, y_tr, train_size=root_size, random_state=seed, stratify=y_tr)
    print("[data] train=%d test=%d root=%d feat=%d | 攻击占比 train=%.2f test=%.2f"
          % (len(X_tr), len(X_te), len(X_root), X_tr.shape[1], y_tr.mean(), y_te.mean()))
    return (X_tr.astype(np.float32), y_tr, X_te.astype(np.float32), y_te,
            X_root.astype(np.float32), y_root, scaler, X_tr.shape[1])

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default=os.path.join(os.path.dirname(__file__), "..", "..", "data"))
    args = ap.parse_args()
    path = download(os.path.abspath(args.data_dir))
    load_and_preprocess(path)
