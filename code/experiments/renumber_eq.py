#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修复方程 tag（references 已正确，只需把 tag 对齐到正确编号）。
正确目标（按内容）：
  3 Delta_root, 4 s_i, 10 T0, 11 density, 12 MTTC_edge, 13 MTTC_cloud, 14 convergence
当前 tag 是二次重排后的乱值，需按内容锚定修正。
"""
import re

files = [
    "paper/v2_abstract.md", "paper/v3_intro.md", "paper/v3_sysmodel.md",
    "paper/v3_framework.md", "paper/v3_eval.md", "paper/v3_discussion.md",
    "paper/algorithms_pseudocode.md", "paper/v2_appendix_b.md",
]

def fix(txt):
    # Delta_root tag -> 3（当前可能是 4）
    txt = re.sub(
        r"(\\Delta_\{?\\mathrm\{root\}?[^$]*?\{SGD\}[^$]*?)(\\tag\{\d+\})",
        lambda m: m.group(1) + r"\tag{3}", txt, count=1)
    return txt

# 因为锚定复杂，直接用唯一子串替换
subs_tags = [
    # (唯一子串, 正确 tag)
    (r"-\mathbf{w}_t, \tag{4}", r"-\mathbf{w}_t, \tag{3}"),       # Delta_root
    (r"\| \, \|\Delta_{\mathrm{root}}\|}. \tag{3}", r"\| \, \|\Delta_{\mathrm{root}}\|}. \tag{4}"),  # s_i
    (r"\ln(1-\kappa\gamma)} \right\rceil \tag{11}", r"\ln(1-\kappa\gamma)} \right\rceil \tag{10}"),  # T0
    (r"d_i = r_i(t)\, u_i / c_i \tag{12}", r"d_i = r_i(t)\, u_i / c_i \tag{11}"),  # density
    (r"\bar{t}_{\mathrm{chain}}. \tag{13}", r"\bar{t}_{\mathrm{chain}}. \tag{12}"),  # MTTC_edge
    (r"+ \bar{t}_{\mathrm{cloud}}, \tag{14}", r"+ \bar{t}_{\mathrm{cloud}}, \tag{13}"),  # MTTC_cloud
    (r"\tau_c G\, \tfrac{1}{\sqrt{T}}\right), \tag{10}", r"\tau_c G\, \tfrac{1}{\sqrt{T}}\right), \tag{14}"),  # convergence
]

# 修复被吃掉的括号
subs_paren = [
    (r"Eqs. 4, 5–7 combines", r"Eqs. 4, 5–7) combines"),
    (r"Eqs. 8–9 renders", r"Eqs. 8–9) renders"),
]

for f in files:
    txt = open(f, encoding="utf-8").read()
    orig = txt
    for old, new in subs_tags:
        txt = txt.replace(old, new)
    for old, new in subs_paren:
        txt = txt.replace(old, new)
    if txt != orig:
        open(f, "w", encoding="utf-8").write(txt)
        print("fixed", f)

print("done")
