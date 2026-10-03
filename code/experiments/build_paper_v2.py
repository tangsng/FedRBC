#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
组装 paper v2（工程应用向，~12000 词）：
- 拼接 v2 章节文件
- 引用占位 [Xid] → IEEE 数字编号（按 v2 首次出现顺序）
- 从 results/tables + raw 回填实验数字占位符（X.XXX）
- 生成 references_ieee.md
输出：paper/paper_v2.md
"""
import os, re, json, glob, math, statistics as st

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
P = lambda *a: os.path.join(ROOT, *a)

# v2 引用顺序（按章节首次出现）
CITE_ORDER = [
    # §1 Intro
    "A1", "E1", "E2", "F1", "N0", "N1", "N2", "N3", "N4", "N5",
    "G1", "B1", "B2", "B6", "B5", "N16", "N11",
    # §3 Related
    "C1", "C2", "C3", "C4", "C5", "P0", "P1", "P2", "P3", "P4", "P5",
    "N6", "N9", "N7", "N8", "N10", "B3", "N12", "N13", "N14", "N15",
    "F2", "F4", "G2", "G3", "D1", "D2",
    # 其余（方法/评估引用）
    "A2", "A3", "A5", "B4", "H1", "N17",
]

SECTIONS = [
    ("paper/v2_abstract.md", None),
    ("paper/v2_intro.md", None),
    ("paper/v2_notation.md", None),
    ("paper/v2_sysmodel.md", None),
    ("paper/v2_related.md", None),
    ("paper/v2_related_ext.md", None),
    ("paper/v2_architecture.md", None),
    ("paper/v2_arch_ext.md", None),
    ("paper/v2_walkthrough.md", None),
    ("paper/v2_design.md", None),
    ("paper/v2_design_ext.md", None),
    ("paper/v2_rationale.md", None),
    ("paper/v2_implementation.md", None),
    ("paper/v2_deployment.md", None),
    ("paper/v2_testing_position.md", None),
    ("paper/v2_runbook.md", None),
    ("paper/v2_lessons.md", None),
    ("paper/v2_results.md", None),
    ("paper/v2_boundary.md", None),
    ("paper/v2_statsig.md", None),
    ("paper/v2_sensitivity.md", None),
    ("paper/v2_discussion.md", None),
    ("paper/v2_outlook.md", None),
    ("paper/v2_conclusion.md", None),
]

TITLE = """# FedRBC: Blockchain-Enabled Reputation-Weighted Robust Federated Learning for Privacy-Preserving Healthcare IoT Edge Networks

**Song Tang$^{1,2,3}$, Zhigang Jin$^{1,*}$**

$^{1}$School of Electrical and Information Engineering, Tianjin University, Tianjin, China
$^{2}$Institute of Applied Mathematics, Hebei Academy of Sciences, Shijiazhuang, China
$^{3}$Hebei Information Security Authentication Technology Innovation Center, Shijiazhuang, China
$^{*}$Corresponding author

**Funding:** This work was supported by the Hebei Provincial Science and Technology Program Project (Grant No. 25360301D).

---

