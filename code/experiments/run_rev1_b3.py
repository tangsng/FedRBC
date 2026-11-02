#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Round-1 revision, batch 3：β=0.5 极限扫描（R2.3：'the sweep stops at 40%
although the gate is claimed plurality-independent'）。

{fedrbc, fltrust, eiffel, fedavg} × {sybil, sign_flip} × β=0.5 × 3 seeds = 24，
tag rev1_b50。对照主表 β=0.3 的同配置，验证 plurality-independent 主张在
恶意占半数时的行为。
"""
import os, sys, subprocess, argparse

SEEDS3 = [42, 43, 44]
FEDRBC = ["--tau-rel", "2.0", "--z-thresh", "2.0", "--soft-T", "0.3"]


def build_jobs():
    jobs = []
    for m in ["fedrbc", "fltrust", "eiffel", "fedavg"]:
        for atk in ["sybil", "sign_flip"]:
            for s in SEEDS3:
                extra = (FEDRBC if m == "fedrbc" else [])
                jobs.append((m, atk, s, extra, "rev1_b50"))
    return jobs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gpu", type=int, default=0)
    ap.add_argument("--shard", type=int, default=0)
    ap.add_argument("--nshards", type=int, default=1)
    a = ap.parse_args()
    here = os.path.dirname(os.path.abspath(__file__))
    py = sys.executable

    jobs = build_jobs()
    my = [j for i, j in enumerate(jobs) if i % a.nshards == a.shard]
    print("[rev1-b3] shard %d/%d: %d jobs" % (a.shard, a.nshards, len(my)), flush=True)
    for k, (m, atk, s, extra, tag) in enumerate(my):
        cmd = [py, os.path.join(here, "run_fl.py"), "--method", m,
               "--alpha", "0.5", "--beta", "0.5", "--attack", atk,
               "--seed", str(s), "--gpu", str(a.gpu), "--tag", tag] + extra
        print("[rev1-b3] (%d/%d) %s" % (k + 1, len(my), " ".join(cmd[2:])), flush=True)
        r = subprocess.run(cmd)
        if r.returncode != 0:
            print("[rev1-b3] FAILED %s %s s%s tag=%s" % (m, atk, s, tag), flush=True)
    print("[rev1-b3] shard %d done" % a.shard, flush=True)


if __name__ == "__main__":
    main()
