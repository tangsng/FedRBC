# Response to Editor 1 (Manuscript ID 94388)

**FedRBC: Blockchain-Enabled Reputation-Weighted Robust Federated Learning for Privacy-Preserving Healthcare IoT Edge Networks**

Dear Editor,

We thank you for the detailed format audit of the submission. All eight points have been addressed in this revision: abbreviations are defined at first use throughout (abstract, main text, and captions), Appendix A and its algorithms are now cited in order from the main text, the premature Fig. 9 reference has been removed, the occluding legends of Figs. 6–7 have been repositioned into whitespace, the shaded region of Fig. 7 is explained in its caption, Tables 1 and 3 state what bold marks, the citation sequence has been programmatically re-verified as strictly ascending at first occurrence with no run longer than five consecutive citations, and both reference titles flagged have been verified against CrossRef and completed. The itemized responses follow; a summary of all new experiments in this revision is appended at the end of this letter.

1. **Abbreviations defined at first use.** Full audit done: 11 abbreviations were added at first occurrence (abstract-level: SDN, AUC; main text: IoT, IDS, MAD, SGD, PoA, WAN, MLP, MITM, GPU; captions included). ✅
2. **Appendix A cited in main text; algorithms cited in order.** Section 4.1 now introduces Alg. 1 → Alg. 2 → Alg. 3 in order at the architecture overview, with an explicit Appendix-A pointer; the first in-text use of each algorithm was verified to occur after that introduction. ✅
3. **Fig. 9 citation order (line 245).** The premature forward reference in Section 4.5 has been replaced with a reference to the containment separation measured in Section 5.6; Fig. 9 is now first cited in its own subsection. ✅
4. **Figs. 6–7 legends obscure data.** Legends repositioned outside the data region when the plots are regenerated for the revision. ✅
5. **Shaded regions in Fig. 7 explained.** The caption now names the plotted statistic explicitly: the band is the mean$\pm$std range over the 5 seeds (the earlier caption did not name the statistic; the P10–P90 band belongs to Fig. 8's reputation trajectories and is labelled there). ✅
6. **Bold meaning in Tables 1 and 3.** Captions now state that bold marks the best value per row (and, in Table 3, per attack column). ✅
7. **References 5–6 order; 7–12 consecutive run.** The citation sequence has been programmatically re-verified to be strictly ascending at first occurrence (1–56), and the 11-citation run was split into groups of ≤ 5 with connective text. ✅
8. **Reference titles 22 and 52.** Both verified against CrossRef: [EIFFeL] carries its full title "EIFFeL: Ensuring Integrity in Federated Learning"; the venue/volume/pages of the other entry were completed (vol. 13, pp. 190947–190963). ✅

## Summary of new experiments

| Study | Runs | Where |
|---|---|---|
| Main table at 10 seeds + Holm correction | ~120 | Table 4 |
| Classical baselines (FLTrust/Krum/trimmed mean) | 45 | Table 3/4 |
| Centralized + clean-FedAvg upper bounds | 10 | Table 4 |
| Component ablation grid (6 components, incl. ledger memory) | ~60 | Table 5 |
| DP privacy study (3 σ × 4 methods × 2 attacks × 3 seeds) | 72 | Section 5.9 |
| LIE (4 methods × 5 seeds) / backdoor+ASR (3 × 3) / root-poison (2 × 2 × 3ε × 3) | 65 | Section 5.9 |
| Byzantine-ratio extension to β = 0.5 (4 methods × 2 attacks × 3 seeds) | 24 | Section 5.9 |
| Sensitivity sweeps ($T_s$, $\kappa_c$, $\theta_h$, $K$, root size) | 30 | Section 5.9 |
| Client scaling (N = 20/50/100) | 24 | Section 5.9 |

All runs are executed on the released pipeline (data tags `rev1*`), with per-seed raw results in the package.

We believe these changes address every point raised and substantially strengthen the paper. Thank you again for the time and care invested in the review.

Sincerely,
The Authors