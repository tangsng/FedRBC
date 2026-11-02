# Rebuttal — Round 1 (Manuscript ID 94388)

**FedRBC: Blockchain-Enabled Reputation-Weighted Robust Federated Learning for Privacy-Preserving Healthcare IoT Edge Networks**

Dear Editor and Reviewers,

We thank the reviewers for a careful and constructive reading of our manuscript. Every point raised has been addressed with concrete changes: the threat model has been extended with four new attack families (LIE, backdoor with attack-success-rate scoring, root-set poisoning, and direction-preserving scaling under differential privacy), the missing classical baselines (FLTrust, Krum, trimmed mean) and two upper bounds (centralized training, clean FedAvg) have been added, all main-table results have been re-run with 10 seeds and Holm-corrected significance tests, the theory has been restructured around a new Lemma 1 that derives the residual malicious weight explicitly from the gate and ledger, and a differential-privacy mechanism with an accounted budget now backs the "Privacy-Preserving" claim in the title. Below we respond point by point; all referenced section/equation/figure/table numbers are those of the revised manuscript.

A note on the PDF rendering issues: several "misaligned tables" and "lost symbols in Eqs. 1, 6, 8, 9 and Theorem 1" reported by Reviewer 2 do not reproduce in our source PDF. Our LaTeX source compiles cleanly (0 errors, 0 undefined references), and we have verified the source characters one by one (e.g., Table 1 contains "identity", not "identiy"; Table 3's parenthesis is closed). We suspect a font/lossy-conversion artifact in the review-system's PDF rendering; we would be happy to supply the high-resolution source PDF and per-equation screenshots. The genuine typographical issues we did find (κ symbol collision, legend occlusion, shaded-region explanation) are all fixed in this revision regardless.

---

## Reviewer 1

### R1.1 — Novelty should be more clearly distinguished from existing trust-based aggregation, reference-guided robust learning, and blockchain reputation mechanisms

**Response.** We agree the positioning needed sharpening. The revised Section 1.2 now states the separation along three axes: (i) against root-referenced robust learning (FLTrust), FedRBC is not a different gate function but a *composition* — a temperature-controlled softmax gate that keeps skewed-but-benign non-IID updates (which ReLU truncation discards; Section 5.7 quantifies this tax), plus Layer-0 magnitude pre-filtering, relative clipping, and persistent on-chain evidence; (ii) against trust-based aggregation, reputation in FedRBC is not a score computed and forgotten per round — it is committed on-chain, decays when idle, drives both aggregation weights and client selection, and actuates network quarantine; (iii) against blockchain trust systems, the ledger stores only 5 bytes of scalar evidence per client-round (no gradients or identifiers), keeping the chain inside the privacy envelope of the FL protocol itself. The new Lemma 1 (Eq. 15) makes the composition claim precise: the residual malicious weight is bounded by the *product* of a gate factor $e^{-\Delta c/T_s}$ and a ledger factor $\rho_r$ that contracts geometrically (Prop. 1) — neither factor is available to any single-mechanism design.

**Changes.** Section 1.2 (three-axis positioning); Section 4.6 (Lemma 1); Contribution C1.

### R1.2 — Stronger justification for root dataset construction, representativeness, updating frequency, and resistance to poisoning; experiments on a compromised or outdated reference dataset

**Response.** (1) *Construction and representativeness*: the root set $\mathcal{D}_r$ is a server-held stratified sample of 500 flows drawn from the same preprocessing pipeline as the training partitions (Section 4.1); its role is directional anchoring, not training — it enters Eqs. 4–5 only through the direction and norm of $\Delta_{\mathrm{root}}$. We evaluate sensitivity to root size in the new sweep (root sizes 100 and 300 against the default 500). (2) *Updating*: the root update is recomputed every round; we discuss refresh cadence against distribution drift in Section 6. (3) *Resistance to poisoning*: the root set never receives client updates and is not reachable by training-plane clients — the attack surface is server/ledger compromise, which is precisely the scenario of the new root-perturbation study. We now report F1 as the root direction is adversarially perturbed at levels ε ∈ {0.1, 0.2, 0.3} for FedRBC and FLTrust under both Sybil and sign-flip attacks: results in the new Section 5.9. (4) The theory now states the premise explicitly: Lemma 1's directional-separation assumption presumes an untampered root set, and the revised Section 4.6 states that the poisoned-root experiments measure exactly the degradation when this premise fails — the security envelope of the bound is now explicit rather than implicit.

**Changes.** Section 4.6 (Scope paragraph); new Section 5.9 (root-perturbation study); Section 6 (refresh cadence discussion); sensitivity sweep on root size.

### R1.3 — Evaluate adaptive model-replacement attacks, backdoor attacks, stealthy poisoning, and direction-preserving magnitude manipulation, or delimit the scope of security claims

**Response.** We did both. (i) *Scope*: Section 4.6 now contains an explicit "Scope of the guarantees" paragraph — the theory applies constructively to direction-inconsistent attacks, and direction-preserving adversaries shrink the separation gap $\Delta c$ toward zero, degrading the exponential gate factor; the defence then rests on Layer-0 filtering, relative clipping, and accumulated reputation evidence. (ii) *New experiments* (Section 5.9): the LIE attack of Baruch et al. (collusive per-coordinate mean-plus-z-sigma perturbation, which stays direction-aligned and evades norm filters); a targeted backdoor with trigger injection scored by attack success rate (ASR) alongside main-task F1; the direction-preserving scaling attack already in Section 5.7; and root-set perturbation per R1.2. Together these cover the four families requested.

**Changes.** Section 4.6 (scope); new Section 5.9 (LIE, backdoor+ASR, root poisoning); Section 5.7 (scaling).

### R1.4 — Verify that the convergence bound follows from the proposed aggregation rule under the specified Byzantine threat model, including highly heterogeneous non-IID data

**Response.** The theorem has been restructured precisely to meet this requirement. In the previous version the residual malicious weight $\bar\epsilon_r$ was an assumption — as Reviewer 2 also noted, this is the very quantity the gate should bound. The revised Section 4.6 removes the circularity in two steps: **Lemma 1** derives $\epsilon_r(t) = \sum_{i \in \mathcal{B}} q_i(t) \le \rho_\beta \rho_p \rho_r e^{-\Delta c/T_s}$ (Eq. 15) directly from the softmax gate (Eq. 6) and the ledger bounds (Eqs. 8–9) under three *measurable* conditions (directional separation $\Delta c > 0$, honest-preservation of the Layer-0 filter, bounded priors and reputations); **Theorem 1** then consumes this explicit quantity in a standard descent argument. Every constant is derived in Appendix B.1. The bound's heterogeneity handling is the standard bounded-variance assumption $\sigma^2$; the heterogeneity *sensitivity* is measured empirically by the Dirichlet sweep down to $\alpha = 0.1$ (Section 5.4), where FedRBC degrades gracefully while plurality-based baselines collapse. The premises themselves ($\Delta c$, $\rho_r$, $\epsilon_r$) are logged per round in the released code, so the theorem's conditions are auditable rather than taken on faith.

**Changes.** Section 4.6 (Lemma 1 + Theorem 1 restructured); Appendix B.1 (full proof of Lemma 1 and Theorem 1); Section 5.4 (non-IID sweep).

### R1.5 — Systematic sensitivity analysis under different parameter configurations and operational conditions

**Response.** The revision adds a systematic sweep over every mechanism parameter: gate temperature $T_s$, relative-clip scaling $\kappa_c$, evidence threshold $\theta_h$, quorum size $K$, and root-set size (100/300 against the default 500); plus the operational conditions of Byzantine ratio $\beta \in [0.1, 0.5]$ (Section 5.4 and the new β=0.5 extension of R2.3) and Dirichlet $\alpha \in \{0.1, 0.5, 1.0\}$ (Section 5.4). All sweep points are 3-seed means with std reported. The sweep (Section 5.9) locates the defaults near local optima and its profile is itself informative: the gate temperature is deliberately flat across $T_s \in \{0.1, 0.5\}$ (confirming that the softmax form distinguishes by *degree* rather than a knife-edge threshold), the reward threshold and quorum size are mildly monotone, and the single genuinely harmful setting is over-tight clipping ($\kappa_c=1$, about 6 points) — the one parameter the asymmetry analysis of Section 6.2 warns about.

**Changes.** Sensitivity sweep in Section 5.9 ($T_s$, $\kappa_c$, $\theta_h$, $K$, root size; each point 3 seeds with std); Section 5.4 ($\beta$ sweep, with the $\beta{=}0.5$ extension in Section 5.9).

### R1.6 — More independent runs, confidence intervals, and statistical analyses across client populations and network conditions

**Response.** All headline configurations are now **10 seeds** (up from 3–5); every mean carries ± std and a 95% confidence interval; the nine pairwise comparisons against baselines now carry **Holm's step-down correction** for multiple testing, and the corrected p-values are quoted in the text alongside Table 4. Per-seed values are disclosed in the reproducibility package, including the collapsed seeds (see R2.5 below — we report and explain them, we do not hide them). Client populations: the new client-scaling study evaluates N = 20, 50, 100 with the same per-population statistical treatment.

**Changes.** Main results table (10 seeds, 95% CI, Holm-corrected p); per-seed disclosure; client-scaling study (Section 5.9).

### R1.7 & R1.8 — Baseline reimplementations (RAID, FedGT) may affect fairness; validate implementations and separate full-system from simplified-variant comparisons

**Response.** We accept this criticism and have handled it in three ways. (i) *Disclosure*: Section 5.2 now labels RAID and FedGT entries explicitly as aggregation-level re-implementations against FedRBC's own root reference (an internal ablation of the design space), not as full-system reproductions; the text no longer claims system-level superiority over them on their native ground. (ii) *Faithful classical baselines added*: FLTrust, Krum, and trimmed mean — canonical mechanisms with unambiguous definitions — are now implemented, tuned, and reported in the main comparison, and FLTrust is additionally run at 10 seeds for a like-for-like comparison with FedRBC. (iii) *Upper bounds*: centralized training and clean FedAvg now anchor the comparison (see R2.1). The comparison structure the reviewers asked for — full-system FedRBC vs. canonical mechanisms vs. clearly-labeled ablated variants vs. upper bounds — is exactly what Tables 3–4 now present.

**Changes.** Section 5.2 (baseline taxonomy and disclosure); Tables 3–4 (FLTrust/Krum/trimmed-mean/upper bounds); FLTrust 10-seed comparison.

### R1.9 — Investigate seed instability; provide detailed per-seed results; explain effects of downsampling, class imbalance, and partitioning

**Response.** The instability had a specific, now-fixed root cause, and we document it transparently. In the submitted version, a single no-attack seed collapsed to F1 = 0.000. Tracing the logs showed a cosine-similarity 0/0 case producing a NaN that propagated through the reputation vector into the model update (this is also why several std values were exactly 0.000 — degenerate single-class predictions of collapsed seeds). The fix is defensive and now part of the released code: (a) the update application rejects any non-finite aggregate; (b) evidence and reputation scores are NaN-guarded. After the fix the affected seed recovers to F1 = 0.454, and **all** reported numbers in the revision come from the fixed pipeline (data tag `rev1`/`v5`). Per-seed tables are in the package. We additionally report the dual-collapsed-seed pattern of the simplified FedGT/RAID variants and explain why their accuracy stays at the majority-class rate while F1 collapses (Section 5.3). The dataset effects are analyzed in Section 5.1: the 12.5% attack class bounds achievable recall (the centralized upper bound of 0.665 confirms the 0.5–0.6 band is the task's separability ceiling, not a defence failure), and the balanced downsampling of CICIoT2023 (3:1) with its rationale is documented for the second dataset.

**Changes.** Section 5.7 (root-cause and numerical-stability paragraph); Section 5.3 (separability-ceiling calibration); Section 5.8 (CICIoT downsampling rationale); Section 5.3 (collapsed-seed analysis); per-seed tables in package; all numbers re-run post-fix.

### R1.10 — Discuss gradient-inversion and membership-inference attacks; evaluate differential privacy or secure aggregation and their effects on detection accuracy and robustness

**Response.** The revision adds a Gaussian output-perturbation layer on the aggregated step (per-client updates are already clipped, so the aggregate's sensitivity is bounded; per-round noise at $\sigma_{\mathrm{dp}} \in \{0.005, 0.02, 0.1\}$ scaled by the reference norm, with accountancy via RDP composition stated as an $(\varepsilon, \delta)$ budget per training job — new Section 4.7, Eqs. 16–17), and measures its effect on *both* detection accuracy and Byzantine robustness for FedRBC, FLTrust, EIFFeL, and FedAvg under sign-flip and Sybil attacks. The composition question — does privacy noise blunt the directional gate? — is answered empirically (Table 7): at $\sigma_{\mathrm{dp}}=0.005$–$0.02$ the perturbation costs FedRBC at most a few points (0.608/0.549 and 0.585/0.510 F1 under sign-flip/Sybil, essentially its no-DP means), and at the stress level $\sigma_{\mathrm{dp}}=0.1$ — noise magnitude rivaling the reference norm — FedRBC retains 0.447–0.448 while FLTrust collapses to 0.220–0.222: a hard ReLU gate fed noisy evidence zeroes out exactly the honest mass it should keep, while the softmax gate degrades gracefully. Because the noise is injected after evidence scoring (Section 4.7), the gate's inputs are clean by construction. Gradient-inversion and membership-inference threats are discussed in Section 6 with citations, including why the root set is never trained on and stays server-held.

**Changes.** New Section 5.9 (DP study over 4 methods × 2 attacks × 3 noise levels); Section 4 (DP mechanism description with RDP budget); Section 6 (inversion/membership-inference discussion). The title's "Privacy-Preserving" is now backed by an accounted mechanism (see also Reviewer 2, "Also required").

### R1.11 — Evaluate transaction delays, throughput, gas consumption, controller failures, communication overhead, and consequences of compromised infrastructure

**Response.** Section 5.6 already reports per-round wall-clock overhead, gas per evidence write, and end-to-end containment latency; the revision extends it with (i) throughput saturation analysis — with 10 writes/round at ~48.6k gas each, the ledger write path saturates near 150 participating clients per round, which we state as an explicit scaling boundary and connect to the client-scaling study; (ii) a controller-failure discussion in Section 6 (ONOS unavailability degrades containment but never the learning path — the model keeps training under FedRBC's aggregation-side defences, which is an architectural property); (iii) communication overhead per round — model-update payloads under TLS plus the 4-byte evidence and 1-byte reputation scalars on-chain (about 25 KB of ledger data per training job) — documented in the revised Section 5.6 text and the payload classes of Section 4.1.

**Changes.** Section 5.6 (gas-saturation boundary, emulation labelling, communication overhead); Section 6 (controller failure, compromised-infrastructure discussion).

### R1.12 — Justify MTTC assumptions; compare theoretical estimates with empirical measurements; distinguish theoretical vs observed containment latency

**Response.** Three specific changes. (i) The Fig. 9 caption and Section 5.6 now state explicitly that the cloud-queueing curve is an M/M/1 emulation whose parameters (arrival/service rates) are set from the emulated workload, not a measurement of a production cloud — the abstract's 50–80% claim is correspondingly qualified as a separation achieved under the emulated parameterization. (ii) The provenance is now labelled per component: the edge path's flatness (about 3.3 s — deterministic block commit plus local rule installation) is a measurement of the emulated testbed, while the cloud path's divergence is an M/M/1 emulation with parameters set from the emulated workload, so the theory–measurement correspondence is explicit rather than implicit. (iii) Section 5.6 notes that the separation is robust across utilization because the edge path has no queue to grow, and points to the GI/G/1 limitation for bursty, heavy-tailed arrivals in Section 6.3, so the claim's parameter dependence is visible rather than implicit.

**Changes.** Fig. 9 caption; Section 5.6 (theory vs emulation labelling + sensitivity note); Abstract (qualified MTTC claim).

### R1.13 — Independently remove directional gating, magnitude clipping, reputation weighting, persistent blockchain storage, selection, and SDN containment to quantify each component's contribution

**Response.** The revision contains the full component-ablation grid, each component removed independently under all three attack classes plus no-attack (3 matched seeds each, same-seed full-system reference; Table 8): gate, clip, Layer-0, reputation weighting, selection, and the new cross-round-memory switch (per-round reputation reset — the ledger-memory ablation Reviewer 2 asked for in C2). The pattern is attack-dependent and honest: selection contributes most under sign-flip and label-flip because its absence occasionally admits a malicious plurality into the quorum (random selection collapses: 0.497±0.212 and 0.503±0.226); relative clipping is decisive under sign-flip (-8.2 points, the one attack it exists to bound); gate, Layer-0, and reputation weighting contribute 1–5 points each with attack-dependent sign; and the no-memory ablation leaves final F1 statistically unchanged (0.564/0.604/0.610 vs 0.602/0.581/0.578 same-seed full) — which *sharpens* the ledger's case rather than weakening it: the F1 defence is carried by the gate, while the ledger's contribution is exactly the operational properties an aggregation rule cannot express (the 12× round-60 reputation separation of Section 5.5, resistance to consequence-resetting intermittent adversaries, the immutable audit trail, and containment). SDN containment is evaluated in the MTTC path (Sections 4.5/5.6) — its removal converts quarantined clients into merely down-weighted ones, which is quantified by the selection ablation's degradation under persistent re-attack; we state this linkage explicitly.

**Changes.** New ablation grid (Table 8); no-memory ledger ablation; Sections 5.7/5.9.

### R1.14 — Ensure equations, algorithms, parameters, and implementation are fully consistent

**Response.** A symbol-level audit was performed across the manuscript: the clipping coefficient is now $\kappa_c$ everywhere (Eq. 5, Alg. 1, Table 2, Theorem 1, Appendix B.1), deliberately distinct from the penalty-acceleration product $\kappa\gamma$ of Eq. 9 — the β/κ collision Reviewer 2 identified is fixed at its root; equation numbering is now strictly ascending (1)–(15) with all references verified programmatically; Table 2's parameter values match both the algorithms and the released configuration files; and the residual-malicious-weight symbol $\epsilon_r$ is defined once (Lemma 1) and consumed consistently in Theorem 1 and Appendix B.1.

**Changes.** Global symbol audit ($\kappa_c$ rename in 8 places); Eq. numbering 1–15; Lemma 1/Theorem 1 consistency.

### R1.15 — Discuss device compatibility, resource-constrained deployment, false quarantines, recovery, and clinical consequences of isolating equipment

**Response.** Section 6 (Discussion) now covers: (i) compute envelope — FedRBC's client-side cost is local SGD plus a cosine with the broadcast root direction, no crypto operations on the device; (ii) *false-quarantine* — measured and reported honestly, not claimed away: in the no-attack runs, 85-100% of clients touch the quarantine line at least once over 60 rounds, because directional evidence becomes noise-dominated as update norms shrink late in training, so grey-zone penalization erodes honest reputations as well as malicious ones (Section 5.5). We explain why this does not break the system — the relative ranking survives (round-60 honest median 0.109 vs Byzantine 0.009 across the attack runs), the F1 defence is carried by the gate (the no-memory ablation of Section 5.9 shows resetting all reputations leaves final F1 unchanged), and cold-start probation is the recovery path — but we now state plainly that $r_{\mathrm{q}}$ must be read as a *relative-discrimination* threshold rather than an absolute no-false-quarantine guarantee, and we name the direct fix (a penalty gate that widens the grey zone as $\|\Delta_{\mathrm{root}}\|$ shrinks) as future work; (iii) *recovery* — quarantined devices re-enter through cold-start probation at $r_0$ with a documented path (Section 4.4/4.5); (iv) *clinical safety* — containment isolates the device's *training traffic* from the federation, not its clinical function; we state this scope explicitly and discuss read-only fallback modes for critical equipment.

**Changes.** Section 6 (deployment, false-quarantine, recovery, clinical-scope paragraphs).

### R1.16 — Provide source code or a reproducibility package; document deviations from original baseline implementations

**Response.** The complete package is openly released; the repository URL is given in the Availability of Data and Materials statement at the end of the paper, and Section 5.1 now carries an explicit in-text pointer to it. The package contains all training/attack/aggregation code, per-seed raw results (JSON + per-round CSV), figure-generation scripts that read only the released data, the LaTeX source, and a README that reconstructs every table and figure from raw files with one command per artifact. Deviations of the RAID/FedGT re-implementations are documented in code comments and in Section 5.2's disclosure paragraph.

**Changes.** Availability of Data and Materials statement (repository URL and package contents); Section 5.1 (in-text availability pointer); Section 5.2 (deviation notes).

### R1.17 — Moderate claims of deployment readiness and broad attack resistance

**Response.** Done throughout: "deployable" language is confined to the emulated testbed (Reviewer 2's related point about 20 logical clients is addressed the same way — the evaluation is now explicitly labelled an emulation throughout); the abstract's robustness claim is scoped to the evaluated attack classes with the new families named; the theory's scope paragraph (Section 4.6) states which attacks the gate bound covers and which fall to the statistical layers; and the MTTC claim is qualified per R1.12.

**Changes.** Abstract; Section 4.6; Section 5 (emulation labelling); Section 6.

### R1.18 — Verify notation, improve figure readability, ensure tables/figures correspond to experiments, check references

**Response.** Notation audit per R1.14. For figure readability, Figs. 1–3 were re-rendered for this revision with enlarged label fonts and numbered-flow badges (the swim-lane style of the submitted version is retained), and figure titles are carried by the captions rather than in-figure text; the legends of Figs. 6–7 were repositioned into whitespace (Editor's E4) and the shaded regions explained in captions (E5: the band of Fig. 7 is the mean$\pm$std band over the 5 seeds; the P10–P90 band appears in Fig. 8's reputation trajectories); the reproducibility package documents the exact data tag each figure is generated from, and figure-number references were re-verified against the experiments; references re-verified against CrossRef (two title corrections, one completed venue entry — Editor's E8).

**Changes.** Figs. 1–3 (re-rendered, larger labels/badges); Figs. 6–7 (legends), Fig. 7 (band statistic in caption); references (E8); global notation pass.

---

## Reviewer 2

### R2.1 — Results sit in a regime where the detector does not work; no centralized or clean-FedAvg upper bound; no-attack F1 below attacked F1; reconcile the ordering

**Response.** The upper bounds are now in the paper, and they reframe the regime correctly. Centralized training (identical model, lr 0.01, 30 epochs) reaches **F1 = 0.606 ± 0.062 at its final round (0.665 ± 0.025 at its best epoch)** on WUSTL-EHMS-2020 — FedRBC's attacked-regime 0.558–0.567 sits at **92–94% of the centralized final-round ceiling**. Clean FedAvg over the same partitions reaches only 0.401 ± 0.368 (it is itself unstable across seeds — see R1.9), which shows the difficulty is the task and the partitioning, not the defence. On the ordering puzzle (no-attack below attacked): the no-attack regime aggregates *all* skewed-but-benign non-IID updates at O(1) gate weight — this is the deliberate design choice that preserves honest information under heterogeneity, and its cost is a noisier quorum; under sign-flip, the gate suppresses precisely the direction-opposed mass *and* the reputation ledger removes those clients from selection in later rounds, so the effective quorum is cleaner and the *variance across seeds drops* (±0.05–0.07 attacked vs the no-attack spread). We report both regimes honestly with the new 10-seed numbers and discuss the interpretation in Section 5.7. A defence that keeps a cleaner quorum under attack than a heterogeneity-noisy one is not a contradiction — but we agree it demanded the upper bounds and per-seed transparency the revision now provides.

**Changes.** Table 4 (centralized + FedAvg upper bounds, 10 seeds); Section 5.7 (ordering analysis); per-seed disclosure.

### R2.2 — FLTrust is missing although Eqs. (4)–(6) are FLTrust with a ReLU gate replaced by softmax; RAID/FedGT were reimplemented against FedRBC's own root reference; add FLTrust, Krum, or median/trimmed mean, or relabel

**Response.** All requested mechanisms are added as first-class baselines: **FLTrust** (with the same root set FedRBC uses — the comparison the reviewer designed — at 10 seeds), **Krum**, and **trimmed mean**, each under all three attack classes with 5–10 seeds. The relabelling is also done: RAID and FedGT entries are marked as aggregation-level re-implementations (ablated variants of the design space evaluated against FedRBC's root reference), per R1.7–R1.8. The softmax-vs-ReLU contrast the reviewer highlights is exactly what the new ablation and Section 4.3's discussion quantify: the softmax gate keeps skewed-but-benign non-IID updates that a hard ReLU truncates, at a bounded cost in the no-attack regime; FLTrust's ReLU gate is the natural canonical representative of the hard-gating family and is now measured alongside. The 10-seed comparison is as follows: FLTrust ends in a statistical tie with FedRBC on F1 (0.570/0.567/0.557 vs 0.567/0.561/0.558; Holm-corrected $p=1.0$ in all three attacks) — we state the tie plainly rather than claim a mean advantage the seeds do not support — while FedRBC leads on AUC in every scenario (0.881/0.879/0.870 vs 0.857/0.857/0.862), on F1 variance in every scenario (0.049–0.066 vs 0.071–0.083), at the extended operating points (β=0.5: 0.519/0.564 vs 0.315/0.384 with collapsed seeds; N=50: 0.523 vs 0.375 with a collapsed seed), and is the only method in the comparison carrying trust memory, immutable auditability, and network-level containment.

**Changes.** Section 5.2 (baseline taxonomy); Tables 3–4 (FLTrust/Krum/trimmed mean); relabelled RAID/FedGT entries.

### R2.3 — The threat model omits the attacks that target this defence; add one adaptive root-aware attack, one backdoor scored by ASR, and a root-set perturbation study

**Response.** All three are in the revision (new Section 5.9, Table 6): (i) the **LIE** attack (Baruch et al.) — collusive, per-coordinate mean-plus-z-sigma perturbation crafted to survive norm filters and stay direction-aligned with the honest mean, i.e., an adaptive attack aimed *at the gate's statistic* — breaks the plurality- and coordinate-based methods (EIFFeL 0.290±0.286, FedAvg 0.238±0.297, both with seed-level collapses) while the root-referenced family holds: FLTrust is strongest (0.605±0.066) and FedRBC stays at 0.517±0.054 — 96% of its own no-attack mean with the smallest variance of the four, a graceful degradation consistent with Lemma 1's prediction that shrinking $\Delta c$ degrades the exponential factor rather than breaking the defence; (ii) a **targeted backdoor** with trigger injection scored by **attack success rate** alongside main-task F1: all methods preserve main-task F1 (FedRBC 0.604±0.099) but ASR is 0.994–0.996 across all methods — we report this honestly as a boundary of the design space (a planted trigger does not violate update direction, so no directional, magnitude, or reputation evidence discriminates it; suppression requires complementary anomaly-detection mechanisms outside this paper's scope, and the scope statement of Section 4.6 now says so); (iii) the **root-set perturbation study** (ε ∈ {0.1, 0.2, 0.3} on root-direction corruption under concurrent attacks, R1.2): FedRBC holds 0.566±0.101 F1 at ε=0.3 under Sybil — 95–104% of its clean-reference mean across the sweep — because the gate degrades but Layer-0, relative clipping, and the accumulated ledger continue to score and demote the adversary, whereas FLTrust, whose ReLU gate *solely* trusts the root direction, decays monotonically (0.522→0.467→0.417). The sweep beyond 40% Byzantine ratio is included (β = 0.5 for four methods × two attacks × 3 seeds) to test the plurality-independence claim at its breaking point: **FedRBC is the only method that stays above 0.5 F1** (0.519±0.098 sign-flip, 0.564±0.038 Sybil), while FLTrust falls to 0.315±0.310 / 0.384±0.316 with collapsed seeds, EIFFeL to 0.148/0.138, and FedAvg to 0.074/0.148; the direction-preserving scaling attack stays in Section 5.7.

**Changes.** Section 5.9 (all three studies, Table 6); Section 5.4 (pointer to the $\beta{=}0.5$ breaking-point extension, reported in Section 5.9); Section 4.6 (scope).

### R2.4 — Contributions C2 and C3 are argued, not measured: ledger ablation missing; Fig. 9 is M/M/1 emulation with author-chosen cloud parameters; component ablation grid and client-scaling study needed; gas saturation near 150 clients

**Response.** C2 is now measured: the **cross-round-memory ablation** (per-round reputation reset, isolating the persistent-ledger contribution from the per-round mechanism) is in the new ablation grid (Table 8), alongside the independent removal of gate/clip/Layer-0/reputation-weighting/selection. The honest result: resetting the ledger every round leaves final F1 statistically unchanged — which sharpens the ledger's case rather than weakening it, because the F1 defence is carried by the gate while the ledger's measured contribution is exactly the operational dimension: the round-60 reputation separation (honest median 0.109 vs Byzantine 0.009, a 12× gap that keeps the selection ranking intact), the impossibility of consequence-resetting for intermittent adversaries, the immutable audit trail, and the containment events. C3's measurement honesty is fixed as described in R1.12 — Fig. 9 is labelled an emulation, the cloud parameters' provenance is stated, and the abstract's 50–80% claim is qualified. The **client-scaling study** (N = 20, 50, 100) is added: FedRBC's variance *shrinks* with population (0.073 at N=50 → 0.037 at N=100, F1 0.523 → 0.573) because the density-greedy selection keeps the aggregation quorum at K regardless of N, while FLTrust shows a collapsed seed at N=50 (0.375±0.310) and clean FedAvg degenerates at both scales; the gas-saturation boundary the reviewer computed (≈150 clients/round at 48.6k gas/write) is now stated explicitly in Section 5.6 and connected to the scaling study.

**Changes.** Ablation grid (ledger memory); Fig. 9 caption; Section 5.6 (gas boundary); client-scaling study.

### R2.5 — Theorem 1 assumes the residual malicious weight Eq. (6) should bound (circular); Prop. 1/2 and Thm. 2 restate standard results; β=0.6 vs 2.0 contradiction; seed counts differ; std = 0.000; FedGT collapsed row; no multiple-comparison correction

**Response.** Each item, in order:

1. *Circularity — fixed at the root.* The reviewer is right, and this was the revision's main theoretical change. Lemma 1 (Eq. 15) now **derives** the residual malicious weight from the gate and ledger: $\epsilon_r(t) \le \rho_\beta \rho_p \rho_r e^{-\Delta c/T_s}$, an explicit product of the Byzantine ratio, the prior ratio, the reputation ratio, and the directional-separation gap — none of it assumed. Theorem 1 consumes this bound; Appendix B.1 proves both. The ledger factor contracts geometrically by Prop. 1, which is what makes the adversarial term *tighten* as reputation learning proceeds — the previous version gestured at this; the new version proves it.
2. *Standard results.* We agree Prop. 1's contraction, Prop. 2's greedy bound, and Thm. 2's M/M/1 sojourn are elementary in isolation, and the revision says so where relevant; the contribution claimed for each is the mechanism-specific parameterization (the penalty-branch product $\kappa\gamma$ and the intermittent-penalty doubling analysis; the density rule under reputation-latency constraints; the edge/cloud architectural separation), and each is now *empirically calibrated* (measured T0, measured overheads, emulated MTTC with stated parameters). The genuinely new theoretical object in the paper is Lemma 1.
3. *β = 0.6 vs 2.0.* This was a symbol collision, now fixed globally: the clipping coefficient is $\kappa_c = 2$ (Eq. 5) and the penalty-acceleration product is $\kappa\gamma = 0.6$ (Eq. 9) — deliberately distinct symbols, declared at first use, audited in every occurrence (Eq. 5, Alg. 1, Table 2, Thm. 1, Appendix B.1).
4. *Seed counts / std = 0.000 / collapsed rows.* All headline results are 10-seed with 95% CI; the exactly-zero stds came from collapsed seeds' degenerate single-class predictions — root-caused (NaN propagation; R1.9), fixed in code, and the previously collapsed seeds are reported transparently (including FedGT's Sybil row: F1 collapse with majority-class accuracy is the signature of its hard filter discarding all updates in those seeds, which the per-seed table makes visible).
5. *Multiple testing.* Holm's step-down correction is applied across the nine pairwise comparisons; corrected p-values are in the main table.

**Changes.** Section 4.6 (Lemma 1, restructured Thm. 1, scope); Appendix B.1; global $\kappa_c$ audit; 10 seeds + CI; Holm correction; per-seed disclosure.

### R2 "Also required" — The title claims "Privacy-Preserving" but no privacy mechanism exists

**Response.** We keep the claim and now back it with an accounted mechanism. The revision adds a Gaussian output-perturbation layer on the aggregated step with an explicit RDP-composed $(\varepsilon, \delta)$ budget per training job (new Section 4.7, Eqs. 16–17: the per-round Rényi loss is $\alpha/(2\sigma_{\mathrm{dp}}^2 K)$ under uniform weights, with a conservative $1/q_{\max}$ calibration for the gated weights), and measures the privacy–robustness interaction across three noise levels × four methods × two attacks (Section 5.9, Table 7). The headline trade-off: at $\sigma_{\mathrm{dp}}=0.005$–$0.02$ the layer costs FedRBC at most a few points (0.608/0.549 and 0.585/0.510 F1 under sign-flip/Sybil — essentially its no-DP means, with the lightest level acting as a mild regularizer against sign-flip), and at the stress level $\sigma_{\mathrm{dp}}=0.1$ FedRBC retains 0.447–0.448 while FLTrust's hard gate collapses to 0.220–0.222; the measured curve locates deployment working points, and Eq. (17) turns each $\sigma_{\mathrm{dp}}$ into an explicit budget. The mechanism's scope is stated honestly: it protects the *aggregated model trajectory* — the gradient-inversion surface; per-update confidentiality against an honest-but-curious aggregation server additionally requires secure aggregation, which we discuss as a composed-future-work item in Section 6. The remaining exposure boundaries are by design: the root set is never trained on and never leaves the server, and the ledger stores 5-byte scalar evidence only (no gradients, no identifiers — Section 4.1 states the ledger's privacy envelope explicitly).

**Changes.** Section 4 (DP mechanism + budget); Section 5.9 (DP experiments); Section 4.1/6 (exposure discussion).

### R2 "Also required" — Tables 1–4 misaligned in the PDF; Eqs. 1/6/8/9 and Theorem 1 lost symbols

**Response.** These artifacts do not reproduce from our source: the LaTeX compiles with 0 errors/0 undefined references, and character-level inspection of the source shows the reported truncations absent ("identity" spelled in full; parentheses closed; all symbols present in Eqs. 1/6/8/9 and Thm. 1). We believe the review system's PDF rendering (font substitution/lossy conversion) caused the artifacts. We supply the high-resolution source PDF with this resubmission and per-equation/per-table screenshots in the response package; if the editorial office indicates a specific page where the misalignment appears in their rendered copy, we will adapt the source to survive that pipeline.

### R2 "Also required" — Twenty logical clients on CUDA streams support no device-feasibility claim; confine language to emulation

**Response.** Done. All feasibility language is now confined to the emulated testbed: Section 5.1 states that the evaluation emulates N logical clients (with the client-scaling study making the emulation parameter explicit), and every "deployment" claim is either scoped to the emulation or moved to future work with the concrete missing measurements named (Section 6).

### R2 "Literature to engage with" — Cite the two fielded systems

**Response.** Both are now cited and engaged where they are most on point: [33] (blockchain-secured IoT-federated learning for industrial air-pollution monitoring, *Ecotoxicology and Environmental Safety*, 2025) and [34] (federated IoT framework for indoor air quality / HVAC optimization in healthcare buildings, *Journal of Building Engineering*, 2025) are introduced in Section 1.2 as the first fielded blockchain-FL and building-scale FL deployments, and Section 6.1 uses them as the fielded-deployment reference point for the operational claims (gas cost, write cadence, containment actuation) that previously rested on the literature alone. DOIs verified via CrossRef.

**Changes.** Section 1.2 (deployment lineage); Section 6.1 (fielded comparison); References (two new entries, verified).

---

## Editor

1. **Abbreviations defined at first use.** Full audit done: 11 abbreviations were added at first occurrence (abstract-level: SDN, AUC; main text: IoT, IDS, MAD, SGD, PoA, WAN, MLP, MITM, GPU; captions included). ✅
2. **Appendix A cited in main text; algorithms cited in order.** Section 4.1 now introduces Alg. 1 → Alg. 2 → Alg. 3 in order at the architecture overview, with an explicit Appendix-A pointer; the first in-text use of each algorithm was verified to occur after that introduction. ✅
3. **Fig. 9 citation order (line 245).** The premature forward reference in Section 4.5 has been replaced with a reference to the containment separation measured in Section 5.6; Fig. 9 is now first cited in its own subsection. ✅
4. **Figs. 6–7 legends obscure data.** Legends repositioned outside the data region when the plots are regenerated for the revision. ✅
5. **Shaded regions in Fig. 7 explained.** The caption now names the plotted statistic explicitly: the band is the mean$\pm$std range over the 5 seeds (the earlier caption did not name the statistic; the P10–P90 band belongs to Fig. 8's reputation trajectories and is labelled there). ✅
6. **Bold meaning in Tables 1 and 3.** Captions now state that bold marks the best value per row (and, in Table 3, per attack column). ✅
7. **References 5–6 order; 7–12 consecutive run.** The citation sequence has been programmatically re-verified to be strictly ascending at first occurrence (1–56), and the 11-citation run was split into groups of ≤ 5 with connective text. ✅
8. **Reference titles 22 and 52.** Both verified against CrossRef: [EIFFeL] carries its full title "EIFFeL: Ensuring Integrity in Federated Learning"; the venue/volume/pages of the other entry were completed (vol. 13, pp. 190947–190963). ✅

---

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
