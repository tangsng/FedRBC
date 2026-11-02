#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SCI 1 区标准架构图与流程图（Fig 1-3，matplotlib 精绘，300 DPI PDF+PNG）。
2026-10-01 更新：
  - 公式编号对齐最终版（升序 1-14）：local SGD=Eq.2, s_i=Eq.4, clip=Eq.5,
    RWRA=Eq.7, reward=Eq.8, penalty/decay=Eq.9, selection=Eq.11, MTTC=Eq.12。
  - 所有图不内嵌标题（正文 caption 已给出）。
  - Fig 1 重绘为清晰的三层架构图：层容器 + 模块分组 + 编号徽标数据流 + 图例。
  - Fig 3 重绘为声誉管理泳道图：编号徽标 + 紧凑布局 + 底部图例（修复超界与留白）。
  - 删除原 Fig 4（检测-遏制闭环改为正文文字表达）。
  - 2026-11-03 可读性修订（R1.18）：默认标签字号 10→10.8、箭头标注 8.5→9.2、
    徽标半径/字号加大（r=0.016, fs=8.5, mutation_scale=14.5）。
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle, Rectangle
import matplotlib.patheffects as pe
import os

OUT = os.path.join(os.path.dirname(__file__), "..", "..", "results", "figures")
os.makedirs(OUT, exist_ok=True)

FILL = dict(peri="#DEEBF7", edge="#FCE8D5", chain="#EAE1F5", contract="#DFF0D8",
            attack="#F8D7DA", honest="#D4EDDA", ctrl="#FFF3CD", gray="#F2F3F4",
            accent="#D6EAF8", white="#FFFFFF")
TXT = "#1B2631"
PURPLE = "#6C3483"
RED = "#C0392B"
BROWN = "#B9770E"


def box(ax, x, y, w, h, text, fill, fs=10.8, ec="#2C3E50", lw=1.1, bold=False,
        tc=TXT, zorder=3, round=0.02):
    b = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.01,rounding_size=%s" % round,
                       fc=fill, ec=ec, lw=lw, zorder=zorder)
    ax.add_patch(b)
    if text:
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs,
                color=tc, zorder=zorder + 1, fontweight=("bold" if bold else "normal"),
                linespacing=1.35)
    return b


def arrow(ax, x1, y1, x2, y2, text="", fs=9.2, color="#2C3E50", lw=1.5, style="-|>",
          ls="-", num=None, zorder=2, tx=0, ty=0.02, tc=TXT, conn="arc3,rad=0.0"):
    a = FancyArrowPatch((x1, y1), (x2, y2), arrowstyle=style, mutation_scale=14.5,
                        color=color, lw=lw, linestyle=ls, connectionstyle=conn, zorder=zorder)
    ax.add_patch(a)
    if text:
        label = (("(%s) " % num) if num else "") + text
        ax.text((x1 + x2) / 2 + tx, (y1 + y2) / 2 + ty, label, ha="center", va="center",
                fontsize=fs, color=tc, zorder=zorder + 2, style="italic",
                path_effects=[pe.withStroke(linewidth=2.6, foreground="white")])


def badge(ax, x, y, num, color="#2C3E50", r=0.016, fs=8.5):
    """编号圆形徽标（SCI 架构图标准做法）。"""
    ax.add_patch(Circle((x, y), r, fc=color, ec="white", lw=1.0, zorder=6))
    ax.text(x, y, str(num), ha="center", va="center", fontsize=fs,
            color="white", fontweight="bold", zorder=7)


