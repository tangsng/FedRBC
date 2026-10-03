#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
按论文引用顺序生成 IEEE 数字编号制参考文献列表。
输入：paper/references_verified.json；输出：paper/references_ieee.md + paper/ref_id_map.json
引用顺序由 CITE_ORDER 显式给出（与正文首次出现顺序一致）。
"""
import json, re

# 正文首次引用顺序（id 对应 references_verified.json）
CITE_ORDER = [
    # §1 Introduction
    "E1", "F4", "E2", "A1", "A2", "B4", "B6", "B1", "B2", "B3",
    "C1", "C2", "C3", "G2", "F1",
    # §2.1
    "A3", "A5", "H1", "N12", "N13", "N14", "N15", "N16",
    # §2.2
    "C4", "C5", "P0", "P2", "P3", "N10", "P4", "P5", "N6", "N7", "N8", "N9", "N11",
    # §2.3
    "G1", "G3", "F2", "N0", "N1", "N4", "N5", "P1", "N2", "N3", "D1", "D2",
]

def fmt_authors(authors, max_n=6):
    def one(a):
        a = a.strip()
        if "," in a:  # DataCite 风格 "Family, Given"
            family, given = a.split(",", 1)
            ini = " ".join(p[0] + "." for p in given.split() if p)
            return ("%s %s" % (ini, family.strip())).strip()
        parts = a.split()
        if len(parts) == 1:
            return a
        family = parts[-1]
        given = " ".join(p[0] + "." for p in parts[:-1] if p)
        return "%s %s" % (given, family)
    if len(authors) > max_n:
        return ", ".join(one(a) for a in authors[:max_n]) + " et al."
    return ", ".join(one(a) for a in authors)

def ieee_entry(e):
    a = fmt_authors(e.get("authors", []))
    t = e["title"].rstrip(".")
    cont = (e.get("container") or "").replace("&amp;", "&")
    year = e.get("year")
    doi = e.get("doi", "")
    vol, issue, page = e.get("volume", ""), e.get("issue", ""), e.get("page", "")
    is_arxiv = "arxiv" in doi.lower()
    if is_arxiv:
        m = re.search(r"arxiv\.(.+)$", doi, re.I)
        return '%s, "%s," arXiv:%s, %s.' % (a, t, m.group(1) if m else cont, year)
    bits = []
    if vol: bits.append("vol. %s" % vol)
    if issue: bits.append("no. %s" % issue)
    if page: bits.append("pp. %s" % page)
    tail = ", ".join(bits)
    s = '%s, "%s," %s' % (a, t, cont if cont else "[source]")
    if tail:
        s += ", " + tail
    s += ", %s" % year
    if doi:
        s += ", doi: %s" % doi
    return s + "."

def main():
    data = json.load(open("paper/references_verified.json", encoding="utf-8"))
    by_id = {e["id"]: e for e in data["entries"]}
    missing = [i for i in CITE_ORDER if i not in by_id]
    assert not missing, "CITE_ORDER 中有未知 id: %s" % missing
    unused = [i for i in by_id if i not in CITE_ORDER]
    if unused:
        print("⚠️ 未被引用的条目（将附在末尾）: %s" % unused)
    order = CITE_ORDER + unused
    id_map, lines = {}, []
    for n, i in enumerate(order, 1):
        id_map[i] = n
        lines.append("[%d] %s" % (n, ieee_entry(by_id[i])))
    json.dump(id_map, open("paper/ref_id_map.json", "w"), indent=1)
    with open("paper/references_ieee.md", "w", encoding="utf-8") as f:
        f.write("# References\n\n" + "\n\n".join(lines) + "\n")
    n_recent = sum(1 for i in order if (by_id[i].get("year") or 0) >= 2024)
    print("共 %d 条｜2024+ %d 条 (%.1f%%)" % (len(order), n_recent, 100 * n_recent / len(order)))

if __name__ == "__main__":
    main()
