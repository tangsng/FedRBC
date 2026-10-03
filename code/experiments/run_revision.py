#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""评审修订实验矩阵（M2/M9/M10 三合一），tag 统一用 v4fix。

M2  T_s 退火修复验证：fedrbc no-attack 三 seed（soft-T 0.3 + soft-T-anneal 2.0）
M9  扩 seed：主表 3 攻击 × 4 方法 × seed{45,46}（增量，42-44 已有）
M10 第二数据集：ciciot 主表 3 攻击 × 4 方法 × seed{42,43,44}

用法：python run_revision.py --gpu 0 --shard 0 --nshards 2 --task all
"""
import os, sys, subprocess, argparse

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gpu", type=int, default=0)
    ap.add_argument("--shard", type=int, default=0)
    ap.add_argument("--nshards", type=int, default=1)
    ap.add_argument("--task", choices=["m2", "m9", "m10", "all"], default="all")
    a = ap.parse_args()
    here = os.path.dirname(os.path.abspath(__file__))
    py = sys.executable

    jobs = []  # (method, alpha, beta, attack, seed, tag, dataset, extra_args)

    def fedrbc_defaults():
        return ["--tau-rel", "2.0", "--z-thresh", "2.0", "--soft-T", "0.3"]

    if a.task in ("m2", "all"):
        # T_s 退火：no-attack 三 seed，验证 seed-43 不再崩溃
        for s in (42, 43, 44):
            jobs.append(("fedrbc", "0.5", "0.0", "none", s, "v4anneal", "wustl",
                         fedrbc_defaults() + ["--soft-T-anneal", "2.0"]))

    if a.task in ("m9", "all"):
        # 扩 seed 主表：新 seed 45,46 × 3 攻击 × 4 方法
        for atk in ("sign_flip", "sybil", "label_flip"):
            for m in ("fedrbc", "raid", "fedgt", "eiffel"):
                for s in (45, 46):
                    if m == "fedrbc":
                        extra = fedrbc_defaults()
                    else:
                        extra = []
                    jobs.append((m, "0.5", "0.3", atk, s, "bl", "wustl", extra))

    if a.task in ("m10", "all"):
        # 第二数据集主表：3 攻击 × 4 方法 × seed{42,43,44}
        for atk in ("sign_flip", "sybil", "label_flip"):
            for m in ("fedrbc", "raid", "fedgt", "eiffel"):
                for s in (42, 43, 44):
                    if m == "fedrbc":
                        extra = fedrbc_defaults()
                    else:
                        extra = []
                    jobs.append((m, "0.5", "0.3", atk, s, "bl", "ciciot", extra))

    my = [j for i, j in enumerate(jobs) if i % a.nshards == a.shard]
    print("[revision] task=%s shard %d/%d: %d jobs on GPU %d" %
          (a.task, a.shard, a.nshards, len(my), a.gpu))
    for k, (m, al, b, atk, s, tag, ds, extra) in enumerate(my):
        cmd = [py, os.path.join(here, "run_fl.py"), "--method", m,
               "--alpha", al, "--beta", b, "--attack", atk, "--seed", str(s),
               "--gpu", str(a.gpu), "--tag", tag, "--dataset", ds] + extra
        print("[revision] (%d/%d) %s" % (k + 1, len(my), " ".join(cmd[2:])))
        r = subprocess.run(cmd)
        if r.returncode != 0:
            print("[revision] FAILED: %s %s %s s%s" % (m, atk, ds, s))
    print("[revision] shard %d 完成 (task=%s)" % (a.shard, a.task))

if __name__ == "__main__":
    main()