# ================= Fig 1: 系统总体架构（三层 + 编号数据流 + 底部图例） =================
def fig1():
    fig, ax = plt.subplots(figsize=(12.2, 8.6))
    ax.set_xlim(0, 1); ax.set_ylim(-0.062, 1.0); ax.axis("off")

    # ---- 三层容器 ----
    layers = [
        ("SENSING LAYER", 0.030, 0.300, FILL["peri"]),
        ("EDGE FEDERATED LAYER", 0.345, 0.635, "#FDF2E9"),
        ("BLOCKCHAIN / CONTROL LAYER", 0.680, 0.955, FILL["chain"]),
    ]
    for name, y0, y1, fc in layers:
        ax.add_patch(FancyBboxPatch((0.02, y0), 0.96, y1 - y0,
                     boxstyle="round,pad=0.003,rounding_size=0.006",
                     fc=fc, ec="#85929E", lw=1.1, alpha=0.30, zorder=0))
        ax.text(0.045, y1 - 0.020, name, fontsize=11.5, color="#2E4053",
                fontweight="bold", va="top", zorder=1)

    # ---- Sensing 层：5 台设备（最后一台为攻击者）----
    devs = ["Wearable\nECG", "Bedside\nMonitor", "Infusion\nPump",
            "Imaging\nGateway", "Compromised\n(MitM)"]
    devfill = [FILL["honest"]] * 4 + [FILL["attack"]]
    devx = [0.055, 0.245, 0.435, 0.625, 0.815]
    for i, (d, f) in enumerate(zip(devs, devfill)):
        box(ax, devx[i], 0.075, 0.145, 0.115, d, f, fs=8.5,
            ec=RED if i == 4 else "#2C3E50", lw=1.4 if i == 4 else 1.0)

    # ---- Edge 层：根集合（左） + 聚合服务器（中，内部 4 步流水线）----
    box(ax, 0.05, 0.40, 0.18, 0.16,
        "Root set $\\mathcal{D}_r$\nreference update\n$\\Delta_{\\rm root}$ (Eq. 3)",
        "#FDEBD0", fs=8.0)
    box(ax, 0.34, 0.40, 0.44, 0.16, "", FILL["accent"], fs=8.0)
    ax.text(0.36, 0.532, "Edge Server (aggregator)", fontsize=9.5,
            fontweight="bold", color=TXT, va="center", zorder=4)
    steps = [("Select\n(Eq. 11)", "#D6EAF8"), ("Evidence $s_i$\n(Eq. 4)", "#FDEBD0"),
             ("Clip $\\tau_c$\n(Eq. 5)", "#FCF3CF"), ("RWRA\n(Eq. 7)", "#D5F5E3")]
    sx = 0.365
    for i, (t, fc) in enumerate(steps):
        box(ax, sx, 0.408, 0.085, 0.100, t, fc, fs=7.0)
        if i < 3:
            arrow(ax, sx + 0.085, 0.458, sx + 0.105, 0.458, "",
                  lw=1.1, color="#5D6D7E", style="-|>", conn="arc3,rad=0.0")
        sx += 0.105

    # ---- Blockchain 层：账本 / 合约 / SDN ----
    box(ax, 0.05, 0.73, 0.24, 0.17,
        "Reputation Ledger\n(on-chain, immutable)\n$r_i(t)\\in[0,1]$", "#E8DAEF", fs=8.0)
    box(ax, 0.36, 0.73, 0.30, 0.17,
        "Smart Contract\n① reputation update (Alg. 2, Eqs. 8–9)\n② containment trigger",
        FILL["contract"], fs=8.0)
    box(ax, 0.72, 0.73, 0.24, 0.17,
        "SDN Controller (ONOS)\nisolation flow rules\nquarantine $r_i<r_{\\rm q}$",
        FILL["ctrl"], fs=8.0)

    # ---- 数据流（编号徽标）----
    # (1) 设备本地 SGD 后上传更新 → 聚合服务器
    arrow(ax, 0.55, 0.19, 0.55, 0.40, "", lw=1.8, zorder=2)
    badge(ax, 0.552, 0.295, 1)
    ax.text(0.585, 0.292, "$\\Delta_i$, $H(\\Delta_i)$\n(local SGD, Eq. 2)",
            fontsize=8.0, style="italic", va="center", zorder=3)
    # 攻击者注入的恶意更新（红虚线）
    arrow(ax, 0.887, 0.19, 0.66, 0.40, "", color=RED, lw=1.4, ls="--", zorder=2)
    ax.text(0.815, 0.285, "poisoned\n$\\tilde{\\Delta}$", fontsize=8.0, color=RED,
            ha="center", style="italic", zorder=3)

    # (2) 根集合 → 聚合服务器（参考方向）
    arrow(ax, 0.23, 0.48, 0.34, 0.48, "", lw=1.4, color=BROWN, zorder=2)
    badge(ax, 0.285, 0.450, 2, color=BROWN)
    ax.text(0.285, 0.514, "reference", fontsize=8.0, color=BROWN,
            ha="center", style="italic", zorder=3)

    # (3) 聚合服务器 → 合约（writeEvidence，链上）
    arrow(ax, 0.52, 0.56, 0.50, 0.73, "", color=PURPLE, lw=1.6, zorder=2)
    badge(ax, 0.472, 0.645, 3, color=PURPLE)
    ax.text(0.435, 0.648, "writeEvidence$(i, s_i)$", fontsize=8.5, color=PURPLE,
            ha="right", style="italic", zorder=3)

    # (4) 合约 ↔ 账本（声誉读写，文字置于箱体上方）
    arrow(ax, 0.36, 0.815, 0.29, 0.815, "", color=PURPLE, lw=1.4,
          style="<|-|>", zorder=2)
    badge(ax, 0.325, 0.808, 4, color=PURPLE)
    ax.text(0.325, 0.972, "read/write $r_i$", fontsize=8.0, color=PURPLE,
            ha="center", style="italic", zorder=3)

    # (5) 账本 → 聚合服务器（声誉反馈到选择/权重）
    arrow(ax, 0.20, 0.73, 0.36, 0.56, "", color=PURPLE, lw=1.4, zorder=2)
    badge(ax, 0.298, 0.616, 5, color=PURPLE)
    ax.text(0.175, 0.660, "$\\mathbf{r}(t)$ →\nselection / weight", fontsize=7.8,
            color=PURPLE, ha="center", style="italic", zorder=3)

    # (6) 合约 → SDN（遏制触发，文字置于箱体上方）
    arrow(ax, 0.66, 0.815, 0.72, 0.815, "", color=RED, lw=1.4, ls="--", zorder=2)
    badge(ax, 0.69, 0.808, 6, color=RED)
    ax.text(0.69, 0.972, "trigger $r_i<r_{\\rm q}$ (Eq. 12)", fontsize=8.0,
            color=RED, ha="center", style="italic", zorder=3)

    # (7) SDN → 攻击者设备（隔离，沿右缘竖直路径，避开中部图元）
    arrow(ax, 0.90, 0.73, 0.887, 0.19, "", color=RED, lw=1.5, ls="--", zorder=2)
    badge(ax, 0.903, 0.46, 7, color=RED)
    ax.text(0.937, 0.46, "isolate", fontsize=8.5, color=RED, rotation=90,
            ha="center", va="center", style="italic", zorder=3)

    # ---- 图例（图底部一行，避免遮挡任何图元）----
    ly = -0.030
    ax.text(0.03, ly, "Legend:", fontsize=8.0, fontweight="bold", va="center", zorder=3)
    leg = [(0.10, TXT, "-", "training / data flow"),
           (0.29, PURPLE, "-", "on-chain reputation"),
           (0.49, RED, "--", "control / isolation"),
           (0.68, BROWN, "-", "root reference")]
    for lx0, c, ls, t in leg:
        ax.plot([lx0, lx0 + 0.040], [ly, ly], color=c, lw=1.6, ls=ls, zorder=3)
        ax.text(lx0 + 0.050, ly, t, fontsize=7.8, va="center", zorder=3)

    fig.savefig(os.path.join(OUT, "fig1_architecture.pdf"), dpi=300, bbox_inches="tight")
    fig.savefig(os.path.join(OUT, "fig1_architecture.png"), dpi=300, bbox_inches="tight")
    plt.close(fig)
    print("fig1 done")


