#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
M9 统计显著性检验：FedRBC vs 各基线，配对 t 检验 + Cohen's d 效应量。
口径：final-round F1，seed 配对（同一 seed 同一攻击下对比），ddof=1。
"""
import json, glob, math, statistics as st
from scipy import stats

T = {"fedrbc": ["v4final"], "raid": ["bl"], "fedgt": ["bl"], "eiffel": ["bl"]}
ATTACKS = ["sign_flip", "sybil", "label_flip"]

def f1_by_seed(method, attack, tags):
    fs = [f for f in glob.glob("results/raw/%s_a0.5_b0.3_%s_s*_summary.json" % (method, attack))]
    fs = [f for f in fs if json.load(open(f))["config"].get("tag", "") in tags]
    out = {}
    for f in fs:
        d = json.load(open(f))
        v = d["final"]["f1"]
        if v == v:  # 非 nan
            out[d["config"]["seed"]] = v
    return out

def cohens_d(paired_diffs):
    if len(paired_diffs) < 2:
        return float("nan")
    return st.mean(paired_diffs) / (st.stdev(paired_diffs) if st.stdev(paired_diffs) > 0 else 1e-12)

print("=== FedRBC vs 基线 配对检验（final F1）===")
for atk in ATTACKS:
    print("\n[%s]" % atk)
    base = f1_by_seed("fedrbc", atk, T["fedrbc"])
    for m in ("raid", "fedgt", "eiffel"):
        other = f1_by_seed(m, atk, T[m])
        common = sorted(set(base) & set(other))
        if len(common) < 2:
            print("  vs %-7s: 配对 seed 不足 (n=%d)" % (m, len(common)))
            continue
        diffs = [base[s] - other[s] for s in common]
        t, p = stats.ttest_rel([base[s] for s in common], [other[s] for s in common])
        d = cohens_d(diffs)
        print("  vs %-7s: n=%d  mean_diff=%+.3f  t=%.2f  p=%.4f  Cohen's d=%+.2f  %s"
              % (m, len(common), st.mean(diffs), t, p, d,
                 "显著(p<0.05)" if p < 0.05 else "不显著"))
