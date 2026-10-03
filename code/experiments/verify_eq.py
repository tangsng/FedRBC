#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""最终一致性校验：方程 tag 与引用。"""
import re, glob

files = glob.glob("paper/v3_*.md") + [
    "paper/v2_abstract.md", "paper/algorithms_pseudocode.md", "paper/v2_appendix_b.md",
]

tags = set()
refs = set()
for f in files:
    t = open(f, encoding="utf-8").read()
    for m in re.findall(r"\\tag\{(\d+)\}", t):
        tags.add(int(m))
    for m in re.findall(r"Eq\.\s*\((\d+)\)", t):
        refs.add(int(m))
    for m in re.findall(r"Eq\.\s*(\d+)(?![0-9])", t):
        refs.add(int(m))
    for m in re.findall(r"Eqs\.\s*\(?([0-9,\s\u2013\-]+)\)?", t):
        for p in m.split(","):
            mm = re.match(r"(\d+)\s*[\u2013\-]\s*(\d+)", p.strip())
            if mm:
                refs.update(range(int(mm.group(1)), int(mm.group(2)) + 1))
            elif p.strip().isdigit():
                refs.add(int(p.strip()))

print("定义:", sorted(tags))
print("引用:", sorted(refs))
print("引用未定义(应为空):", sorted(refs - tags))
print("定义未引用(可容忍):", sorted(tags - refs))

# 语义抽查：确认关键引用指向正确
checks = {
    "paper/v3_sysmodel.md": [("tag{3}", "Delta_root"), ("tag{1}", "F"), ("tag{2}", "Delta_i")],
    "paper/v3_framework.md": [("tag{4}", "s_i"), ("tag{6}", "q"), ("tag{10}", "T0"),
                              ("tag{11}", "density"), ("tag{12}", "edge"), ("tag{13}", "cloud"),
                              ("tag{14}", "convergence")],
}
print("\n=== 语义抽查 ===")
for f, items in checks.items():
    t = open(f, encoding="utf-8").read()
    for tag, kw in items:
        # 找到 tag 所在的完整公式行
        for line in t.split("\n"):
            if tag in line:
                print(f"  {f}: {tag} -> {'OK' if kw in line else 'MISMATCH'} ({line[:60]}...)")
                break
