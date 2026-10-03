#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CMC 投稿 LaTeX 生成器（v2）。
将 v3 源 markdown 转换为 Tech Science Press (CMC) LaTeX 模板。
"""
import re, json, ast, os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
P = lambda *a: os.path.join(ROOT, *a)

# ---------- 引用 ----------
def load_order():
    src = open(P("code/experiments/build_paper_v3.py"), encoding="utf-8").read()
    m = re.search(r"CITE_ORDER = \[(.*?)\]", src, re.S)
    return ast.literal_eval("[" + m.group(1) + "]")

CITE_ORDER = load_order()
DATA = json.load(open(P("paper/references_verified.json"), encoding="utf-8"))
BYID = {e["id"]: e for e in DATA["entries"]}
ID2NUM = {rid: i + 1 for i, rid in enumerate(CITE_ORDER)}

# ---------- 作者名归一化 ----------
_PARTICLES = {"van", "der", "den", "de", "el", "al", "la", "le", "di", "da", "del", "y", "e", "i", "von", "du"}

def norm_author(a):
    a = a.strip()
    if not a:
        return ""
    if "," in a:
        fam, given = a.split(",", 1)
        fam = fam.strip()
        ini = "".join(p[0] for p in given.split() if p)
        return ("%s %s" % (fam, ini)).strip()
    parts = a.split()
    if len(parts) == 1:
        return a
    # 小写姓氏助词（van der / el / ...）并入姓：从倒数第二个词向前扫描助词
    surname_start = len(parts) - 1
    j = len(parts) - 2
    while j >= 1 and parts[j].lower() in _PARTICLES:
        surname_start = j
        j -= 1
    fam = " ".join(parts[surname_start:])
    ini = "".join(p[0] for p in parts[:surname_start] if p)
    return ("%s %s" % (fam, ini)).strip()

def fmt_authors(authors, max_n=6):
    if not authors:
        return ""
    normed = [norm_author(a) for a in authors if norm_author(a)]
    if len(normed) > max_n:
        return ", ".join(normed[:max_n]) + ", et al"
    return ", ".join(normed)

def esc(s):
    # 反复解码 &amp; 直到稳定，再转义 LaTeX 特殊字符
    prev = None
    while prev != s:
        prev = s
        s = s.replace("&amp;", "&")
    s = s.replace("&", r"\&")
    s = s.replace("_", r"\_")
    s = s.replace("%", r"\%")
    s = s.replace("#", r"\#")
    return s

# ---------- Vancouver ----------
def vancouver(e):
    a = fmt_authors(e.get("authors", []))
    t = esc((e.get("title") or "").strip().rstrip("."))
    cont = esc((e.get("container") or "").strip())
    year = str(e.get("year") or "").strip()
    doi = str(e.get("doi") or "").strip()
    vol = str(e.get("volume") or "").strip()
    issue = str(e.get("issue") or "").strip()
    page = str(e.get("page") or "").strip()
    doi_link = " [\\href{https://doi.org/%s}{CrossRef}]" % doi if doi else ""

    low = (cont + " " + doi).lower()
    if "arxiv" in low:
        m = re.search(r"arxiv\.([\d\.]+)", low)
        return r"%s. %s. arXiv:%s. %s.%s" % (a, t, m.group(1) if m else cont, year, doi_link)

    is_conf = any(k in low for k in
                  ["proceedings", "conference", "workshop", "symposium", "meeting",
                   "icws", "icc ", "wcnc", "ccnc", "smartcloud", "iwcmc", "globecom",
                   "ndss", "csf", "aistats", "mlsys", "iccc", "gbc", "insticc",
                   "acm sigsac", "hot topics", "hotnets", "international workshop"])
    if vol and not is_conf:
        volpage = vol
        if issue:
            volpage += "(%s)" % issue
        if page:
            volpage += ":" + page
        return r"%s. %s. %s. %s;%s.%s" % (a, t, cont, year, volpage, doi_link)
    if is_conf:
        if page:
            return r"%s. %s. In: %s. %s. p. %s.%s" % (a, t, cont, year, page, doi_link)
        return r"%s. %s. In: %s. %s.%s" % (a, t, cont, year, doi_link)
    if page:
        return r"%s. %s. %s. %s. p. %s.%s" % (a, t, cont, year, page, doi_link)
    return r"%s. %s. %s. %s.%s" % (a, t, cont, year, doi_link)

# ---------- md -> tex ----------
def conv_citations(txt):
    def expand_token(tok):
        tok = tok.strip()
        m = re.match(r"^([A-Z]+)(\d+)–([A-Z]+)(\d+)$", tok)
        if m and m.group(1) == m.group(3):
            nums = [ID2NUM.get("%s%d" % (m.group(1), k))
                    for k in range(int(m.group(2)), int(m.group(4)) + 1)]
            return [n for n in nums if n]
        if re.match(r"^[A-Z]+\d+$", tok) and tok in ID2NUM:
            return [ID2NUM[tok]]
        return None
    def repl(m):
        nums = []
        for tok in m.group(1).split(","):
            r = expand_token(tok)
            if r is None:
                return m.group(0)
            nums.extend(r)
        nums = sorted(set(nums))
        return r"\cite{%s}" % ",".join("ref-%d" % n for n in nums)
    return re.sub(r"\[((?:[A-Z]+\d+(?:–[A-Z]+\d+)?)(?:\s*,\s*[A-Z]+\d+(?:–[A-Z]+\d+)?)*)\]",
                  repl, txt)

UNICODE_MAP = [
    ("→", r"$\to$"), ("←", r"$\leftarrow$"), ("±", r"$\pm$"), ("×", r"$\times$"),
    ("≈", r"$\approx$"), ("≤", r"$\leq$"), ("≥", r"$\geq$"), ("–", "--"),
    ("—", "---"), ("…", r"\dots"), ("·", r"$\cdot$"),
    ("%", r"\%"),
    ("α", r"$\alpha$"), ("β", r"$\beta$"), ("γ", r"$\gamma$"), ("δ", r"$\delta$"),
    ("ε", r"$\epsilon$"), ("η", r"$\eta$"), ("θ", r"$\theta$"), ("κ", r"$\kappa$"),
    ("λ", r"$\lambda$"), ("μ", r"$\mu$"), ("ρ", r"$\rho$"), ("τ", r"$\tau$"),
    ("φ", r"$\phi$"), ("Δ", r"$\Delta$"), ("Ω", r"$\Omega$"), ("σ", r"$\sigma$"),
    ("½", r"$\tfrac{1}{2}$"),
]

def conv_inline(txt):
    # 保护 $...$ 数学块
    maths = []
    def stash(m):
        maths.append(m.group(0))
        return "\x00M%d\x00" % (len(maths) - 1)
    txt = re.sub(r"\$[^$]+\$", stash, txt)
    for a, b in UNICODE_MAP:
        txt = txt.replace(a, b)
    def unstash(m):
        return maths[int(m.group(1))]
    txt = re.sub(r"\x00M(\d+)\x00", unstash, txt)
    return txt

def conv_para(line):
    line = conv_citations(line)
    # 保护数学块
    maths = []
    def stash(m):
        maths.append(m.group(0))
        return "\x00M%d\x00" % (len(maths) - 1)
    line = re.sub(r"\$[^$]+\$", stash, line)
    # Unicode 符号（非数学）
    for a, b in UNICODE_MAP:
        line = line.replace(a, b)
    # 加粗 / 斜体
    line = re.sub(r"\*\*(.+?)\*\*", r"\\textbf{\1}", line)
    line = re.sub(r"\*([^*\n]+?)\*", r"\\emph{\1}", line)
    # 行内代码 `foo` -> \texttt{foo}
    line = re.sub(r"`([^`]+)`", r"\\texttt{\1}", line)
    # 还原数学块
    line = re.sub(r"\x00M(\d+)\x00", lambda m: maths[int(m.group(1))], line)
    return line

def conv_display(line):
    def repl(m):
        body = m.group(1).strip()
        tm = re.search(r"\\tag\{(\d+)\}", body)
        if tm:
            body = re.sub(r"\\tag\{\d+\}", "", body).strip()
            return "\\begin{equation}\n%s\n\\tag{%s}\n\\end{equation}" % (body, tm.group(1))
        return "\\[\n%s\n\\]" % body
    return re.sub(r"\$\$(.+?)\$\$", repl, line, flags=re.S)

def slug(t):
    return re.sub(r"[^a-zA-Z0-9]+", "-", t).strip("-").lower()

# ---------- 章节处理 ----------
_TBL_GLOBAL = [0]  # 全局表格计数器

def process_section(md_path):
    txt = open(md_path, encoding="utf-8").read()
    lines = txt.split("\n")
    out = []
    i = 0
    while i < len(lines):
        s = lines[i].rstrip()
        st = s.strip()
        if not st:
            i += 1
            continue
        # 标题
        if st.startswith("# "):
            t = re.sub(r"^\d+\.?\s*", "", st[2:].strip())
            out.append("\\section{%s}\\label{sec:%s}" % (conv_inline(t), slug(t)))
            i += 1
            continue
        if st.startswith("## "):
            t = re.sub(r"^\d+\.\d+\.?\s*", "", st[3:].strip())
            out.append("\\subsection{%s}\\label{sec:%s}" % (conv_inline(t), slug(t)))
            i += 1
            continue
        if st.startswith("### "):
            t = re.sub(r"^\d+\.\d+\.\d+\.?\s*", "", st[4:].strip())
            out.append("\\subsubsection{%s}" % conv_inline(t))
            i += 1
            continue
        # 图片
        if st.startswith("!["):
            m = re.match(r"!\[(.*?)\]\((.*?)\)", st)
            if m:
                out.append("@@FIGURE:%s@@" % m.group(1).strip())
                i += 1
                continue
        # 图/表 caption 行：跳过（由 FIG_MAP/TABLES 提供）
        if st.startswith("**Fig.") or st.startswith("**Table"):
            i += 1
            continue
        # 表格
        if st.startswith("|"):
            while i < len(lines) and lines[i].strip().startswith("|"):
                i += 1
            _TBL_GLOBAL[0] += 1
            out.append("@@TABLE%d@@" % _TBL_GLOBAL[0])
            continue
        # 显示公式
        if st.startswith("$$"):
            out.append(conv_display(st))
            i += 1
            continue
        # 列表（连续 - 项合并为一个 itemize）
        if st.startswith("- "):
            items = []
            while i < len(lines) and lines[i].strip().startswith("- "):
                items.append("\\item " + conv_para(lines[i].strip()[2:]))
                i += 1
            out.append("\\begin{itemize}\n" + "\n".join(items) + "\n\\end{itemize}")
            continue
        # 普通段落
        out.append(conv_para(st))
        i += 1
    return "\n\n".join(out)

# ---------- 表格 ----------
def T(caption, label, cols, rows):
    header = " & ".join(r"\textbf{%s}" % c for c in cols[0]) + r"\\"
    body = []
    for r in rows:
        body.append(" & ".join(r) + r"\\")
    return r"""\begin{table}[H]
