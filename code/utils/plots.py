#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FedRBC 图表生成（Phase 6）。
读 results/raw/，产出 results/figures/（PDF+PNG, 300 DPI）与 results/tables/（CSV+LaTeX 三线表）。
图例一律置于数据区外或空旷区，坐标轴带标签/单位。
"""
import os, sys, json, glob
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

RAW = os.path.join(os.path.dirname(__file__), "..", "..", "results", "raw")
FIG = os.path.join(os.path.dirname(__file__), "..", "..", "results", "figures")
TAB = os.path.join(os.path.dirname(__file__), "..", "..", "results", "tables")
os.makedirs(FIG, exist_ok=True); os.makedirs(TAB, exist_ok=True)

plt.rcParams.update({
    "font.size": 11, "axes.titlesize": 12, "axes.labelsize": 11,
    "legend.fontsize": 9.5, "xtick.labelsize": 10, "ytick.labelsize": 10,
    "figure.dpi": 300, "savefig.dpi": 300, "pdf.fonttype": 42,
    "axes.grid": True, "grid.alpha": 0.3, "axes.axisbelow": True,
})
METHOD_LABEL = {"fedavg": "FedAvg", "fedprox": "FedProx", "krum": "Krum",
                "trimmed_mean": "TrimmedMean", "fltrust": "FLTrust", "fedrbc": "FedRBC (Ours)"}
COLORS = {"fedavg": "#7f7f7f", "fedprox": "#9467bd", "krum": "#2ca02c",
          "trimmed_mean": "#17becf", "fltrust": "#d62728", "fedrbc": "#1f77b4"}

def savefig(fig, name):
    for ext in ("pdf", "png"):
        fig.savefig(os.path.join(FIG, "%s.%s" % (name, ext)), bbox_inches="tight")
    plt.close(fig)
    print("[fig] %s" % name)

# ---------- 数据装载 ----------
def load_summaries():
    out = []
    for f in glob.glob(os.path.join(RAW, "*_summary.json")):
        d = json.load(open(f))
        c = d["config"]
        if c.get("tag", "") in ("tune", "diag", "fix", "smoke"):
            continue  # 排除调参/诊断 run
        out.append(dict(method=c["method"], attack=c["attack"], beta=c["beta"],
                        alpha=c["alpha"], seed=c["seed"], tag=c.get("tag", ""),
                        f1=d["final"]["f1"], auc=d["final"]["auc"], acc=d["final"]["acc"],
                        best_f1=d["best_f1"], wall=d["wall_sec"], run=d["run_name"]))
    return pd.DataFrame(out)

def load_rounds(run_name):
    return pd.read_csv(os.path.join(RAW, run_name + "_rounds.csv"))

def curve(method, attack, beta, alpha, tag=""):
    """返回 (rounds, mean, std) over seeds。"""
    df = load_summaries()
    sel = df[(df.method == method) & (df.attack == attack) &
             (df.beta == beta) & (df.alpha == alpha) & (df.tag == tag)]
    curves = []
    for _, r in sel.iterrows():
        rd = load_rounds(r["run"])
        curves.append(rd["f1"].values)
    if not curves:
        return None
    L = min(len(c) for c in curves)
    M = np.array([c[:L] for c in curves])
    return np.arange(1, L + 1), M.mean(0), M.std(0, ddof=1)

# ---------- Fig 1: 系统架构 ----------
def fig1():
    fig, ax = plt.subplots(figsize=(9.2, 5.6))
    ax.axis("off")
    planes = [
        ("Device Plane", "Medical IoT sensors\n(ward / ICU / ambulance / home)", "#e8f0fe"),
        ("Edge Intelligence Plane", "Local training + first-stage inference\nRoot-set evidence scoring", "#e6f4ea"),
        ("Blockchain Trust Plane", "Permissioned ledger\nUpdateTrust() contract, audit log", "#fef7e0"),
        ("SDN Control Plane", "ONOS controller\nallow / restrict / isolate rules", "#fce8e6"),
    ]
    for i, (t, s, c) in enumerate(planes):
        x = 0.03 + i * 0.245
        ax.add_patch(plt.Rectangle((x, 0.62), 0.21, 0.30, facecolor=c, edgecolor="#333", lw=1.2,
                                   transform=ax.transAxes))
        ax.text(x + 0.105, 0.865, t, ha="center", va="center", fontsize=10.5,
                fontweight="bold", transform=ax.transAxes)
        ax.text(x + 0.105, 0.72, s, ha="center", va="center", fontsize=8.2, transform=ax.transAxes)
    flow = [("① uploads $\\Delta_t^i$", 0.245, 0.56),
            ("② evidence $s_i(t)=\\cos(\\Delta_t^i,\\Delta_t^{root})$", 0.5, 0.50),
            ("③ on-chain $r_i(t+1)$ (Eq. 11-12)", 0.5, 0.40),
            ("④ aggregate (Eq. 10)", 0.245, 0.32),
            ("⑤ isolate rule if $r_i<\\tau_r$", 0.755, 0.32)]
    for txt, x, y in flow:
        ax.text(x, y, txt, ha="center", va="center", fontsize=9,
                bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="#1f77b4", lw=0.9),
                transform=ax.transAxes)
    for (x1, y1, x2, y2) in [(0.135, 0.62, 0.375, 0.62), (0.375, 0.62, 0.62, 0.62),
                             (0.62, 0.62, 0.865, 0.62), (0.865, 0.62, 0.865, 0.40),
                             (0.62, 0.36, 0.375, 0.36), (0.375, 0.40, 0.375, 0.50)]:
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1), xycoords="axes fraction",
                    arrowprops=dict(arrowstyle="->", color="#555", lw=1.1))
    ax.set_title("FedRBC: four-plane architecture and per-round workflow (S1-S6)", fontsize=12)
    savefig(fig, "fig1_architecture")

# ---------- Fig 2: 声誉动力学 ----------
def fig2(rep_file, byz_clients, gamma=0.3, mu_m=0.0, tau_r=0.35):
    H = np.load(rep_file)  # (T+1, N)
    T = H.shape[0] - 1
    t = np.arange(T + 1)
    byz = sorted(set(byz_clients))
    hon = [i for i in range(H.shape[1]) if i not in byz]
    fig, ax = plt.subplots(figsize=(6.6, 4.3))
    for i in hon:
        ax.plot(t, H[:, i], color="#1f77b4", alpha=0.22, lw=0.9)
    for i in byz:
        ax.plot(t, H[:, i], color="#d62728", alpha=0.45, lw=1.1)
    ax.plot(t, np.median(H[:, hon], axis=1), color="#1f77b4", lw=2.6, label="Honest clients (median)")
    ax.plot(t, np.median(H[:, list(byz)], axis=1), color="#d62728", lw=2.6, label="Byzantine clients (median)")
    # 理论上界 (Eq. 19): r0*(1-gamma)^t + g(mu_m)*(1-(1-gamma)^t)
    gmm = 0.5 * (1 + mu_m)
    bound = 0.5 * (1 - gamma) ** t + gmm * (1 - (1 - gamma) ** t)
    ax.plot(t, bound, "k--", lw=1.4, label="Theory upper bound, Eq. (19)")
    ax.axhline(tau_r, color="#7f7f7f", ls=":", lw=1.2)
    ax.text(T * 0.55, tau_r + 0.015, "quarantine threshold $\\tau_r$", fontsize=8.5, color="#555")
    ax.set_xlabel("Communication round $t$"); ax.set_ylabel("Reputation $r_i(t)$")
    ax.set_ylim(-0.02, 1.02)
    ax.legend(loc="upper right", framealpha=0.95)
    ax.set_title("Reputation dynamics under 20% label-flip poisoning (Prop. 1)")
    savefig(fig, "fig2_reputation")

# ---------- Fig 3: 收敛曲线 ----------
def fig3():
    fig, ax = plt.subplots(figsize=(6.6, 4.4))
    for m in ["fedavg", "fedprox", "krum", "trimmed_mean", "fltrust", "fedrbc"]:
        r = curve(m, "label_flip", 0.2, 0.5)
        if r is None: continue
        x, mu, sd = r
        ax.plot(x, mu, color=COLORS[m], lw=1.8 if m == "fedrbc" else 1.3,
                label=METHOD_LABEL[m])
        ax.fill_between(x, mu - sd, mu + sd, color=COLORS[m], alpha=0.15)
    ax.set_xlabel("Communication round $t$"); ax.set_ylabel("Test F1-score")
    ax.legend(loc="lower right", framealpha=0.95)
    ax.set_title("Convergence under 20% label-flip (Dirichlet $\\alpha$=0.5, mean$\\pm$std, 3 seeds)")
    savefig(fig, "fig3_convergence")

# ---------- Fig 4: 主结果柱状 ----------
def fig4(df):
    sel = df[(df.attack == "label_flip") & (df.beta == 0.2) & (df.alpha == 0.5) & (df.tag == "")]
    order = ["fedavg", "fedprox", "krum", "trimmed_mean", "fltrust", "fedrbc"]
    g = sel.groupby("method").agg(f1m=("f1", "mean"), f1s=("f1", "std"),
                                  aucm=("auc", "mean"), aucs=("auc", "std")).reindex(order)
    x = np.arange(len(order)); w = 0.38
    fig, ax = plt.subplots(figsize=(7.0, 4.2))
    b1 = ax.bar(x - w / 2, g["f1m"], w, yerr=g["f1s"], capsize=3, color="#1f77b4", label="F1-score")
    b2 = ax.bar(x + w / 2, g["aucm"], w, yerr=g["aucs"], capsize=3, color="#ff7f0e", label="AUC")
    ax.set_xticks(x); ax.set_xticklabels([METHOD_LABEL[m] for m in order], rotation=18, ha="right")
    ax.set_ylabel("Score"); ax.set_ylim(0, 1.05)
    ax.legend(loc="upper left", framealpha=0.95)
    ax.set_title("Final performance under 20% label-flip (mean$\\pm$std, 3 seeds)")
    savefig(fig, "fig4_main_bar")

# ---------- Fig 5: 鲁棒性（恶意比例） ----------
def fig5(df):
    methods = ["fedavg", "krum", "fltrust", "fedrbc"]
    betas = [0.0, 0.1, 0.2, 0.3]
    fig, ax = plt.subplots(figsize=(6.8, 4.2))
    for m in methods:
        ys, es = [], []
        for b in betas:
            atk = "none" if b == 0.0 else "label_flip"
            s = df[(df.method == m) & (df.attack == atk) & (df.beta == b) &
                   (df.alpha == 0.5) & (df.tag == "")]
            ys.append(s["f1"].mean() if len(s) else np.nan)
            es.append(s["f1"].std(ddof=1) if len(s) > 1 else 0)
        ax.errorbar([b * 100 for b in betas], ys, yerr=es, marker="o", lw=1.8 if m == "fedrbc" else 1.3,
                    capsize=3, color=COLORS[m], label=METHOD_LABEL[m])
    ax.set_xlabel("Byzantine ratio $\\beta$ (%)"); ax.set_ylabel("Test F1-score")
    ax.set_xticks([0, 10, 20, 30])
    ax.legend(loc="lower left", framealpha=0.95)
    ax.set_title("Robustness vs. poisoning intensity (mean$\\pm$std, 3 seeds)")
    savefig(fig, "fig5_robustness")

# ---------- Fig 6: Non-IID 敏感性 ----------
def fig6(df):
    methods = ["fedavg", "krum", "fltrust", "fedrbc"]
    alphas = [0.1, 0.5, 1.0]
    x = np.arange(len(alphas)); w = 0.19
    fig, ax = plt.subplots(figsize=(6.8, 4.2))
    for k, m in enumerate(methods):
        ys, es = [], []
        for a in alphas:
            s = df[(df.method == m) & (df.attack == "label_flip") & (df.beta == 0.2) &
                   (df.alpha == a) & (df.tag == "")]
            v = s["f1"].dropna().values
            ys.append(float(np.nanmean(v)) if len(v) else 0.0)
            es.append(float(np.nanstd(v, ddof=1)) if len(v) > 1 else 0.0)
        ax.bar(x + (k - 1.5) * w, ys, w, yerr=es, capsize=2.5, color=COLORS[m], label=METHOD_LABEL[m])
    ax.set_xticks(x); ax.set_xticklabels(["$\\alpha$=0.1\n(strong)", "$\\alpha$=0.5", "$\\alpha$=1.0\n(weak)"])
    ax.set_xlabel("Non-IID degree (Dirichlet $\\alpha$)"); ax.set_ylabel("Test F1-score")
    ax.set_ylim(0, 1.0)
    ax.legend(loc="lower right", ncol=2, framealpha=0.95)
    ax.set_title("Sensitivity to data heterogeneity (20% label-flip)")
    savefig(fig, "fig6_noniid")

# ---------- Fig 7: MTTC ----------
def fig7():
    df = pd.read_csv(os.path.join(RAW, "mttc.csv"))
    fig, ax = plt.subplots(figsize=(6.4, 4.2))
    ax.plot(df["rho"], df["mttc_cloud"], "o-", color="#d62728", lw=1.6, ms=4,
            label="Cloud revalidation (baseline, Eq. 16)")
    ax.plot(df["rho"], df["mttc_edge"], "s-", color="#1f77b4", lw=1.6, ms=4,
            label="Edge-local verification (FedRBC, Eq. 15)")
    ax.set_xlabel("Cloud verifier utilization $\\rho=\\lambda_a/\\mu_c$")
    ax.set_ylabel("MTTC (time units)")
    ax.legend(loc="upper left", framealpha=0.95)
    ax.set_title("Mean time to containment vs. verification load (Thm. 2)")
    savefig(fig, "fig7_mttc")

# ---------- Fig 8: 客户端选择 ----------
def fig8():
    fig, ax = plt.subplots(figsize=(6.4, 4.2))
    for tag, label, c in [("", "Reputation-aware selection (Eq. 14)", "#1f77b4"),
                          ("abl_randsel", "Random selection (ablation)", "#7f7f7f")]:
        r = curve("fedrbc", "label_flip", 0.2, 0.5, tag=tag)
        if r is None: continue
        x, mu, sd = r
        ax.plot(x, mu, color=c, lw=1.8, label=label)
        ax.fill_between(x, mu - sd, mu + sd, color=c, alpha=0.15)
    ax.set_xlabel("Communication round $t$"); ax.set_ylabel("Test F1-score")
    ax.legend(loc="lower right", framealpha=0.95)
    ax.set_title("Effect of reputation-aware client selection (Prop. 2)")
    savefig(fig, "fig8_selection")

# ---------- Tables（CSV + LaTeX 三线表） ----------
def latex_booktabs(df, path, caption_cols):
    cols = list(df.columns)
    lines = ["\\begin{tabular}{%s}" % ("l" + "c" * (len(cols) - 1)),
             "\\toprule",
             " & ".join(caption_cols) + " \\\\",
             "\\midrule"]
    for _, r in df.iterrows():
        lines.append(" & ".join(str(v) for v in r.values) + " \\\\")
    lines += ["\\bottomrule", "\\end{tabular}"]
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

def table_main(df):
    sel = df[(df.attack == "label_flip") & (df.beta == 0.2) & (df.alpha == 0.5) & (df.tag == "")]
    order = ["fedavg", "fedprox", "krum", "trimmed_mean", "fltrust", "fedrbc"]
    rows = []
    for m in order:
        s = sel[sel.method == m]
        if not len(s): continue
        rows.append(dict(Method=METHOD_LABEL[m],
                         F1="%.3f$\\pm$%.3f" % (s["f1"].mean(), s["f1"].std(ddof=1)),
                         AUC="%.3f$\\pm$%.3f" % (s["auc"].mean(), s["auc"].std(ddof=1)),
                         Acc="%.3f$\\pm$%.3f" % (s["acc"].mean(), s["acc"].std(ddof=1))))
    out = pd.DataFrame(rows)
    out.to_csv(os.path.join(TAB, "table5_main.csv"), index=False)
    latex_booktabs(out, os.path.join(TAB, "table5_main.tex"), ["Method", "F1-score", "AUC", "Accuracy"])
    print("[tab] table5_main")

def table_ablation(df):
    sel = df[(df.method == "fedrbc") & (df.attack == "label_flip") & (df.beta == 0.2) & (df.alpha == 0.5)]
    variants = [("", "FedRBC (full)"), ("abl_norep", "w/o reputation weighting"),
                ("abl_randsel", "w/o reputation-aware selection"),
                ("abl_nodecay", "w/o decay & penalty")]
    rows = []
    for tag, name in variants:
        s = sel[sel.tag == tag]
        if not len(s): continue
        rows.append(dict(Variant=name,
                         F1="%.3f$\\pm$%.3f" % (s["f1"].mean(), s["f1"].std(ddof=1)),
                         AUC="%.3f$\\pm$%.3f" % (s["auc"].mean(), s["auc"].std(ddof=1))))
    out = pd.DataFrame(rows)
    out.to_csv(os.path.join(TAB, "table7_ablation.csv"), index=False)
    latex_booktabs(out, os.path.join(TAB, "table7_ablation.tex"), ["Variant", "F1-score", "AUC"])
    print("[tab] table7_ablation")

def main():
    df = load_summaries()
    if not len(df):
        print("no summaries found"); return
    print("loaded %d runs" % len(df))
    fig1()
    # Fig 2 需要 repdyn（60 轮）的 rep.npy 与 byz 列表
    reps = sorted(glob.glob(os.path.join(RAW, "fedrbc_a0.5_b0.2_label_flip_s42_repdyn_rep.npy")))
    if not reps:
        reps = sorted(glob.glob(os.path.join(RAW, "fedrbc_a0.5_b0.2_label_flip_s42_rep.npy")))
    if reps:
        d = json.load(open(os.path.join(RAW, os.path.basename(reps[0]).replace("_rep.npy", "_summary.json"))))
        fig2(reps[0], d["byz_clients"])
    fig3(); fig4(df); fig5(df); fig6(df); fig7(); fig8()
    table_main(df); table_ablation(df)
    print("all done.")

if __name__ == "__main__":
    main()
