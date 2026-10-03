#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
v5 最终结果汇总（M9 扩 seed 后的主表 + 显著性检验 + M2 no-attack + M10 ciciot）。
输出：paper 修订所需的全部数字（供人工/脚本填入论文）。
"""
import json, glob, statistics as st
from scipy import stats

T = {"fedrbc": ["v5"], "raid": ["v5"], "fedgt": ["v5"], "eiffel": ["v5"]}
ATTACKS = ["sign_flip", "sybil", "label_flip"]

def by_seed(method, attack, beta, tags, dataset="wustl"):
    # 文件名含 dataset 时需区分；当前 run 未在文件名标注 dataset，需从 config 读
    fs = [f for f in glob.glob("results/raw/%s_a0.5_b%s_%s_s*_summary.json" % (method, beta, attack))]
    out = {}
    for f in fs:
        d = json.load(open(f))
        if d["config"].get("tag", "") in tags and d["config"].get("dataset", "wustl") == dataset:
            v = d["final"]["f1"]
            if v == v:
                out[d["config"]["seed"]] = v
    return out

def mstd(vals):
    vals = [v for v in vals if v == v]
    return (st.mean(vals), st.stdev(vals) if len(vals) > 1 else 0.0, len(vals))

print("=== 主表 wustl 5 seeds（F1/AUC/Acc）===")
for atk in ATTACKS:
    print("[%s]" % atk)
    for m in T:
        fs = [f for f in glob.glob("results/raw/%s_a0.5_b0.3_%s_s*_summary.json" % (m, atk))]
        fs = [f for f in fs if json.load(open(f))["config"].get("tag", "") in T[m]
              and json.load(open(f))["config"].get("dataset", "wustl") == "wustl"]
        for k in ("f1", "auc", "acc"):
            vals = [json.load(open(f))["final"][k] for f in fs]
            vals = [v for v in vals if v == v]
            if k == "f1":
                print("  %-8s F1=%.3f±%.3f AUC=%.3f Acc=%.3f (n=%d)" % (
                    m, st.mean(vals), st.stdev(vals) if len(vals) > 1 else 0,
                    st.mean([json.load(open(f))["final"]["auc"] for f in fs if json.load(open(f))["final"]["auc"] == json.load(open(f))["final"]["auc"]]),
                    st.mean([json.load(open(f))["final"]["acc"] for f in fs]),
                    len(vals)))
        break  # 只打一次（已在 f1 分支打完三指标）

print("\n=== 显著性检验（配对 t，5 seeds）===")
for atk in ATTACKS:
    base = by_seed("fedrbc", atk, "0.3", T["fedrbc"])
    line = "[%s]" % atk
    for m in ("raid", "fedgt", "eiffel"):
        other = by_seed(m, atk, "0.3", T[m])
        common = sorted(set(base) & set(other))
        if len(common) < 3:
            line += "  %s:n=%d" % (m, len(common))
            continue
        t, p = stats.ttest_rel([base[s] for s in common], [other[s] for s in common])
        diff = st.mean([base[s] - other[s] for s in common])
        d = diff / (st.stdev([base[s]-other[s] for s in common]) + 1e-12)
        line += "  %s:Δ%.3f p=%.3f%s" % (m, diff, p, "*" if p < 0.05 else "")
    print(line)

print("\n=== no-attack 5 seeds（M2 修复验证）===")
for m in T:
    fs = [f for f in glob.glob("results/raw/%s_a0.5_b0.0_none_s*_summary.json" % m)]
    fs = [f for f in fs if json.load(open(f))["config"].get("tag", "") in T[m]
          and json.load(open(f))["config"].get("dataset", "wustl") == "wustl"]
    vals = [json.load(open(f))["final"]["f1"] for f in fs]
    vals = [v for v in vals if v == v]
    print("  %-8s F1=%.3f±%.3f (n=%d)" % (m, st.mean(vals), st.stdev(vals) if len(vals) > 1 else 0, len(vals)))

print("\n=== ciciot 第二数据集主表（M10）===")
for atk in ATTACKS:
    print("[%s]" % atk)
    for m in T:
        fs = [f for f in glob.glob("results/raw/%s_a0.5_b0.3_%s_s*_summary.json" % (m, atk))]
        fs = [f for f in fs if json.load(open(f))["config"].get("tag", "") in T[m]
              and json.load(open(f))["config"].get("dataset", "wustl") == "ciciot"]
        vals = [json.load(open(f))["final"]["f1"] for f in fs]
        vals = [v for v in vals if v == v]
        if vals:
            print("  %-8s F1=%.3f±%.3f (n=%d)" % (m, st.mean(vals), st.stdev(vals) if len(vals) > 1 else 0, len(vals)))