\tablesize{\footnotesize}
\caption{%s}
\label{%s}
\begin{tabularx}{\textwidth}{%s}
\toprule
%s
\midrule
%s
\bottomrule
\end{tabularx}
\end{table}""" % (caption, label, cols[1], header, "\n".join(body))

def gen_tables():
    C = r">{\centering\arraybackslash}X"
    t1 = T("Positioning of FedRBC against representative systems ($\\checkmark$ = full, $\\circ$ = partial, $\\times$ = none).",
           "tab:t1", [["System","Year","Robust aggregation","Persistent trust","Trust-gated selection","Network containment","Collusion resistance","Eval. vs. model-layer attacks"], "l"+C*7], [
        ["DeepChain [N17]","2019","$\\times$","$\\checkmark$ (audit only)","$\\times$","$\\times$","$\\times$","$\\times$"],
        ["FLTrust [B3]","2021","$\\checkmark$ (root gate)","$\\times$","$\\times$","$\\times$","$\\circ$","$\\circ$"],
        ["EIFFeL [B5]","2022","$\\checkmark$ (coord. vote)","$\\times$","$\\times$","$\\times$","$\\times$","$\\circ$"],
        ["FedGT [N22]","2025","$\\checkmark$ (hard identify)","$\\circ$","$\\circ$","$\\times$","$\\times$","$\\times$"],
        ["TFFL/DRC [N21]","2025","$\\checkmark$ (subj. logic)","$\\circ$","$\\circ$","$\\times$","$\\circ$ (on-chain)","$\\circ$"],
        ["FedGreed [N18]","2025","$\\checkmark$ (loss greedy)","$\\circ$","$\\circ$","$\\times$","$\\times$","$\\checkmark$"],
        ["RAID [N11]","2026","$\\circ$ (score)","$\\circ$ (per-round)","$\\times$","$\\times$","$\\times$","$\\circ$"],
        ["Model verification [N19]","2026","$\\circ$ (dual metric)","$\\circ$","$\\circ$","$\\times$","$\\checkmark$ (on-chain)","$\\times$"],
        ["Loss-based clustering [N20]","2025","$\\checkmark$ (loss cluster)","$\\circ$","$\\circ$","$\\times$","$\\times$","$\\checkmark$"],
        ["\\textbf{FedRBC}","---","$\\checkmark$ (ref + clip + softmax)","$\\checkmark$ (on-chain)","$\\checkmark$ (Eq. 11)","$\\checkmark$ (SDN)","$\\checkmark$","$\\checkmark$"],
    ])
    t2 = T("Simulation parameters (held fixed across all experiments).","tab:t2",
           [["Group","Parameter","Value","Group","Parameter","Value"],"l"+C*5], [
        ["Federation","clients $N$ / quorum $K$","20 / 10","RWRA","$z_{\\mathrm{th}}$ / $\\kappa$ / $T_s$","2 / 2 / 0.3"],
        ["Training","rounds $T$ / epochs $E$","60 / 2","Contract","$\\gamma$ / $\\kappa$ / $\\lambda_{\\mathrm{dec}}$","0.3 / 2.0 / 0.01"],
        ["Training","batch / lr / momentum","32 / 0.05 / 0.9","Contract","$\\theta_h$ / $\\theta_m$ / $r_{\\mathrm{q}}$","0.3 / 0.0 / 0.15"],
        ["Data","root set $\\lvert\\mathcal{D}_r\\rvert$","500","Selection","budget $B$","25 (cost units)"],
        ["Data","Dirichlet $\\alpha$ (default)","0.5","Protocol","seeds","$\\{42, 43, 44, 45, 46\\}$"],
        ["Threat","Byzantine ratio $\\beta$ (default)","30\\%","Testbed","GPUs","2$\\times$ V100S-32GB"],
        ["Selection","utility $u_i$ / cost $c_i$","$\\mathcal{U}[0,1]$ / $\\mathcal{U}[1,5]$","---","---","---"],
    ])
    t3 = T("Threat-model coverage matrix ($\\checkmark$ = covered, partial = limited, $\\times$ = not covered).","tab:t3",
           [["System","Year","Magnitude (scaling)","Direction (sign-flip)","Collusion (Sybil)","Data (label-flip)","Persistent audit","Selection-aware"],"l"+C*7], [
        ["RAID [N11]","2026","$\\times$","partial (scoring lag)","$\\times$","partial (soft score)","$\\times$","$\\times$"],
        ["FedGT [N22]","2025","$\\times$ (no clipping)","$\\checkmark$ (hard identify)","$\\checkmark$ (hard identify)","$\\circ$ (direction)","$\\times$","$\\times$"],
        ["EIFFeL [B5]","2022","partial (coord. clip)","$\\checkmark$ if $f<K/2$","$\\times$ (plurality forge)","partial","$\\times$","$\\times$"],
        ["\\textbf{FedRBC}","---","$\\checkmark$ (Layer-0 + rel. clip)","$\\checkmark$ (softmax gate, Eq. 6)","$\\checkmark$ (root gate + ledger)","$\\checkmark$ (evidence weighting)","$\\checkmark$ (on-chain)","$\\checkmark$ (Eq. 11)"],
    ])
    t4 = T("Final-round detection metrics under three attack classes ($\\beta=30\\%$, $\\alpha=0.5$; mean $\\pm$ std, 5 seeds). Best per row in bold.","tab:t4",
           [["Attack","Method","F1","AUC","Acc"],"l"+C*4], [
        ["Sign-flip","\\textbf{FedRBC (Ours)}","\\textbf{0.588$\\pm$0.062}","\\textbf{0.887$\\pm$0.007}","0.875$\\pm$0.032"],
        ["","RAID (2026)","0.223$\\pm$0.249","0.554$\\pm$0.070","0.636$\\pm$0.344"],
        ["","FedGT (2025)","0.190$\\pm$0.258","0.587$\\pm$0.022","0.717$\\pm$0.530"],
        ["","EIFFeL (2022)","0.502$\\pm$0.097","0.832$\\pm$0.008","0.814$\\pm$0.026"],
        ["Sybil collusion","\\textbf{FedRBC (Ours)}","\\textbf{0.570$\\pm$0.056}","\\textbf{0.885$\\pm$0.009}","0.865$\\pm$0.010"],
        ["","RAID (2026)","0.128$\\pm$0.167","0.558$\\pm$0.000","0.689$\\pm$0.000"],
        ["","FedGT (2025)","0.142$\\pm$0.285","0.567$\\pm$0.001","0.886$\\pm$0.000"],
        ["","EIFFeL (2022)","0.089$\\pm$0.122","0.500$\\pm$0.001","0.579$\\pm$0.000"],
        ["Label-flip","\\textbf{FedRBC (Ours)}","\\textbf{0.561$\\pm$0.057}","\\textbf{0.877$\\pm$0.008}","0.861$\\pm$0.010"],
        ["","RAID (2026)","0.405$\\pm$0.263","0.726$\\pm$0.248","0.723$\\pm$0.000"],
        ["","FedGT (2025)","0.252$\\pm$0.262","0.560$\\pm$0.110","0.588$\\pm$0.000"],
        ["","EIFFeL (2022)","0.454$\\pm$0.169","0.795$\\pm$0.022","0.675$\\pm$0.000"],
    ])
    t5 = T("Cross-dataset generalization on CICIoT2023 ($\\beta=30\\%$, $\\alpha=0.5$; mean $\\pm$ std, 3 seeds). Best F1 per row in bold.","tab:t5",
           [["Attack","\\textbf{FedRBC (Ours)}","RAID (2026)","FedGT (2025)","EIFFeL (2022)"],"l"+C*4], [
        ["Sign-flip","\\textbf{0.992$\\pm$0.000}","0.286$\\pm$0.495","0.901$\\pm$0.076","0.987$\\pm$0.006"],
        ["Sybil collusion","\\textbf{0.730$\\pm$0.344}","0.592$\\pm$0.514","0.629$\\pm$0.546","0.417$\\pm$0.400"],
        ["Label-flip","\\textbf{0.992$\\pm$0.000}","0.615$\\pm$0.537","0.575$\\pm$0.489","0.947$\\pm$0.078"],
    ])
    return {1: t1, 2: t2, 3: t3, 4: t4, 5: t5}

TABLES = gen_tables()

# ---------- 图片 ----------
FIG_MAP = {
    "Fig. 1": ("fig1_architecture", "FedRBC system architecture for healthcare IoT edge networks. Raw telemetry never leaves the sensing layer; only parameter deltas and scalar evidence cross layer boundaries. Numbered flows: (1) model updates $\\Delta_i$ with content hash (local SGD, Eq.~2); (2) root reference $\\Delta_{\\rm root}$ (Eq.~3); (3) evidence submission $\\mathrm{writeEvidence}(i, s_i)$; (4) on-chain reputation read/write; (5) reputation feedback $\\mathbf{r}(t)$ to selection and aggregation weights; (6) containment trigger (Eq.~12); (7) SDN isolation of the compromised device. The red dashed path marks the adversarial channel of the MitM device."),
    "Fig. 2": ("fig2_sequence", "Interaction sequence of one federated round in FedRBC. Steps (1)--(6) constitute the training loop; steps (7)--(8) fire only when a client's on-chain reputation crosses the quarantine threshold. Evidence and reputation are the only values committed on-chain; model payloads stay off-chain, bound to their evidence by content hashes."),
    "Fig. 3": ("fig3_repflow", "On-chain reputation management workflow (Alg. 2). Each evidence write is routed to the reward, penalty, or grey-zone branch by the evidence thresholds; non-participating clients undergo temporal decay; quarantine is triggered when any reputation falls below $r_{\\rm q}$, emitting the containment event consumed by the SDN controller."),
    "Fig. 4": ("fig5_main_attacks", "Final-round F1, AUC, and accuracy under the three attack classes ($\\beta$=30\\%, $\\alpha$=0.5; mean$\\pm$std over 5 seeds). FedRBC (red) attains the highest F1 and AUC in every scenario and the smallest variance; error bars denote one standard deviation."),
    "Fig. 5": ("fig7_beta_sweep", "Test F1 versus Byzantine ratio $\\beta$ under Sybil collusion ($\\alpha$=0.5; mean$\\pm$std, 3 seeds). FedRBC stays flat while FedGT's binary identification collapses once a forged plurality forms, and the statistical baselines fail, because only a plurality-independent reference plus persistent trust survives high $\\beta$."),
    "Fig. 6": ("fig8_noniid", "Test F1 versus Dirichlet concentration $\\alpha$ under Sybil collusion ($\\beta$=30\\%; mean$\\pm$std, 3 seeds). FedRBC degrades most gracefully: it is the only system above $0.3$ at the extreme $\\alpha$=0.1 and holds a 15.6-point lead at $\\alpha$=1.0."),
    "Fig. 7": ("fig6_convergence", "Per-round test F1 under Sybil collusion ($\\beta$=30\\%, $\\alpha$=0.5; mean$\\pm$std band over 3 seeds). FedRBC plateaus within roughly 10 rounds, because quarantined adversaries are excluded from selection rather than merely down-weighted at aggregation."),
    "Fig. 8": ("fig9_repdyn", "On-chain reputation trajectories under Sybil collusion (a representative single seed, 60 rounds). Byzantine reputations (red) decay along the theoretical bound of Prop. 1 (dotted) and never recover after quarantine; honest reputations (green) erode under grey-zone penalization but recover once the quorum cleans. The trajectory is illustrative rather than a seed-averaged claim; the suppression-time bound of Eq. 10 is exact for the Byzantine curves in all seeds."),
    "Fig. 9": ("fig10_mttc", "Mean time to containment versus utilization $\\rho=\\lambda_a/\\mu$ (M/M/1 emulation, Eq. 12). The FedRBC edge loop stays flat at $\\approx$3.3 s while the cloud-roundtrip baseline grows from 6.7 s to 16.1 s --- a 50--80\\% reduction consistent with Thm. 2."),
}

def make_figure(key):
    fname, cap = FIG_MAP[key]
    return r"""\begin{figure}[H]
