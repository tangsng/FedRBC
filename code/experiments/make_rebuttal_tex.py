#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""rebuttal md → 简单 LaTeX（article 类）供 H100 编译 PDF。
用法：python make_rebuttal_tex.py <input.md> <output.tex> "<PDF 页眉标题>"
处理：# 标题层级、**粗体**、*斜体*、| 表格 |、--- 分割线、$数学$ 原样、Unicode 数学映射。"""
import re
import sys


def convert(src, dst, letter):
    md = open(src, encoding="utf-8").read()

    def inline(s):
        keep = []
        def stash(m):
            keep.append(m.group(0))
            return "\x00%d\x00" % (len(keep) - 1)
        s = re.sub(r"\$[^$]+\$", stash, s)
        s = re.sub(r"\\[a-zA-Z]+\{[^}]*\}", stash, s)
        s = re.sub(r"\*\*(.+?)\*\*", r"\\textbf{\1}", s)
        s = re.sub(r"(?<![\w*])\*([^*\n]+?)\*(?![\w*])", r"\\emph{\1}", s)
        UNI = {
            "—": "---", "–": "--", "×": r"$\times$", "±": r"$\pm$",
            "β": r"$\beta$", "→": r"$\rightarrow$", "κ": r"$\kappa$",
            "ε": r"$\varepsilon$", "∈": r"$\in$", "≈": r"$\approx$",
            "≤": r"$\le$", "σ": r"$\sigma$", "✅": r"\checkmark",
            "é": "\\'e",
        }
        for k, v in UNI.items():
            s = s.replace(k, v)
        s = s.replace("&", r"\&").replace("#", r"\#")
        s = re.sub(r"(?<!\\)%", r"\%", s)
        s = re.sub(r"\x00(\d+)\x00", lambda m: keep[int(m.group(1))], s)
        return s

    out = []
    lines = md.split("\n")
    i = 0
    while i < len(lines):
        ln = lines[i]
        st = ln.strip()
        if st.startswith("### "):
            out.append(r"\subsubsection*{%s}" % inline(st[4:]))
        elif st.startswith("## "):
            out.append(r"\subsection*{%s}" % inline(st[3:]))
        elif st.startswith("# "):
            out.append(r"\section*{%s}" % inline(st[2:]))
        elif st == "---":
            out.append(r"\noindent\rule{\textwidth}{0.4pt}")
        elif st.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not re.match(r"^[\s:-]+$", "".join(cells)):
                    rows.append(cells)
                i += 1
            i -= 1
            ncol = max(len(r) for r in rows)
            out.append(r"\begin{table}[H]\centering\small")
            out.append(r"\begin{tabular}{%s}" % ("l" + "c" * (ncol - 1)))
            for j, r in enumerate(rows):
                r = r + [""] * (ncol - len(r))
                out.append(" & ".join(inline(c) for c in r) + r"\\")
                if j == 0:
                    out.append(r"\hline")
            out.append(r"\hline\end{tabular}\end{table}")
        elif st == "":
            pass
        else:
            out.append(inline(st) + "\n")
        i += 1

    tex = r"""\documentclass[10pt]{article}
\usepackage[margin=2.2cm]{geometry}
\usepackage{booktabs}
\usepackage{amsmath,amssymb}
\usepackage{float}
\usepackage[T1]{fontenc}
\usepackage{setspace}
\onehalfspacing
\setlength{\parindent}{0pt}
\setlength{\parskip}{4pt}
\begin{document}
\begin{center}
{\LARGE\bfseries """ + letter + r"""}\\[4pt]
{\large Manuscript ID 94388: FedRBC: Blockchain-Enabled Reputation-Weighted Robust\\
Federated Learning for Privacy-Preserving Healthcare IoT Edge Networks}
\end{center}
""" + "\n".join(out) + "\n\\end{document}\n"

    open(dst, "w", encoding="utf-8").write(tex)
    print("written", dst, len(tex), "chars")


if __name__ == "__main__":
    src, dst, letter = sys.argv[1], sys.argv[2], sys.argv[3]
    convert(src, dst, letter)
