#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""paper v3 终检：公式、图表引用、夸大用语、文献一致性、Table 4 数字回查。"""
import re, os, json, glob, math, statistics as st

doc = open("paper/paper_v3.md", encoding="utf-8").read()
body = doc[:doc.index("# References")]
issues = []

# ---- 1. 公式 ----
defined = sorted(set(int(x) for x in re.findall(r"\\tag\{(\d+)[a-z]?\}", body)))
cited = set(int(x) for x in re.findall(r"Eq\.?\s*\((\d+)[a-z]?\)", body))
cited |= set(int(x) for x in re.findall(r"\(Eq\.\s*(\d+)[a-z]?\)", body))
for m in re.finditer(r"Eqs\.\s*\((\d+)\)–\((\d+)\)", body):
    cited |= set(range(int(m.group(1)), int(m.group(2)) + 1))
cited = sorted(cited)
print("公式已定义:", defined)
print("公式被引用:", cited)
gaps = [d for d in defined if d not in cited]
undef = [c for c in cited if c not in defined]
if gaps:
    issues.append("已定义未引用公式: %s" % gaps)
if undef:
    issues.append("引用未定义公式: %s" % undef)

# ---- 2. 图表引用 ----
figs_cited = sorted(set(int(x) for x in re.findall(r"Fig\.\s*(\d+)", body)))
tabs_cited = sorted(set(int(x) for x in re.findall(r"Table\s*(\d+)", body)))
print("Fig 引用:", figs_cited, "（应有 1-9）")
print("Table 引用:", tabs_cited, "（应有 1-5）")
for f in range(1, 10):
    if f not in figs_cited:
        issues.append("Fig %d 未引用" % f)
for t in range(1, 6):
    if t not in tabs_cited:
        issues.append("Table %d 未引用" % t)
figs_embedded = re.findall(r"!\[Fig\. (\d+)\]", body)
print("图片嵌入:", figs_embedded)
if len(figs_embedded) != 9:
    issues.append("图片嵌入数量 %d ≠ 9" % len(figs_embedded))

# ---- 3. 夸大用语 ----
hype = ["revolutionary", "first ever", "groundbreaking", "unprecedented",
        "significantly outperforms", "far superior", "perfect", "novel approach",
        "state-of-the-art"]
for h in hype:
    for m in re.finditer(re.escape(h), body, re.I):
        issues.append("夸大用语 '%s': ...%s..." % (h, body[max(0, m.start()-40):m.start()+40].replace("\n", " ")))

# ---- 4. 文献 ----
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
print("文献条数:", n_refs, "| 覆盖: %d/%d" % (len(cited_nums), n_refs))
missing = [n for n in range(1, n_refs + 1) if n not in cited_nums]
if missing:
    issues.append("文献未被正文引用: %s" % missing)
residual = re.findall(r"\[[A-Z]+\d+[^\]]*\]", body)
if residual:
    issues.append("残留占位: %s" % residual[:5])

# ---- 5. Table 4 数字回查 ----
T = {"fedrbc": "v5", "raid": "v5", "fedgt": "v5", "eiffel": "v5"}
def ms(m, atk, k="f1"):
    fs = [f for f in glob.glob("results/raw/%s_a0.5_b0.3_%s_s*_summary.json" % (m, atk))]
    fs = [f for f in fs if json.load(open(f))["config"].get("tag", "") == T[m]]
    v = [json.load(open(f))["final"][k] for f in fs]
    v = [x for x in v if not (isinstance(x, float) and math.isnan(x))]
    return (st.mean(v), st.stdev(v) if len(v) > 1 else 0) if v else (float("nan"), 0)
PAPER = {
    ("sign_flip", "fedrbc"): (0.588, 0.062), ("sign_flip", "eiffel"): (0.502, 0.097),
    ("sign_flip", "fedgt"): (0.190, 0.258), ("sign_flip", "raid"): (0.223, 0.249),
    ("sybil", "fedrbc"): (0.570, 0.056), ("sybil", "fedgt"): (0.142, 0.285),
    ("sybil", "raid"): (0.128, 0.167), ("sybil", "eiffel"): (0.089, 0.122),
    ("label_flip", "fedrbc"): (0.561, 0.057), ("label_flip", "fedgt"): (0.252, 0.262),
    ("label_flip", "raid"): (0.405, 0.263), ("label_flip", "eiffel"): (0.454, 0.169),
}
bad = 0
for (atk, m), (pm, ps) in PAPER.items():
    rm, rs = ms(m, atk)
    if math.isnan(rm) or abs(rm - pm) > 0.005:
        issues.append("Table4 数字不符 %s/%s: 论文 %.3f vs raw %.3f" % (atk, m, pm, rm))
        bad += 1
print("Table4 回查: %d/12 一致" % (12 - bad))

# ---- 6. 作者基金 ----
for kw in ["Song Tang", "Zhigang Jin", "Tianjin University", "25360301D"]:
    if kw not in doc:
        issues.append("作者/基金缺失: %s" % kw)

print("\n=== 终检问题（%d 项）===" % len(issues))
for i, x in enumerate(issues, 1):
    print("%2d. %s" % (i, x))
if not issues:
    print("全部通过 ✅")