\centering
\includegraphics[width=\textwidth]{Figures/%s}
\caption{%s}
\label{fig:%s}
\end{figure}""" % (fname, cap, fname)

def fill_placeholders(body):
    def tbl_repl(m):
        n = int(m.group(1))
        return TABLES.get(n, "")
    body = re.sub(r"@@TABLE(\d+)@@", tbl_repl, body)
    def fig_repl(m):
        return make_figure(m.group(1))
    body = re.sub(r"@@FIGURE:(Fig\. \d+)@@", fig_repl, body)
    return body

# ---------- 附录证明（逐行转换，复用 conv_para / conv_display） ----------
def _clean_ascii(s):
    # 去掉中文等非 ASCII 内容
    s = re.sub(r"[^\x00-\x7F]+", "", s)
    return s.strip()

def conv_proof(md):
    lines = md.split("\n")
    out = []
    for line in lines:
        st = line.strip()
        if not st:
            continue
        if st.startswith("# "):
            out.append("\\section*{%s}" % _clean_ascii(st[2:].strip()))
        elif st.startswith("## "):
            out.append("\\subsection*{%s}" % _clean_ascii(st[3:].strip()))
        elif st.startswith("$$"):
            out.append(conv_display(st))
        else:
            out.append(conv_para(st))
    return "\n\n".join(out)

# ---------- 附录算法（markdown 表格 -> LaTeX） ----------
def conv_algorithm(md):
    lines = md.split("\n")
    out = []
    i = 0
    while i < len(lines):
        st = lines[i].strip()
        if not st:
            i += 1
            continue
        if st.startswith("# "):
            out.append("\\section*{%s}" % _clean_ascii(st[2:].strip()))
            i += 1
            continue
        if st.startswith("**Algorithm"):
            title = st.strip("*").strip()
            title = conv_para(title)
            out.append("\\noindent\\textbf{%s}" % title)
            i += 1
            continue
        if st == "---":
            out.append("\\vspace{0.5em}")
            i += 1
            continue
        if st.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                rows.append(cells)
                i += 1
            body = []
            for cells in rows:
                if len(cells) < 2:
                    continue
                if set("".join(cells).replace(" ", "")) <= {"-", ":"}:
                    continue
                key = cells[0].strip()
                val = " ".join(cells[1:]).strip()
                key = conv_para(key)
                val = conv_para(val)
                body.append("\\noindent\\makebox[1.6em][r]{%s}~ %s" % (key, val))
            out.append("\\begin{quote}\n" + "\n\n".join(body) + "\n\\end{quote}")
            continue
        i += 1
    return "\n\n".join(out)

def main():
    # abstract
    abstract_md = open(P("paper/v2_abstract.md"), encoding="utf-8").read()
    abs_body = [l for l in abstract_md.split("\n") if l.strip() and not l.startswith("#") and not l.startswith("**")][0]
    abstract = conv_para(abs_body)

    keywords = "federated learning; blockchain; reputation; Byzantine robustness; smart contract; healthcare IoT"

    secs = {}
    _TBL_GLOBAL[0] = 0  # 重置全局表格计数器
    for path, key in [("paper/v3_intro.md", "intro"), ("paper/v3_sysmodel.md", "sysmodel"),
                      ("paper/v3_framework.md", "framework"), ("paper/v3_eval.md", "eval"),
                      ("paper/v3_discussion.md", "discussion")]:
        secs[key] = process_section(P(path))

    for k in list(secs.keys()):
        secs[k] = fill_placeholders(secs[k])

    # 附录
    algo_md = open(P("paper/algorithms_pseudocode.md"), encoding="utf-8").read()
    appendix_algo = conv_algorithm(algo_md)
    proof_md = open(P("paper/v2_appendix_b.md"), encoding="utf-8").read()
    appendix_proof = conv_proof(proof_md)

    # 参考文献
    bibitems = []
    for i, rid in enumerate(CITE_ORDER, 1):
        bibitems.append("\\bibitem{ref-%d}\n%s\n" % (i, vancouver(BYID[rid])))
    thebibliography = "\n".join(bibitems)

    tex = build_tex(abstract, keywords, secs, thebibliography, appendix_algo, appendix_proof)
    # 全局：\mathbb{1} -> \mathbf{1}（指示函数，用标准 amsfonts 的粗体 1，避免 bbm 依赖）
    tex = tex.replace(r"\mathbbm{1}", r"\mathbf{1}").replace(r"\mathbb{1}", r"\mathbf{1}")
    outpath = P("paper/cmc_latex/FedRBC_cmc.tex")
    open(outpath, "w", encoding="utf-8").write(tex)
    print("已生成", outpath)

def build_tex(abstract, keywords, secs, thebibliography, appendix_algo, appendix_proof):
    head = r"""%FedRBC for Computers, Materials & Continua (CMC)
