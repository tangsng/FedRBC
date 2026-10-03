#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实验矩阵批量驱动：按 GPU 分片执行（Phase 1 §5 实验矩阵，~104 runs）。
用法：
  python run_matrix.py --gpu 0 --shard 0 --nshards 2   # GPU0 跑一半
  python run_matrix.py --gpu 1 --shard 1 --nshards 2   # GPU1 跑另一半
  python run_matrix.py --list                          # 仅列出全部实验
"""
import os, sys, subprocess, argparse, itertools, json

SEEDS = [42, 43, 44]
MAIN_METHODS = ["fedavg", "fedprox", "krum", "trimmed_mean", "fltrust", "fedrbc"]
ROB_METHODS = ["fedavg", "krum", "fltrust", "fedrbc"]

def build_matrix():
    """返回实验配置列表，每项为 run_fl.py 的参数字典。"""
    jobs = []
    def add(method, alpha, beta, attack, seed, tag=""):
        jobs.append(dict(method=method, alpha=alpha, beta=beta, attack=attack,
                         seed=seed, tag=tag))
    # EXP-MAIN: 6 方法 x label_flip 20% x a=0.5 x 3 seeds
    for m in MAIN_METHODS:
        for s in SEEDS:
            add(m, 0.5, 0.2, "label_flip", s)
    # EXP-CLEAN: 6 方法 x 无攻击 x a=0.5 x 3 seeds
    for m in MAIN_METHODS:
        for s in SEEDS:
            add(m, 0.5, 0.0, "none", s)
    # EXP-ROBUST: 4 方法 x {10,30}% x a=0.5 x 3 seeds
    for m in ROB_METHODS:
        for b in (0.1, 0.3):
            for s in SEEDS:
                add(m, 0.5, b, "label_flip", s)
    # EXP-NONIID: 4 方法 x a {0.1,1.0} x 20% x 3 seeds
    for m in ROB_METHODS:
        for a in (0.1, 1.0):
            for s in SEEDS:
                add(m, a, 0.2, "label_flip", s)
    # EXP-ABLATION: FedRBC 变体 x 3 seeds
    for s in SEEDS:
        jobs.append(dict(method="fedrbc", alpha=0.5, beta=0.2, attack="label_flip",
                         seed=s, tag="abl_norep", extra=["--no-rep-weight"]))
        jobs.append(dict(method="fedrbc", alpha=0.5, beta=0.2, attack="label_flip",
                         seed=s, tag="abl_randsel", extra=["--selection", "random"]))
        jobs.append(dict(method="fedrbc", alpha=0.5, beta=0.2, attack="label_flip",
                         seed=s, tag="abl_nodecay", extra=["--no-decay", "--no-penalty"]))
    # EXP-REPDYN: FedRBC 单 seed（声誉历史落盘供 Fig 2）
    jobs.append(dict(method="fedrbc", alpha=0.5, beta=0.2, attack="label_flip",
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
    cmd += job.get("extra", [])
    return cmd

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gpu", type=int, default=0)
    ap.add_argument("--shard", type=int, default=0)
    ap.add_argument("--nshards", type=int, default=1)
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--rounds", type=int, default=None, help="覆盖默认轮数（冒烟用）")
    args = ap.parse_args()

    jobs = build_matrix()
    if args.list:
        print("共 %d 个实验" % len(jobs))
        for i, j in enumerate(jobs):
            print(i, j)
        return
    my_jobs = [j for i, j in enumerate(jobs) if i % args.nshards == args.shard]
    print("[matrix] shard %d/%d: %d jobs on GPU %d" % (args.shard, args.nshards, len(my_jobs), args.gpu))
    fails = []
    for k, job in enumerate(my_jobs):
        cmd = job_cmd(job, args.gpu)
        if args.rounds:
            cmd += ["--rounds", str(args.rounds)]
        print("[matrix] (%d/%d) %s" % (k + 1, len(my_jobs), " ".join(cmd[2:])))
        r = subprocess.run(cmd)
        if r.returncode != 0:
            fails.append(job)
            print("[matrix] ⚠️ FAILED: %s" % job)
    print("[matrix] shard %d 完成，失败 %d" % (args.shard, len(fails)))
    if fails:
        sys.exit(1)

if __name__ == "__main__":
    main()
