#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Round-1 论文表格生成：从 results/rev1_all.csv 计算 Table 4/6/7/8 全部数字，
输出可直接粘贴进 v3_eval.md 的 markdown。b3 (β=0.5) 完成后重跑可自动包含。"""
import csv, math, statistics as st

ROWS = list(csv.DictReader(open(r"D:\workbuddy\CMC0930\results\rev1_all.csv", encoding="utf-8")))

def f(r, k):
    v = r.get(k, "")
    try:
        x = float(v)
        return x if x == x else None
    except Exception:
        return None

def sel(group, method=None, attack=None, **kw):
    out = []
    for r in ROWS:
        if r["group"] != group:
            continue
        if method and r["method"] != method:
            continue
        if attack and r["attack"] != attack:
            continue
        ok = True
        for k, v in kw.items():
            rv = f(r, k)
            if k in ("dp_sigma", "root_poison"):
                if (rv or 0.0) != float(v):
                    ok = False
            elif abs((rv if rv is not None else -1e9) - float(v)) > 1e-9:
                ok = False
        if ok:
            out.append(r)
    return out

def msf(rows, key="f1"):
    vals = [f(r, key) for r in rows]
    vals = [v for v in vals if v is not None and not math.isnan(v)]
    if not vals:
        return "n/a"
    m = st.mean(vals)
    s = st.stdev(vals) if len(vals) > 1 else 0.0
    return "%.3f±%.3f" % (m, s), len(vals)

def cell(group, method, attack, key="f1", **kw):
    rows = sel(group, method=method, attack=attack, **kw)
    r = msf(rows, key)
    return r if isinstance(r, str) else r[0]

def n_of(group, method, attack, **kw):
    return len(sel(group, method=method, attack=attack, **kw))

ATT = ["sign_flip", "sybil", "label_flip"]
M7 = ["fedrbc", "fltrust", "krum", "trimmed_mean", "eiffel", "raid", "fedgt"]
NAME = {"fedrbc": "**FedRBC (Ours)**", "fltrust": "FLTrust", "krum": "Krum",
        "trimmed_mean": "Trimmed mean", "eiffel": "EIFFeL (2022)",
        "raid": "RAID (2026)", "fedgt": "FedGT (2025)", "fedavg": "FedAvg"}

print("=" * 70)
print("### Table 4 (new): 10-seed main comparison + upper bounds")
print()
print("| Attack | Method | F1 | AUC |")
print("|---|---|---|---|")
for atk in ATT:
    for m in M7:
        n = n_of("main", m, atk)
        nn = "" if n == 10 else " (n=%d)" % n
        print("| %s | %s%s | %s | %s |" % (atk if m == "fedrbc" else "",
              NAME[m], nn, cell("main", m, atk), cell("main", m, atk, "auc")))
print("| No attack (upper bounds) | Centralized | %s | %s |" % (
    cell("centralized", None, "none"), cell("centralized", None, "none", "auc")))
print("| | Clean FedAvg | %s | %s |" % (
    cell("upper_noattack", "fedavg", "none"), cell("upper_noattack", "fedavg", "none", "auc")))
print("| | FedRBC (no attack) | %s | %s |" % (
    cell("upper_noattack", "fedrbc", "none"), cell("upper_noattack", "fedrbc", "none", "auc")))

print()
print("=" * 70)
print("### Table 6: extended threat model (LIE / backdoor / root-poison)")
print()
print("| Study | Method | F1 | ASR |")
print("|---|---|---|---|")
for m in ["fedrbc", "fltrust", "eiffel", "fedavg"]:
    print("| LIE (5 seeds) | %s | %s | - |" % (NAME[m], cell("lie", m, "lie")))
for m in ["fedrbc", "fltrust", "fedavg"]:
    rows = sel("bd", method=m, attack="backdoor")
    asr = [f(r, "asr") for r in rows]
    asr = [a for a in asr if a is not None]
    print("| Backdoor (3 seeds) | %s | %s | %.3f±%.3f |" % (
        NAME[m], cell("bd", m, "backdoor"), st.mean(asr), st.stdev(asr)))
for eps in ["0.1", "0.2", "0.3"]:
    for atk in ["sybil", "sign_flip"]:
        print("| Root-poison ε=%s, %s | FedRBC | %s | - |" % (eps, atk, cell("root_poison", "fedrbc", atk, root_poison=eps)))
        print("| | FLTrust | %s | - |" % cell("root_poison", "fltrust", atk, root_poison=eps))

print()
print("=" * 70)
print("### Table 7: DP trade-off (F1)")
print()
print("| σ_dp | Method | sign-flip F1 | Sybil F1 |")
print("|---|---|---|---|")
for sig in ["0.005", "0.02", "0.1"]:
    for m in ["fedrbc", "fltrust", "eiffel", "fedavg"]:
        print("| %s | %s | %s | %s |" % (sig, NAME[m],
              cell("dp", m, "sign_flip", dp_sigma=sig), cell("dp", m, "sybil", dp_sigma=sig)))

print()
print("=" * 70)
print("### Table 8: component ablation, 3 seeds matched (F1), full = same-seed baseline")
print()
full3 = {}
for atk in ATT:
    full3[atk] = [f(r, "f1") for r in sel("main", "fedrbc", atk) if r["seed"] in ("42", "43", "44")]
print("| Configuration | Sign-flip | Sybil | Label-flip |")
print("|---|---|---|---|")
def m3(vals):
    vals = [v for v in vals if v is not None and not math.isnan(v)]
    return "%.3f±%.3f" % (st.mean(vals), st.stdev(vals))
print("| **FedRBC (full, same seeds)** | %s | %s | %s |" % (m3(full3["sign_flip"]), m3(full3["sybil"]), m3(full3["label_flip"])))
for name, tag in [("− directional gate", "rev1-ab_gate"), ("− relative clipping", "rev1-ab_clip"),
                  ("− Layer-0 filter", "rev1-ab_layer0"), ("− reputation weighting", "rev1-ab_repw"),
                  ("− selection (random)", "rev1-ab_select")]:
    vals = {atk: [f(r, "f1") for r in ROWS if r["group"] == "ablation" and r["tag"] == tag and r["attack"] == atk] for atk in ATT}
    print("| %s | %s | %s | %s |" % (name, m3(vals["sign_flip"]), m3(vals["sybil"]), m3(vals["label_flip"])))
vals = {atk: [f(r, "f1") for r in sel("abmemory", "fedrbc", atk)] for atk in ATT}
print("| − cross-round memory (ledger reset) | %s | %s | %s |" % (m3(vals["sign_flip"]), m3(vals["sybil"]), m3(vals["label_flip"])))

print()
print("=" * 70)
print("### β=0.5 (b3; auto-updates when batch-3 completes)")
print()
for m in ["fedrbc", "fltrust", "eiffel", "fedavg"]:
    row = "| %s | %s | %s |" % (NAME[m], cell("b50", m, "sign_flip"), cell("b50", m, "sybil"))
    print(row)

print()
print("=" * 70)
print("### Sensitivity & scaling text numbers")
print("Defaults (10-seed): sign_flip %s sybil %s label_flip %s" % (
    cell("main", "fedrbc", "sign_flip"), cell("main", "fedrbc", "sybil"), cell("main", "fedrbc", "label_flip")))
for tag in ["softT01", "softT05", "taurel10", "taurel30", "thh01", "thh05", "k06", "k14", "root100", "root300"]:
    rows = [r for r in ROWS if r["group"] == "sens" and r["tag"].endswith(tag)]
    vals = [f(r, "f1") for r in rows if f(r, "f1") is not None]
    print("sens %s: %s (n=%d)" % (tag, m3(vals) if vals else "n/a", len(vals)))
for N in ["50", "100"]:
    for m in ["fedrbc", "fltrust", "fedavg"]:
        rows = [r for r in ROWS if r["group"] == "scaling" and r["method"] == m and r["n_clients"] == N]
        vals = [f(r, "f1") for r in rows]
        vals = [v for v in vals if v is not None and not math.isnan(v)]
        print("scaling N=%s %s: %s (raw n=%d incl. collapses)" % (N, m, m3(vals) if vals else "all-collapsed", len(rows)))
print()
print("AUC of fedrbc main:", {atk: cell("main", "fedrbc", atk, "auc") for atk in ATT})
