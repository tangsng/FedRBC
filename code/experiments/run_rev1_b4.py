#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Round-1 batch 4：§5.7 边界场景数据的修复后管线重跑（scaling + noise）。
正文原数字来自 v7（NaN 修复前存档），与"all numbers from the fixed pipeline"声明矛盾。
{fedrbc, fltrust, fedgt, eiffel} × {scaling, noise} × 3 seeds = 24，tag rev1。"""
import os, sys, subprocess, argparse

SEEDS3 = [42, 43, 44]
FEDRBC = ["--tau-rel", "2.0", "--z-thresh", "2.0", "--soft-T", "0.3"]


def build_jobs():
    jobs = []
    for m in ["fedrbc", "fltrust", "fedgt", "eiffel"]:
        for atk in ["scaling", "noise"]:
            for s in SEEDS3:
                extra = (FEDRBC if m == "fedrbc" else [])
                jobs.append((m, atk, s, extra))
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
    print("[rev1-b4] shard %d/%d: %d jobs" % (a.shard, a.nshards, len(my)), flush=True)
    for k, (m, atk, s, extra) in enumerate(my):
        cmd = [py, os.path.join(here, "run_fl.py"), "--method", m,
               "--alpha", "0.5", "--beta", "0.3", "--attack", atk,
               "--seed", str(s), "--gpu", str(a.gpu), "--tag", "rev1"] + extra
        print("[rev1-b4] (%d/%d) %s" % (k + 1, len(my), " ".join(cmd[2:])), flush=True)
        r = subprocess.run(cmd)
        if r.returncode != 0:
            print("[rev1-b4] FAILED %s %s s%s" % (m, atk, s), flush=True)
    print("[rev1-b4] shard %d done" % a.shard, flush=True)


if __name__ == "__main__":
    main()