# ================= Fig 2: 单轮联邦交互时序图 =================
def fig2():
    fig, ax = plt.subplots(figsize=(11.4, 8.2))
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")

    actors = [("IoT Client $i$", 0.10), ("Edge Server", 0.36),
              ("Smart Contract", 0.60), ("Reputation\nLedger", 0.78), ("ONOS SDN", 0.93)]
    fills = [FILL["honest"], FILL["accent"], FILL["contract"], "#E8DAEF", FILL["ctrl"]]
    widths = [0.14, 0.15, 0.15, 0.13, 0.11]
    top, bot = 0.92, 0.06
    for (name, x), f, w in zip(actors, fills, widths):
        box(ax, x - w / 2, top, w, 0.05, name, f, fs=9, bold=True)
        ax.plot([x, x], [bot, top - 0.0], ls=(0, (4, 3)), color="#7F8C8D", lw=1.0, zorder=1)

    def msg(x1, x2, y, text, num, color="#2C3E50", ls="-"):
        arrow(ax, x1, y, x2, y, "", color=color, lw=1.5, ls=ls)
        ax.text((x1 + x2) / 2, y + 0.016, "(%s) %s" % (num, text), ha="center",
                fontsize=8.5, style="italic", color="#1B2631",
                path_effects=[pe.withStroke(linewidth=2.6, foreground="white")])

    def act(x, y, h, label, fill=FILL["gray"]):
        box(ax, x - 0.055, y - h, 0.11, h, label, fill, fs=8.0)

    ci, es, sc, rl, sd = [a[1] for a in actors]
    y = 0.88
    msg(es, ci, y, "broadcast $\\mathbf{w}_t$, $\\mathcal{S}_t$ (Eq. 11)", 1); y -= 0.065
    act(ci, y, 0.05, "local SGD\n(Eq. 2)", FILL["honest"]); y -= 0.08
    msg(ci, es, y, "submit $\\Delta_i$, $H(\\Delta_i)$", 2); y -= 0.065
    act(es, y, 0.065, "clip + evidence\n$s_i$ (Eqs. 4, 5)", "#FDEBD0"); y -= 0.095
    msg(es, sc, y, "tx: writeEvidence$(i, s_i)$", 3); y -= 0.065
    act(sc, y, 0.075, "Alg. 2: reward /\npenalty / decay\n(Eqs. 8–9)", FILL["contract"]); y -= 0.105
    arrow(ax, sc, y, rl, y, "", color="#2C3E50", lw=1.5)
    ax.text((sc + rl) / 2, y + 0.016, "(4) commit $r_i(t{+}1)$", ha="center",
            fontsize=8.5, style="italic",
            path_effects=[pe.withStroke(linewidth=2.6, foreground="white")]); y -= 0.065
    msg(rl, es, y, "read $\\mathbf{r}(t{+}1)$", 5, color="#6C3483"); y -= 0.065
    act(es, y, 0.055, "RWRA aggregate\n(Eq. 7)", FILL["accent"]); y -= 0.085
    msg(es, ci, y, "broadcast $\\mathbf{w}_{t+1}$", 6); y -= 0.065
    msg(sc, sd, y, "isolate$(i)$ if $r_i<r_{\\rm q}$ (Eq. 12)", 7, color="#922B21", ls="--"); y -= 0.055
    msg(sd, ci, y, "quarantine flow rule", 8, color="#922B21", ls="--")

    fig.savefig(os.path.join(OUT, "fig2_sequence.pdf"), dpi=300, bbox_inches="tight")
    fig.savefig(os.path.join(OUT, "fig2_sequence.png"), dpi=300, bbox_inches="tight")
    plt.close(fig)
    print("fig2 done")


