#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
论文整合器：sections_draft.md + method_draft.md + results_section.md -> paper.md
- 替换引用占位 [[ID]] 为 IEEE 编号 [n]（依 ref_id_map.json，多引用 [[A],[B]] -> [n],[m]）
- 拼接参考文献列表 references_ieee.md
用法：python code/experiments/build_paper.py
"""
import json, re, os

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
PAPER = os.path.join(ROOT, "paper")

def load(name):
    with open(os.path.join(PAPER, name), encoding="utf-8") as f:
        return f.read()

def replace_cites(text, id_map):
    def rep(m):
        ids = re.findall(r"[A-Z]\d+", m.group(0))
        if not ids:
            return m.group(0)
        try:
            nums = [str(id_map[i]) for i in ids]
        except KeyError as e:
            raise SystemExit("未知引用 id: %s（上下文: ...%s...）" % (e.args[0], text[max(0, m.start()-60):m.start()]))
        return "[" + "], [".join(nums) + "]"
    return re.sub(r"\[\[[A-Z0-9\[\],.\s]+?\]\]", rep, text)

def main():
    id_map = json.load(open(os.path.join(PAPER, "ref_id_map.json")))
    sections = load("sections_draft.md")
    method = load("method_draft.md")
    results = load("results_section.md")  # Phase 7 由真实数据生成
    refs = load("references_ieee.md")

    # 抽取 sections_draft 的各部分
    def between(src, start, end=None):
        i = src.index(start)
        j = src.index(end) if end else len(src)
        return src[i:j].strip()

    abstract = between(sections, "## Abstract", "## 1. Introduction")
    intro = between(sections, "## 1. Introduction", "## 2. Related Work")
    related = between(sections, "## 2. Related Work", "## 6.1 Experimental Setup")
    setup = between(sections, "## 6.1 Experimental Setup", "## 7. Discussion")
    discussion = between(sections, "## 7. Discussion", "## 8. Conclusion")
    conclusion = between(sections, "## 8. Conclusion", "## 作者与基金")
    authors = between(sections, "## 作者与基金")

    # method_draft 去掉头部说明，保留 §3 起
    mi = method.index("## 3. System Model")
    method_body = method[mi:method.index("## 贡献点")].strip()

    title = ("# FedRBC: Blockchain-Enabled Reputation-Weighted Robust Federated Learning "
             "for Privacy-Preserving Healthcare IoT Edge Networks\n")
    parts = [title, authors, abstract, intro, related, method_body,
             "## 6. Performance Evaluation\n\n" + setup + "\n\n" + results,
             discussion, conclusion, refs]
    doc = "\n\n---\n\n".join(p.strip() for p in parts)
    doc = replace_cites(doc, id_map)

    out = os.path.join(PAPER, "paper.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write(doc)
    words = len(re.findall(r"[A-Za-z][A-Za-z\-']+", doc))
    cites = sorted(set(int(x) for x in re.findall(r"\[(\d+)\]", doc) if int(x) <= 100))
    print("paper.md 生成：%d 英文词（正文口径含图表标题），引用编号使用 %d/%d 条"
          % (words, len(cites), len(id_map)))

if __name__ == "__main__":
    main()
