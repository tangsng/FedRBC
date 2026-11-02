#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Round-1 revision, batch 2：需新代码的补充实验（全部 wustl）。

① DP 组合（R2/R1.10）：{fedrbc, fltrust, eiffel, fedavg} × {sybil, sign_flip}
   × sigma ∈ {0.005, 0.02, 0.1} × 3 seeds = 72，tag rev1_dp<sig>
② LIE 攻击（R2.3）：{fedrbc, fltrust, eiffel, fedavg} × 5 seeds = 20，tag rev1_lie
③ backdoor + ASR（R2.3）：{fedrbc, fltrust, fedavg} × 3 seeds = 9，tag rev1_bd
④ root-set poisoning（R2.3）：{fedrbc, fltrust} × {sybil, sign_flip}
   × eps ∈ {0.1, 0.2, 0.3} × 3 seeds = 36，tag rev1_rp<eps>
⑤ 无跨轮记忆消融（R1.13）：fedrbc × 3 攻击 × 3 seeds = 9，tag rev1_abmemory
⑥ 敏感性（R1.5）：fedrbc sybil × {soft-T 0.1/0.5, tau-rel 1/3, theta-h 0.1/0.5,
   K 6/14, root 100/300} × 3 seeds = 30，tag rev1_sens_<name>
⑦ client scaling（R2.4）：N ∈ {50, 100} × {fedrbc, fltrust, fedavg} × 3 seeds = 18，
   tag rev1_n<N>
⑧ FLTrust 扩 seeds 47-51（与主表 10-seed 对齐）：3 攻击 × 5 = 15，tag rev1
⑨ 集中式上界（R2.1）：seeds 42-46 = 5（run_centralized.py）
"""
import os, sys, subprocess, argparse

SEEDS3 = [42, 43, 44]
SEEDS5 = [42, 43, 44, 45, 46]
SEEDS_NEW = [47, 48, 49, 50, 51]
ATTACKS = ["sign_flip", "sybil", "label_flip"]
FEDRBC = ["--tau-rel", "2.0", "--z-thresh", "2.0", "--soft-T", "0.3"]

SENS = {
    "softT01": ["--tau-rel", "2.0", "--z-thresh", "2.0", "--soft-T", "0.1"],
    "softT05": ["--tau-rel", "2.0", "--z-thresh", "2.0", "--soft-T", "0.5"],
    "taurel10": ["--tau-rel", "1.0", "--z-thresh", "2.0", "--soft-T", "0.3"],
    "taurel30": ["--tau-rel", "3.0", "--z-thresh", "2.0", "--soft-T", "0.3"],
    "thh01": ["--tau-rel", "2.0", "--z-thresh", "2.0", "--soft-T", "0.3", "--theta-h", "0.1"],
    "thh05": ["--tau-rel", "2.0", "--z-thresh", "2.0", "--soft-T", "0.3", "--theta-h", "0.5"],
    "k06": ["--tau-rel", "2.0", "--z-thresh", "2.0", "--soft-T", "0.3", "--k-per-round", "6"],
    "k14": ["--tau-rel", "2.0", "--z-thresh", "2.0", "--soft-T", "0.3", "--k-per-round", "14"],
    "root100": ["--tau-rel", "2.0", "--z-thresh", "2.0", "--soft-T", "0.3", "--root-size", "100"],
    "root300": ["--tau-rel", "2.0", "--z-thresh", "2.0", "--soft-T", "0.3", "--root-size", "300"],
}


def build_jobs():
    jobs = []  # (method, atk, seed, extra, tag)  atk="none" 表示 centralized
    # ① DP
    for m in ["fedrbc", "fltrust", "eiffel", "fedavg"]:
        for atk in ["sybil", "sign_flip"]:
            for sig in ["0.005", "0.02", "0.1"]:
                for s in SEEDS3:
                    extra = (FEDRBC if m == "fedrbc" else []) + ["--dp-sigma", sig]
                    jobs.append((m, atk, s, extra, "rev1_dp" + sig.replace(".", "")))
    # ② LIE
    for m in ["fedrbc", "fltrust", "eiffel", "fedavg"]:
        for s in SEEDS5:
            extra = (FEDRBC if m == "fedrbc" else []) + ["--attack", "lie"]
            jobs.append((m, "lie", s, extra, "rev1_lie"))
    # ③ backdoor
    for m in ["fedrbc", "fltrust", "fedavg"]:
        for s in SEEDS3:
            extra = (FEDRBC if m == "fedrbc" else []) + ["--attack", "backdoor"]
            jobs.append((m, "backdoor", s, extra, "rev1_bd"))
    # ④ root poisoning
    for m in ["fedrbc", "fltrust"]:
        for atk in ["sybil", "sign_flip"]:
            for eps in ["0.1", "0.2", "0.3"]:
                for s in SEEDS3:
                    extra = (FEDRBC if m == "fedrbc" else []) + ["--root-poison", eps]
                    jobs.append((m, atk, s, extra, "rev1_rp" + eps.replace(".", "")))
    # ⑤ no-memory
    for atk in ATTACKS:
        for s in SEEDS3:
            jobs.append(("fedrbc", atk, s, FEDRBC + ["--no-memory"], "rev1_abmemory"))
    # ⑥ 敏感性（sybil）
    for name, extra in SENS.items():
        for s in SEEDS3:
            jobs.append(("fedrbc", "sybil", s, extra, "rev1_sens_" + name))
    # ⑦ client scaling
    for N in [50, 100]:
        for m in ["fedrbc", "fltrust", "fedavg"]:
            for s in SEEDS3:
                extra = (FEDRBC if m == "fedrbc" else []) + ["--n-clients", str(N)]
                jobs.append((m, "sybil", s, extra, "rev1_n%d" % N))
    # ⑧ FLTrust 扩 seeds
    for atk in ATTACKS:
        for s in SEEDS_NEW:
            jobs.append(("fltrust", atk, s, [], "rev1"))
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
    print("[rev1-b2] shard %d/%d: %d jobs" % (a.shard, a.nshards, len(my)), flush=True)
    for k, (m, atk, s, extra, tag) in enumerate(my):
        cmd = [py, os.path.join(here, "run_fl.py"), "--method", m,
               "--alpha", "0.5", "--beta", "0.3", "--attack", atk,
               "--seed", str(s), "--gpu", str(a.gpu), "--tag", tag] + extra
        print("[rev1-b2] (%d/%d) %s" % (k + 1, len(my), " ".join(cmd[2:])), flush=True)
        r = subprocess.run(cmd)
        if r.returncode != 0:
            print("[rev1-b2] FAILED %s %s s%s tag=%s" % (m, atk, s, tag), flush=True)
    print("[rev1-b2] shard %d done" % a.shard, flush=True)


if __name__ == "__main__":
    main()
