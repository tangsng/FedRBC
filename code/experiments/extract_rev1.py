#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Round-1 数据提取：汇总 results/raw 下全部 rev1* 结果（b1+b2+b3），生成
论文表格与 rebuttal 所需的统计（mean±std、95%CI、Holm 校正 p 值）。

用法（V100）：python3 experiments/extract_rev1.py [--raw results/raw] [--out results/rev1]
输出：
  rev1_report.md   人读汇总（每组的 mean±std / n / per-seed / Holm p）
  rev1_main.csv    主表长表（method×attack×seed 全部指标 + Holm 校正）
  rev1_groups.csv  其余组（dp/lie/bd/rp/abmemory/sens/n/b50/ab/upper）长表
"""
import os, sys, json, glob, argparse, math
import statistics as st

try:
    from scipy import stats as sps
except Exception:
    sps = None  # t 检验退化为无


def ms(vals, ddof=1):
    vals = [v for v in vals if v is not None and v == v]
    if not vals:
        return (float("nan"), float("nan"), 0)
    m = st.mean(vals)
    s = st.stdev(vals) if len(vals) > 1 else 0.0
    return (m, s, len(vals))


def ci95(m, s, n):
    if n < 2 or s == 0:
        return float("nan")
    t = {2: 12.706, 3: 4.303, 4: 3.182, 5: 2.776, 6: 2.571, 7: 2.447,
         8: 2.365, 9: 2.306, 10: 2.262, 15: 2.145}.get(n, 1.96)
    return t * s / math.sqrt(n)


def welch(a, b):
    if sps is None or len(a) < 2 or len(b) < 2:
        return float("nan")
    t, p = sps.ttest_ind(a, b, equal_var=False)
    return p


def holm(pvals):
    """Holm step-down: 返回校正后 p（与顺序无关的标记法：p_adj = max_{j<=i}(p_(j)*m/(m-j+1))，截 1）."""
    m = len(pvals)
    idx = sorted(range(m), key=lambda i: pvals[i] if pvals[i] == pvals[i] else 1.0)
    adj = [0.0] * m
    run = 0.0
    for rank, i in enumerate(idx):
        p = pvals[i] if pvals[i] == pvals[i] else 1.0
        v = min(1.0, (m - rank) * p)
        run = max(run, v)
        adj[i] = run
    return adj


def main():
    ap = argparse.ArgumentParser()
    here = os.path.dirname(os.path.abspath(__file__))
    ap.add_argument("--raw", default=os.path.join(here, "..", "..", "results", "raw"))
    ap.add_argument("--out", default=os.path.join(here, "..", "..", "results", "rev1"))
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)

    files = sorted(glob.glob(os.path.join(a.raw, "*_summary.json")))
    recs = []
    for f in files:
        try:
            d = json.load(open(f))
        except Exception as e:
            print("SKIP corrupt:", f, e)
            continue
        c = d.get("config", {})
        if c.get("dataset", "wustl") == "ciciot":
            continue  # 第二数据集单独提取
        tag = c.get("tag", "")
        if not (tag.startswith("rev1") or tag == "v5" or d["run_name"].startswith("centralized")):
            continue  # v7/bl 旧存档与其余历史 tag 不收；v5 收（主表 42-46 与 no-attack）
        fin = d.get("final", {})
        recs.append(dict(
            run=d["run_name"], file=os.path.basename(f), tag=tag,
            method=c.get("method", ""), attack=c.get("attack", "none"),
            seed=c.get("seed", -1), beta=c.get("beta", 0.3), alpha=c.get("alpha", 0.5),
            n_clients=c.get("n_clients", 20), root_size=c.get("root_size", 500),
            dp_sigma=c.get("dp_sigma", 0.0), root_poison=c.get("root_poison", 0.0),
            soft_T=c.get("soft_T", 0.3), tau_rel=c.get("tau_rel", 2.0),
            theta_h=c.get("theta_h", 0.3), k_per_round=c.get("k_per_round", 10),
            memory=c.get("memory", True),
            f1=fin.get("f1"), acc=fin.get("acc"), auc=fin.get("auc"),
            asr=fin.get("asr"), best_f1=d.get("best_f1"),
        ))
    print("loaded %d rev1 runs" % len(recs))

    # ---------- 分组 ----------
    def default_profile(r, beta=None):
        """主表默认配置指纹（alpha=0.5, K=10, 20 clients, 500 root,
        无 DP/无 root-poison/有记忆/默认 T_s/tau_rel/theta_h）——用于把 v5 旧主表
        数据与 rev1 新跑合并，同时排除 v5 时期的 β/α 扫描。基线方法的
        soft_T/tau_rel 在 v5 config 中为 None（参数不适用），按默认放行。
        beta=None 跳过 beta 检查（no-attack 上界场景 β=0.0）。"""
        return ((beta is None or r["beta"] == beta) and r["alpha"] == 0.5
                and r["n_clients"] == 20
                and (r["dp_sigma"] or 0) == 0 and (r["root_poison"] or 0) == 0
                and r["memory"] is not False
                and r["soft_T"] in (None, 0.3) and r["tau_rel"] in (None, 2.0)
                and r["theta_h"] in (None, 0.3) and r["k_per_round"] in (None, 10)
                and r["root_size"] in (None, 500))

    def grp(r):
        t = r["tag"]
        name = r["run"]
        if name.startswith("centralized"):
            return "centralized"
        # b1 消融 tag 是 "rev1-ab_clip"（下划线，历史两次命名不一致的坑）
        if "rev1-ab-" in t or t.startswith("rev1_ab_") or t.startswith("rev1-ab_"):
            return "ablation"
        # no-attack 上界：beta=0.0（无攻击时 beta 无意义，跳过 beta 检查）
        if t in ("rev1", "v5") and r["attack"] == "none" and default_profile(r, beta=None):
            return "upper_noattack"
        if t in ("rev1", "v5") and default_profile(r, beta=0.3) and r["attack"] in (
                "sign_flip", "sybil", "label_flip"):
            return "main"
        if t.startswith("rev1_dp"):
            return "dp"
        if t == "rev1_lie":
            return "lie"
        if t == "rev1_bd":
            return "bd"
        if t.startswith("rev1_rp"):
            return "root_poison"
        if t == "rev1_abmemory":
            return "abmemory"
        if t.startswith("rev1_sens"):
            return "sens"
        if t.startswith("rev1_n") and t != "rev1":
            return "scaling"
        if t == "rev1_b50":
            return "b50"
        return "other:" + t

    for r in recs:
        r["group"] = grp(r)

    # ---------- 主表 + Holm ----------
    main_rows = [r for r in recs if r["group"] == "main"]
    attacks = ["sign_flip", "sybil", "label_flip"]
    methods = ["fedrbc", "fltrust", "krum", "trimmed_mean", "eiffel", "raid", "fedgt"]
    report = ["# rev1 extraction report\n"]
    report.append("## Main table (tag=rev1, F1 mean±std [95% CI], n)\n")
    report.append("| method | " + " | ".join(attacks) + " |")
    report.append("|---|" + "---|" * len(attacks))
    main_cell = {}
    for m in methods:
        cells = []
        for atk in attacks:
            vals = [r["f1"] for r in main_rows if r["method"] == m and r["attack"] == atk]
            mm, ss, n = ms(vals)
            main_cell[(m, atk)] = vals
            cells.append("%.3f±%.3f [%.3f,%.3f] n=%d" % (mm, ss, mm - ci95(mm, ss, n), mm + ci95(mm, ss, n), n))
        report.append("| %s | %s |" % (m, " | ".join(cells)))

    # Holm 校正：每攻击 FedRBC vs 每基线（Welch t）
    if sps is not None:
        report.append("\n## Holm-corrected p-values (Welch t-test, FedRBC vs baseline, per attack)\n")
        allp, label = [], []
        for atk in attacks:
            for m in methods[1:]:
                p = welch(main_cell[("fedrbc", atk)], main_cell[(m, atk)])
                allp.append(p)
                label.append((m, atk))
        adj = holm(allp)
        report.append("| baseline | attack | p_raw | p_holm |")
        report.append("|---|---|---|---|")
        for (m, atk), p, pa in zip(label, allp, adj):
            report.append("| %s | %s | %.4f | %.4f |" % (m, atk, p, pa))

    # ---------- 各组汇总 ----------
    def dump_group(gname, keyfn, cols=None):
        rows = [r for r in recs if r["group"] == gname]
        if not rows:
            return
        report.append("\n## Group: %s (%d runs)\n" % (gname, len(rows)))
        keys = {}
        for r in rows:
            k = keyfn(r)
            keys.setdefault(k, []).append(r)
        report.append("| key | F1 mean±std (n) | AUC | ASR | per-seed F1 |")
        report.append("|---|---|---|---|---|")
        for k in sorted(keys, key=str):
            rs = keys[k]
            f1s = [r["f1"] for r in rs]
            aucs = [r["auc"] for r in rs]
            asrs = [r["asr"] for r in rs if r["asr"] is not None]
            mm, ss, n = ms(f1s)
            am, a_, _ = ms(aucs)
            sm, s_, _ = ms(asrs)
            per = ", ".join("s%d=%.3f" % (r["seed"], r["f1"] or float("nan")) for r in sorted(rs, key=lambda x: x["seed"]))
            report.append("| %s | %.3f±%.3f (%d) | %.3f | %s | %s |" % (
                str(k), mm, ss, n, am, ("%.3f" % sm) if asrs else "-", per))

    dump_group("dp", lambda r: (r["method"], r["attack"], r["dp_sigma"]))
    dump_group("lie", lambda r: (r["method"],))
    dump_group("bd", lambda r: (r["method"],))
    dump_group("root_poison", lambda r: (r["method"], r["attack"], r["root_poison"]))
    dump_group("abmemory", lambda r: (r["attack"],))
    dump_group("sens", lambda r: (r["tag"].replace("rev1_sens_", ""),))
    dump_group("scaling", lambda r: (r["method"], r["n_clients"]))
    dump_group("b50", lambda r: (r["method"], r["attack"]))
    dump_group("ablation", lambda r: (r["tag"].replace("rev1-ab-", "").replace("rev1_ab_", ""), r["attack"]))
    dump_group("upper_noattack", lambda r: (r["method"], r["beta"]))
    dump_group("centralized", lambda r: ("centralized",))

    # no-attack fedrbc（v5 tag 呢？主 no-attack 是 rev1 tag 吗——b1 的 fedavg no-attack tag=rev1；fedrbc no-attack 的 v5 数据 tag 是什么）
    report.append("\n## per-group run counts\n")
    from collections import Counter
    for g, c in sorted(Counter(r["group"] for r in recs).items()):
        report.append("- %s: %d" % (g, c))

    rep = "\n".join(report)
    open(os.path.join(a.out, "rev1_report.md"), "w", encoding="utf-8").write(rep)
    print(rep[:3000])
    print("... full report ->", os.path.join(a.out, "rev1_report.md"))

    # ---------- CSV ----------
    import csv as csvmod
    with open(os.path.join(a.out, "rev1_all.csv"), "w", newline="", encoding="utf-8") as f:
        w = csvmod.DictWriter(f, fieldnames=list(recs[0].keys()) if recs else ["run"])
        w.writeheader()
        for r in recs:
            w.writerow(r)
    print("csv ->", os.path.join(a.out, "rev1_all.csv"))


if __name__ == "__main__":
    main()
