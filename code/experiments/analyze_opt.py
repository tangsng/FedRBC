#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""分析 FedRBC 改进 E 扫描结果。"""
import os, json, glob, statistics as st
from collections import defaultdict

RAW = os.path.join(os.path.dirname(__file__), "..", "..", "results", "raw")

def main():
    files = glob.glob(os.path.join(RAW, "fedrbc_*_e_*_*_summary.json"))
    if not files:
        print("未找到 e-scan 结果"); return
    groups = defaultdict(list)
    for f in files:
        d = json.load(open(f))
        c = d["config"]
        cfgtag = c["tag"].split("_")[1]          # base/e1/e2/e12/e12b
        beta, alpha = c["beta"], c["alpha"]
        if beta == 0.3:
            scene = "s1_b30"
        elif beta == 0.0:
            scene = "s2_clean"
        else:
            scene = "s4_b20"
        groups[(cfgtag, scene)].append(d)

    print("=== 改进 E 验证（final F1 / AUC / Acc, mean±std）===\n")
    for scene, sname in [("s1_b30", "β=30% 高强度"),
                          ("s2_clean", "β=0 攻击自由"),
                          ("s4_b20", "β=20% 主配置(必须守)")]:
        print("### %s (%s) ###" % (scene, sname))
        rows = []
        for (cfgtag, sc), ds in groups.items():
            if sc != scene:
                continue
            f1 = [d["final"]["f1"] for d in ds]
            auc = [d["final"]["auc"] for d in ds]
            acc = [d["final"]["acc"] for d in ds]
            rows.append((cfgtag, len(ds),
                         st.mean(f1), st.stdev(f1) if len(f1) > 1 else 0,
                         st.mean(auc), st.mean(acc)))
        rows.sort(key=lambda r: -r[2])
        print("  config    n   F1(mean±std)     AUC      Acc")
        for cfgtag, n, f1m, f1s, auc, acc in rows:
            mark = "  <-- baseline" if cfgtag == "base" else ""
            print("  %-8s %d   %.3f±%.3f   %.3f   %.3f%s" % (cfgtag, n, f1m, f1s, auc, acc, mark))
        print()

if __name__ == "__main__":
    main()