\documentclass[cmc,article,submit,moreauthors,pdftex]{Definitions/tsp}
\input{Definitions/package}
\include{Definitions/unicode}

%% Additional macros (C/L/R column types are already defined by tsp.cls)
\graphicspath{{Figures/}}

%=================================================================
%% Article metadata (assigned by Editorial Office)
\continuouspages{}
\firstpage{1}
\makeatletter
\setcounter{page}{\@firstpage}
\makeatother
\pubvolume{0}
\issuenum{0}
\elocationid{0}
\articlenumber{0}
\pubyear{2026}
\doiyear{2026}
\copyrightyear{2026}
\datereceived{Day Month Year}
\dateaccepted{Day Month Year}
\dateonlinefirst{}
\datepublished{Day Month Year}

%=================================================================
\Title{FedRBC: Blockchain-Enabled Reputation-Weighted Robust Federated Learning for Privacy-Preserving Healthcare IoT Edge Networks}

\Author{Song Tang\textsuperscript{1,2,3}, Zhigang Jin\textsuperscript{1,*} and Zhiqiang Wang\textsuperscript{2,3}}
\AuthorNames{Song Tang, Zhigang Jin and Zhiqiang Wang}

\address{%
\textsuperscript{1}School of Electrical and Information Engineering, Tianjin University, Tianjin 300072, China

\textsuperscript{2}Institute of Applied Mathematics, Hebei Academy of Sciences, Shijiazhuang 050081, China

\textsuperscript{3}Information Security Authentication Technology Innovation Center of Hebei Province, Shijiazhuang 050081, China
}%

