#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""只补跑 fedgt 基线（FedGT 2025），tag=bl，覆盖原矩阵 fedgreed 全部 runs。"""
import os, sys, subprocess, argparse

SEEDS = [42, 43, 44]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gpu", type=int, default=0)
    ap.add_argument("--shard", type=int, default=0)
    ap.add_argument("--nshards", type=int, default=1)
    a = ap.parse_args()
    here = os.path.dirname(os.path.abspath(__file__))
    py = sys.executable

    jobs = []
    def add(alpha, beta, attack, seed, tag="bl"):
        jobs.append(dict(alpha=alpha, beta=beta, attack=attack, seed=seed, tag=tag))
    # EXP-1 主表（4 攻击 × 3 seeds）
    for atk in ("scaling", "sign_flip", "sybil", "noise"):
        for s in SEEDS:
            add(0.5, 0.3, atk, s)
    # EXP-2 无攻击
    for s in SEEDS:
        add(0.5, 0.0, "none", s)
    # EXP-3 Non-IID（sybil）
    for al in (0.1, 1.0):
        for s in SEEDS:
            add(al, 0.3, "sybil", s)
    # EXP-4 β 扫描（sybil）
    for b in (0.1, 0.2, 0.4):
        for s in SEEDS:
            add(0.5, b, "sybil", s)

    my = [j for i, j in enumerate(jobs) if i % a.nshards == a.shard]
    print("[fedgreed] shard %d/%d: %d jobs on GPU %d" % (a.shard, a.nshards, len(my), a.gpu))
    for k, j in enumerate(my):
        cmd = [py, os.path.join(here, "run_fl.py"), "--method", "fedgt",
               "--alpha", str(j["alpha"]), "--beta", str(j["beta"]),
               "--attack", j["attack"], "--seed", str(j["seed"]),
               "--gpu", str(a.gpu), "--tag", j["tag"]]
        print("[fedgreed] (%d/%d) %s" % (k + 1, len(my), " ".join(cmd[2:])))
        r = subprocess.run(cmd)
        if r.returncode != 0:
            print("[fedgreed] FAILED: %s" % j)
    print("[fedgreed] shard %d 完成" % a.shard)

if __name__ == "__main__":
    main()
