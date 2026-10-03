#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 8 终检：公式/图表引用完整性、夸大用语、符号初查、一致性映射。"""
import re, sys

doc = open("paper/paper.md", encoding="utf-8").read()
body = doc[:doc.index("# References")]

issues = []

# ---- 1. 公式编号定义 vs 引用（含 parenthetical "(Eq. X)" 与范围 "Eqs. (a)–(b)"） ----
defined = sorted(set(int(x) for x in re.findall(r"\\tag\{(\d+)[a-z]?\}", body)))
cited = set(int(x) for x in re.findall(r"Eq\.?\s*\((\d+)[a-z]?\)", body))
cited |= set(int(x) for x in re.findall(r"\(Eq\.\s*(\d+)[a-z]?\)", body))
for m in re.finditer(r"Eqs\.\s*\((\d+)\)–\((\d+)\)", body):  # 范围引用展开
    a, b = int(m.group(1)), int(m.group(2))
    cited |= set(range(a, b + 1))
cited = sorted(cited)
uncited = [d for d in defined if d not in cited and d not in (3,)]
undef_cited = [c for c in cited if c not in defined]
print("公式编号已定义: %s" % defined)
print("公式正文被引用: %s" % cited)
if uncited:
    issues.append("已定义但未被引用公式: %s" % uncited)
if undef_cited:
    issues.append("引用了未定义公式: %s" % undef_cited)

# ---- 2. 图表引用完整性 ----
figs_cited = sorted(set(int(x) for x in re.findall(r"Fig\.?\s*(\d+)", body)))
tabs_cited = sorted(set(int(x) for x in re.findall(r"Table\s*(\d+)", body)))
figs_have = list(range(1, 9))
tabs_have = [1, 2, 3, 4, 5, 6, 7]
print("Fig 引用: %s（应有 1-8）" % figs_cited)
print("Table 引用: %s（应有 1-7）" % tabs_cited)
for f in figs_have:
    if f not in figs_cited:
        issues.append("Fig %d 未在正文引用" % f)
for t in tabs_have:
    if t not in tabs_cited:
        issues.append("Table %d 未在正文引用" % t)

# ---- 3. 夸大/禁用用语扫描 ----
hype = ["revolutionary", "first ever", "groundbreaking", "unprecedented", "state-of-the-art",
        "significantly outperforms", "far superior", "perfect", "novel approach"]
hits = []
for h in hype:
    for m in re.finditer(re.escape(h), body, re.I):
        hits.append((h, body[max(0, m.start()-40):m.start()+40].replace("\n", " ")))
if hits:
    for h, ctx in hits:
        issues.append("夸大/禁用用语 '%s': ...%s..." % (h, ctx))
print("夸大用语扫描: %d 处" % len(hits))

# ---- 4. 符号抽查（关键符号成对检查：首次出现带定义关键词） ----
sym_checks = [
    ("\\mathbf{w}_t", "global model"),
    ("r_i(t)", "reputation"),
    ("\\mathrm{MTTC}", "mean time to containment"),
]
for pat, desc in sym_checks:
    if pat not in body:
        issues.append("符号未出现: %s (%s)" % (pat, desc))
# 大小写混用检查：\lambda_dec vs \lambda_a 应共存且不混
if "\\lambda_{\\mathrm{dec}}" not in body:
    issues.append("λ_dec 缺失")

# ---- 5. 贡献-实验映射（关键词成对出现） ----
pairs = [("Theorem 1", "Fig. 3"), ("Proposition 1", "Fig. 2"),
         ("Proposition 2", "Fig. 8"), ("Theorem 2", "Fig. 7")]
for th, fg in pairs:
    if th not in body or fg not in body:
        issues.append("映射缺失: %s <-> %s" % (th, fg))

# ---- 6. 文献指标终核 ----
import json
data = json.load(open("paper/references_verified.json", encoding="utf-8"))
n = len(data["entries"]); nr = data["n_recent_2024plus"]; nt = data["n_top_tier"]
print("文献: 总数 %d (>=35:%s) | 2024+ %d (%.1f%%, >=50%%:%s) | top %d (>=5:%s)" % (
    n, n >= 35, nr, 100 * nr / n, nr / n >= 0.5, nt, nt >= 5))
cited_nums = set(int(x) for x in re.findall(r"\[(\d+)\]", body) if int(x) <= 100)
print("正文引用编号覆盖: %d/%d" % (len(cited_nums), n))

# ---- 7. 作者与基金 ----
for kw in ["Song Tang", "Zhigang Jin", "Tianjin University", "25360301D", "Hebei"]:
    if kw not in doc:
        issues.append("作者/基金缺失: %s" % kw)

print("\n=== 终检问题（%d 项）===" % len(issues))
for i, x in enumerate(issues, 1):
    print("%2d. %s" % (i, x))
if not issues:
    print("全部通过 ✅")
