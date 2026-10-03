#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v4 验证：median 参照裁剪 + q 排除违规者，tag=v4。
范围：scaling/none/noise(σ=1.0/2.5)/sign_flip/sybil 各 3 seeds。"""
import os, sys, subprocess, argparse

SEEDS = [42, 43, 44]
JOBS = [
    dict(attack="scaling", beta=0.3, noise_sigma=1.0),
    dict(attack="none", beta=0.0, noise_sigma=1.0),
    dict(attack="noise", beta=0.3, noise_sigma=1.0),
    dict(attack="noise", beta=0.3, noise_sigma=2.5, tag_suffix="_ns25"),
    dict(attack="sign_flip", beta=0.3, noise_sigma=1.0),
    dict(attack="sybil", beta=0.3, noise_sigma=1.0),
]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gpu", type=int, default=0)
    ap.add_argument("--shard", type=int, default=0)
    ap.add_argument("--nshards", type=int, default=1)
    ap.add_argument("--tau-rel", type=float, default=2.0)
    args = ap.parse_args()
    here = os.path.dirname(os.path.abspath(__file__))
    py = sys.executable

    jobs = []
    for j in JOBS:
        for s in SEEDS:
            jobs.append((j, s))
    my = [x for i, x in enumerate(jobs) if i % args.nshards == args.shard]
    print("[v4] shard %d/%d: %d jobs (tau_rel=%.1f)" % (args.shard, args.nshards, len(my), args.tau_rel))
    for k, (j, s) in enumerate(my):
        tag = "v4" + j.get("tag_suffix", "")
        cmd = [py, os.path.join(here, "run_fl.py"), "--method", "fedrbc",
               "--alpha", "0.5", "--beta", str(j["beta"]), "--attack", j["attack"],
               "--seed", str(s), "--gpu", str(args.gpu),
               "--tau-rel", str(args.tau_rel),
               "--noise-sigma", str(j["noise_sigma"]), "--tag", tag]
        print("[v4] (%d/%d) %s" % (k + 1, len(my), " ".join(cmd[2:])))
        r = subprocess.run(cmd)
        if r.returncode != 0:
            print("[v4] FAILED: %s %s" % (j, s))
    print("[v4] shard %d 完成" % args.shard)

if __name__ == "__main__":
    main()
