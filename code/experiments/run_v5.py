#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""最终干净重跑：全局 NaN 防护下，4 方法 × 3 攻击 × 5 seeds 主表 + no-attack。
tag=v5。这是投稿用的最终数据（修复了 NaN 后期崩溃的数值稳定性 bug）。"""
import os, sys, subprocess, argparse

METHODS = ["fedrbc", "raid", "fedgt", "eiffel"]
ATTACKS = ["sign_flip", "sybil", "label_flip"]
SEEDS = [42, 43, 44, 45, 46]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gpu", type=int, default=0)
    ap.add_argument("--shard", type=int, default=0)
    ap.add_argument("--nshards", type=int, default=1)
    a = ap.parse_args()
    here = os.path.dirname(os.path.abspath(__file__))
    py = sys.executable

    jobs = []
    for atk in ATTACKS:
        for m in METHODS:
            for s in SEEDS:
                extra = ["--tau-rel", "2.0", "--z-thresh", "2.0", "--soft-T", "0.3"] if m == "fedrbc" else []
                jobs.append((m, "0.5", "0.3", atk, s, "v5", extra))
    # no-attack（5 seeds，4 方法）
    for m in METHODS:
        for s in SEEDS:
            extra = ["--tau-rel", "2.0", "--z-thresh", "2.0", "--soft-T", "0.3"] if m == "fedrbc" else []
            jobs.append((m, "0.5", "0.0", "none", s, "v5", extra))

    my = [j for i, j in enumerate(jobs) if i % a.nshards == a.shard]
    print("[v5] shard %d/%d: %d jobs on GPU %d" % (a.shard, a.nshards, len(my), a.gpu))
    for k, (m, al, b, atk, s, tag, extra) in enumerate(my):
        cmd = [py, os.path.join(here, "run_fl.py"), "--method", m,
               "--alpha", al, "--beta", b, "--attack", atk, "--seed", str(s),
               "--gpu", str(a.gpu), "--tag", tag] + extra
        print("[v5] (%d/%d) %s" % (k + 1, len(my), " ".join(cmd[2:])))
        r = subprocess.run(cmd)
        if r.returncode != 0:
            print("[v5] FAILED: %s %s s%s" % (m, atk, s))
    print("[v5] shard %d 完成" % a.shard)

if __name__ == "__main__":
    main()
