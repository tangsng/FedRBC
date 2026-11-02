#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""将 rebuttal_round1.md 拆分为三份独立回复信：
Response to Reviewer 1 / Response to Reviewer 2 / Response to Editor 1
各含定制致谢开头；渲染说明归 R2 版；新实验汇总表归 Editor 版。"""
import re, io, os

SRC = r"D:\workbuddy\CMC0930\paper\rebuttal_round1.md"
OUT_DIR = r"D:\workbuddy\CMC0930\paper"

TITLE = ("**FedRBC: Blockchain-Enabled Reputation-Weighted Robust Federated Learning "
         "for Privacy-Preserving Healthcare IoT Edge Networks**")

md = io.open(SRC, encoding="utf-8").read()
lines = md.split("\n")

# 定位分块（按已知结构行号切）
def block(marker):
    """返回从 '## marker' 行到下一个 '---' 或文末的内容（不含该节标题行与 ---）。"""
    start = None
    for i, ln in enumerate(lines):
        if ln.strip() == "## " + marker:
            start = i + 1
            break
    assert start is not None, "marker not found: " + marker
    end = len(lines)
    for j in range(start, len(lines)):
        if lines[j].strip() == "---":
            end = j
            break
    return "\n".join(lines[start:end]).strip()

r1_body = block("Reviewer 1")
r2_body = block("Reviewer 2")
ed_body = block("Editor")
summary_body = block("Summary of new experiments")

# 渲染说明段（从总头中抽出，归入 R2 版）
m = re.search(r"A note on the PDF rendering issues:.*?(?=\n\n|\Z)", md, re.S)
render_note = m.group(0).strip() if m else ""

R1_OPEN = """Dear Reviewer 1,

We thank you for a careful and constructive review — your eighteen points have materially improved the paper. In response, we extended the threat model with four new attack families (LIE, backdoor with attack-success-rate scoring, root-set poisoning, and direction-preserving scaling under differential privacy), raised every headline configuration to ten seeds with 95% confidence intervals and Holm-corrected significance tests, added the classical baselines and the upper references you asked for, restructured the convergence theory so that its residual adversarial term is derived explicitly from the gate and ledger rather than assumed, measured the full component-ablation grid including the ledger-memory ablation, expanded the sensitivity and client-scaling studies, and widened the deployment, false-quarantine, and clinical-safety discussion. We respond point by point below; all section/equation/figure/table numbers refer to the revised manuscript."""

R2_OPEN = """Dear Reviewer 2,

We thank you for a demanding and precise review — the five major points and the additional requirements have reshaped this paper for the better. In response, we added the centralized and clean-FedAvg references that calibrate the operating regime; added FLTrust, Krum, and trimmed mean as first-class baselines and relabelled the simplified recent-system variants as aggregation-level re-implementations; extended the threat model with exactly the attacks that target this defence (LIE, backdoor scored by attack success rate, root-set perturbation, and the Byzantine ratio up to 0.5); measured the previously argued contributions (the ledger-memory ablation and the client-scaling study); restructured the theory around a new Lemma 1 that derives the residual malicious weight from the gate and ledger explicitly; fixed the kappa/beta symbol collision at its root; added an accounted differential-privacy mechanism backing the title's claim; and confined the device-feasibility language to emulation. We respond point by point below; all section/equation/figure/table numbers refer to the revised manuscript.

""" + render_note

ED_OPEN = """Dear Editor,

We thank you for the detailed format audit of the submission. All eight points have been addressed in this revision: abbreviations are defined at first use throughout (abstract, main text, and captions), Appendix A and its algorithms are now cited in order from the main text, the premature Fig. 9 reference has been removed, the occluding legends of Figs. 6–7 have been repositioned into whitespace, the shaded region of Fig. 7 is explained in its caption, Tables 1 and 3 state what bold marks, the citation sequence has been programmatically re-verified as strictly ascending at first occurrence with no run longer than five consecutive citations, and both reference titles flagged have been verified against CrossRef and completed. The itemized responses follow; a summary of all new experiments in this revision is appended at the end of this letter."""

def write_doc(fname, salutation_title, opener, body, appendix=None):
    parts = ["# " + salutation_title + " (Manuscript ID 94388)", "",
             TITLE, "", opener, "", body]
    if appendix:
        parts += ["", appendix]
    io.open(os.path.join(OUT_DIR, fname), "w", encoding="utf-8").write("\n".join(parts))
    print("wrote", fname)

write_doc("response_reviewer1.md", "Response to Reviewer 1", R1_OPEN, r1_body)
write_doc("response_reviewer2.md", "Response to Reviewer 2", R2_OPEN, r2_body)
write_doc("response_editor1.md", "Response to Editor 1", ED_OPEN, ed_body,
          appendix="## Summary of new experiments\n\n" + summary_body)
print("done")
