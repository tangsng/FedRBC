#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FedRBC v2 重跑（相对裁剪 tau_rel=κ，Eq. 7 修订版），tag=v2。
范围：原仿真矩阵中全部 fedrbc runs（31 个）。
"""
import os, sys, subprocess, argparse

SEEDS = [42, 43, 44]
ATTACKS = ["scaling", "sign_flip", "sybil", "noise"]

def build_jobs(tau_rel):
    jobs = []
    def add(alpha, beta, attack, seed, tag="v2"):
        jobs.append(dict(alpha=alpha, beta=beta, attack=attack, seed=seed, tag=tag))
    for atk in ATTACKS:
        for s in SEEDS:
            add(0.5, 0.3, atk, s)
    for s in SEEDS:
        add(0.5, 0.0, "none", s)
    for a in (0.1, 1.0):
        for s in SEEDS:
            add(a, 0.3, "sybil", s)
    for b in (0.1, 0.2, 0.4):
        for s in SEEDS:
            add(0.5, b, "sybil", s)
    jobs.append(dict(alpha=0.5, beta=0.3, attack="sybil", seed=42, tag="v2repdyn"))
    return jobs

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gpu", type=int, default=0)
    ap.add_argument("--shard", type=int, default=0)
    ap.add_argument("--nshards", type=int, default=1)
    ap.add_argument("--tau-rel", type=float, default=2.0)
    args = ap.parse_args()

    here = os.path.dirname(os.path.abspath(__file__))
    py = sys.executable
    jobs = build_jobs(args.tau_rel)
    my_jobs = [j for i, j in enumerate(jobs) if i % args.nshards == args.shard]
    print("[fedrbc-v2] shard %d/%d: %d jobs (tau_rel=%.1f)" %
          (args.shard, args.nshards, len(my_jobs), args.tau_rel))
    for k, job in enumerate(my_jobs):
        cmd = [py, os.path.join(here, "run_fl.py"),
               "--method", "fedrbc", "--alpha", str(job["alpha"]),
               "--beta", str(job["beta"]), "--attack", job["attack"],
               "--seed", str(job["seed"]), "--gpu", str(args.gpu),
               "--tau-rel", str(args.tau_rel), "--tag", job["tag"]]
        print("[fedrbc-v2] (%d/%d) %s" % (k + 1, len(my_jobs), " ".join(cmd[2:])))
        r = subprocess.run(cmd)
        if r.returncode != 0:
            print("[fedrbc-v2] ⚠️ FAILED: %s" % job)
    print("[fedrbc-v2] shard %d 完成" % args.shard)

if __name__ == "__main__":
    main()
