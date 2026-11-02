#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
仿真结果图表（论文 v2 终版，SCI 1 区标准，300 DPI PDF+PNG）。
数据源：全部方法 tag=v5（NaN 防护后的最终数据）；mttc.csv 为解析仿真。
图内无标题（标题在正文 caption）；fig5 子图攻击名为面板标识。
Fig 5  主表（3 攻击 × 4 方法分组柱状，5 seeds）
Fig 6  收敛曲线（sybil）
Fig 7  β 扫描（sybil，3 seeds）
Fig 8  Non-IID 敏感性（sybil，3 seeds）
Fig 9  声誉动态（v5 rep.npy，s42）
Fig 10 MTTC（图例公式编号 Eq.12/13）
Table 5 主表 CSV+LaTeX；Table 6 开销
"""
import os, json, glob, math
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

RAW = os.path.join(os.path.dirname(__file__), "..", "..", "results", "raw")
FIG = os.path.join(os.path.dirname(__file__), "..", "..", "results", "figures")
TAB = os.path.join(os.path.dirname(__file__), "..", "..", "results", "tables")
os.makedirs(FIG, exist_ok=True); os.makedirs(TAB, exist_ok=True)

plt.rcParams.update({
    "font.size": 10.5, "axes.titlesize": 11.5, "axes.labelsize": 10.5,
    "legend.fontsize": 9, "xtick.labelsize": 9.5, "ytick.labelsize": 9.5,
    "axes.linewidth": 0.9, "grid.linewidth": 0.5, "lines.linewidth": 1.6,
    "figure.dpi": 300, "savefig.dpi": 300, "axes.grid": True,
    "grid.alpha": 0.35, "legend.framealpha": 0.95,
})

METHODS = ["fedrbc", "raid", "fedgt", "eiffel"]
LABEL = {"fedrbc": "FedRBC (Ours)", "raid": "RAID (2026)", "fedgt": "FedGT (2025)",
         "eiffel": "EIFFeL (2022)", "fltrust": "FLTrust (2021)"}
COLOR = {"fedrbc": "#C0392B", "raid": "#8E44AD", "fedgt": "#2471A3",
         "eiffel": "#1E8449", "fltrust": "#D68910"}
MARK = {"fedrbc": "o", "raid": "s", "fedgt": "^", "eiffel": "D", "fltrust": "v"}
ATTACKS = ["sign_flip", "sybil", "label_flip"]
ATK_LABEL = {"sign_flip": "Sign-flip", "sybil": "Sybil collusion",
             "label_flip": "Label-flip", "scaling": "Scaling",
             "noise": "Gaussian noise", "none": "No attack"}
TAG = {"fedrbc": "v5", "raid": "v5", "fedgt": "v5", "eiffel": "v5", "fltrust": "rev1"}


def load_summary(method, alpha, beta, attack, dataset="wustl"):
    tag = TAG[method]
    out = []
    for f in sorted(glob.glob(os.path.join(
            RAW, "%s_a%s_b%s_%s_s*_summary.json" % (method, alpha, beta, attack)))):
        d = json.load(open(f))
        if d["config"].get("tag", "") != tag:
            continue
        if d["config"].get("dataset", "wustl") != dataset:
            continue
        out.append(d)
    return out


def load_rev10(method, alpha, beta, attack, dataset="wustl"):
    """Round-1 主表 10-seed 数据：s42-46 在 tag=v5、s47-51 在 tag=rev1，取并集。"""
    out, seen = [], set()
    for f in sorted(glob.glob(os.path.join(
            RAW, "%s_a%s_b%s_%s_s*_summary.json" % (method, alpha, beta, attack)))):
        d = json.load(open(f))
        t = d["config"].get("tag", "")
        if t not in ("v5", "rev1"):
            continue
        if d["config"].get("dataset", "wustl") != dataset:
            continue
        # 排除消融/扩展实验的 rev1_* 变体 tag
        s = d["config"]["seed"]
        if (t, s) in seen:
            continue
        seen.add((t, s))
        if t == "v5" and s not in (42, 43, 44, 45, 46):
            continue
        if t == "rev1" and s not in (47, 48, 49, 50, 51):
            continue
        # 默认配置指纹（排除 β/α 扫描）已在文件名层由 a/b 参数保证
        if abs(float(d["config"].get("beta", 0.3)) - float(beta)) > 1e-9:
            continue
        if d["config"].get("dp_sigma", 0) or d["config"].get("root_poison", 0):
            continue
        if not d["config"].get("memory", True) and method == "fedrbc":
            continue
        if method == "fedrbc" and d["config"].get("soft_T", 0.3) not in (0.3, None):
            continue
        out.append(d)
    return out


def stat(ds, key):
    vals = [d["final"][key] for d in ds if not math.isnan(d["final"][key])]
    if not vals:
        return float("nan"), 0.0
    m = float(np.mean(vals))
    s = float(np.std(vals, ddof=1)) if len(vals) > 1 else 0.0
    return m, s


def savefig(fig, name):
    fig.savefig(os.path.join(FIG, name + ".pdf"), bbox_inches="tight")
    fig.savefig(os.path.join(FIG, name + ".png"), bbox_inches="tight")
    plt.close(fig)
    print(name, "done")


# ---------- Fig 5: 主表分组柱状（Round-1：10-seed，5 方法含 FLTrust） ----------
def fig5():
    m5 = ["fedrbc", "fltrust", "eiffel", "raid", "fedgt"]
    fig, axes = plt.subplots(1, 3, figsize=(11.6, 3.6), sharey=True)
    for k, atk in enumerate(ATTACKS):
        ax = axes[k]
        xs = np.arange(3)
        w = 0.155
        for j, m in enumerate(m5):
            ds = load_rev10(m, "0.5", "0.3", atk)
            print("  fig5 %s %s: n=%d" % (m, atk, len(ds)))
            means = [stat(ds, kk)[0] for kk in ("f1", "auc", "acc")]
            stds = [stat(ds, kk)[1] for kk in ("f1", "auc", "acc")]
            means = [0.0 if math.isnan(v) else v for v in means]
            ax.bar(xs + (j - 2.0) * w, means, w, yerr=stds, capsize=2.5,
                   color=COLOR[m], label=(LABEL[m] if k == 0 else None),
                   edgecolor="white", linewidth=0.5, error_kw=dict(lw=0.8))
        ax.set_xticks(xs); ax.set_xticklabels(["F1", "AUC", "Acc"])
        ax.set_title(ATK_LABEL[atk], fontsize=10.5)
        ax.set_ylim(0, 1.02)
        if k == 0:
            ax.set_ylabel("Score")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=5, frameon=False,
               bbox_to_anchor=(0.5, 1.05))
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    savefig(fig, "fig5_main_attacks")


# ---------- Fig 6: 收敛曲线（sybil） ----------
def fig6():
    fig, ax = plt.subplots(figsize=(6.6, 4.0))
    for m in METHODS:
        runs = []
        for f in sorted(glob.glob(os.path.join(
                RAW, "%s_a0.5_b0.3_sybil_s*_rounds.csv" % m))):
            sj = f.replace("_rounds.csv", "_summary.json")
            tag = ""
            if os.path.exists(sj):
                cfg = json.load(open(sj))["config"]
                tag = cfg.get("tag", "")
                if cfg.get("dataset", "wustl") != "wustl":
                    continue
            if tag != TAG[m]:
                continue
            df = pd.read_csv(f)
            runs.append(df["f1"].values)
        if not runs:
            continue
        L = min(len(r) for r in runs)
        R = np.stack([r[:L] for r in runs])
        x = np.arange(1, L + 1)
        ax.plot(x, R.mean(axis=0), color=COLOR[m], label=LABEL[m])
        if len(runs) > 1:
            ax.fill_between(x, R.mean(axis=0) - R.std(axis=0, ddof=1),
                            R.mean(axis=0) + R.std(axis=0, ddof=1),
                            color=COLOR[m], alpha=0.16, linewidth=0)
    ax.set_xlabel("Communication round $t$")
    ax.set_ylabel("Test F1-score")
    # E4: 图例避让数据（曲线自左下向右上收敛后持稳，右上角为空白区）
    ax.legend(loc="upper right")
    ax.set_ylim(0, 1.0)
    savefig(fig, "fig6_convergence")


# ---------- Fig 7: β 扫描（sybil） ----------
def fig7():
    fig, ax = plt.subplots(figsize=(6.6, 4.0))
    betas = ["0.1", "0.2", "0.3", "0.4"]
    for m in METHODS:
        ys, es = [], []
        for b in betas:
            ds = load_summary(m, "0.5", b, "sybil")
            mm, ss = stat(ds, "f1")
            ys.append(mm); es.append(ss)
        ax.errorbar([float(b) * 100 for b in betas], ys, yerr=es, marker=MARK[m],
                    ms=5.5, capsize=3, color=COLOR[m], label=LABEL[m],
                    lw=1.9 if m == "fedrbc" else 1.3)
    ax.set_xlabel("Byzantine ratio $\\beta$ (%)")
    ax.set_ylabel("Test F1-score")
    ax.set_xticks([10, 20, 30, 40])
    ax.legend(loc="lower left")
    ax.set_ylim(0, 1.0)
    savefig(fig, "fig7_beta_sweep")


# ---------- Fig 8: Non-IID 敏感性 ----------
def fig8():
    fig, ax = plt.subplots(figsize=(6.8, 4.0))
    alphas = ["0.1", "0.5", "1.0"]
    xs = np.arange(3); w = 0.19
    for j, m in enumerate(METHODS):
        means, stds = [], []
        for a in alphas:
            ds = load_summary(m, a, "0.3", "sybil")
            mm, ss = stat(ds, "f1")
            means.append(0.0 if math.isnan(mm) else mm); stds.append(ss)
        ax.bar(xs + (j - 1.5) * w, means, w, yerr=stds, capsize=3,
               color=COLOR[m], label=LABEL[m], edgecolor="white", linewidth=0.5,
               error_kw=dict(lw=0.8))
    ax.set_xticks(xs)
    ax.set_xticklabels(["$\\alpha$=0.1\n(extreme)", "$\\alpha$=0.5\n(moderate)", "$\\alpha$=1.0\n(mild)"])
    ax.set_ylabel("Test F1-score")
    ax.set_ylim(0, 1.0)
    # E4: 图例避让柱组（柱高 ≤0.7，上方留白充分）
    ax.legend(loc="upper right", ncol=2)
    savefig(fig, "fig8_noniid")


# ---------- Fig 9: 声誉动态 ----------
def fig9():
    reps = sorted(glob.glob(os.path.join(RAW, "fedrbc_a0.5_b0.3_sybil_s42_v5_rep.npy")))
    if not reps:
        print("fig9: repdyn 缺失"); return
    R = np.load(reps[0])
    sj = reps[0].replace("_rep.npy", "_summary.json")
    byz = json.load(open(sj))["byz_clients"] if os.path.exists(sj) else []
    T = R.shape[0] - 1
    x = np.arange(0, T + 1)
    fig, ax = plt.subplots(figsize=(6.8, 4.0))
    honest = [i for i in range(R.shape[1]) if i not in byz]
    H = R[:, honest]
    ax.fill_between(x, np.percentile(H, 10, axis=1), np.percentile(H, 90, axis=1),
                    color="#1E8449", alpha=0.18, linewidth=0, label="Honest (P10–P90)")
    ax.plot(x, np.median(H, axis=1), color="#1E8449", lw=2.0, label="Honest (median)")
    for i in byz:
        ax.plot(x, R[:, i], color="#C0392B", lw=1.1, alpha=0.75)
    ax.plot([], [], color="#C0392B", lw=1.4, label="Byzantine (individual)")
    ax.axhline(0.15, color="#7D3C98", ls="--", lw=1.3, label="Quarantine $r_{\\rm q}$=0.15")
    r0, kg = 0.5, 0.6
    ax.plot(x, r0 * (1 - kg) ** x, color="#922B21", ls=":", lw=1.6,
            label="Theory bound $r_0(1-\\kappa\\gamma)^t$")
    ax.set_xlabel("Communication round $t$")
    ax.set_ylabel("On-chain reputation $r_i(t)$")
    ax.legend(loc="upper right", fontsize=8.5)
    ax.set_ylim(0, 1.0)
    savefig(fig, "fig9_repdyn")


# ---------- Fig 10: MTTC ----------
def fig10():
    f = os.path.join(RAW, "mttc.csv")
    if not os.path.exists(f):
        print("fig10: mttc.csv 缺失"); return
    df = pd.read_csv(f)
    fig, ax = plt.subplots(figsize=(6.6, 4.0))
    for col, lb, c in [("mttc_edge", "FedRBC edge containment (Eq. 12)", "#C0392B"),
                       ("mttc_cloud", "Cloud-roundtrip baseline (Eq. 13)", "#2471A3")]:
        if col in df.columns:
            ax.plot(df["rho"], df[col], marker="o", ms=5, color=c, label=lb)
    ax.set_xlabel("Utilization $\\rho = \\lambda_a / \\mu$")
    ax.set_ylabel("MTTC (s)")
    ax.legend(loc="upper left")
    savefig(fig, "fig10_mttc")


# ---------- Table 5: 主表 ----------
def table5():
    rows = []
    for atk in ATTACKS:
        for m in METHODS:
            ds = load_summary(m, "0.5", "0.3", atk)
            f1, f1s = stat(ds, "f1")
            auc, aucs = stat(ds, "auc")
            acc, accs = stat(ds, "acc")
            def fmt(v, s):
                return "collapse" if math.isnan(v) else "%.3f$\\pm$%.3f" % (v, s)
            rows.append(dict(Attack=ATK_LABEL[atk], Method=LABEL[m],
                             F1=fmt(f1, f1s), AUC=fmt(auc, aucs), Acc=fmt(acc, accs)))
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(TAB, "table5_main.csv"), index=False)
    with open(os.path.join(TAB, "table5_main.tex"), "w") as fh:
        fh.write("\\begin{tabular}{llccc}\n\\toprule\nAttack & Method & F1 & AUC & Acc \\\\\n\\midrule\n")
        for _, r in df.iterrows():
            fh.write("%s & %s & %s & %s & %s \\\\\n" % (r.Attack, r.Method, r.F1, r.AUC, r.Acc))
        fh.write("\\bottomrule\n\\end{tabular}\n")
    print("table5 done")


# ---------- Table 6: 每轮开销 ----------
def table6():
    rows = []
    for m in METHODS:
        ws = []
        for atk in ATTACKS:
            for d in load_summary(m, "0.5", "0.3", atk):
                ws.append(d["wall_sec"] / d["config"]["rounds"])
        if ws:
            rows.append((LABEL[m], float(np.mean(ws)), float(np.std(ws, ddof=1))))
    df = pd.DataFrame(rows, columns=["Method", "Sec/Round", "Std"])
    df.to_csv(os.path.join(TAB, "table6_overhead.csv"), index=False)
    print("table6 done")


if __name__ == "__main__":
    fig5(); fig6(); fig7(); fig8(); fig9(); fig10()
    table5(); table6()
    print("all sim figures/tables done.")