# ================= Fig 3: 链上声誉管理流程（泳道 + 编号徽标 + 图例） =================
def fig3():
    fig, ax = plt.subplots(figsize=(11.2, 8.0))
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")

    actors = [("Edge Server", 0.14), ("Smart Contract", 0.44),
              ("Reputation\nLedger", 0.70), ("ONOS SDN", 0.87)]
    fills = [FILL["accent"], FILL["contract"], "#E8DAEF", FILL["ctrl"]]
    widths = [0.15, 0.16, 0.14, 0.11]
    top, bot = 0.92, 0.15
    for (name, x), f, w in zip(actors, fills, widths):
        box(ax, x - w / 2, top, w, 0.05, name, f, fs=9, bold=True)
        ax.plot([x, x], [bot, top], ls=(0, (4, 3)), color="#7F8C8D", lw=1.0, zorder=1)

    def msg(x1, x2, y, text, num, color="#2C3E50", ls="-"):
        arrow(ax, x1, y, x2, y, "", color=color, lw=1.5, ls=ls)
        ax.text((x1 + x2) / 2, y + 0.018, text, ha="center", fontsize=8.5,
                style="italic", color="#1B2631",
                path_effects=[pe.withStroke(linewidth=2.6, foreground="white")])
        badge(ax, (x1 + x2) / 2, y - 0.020, num, color)

    def act(x, y, h, label, fill=FILL["gray"], w=0.14):
        box(ax, x - w / 2, y - h, w, h, label, fill, fs=8.0)

    es, sc, rl, sd = [a[1] for a in actors]

    y = 0.86
    msg(es, sc, y, "writeEvidence$(i, s_i, H(\\Delta_i))$", 1); y -= 0.078
    act(sc, y, 0.11, "branch on $s_i$:\nreward (Eq. 8) /\npenalty (Eq. 9) /\ngrey zone",
        FILL["contract"], w=0.19); y -= 0.128
    msg(sc, rl, y, "commit $r_i(t{+}1)$", 2, color=PURPLE); y -= 0.072
    act(rl, y, 0.07, "decay $r_j(1-\\lambda_{\\rm dec})$\nfor $j \\notin \\mathcal{S}_t$ (Eq. 9)",
        "#E8DAEF", w=0.19); y -= 0.090
    msg(rl, es, y, "read $\\mathbf{r}(t{+}1)$ → selection (Eq. 11)", 3, color=PURPLE); y -= 0.076
    msg(sc, sd, y, "if $r_i<r_{\\rm q}$: containment event", 4, color=RED, ls="--"); y -= 0.068
    act(sd, y, 0.055, "install drop\nrule (isolate)", FILL["ctrl"], w=0.13); y -= 0.070

    # ---- 底部说明（填充留白，表达循环语义）----
    ax.text(0.5, 0.185, "(1)–(3) repeat each federated round;  (4) fires only on quarantine",
            fontsize=8.5, color="#5D6D7E", ha="center", va="center",
            style="italic", zorder=3)

    # ---- 图例（底部，填充留白）----
    ly = 0.088
    ax.text(0.045, ly, "Legend:", fontsize=8.0, fontweight="bold", va="center", zorder=3)
    lx = 0.14
    leg = [(TXT, "-", "evidence / commit"),
           (PURPLE, "-", "reputation read/write"),
           (RED, "--", "containment trigger")]
    for c, ls, t in leg:
        ax.plot([lx, lx + 0.05], [ly, ly], color=c, lw=1.6, ls=ls, zorder=3)
        ax.text(lx + 0.06, ly, t, fontsize=8.0, va="center", zorder=3)
        lx += 0.245

    fig.savefig(os.path.join(OUT, "fig3_repflow.pdf"), dpi=300, bbox_inches="tight")
    fig.savefig(os.path.join(OUT, "fig3_repflow.png"), dpi=300, bbox_inches="tight")
    plt.close(fig)
    print("fig3 done")


if __name__ == "__main__":
    fig1(); fig2(); fig3()
    print("architecture figures (Fig 1-3) done.")
