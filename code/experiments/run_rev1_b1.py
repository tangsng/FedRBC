#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Round-1 revision, batch 1: 无需新代码的补充实验。

① 经典鲁棒基线（R2.2）：fltrust / krum / trimmed_mean × 3 攻击 × 5 seeds = 45
② 主表扩 seeds（R1.6）：4 方法 × 3 攻击 × seeds 47-51 = 60
③ 无攻击上界（R2.1）：fedavg no-attack × 5 seeds = 5
④ 组件消融（R1.13/R2.4）：fedrbc 去{方向门控/裁剪/Layer0/声誉加权/选择}
   × 3 攻击 × 3 seeds = 45
tag = rev1
"""
import os
import sys
import subprocess
import argparse

ATTACKS = ["sign_flip", "sybil", "label_flip"]
SEEDS5 = [42, 43, 44, 45, 46]
SEEDS_NEW = [47, 48, 49, 50, 51]
SEEDS3 = [42, 43, 44]
FEDRBC = ["--tau-rel", "2.0", "--z-thresh", "2.0", "--soft-T", "0.3"]

ABLATIONS = {
    # 完整版去掉单一组件；gate 消融需退回 ReLU 模式（不给 soft-T）且 gate-p=0
    "ab_gate":   ["--tau-rel", "2.0", "--z-thresh", "2.0", "--gate-p", "0"],
    "ab_clip":   ["--z-thresh", "2.0", "--soft-T", "0.3"],
    "ab_layer0": ["--tau-rel", "2.0", "--soft-T", "0.3"],
    "ab_repw":   FEDRBC + ["--no-rep-weight"],
    "ab_select": FEDRBC + ["--selection", "random"],
}


def jobs_all():
    jobs = []
    # ① 经典基线
    for m in ["fltrust", "krum", "trimmed_mean"]:
        for atk in ATTACKS:
            for s in SEEDS5:
                jobs.append((m, atk, s, []))
    # ② 主表扩 seeds
    for m in ["fedrbc", "raid", "fedgt", "eiffel"]:
        for atk in ATTACKS:
            for s in SEEDS_NEW:
                extra = FEDRBC if m == "fedrbc" else []
                jobs.append((m, atk, s, extra))
    # ③ 无攻击 fedavg 上界
    for s in SEEDS5:
        jobs.append(("fedavg", "none", s, []))
    # ④ 消融（方法名 fedrbc，组件开关区分；run_name 需要可区分 → 用 --attack 同名会冲突！）
    #    消融跑法：方法仍为 fedrbc，但 tag 不同：rev1 是统一的，文件名会覆盖！
    #    处理：消融用独立 runner 传 --tag rev1-ab-<name>，见下。
    return jobs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gpu", type=int, default=0)
    ap.add_argument("--shard", type=int, default=0)
    ap.add_argument("--nshards", type=int, default=1)
    a = ap.parse_args()
    here = os.path.dirname(os.path.abspath(__file__))
    py = sys.executable

    jobs = jobs_all()
    # ④ 消融：为避免同名覆盖，给每个消融配置独立 tag
    ab_jobs = []
    for name, extra in ABLATIONS.items():
        for atk in ATTACKS:
            for s in SEEDS3:
                ab_jobs.append(("fedrbc", atk, s, extra, "rev1-%s" % name))

    my = [j for i, j in enumerate(jobs) if i % a.nshards == a.shard]
    my_ab = [j for i, j in enumerate(ab_jobs) if i % a.nshards == a.shard]
    print("[rev1-b1] shard %d/%d: %d standard + %d ablation"
          % (a.shard, a.nshards, len(my), len(my_ab)), flush=True)

    for k, (m, atk, s, extra) in enumerate(my):
        cmd = [py, os.path.join(here, "run_fl.py"), "--method", m,
               "--alpha", "0.5", "--beta", ("0.0" if atk == "none" else "0.3"),
               "--attack", atk, "--seed", str(s), "--gpu", str(a.gpu),
               "--tag", "rev1"] + extra
        print("[rev1-b1] (%d/%d) %s" % (k + 1, len(my), " ".join(cmd[2:])), flush=True)
        r = subprocess.run(cmd)
        if r.returncode != 0:
            print("[rev1-b1] FAILED %s %s s%s" % (m, atk, s), flush=True)

    for k, (m, atk, s, extra, tag) in enumerate(my_ab):
        cmd = [py, os.path.join(here, "run_fl.py"), "--method", m,
               "--alpha", "0.5", "--beta", "0.3", "--attack", atk,
               "--seed", str(s), "--gpu", str(a.gpu), "--tag", tag] + extra
        print("[rev1-b1-ab] (%d/%d) %s" % (k + 1, len(my_ab), " ".join(cmd[2:])), flush=True)
        r = subprocess.run(cmd)
        if r.returncode != 0:
            print("[rev1-b1] FAILED ablation %s %s s%s" % (tag, atk, s), flush=True)

    print("[rev1-b1] shard %d done" % a.shard, flush=True)


if __name__ == "__main__":
    main()