"""

def fmt_authors(authors, max_n=6):
    def one(a):
        a = a.strip()
        if "," in a:
            family, given = a.split(",", 1)
            ini = " ".join(p[0] + "." for p in given.split() if p)
            return ("%s %s" % (ini, family.strip())).strip()
        parts = a.split()
        if len(parts) == 1:
            return a
        return "%s %s" % (" ".join(p[0] + "." for p in parts[:-1] if p), parts[-1])
    if len(authors) > max_n:
        return ", ".join(one(a) for a in authors[:max_n]) + " et al."
    return ", ".join(one(a) for a in authors)

def ieee_entry(e):
    a = fmt_authors(e.get("authors", []))
    t = e["title"].rstrip(".")
    cont = (e.get("container") or "").replace("&amp;", "&")
    year = e.get("year"); doi = e.get("doi", "")
    vol, issue, page = e.get("volume", ""), e.get("issue", ""), e.get("page", "")
    if "arxiv" in doi.lower():
        m = re.search(r"arxiv\.(.+)$", doi, re.I)
        return '%s, "%s," arXiv:%s, %s.' % (a, t, m.group(1) if m else cont, year)
    bits = []
    if vol: bits.append("vol. %s" % vol)
    if issue: bits.append("no. %s" % issue)
    if page: bits.append("pp. %s" % page)
    s = '%s, "%s," %s' % (a, t, cont if cont else "[source]")
    if bits:
        s += ", " + ", ".join(bits)
    s += ", %s" % year
    if doi:
        s += ", doi: %s" % doi
    return s + "."

def build_refmap():
    data = json.load(open(P("paper/references_verified.json"), encoding="utf-8"))
    by_id = {e["id"]: e for e in data["entries"]}
    id2num = {}
    refs = []
    for i, rid in enumerate(CITE_ORDER, 1):
        id2num[rid] = i
        refs.append("[%d] %s\n" % (i, ieee_entry(by_id[rid])))
    return id2num, refs

def replace_cites(text, id2num):
    """逐引用块处理：支持 [A1]、[A1, E1, E2]、[N0–N5]、[F1, N0–N5] 混合形态。
    映射到数字后，连续段合并为 a–b，不连续则逗号分隔。"""
    def expand_token(tok):
        tok = tok.strip()
        m = re.match(r"^([A-Z]+)(\d+)–([A-Z]+)(\d+)$", tok)
        if m and m.group(1) == m.group(3):
            nums = [id2num.get("%s%d" % (m.group(1), k))
                    for k in range(int(m.group(2)), int(m.group(4)) + 1)]
            return [n for n in nums if n]
        if re.match(r"^[A-Z]+\d+$", tok) and tok in id2num:
            return [id2num[tok]]
        return None
    def repl_block(m):
        inner = m.group(1)
        nums, ok = [], True
        for tok in inner.split(","):
            r = expand_token(tok)
            if r is None:
                ok = False
                break
            nums.extend(r)
        if not ok or not nums:
            return m.group(0)
        nums = sorted(set(nums))
        out, i = [], 0
        while i < len(nums):
            j = i
            while j + 1 < len(nums) and nums[j + 1] == nums[j] + 1:
                j += 1
            if j - i >= 2:
                out.append("%d–%d" % (nums[i], nums[j]))
            else:
                out.extend(str(nums[k]) for k in range(i, j + 1))
            i = j + 1
        return "[%s]" % ", ".join(out)
    return re.sub(
        r"\[((?:[A-Z]+\d+(?:–[A-Z]+\d+)?)(?:\s*,\s*[A-Z]+\d+(?:–[A-Z]+\d+)?)*)\]",
        repl_block, text)

# ---------- 实验数字回填 ----------
def raw_stat(method, alpha, beta, attack, tag, key="f1"):
    vals = []
    for f in glob.glob(P("results/raw/%s_a%s_b%s_%s_s*_summary.json" % (method, alpha, beta, attack))):
        d = json.load(open(f))
        if d["config"].get("tag", "") != tag:
            continue
        v = d["final"][key]
        if not (isinstance(v, float) and math.isnan(v)):
            vals.append(v)
    if not vals:
        return None, 0.0
    return (sum(vals) / len(vals), st.stdev(vals) if len(vals) > 1 else 0.0)

def fill_numbers(text):
    """回填 §7 骨架中的 X.XXX 占位（当前先保留占位，由终稿阶段替换）。"""
    return text

def main():
    id2num, refs = build_refmap()
    parts = [TITLE]
    for path, _ in SECTIONS:
        fp = P(path)
        if not os.path.exists(fp):
            print("⚠️ 缺章节:", path); continue
        txt = open(fp, encoding="utf-8").read()
        txt = replace_cites(txt, id2num)
        txt = fill_numbers(txt)
        parts.append(txt.rstrip() + "\n")
    # 附录：伪代码 + 证明
    algo = open(P("paper/algorithms_pseudocode.md"), encoding="utf-8").read()
    parts.append("\n# Appendix A. Algorithms\n\n" + algo)
    proof = open(P("paper/v2_appendix_b.md"), encoding="utf-8").read()
    parts.append("\n" + proof)
    parts.append("\n# References\n\n" + "\n".join(refs))
    out = "\n".join(parts)
    open(P("paper/paper_v2.md"), "w", encoding="utf-8").write(out)
    body = out[:out.index("# References")]
    words = len(re.findall(r"[A-Za-z][A-Za-z\-']*", body))
    print("paper_v2.md 生成：%d 英文词（含图题表格口径）" % words)
    words2 = len(re.findall(r"[A-Za-z][A-Za-z\-']*", "\n".join(
        l for l in body.split("\n") if not l.strip().startswith(("|", "!", "$$", "#")))))
    print("纯正文词数（估）: %d" % words2)

if __name__ == "__main__":
    main()
