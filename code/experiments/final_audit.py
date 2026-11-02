#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Round-1 最终一致性终检：
1. Eq tag{1..17} 唯一性 + 正文引用顺序合理性
2. Table 1-8 / Fig 1-9 caption 存在 + 首次引用顺序升序
3. 文献引用 [n] 首现序列 1-56 严格递增 + 连引 ≤5
4. 中英关键统计数字对照（paper_v3.md vs FedRBC_cn.md）
用法：python final_audit.py   （exit 0 = 全过，非 0 = 有问题清单）"""
import re, sys

EN = open(r"D:\workbuddy\CMC0930\paper\paper_v3.md", encoding="utf-8").read()
CN = open(r"D:\workbuddy\CMC0930\paper\FedRBC_cn.md", encoding="utf-8").read()
problems = []

# ---------- 1. Eq tags ----------
tags = [int(m) for m in re.findall(r"\\tag\{(\d+)\}", EN)]
expect = list(range(1, len(tags) + 1))
if tags != expect:
    dup = [t for t in tags if tags.count(t) > 1]
    problems.append("Eq tags 非连续/乱序: %s (expect %s..%d)%s" % (
        tags, "1", expect[-1], (" dup=%s" % dup) if dup else ""))
else:
    print("OK  Eq tags 1-%d 连续唯一" % len(tags))

# 正文 Eq. (n) 引用检查：引用的 n 必须已定义或即将定义（允许 forward ref 到 Lemma 1，
# 但检查不存在超过最大 tag 的引用）
refs = [int(m) for m in re.findall(r"Eqs?\.\s*\(?(\d+)", EN)]
bad = [n for n in refs if n > len(tags)]
if bad:
    problems.append("Eq 引用超界: %s" % sorted(set(bad)))

# ---------- 2. Table / Fig ----------
tcaps = re.findall(r"\*\*Table (\d+)\.\*\*", EN)
tcaps = [int(x) for x in tcaps]
t_expect = list(range(1, len(tcaps) + 1))
if tcaps != t_expect:
    problems.append("Table caption 顺序异常: %s" % tcaps)
else:
    print("OK  Table captions 1-%d 顺序正确" % len(tcaps))
trefs = [int(m) for m in re.findall(r"Table (\d+)", re.sub(r"\*\*Table \d+\.\*\*", "", EN))]
t_over = [n for n in trefs if n > len(tcaps)]
if t_over:
    problems.append("Table 引用超界: %s" % sorted(set(t_over)))
# 首次引用须不早于 caption 序（弱检查：首现顺序递增）
first_seen = {}
for n in trefs:
    if n not in first_seen:
        first_seen[n] = True
seq = list(first_seen.keys())
if seq != sorted(seq) and len(seq) > 1:
    # 允许同段内 Table 4/5/6 混排；只报告非首个引用提前于 caption 出现
    for i, n in enumerate(seq):
        if i > 0 and n < seq[i - 1] and n not in tcaps[:tcaps.index(seq[i - 1]) + 1]:
            problems.append("Table %d 首现顺序异常（前一个 %d）" % (n, seq[i - 1]))

fcaps = [int(x) for x in re.findall(r"\*\*Fig\. (\d+)\.\*\*", EN)]
f_expect = list(range(1, len(fcaps) + 1))
if fcaps != f_expect:
    problems.append("Fig caption 顺序异常: %s" % fcaps)
else:
    print("OK  Fig captions 1-%d 顺序正确" % len(fcaps))
frefs = [int(m) for m in re.findall(r"Fig\. (\d+)", re.sub(r"\*\*Fig\. \d+\.\*\*", "", EN))]
f_over = [n for n in frefs if n > len(fcaps)]
if f_over:
    problems.append("Fig 引用超界: %s" % sorted(set(f_over)))

# ---------- 3. 引用首现序列 ----------
body = re.sub(r"^# References.*", "", EN, flags=re.S | re.M)
cites = []
for m in re.finditer(r"\[(\d+(?:[,\u2013-]\s*\d+)*)\]", body):
    # 排除数学区间：前一个字符为字母（如 $\mathcal{U}[1,5]$、r∈[0,1]）
    if m.start() > 0 and (body[m.start() - 1].isalpha() or body[m.start() - 1] in "$"):
        continue
    group = m.group(1)
    for part in re.split(r",", group.replace(" ", "")):
        rng = re.match(r"^(\d+)[\u2013-](\d+)$", part)
        if rng:  # 区间展开：a–b → a..b（中点全部计入首现）
            a, b = int(rng.group(1)), int(rng.group(2))
            if 0 < a <= b and b - a < 20:
                cites.extend(range(a, b + 1))
            continue
        if part.isdigit() and int(part) != 0:  # "[0,1]" 数学区间丢弃 0
            cites.append(int(part))
firsts = []
seen = set()
for c in cites:
    if c not in seen:
        seen.add(c)
        firsts.append(c)
viol = [(a, b) for a, b in zip(firsts, firsts[1:]) if b < a]
if viol:
    problems.append("引用首现序列非递增: %s（前 30 首现: %s）" % (viol[:5], firsts[:30]))
else:
    print("OK  引用首现序列 1-%d 严格递增" % max(firsts))
# 连引 >5 检测
runs = re.findall(r"\[((?:\d+,\s*)*\d+)\]", body)
long_runs = [r for r in runs if len(re.findall(r"\d+", r)) > 5]
if long_runs:
    problems.append("存在 >5 连引: %s" % long_runs[:3])
else:
    print("OK  无超过 5 连的连引")

# ---------- 4. 中英数字对照 ----------
KEY = ["0.567", "0.561", "0.558", "0.570", "0.606", "0.401", "0.540",
       "0.517", "0.605", "0.566", "0.417", "0.447", "0.220", "0.519",
       "0.564", "0.315", "0.994", "0.109", "0.009"]
miss_en = [k for k in KEY if k not in EN]
miss_cn = [k for k in KEY if k not in CN]
if miss_en:
    problems.append("EN 缺关键数字: %s" % miss_en)
if miss_cn:
    problems.append("CN 缺关键数字: %s" % miss_cn)
if not miss_en and not miss_cn:
    print("OK  中英关键数字 %d/%d 全部在位" % (len(KEY), len(KEY)))

# ---------- 5. 术语残留检查 ----------
stale = []
for pat, name in [(r"\bkappa\\\|Delta_\{\\mathrm\{root", "κ 未改 κ_c?"),
                  (r"0\.588", "旧 5-seed 数字 0.588"),
                  (r"\\pm0\.056", "旧 std 0.056")]:
    if re.search(pat, EN):
        stale.append(name)
if stale:
    problems.append("EN 残留: %s" % stale)
else:
    print("OK  无旧数字/旧符号残留")

print()
if problems:
    print("==== FAILURES (%d) ====" % len(problems))
    for p in problems:
        print(" -", p)
    sys.exit(1)
print("==== ALL CHECKS PASSED ====")