\corres{Corresponding Author: Zhigang Jin. Email: zgjin@tju.edu.cn}

\abstract{@@ABSTRACT@@}

\keyword{@@KEYWORDS@@}

\begin{document}

"""
    head = head.replace("@@ABSTRACT@@", abstract).replace("@@KEYWORDS@@", keywords)
    return (head
            + secs["intro"] + "\n\n" + secs["sysmodel"] + "\n\n"
            + secs["framework"] + "\n\n" + secs["eval"] + "\n\n"
            + secs["discussion"] + "\n\n"
            + r"""
\acknowledgement{Not applicable.}

\funding{This work is supported by the Hebei Provincial Science and Technology Program Project (Grant No. 25360301D): ``Research and Application Demonstration of Key Technologies for Public Data Authorization and Operation Based on Trusted Data Space.''}

\authorcontributions{The authors confirm contribution to the paper as follows: Conceptualization, Song Tang and Zhigang Jin; methodology, Song Tang; software, Song Tang; validation, Song Tang and Zhiqiang Wang; formal analysis, Song Tang; investigation, Song Tang and Zhiqiang Wang; resources, Zhigang Jin; data curation, Song Tang; writing---original draft preparation, Song Tang; writing---review and editing, Zhigang Jin and Zhiqiang Wang; visualization, Song Tang; supervision, Zhigang Jin; project administration, Zhigang Jin; funding acquisition, Zhigang Jin. All authors reviewed and approved the final version of the manuscript.}

\availabilityofdataandmaterials{The source code and raw data that support the findings of this study are openly available in the FedRBC repository at \url{https://github.com/tangsng/FedRBC}.}

\ethicsapproval{Not applicable.}

\conflictsofinterest{The authors declare no conflicts of interest. The funders had no role in the design of the study; in the collection, analyses, or interpretation of data; in the writing of the manuscript; or in the decision to publish the results.}

%% Appendices
\appendixstart
\appendix

"""
            + appendix_algo + "\n\n" + appendix_proof + "\n\n"
            + r"""
\reftitle{References}
\begin{thebibliography}{999}
""" + thebibliography + r"""
\end{thebibliography}
\end{document}
""")

if __name__ == "__main__":
    main()
