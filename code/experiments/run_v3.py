#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v3 补跑：violation 版（相对裁剪+幅度违规惩罚分支），tag=v3。
范围：scaling / noise / none 对照，各 3 seeds；scaling 加 κ=2.0 备选。"""
import os, sys, subprocess, argparse

SEEDS = [42, 43, 44]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gpu", type=int, default=0)
    ap.add_argument("--shard", type=int, default=0)
    ap.add_argument("--nshards", type=int, default=1)
    args = ap.parse_args()
    here = os.path.dirname(os.path.abspath(__file__))
    py = sys.executable

    jobs = []
    for s in SEEDS:
        jobs.append(dict(attack="scaling", seed=s, tau_rel=1.5, tag="v3"))
        jobs.append(dict(attack="noise", seed=s, tau_rel=1.5, tag="v3"))
        jobs.append(dict(attack="none", seed=s, tau_rel=1.5, tag="v3"))
        jobs.append(dict(attack="scaling", seed=s, tau_rel=2.0, tag="v3k2"))
    my = [j for i, j in enumerate(jobs) if i % args.nshards == args.shard]
    print("[v3] shard %d/%d: %d jobs" % (args.shard, args.nshards, len(my)))
    for k, j in enumerate(my):
        b = 0.3 if j["attack"] != "none" else 0.0
        cmd = [py, os.path.join(here, "run_fl.py"), "--method", "fedrbc",
               "--alpha", "0.5", "--beta", str(b), "--attack", j["attack"],
               "--seed", str(j["seed"]), "--gpu", str(args.gpu),
               "--tau-rel", str(j["tau_rel"]), "--tag", j["tag"]]
        print("[v3] (%d/%d) %s" % (k + 1, len(my), " ".join(cmd[2:])))
        r = subprocess.run(cmd)
        if r.returncode != 0:
            print("[v3] FAILED: %s" % j)
    print("[v3] shard %d 完成" % args.shard)

if __name__ == "__main__":
    main()
