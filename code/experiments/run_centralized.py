#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""集中式训练上界（R2.1）：全数据单点训练同一 MLP，供论文锚定"检测器工作区间"。

用法：python run_centralized.py --seed 42 [--epochs 60]
输出：results/raw/centralized_s<seed>_rev1_summary.json
"""
import os, sys, time, json, argparse
import numpy as np
import torch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from data.download import download, load_and_preprocess
from models.mlp import MLPIDS
from utils.metrics import evaluate

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--epochs", type=int, default=60)
    ap.add_argument("--batch", type=int, default=64)
    ap.add_argument("--lr", type=float, default=0.05)
    ap.add_argument("--gpu", type=int, default=0)
    ap.add_argument("--data-dir", default=os.path.join(os.path.dirname(__file__), "..", "..", "data"))
    ap.add_argument("--out-dir", default=os.path.join(os.path.dirname(__file__), "..", "..", "results", "raw"))
    args = ap.parse_args()

    torch.manual_seed(args.seed); np.random.seed(args.seed)
    device = torch.device("cuda:%d" % args.gpu if torch.cuda.is_available() else "cpu")
    csv_path = download(os.path.abspath(args.data_dir))
    X_tr, y_tr, X_te, y_te, _, _, _, feat_dim = load_and_preprocess(csv_path, seed=args.seed)

    model = MLPIDS(in_dim=feat_dim).to(device)
    X = torch.from_numpy(X_tr).to(device)
    y = torch.from_numpy(np.asarray(y_tr)).to(device)
    n_out = 2
    cnt = torch.bincount(y, minlength=n_out).float()
    crit = torch.nn.CrossEntropyLoss(weight=(cnt.sum() / (n_out * cnt.clamp(min=1.0))).to(device))
    opt = torch.optim.SGD(model.parameters(), lr=args.lr, momentum=0.9)

    t0 = time.time()
    n = len(X)
    best_f1, final = 0.0, {}
    for ep in range(1, args.epochs + 1):
        model.train()
        perm = torch.randperm(n, device=device)
        for i in range(0, n, args.batch):
            idx = perm[i:i + args.batch]
            opt.zero_grad()
            crit(model(X[idx]), y[idx]).backward()
            opt.step()
        m = evaluate(model, X_te, y_te, device)
        best_f1 = max(best_f1, m["f1"])
        final = m
    summary = dict(run_name="centralized_s%d_rev1" % args.seed,
                   config=vars(args), final=final, best_f1=best_f1,
                   wall_sec=time.time() - t0)
    out = os.path.join(os.path.abspath(args.out_dir), summary["run_name"] + "_summary.json")
    json.dump(summary, open(out, "w"), indent=1)
    print("DONE centralized s%d | final f1=%.4f best=%.4f auc=%.4f | %.1fs"
          % (args.seed, final["f1"], best_f1, final["auc"], summary["wall_sec"]))

if __name__ == "__main__":
    main()
