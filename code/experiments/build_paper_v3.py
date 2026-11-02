#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
组装 paper v3（CMC 学术版，7 章制，≤12000 词）：
1 Introduction（含 Related Work + Table 1）
2 System Model and Assumptions
3 Problem Formulation
4 Proposed FedRBC Framework
5 Performance Evaluation
6 Discussion and Limitations
7 Conclusion
Appendix A/B + References
"""
import os, re, json, glob, math, statistics as st

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
P = lambda *a: os.path.join(ROOT, *a)

# v3 引用顺序（按章节首次出现；N16/DGF 已删，新增 N18/N19/N20/N21）
CITE_ORDER = [
    # §1 Intro: FL 定义与医疗 IDS（F2/F4 为 TON_IoT、CICIoT2023 数据集文献）
    "A1", "E1", "E2", "F1", "N0", "N1", "N2", "N3", "N4", "N5",
    "G1",
    # §1 理论背景与三类 gap
    "B1", "B2", "B6", "B4", "H1", "A2", "A3", "A5",
    "B5", "N11",
    # §1 blockchain FL
    "C1", "C2", "C3", "C4", "C5", "P0", "P1", "P2", "P3", "P4", "P5",
    "N23", "N24",
    "N6", "N9", "B3", "N7", "N8", "N10",
    "N22", "N21", "N19", "N18", "N20", "N12", "N13", "N14", "N15", "N17",
    "F2", "F4",
    # §4 framework SDN / §6 discussion
    "G2", "G3", "D1", "D2",
]

SECTIONS = [
    "paper/v2_abstract.md",
    "paper/v3_intro.md",
    "paper/v3_sysmodel.md",
    "paper/v3_framework.md",
    "paper/v3_eval.md",
    "paper/v3_discussion.md",
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
    id2num, refs = {}, []
    for i, rid in enumerate(CITE_ORDER, 1):
        id2num[rid] = i
        refs.append("[%d] %s\n" % (i, ieee_entry(by_id[rid])))
    return id2num, refs

def replace_cites(text, id2num):
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
        nums, ok = [], True
        for tok in m.group(1).split(","):
            r = expand_token(tok)
            if r is None:
                ok = False; break
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

def main():
    id2num, refs = build_refmap()
    parts = [TITLE]
    for path in SECTIONS:
        txt = open(P(path), encoding="utf-8").read()
        parts.append(replace_cites(txt, id2num).rstrip() + "\n")
    # 附录
    algo = open(P("paper/algorithms_pseudocode.md"), encoding="utf-8").read()
    parts.append("\n# Appendix A. Algorithms\n\n" + algo)
    proof = open(P("paper/v2_appendix_b.md"), encoding="utf-8").read()
    parts.append("\n" + proof)
    parts.append("\n# References\n\n" + "\n".join(refs))
    out = "\n".join(parts)
    open(P("paper/paper_v3.md"), "w", encoding="utf-8").write(out)
    body = out[:out.index("# References")]
    words = len(re.findall(r"[A-Za-z][A-Za-z\-']*", body))
    print("paper_v3.md 生成：%d 英文词（含图题表格口径）" % words)
    words2 = len(re.findall(r"[A-Za-z][A-Za-z\-']*", "\n".join(
        l for l in body.split("\n") if not l.strip().startswith(("|", "!", "$$", "#")))))
    print("纯正文词数（估）: %d" % words2)

if __name__ == "__main__":
    main()
