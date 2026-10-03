#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""补跑 β/α 扫描的 v5 数据（NaN 防护代码）。

β sweep: 4 方法 × β{0.1,0.2,0.4} × seeds{42,43,44} = 36 runs (sybil, α=0.5)
α sweep: 4 方法 × α{0.1,1.0} × seeds{42,43,44} = 24 runs (sybil, β=0.3)
共 60 runs, tag=v5。β=0.3 与 α=0.5 的点直接复用主表已有 v5 数据。
"""
import os
import sys
import subprocess
import argparse

METHODS = ["fedrbc", "raid", "fedgt", "eiffel"]
SEEDS = [42, 43, 44]
BETAS = ["0.1", "0.2", "0.4"]          # β sweep（β=0.3 复用主表）
ALPHAS = ["0.1", "1.0"]                # α sweep（α=0.5 复用主表）


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gpu", type=int, default=0)
    ap.add_argument("--shard", type=int, default=0)
    ap.add_argument("--nshards", type=int, default=1)
    a = ap.parse_args()

    here = os.path.dirname(os.path.abspath(__file__))
    py = sys.executable
    jobs = []
    # β sweep
    for b in BETAS:
        for m in METHODS:
            for s in SEEDS:
                extra = ["--tau-rel", "2.0", "--z-thresh", "2.0", "--soft-T", "0.3"] if m == "fedrbc" else []
                jobs.append((m, "0.5", b, "sybil", s, extra))
    # α sweep
    for al in ALPHAS:
        for m in METHODS:
            for s in SEEDS:
                extra = ["--tau-rel", "2.0", "--z-thresh", "2.0", "--soft-T", "0.3"] if m == "fedrbc" else []
                jobs.append((m, al, "0.3", "sybil", s, extra))

    my = [j for i, j in enumerate(jobs) if i % a.nshards == a.shard]
    print("[sweep-v5] shard %d/%d: %d jobs" % (a.shard, a.nshards, len(my)), flush=True)
    for k, (m, al, b, atk, s, extra) in enumerate(my):
        cmd = [py, os.path.join(here, "run_fl.py"),
               "--method", m, "--alpha", al, "--beta", b,
               "--attack", atk, "--seed", str(s),
               "--gpu", str(a.gpu), "--tag", "v5"] + extra
        print("[sweep-v5] (%d/%d) %s" % (k + 1, len(my), " ".join(cmd[2:])), flush=True)
        r = subprocess.run(cmd)
        if r.returncode != 0:
            print("[sweep-v5] FAILED %s a%s b%s s%s" % (m, al, b, s), flush=True)
    print("[sweep-v5] shard %d done" % a.shard, flush=True)


if __name__ == "__main__":
    main()
