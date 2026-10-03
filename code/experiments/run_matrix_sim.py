#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
仿真实验矩阵（论文 v2，工程应用方向，新基线对比）。
方法：FedRBC vs RAID(2026) vs FedGT(2025) vs EIFFeL(2022)
威胁模型（仿真）：scaling / sign_flip / sybil / noise（模型层攻击）
矩阵：
  EXP-1 主表: 4攻击 × 4方法 × β=0.3 × α=0.5 × 3 seeds = 48
  EXP-2 无攻击对照: 4方法 × β=0 × 3 seeds = 12
  EXP-3 Non-IID: sybil × α∈{0.1,1.0} × 4方法 × 3 seeds = 24
  EXP-4 β扫描: sybil × β∈{0.1,0.2,0.4} × 4方法 × 3 seeds = 36
  EXP-5 repdyn: fedrbc × sybil × s42 = 1
  共 121 runs
用法：
  python run_matrix_sim.py --gpu 0 --shard 0 --nshards 2
"""
import os, sys, subprocess, argparse

SEEDS = [42, 43, 44]
METHODS = ["fedrbc", "raid", "fedgt", "eiffel"]
ATTACKS = ["scaling", "sign_flip", "sybil", "noise"]

def build_matrix():
    jobs = []
    def add(method, alpha, beta, attack, seed, tag=""):
        jobs.append(dict(method=method, alpha=alpha, beta=beta, attack=attack,
                         seed=seed, tag=tag))
    # EXP-1 主表
    for atk in ATTACKS:
        for m in METHODS:
            for s in SEEDS:
                add(m, 0.5, 0.3, atk, s)
    # EXP-2 无攻击对照
    for m in METHODS:
        for s in SEEDS:
            add(m, 0.5, 0.0, "none", s)
    # EXP-3 Non-IID
    for a in (0.1, 1.0):
        for m in METHODS:
            for s in SEEDS:
                add(m, a, 0.3, "sybil", s)
    # EXP-4 β扫描
    for b in (0.1, 0.2, 0.4):
        for m in METHODS:
            for s in SEEDS:
                add(m, 0.5, b, "sybil", s)
    # EXP-5 repdyn
    jobs.append(dict(method="fedrbc", alpha=0.5, beta=0.3, attack="sybil",
                     seed=42, tag="repdyn"))
    return jobs

def job_cmd(job, gpu, py=sys.executable):
    here = os.path.dirname(os.path.abspath(__file__))
    cmd = [py, os.path.join(here, "run_fl.py"),
           "--method", job["method"],
           "--alpha", str(job["alpha"]),
           "--beta", str(job["beta"]),
           "--attack", job["attack"],
           "--seed", str(job["seed"]),
           "--gpu", str(gpu)]
    if job.get("tag"):
        cmd += ["--tag", job["tag"]]
    return cmd

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gpu", type=int, default=0)
    ap.add_argument("--shard", type=int, default=0)
    ap.add_argument("--nshards", type=int, default=1)
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--rounds", type=int, default=None)
    args = ap.parse_args()

    jobs = build_matrix()
    if args.list:
        print("共 %d 个实验" % len(jobs))
        for i, j in enumerate(jobs):
            print(i, j)
        return
    my_jobs = [j for i, j in enumerate(jobs) if i % args.nshards == args.shard]
    print("[sim-matrix] shard %d/%d: %d jobs on GPU %d" % (args.shard, args.nshards, len(my_jobs), args.gpu))
    fails = []
    for k, job in enumerate(my_jobs):
        cmd = job_cmd(job, args.gpu)
        if args.rounds:
            cmd += ["--rounds", str(args.rounds)]
        print("[sim-matrix] (%d/%d) %s" % (k + 1, len(my_jobs), " ".join(cmd[2:])))
        r = subprocess.run(cmd)
        if r.returncode != 0:
            fails.append(job)
            print("[sim-matrix] ⚠️ FAILED: %s" % job)
    print("[sim-matrix] shard %d 完成，失败 %d" % (args.shard, len(fails)))
    if fails:
        sys.exit(1)

if __name__ == "__main__":
    main()
