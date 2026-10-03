#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""通用工具：seed、日志、JSON 落盘。"""
import os, json, random, logging
import numpy as np
import torch

def set_seed(seed):
    random.seed(seed); np.random.seed(seed)
    torch.manual_seed(seed); torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False

def get_logger(name="fedrbc"):
    lg = logging.getLogger(name)
    if not lg.handlers:
        h = logging.StreamHandler()
        h.setFormatter(logging.Formatter("[%(asctime)s] %(message)s", "%H:%M:%S"))
        lg.addHandler(h); lg.setLevel(logging.INFO)
    return lg

def save_json(obj, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, default=_jsonable)

def _jsonable(o):
    if isinstance(o, (np.integer,)): return int(o)
    if isinstance(o, (np.floating,)): return float(o)
    if isinstance(o, np.ndarray): return o.tolist()
    return str(o)

class CSVLogger:
    """逐行追加 CSV（round 级指标）。"""
    def __init__(self, path, header):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.path = path
        with open(path, "w", encoding="utf-8") as f:
            f.write(",".join(header) + "\n")
    def log(self, row):
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(",".join(str(x) for x in row) + "\n")
