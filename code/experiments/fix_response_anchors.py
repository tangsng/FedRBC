#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""审计修正批处理：修正三份回复信 + 合并版中全部锚点失真（2026-11-03 交叉审计发现）。"""
import io

EDITS = {
    # 文件 -> [(old, new), ...]
    "response_reviewer1.md": [
        # R1.5: 敏感性结论与实测相反（T_s 平坦、κ_c 有害）；θ_m 未扫描
        ("All sweep points are 3-seed means with std reported; the sensitivity study identifies the two genuinely sensitive parameters ($T_s$ and $\\theta_h$) and the flat regions that justify the default configuration.",
         "All sweep points are 3-seed means with std reported. The sweep (Section 5.9) locates the defaults near local optima and its profile is itself informative: the gate temperature is deliberately flat across $T_s \\in \\{0.1, 0.5\\}$ (confirming that the softmax form distinguishes by *degree* rather than a knife-edge threshold), the reward threshold and quorum size are mildly monotone, and the single genuinely harmful setting is over-tight clipping ($\\kappa_c=1$, about 6 points) — the one parameter the asymmetry analysis of Section 6.2 warns about."),
        ("**Changes.** New sensitivity subsection with tables/plots for $T_s$, $\\kappa_c$, $\\theta_h$, $\\theta_m$, $K$, root size; Section 5.4.",
         "**Changes.** Sensitivity sweep in Section 5.9 ($T_s$, $\\kappa_c$, $\\theta_h$, $K$, root size; each point 3 seeds with std); Section 5.4 ($\\beta$ sweep, with the $\\beta{=}0.5$ extension in Section 5.9)."),
        # R1.6: p 值不在表内（表 caption 明说 quoted in the text）
        ("the corrected p-values are reported in the main table",
         "the corrected p-values are quoted in the text alongside Table 4"),
        # R1.9: root-cause 段在 5.7；dataset effects 在 5.3/5.8
        ("**Changes.** Section 5.1 (root-cause paragraph + dataset effects); Section 5.3 (collapsed-seed analysis); per-seed tables in package; all numbers re-run post-fix.",
         "**Changes.** Section 5.7 (root-cause and numerical-stability paragraph); Section 5.3 (separability-ceiling calibration); Section 5.8 (CICIoT downsampling rationale); Section 5.3 (collapsed-seed analysis); per-seed tables in package; all numbers re-run post-fix."),
        # R1.11: 通信开销不在同一表（在 4.1/5.6 文字）
        ("(iii) communication overhead per round (update + evidence payload sizes) in the same table.",
         "(iii) communication overhead per round — model-update payloads under TLS plus the 4-byte evidence and 1-byte reputation scalars on-chain (about 25 KB of ledger data per training job) — documented in the revised Section 5.6 text and the payload classes of Section 4.1."),
        ("**Changes.** Section 5.6 (extended overhead table); Section 6 (controller failure, compromised-infrastructure discussion).",
         "**Changes.** Section 5.6 (gas-saturation boundary, emulation labelling, communication overhead); Section 6 (controller failure, compromised-infrastructure discussion)."),
        # R1.12: empirical latency distribution 未呈现
        ("(ii) The measured part (edge path: on-chain commit + local rule installation) is presented with its empirical latency distribution, and the theory–measurement correspondence is shown: the edge path's flatness in load is measured, the cloud path's divergence is emulated and labelled as such.",
         "(ii) The provenance is now labelled per component: the edge path's flatness (about 3.3 s — deterministic block commit plus local rule installation) is a measurement of the emulated testbed, while the cloud path's divergence is an M/M/1 emulation with parameters set from the emulated workload, so the theory–measurement correspondence is explicit rather than implicit."),
        ("(iii) A sensitivity note reports how the separation changes with arrival rate, service rate, and burstiness (M/M/1 vs bursty arrivals), so the claim's parameter dependence is visible rather than implicit.",
         "(iii) Section 5.6 notes that the separation is robust across utilization because the edge path has no queue to grow, and points to the GI/G/1 limitation for bursty, heavy-tailed arrivals in Section 6.3, so the claim's parameter dependence is visible rather than implicit."),
        # R1.13: 消融表是 Table 8 不是 Table 5
        ("**Changes.** New ablation grid (Table 5 expanded); no-memory ledger ablation; Section 5.7/5.9.",
         "**Changes.** New ablation grid (Table 8); no-memory ledger ablation; Sections 5.7/5.9."),
        # R1.18: 四处失真
        ("**Response.** Notation audit per R1.14; Fig. 1 and Fig. 3 redrawn in standard SCI architecture style (swim-lane planes, numbered flows, no in-figure titles — captions carry the titles); the redundant Fig. 4 deleted with its content absorbed into text; legends of Figs. 6–7 repositioned to a no-occlusion corner (Editor's E4) and the shaded regions explained in captions (E5: the band is the P10–P90 range across seeds); every figure now names the exact data tag it was generated from; references re-verified against CrossRef (two title corrections, one completed venue entry — Editor's E8).",
         "**Response.** Notation audit per R1.14. For figure readability, Figs. 1–3 were re-rendered for this revision with enlarged label fonts and numbered-flow badges (the swim-lane style of the submitted version is retained), and figure titles are carried by the captions rather than in-figure text; the legends of Figs. 6–7 were repositioned into whitespace (Editor's E4) and the shaded regions explained in captions (E5: the band of Fig. 7 is the mean$\\pm$std band over the 5 seeds; the P10–P90 band appears in Fig. 8's reputation trajectories); the reproducibility package documents the exact data tag each figure is generated from, and figure-number references were re-verified against the experiments; references re-verified against CrossRef (two title corrections, one completed venue entry — Editor's E8)."),
        ("**Changes.** Figs. 1, 3 (redraw); Fig. 4 (removed); Figs. 6–7 (legends/shading); References (E8); global notation pass.",
         "**Changes.** Figs. 1–3 (re-rendered, larger labels/badges); Figs. 6–7 (legends), Fig. 7 (band statistic in caption); references (E8); global notation pass."),
    ],
    "response_editor1.md": [
        # E5: Fig.7 的带是 mean±std（P10–P90 是 Fig.8）
        ("5. **Shaded regions in Fig. 7 explained.** The caption now states that the shaded band is the P10–P90 range across seeds (min–max whiskers in the earlier caption text have been unified with the actual plotted statistic). ✅",
         "5. **Shaded regions in Fig. 7 explained.** The caption now names the plotted statistic explicitly: the band is the mean$\\pm$std range over the 5 seeds (the earlier caption did not name the statistic; the P10–P90 band belongs to Fig. 8's reputation trajectories and is labelled there). ✅"),
    ],
    "response_reviewer2.md": [
        # R2.3 Changes: β=0.5 在 Table 6/§5.9
        ("**Changes.** Section 5.9 (all three studies); Section 5.4 (β extended to 0.5); Section 4.6 (scope).",
         "**Changes.** Section 5.9 (all three studies, Table 6); Section 5.4 (pointer to the $\\beta{=}0.5$ breaking-point extension, reported in Section 5.9); Section 4.6 (scope)."),
    ],
    "rebuttal_round1.md": [
        # 合并版同步（同 response_reviewer1 的全部 + E5 + R2.3）
        ("All sweep points are 3-seed means with std reported; the sensitivity study identifies the two genuinely sensitive parameters ($T_s$ and $\\theta_h$) and the flat regions that justify the default configuration.",
         "All sweep points are 3-seed means with std reported. The sweep (Section 5.9) locates the defaults near local optima and its profile is itself informative: the gate temperature is deliberately flat across $T_s \\in \\{0.1, 0.5\\}$ (confirming that the softmax form distinguishes by *degree* rather than a knife-edge threshold), the reward threshold and quorum size are mildly monotone, and the single genuinely harmful setting is over-tight clipping ($\\kappa_c=1$, about 6 points) — the one parameter the asymmetry analysis of Section 6.2 warns about."),
        ("**Changes.** New sensitivity subsection with tables/plots for $T_s$, $\\kappa_c$, $\\theta_h$, $\\theta_m$, $K$, root size; Section 5.4.",
         "**Changes.** Sensitivity sweep in Section 5.9 ($T_s$, $\\kappa_c$, $\\theta_h$, $K$, root size; each point 3 seeds with std); Section 5.4 ($\\beta$ sweep, with the $\\beta{=}0.5$ extension in Section 5.9)."),
        ("the corrected p-values are reported in the main table",
         "the corrected p-values are quoted in the text alongside Table 4"),
        ("**Changes.** Section 5.1 (root-cause paragraph + dataset effects); Section 5.3 (collapsed-seed analysis); per-seed tables in package; all numbers re-run post-fix.",
         "**Changes.** Section 5.7 (root-cause and numerical-stability paragraph); Section 5.3 (separability-ceiling calibration); Section 5.8 (CICIoT downsampling rationale); Section 5.3 (collapsed-seed analysis); per-seed tables in package; all numbers re-run post-fix."),
        ("(iii) communication overhead per round (update + evidence payload sizes) in the same table.",
         "(iii) communication overhead per round — model-update payloads under TLS plus the 4-byte evidence and 1-byte reputation scalars on-chain (about 25 KB of ledger data per training job) — documented in the revised Section 5.6 text and the payload classes of Section 4.1."),
        ("**Changes.** Section 5.6 (extended overhead table); Section 6 (controller failure, compromised-infrastructure discussion).",
         "**Changes.** Section 5.6 (gas-saturation boundary, emulation labelling, communication overhead); Section 6 (controller failure, compromised-infrastructure discussion)."),
        ("(ii) The measured part (edge path: on-chain commit + local rule installation) is presented with its empirical latency distribution, and the theory–measurement correspondence is shown: the edge path's flatness in load is measured, the cloud path's divergence is emulated and labelled as such.",
         "(ii) The provenance is now labelled per component: the edge path's flatness (about 3.3 s — deterministic block commit plus local rule installation) is a measurement of the emulated testbed, while the cloud path's divergence is an M/M/1 emulation with parameters set from the emulated workload, so the theory–measurement correspondence is explicit rather than implicit."),
        ("(iii) A sensitivity note reports how the separation changes with arrival rate, service rate, and burstiness (M/M/1 vs bursty arrivals), so the claim's parameter dependence is visible rather than implicit.",
         "(iii) Section 5.6 notes that the separation is robust across utilization because the edge path has no queue to grow, and points to the GI/G/1 limitation for bursty, heavy-tailed arrivals in Section 6.3, so the claim's parameter dependence is visible rather than implicit."),
        ("**Changes.** New ablation grid (Table 5 expanded); no-memory ledger ablation; Section 5.7/5.9.",
         "**Changes.** New ablation grid (Table 8); no-memory ledger ablation; Sections 5.7/5.9."),
        ("**Response.** Notation audit per R1.14; Fig. 1 and Fig. 3 redrawn in standard SCI architecture style (swim-lane planes, numbered flows, no in-figure titles — captions carry the titles); the redundant Fig. 4 deleted with its content absorbed into text; legends of Figs. 6–7 repositioned to a no-occlusion corner (Editor's E4) and the shaded regions explained in captions (E5: the band is the P10–P90 range across seeds); every figure now names the exact data tag it was generated from; references re-verified against CrossRef (two title corrections, one completed venue entry — Editor's E8).",
         "**Response.** Notation audit per R1.14. For figure readability, Figs. 1–3 were re-rendered for this revision with enlarged label fonts and numbered-flow badges (the swim-lane style of the submitted version is retained), and figure titles are carried by the captions rather than in-figure text; the legends of Figs. 6–7 were repositioned into whitespace (Editor's E4) and the shaded regions explained in captions (E5: the band of Fig. 7 is the mean$\\pm$std band over the 5 seeds; the P10–P90 band appears in Fig. 8's reputation trajectories); the reproducibility package documents the exact data tag each figure is generated from, and figure-number references were re-verified against the experiments; references re-verified against CrossRef (two title corrections, one completed venue entry — Editor's E8)."),
        ("**Changes.** Figs. 1, 3 (redraw); Fig. 4 (removed); Figs. 6–7 (legends/shading); References (E8); global notation pass.",
         "**Changes.** Figs. 1–3 (re-rendered, larger labels/badges); Figs. 6–7 (legends), Fig. 7 (band statistic in caption); references (E8); global notation pass."),
        ("5. **Shaded regions in Fig. 7 explained.** The caption now states that the shaded band is the P10–P90 range across seeds (min–max whiskers in the earlier caption text have been unified with the actual plotted statistic). ✅",
         "5. **Shaded regions in Fig. 7 explained.** The caption now names the plotted statistic explicitly: the band is the mean$\\pm$std range over the 5 seeds (the earlier caption did not name the statistic; the P10–P90 band belongs to Fig. 8's reputation trajectories and is labelled there). ✅"),
        ("**Changes.** Section 5.9 (all three studies); Section 5.4 (β extended to 0.5); Section 4.6 (scope).",
         "**Changes.** Section 5.9 (all three studies, Table 6); Section 5.4 (pointer to the $\\beta{=}0.5$ breaking-point extension, reported in Section 5.9); Section 4.6 (scope)."),
    ],
}

BASE = r"D:\workbuddy\CMC0930\paper"
total = 0
for fname, pairs in EDITS.items():
    p = BASE + "\\" + fname
    t = io.open(p, encoding="utf-8").read()
    for old, new in pairs:
        if old not in t:
            print("MISS in %s: %s..." % (fname, old[:70]))
            continue
        assert t.count(old) == 1, "non-unique in %s: %s..." % (fname, old[:50])
        t = t.replace(old, new, 1)
        total += 1
    io.open(p, "w", encoding="utf-8").write(t)
print("applied", total, "edits")
