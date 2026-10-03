#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
改进 E 验证扫描：root-对齐归一化(E1) + 声誉即时门控(E2) 的组合。
场景：s1 β=30% 高强度, s2 β=0 干净, s4 β=20% 主配置(必须守)。
配置：
  base           原版
  e1             --root-align
  e2             --rep-gate-alpha 0.5
  e12            --root-align --rep-gate-alpha 0.5
  e12b           --root-align --rep-gate-alpha 1.0
每配置 3 seeds。
"""
import os, sys, subprocess, argparse

SEEDS = [42, 43, 44]
SCENES = [("s1_b30", 0.5, 0.3), ("s2_clean", 0.5, 0.0), ("s4_b20", 0.5, 0.2)]
CONFIGS = [
    ("base", []),
    ("e1", ["--root-align"]),
    ("e2", ["--rep-gate-alpha", "0.5"]),
    ("e12", ["--root-align", "--rep-gate-alpha", "0.5"]),
    ("e12b", ["--root-align", "--rep-gate-alpha", "1.0"]),
]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gpu", type=int, default=0)
    ap.add_argument("--shard", type=int, default=0)
    ap.add_argument("--nshards", type=int, default=1)
    args = ap.parse_args()

    here = os.path.dirname(os.path.abspath(__file__))
    py = sys.executable
    jobs = []
    for (name, a, b) in SCENES:
        for (cfgtag, extra) in CONFIGS:
            for s in SEEDS:
                tag = "e_%s_%s" % (cfgtag, name)
                cmd = [py, os.path.join(here, "run_fl.py"),
                       "--method", "fedrbc", "--alpha", str(a), "--beta", str(b),
                       "--attack", ("label_flip" if b > 0 else "none"),
                       "--seed", str(s), "--gpu", str(args.gpu),
                       "--tag", tag] + extra
                jobs.append(cmd)

    my_jobs = [j for i, j in enumerate(jobs) if i % args.nshards == args.shard]
    print("[e-scan] shard %d/%d: %d jobs on GPU %d" %
          (args.shard, args.nshards, len(my_jobs), args.gpu))
    for k, cmd in enumerate(my_jobs):
        print("[e-scan] (%d/%d) %s" % (k + 1, len(my_jobs), " ".join(cmd[2:])))
        r = subprocess.run(cmd)
        if r.returncode != 0:
            print("[e-scan] ⚠️ FAILED: %s" % " ".join(cmd[2:]))
    print("[e-scan] shard %d 完成" % args.shard)

if __name__ == "__main__":
    main()
