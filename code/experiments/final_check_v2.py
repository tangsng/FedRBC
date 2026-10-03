#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""paper v2 终检：公式编号、图表引用、夸大用语、文献引用一致性、关键数字回查。"""
import re, os, json, glob, math, statistics as st

doc = open("paper/paper_v2.md", encoding="utf-8").read()
body = doc[:doc.index("# References")]
issues = []

# ---- 1. 公式编号定义 vs 引用 ----
defined = sorted(set(int(x) for x in re.findall(r"\\tag\{(\d+)[a-z]?\}", body)))
cited = set(int(x) for x in re.findall(r"Eq\.?\s*\((\d+)[a-z]?\)", body))
cited |= set(int(x) for x in re.findall(r"\(Eq\.\s*(\d+)[a-z]?\)", body))
cited |= set(int(x) for x in re.findall(r"Eq\.\s*(\d+)[a-z]?\b", body))  # Eq. 20 无括号形式
for m in re.finditer(r"Eqs\.\s*\((\d+)\)–\((\d+)\)", body):
    cited |= set(range(int(m.group(1)), int(m.group(2)) + 1))
cited = sorted(cited)
print("公式已定义:", defined)
print("公式被引用:", cited)
gaps = [d for d in defined if d not in cited and d not in (2, 3)]
undef = [c for c in cited if c not in defined]
if gaps:
    issues.append("已定义未引用公式: %s" % gaps)
if undef:
    issues.append("引用未定义公式: %s" % undef)

# ---- 2. 图表引用 ----
figs_cited = sorted(set(int(x) for x in re.findall(r"Fig\.\s*(\d+)", body)))
tabs_cited = sorted(set(int(x) for x in re.findall(r"Table\s*(\d+)", body)))
print("Fig 引用:", figs_cited, "（应有 1-10）")
print("Table 引用:", tabs_cited, "（应有 1-6）")
for f in range(1, 11):
    if f not in figs_cited:
        issues.append("Fig %d 未引用" % f)
for t in range(1, 7):
    if t not in tabs_cited:
        issues.append("Table %d 未引用" % t)

# ---- 3. 夸大用语 ----
hype = ["revolutionary", "first ever", "groundbreaking", "unprecedented",
        "significantly outperforms", "far superior", "perfect", "novel approach",
        "state-of-the-art"]
hits = 0
for h in hype:
    for m in re.finditer(re.escape(h), body, re.I):
        hits += 1
        issues.append("夸大用语 '%s': ...%s..." % (h, body[max(0, m.start()-40):m.start()+40].replace("\n", " ")))
print("夸大用语:", hits)

# ---- 4. 文献引用编号一致性（支持复合块 [a, b, c] 与范围 [a–b]） ----
ref_block = doc[doc.index("# References"):]
n_refs = len(re.findall(r"^\[\d+\]", ref_block, re.M))
cited_nums = set()
for m in re.finditer(r"\[([0-9][0-9,\s–]*)\]", body):
    for part in m.group(1).split(","):
        part = part.strip()
        if "–" in part:
            a, b = part.split("–")
            if a.strip().isdigit() and b.strip().isdigit():
                cited_nums |= set(range(int(a), int(b) + 1))
        elif part.isdigit():
            cited_nums.add(int(part))
cited_nums = {n for n in cited_nums if 1 <= n <= n_refs}
print("文献条数:", n_refs, "| 正文引用编号覆盖: %d/%d" % (len(cited_nums), n_refs))
over = [n for n in cited_nums if n > n_refs]
if over:
    issues.append("引用编号超出文献列表: %s" % over)
missing = [n for n in range(1, n_refs + 1) if n not in cited_nums]
if missing:
    issues.append("文献未被正文引用: %s" % missing)

# ---- 5. 关键数字回查（Table 5 vs raw） ----
print("\n--- 数字回查 ---")
T = {"fedrbc": "v7", "raid": "bl", "fedgt": "bl", "eiffel": "bl"}
def ms(m, atk, k="f1"):
    fs = [f for f in glob.glob("results/raw/%s_a0.5_b0.3_%s_s*_summary.json" % (m, atk))]
    fs = [f for f in fs if json.load(open(f))["config"].get("tag", "") == T[m]]
    v = [json.load(open(f))["final"][k] for f in fs]
    v = [x for x in v if not (isinstance(x, float) and math.isnan(x))]
    return (st.mean(v), st.stdev(v) if len(v) > 1 else 0) if v else (float("nan"), 0)
PAPER5 = {
    ("sign_flip", "fedrbc"): (0.604, 0.113), ("sign_flip", "eiffel"): (0.468, 0.117),
    ("sign_flip", "fedgt"): (0.414, 0.367), ("sign_flip", "raid"): (0.214, 0.370),
    ("sybil", "fedrbc"): (0.578, 0.108), ("sybil", "fedgt"): (0.317, 0.275),
    ("sybil", "raid"): (0.138, 0.208), ("sybil", "eiffel"): (0.0, 0.0),
    ("label_flip", "fedrbc"): (0.505, 0.156), ("label_flip", "fedgt"): (0.494, 0.272),
    ("label_flip", "raid"): (0.417, 0.331), ("label_flip", "eiffel"): (0.429, 0.230),
}
bad = 0
for (atk, m), (pm, ps) in PAPER5.items():
    rm, rs = ms(m, atk)
    if math.isnan(rm) or abs(rm - pm) > 0.005:
        issues.append("Table5 数字不符 %s/%s: 论文 %.3f vs raw %.3f" % (atk, m, pm, rm))
        bad += 1
print("Table5 回查: %d/%d 一致" % (12 - bad, 12))

# ---- 6. 作者与基金 ----
for kw in ["Song Tang", "Zhigang Jin", "Tianjin University", "25360301D", "Hebei"]:
    if kw not in doc:
        issues.append("作者/基金缺失: %s" % kw)

print("\n=== 终检问题（%d 项）===" % len(issues))
for i, x in enumerate(issues, 1):
    print("%2d. %s" % (i, x))
if not issues:
    print("全部通过 ✅")
