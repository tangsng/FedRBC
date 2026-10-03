#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""最终修订实验：带 NaN 防护的 fedrbc 重跑（M2 根因修复 = 数值稳定性）。

重跑 fedrbc 主表 3 攻击 × seed{42..46} + no-attack × seed{42..46}，tag=v4final。
（RAID/FedGT/EIFFeL 无需重跑，它们已用 bl tag 有 seed 45/46 结果。）
"""
import os, sys, subprocess, argparse

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gpu", type=int, default=0)
    ap.add_argument("--shard", type=int, default=0)
    ap.add_argument("--nshards", type=int, default=1)
    a = ap.parse_args()
    here = os.path.dirname(os.path.abspath(__file__))
    py = sys.executable

    jobs = []
    # 主表 3 攻击 × 5 seeds
    for atk in ("sign_flip", "sybil", "label_flip"):
        for s in (42, 43, 44, 45, 46):
            jobs.append(("fedrbc", "0.5", "0.3", atk, s, "v4final",
                         ["--tau-rel", "2.0", "--z-thresh", "2.0", "--soft-T", "0.3"]))
    # no-attack 5 seeds
    for s in (42, 43, 44, 45, 46):
        jobs.append(("fedrbc", "0.5", "0.0", "none", s, "v4final",
                     ["--tau-rel", "2.0", "--z-thresh", "2.0", "--soft-T", "0.3"]))

    my = [j for i, j in enumerate(jobs) if i % a.nshards == a.shard]
    print("[v4final] shard %d/%d: %d jobs on GPU %d" % (a.shard, a.nshards, len(my), a.gpu))
    for k, (m, al, b, atk, s, tag, extra) in enumerate(my):
        cmd = [py, os.path.join(here, "run_fl.py"), "--method", m,
               "--alpha", al, "--beta", b, "--attack", atk, "--seed", str(s),
               "--gpu", str(a.gpu), "--tag", tag] + extra
        print("[v4final] (%d/%d) %s" % (k + 1, len(my), " ".join(cmd[2:])))
        r = subprocess.run(cmd)
        if r.returncode != 0:
            print("[v4final] FAILED: %s %s s%s" % (m, atk, s))
    print("[v4final] shard %d 完成" % a.shard)

if __name__ == "__main__":
    main()
