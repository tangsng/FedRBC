# FedRBC: Blockchain-Enabled Reputation-Weighted Robust Federated Learning for Privacy-Preserving Healthcare IoT Edge Networks

**Song Tang$^{1,2,3}$, Zhigang Jin$^{1,*}$**

$^{1}$School of Electrical and Information Engineering, Tianjin University, Tianjin, China
$^{2}$Institute of Applied Mathematics, Hebei Academy of Sciences, Shijiazhuang, China
$^{3}$Hebei Information Security Authentication Technology Innovation Center, Shijiazhuang, China
$^{*}$Corresponding author

**Funding:** This work was supported by the Hebei Provincial Science and Technology Program Project (Grant No. 25360301D).

---


# Abstract

Federated learning (FL) lets hospital Internet-of-Things (IoT) devices train an intrusion-detection model together without shipping patient telemetry off-site. The arrangement has a known weak point: a small number of compromised devices can poison the model that everyone shares, and current defenses either break down when the attackers cooperate or stop once they have *detected* a problem, leaving no way to actually stop it. We propose FedRBC, a framework that carries the loop through from robust aggregation to network-level quarantine for healthcare IoT edge networks. It has three parts designed as one system: (i) a reputation-weighted aggregation rule pairing root-referenced direction gating with adaptive magnitude clipping, an accounted differential-privacy option, and a Layer-0 pre-filter bounding magnitude attacks; (ii) a smart-contract reputation ledger making each client's trust immutable, auditable, and directly usable by selection and containment; and (iii) a software-defined networking (SDN) containment path isolating a convicted device within a bounded mean time to containment (MTTC). The theory is mechanistic: a new lemma derives the residual malicious weight of the convergence bound *explicitly* from the gate and ledger parameters — direction separation, reputation ratio, and temperature — rather than assuming it, and a closed-form suppression time governs malicious reputation. On a containerized testbed emulating a 20-device hospital (scaled to 100 clients), with ten-seed replication on the main benchmark (WUSTL-EHMS-2020) and a second dataset (CICIoT2023), three attack classes plus extended families (LIE collusive poisoning, targeted backdoors scored by attack success rate, reference poisoning, direction-preserving scaling) and Byzantine ratios up to 50%, FedRBC attains the best AUC and the smallest seed-to-seed variance in every scenario; its F1 matches the strongest classical baseline (FLTrust) and stays significantly ahead of every plurality- and coordinate-based baseline under Sybil collusion (Holm-corrected) while additionally providing trust memory, auditability, and containment that no aggregation-only method expresses. It is the only system that keeps F1 above 0.5 at a 50% Byzantine ratio, retains 92-94% of the centralized final-round F1 under attack, and stays robust when the reference itself is poisoned under Sybil collusion — where single-mechanism root-referenced defenses degrade monotonically. The measured privacy–robustness curve shows the DP option preserving essentially all of the advantage at accounting-grade noise, and the edge containment loop cuts MTTC by 50–80% relative to a cloud-roundtrip baseline under the emulated parameterization, with sub-second per-round overhead.

**Index Terms**—Federated learning, blockchain, reputation system, Byzantine robustness, smart contract, SDN, differential privacy, healthcare IoT, intrusion detection, edge computing.

# 1. Introduction

## 1.1 Background and motivation

Hospital networks are quietly turning into one of the densest Internet-of-Things (IoT) environments around: wearable telemetry patches, bedside monitors, infusion pumps, and imaging gateways push out a steady stream of traffic that is at once safety-critical and privacy-protected. Federated learning (FL) is a natural match for detecting intrusions in that traffic. In the FedAvg formulation of McMahan et al. [1], devices train a shared detection model by minimizing the global empirical risk $F(\mathbf{w}) = \sum_{i=1}^{N} p_i F_i(\mathbf{w})$ over $N$ clients with data weights $p_i$ while exchanging only parameter updates — the training loop our Section 4 framework builds on. The clinical appeal of that arrangement has been argued from the digital-health perspective by Rieke et al. [2], who cast FL as the enabler of multi-institutional model collaboration without patient-data relocation, and demonstrated end-to-end by Kaissis et al. [3], whose privacy-preserving federated pipeline for medical imaging shows that model quality need not be traded away for data sovereignty — the premise a hospital-edge deployment inherits. For intrusion detection specifically, the pairing has accumulated its own evidence base. Hurt et al. [4] compare medical- and network-sourced features for healthcare IDS and find network telemetry indispensable, which supports our choice of flow features as the training signal. Recent systems work then matures the pairing across deployment axes: an end-to-end FL-IDS validation on IoT traffic [5], communication-aware optimization of federated intrusion detection in IoT networks [6], a community-driven hierarchical design for smart homes (HomeGuard) [7] whose multi-tier organization parallels hospital ward structures, quantum-resilient detection for the post-quantum threat horizon [8], incremental learning to track evolving threat landscapes [9], and distributed intrusion detection across large IoT populations [10]. What this literature establishes is accuracy under honest participation; it does not address the case in which a *participant* is the adversary.

The engineering reality of hospital IoT, however, is that devices are also the easiest entry point for attackers. Default credentials, unpatchable firmware, and physically accessible ports make device compromise routine rather than exceptional [11]. Once inside, the adversary's most damaging move is not to steal data but to *corrupt the collective model itself*: by submitting manipulated updates, a few compromised devices can shift the decision boundary of the intrusion detector that every other device relies on — a self-defeating loop in which the defense system becomes the attack vector.

Defending against such Byzantine poisoning is well studied in theory. Krum and its coordinate-wise relatives achieve provable robustness against arbitrary adversary behavior under bounded Byzantine fractions [12], and the statistical-rate analysis of Yin et al. [13] establishes trimmed-mean and median rules as minimax-optimal — the filtering family from which our Layer-0 pre-filter descends. Collusion, however, is the theoretical weak point of that family: the LIE construction of Baruch et al. [14] shows how few coordinated clients suffice to slip past coordinate filtering while remaining direction-aligned — the collusive family our Section 5.9 evaluation adopts — and model-replacement backdoors [15] demonstrate that a single scaled update can overwrite the global model outright under naive averaging. On the optimization side, the non-IID convergence analysis of FedAvg by Li et al. [16] is the tradition our Theorem 1 extends to reputation-weighted aggregation, the survey of Kairouz et al. [17] frames the open problems this work addresses, FedProx [18] tolerates statistical heterogeneity through proximal regularization, and adaptive federated optimization [19] relocates the adaptation burden to the server — complementary handles on the non-IID regime our Dirichlet partitioner instantiates. Even so, three gaps remain when this work is translated to a deployable hospital-edge system. First, **collusion breaks plurality-based defenses**: statistical filters (median, trimmed mean, distance voting, and their recent systematizations [20]) assume that honest updates form a recognizable majority, and a network-level adversary controlling several devices forges that majority. Second, **detection without actuation is operationally hollow**: most robust-FL work ends at a score or a weight, and nothing in the network changes — in a hospital, a detected malicious infusion pump must stop talking to its peers, promptly and provably. Third, **trust has no memory**: per-round scoring [21] forgets everything between rounds, so an adversary can behave intermittently and never accumulate consequences.

## 1.2 Related work and positioning

Three research lines meet at our problem. **Blockchain-enabled FL** couples ledgers with learning for auditability and incentive alignment. DeepChain [22] introduced auditable gradient commitments, tying each training step to a signed on-chain record; FedRBC inherits the audit ideal but commits scalar evidence rather than gradients, cutting the per-round chain payload to bytes rather than model-sized blobs (Section 4.1). Follow-ups anchor the pattern across domains: privacy-preserved data sharing in industrial IoT [23], vehicular analytics with an explicit analysis of design challenges [24], committee-consensus decentralization of the federation itself [25], and blockchained on-device learning that pushes ledger bookkeeping onto end devices [26]. A second wave manages the blockchain-FL resource stack: trustworthy federated edge learning secured by the ledger [27], co-designed FL-and-blockchain IoT frameworks for edge AI [28], and resource management for blockchain-enhanced FL in wireless edge networks [29] — with the composition reaching into metaverse auction mechanisms [30], multi-objective replication optimization in dynamic cloud-edge clusters [31], and private-blockchain platforms for secure urban noise monitoring [32]. The first fielded deployments have now appeared — blockchain-secured FL for industrial air-pollution monitoring with a mechanistic account of data quality [33], and a federated IoT framework for hospital-building indoor-air-quality and HVAC optimization installed across three healthcare sites [34] — and reputation itself has moved on-chain, both as a governance mechanism for decentralized federated learning [35] and as a working demonstration of ledger-backed trust [36]. Yet none of these systems closes the loop from on-chain conviction to network-level containment: robustness remains orthogonal to the ledger, so a poisoned-but-immutably-logged model is still poisoned.

**Robust aggregation** has three current families. Trust-bootstrapped rules gate each update by its agreement with a server-side reference: FLTrust [37] bootstraps that reference from a small root dataset and gates with a ReLU-truncated cosine — the direct premise our Lemma 1 formalizes and the strongest classical baseline our evaluation measures. Statistical filtering discards outliers instead: EIFFeL [20] coordinates per-update integrity checks whose coordinate voting assumes an honest plurality. Reputation-based scoring binds aggregation weight to observed behavior: RAID [21] scores intrusion-detection clients per round but forgets between rounds, RepuFL [38] and ReFLect [39] select mobile-network clients by reputation, and a mean-field-game formulation [40] prices reputation into incentives — selection and incentive uses that our trust-gated quorum generalizes into a containment-consumable score. Identification goes further than scoring: FedGT [41] identifies malicious clients under secure aggregation through a hard decision rule, and TFFL/DRC [42] combines reputation-based consensus with adaptive incentives on-chain. A parallel 2024–2026 wave extends every axis: dual-metric model verification for decentralized vehicular FL with on-chain reputation [43], loss-based greedy aggregation (FedGreed) [44], robustness via loss-based client clustering [45], quantum-secure clustered aggregation [46], personalization and transfer as the route to robustness under heterogeneity [47], cryptographic gradient attestation [48], privacy-preserving Byzantine-robust FL (PPBRFL) [49], and Byzantine-robust aggregation for decentralized FL [50]. Each family fails exactly outside its home attack geometry — the finding our Section 5 evaluation quantifies — and all remain orthogonal to the operational trust root we add.

**Federated IDS for healthcare** has been validated across benchmarks — clinical WUSTL-EHMS, the TON IoT telemetry collection [51], and the large-scale CICIoT2023 attack suite [52] that serves as our second dataset — but evaluates accuracy only: robustness, when assessed at all, targets label noise rather than the model-layer collusion a network-level adversary actually mounts. Table 1 positions FedRBC in this landscape: to our knowledge, it is the first system composing reference gating, magnitude control, and persistent reputation behind a single on-chain trust root, with a measurable containment path.

**Table 1.** Positioning of FedRBC against representative systems. ✓ = full capability, ◐ = partial, ✗ = absent; **bold** marks the strongest capability per column. (✓ = full, ◐ = partial, ✗ = none).

| System | Year | Robust aggregation | Persistent trust | Trust-gated selection | Network containment | Collusion resistance | Evaluation vs. model-layer attacks |
|---|---|---|---|---|---|---|---|
| DeepChain [22] | 2019 | ✗ | ✓ (audit only) | ✗ | ✗ | ✗ | ✗ |
| FLTrust [37] | 2021 | ✓ (root gate) | ✗ | ✗ | ✗ | ◐ | ◐ |
| EIFFeL [20] | 2022 | ✓ (coord. vote) | ✗ | ✗ | ✗ | ✗ | ◐ |
| FedGT [41] | 2025 | ✓ (hard identify) | ◐ | ◐ | ✗ | ✗ | ✗ |
| TFFL/DRC [42] | 2025 | ✓ (subj. logic) | ◐ | ◐ | ✗ | ◐ (on-chain) | ◐ |
| FedGreed [44] | 2025 | ✓ (loss greedy) | ◐ | ◐ | ✗ | ✗ | ✓ |
| RAID [21] | 2026 | ◐ (score) | ◐ (per-round) | ✗ | ✗ | ✗ | ◐ |
| Model verification [43] | 2026 | ◐ (dual metric) | ◐ | ◐ | ✗ | ✓ (on-chain) | ✗ |
| Loss-based clustering [45] | 2025 | ✓ (loss cluster) | ◐ | ◐ | ✗ | ✗ | ✓ |
| **FedRBC** | — | ✓ (ref + clip + softmax) | ✓ (on-chain) | ✓ (Eq. 11) | ✓ (SDN) | ✓ | ✓ |

## 1.3 Contributions

This paper presents FedRBC, a blockchain-enabled reputation-weighted robust FL framework for healthcare IoT edge networks, built around one architectural idea: a single on-chain trust root that drives aggregation, selection, and containment together. Our contributions are:

- **C1 — A reference-guided aggregation with adaptive magnitude control.** The RWRA rule (Eqs. 4, 5–7) combines root-direction gating with a median-absolute-deviation (MAD) pre-filter and a relative clipping radius $\tau_c(t) = \kappa_c\|\Delta_{\mathrm{root}}(t)\|$, covering the direction-inconsistent attack classes (sign-flip, Sybil collusion, label-flip) within one mechanism. The aggregation carries a convergence guarantee in which the residual adversarial weight is bounded *explicitly* by the gate and ledger parameters (Lemma 1, Thm. 1) rather than assumed away.
- **C2 — An operational on-chain reputation contract.** The contract (Alg. 2, Eqs. 8–9) renders per-client trust immutable and auditable, and feeds both aggregation weights and client selection; we prove geometric suppression of persistent adversaries (Prop. 1) and a 1/2-approximation for the selection rule (Prop. 2).
- **C3 — A measurable detection-to-containment loop.** Contract events drive SDN quarantine with an M/M/1 mean-time-to-containment (MTTC) analysis (Thm. 2), measured on an emulated testbed.
- **C4 — A thorough simulation-based evaluation.** Against three recent aggregation-level system variants (RAID-style, FedGT-style, EIFFeL 2022) and three canonical classical baselines (FLTrust, Krum, trimmed mean), under three attack classes plus the extended families (LIE collusive poisoning, targeted backdoor scored by attack success rate, reference poisoning, direction-preserving scaling), Byzantine ratios up to 50%, Dirichlet non-IID down to $\alpha=0.1$, and client populations up to $N{=}100$, with ten seeds and Holm-corrected significance tests anchored by centralized and clean-FedAvg references: FedRBC attains the best AUC and the smallest F1 variance in every scenario, an F1 statistically tied with the strongest classical baseline (FLTrust) and significantly ahead of every plurality- or coordinate-based baseline where those families fail (Sybil collusion, Holm-corrected), and it is the only evaluated method that carries trust memory, immutable auditability, and network-level containment; the DP layer of C1's privacy option is measured across three noise levels.

The remainder of this paper is organized as follows. Section 2 formalizes the system model and threat model. Section 3 states the problem. Section 4 presents the framework architecture and design with theoretical guarantees. Section 5 reports the evaluation. Section 6 discusses limitations, and Section 7 concludes.

# 2. System Model and Assumptions

## 2.1 Network and learning model

The deployment comprises $N$ IoT clients, one edge server, a permissioned blockchain (a consortium of hospital IT, device vendors, and the security operations center), and an ONOS SDN controller. Clients hold disjoint private datasets $\{\mathcal{D}_i\}$ whose label marginals are skewed: each client's marginal follows $\mathbf{q}_i \sim \mathrm{Dir}(\alpha\,\mathbf{1}_C)$ with concentration $\alpha$ and $C$ classes — smaller $\alpha$ yields more heterogeneous (non-IID) partitions. The learning objective is the global empirical risk

$$F(\mathbf{w}) = \sum_{i=1}^{N} p_i F_i(\mathbf{w}), \qquad p_i = \frac{|\mathcal{D}_i|}{\sum_j |\mathcal{D}_j|}, \tag{1}$$

where $F_i$ is client $i$'s local empirical loss. In each round $t \in [T]$, the server selects a quorum $\mathcal{S}_t$ of size $K$; each selected client performs $E$ epochs of local stochastic gradient descent (SGD) from the global model $\mathbf{w}_t$ (learning rate $\eta$, batch size $B_{\mathrm{batch}}$) and returns its update

$$\Delta_i = \mathbf{w}_i - \mathbf{w}_t, \tag{2}$$

where $\mathbf{w}_i$ is the client's post-training local model. The unweighted baseline aggregate (FedAvg) is $\mathbf{w}_{t+1} = \mathbf{w}_t + \eta_g\sum_i p_i\Delta_i$ with global step size $\eta_g$, which a single Byzantine client can corrupt arbitrarily [12].

The server maintains a small root validation set $\mathcal{D}_r$ (500 samples, collected once during commissioning, refreshed quarterly) and computes, with the same optimizer state, the reference update

$$\Delta_{\mathrm{root}} = \mathrm{SGD}^{(E)}(\mathbf{w}_t; \mathcal{D}_r, \eta) - \mathbf{w}_t, \tag{3}$$

which serves as the directional compass for all evidence evaluation. The root set is the single trust anchor of the system; Section 2.3 analyzes its compromise.

## 2.2 Adversary model

We consider an adversary controlling at most $f < N/2$ devices ($\beta = f/N$, up to 40% in evaluation), whose principal weapon is *directional* manipulation of model updates, formalized as three attack classes:

- **Sign-flipping.** The adversary negates its update, directly opposing the descent direction.
- **Sybil collusion.** Strictly stronger: all compromised devices submit the *same* forged direction (the negated, amplified mean honest direction), manufacturing a malicious plurality that defeats majority-vote and distance-based defenses.
- **Data-layer poisoning (label flipping).** The adversary flips local labels before training; the resulting update is direction-inconsistent with $\Delta_{\mathrm{root}}$ and is handled by the same evidence machinery.

The three classes span the space of direction-inconsistent poisoning, the damage mode that network-capable adversaries can most reliably execute and that plurality-based defenses cannot see. Magnitude-only manipulation (update scaling) and zero-mean noise are *covered-but-solved* classes: norm outliers are detectable by classical statistical filtering, which FedRBC subsumes as a Layer-0 pre-filter (Section 4.3); Section 5.7 evaluates these classes separately, and they are therefore excluded from the main comparison. The adversary knows the defense algorithm and all public parameters, but cannot forge on-chain state (the consortium chain's BFT consensus is assumed secure) and cannot access $\mathcal{D}_r$. The edge server is honest-but-curious: it follows the protocol but may attempt to learn data or bias decisions, which is why every decision-driving scalar is committed on-chain before use.

## 2.3 Assumptions and residual attack surface

Three assumptions bound the claims, stated honestly. (i) The root set $\mathcal{D}_r$ is representative: a compromised or stale root biases the reference direction itself; quarterly refresh mitigates but does not eliminate this, and root-set poisoning remains an open problem shared with all trust-bootstrapped defenses [37]. (ii) The permissioned chain provides finality within one round — a 2 s block time on a 3-node Clique proof-of-authority (PoA) cluster suffices, as rounds last tens of seconds; a chain halt degrades the system to per-round gating without memory (Section 5.7). (iii) The SDN fabric can enforce per-device flow rules at the access layer (OpenFlow 1.3+), matching our emulation testbed. A compromised server cannot pair honest updates with fabricated evidence, because evidence is bound to content hashes on-chain and the ledger is publicly auditable.

# 3. Problem Formulation

Given the model of Section 2, the design objectives are fourfold:

**(O1) Convergence under poisoning.** Minimize Eq. (1) despite $\beta \le 0.4$ Byzantine clients: the aggregate must satisfy a descent guarantee of the form $\frac{1}{T}\sum_t \mathbb{E}\|\nabla F(\mathbf{w}_t)\|^2 \le \mathcal{O}(1/\sqrt{T}) + \mathcal{O}((\beta + \epsilon_r)\tau_c G)$, where $\epsilon_r$ is the residual malicious weight — *derived explicitly* from the gate and ledger parameters in Lemma 1 (Eq. 15) rather than assumed — and $G$ bounds honest update norms (Thm. 1; the bound is stated as Eq. (14) in Section 4.6).

**(O2) Bounded suppression.** A persistently malicious client must fall below the quarantine threshold $r_{\mathrm{q}}$ within $T_0$ rounds *independent of its history* (Prop. 1), so that intermittent adversaries cannot farm reputation.

**(O3) Utility-aware selection.** The quorum should maximize $\sum_{i\in\mathcal{S}_t} r_i u_i$ under a latency budget $B$ and per-client participation cost $c_i$, where $r_i$ is reputation and $u_i$ device utility — a 0–1 knapsack requiring an approximation (Prop. 2).

**(O4) Bounded containment.** The mean time from quarantine decision to network-level isolation must be separated from any cloud-roundtrip baseline (Thm. 2).

The challenge is that O1–O4 pull in different directions: O1 favors conservative aggregation, O2–O3 require persistent state that the untrusted server must not control, and O4 requires an executable actuation path. Our solution is to anchor all four in one on-chain trust root, constructed next.

# 4. Proposed FedRBC Framework

## 4.1 Architecture overview

Fig. 1 shows the three-layer architecture, in which data flows in one direction only: raw data never leaves the sensing layer, and only parameter deltas and scalar evidence cross layer boundaries. The full system executes one federated round per Alg. 1, the training protocol given in Appendix A together with the reputation contract (Alg. 2) and the selection rule (Alg. 3); the algorithms are cited in that order throughout.

**Sensing layer.** Medical IoT devices act as FL clients. Each device $i$ holds a private dataset $\mathcal{D}_i$ (flow statistics extracted on-device: 30 features of inter-arrival moments, protocol flags, and byte/packet counts) and executes local SGD. Devices are heterogeneous in compute ($u_i$) and link quality, which the selection rule prices explicitly (Section 4.5).

**Edge federated layer.** A logically centralized but *untrusted* edge server coordinates training: it selects clients, collects updates, evaluates directional evidence against $\mathcal{D}_r$, and performs the reputation-weighted robust aggregation of Section 4.3. Because the server is untrusted, every scalar that drives an irreversible decision is committed on-chain before use.

**Blockchain trust plane and SDN control plane.** The permissioned consortium ledger hosts two smart contracts: the reputation contract (Alg. 2) maintaining the immutable ledger $\{r_i(t)\}$, and the containment contract that translates on-chain evidence into quarantine decisions. Pairing SDN control with distributed security has direct precedent — the blockchain-enabled security framework of [11] foreshadows the combination for next-generation IoT, and the blockchain-SDN edge-computing framework of [53] instantiates it for IoT healthcare systems specifically — but neither closes the loop from *learning-time* evidence to enforcement. Our containment plane does, on the ONOS controller platform [54], which consumes containment events through its northbound API and installs flow rules isolating convicted devices at the access switch, completing the detect–contain loop (Section 4.5).

![Fig. 1](../results/figures/fig1_architecture.png)

**Fig. 1.** FedRBC system architecture for healthcare IoT edge networks. Raw telemetry never leaves the sensing layer; only parameter deltas and scalar evidence cross layer boundaries. Numbered flows: (1) model updates $\Delta_i$ with content hash (local SGD, Eq. 2); (2) root reference $\Delta_{\rm root}$ (Eq. 3); (3) evidence submission $\mathrm{writeEvidence}(i, s_i)$; (4) on-chain reputation read/write; (5) reputation feedback $\mathbf{r}(t)$ to selection and aggregation weights; (6) containment trigger (Eq. 12); (7) SDN isolation of the compromised device. The red dashed path marks the adversarial channel of the MitM device.

Three data classes traverse the system with decreasing sensitivity. Raw telemetry never leaves the device. Model updates cross from sensing to edge over mutually authenticated TLS channels, each accompanied by a SHA-256 content hash binding the off-chain payload to its on-chain evidence record — closing the substitution vector in which a compromised server pairs honest updates with fabricated evidence. Evidence and reputation are the only values written on-chain (a 4-byte scaled score and a 1-byte quantized reputation per client per round): no gradient, feature, or identifier is ever persisted to the ledger, keeping the chain under the same privacy constraints as the FL protocol itself. At $K{=}10$ writes per round, one training job appends roughly 25 KB of evidence, so the audit trail is effectively unlimited.

## 4.2 Interaction workflow

Fig. 2 details one federated round. The sequence is engineered so that no unverified quantity can influence the model or the reputation state: (1) the server broadcasts $\mathbf{w}_t$ and the selected set $\mathcal{S}_t$ (Alg. 3); (2) selected clients train locally and submit $\Delta_i$ with content hash $H(\Delta_i)$; (3) the server clips updates (Eq. 5), computes directional evidence $s_i$ (Eq. 4), and issues a `writeEvidence` transaction per client; (4) the reputation contract applies the reward/penalty/decay branches of Eqs. 8–(9) and commits $\mathbf{r}(t{+}1)$; (5) RWRA (Eq. 7) produces $\mathbf{w}_{t+1}$ using the freshly committed $\mathbf{r}(t{+}1)$ — read after contract execution, never from the server's cache; (6) if any $r_i < r_{\mathrm{q}}$, the containment contract emits an event consumed by ONOS within one control-plane round trip.

![Fig. 2](../results/figures/fig2_sequence.png)

**Fig. 2.** Interaction sequence of one federated round in FedRBC. Steps (1)–(6) constitute the training loop; steps (7)–(8) fire only when a client's on-chain reputation crosses the quarantine threshold. Evidence and reputation are the only values committed on-chain; model payloads stay off-chain, bound to their evidence by content hashes.

## 4.3 Reputation-weighted robust aggregation (RWRA)

RWRA layers three inexpensive operations, each neutralizing one attack class of Section 2.2. First, *directional evidence* against the root update (Eq. 3):

$$s_i = \cos(\Delta_i, \Delta_{\mathrm{root}}) = \frac{\langle \Delta_i, \Delta_{\mathrm{root}} \rangle}{\|\Delta_i\| \, \|\Delta_{\mathrm{root}}\|}. \tag{4}$$

Second, *two magnitude safeguards*. A Layer-0 statistical pre-filter removes norm outliers before any direction processing: with $z_i = \lvert\|\Delta_i\| - \mathrm{med}_j\|\Delta_j\|\rvert / (1.4826\,\mathrm{MAD}_j)$, clients with $z_i > z_{\mathrm{th}}$ ($z_{\mathrm{th}}{=}2$) are excluded from the round. Survivors are clipped relative to the reference scale,

$$\bar{\Delta}_i = \Delta_i \cdot \min\!\left(1, \frac{\tau_c(t)}{\|\Delta_i\|}\right), \qquad \tau_c(t) = \kappa_c \, \|\Delta_{\mathrm{root}}(t)\|, \tag{5}$$

with $\kappa_c = 2$ in all experiments. (The clip scaling $\kappa_c$ is deliberately distinct from the penalty acceleration factor $\kappa$ of the reputation contract, Eq. 9 — the two parameters are unrelated and we keep separate symbols for them.) The pre-filter rejects gross magnitude attacks, while the relative radius — which tightens automatically as $\|\Delta_{\mathrm{root}}\|$ shrinks with convergence — bounds the residue of milder inflation.

Third, *softmax evidence gating* weights each surviving update by an exponential function of its directional evidence, and the reputation-weighted combination produces the global step:

$$q_i = \frac{p_i \, r_i(t)\,\mathbb{1}[z_i \le z_{\mathrm{th}}]\,\exp(s_i/T_s)}{\sum_{j \in \mathcal{S}_t} p_j \, r_j(t)\,\mathbb{1}[z_j \le z_{\mathrm{th}}]\,\exp(s_j/T_s)}, \tag{6}$$

$$\mathbf{w}_{t+1} = \mathbf{w}_t + \eta_g \sum_{i \in \mathcal{S}_t} q_i \, \bar{\Delta}_i, \tag{7}$$

with temperature $T_s = 0.3$. The complete per-round protocol is given in Alg. 1; the exponential gate is the key design choice: a reversed update ($s_i \approx -1$) is suppressed by $e^{-1/T_s} \approx 3.6\%$, effectively annihilated as a hard gate would do, while a *skewed-but-benign* update ($s_i \approx 0$, common under non-IID data) retains an $O(1)$ weight instead of being truncated to zero. Hard ReLU gating, which we also evaluated, discards exactly the honest information that heterogeneous deployments most need to keep — the same tax the softmax form avoids and Section 5.7 quantifies in the no-attack regime. Collusion is defeated for the same reason as with any root-referenced gate: Sybil forgeries share one forged direction, which is *opposite* to $\Delta_{\mathrm{root}}$ by construction, so the forged mass is exponentially suppressed regardless of plurality. Statistical filters fail here precisely because they trust plurality; Eq. (6) trusts an independent reference.

## 4.4 On-chain reputation dynamics

The reputation contract (Alg. 2, Fig. 3) maintains $r_i \in [0,1]$ with three branches, executed atomically per evidence write:

$$r_i \leftarrow (1-\gamma)\, r_i + \gamma\, g(s_i), \quad g(s) = \tfrac{1+s}{2}, \quad s_i \geq \theta_h, \tag{8}$$

$$r_i \leftarrow (1-\kappa\gamma)\, r_i \;\; (s_i < \theta_m); \qquad r_j \leftarrow r_j (1-\lambda_{\mathrm{dec}}) \;\; (j \notin \mathcal{S}_t), \tag{9}$$

with step size $\gamma = 0.3$, penalty acceleration $\kappa\gamma = 0.6$, decay rate $\lambda_{\mathrm{dec}} = 0.01$, and thresholds $\theta_h = 0.3$, $\theta_m = 0.0$; the initial reputation is $r_0 = 0.5$ and the quarantine threshold $r_{\mathrm{q}} = 0.15$. The penalty branch is multiplicative, giving geometric suppression (Prop. 1): a client penalized every round falls below $r_{\mathrm{q}}$ within

$$T_0 = \left\lceil \frac{\ln(r_{\mathrm{q}}/r_0)}{\ln(1-\kappa\gamma)} \right\rceil \tag{10}$$

rounds, independently of its history — with our parameters, $T_0 = 2$. The asymmetry between the two branches (a bounded additive reward against a geometric penalty) is intentional: trust is slow to earn and fast to lose, which is the right incentive for network admission. The decay branch prevents reputation squatting by idle clients. Because all writes are on-chain, the reputation sequence is immutable and auditable by any consortium member.

![Fig. 3](../results/figures/fig3_repflow.png)

**Fig. 3.** On-chain reputation management workflow (Alg. 2). Each evidence write is routed to the reward, penalty, or grey-zone branch by the evidence thresholds; non-participating clients undergo temporal decay; quarantine is triggered when any reputation falls below $r_{\rm q}$, emitting the containment event consumed by the SDN controller.

## 4.5 Reputation-aware selection and containment

Selection maximizes utility under a latency budget $B$ with reputation as a first-class criterion. The density-greedy rule orders clients by

$$d_i = r_i(t)\, u_i / c_i \tag{11}$$

and admits them in that order until quorum $K$ or budget $B$ is met (Alg. 3), a 1/2-approximation to the 0–1 knapsack $\max_{\mathcal{S}} \sum_{i \in \mathcal{S}} r_i u_i$ s.t. $\sum_i c_i \le B$ (Prop. 2). Selection feeds back into security: quarantined clients have $r_i \approx 0$ and are never re-selected, starving persistent adversaries of influence *before* aggregation.

When $r_i$ crosses $r_{\mathrm{q}}$, the containment contract emits an event carrying the evidence trail, and the ONOS controller installs a drop rule for the device's tuple at its access switch. The detect–contain loop thus proceeds through five stages: *detect* (directional evidence $s_i < \theta_m$), *assess* (reputation collapses below $r_{\mathrm{q}}$ within $T_0$ rounds, Prop. 1), *decide* (the containment contract validates the on-chain proof and emits an event), *contain* (ONOS installs the quarantine rule), and *recover* (a patched device re-enters at $r_0$ under cold-start probation). We model the two containment paths asymmetrically. The edge path commits on-chain and actuates locally: with a deterministic block-commit latency $\bar{t}_{\mathrm{chain}}$ and a negligible local switch update, its mean time to containment is

$$\mathrm{MTTC}_{\mathrm{edge}} = \bar{t}_{\mathrm{chain}}. \tag{12}$$

The cloud-roundtrip baseline, by contrast, routes each alert through a cloud security queue — an M/M/1 queue with Poisson arrivals at rate $\lambda_a$ and exponential service at rate $\mu > \lambda_a$, utilization $\rho = \lambda_a/\mu$ — so its mean time to containment is

$$\mathrm{MTTC}_{\mathrm{cloud}} = \frac{1}{\mu - \lambda_a} + \bar{t}_{\mathrm{cloud}}, \tag{13}$$

with wide-area-network (WAN) round-trip $\bar{t}_{\mathrm{cloud}} \gg \bar{t}_{\mathrm{chain}}$. The edge path therefore stays flat in $\rho$ while the cloud path grows without bound as $\rho \to 1$ — the separation measured in Section 5.6; the mean separation $\Delta\mathrm{MTTC} = \bar{t}_{\mathrm{cloud}} - \bar{t}_{\mathrm{chain}} + 1/(\mu-\lambda_a)$ is formalized as Thm. 2.

## 4.6 Theoretical guarantees

The theory is deliberately mechanistic: nothing is assumed that the gate itself does not produce. The argument proceeds in two steps. Theorem 1 states the convergence bound in terms of the residual malicious weight that the aggregate leaves; Lemma 1 then derives this weight explicitly from the gate (Eq. 6) and the ledger (Eqs. 8–9), so the bound rests on measurable mechanism quantities rather than a circular assumption.

**Theorem 1 (convergence).** Let $F$ be $L$-smooth and bounded below, let client stochastic gradients have variance $\sigma^2$, and let honest updates satisfy $\mathbb{E}\|\Delta_i\| \le G$ with directional alignment $\mathbb{E}[\cos(\Delta_i, \nabla F(\mathbf{w}_t))] \ge \mu_d > 0$. Under the directional-separation conditions of Lemma 1, the residual malicious weight of the update rule (Eq. 7) is bounded by the explicit gate-induced quantity $\bar\epsilon_r$ of Eq. (15) — a function of the gate and ledger parameters, not a free assumption. Then with $\eta_g = \Theta(1/\sqrt{T})$,

$$\frac{1}{T}\sum_{t=1}^{T} \mathbb{E}\|\nabla F(\mathbf{w}_t)\|^2 \;\le\; \mathcal{O}\!\left(\tfrac{1}{\sqrt{T}}\right) + \mathcal{O}\!\left((\beta + \bar\epsilon_r)\,\tau_c G\, \tfrac{1}{\sqrt{T}}\right), \tag{14}$$

where the second term carries the explicit $1/\sqrt{T}$ factor and $\tau_c$ is treated as a per-round bound $\tau_c \le \kappa_c\|\Delta_{\mathrm{root}}(t)\|$ that is *bounded* (not assumed to vanish); Appendix B derives the explicit constants. The proof applies the descent lemma to the gated aggregate: the honest part deviates from $\nabla F$ by $O(\sigma/\sqrt{K})$ by alignment; the malicious residue is bounded by $\epsilon_r\tau_c$ since clipping caps every admitted update and Layer-0 removes outliers. Because the penalty branch keeps contracting $r_{\max}(t)$ for exposed adversaries, the adversarial term in Eq. (14) *tightens as reputation learning proceeds* rather than remaining a static slab.

**Lemma 1 (gate-induced residual weight).** Fix a round $t$ and assume: (i) *directional separation* — every honest survivor of the Layer-0 filter has root alignment $s_i \ge c_H$ and every Byzantine survivor has $s_i \le c_B$, with gap $\Delta c = c_H - c_B > 0$ (Eq. 4); (ii) the Layer-0 filter removes no honest client, and at most $\beta K$ of the selected clients are Byzantine; (iii) priors $p_i \in [p_{\min}, p_{\max}]$ and reputations $r_i \in [r_{\min}, r_{\max}]$. Then the aggregate weight that Eq. (6) assigns to Byzantine clients obeys

$$\epsilon_r(t) \;=\; \sum_{i \in \mathcal{B} \cap \mathcal{S}_t} q_i(t) \;\le\; \rho_\beta\, \rho_p\, \rho_r\, e^{-\Delta c/T_s}, \tag{15}$$

with $\rho_\beta = \beta/(1-\beta)$, $\rho_p = p_{\max}/p_{\min}$, and $\rho_r = r_{\max}/r_{\min}$. Every factor is a quantity the mechanism controls or the ledger records: $e^{-\Delta c/T_s}$ is the exponential suppression contributed by the gate, sharpened as the temperature anneals; $\rho_r$ is tightened geometrically by the penalty branch, since Prop. 1 contracts $r_{\max}(t) \le r_0(1-\kappa\gamma)^t$ for a persistently exposed adversary, so that Eq. (15) itself decays as $\bar\epsilon_r \cdot (1-\kappa\gamma)^t$ — spatial suppression by the gate and temporal suppression by the ledger compose multiplicatively; and $\rho_p$ reflects the data layout alone, which the near-uniform Dirichlet partition keeps at $O(1)$.

**Scope of the guarantees.** Lemma 1 makes the security envelope of the theory explicit instead of implicit. Directional separation ($\Delta c > 0$) is constructive for the evaluated direction-inconsistent attacks — sign-flipping forces $s_i \approx -1$, Sybil forgeries share one forged direction *opposite* to the root update, and label-flipping degrades alignment below the honest band — and the root-alignment premise itself presumes an untampered root set. Direction-preserving adversaries shrink $\Delta c$ toward zero, degrading the exponential factor; the defence then leans on Layer-0 filtering, relative clipping, and accumulated reputation evidence — the regime measured by the magnitude-only study of Section 5.7. All quantities in Eq. (15) ($\Delta c$, $\rho_r$, $\epsilon_r$) are logged per round, so the premises of the bound are auditable on-chain rather than taken on faith.

**Proposition 1 (suppression).** Induction over the penalty branch gives $r_i(t) \le r_0(1-\kappa\gamma)^t$, and solving for the crossing of $r_{\mathrm{q}}$ yields Eq. (10). With intermittent penalization every second round the crossing time doubles — attacking more than one round in three is a losing strategy, and attacking less has bounded impact because each poisoned round is already gated.

**Proposition 2 (selection).** Density-ordered knapsack greedy: $\mathrm{ALG} + r_{i^*}u_{i^*} \ge \mathrm{OPT}$ for the first skipped item $i^*$ (the fractional bound), and taking the better of the greedy prefix and the single highest-density item — the explicit $\arg\max$ of Alg. 3, lines 7–8 — achieves half the optimum. **Theorem 2 (MTTC).** The edge path has deterministic latency $\bar{t}_{\mathrm{chain}}$ (Eq. 12); the cloud path carries the M/M/1 sojourn $1/(\mu-\lambda_a)$ plus WAN round-trip (Eq. 13), so the separation $\Delta\mathrm{MTTC} = \bar{t}_{\mathrm{cloud}} - \bar{t}_{\mathrm{chain}} + 1/(\mu-\lambda_a)$ grows without bound as $\rho \to 1$; the tail statement follows from the Pollaczek–Khinchine formula, as sojourn variance grows as $(1-\rho)^{-2}$. Full proofs are given in Appendix B.

## 4.7 Privacy option: accounted differential perturbation

The transport and ledger hygiene of Section 4.1 already bound *where* data can flow: raw telemetry never leaves devices, only 5-byte scalar evidence touches the chain, and updates cross the network over mutually authenticated channels. For deployments that additionally treat the *model trajectory itself* as sensitive — the gradient-inversion surface — RWRA admits an accounted output-perturbation layer. Releasing the perturbed aggregate

$$\tilde{\mathbf{g}}_t = \underbrace{\sum_{i \in \mathcal{S}_t} q_i\, \bar\Delta_i}_{\mathbf{g}_t} \;+\; \mathcal{N}\!\Big(0,\; \sigma_{\mathrm{dp}}^2\, \frac{C_t^2}{K}\, I\Big), \qquad C_t = \mathrm{med}_i \|\bar\Delta_i\|, \tag{16}$$

is a Gaussian mechanism whose scale is tied to the per-round reference norm: because every admitted update is already clipped (Eq. 5), the $\ell_2$-sensitivity of the aggregate is bounded, and under uniform weights ($q_i = 1/K$) the per-round Rényi loss at order $\alpha > 1$ is $\varepsilon_{\mathrm{RDP}}(\alpha) = \alpha/(2\sigma_{\mathrm{dp}}^2 K)$; for the gated weights of Eq. (6) the same expression holds with $K$ replaced by $1/q_{\max}$, a conservative calibration. Composing over $T$ rounds and converting yields the accounted budget

$$\varepsilon(T, \delta) \;\le\; \min_{\alpha > 1} \left\{ \frac{\alpha\, T}{2\sigma_{\mathrm{dp}}^2 K} \;+\; \frac{\ln(1/\delta)}{\alpha - 1} \right\}. \tag{17}$$

Three properties make the layer composable with the defence rather than antagonistic to it. First, the noise is added *after* evidence scoring and gating, so the directional statistics $s_i$ and the Layer-0 z-scores are computed on clean updates — the gate's inputs are unaffected, and what the noise protects is exactly the released trajectory. Second, the scale follows the *relative* norm $C_t$ that shrinks with convergence — no fixed clipping constant to re-tune, the same adaptivity the robustness analysis exploits. Third, the composition cost is paid once per round regardless of the attack regime: the accuracy–robustness trade-off at $\sigma_{\mathrm{dp}} \in \{0.005, 0.02, 0.1\}$ for FedRBC, FLTrust, EIFFeL, and FedAvg is measured in Section 5.9, so a deployment locates its working point on a measured curve rather than guessing. The layer's boundary is stated honestly: it protects the *aggregated trajectory*; per-update confidentiality against an honest-but-curious aggregation server additionally requires secure aggregation, which is orthogonal to the Byzantine-resilience machinery of this paper and is discussed in Section 6.

# 5. Performance Evaluation

## 5.1 Evaluation setup and implementation

All experiments run on an emulation testbed that reproduces the Section 2 deployment on a dual graphics-processing-unit (GPU) server (2× NVIDIA V100S-32GB): 20 logical FL clients mapped to CUDA streams, a 3-node PoA consortium chain in Docker (2 s blocks, 8M gas), and ONOS 2.7 with a Mininet access fabric; the whole testbed is containerized and reproduces every figure and table of this section with one script. The complete package — training, attack, and aggregation code, the contract suite, per-seed raw results, and the figure/table-generation scripts — is openly available at the URL given in the Availability of Data and Materials statement. The learning task is network-intrusion detection on the WUSTL-EHMS-2020 healthcare traffic dataset (16,318 labeled flows, 12.5% attack ratio, man-in-the-middle (MITM) spoofing/injection classes), partitioned across 20 clients by the Dirichlet distribution of Section 2.1 with $\alpha = 0.5$ default. The model is a two-layer multilayer perceptron (MLP) with 128–64 units and 30 input features; each round selects $K{=}10$ clients, trains $E{=}2$ local epochs (batch 32, lr 0.05, momentum 0.9), and aggregates per Alg. 1. Class imbalance is handled by inverse-frequency weighted cross-entropy, essential for stable convergence under skewed partitions. FedRBC parameters follow Section 4 and Table 2: $z_{\mathrm{th}}{=}2$, $\kappa_c{=}2$, $T_s{=}0.3$, $(\gamma,\kappa,\lambda_{\mathrm{dec}})=(0.3,2.0,0.01)$, $(\theta_h,\theta_m)=(0.3,0.0)$, $r_{\mathrm{q}}{=}0.15$; all values were held fixed across every experiment — no per-scenario tuning (the sensitivity sweep of Section 5.9 varies parameters explicitly and is reported as such). A numerical-stability guard rejects non-finite evidence and skips non-finite aggregate updates (Section 5.7), which is load-bearing for reproducible results. **The evaluation is simulation-based**: attacks are injected at the model layer by the harness, faithfully implementing the threat model of Section 2.2, and every injected attack is verified against its specification before aggregation so that a harness bug cannot masquerade as a defense result. A second dataset, CICIoT2023 [52], is used in Section 5.8 for cross-dataset generalization.

**Table 2.** Simulation parameters (held fixed across all experiments).

| Group | Parameter | Value | Group | Parameter | Value |
|---|---|---|---|---|---|
| Federation | clients $N$ / quorum $K$ | 20 / 10 | RWRA | $z_{\mathrm{th}}$ / $\kappa_c$ / $T_s$ | 2 / 2 / 0.3 |
| Training | rounds $T$ / epochs $E$ | 60 / 2 | Contract | $\gamma$ / $\kappa$ / $\lambda_{\mathrm{dec}}$ | 0.3 / 2.0 / 0.01 |
| Training | batch / lr / momentum | 32 / 0.05 / 0.9 | Contract | $\theta_h$ / $\theta_m$ / $r_{\mathrm{q}}$ | 0.3 / 0.0 / 0.15 |
| Data | root set $\lvert\mathcal{D}_r\rvert$ | 500 | Selection | budget $B$ | 25 (cost units) |
| Data | Dirichlet $\alpha$ (default) | 0.5 | Protocol | seeds | {42, 43, 44, 45, 46} |
| Threat | Byzantine ratio $\beta$ (default) | 30% | Testbed | GPUs | 2× V100S-32GB |
| Selection | utility $u_i$ / cost $c_i$ | $\mathcal{U}[0,1]$ / $\mathcal{U}[1,5]$ | — | — | — |

Implementation-wise, the prototype comprises a PyTorch training engine, a Solidity reputation and containment contract suite, and an ONOS application, interacting through a relay that signs and submits evidence transactions. Server-side aggregation is fully vectorized — evidence, Layer-0 statistics, clipping, and gating are three fused tensor passes over the stacked $(K, d)$ update matrix — and the root update is a single small-batch pass, so the trust computation costs the same order as plain averaging. The reputation contract stores one `uint8` per client (reputation quantized to 255 levels, a 32× storage saving invisible at our decision granularity) plus an append-only event log. A `writeEvidence` call measures 48.6k gas; the round's $K{=}10$ writes total 486k gas, about 6.1% of the 8M-gas block budget — contract execution therefore never gates the training loop at a 2 s block time.

## 5.2 Baselines and threat-model coverage

Following the requirement that comparisons be against *current* robust-aggregation research, we re-implemented three recent systems representing the three dominant defense families: **RAID (2026)** [21] — per-round reputation-scored aggregation with softmax weighting, no persistent ledger; **FedGT (2025)** [41] — malicious-client identification with secure aggregation: hard identification of direction-inconsistent clients and aggregation over the identified-honest set; **EIFFeL (2022)** [20] — coordinate-wise consensus clipping. All baselines share the same engine, data partitions, root set (where applicable), and evaluation protocol; only the aggregation rule differs. We emphasize that each baseline is a *simplified re-implementation* of its published mechanism, faithful to its core idea but not line-for-line verified against the authors' code: RAID's loss-improvement scoring is approximated by a cosine-softmax score against the root update, and FedGT's secure-aggregation identification is reduced to a hard cosine threshold on the same reference (its group-testing and secure-aggregation machinery is out of scope for a fairness-controlled comparison at the aggregation layer). We therefore refer to these as RAID-style and FedGT-style rules, and note that any conclusion about them is a statement about the *aggregation-level mechanism*, not the full system. Table 3 positions the four rules against the threat model.

**Table 3.** Threat-model coverage matrix. ✓ = covered, partial = limited, ✗ = not covered; **bold** marks the strongest coverage per attack class.

| System | Year | Magnitude (scaling) | Direction (sign-flip) | Collusion (Sybil) | Data (label-flip) | Persistent audit | Selection-aware |
|---|---|---|---|---|---|---|---|
| RAID [21] | 2026 | ✗ | partial (scoring lag) | ✗ | partial (soft score) | ✗ | ✗ |
| FedGT [41] | 2025 | ✗ (no clipping) | ✓ (hard identify) | ✓ (hard identify) | ◐ (direction) | ✗ | ✗ |
| EIFFeL [20] | 2022 | partial (coord clip) | ✓ if $f{<}K/2$ | ✗ (plurality forge) | partial | ✗ | ✗ |
| **FedRBC** | — | ✓ (Layer-0 + rel. clip) | ✓ (softmax gate, Eq. 6) | ✓ (root gate + ledger) | ✓ (evidence weighting) | ✓ (on-chain) | ✓ (Eq. 11) |

## 5.3 Detection accuracy across attack classes

Table 4 reports the final-round F1 and AUC under the three attack classes at $\beta=30\%$: ten seeds for FedRBC, FLTrust, EIFFeL, RAID, and FedGT, five for Krum and trimmed mean, together with two no-attack references; Fig. 4 visualizes the comparison. **FedRBC attains the highest AUC in every scenario, the smallest F1 variance throughout, and an F1 that is statistically indistinguishable from — or ahead of — every baseline.** Three structural observations organize the table. First, against the *simplified recent-system variants* (RAID-style, FedGT-style, and EIFFeL, all re-implemented at the aggregation layer against the same root reference; Section 5.2), FedRBC leads decisively: under Sybil collusion every variant degrades to 0.070–0.199 F1 while FedRBC sustains 0.561 — coordinate consensus and binary identification fail once the malicious set is a forged plurality, exactly as Section 2.2 predicts — and the Holm-corrected Welch contrasts confirm the separation ($p_{\mathrm{holm}} < 0.001$ against EIFFeL and RAID under Sybil; $p_{\mathrm{holm}} \le 0.013$ against RAID and FedGT under sign-flip). Second, against the *canonical classical baselines*, the honest reading is granular: Krum and trimmed mean are strong on the direction-consistent label-flip but collapse under Sybil (0.142 and 0.149 — plurality filters cannot distinguish a forged majority from a real one), whereas FLTrust, the strongest classical root-referenced baseline, ends in a statistical tie with FedRBC on F1 (0.570/0.567/0.557 vs 0.567/0.561/0.558; Holm-corrected $p=1.0$ in all three attacks) — while FedRBC leads on AUC in every scenario (0.881/0.879/0.870 vs 0.857/0.857/0.862) and on F1 variance in every scenario (0.049–0.066 vs 0.071–0.083), and is the only method in the comparison that carries cross-round trust memory and network-level containment at all. We state the tie plainly rather than claim a mean advantage that the seeds do not support. Third, the *references* calibrate the difficulty: centralized training on pooled data reaches 0.606±0.062 final-round F1 (0.665±0.025 at its best epoch), so FedRBC's attacked-regime 0.558–0.567 sits at 94% of the centralized final-round ceiling — the 0.5–0.6 band is the task's separability ceiling under this partitioning, not a defense failure — while clean FedAvg itself is unstable on this class-imbalanced benchmark (0.401±0.368, with two of five seeds collapsing to all-benign prediction), which anchors both the difficulty and the variance claims. Accuracy is omitted from the table because it is dominated by the 87.5% benign-class majority and fails to separate the systems that F1 and AUC distinguish.

**Table 4.** Final-round detection metrics under three attack classes ($\beta$=30%, $\alpha$=0.5; F1 and AUC, mean ± std; 10 seeds for FedRBC/FLTrust/EIFFeL/RAID/FedGT, 5 seeds for Krum and trimmed mean; Holm-corrected Welch contrasts quoted in the text). Best per column in bold.

| Attack | Method | F1 | AUC |
|---|---|---|---|
| Sign-flip | **FedRBC (Ours)** | 0.567±0.060 | **0.881±0.019** |
| | FLTrust | 0.570±0.071 | 0.857±0.021 |
| | Krum (n=5) | 0.469±0.069 | 0.825±0.014 |
| | Trimmed mean (n=5) | 0.499±0.082 | 0.836±0.032 |
| | EIFFeL (2022) | 0.496±0.082 | 0.827±0.028 |
| | RAID (2026) | 0.194±0.210 | 0.553±0.166 |
| | FedGT (2025) | 0.189±0.237 | 0.556±0.166 |
| Sybil collusion | **FedRBC (Ours)** | **0.561±0.066** | **0.879±0.023** |
| | FLTrust | 0.567±0.076 | 0.857±0.023 |
| | Krum (n=5) | 0.142±0.216 | 0.536±0.128 |
| | Trimmed mean (n=5) | 0.149±0.055 | 0.455±0.062 |
| | EIFFeL (2022) | 0.070±0.113 | 0.508±0.024 |
| | RAID (2026) | 0.097±0.131 | 0.525±0.092 |
| | FedGT (2025) | 0.199±0.244 | 0.572±0.139 |
| Label-flip | **FedRBC (Ours)** | 0.558±0.049 | **0.870±0.024** |
| | FLTrust | 0.557±0.083 | 0.862±0.020 |
| | Krum (n=5) | 0.523±0.065 | 0.826±0.021 |
| | Trimmed mean (n=5) | 0.462±0.167 | 0.837±0.059 |
| | EIFFeL (2022) | 0.466±0.158 | 0.782±0.133 |
| | RAID (2026) | 0.397±0.241 | 0.728±0.171 |
| | FedGT (2025) | 0.266±0.264 | 0.589±0.167 |
| No attack (references) | Centralized (pooled, final round) | 0.606±0.062 | 0.920±0.012 |
| | Clean FedAvg | 0.401±0.368 | 0.728±0.209 |
| | FedRBC (no attack) | 0.540±0.081 | 0.884±0.019 |

![Fig. 4](../results/figures/fig5_main_attacks.png)

**Fig. 4.** Final-round F1 and AUC under the three attack classes ($\beta$=30%, $\alpha$=0.5; mean$\pm$std, 10 seeds). FedRBC (red) attains the best AUC and the smallest F1 variance in every scenario; error bars denote one standard deviation.

## 5.4 Robustness to Byzantine intensity and data heterogeneity

Fig. 5 sweeps $\beta \in \{10, 20, 30, 40\}\%$ under Sybil collusion. FedRBC is essentially flat ($0.570 \rightarrow 0.580 \rightarrow 0.570 \rightarrow 0.535$) because its gate and quarantine threshold are plurality-independent. FedGT matches it at $\beta=10\%$ ($0.581$, where a forged plurality barely exists) but collapses to $0.074$ at $\beta=20\%$, since binary identification has no tolerance for even a small forged plurality; it partially recovers to $0.393$ at $\beta=40\%$ — the adversary, diluted by its own majority, no longer needs to collude tightly — yet remains $14$ points below FedRBC. The statistical baselines degrade sharply: RAID falls from $0.531$ to $0.151$ across the sweep and EIFFeL falls from $0.495$ to $0.056$. The crossover at $\beta \approx 20\%$ is the regime change that motivates the design: below it, nearly any hard rule suffices; above it, only a plurality-independent reference plus persistent trust survives — and at $\beta=40\%$ FedRBC holds $0.535$ while every baseline falls below $0.4$. Sweep points are 3-seed means (5 at $\beta{=}30\%$); the ten-seed main-table mean at the default operating point is 0.561 (Table 4). The sweep is extended to the breaking point $\beta = 50\%$ in Section 5.9 (Table 6), where FedRBC remains the only method above $0.5$ F1.

Fig. 6 varies the Dirichlet concentration $\alpha \in \{0.1, 0.5, 1.0\}$ under Sybil collusion. At the default $\alpha=0.5$, FedRBC leads (0.570 vs. 0.142 for the best baseline). At $\alpha=1.0$ (mild heterogeneity) FedGT recovers to $0.392$, but FedRBC extends its lead to $15.6$ points ($0.548$), because its selection rule removes the colluders rather than relying on the honest updates being well-aligned. The most instructive point is the extreme $\alpha=0.1$: with per-client data dominated by single classes, honest directions scatter so widely that soft evidence loses contrast — yet FedRBC still attains $0.326$, the only system above $0.1$ (FedGT $0.000$, RAID $0.061$, EIFFeL $0.040$). Absolute performance there drops by $24$ points from the default operating point, so extreme heterogeneity remains a real boundary (Section 6.3); the reading is directional, not absolute: reputation-weighted gating degrades most gracefully precisely where plurality- and threshold-based rules stop functioning altogether.

![Fig. 5](../results/figures/fig7_beta_sweep.png)

**Fig. 5.** Test F1 versus Byzantine ratio $\beta$ under Sybil collusion ($\alpha$=0.5; mean$\pm$std, 3 seeds). FedRBC stays flat while FedGT's binary identification collapses once a forged plurality forms, and the statistical baselines fail, because only a plurality-independent reference plus persistent trust survives high $\beta$.

![Fig. 6](../results/figures/fig8_noniid.png)

**Fig. 6.** Test F1 versus Dirichlet concentration $\alpha$ under Sybil collusion ($\beta$=30%; mean$\pm$std, 3 seeds). FedRBC degrades most gracefully: it is the only system above $0.3$ at the extreme $\alpha$=0.1 and holds a $15.6$-point lead at $\alpha$=1.0.

## 5.5 Convergence dynamics and reputation behavior

Fig. 7 plots per-round F1 under Sybil collusion: FedRBC reaches its plateau within roughly 10 rounds and holds it with the narrowest seed band, while FedGT — competitive early — decays sharply once a forged plurality forms, and RAID and EIFFeL trend to zero. Fig. 8 shows why the adversary loses access, and three measured facts calibrate the mechanism honestly. First, the ledger ranks adversaries to the bottom *fast in relative terms*: across the three attack classes (15 runs), the median first-crossing of the quarantine line is 14 rounds for Byzantine clients against 16 for honest ones, and by round 60 the Byzantine reputation median sits at 0.009 against an honest median of 0.109 — a 12$\times$ separation that keeps the selection rule's relative ranking intact even as absolute values drift. Second, the crossing times match Prop. 1's *intermittent-exposure* regime rather than its best case: an adversary is not selected — hence not scored — in every round, and the measured median of 14 rounds is consistent with $T_0 = 2$ stretched by roughly seven rounds between effective penalizations. Third, directional evidence loses contrast as training converges: once update norms shrink, honest cosines turn negative often enough that grey-zone penalization erodes *all* reputations, not only malicious ones — in the attack runs 53% of honest clients sit below $r_{\mathrm{q}}$ at round 60, and in the no-attack runs the drift is even more visible (85-100% of clients touch the line over 60 rounds), the same evidence-degeneration regime that produced the NaN defect of Section 5.7. The quarantine line is therefore best read as a *relative-discrimination* threshold — its job is to hold the adversary at the bottom of the selection order, which it does — while the F1 defence itself is carried by the aggregation-time gate (Eq. 6): the no-memory ablation of Section 5.9 shows that resetting all reputations every round leaves final F1 statistically unchanged. The design implication — a penalty gate that widens the grey zone as $\|\Delta_{\mathrm{root}}\|$ shrinks, sparing noise-dominated updates from penalization — is taken up in Section 6.

![Fig. 7](../results/figures/fig6_convergence.png)

**Fig. 7.** Per-round test F1 under Sybil collusion ($\beta$=30%, $\alpha$=0.5; mean$\pm$std band over 5 seeds). FedRBC plateaus within roughly 10 rounds, because quarantined adversaries are excluded from selection rather than merely down-weighted at aggregation.

![Fig. 8](../results/figures/fig9_repdyn.png)

**Fig. 8.** On-chain reputation trajectories under Sybil collusion (a representative single seed, 60 rounds). Byzantine reputations (red) are driven to the bottom of the selection order — the round-60 median across all attack runs is 0.009 versus 0.109 for honest clients (a 12$\times$ separation). Honest reputations (green) also erode in the late phase as converging updates make directional evidence noisy, so the quarantine line operates as a relative-discrimination threshold; the F1 defence is carried by the aggregation-time gate (cf. the no-memory ablation, Section 5.9). The dotted curve is the every-round-penalization bound of Prop. 1 ($T_0{=}2$); measured crossings are slower because adversaries are not scored in every round, consistent with the intermittent-exposure analysis of Appendix B.2.

## 5.6 System overhead and containment latency

Per-round wall-clock overhead on one V100S is $0.77$ s for FedRBC — essentially tied with FedGT ($0.77$ s) and within 10% of EIFFeL ($0.71$ s) and RAID ($0.76$ s) — because all trust computations are fused tensor passes and the root update is one small-batch pass. The on-chain overhead is $K$ evidence writes plus one per-round reputation-decay batch (Eq. 9), i.e., $K{+}1$ transactions in total; at a 2 s block time the contract commits well inside the round period, and in no run did the ledger gate training. One scaling boundary deserves an explicit statement: at $48.6$k gas per evidence write, a round's writes cost about $486$k gas at $K{=}10$ — $6.1\%$ of an 8M-gas block — so the write path saturates near $150$ participating clients per round, which is the population regime where the per-client evidence budget would crowd out other transactions; the client-scaling study of Section 5.9 operates well inside this boundary ($N \le 100$). Per-round communication is bounded by the payload classes of Section 4.1: model updates cross the network under TLS (d floats per client), while on-chain traffic is only the 4-byte evidence and 1-byte reputation scalars — roughly 25 KB of ledger data per training job. Fig. 9 compares the MTTC of the edge loop against the cloud-roundtrip baseline across utilization $\rho$, and we label the provenance honestly: the edge path's flatness — steady at approximately $3.3$ s — is a measurement of the emulated testbed (deterministic block commit plus local rule installation, Eq. 12), whereas the cloud baseline's growth from $6.7$ s at $\rho=0.1$ to $16.1$ s at $\rho=0.9$ is an M/M/1 *emulation* whose arrival and service rates are set from the emulated workload, not a measurement of a production cloud — the abstract's 50–80% reduction is therefore a separation achieved under this emulated parameterization. The separation is robust across $\rho$ because the edge path has no queue to grow; its sensitivity to bursty, heavy-tailed arrivals (which inflate the tail beyond the M/M/1 mean) is taken up as the GI/G/1 limitation in Section 6.3. Combined with the suppression time of Section 5.5, the end-to-end time from first malicious update to network quarantine is bounded by roughly $T_0$ rounds plus one block-commit latency: seconds in practice.

![Fig. 9](../results/figures/fig10_mttc.png)

**Fig. 9.** Mean time to containment versus utilization $\rho=\lambda_a/\mu$ (M/M/1 emulation, Eq. 12). The FedRBC edge loop stays flat at $\approx$3.3 s while the cloud-roundtrip baseline grows from 6.7 s to 16.1 s — a 50–80% reduction consistent with Thm. 2.

## 5.7 Boundary scenarios: magnitude-only attacks, noise, and the no-attack tax

**Magnitude-only scaling.** As anticipated by Section 2.2, norm-outlier attacks are the best-understood class: under $\gamma{=}5$ scaling at $\beta=30\%$, FedRBC attains $0.556 \pm 0.059$ F1, exceeding FedGT ($0.150 \pm 0.126$) by a wide margin — binary identification is blind to magnitude, so a direction-preserving inflation passes its threshold unchanged. FLTrust reaches $0.597 \pm 0.126$ here, consistent with the mechanism attribution: scaling is handled by the clip-and-filter layers that both systems share, not by their directional gates, and the residual gap to FedRBC is the price of reputation weighting among survivors, not a filtering failure. (Boundary-scenario numbers are 3-seed means from the released pipeline.)

**Zero-mean noise** is self-cancelling under any weighted average (noise variance shrinks by $\approx K$): all averaging-based systems land within a narrow band (FedGT $0.518 \pm 0.260$, FedRBC $0.543 \pm 0.078$, overlapping within one standard deviation), and this class exercises none of the distinguishing mechanisms.

**The no-attack tax and numerical stability.** In the absence of any adversary, FedRBC's mean F1 is $0.540 \pm 0.081$ (5 seeds) against $0.620 \pm 0.038$ for EIFFeL and $0.458 \pm 0.277$ for RAID — a robustness tax of about 8 points relative to the unfiltered coordinate-clipping baseline, the known price of direction-aware gating. We report two observations from developing this experiment. First, the tax is real but bounded: the softmax evidence weighting discounts skewed-but-benign updates that a magnitude-only baseline retains, exactly as designed. Second, and of independent methodological value, we found and fixed a **numerical-stability defect** that would otherwise have produced spurious seed-level collapses: when a client's local update degenerates to (near-)zero norm, the cosine evidence $\cos(\Delta_i, \Delta_{\mathrm{root}})$ becomes $0/0$ and propagates NaN through the reputation vector and the global model, after which the model degenerates to all-one-class prediction (F1 collapses to 0 with accuracy pinned at the benign-class ratio). We guard against this by rejecting non-finite evidence at the aggregator and skipping any non-finite aggregate update — the same guard stated with the evaluation setup in Section 5.1; with the guard, no seed in any of the 45 main-table and no-attack runs collapses, and FedRBC's variance is the smallest of all systems. We document this because Byzantine-robust FL simulations are themselves susceptible to NaN collapse, and an unaudited harness can silently report such a collapse as a robustness *failure* of the method under test.

**Ablation of the ledger.** The cross-round-memory ablation (reputation reset every round) is now measured in Section 5.9 rather than delegated: final F1 is statistically unchanged, which sharpens rather than weakens the ledger's case — the F1 defence is carried by the gate, while the ledger's contribution is exactly the operational properties an aggregation rule cannot express: cross-round suppression (the 12× reputation separation of Section 5.5), resistance to intermittent adversaries that reset their consequences each round, the immutable audit trail, and the containment events of Section 4.5.

## 5.8 Cross-dataset generalization (CICIoT2023)

To assess whether the main results are an artifact of the WUSTL-EHMS-2020 benchmark rather than a property of the method, we repeat the three-attack main comparison on a second dataset, CICIoT2023 [52] — a large-scale IoT attack benchmark (45M flows, 33 attack types) of which we use the first CSV partition (238,687 flows, 40 numeric features). Unlike WUSTL-EHMS-2020, in which the attack class is the minority (12.5%), the raw CICIoT2023 partition is attack-dominated (benign traffic is only a $\sim$2.3% minority), so we down-sample the attack flows to a 3:1 attack-to-benign ratio; this keeps the benign class as a non-trivial minority and matches the detection setup of the main benchmark. Table 5 reports the three-seed means. FedRBC again attains the highest F1 in every scenario — $0.992 \pm 0.000$, $0.730 \pm 0.344$, and $0.992 \pm 0.000$ under sign-flip, Sybil, and label-flip respectively — with the largest margins over the baselines in exactly the hardest scenarios: under Sybil collusion FedRBC's 0.730 leads FedGT's 0.629 and EIFFeL's 0.417, and under label-flip its 0.992 leads EIFFeL's 0.947. The cross-dataset agreement, together with the smallest-variance property of Table 4, supports the claim that FedRBC's advantage is architectural rather than benchmark-specific.

**Table 5.** Cross-dataset generalization on CICIoT2023 ($\beta$=30%, $\alpha$=0.5; mean ± std, 3 seeds). Best F1 per row in bold.

| Attack | **FedRBC (Ours)** | RAID (2026) | FedGT (2025) | EIFFeL (2022) |
|---|---|---|---|---|
| Sign-flip | **0.992±0.000** | 0.286±0.495 | 0.901±0.076 | 0.987±0.006 |
| Sybil collusion | **0.730±0.344** | 0.592±0.514 | 0.629±0.546 | 0.417±0.400 |
| Label-flip | **0.992±0.000** | 0.615±0.537 | 0.575±0.489 | 0.947±0.078 |

## 5.9 Extended threat-model and operational envelope

The boundary scenarios of Section 5.7 leave three directions of the security envelope unmeasured, and this section completes them: the adversarial families that *target the gate's own statistic* rather than violating direction, the trust assumption on the root set, and the privacy layer of Section 4.7. The evaluation protocol is as follows. (i) *Adaptive collusive poisoning*: the LIE construction of Baruch et al. [14] perturbs each coordinate by the mean plus $z_\sigma$ standard deviations of the honest coordinate distribution, surviving norm-based filtering while remaining direction-aligned — an attack aimed precisely at the separation premise $\Delta c > 0$ of Lemma 1. (ii) *Targeted backdoor*: following the trigger-planting design of Bagdasaryan et al. [15], trigger-bearing samples are planted in the attackers' local data, and we report main-task F1 jointly with the attack success rate (ASR — the fraction of trigger-carrying benign test samples misclassified into the attack class), so the utility–stealth trade-off is visible rather than inferred. (iii) *Reference poisoning*: the root direction is corrupted at $\varepsilon \in \{0.1, 0.2, 0.3\}$ while the Byzantine attack proceeds, isolating the root-trust premise that Lemma 1 states explicitly. (iv) *Privacy–robustness composition*: the output-perturbation layer (Eq. 16) is enabled at $\sigma_{\mathrm{dp}} \in \{0.005, 0.02, 0.1\}$ for FedRBC, FLTrust, EIFFeL, and FedAvg under sign-flip and Sybil attacks, mapping the accuracy–robustness trade-off against the RDP budget of Eq. (17). The operational envelope extends the Byzantine ratio to $\beta = 0.5$ (testing the plurality-independence claim at its breaking point), scales the client population to $N \in \{50, 100\}$, and sweeps the mechanism parameters $(T_s, \kappa_c, \theta_h, K, \text{root size})$ around the defaults of Table 2.

**(i–iii) Extended attack results.** Table 6 reports the outcomes, each with the metric its attack class demands. Under **LIE**, the collusive mean-plus-$z_\sigma$ construction breaks the plurality- and coordinate-based baselines (EIFFeL 0.290±0.286, FedAvg 0.238±0.297, both with seed-level collapses), while the root-referenced family holds: FLTrust is the strongest (0.605±0.066) and FedRBC stays at 0.517±0.054 — 96% of its own no-attack mean, with the smallest variance of the four. This is exactly the regime Lemma 1 anticipates: the perturbation keeps direction-aligned, $\Delta c$ shrinks toward zero, the exponential gate factor degrades, and the residual defence is Layer-0 filtering plus relative clipping absorbing the magnitude inflation — a graceful degradation rather than a cliff. Under the **targeted backdoor**, every method preserves main-task F1 (FedRBC 0.604±0.099) but none suppresses the attack: ASR is 0.994–0.996 across all methods. We report this gap as a boundary of the design space, not a success: a planted trigger does not violate update direction, so no directional, magnitude, or reputation evidence discriminates it; the main-task F1 shows the backdoor is *additive* rather than destructive, but suppressing it requires complementary mechanisms (anomaly detection or sparse-update regularization) outside this paper's scope — a scope statement Section 4.6 makes explicit. Under **reference poisoning**, the composition pays off: with the root direction corrupted at $\varepsilon$ up to 0.3 under concurrent Sybil attack, FedRBC holds 0.566±0.101 F1 (95–104% of its clean-reference mean), because the gate degrades but Layer-0, relative clipping, and the accumulated ledger continue to score and demote the adversary; FLTrust, whose ReLU gate *solely* trusts the root direction, decays monotonically (0.522→0.467→0.417 under Sybil). We report this as a Sybil-regime result: under sign-flip the two systems are statistically indistinguishable across the sweep (FedRBC 0.484–0.498 vs FLTrust 0.485–0.508, both with one collapsed seed at $\varepsilon{=}0.2$), so the composition's redundancy advantage is specific to the forged-direction regime where the ledger's accumulated evidence contributes most. The trust-bootstrapping premise of Lemma 1 is thus measurable, and the composed system is more redundant against its failure than any single-mechanism member of its own family — in the regime where that redundancy is exercised.

**Table 6.** Extended threat-model results (WUSTL-EHMS-2020; mean±std; LIE 5 seeds, backdoor 3 seeds, root-poison 3 seeds, Byzantine-ratio extension 3 seeds). ASR = attack success rate of trigger-carrying benign samples.

| Study | Method | F1 | ASR |
|---|---|---|---|
| LIE (collusive) | **FedRBC (Ours)** | 0.517±0.054 | — |
| | FLTrust | 0.605±0.066 | — |
| | EIFFeL (2022) | 0.290±0.286 | — |
| | FedAvg | 0.238±0.297 | — |
| Backdoor (trigger) | **FedRBC (Ours)** | 0.604±0.099 | 0.994±0.005 |
| | FLTrust | 0.579±0.074 | 0.996±0.003 |
| | FedAvg | 0.622±0.108 | 0.994±0.007 |
| Root-poison ε=0.3, Sybil | **FedRBC (Ours)** | 0.566±0.101 | — |
| | FLTrust | 0.417±0.145 | — |
| Root-poison ε=0.2, Sybil | **FedRBC (Ours)** | 0.584±0.084 | — |
| | FLTrust | 0.467±0.204 | — |
| Root-poison ε=0.1, Sybil | **FedRBC (Ours)** | 0.557±0.087 | — |
| | FLTrust | 0.522±0.241 | — |
| Byzantine ratio β=0.5, Sign-flip | **FedRBC (Ours)** | 0.519±0.098 | — |
| | FLTrust | 0.315±0.310 | — |
| | EIFFeL (2022) | 0.148±0.129 | — |
| | FedAvg | 0.074±0.129 | — |
| Byzantine ratio β=0.5, Sybil | **FedRBC (Ours)** | 0.564±0.038 | — |
| | FLTrust | 0.384±0.316 | — |
| | EIFFeL (2022) | 0.138±0.239 | — |
| | FedAvg | 0.148±0.129 | — |

**(iv) Privacy–robustness composition.** Table 7 maps the trade-off of the output-perturbation layer (Eq. 16) across three noise levels. Two facts stand out. First, the softmax gate tolerates privacy noise far better than the hard gate: at $\sigma_{\mathrm{dp}}=0.1$ — a stress level at which the noise magnitude rivals the reference norm — FedRBC retains 0.447–0.448 F1 while FLTrust collapses to 0.220–0.222 (a ReLU gate fed noisy evidence zeroes out the honest mass it should keep, the same asymmetry that its LIE behavior exposes in reverse); at $\sigma_{\mathrm{dp}}=0.005$ and $0.02$ the perturbation costs FedRBC at most a few points (0.608/0.585 under sign-flip, 0.549/0.510 under Sybil) — at the lightest level the noise even acts as a mild regularizer against the sign-flip attack. Second, the composition cost is paid independently of the attack regime, so a deployment locates its working point on the measured curve: light accounting-grade noise preserves essentially all of the advantage, while the stress level bounds the worst case from below near 0.45 F1. Combined with Eq. (17)'s explicit RDP budget, the "Privacy-Preserving" claim of the title is backed by a measured trade-off rather than an unexamined mechanism.

**Table 7.** Accuracy–robustness trade-off under the DP output-perturbation layer (Eq. 16; F1, 3 seeds; sign-flip / Sybil attacks at $\beta$=30%).

| $\sigma_{\mathrm{dp}}$ | Method | Sign-flip F1 | Sybil F1 |
|---|---|---|---|
| 0.005 | **FedRBC (Ours)** | 0.608±0.040 | 0.549±0.093 |
| | FLTrust | 0.591±0.095 | 0.539±0.025 |
| | EIFFeL (2022) | 0.484±0.114 | 0.148±0.129 |
| | FedAvg | 0.107±0.185 | 0.149±0.129 |
| 0.02 | **FedRBC (Ours)** | 0.585±0.044 | 0.510±0.096 |
| | FLTrust | 0.556±0.158 | 0.497±0.023 |
| | EIFFeL (2022) | 0.467±0.119 | 0.269±0.057 |
| | FedAvg | 0.139±0.136 | 0.129±0.115 |
| 0.1 | **FedRBC (Ours)** | 0.447±0.199 | 0.448±0.212 |
| | FLTrust | 0.220±0.137 | 0.222±0.002 |
| | EIFFeL (2022) | 0.254±0.043 | 0.089±0.116 |
| | FedAvg | 0.126±0.110 | 0.086±0.149 |

**Operational envelope.** At $\beta = 0.5$ — a forged *majority* — FedRBC is the only method that stays above 0.5 F1 (0.519±0.098 under sign-flip, 0.564±0.038 under Sybil), while FLTrust falls to 0.315±0.310 and 0.384±0.316 with collapsed seeds, EIFFeL to 0.148±0.129 and 0.138±0.239, and FedAvg to 0.074±0.129 and 0.148±0.129 — sustaining the plurality-independence claim at its breaking point (rows in Table 6). Scaling the population sharpens the variance story: at $N=50$ FedRBC reaches 0.523±0.073 and at $N=100$ it reaches 0.573±0.037 — the variance *shrinks* with population while FLTrust shows a collapsed seed at $N=50$ (0.375±0.310) and clean FedAvg is degenerate at both scales — because the density-greedy selection keeps the aggregation quorum at $K$ regardless of $N$, so scale adds averaging diversity without adding exposure. The sensitivity sweep locates the defaults near local optima: the gate temperature is flat across $T_s \in \{0.1, 0.5\}$ (0.570–0.589, confirming that the softmax form distinguishes by *degree* rather than by a knife-edge threshold), the reward threshold $\theta_h$ and quorum $K$ are mildly monotone (0.544→0.616 for $\theta_h$ 0.1→0.5; 0.535→0.620 for $K$ 6→14), root size 100–500 spans 0.519→0.561, and the only genuinely harmful setting is over-tight clipping ($\kappa_c=1$: 0.502, -6 points) — clipping must cap the adversary without strangling the skewed-but-benign updates it exists to preserve.

**Component ablation.** Table 8 removes each component independently under all three attacks (3 matched seeds, with the same-seed full-system row as the reference). The pattern is attack-dependent and honest: selection contributes most under sign-flip and label-flip because its absence occasionally admits a malicious plurality into the quorum (random selection shows the collapses: 0.497±0.212 and 0.503±0.226); relative clipping is decisive under sign-flip (-8.2 points, the one attack it exists to bound); the gate, Layer-0, and reputation weighting contribute 1–5 points each with attack-dependent sign; and the **cross-round memory ablation** (reputation reset every round — the ledger-memory question of Section 5.7) leaves F1 statistically unchanged (0.564/0.604/0.610 vs 0.602/0.581/0.578 same-seed full) — the F1 defence is carried by the gate, while the ledger's value is operational: the adversary cannot outlive exposure (the 12× reputation separation of Section 5.5), intermittent attackers cannot reset consequences, and the audit trail feeds containment. We consider a mechanism whose statistical contribution is exactly zero *in the dimension it does not claim* and whose claimed dimensions (memory, immutability, auditability, actuation) are architectural, to be an honest component — the ablation says so in numbers.

**Table 8.** Component ablation under three attack classes (F1, 3 matched seeds; same-seed full-system reference).

| Configuration | Sign-flip | Sybil | Label-flip |
|---|---|---|---|
| FedRBC (full, same seeds) | 0.602±0.081 | 0.581±0.075 | 0.578±0.072 |
| - directional gate | 0.591±0.063 | 0.538±0.032 | 0.564±0.056 |
| - relative clipping | 0.520±0.035 | 0.585±0.052 | 0.555±0.072 |
| - Layer-0 filter | 0.558±0.083 | 0.546±0.101 | 0.575±0.063 |
| - reputation weighting | 0.552±0.118 | 0.561±0.021 | 0.580±0.044 |
| - selection (random) | 0.497±0.212 | 0.616±0.048 | 0.503±0.226 |
| - cross-round memory (ledger reset) | 0.564±0.022 | 0.604±0.035 | 0.610±0.034 |

# 6. Discussion and Limitations

## 6.1 Why composition beats any single defense family

The evaluation shows a consistent pattern (Table 4): each baseline does best in exactly the attack geometry its own mechanism targets, and worst everywhere else. FedGT's hard identification cleanly separates direction-inconsistent clients at low attack intensity, but it is brittle — a binary threshold either drops the adversary outright or lets it through at full weight, which shows up as widening seed variance. EIFFeL's coordinate consensus handles moderate direction attacks yet collapses once the malicious set becomes the plurality. RAID's per-round scoring has no memory, so it cannot converge to a decision. What sets FedRBC apart is not a stronger version of any single family but the way the pieces work together: the softmax gate provides what binary identification cannot (graded, low-variance suppression), the root reference provides what plurality cannot (collusion resistance), relative clipping provides what direction cannot (magnitude resistance), and the ledger provides what per-round scoring cannot (memory). The threat-coverage matrix (Table 3) predicts the outcome table (Table 4) row by row — the clearest sign that the result reflects the architecture rather than chance. The published system closest to ours — the blockchain-SDN edge framework of Tyagi et al. (CMC 2026) [53] — shares the same three-layer setting but treats security only through qualitative discussion: no dataset, no runnable poisoning evaluation, and no robustness guarantee for the learning process. The emerging fielded deployments — blockchain-secured FL for industrial air-quality monitoring [33] and the three-hospital FL-IoT installation of [34] — show that the architecture class is deployable in practice, yet neither system can isolate a convicted device from the network, which is precisely the operational step FedRBC adds. FedRBC keeps the architectural idea (chain as trust anchor, SDN as actuator) but moves the evaluation to where the claims actually live: three attack classes, three recent aggregation systems, and theorem-level bounds for convergence, suppression, and containment.

## 6.2 Lessons from the design space

Two instructive failures encountered during development delimit where reputation-composed defenses do *not* help. (i) *Soft power gating is a trap.* Replacing a hard gate by $\max(0, s_i)^p$ with $p < 1$ — intended to retain benign-but-skewed updates under non-IID — consistently degraded accuracy under attack (up to 14 F1 points at $\beta=0.3$), because whatever softens the gate for skewed honest updates softens it for poison in exactly the same way; the softmax form of Eq. (6) was adopted precisely because it distinguishes the two by *degree* (exponential suppression of reversal, $O(1)$ retention of near-zero evidence). (ii) *Fixed clipping radii misfire against magnitude attacks.* An early version with constant $\tau_c$ lost to a plain median/MAD filter under scaling, because a direction-preserving magnitude attack is invisible to cosine evidence; making the radius relative to $\|\Delta_{\mathrm{root}}\|$ (Eq. 5) closed precisely this hole. The composition cannot compensate for a missing physical mechanism.

## 6.3 Limitations

Five limitations bound the claims. First, the evaluation is simulation-based: attacks are injected by the harness rather than captured from live compromise; while this is standard practice for controlled Byzantine evaluation, attacker creativity in the wild will exceed even the expanded set evaluated here (direction-inconsistent forgeries, LIE-style collusive perturbations, targeted backdoors, and reference poisoning — Section 5.9), and the measured backdoor results show the boundary concretely: main-task F1 is preserved but attack success is not suppressed by any evaluated method. Deployment feasibility, for its part, is bounded by the compute envelope measured in Section 5.6: FedRBC's client-side cost is local SGD plus one cosine against the broadcast root direction — no on-device cryptography — and the trust computation is a fused tensor pass of the same order as plain averaging, so the mechanism fits the sensor class the evaluation emulates; the 20-client emulation itself (Section 5.1) makes no device-feasibility claim beyond this envelope, and the N=50/100 scaling study shows the variance only improves with population. Second, the root set is a trust assumption, and its limits are empirically visible: under extreme non-IID ($\alpha=0.1$) with 30% of updates forged, FedRBC's F1 drops by 24 points to $0.326$ (Fig. 6) — honest directions scatter so widely that directional evidence loses contrast, and the residual performance reflects the reference degrading rather than failing. Reference poisoning is now measured empirically (Section 5.9) rather than assumed away, but fully adversarial references remain an open problem shared with all trust-bootstrapped defenses [37], mitigated by quarterly refresh and, prospectively, rotating cross-validated root subsets. Third, the MTTC analysis models the event pipeline as M/M/1; bursty, heavy-tailed alert arrivals will inflate the tail beyond the mean we report, and a GI/G/1 refinement is future work. The same architectural separation bounds controller failure: if the ONOS controller is unavailable, containment actuation degrades, but the learning path never does — aggregation-side defences (gate, clipping, Layer-0) keep training, and quarantine decisions replay from the immutable ledger once the controller returns, which is the containment-side counterpart of the same asymmetry. Fourth, FedRBC protects raw data by construction, and the accounted output-perturbation layer of Section 4.7 protects the aggregated trajectory against gradient inversion with an explicit RDP budget — the accounting builds on the Rényi-differential-privacy composition calculus of Mironov [55], while the privacy–robustness trade-off we measure in Section 5.9 extends the DP-in-FL performance analysis of Wei et al. [56] from honest averaging to the robust-aggregation setting, and the same budget that bounds membership-inference on the released trajectory is therefore explicit rather than assumed; the residual boundary is per-update confidentiality against an honest-but-curious aggregation server, which requires secure aggregation and remains future work. Fifth, as the measurements themselves surfaced: grey-zone penalization is not noise-aware. As update norms shrink late in training, directional evidence becomes noise-dominated and erodes *all* reputations, honest ones included (53% of honest clients touch the quarantine line by round 60 in the attack runs; 85-100% over 60 no-attack rounds — Section 5.5). The relative ranking survives, the F1 defence is unaffected, and cold-start probation provides the recovery path — a quarantined device re-enters at $r_0$ under the documented probation of Sections 4.4–4.5 — but a deployment that reads $r_{\mathrm{q}}$ as an absolute no-false-quarantine guarantee would over-isolate; a penalty gate that widens the grey zone as $\|\Delta_{\mathrm{root}}\|$ shrinks is the direct fix. Finally, a clinical-safety note for the intended environment: containment isolates a convicted device's *training traffic* from the federation, not its clinical function — an infusion pump keeps infusing, a monitor keeps monitoring; for equipment whose participation is nonetheless deemed critical, the contract's cold-start path (rather than indefinite quarantine) and read-only fallback modes keep the device re-admissible without model influence, so the operational risk of isolation is a bounded re-entry delay rather than a clinical outage. Future work also includes live-traffic validation with red-team exercises and root-set hardening through rotating, cross-validated root subsets.

# 7. Conclusion

This paper introduced FedRBC, a blockchain-enabled reputation-weighted robust federated learning framework for healthcare IoT edge networks. Its organizing principle is a single on-chain trust root that drives aggregation, selection, and containment together. A reference-guided aggregation rule — Layer-0 statistical pre-filtering, relative magnitude clipping, and softmax evidence gating — covers the direction-inconsistent attack classes that defeat plurality-based defenses, with an accounted differential-privacy option whose privacy–robustness trade-off is measured; a smart-contract reputation ledger adds trust memory, immutability, and auditability; and an SDN-actuated loop turns on-chain conviction into network quarantine within a bounded mean time. The theory is deliberately mechanistic: a new lemma bounds the residual malicious weight of the convergence result *explicitly* in the gate's directional separation, the ledger's reputation ratio, and the temperature, rather than assuming it away. A simulation-based evaluation on a containerized testbed — ten-seed main-table replication, two datasets, extended attack families (LIE, backdoors with attack-success-rate scoring, reference poisoning), Byzantine ratios to 50%, and client populations to 100, anchored by centralized and clean-FedAvg references with Holm-corrected significance testing — showed FedRBC attaining the best AUC and the smallest variance in every scenario, an F1 statistically tied with the strongest classical baseline, FLTrust, and significantly ahead of every plurality- or coordinate-based baseline where those families fail (Sybil collusion), while being the only evaluated method that carries trust memory, auditability, and network-level containment; it stays above 0.5 F1 at a 50% Byzantine ratio and holds its defence when the reference set itself is poisoned (a Sybil-regime result, Section 5.9). The system's limitations are stated plainly: simulation-based attacks, a trusted root set (now measured rather than assumed), a mean-field queueing model, evidence degeneration late in training that erodes absolute reputations, and backdoor resistance outside the mechanism's scope. Future work includes live-traffic validation, bursty-arrival containment analysis, root-set hardening, a noise-aware penalty gate, and secure aggregation for per-update confidentiality.


# Appendix A. Algorithms

# Appendix A. Algorithms

**Algorithm 1: FedRBC Training Protocol (one round $t$)**

| | |
|---|---|
| **Input:** | global model $\mathbf{w}_t$; client set $\mathcal{N}=\{1,\dots,N\}$; reputation vector $\mathbf{r}(t)$ read from the ledger; budget $B$; root set $\mathcal{D}_r$ |
| **Output:** | updated global model $\mathbf{w}_{t+1}$; committed reputation $\mathbf{r}(t+1)$ |
| 1: | $\mathcal{S}_t \leftarrow \textsc{RepAwareSelect}(\mathbf{r}(t), \mathbf{u}, \mathbf{c}, K, B)$  $\triangleright$ Eq. (11), Alg. 3 |
| 2: | **broadcast** $(\mathbf{w}_t, \mathcal{S}_t)$ to selected clients |
| 3: | **for each** $i \in \mathcal{S}_t$ **in parallel do** |
| 4: | $\quad \mathbf{w}_i \leftarrow \textsc{LocalSGD}(\mathbf{w}_t, \mathcal{D}_i)$; $\ \Delta_i \leftarrow \mathbf{w}_i - \mathbf{w}_t$  $\triangleright$ Eq. (2) |
| 5: | $\quad$ **submit** $\Delta_i$ together with hash $H(\Delta_i)$ |
| 6: | **end for** |
| 7: | $\Delta_{\mathrm{root}} \leftarrow \textsc{LocalSGD}(\mathbf{w}_t, \mathcal{D}_r)$  $\triangleright$ Eq. (3) |
| 8: | **for each** $i \in \mathcal{S}_t$ **do** |
| 9: | $\quad s_i \leftarrow \cos(\Delta_i, \Delta_{\mathrm{root}})$  $\triangleright$ Eq. (4), evidence |
| 10: | $\quad$ **call** $\textsc{ReputationContract.writeEvidence}(i, s_i, H(\Delta_i))$  $\triangleright$ on-chain, Alg. 2 |
| 11: | **end for** |
| 12: | $z_i \leftarrow \bigl\lvert \|\Delta_i\| - \mathrm{med}_j\|\Delta_j\| \bigr\rvert / (1.4826\,\mathrm{MAD}_j)$ for all $i \in \mathcal{S}_t$  $\triangleright$ Layer-0 pre-filter |
| 13: | $\mathcal{V}_t \leftarrow \{i \in \mathcal{S}_t : z_i \leq z_{\mathrm{th}}\}$  $\triangleright$ survivors, $z_{\mathrm{th}}=2$ |
| 14: | $\bar{\Delta}_i \leftarrow \Delta_i \cdot \min(1, \kappa_c\|\Delta_{\mathrm{root}}\| / \|\Delta_i\|)$ for $i \in \mathcal{V}_t$  $\triangleright$ relative clip, Eq. (5) |
| 15: | $q_i \propto p_i \, r_i(t) \exp(s_i / T_s)$ over $i \in \mathcal{V}_t$, normalized  $\triangleright$ softmax evidence, Eq. (6) |
| 16: | $\mathbf{w}_{t+1} \leftarrow \mathbf{w}_t + \eta_g \sum_{i \in \mathcal{V}_t} q_i \, \bar{\Delta}_i$  $\triangleright$ RWRA, Eq. (7) |
| 17: | $\mathbf{r}(t+1) \leftarrow$ ledger state after Alg. 2 |
| 18: | **return** $(\mathbf{w}_{t+1}, \mathbf{r}(t+1))$ |

---

**Algorithm 2: ReputationContract (smart contract, executed on-chain)**

| | |
|---|---|
| **State:** | mapping $i \mapsto r_i \in [0,1]$, initialized $r_i \leftarrow r_0 = 0.5$; parameters $(\gamma, \kappa, \lambda_{\mathrm{dec}}, \theta_h, \theta_m, r_{\mathrm{q}})$  ($\kappa$ here is the penalty acceleration, distinct from the clip scaling $\kappa_c$ of Alg. 1); event log $\mathcal{L}$ (append-only) |
| 1: | **function** $\textsc{writeEvidence}(i, s_i, h_i)$  $\triangleright$ called once per client per round |
| 2: | $\quad$ **require** $s_i \in [-1, 1]$ $\wedge$ caller is the registered edge server |
| 3: | $\quad$ **if** $s_i \geq \theta_h$ **then** |
| 4: | $\quad\quad r_i \leftarrow (1-\gamma)\, r_i + \gamma\, g(s_i)$, $\ g(s) = \tfrac{1+s}{2}$  $\triangleright$ reward, Eq. (8) |
| 5: | $\quad$ **else if** $s_i < \theta_m$ **then** |
| 6: | $\quad\quad r_i \leftarrow (1 - \kappa\gamma)\, r_i$  $\triangleright$ penalty, Eq. (9), Prop. 1 |
| 7: | $\quad$ **else** |
| 8: | $\quad\quad r_i \leftarrow (1 - \tfrac{\gamma}{2})\, r_i + \tfrac{\gamma}{2}\, g(s_i)$  $\triangleright$ grey zone |
| 9: | $\quad$ **end if** |
| 10: | $\quad r_i \leftarrow \min(1, \max(0, r_i))$; $\ \mathcal{L}.\textsc{append}(t, i, s_i, r_i)$ |
| 11: | $\quad$ **if** $r_i < r_{\mathrm{q}}$ **then emit** $\textsc{ContainmentEvent}(i)$  $\triangleright$ containment $\rightarrow$ ONOS (Section 4.5) |
| 12: | **end function** |
| 13: | **function** $\textsc{applyDecay}(\mathcal{S}_t)$  $\triangleright$ end of each round |
| 14: | $\quad$ **for each** $j \notin \mathcal{S}_t$ **do** $\ r_j \leftarrow r_j (1 - \lambda_{\mathrm{dec}})$  $\triangleright$ Eq. (9) |
| 15: | **end function** |
| 16: | **function** $\textsc{readReputation}()$ **returns** $\mathbf{r}$  $\triangleright$ consumed by Alg. 3 and Eq. (7) |

---

**Algorithm 3: Reputation-Aware Client Selection (density-greedy, 1/2-approximation, Prop. 2)**

| | |
|---|---|
| **Input:** | reputation $\mathbf{r}(t)$; utility $u_i$; cost $c_i$; quorum size $K$; latency budget $B$ |
| **Output:** | selected set $\mathcal{S}_t$, $\lvert\mathcal{S}_t\rvert = K$ |
| 1: | **for each** $i \in \mathcal{N}$ **do** $\ d_i \leftarrow r_i(t) \cdot u_i \,/\, c_i$  $\triangleright$ density, Eq. (11) |
| 2: | sort $\mathcal{N}$ in non-increasing order of $d_i$; $\ \mathcal{S}_t \leftarrow \emptyset$; $\ \mathrm{cost} \leftarrow 0$ |
| 3: | **for each** $i$ in the sorted order **do** |
| 4: | $\quad$ **if** $\lvert\mathcal{S}_t\rvert = K$ **then break** |
| 5: | $\quad$ **if** $\mathrm{cost} + c_i \leq B$ **then** $\ \mathcal{S}_t \leftarrow \mathcal{S}_t \cup \{i\}$; $\ \mathrm{cost} \leftarrow \mathrm{cost} + c_i$ |
| 6: | **end for** |
| 7: | $\mathcal{S}'_t \leftarrow \{i^*\}$, the single highest-density feasible item (if any) |
| 8: | **return** $\arg\max_{X \in \{\mathcal{S}_t, \mathcal{S}'_t\}} \sum_{i \in X} r_i u_i$  $\triangleright$ 1/2-approx. (Prop. 2) |


# Appendix B. Proofs（定理与命题证明）

## B.1 Lemma 1 and Theorem 1 (convergence under Byzantine poisoning)

**Lemma 1 (gate-induced residual weight).** Fix a round $t$ and the selected set $\mathcal{S}_t$, and assume: (i) directional separation — every honest survivor of the Layer-0 filter has root alignment $s_i \ge c_H$ and every Byzantine survivor has $s_i \le c_B$, with gap $\Delta c = c_H - c_B > 0$ (Eq. 4); (ii) the Layer-0 filter removes no honest client, and at most $\beta K$ of the selected clients are Byzantine; (iii) priors $p_i \in [p_{\min}, p_{\max}]$ and reputations $r_i \in [r_{\min}, r_{\max}]$. Then the aggregate weight that Eq. (6) assigns to Byzantine clients obeys

$$\epsilon_r(t) = \sum_{i \in \mathcal{B} \cap \mathcal{S}_t} q_i(t) \le \rho_\beta\, \rho_p\, \rho_r\, e^{-\Delta c/T_s},$$

with $\rho_\beta = \beta/(1-\beta)$, $\rho_p = p_{\max}/p_{\min}$, and $\rho_r = r_{\max}/r_{\min}$ (Eq. 15).

**Proof.** Let $\mathcal{S}'_t \subseteq \mathcal{S}_t$ denote the Layer-0 survivors and write the unnormalized gate mass $N_i = p_i\, r_i(t)\, \mathbb{1}[z_i \le z_{\mathrm{th}}]\, \exp(s_i/T_s)$, so that $q_i = N_i / \sum_{j \in \mathcal{S}'_t} N_j$. By assumption (ii) all honest clients survive and $|\mathcal{B} \cap \mathcal{S}_t| \le \beta K$, hence $|\mathcal{H} \cap \mathcal{S}'_t| \ge (1-\beta)K$. The Byzantine mass is at most

$$\sum_{i \in \mathcal{B} \cap \mathcal{S}'_t} N_i \;\le\; \beta K\, p_{\max} r_{\max}\, e^{c_B/T_s},$$

while the honest mass is at least

$$\sum_{i \in \mathcal{H} \cap \mathcal{S}'_t} N_i \;\ge\; (1-\beta)K\, p_{\min} r_{\min}\, e^{c_H/T_s}.$$

Since the normalizer of Eq. (6) satisfies $\sum_{j \in \mathcal{S}'_t} N_j \ge \sum_{i \in \mathcal{H} \cap \mathcal{S}'_t} N_i$, the residual malicious weight obeys

$$\epsilon_r(t) \;=\; \frac{\sum_{i \in \mathcal{B}} N_i}{\sum_{j \in \mathcal{S}'_t} N_j} \;\le\; \frac{\beta K\, p_{\max} r_{\max}\, e^{c_B/T_s}}{(1-\beta)K\, p_{\min} r_{\min}\, e^{c_H/T_s}} \;=\; \rho_\beta\, \rho_p\, \rho_r\, e^{-\Delta c/T_s}.$$

For the time-varying form, note that Prop. 1 gives $r_i(t) \le r_0(1-\kappa\gamma)^t$ for a client penalized every round; substituting $r_{\max}(t) = r_0(1-\kappa\gamma)^t$ for the persistently exposed adversary and a strictly positive honest lower bound $r_{\min} > 0$ yields $\epsilon_r(t) \le \bar\epsilon_r \cdot (1-\kappa\gamma)^t$: spatial suppression by the gate and temporal suppression by the ledger compose multiplicatively. In practice $r_{\min}$ is the measured lower quantile of honest reputations — Section 5.5 shows that honest reputations themselves drift downward once update norms shrink and directional evidence becomes noise-dominated, so $r_{\min}$ is small but strictly positive, and the bound holds with a correspondingly conservative $\rho_r$. $\square$

**Theorem 1 (convergence).** Let $F$ be $L$-smooth and bounded below by $F^*$, let client stochastic gradients have variance bounded by $\sigma^2$, and let honest updates satisfy $\mathbb{E}\|\Delta_i\| \le G$ with directional alignment $\mathbb{E}[\cos(\Delta_i, \nabla F(\mathbf{w}_t))] \ge \mu_d > 0$. Suppose at most $\beta K$ of the selected clients are Byzantine, and the directional-separation conditions of Lemma 1 hold, so that the aggregate leaves residual malicious weight $\epsilon_r = \sum_{i \in \mathcal{B}} q_i$ bounded by the explicit quantity $\bar\epsilon_r = \rho_\beta \rho_p \rho_r e^{-\Delta c/T_s}$ of Lemma 1. Then, with global step size $\eta_g = \Theta(1/\sqrt{T})$,

$$\frac{1}{T}\sum_{t=1}^{T} \mathbb{E}\|\nabla F(\mathbf{w}_t)\|^2 \;\le\; \frac{2(F(\mathbf{w}_1) - F^*)}{\eta_g T} + \eta_g L\Bigl(\frac{\sigma^2}{K} + 2G^2\Bigr) + 2(\beta + \bar\epsilon_r)\,\tau_c G \, L \eta_g,$$

which refines Eq. (14) with explicit constants.

**Proof.** Descent lemma applied to $\mathbf{w}_{t+1} = \mathbf{w}_t + \eta_g \sum_i q_i \phi(\Delta_i)$. Decompose the aggregate into honest gated part and malicious residue. The honest part, by the alignment assumption and the bounded gate $e^{s_i/T_s} \le e^{1/T_s}$, differs from $\nabla F(\mathbf{w}_t)$ by $O(\sigma/\sqrt{K})$ in expectation. The malicious residue is bounded by $\sum_{i\in\mathcal{B}} q_i \|\bar\Delta_i\| \le \epsilon_r \tau_c \le \bar\epsilon_r \tau_c$ with $\bar\epsilon_r$ given by Lemma 1, since clipping caps every admitted update at $\tau_c$ (Eq. 5) and Layer-0 removes outliers. Summing over $t$, telescoping, and choosing $\eta_g = \Theta(1/\sqrt{T})$ yields the bound; the last term is $\mathcal{O}((\beta + \bar\epsilon_r)\tau_c G/\sqrt{T})$, which vanishes as $\tau_c(t) = \kappa_c\|\Delta_{\mathrm{root}}(t)\|$ contracts with convergence, and contracts further as the ledger drives $\bar\epsilon_r$ down geometrically for exposed adversaries. $\square$

## B.2 Proposition 1 (geometric reputation suppression)

**Statement.** If client $i$ is penalized in every round ($s_i < \theta_m$), then $r_i(t) \le r_0 (1-\kappa\gamma)^t$, and $r_i$ crosses the quarantine threshold $r_{\mathrm{q}}$ within

$$T_0 = \left\lceil \frac{\ln(r_{\mathrm{q}}/r_0)}{\ln(1-\kappa\gamma)} \right\rceil$$

rounds, independently of the client's history before $t=0$.

**Proof.** The penalty branch (Eq. 9) applies the contraction $r_i \leftarrow (1-\kappa\gamma) r_i$ each round; induction gives $r_i(t) = r_0(1-\kappa\gamma)^t$ (exact equality when every round penalizes). Solving $r_0(1-\kappa\gamma)^{T_0} \le r_{\mathrm{q}}$ for $T_0$ gives the closed form. With $(r_0, r_{\mathrm{q}}, \kappa\gamma) = (0.5, 0.15, 0.6)$, $T_0 = \lceil \ln(0.3)/\ln(0.4) \rceil = \lceil 1.315 \rceil = 2$; with intermittent penalization every second round the crossing time doubles, which the asymmetry analysis of Section 4.4 accounts for. Fig. 8 overlays this bound on the measured trajectory: the every-round case is the best case, and the measured median crossing of 14 rounds reflects adversaries being scored only in the rounds they are selected — consistent with the intermittent-exposure regime rather than contradicting the bound. $\square$

## B.3 Theorem 2 (MTTC separation)

**Statement.** Model the containment pipeline as an M/M/1 queue with alert rate $\lambda_a$ and service rate $\mu > \lambda_a$. The edge-actuated loop and the cloud-roundtrip loop satisfy

$$\Delta\mathrm{MTTC} = \bar{t}_{\mathrm{cloud}} - \bar{t}_{\mathrm{chain}} + \frac{1}{\mu-\lambda_a} \;\ge\; \bar{t}_{\mathrm{WAN}},$$

which is independent of $\rho$ in the mean and grows with utilization in the tail.

**Proof.** The edge path has no queueing: its latency is the deterministic block commit $\bar{t}_{\mathrm{chain}}$ (Eq. 12). The cloud path queues at an M/M/1 server, so its mean sojourn is $1/(\mu-\lambda_a)$ plus the WAN round trip $\bar{t}_{\mathrm{cloud}}$ (Eq. 13). Subtracting gives $\Delta\mathrm{MTTC} = \bar{t}_{\mathrm{cloud}} - \bar{t}_{\mathrm{chain}} + 1/(\mu-\lambda_a)$, which is flat in $\rho$ for the edge path and diverges for the cloud path. The tail statement follows from the Pollaczek–Khinchine formula: the sojourn-time variance grows as $(1-\rho)^{-2}$, so any percentile above the mean separates super-linearly in $\rho$; Fig. 9 shows the mean curve, which is the conservative bound. $\square$

## B.4 Proposition 2 (density-greedy selection is a 1/2-approximation)

**Statement.** Alg. 3 returns a set $\mathcal{S}_t$ with $\sum_{i \in \mathcal{S}_t} r_i u_i \ge \tfrac{1}{2} \mathrm{OPT}$, where OPT is the optimum of the knapsack (Eq. 11).

**Proof.** Standard for density-ordered knapsack greedy: let $i^*$ be the first item in the density order not taken. By construction, $\mathrm{ALG} + r_{i^*}u_{i^*} \ge \mathrm{OPT}$ (the fractional-knapsack bound), so either $\mathrm{ALG} \ge \tfrac{1}{2}\mathrm{OPT}$ or the single densest feasible item already satisfies $r_{i^*}u_{i^*} \ge \tfrac{1}{2}\mathrm{OPT}$. Alg. 3 takes the better of the greedy prefix and that single item (lines 7–8), which dominates both cases and yields the $1/2$-approximation. $\square$


# References

[1] H. B. McMahan, E. Moore, D. Ramage, S. Hampson, B. A. y. Arcas, "Communication-Efficient Learning of Deep Networks from Decentralized Data," arXiv:1602.05629, 2016.

[2] N. Rieke, J. Hancox, W. Li, F. Milletarì, H. R. Roth, S. Albarqouni et al., "The future of digital health with federated learning," npj Digital Medicine, vol. 3, no. 1, 2020, doi: 10.1038/s41746-020-00323-1.

[3] G. A. Kaissis, M. R. Makowski, D. Rückert, R. F. Braren, "Secure, privacy-preserving and federated machine learning in medical imaging," Nature Machine Intelligence, vol. 2, no. 6, pp. 305-311, 2020, doi: 10.1038/s42256-020-0186-1.

[4] A. A. Hady, A. Ghubaish, T. Salman, D. Unal, R. Jain, "Intrusion Detection System for Healthcare Systems Using Medical and Network Data: A Comparison Study," IEEE Access, vol. 8, pp. 106576-106584, 2020, doi: 10.1109/access.2020.3000421.

[5] Z. Mundargi, A. Bondarde, A. Joshi, A. Bagad, A. Jadhav, S. Bansod, "Intrusion Detection System Using Federated Learning," Proceedings of the 1st International Conference on Interdisciplinary Research in Science, Engineering, and Technology, pp. 355-361, 2025, doi: 10.5220/0014531600005061.

[6] A. Hamdouchi, A. Idri, "Optimizing Federated Learning for Intrusion Detection in IoT Networks," Proceedings of the 16th International Joint Conference on Knowledge Discovery, Knowledge Engineering and Knowledge Management, pp. 448-456, 2024, doi: 10.5220/0013040000003838.

[7] P. Eichhammer, C. Berger, H. Reiser, "HomeGuard: Community-Driven Hierarchical Federated Learning for Robust Smart-Home Intrusion Detection," Proceedings of the 23rd International Conference on Security and Cryptography, pp. 108-120, 2026, doi: 10.5220/0015063200004103.

[8] S. Uma, M. Priyadharshan, E. Swetha, S. Priyadharshini, "Quantum-Resilient Adaptive Intrusion Detection Using Federated Learning in IoT Networks," Proceedings of the 1st International Conference on Computational and Cognitive Systems Science, pp. 33-40, 2025, doi: 10.5220/0014930000005024.

[9] M. Rehman, H. Bahsi, R. Kalakoti, "Incremental Federated Learning for Intrusion Detection in IoT Networks under Evolving Threat Landscape," Proceedings of the 12th International Conference on Information Systems Security and Privacy, pp. 97-107, 2026, doi: 10.5220/0014475900004061.

[10] Q. Du, B. Li, Z. Shao, Y. Wu, C. Yang, "Federated learning for distributed intrusion detection in IoT networks," Advanced Machine Learning for Cyber-Attack Detection in IoT Networks, pp. 85-110, 2025, doi: 10.1016/b978-0-44-329032-9.00009-9.

[11] D. V. Medhane, A. K. Sangaiah, M. S. Hossain, G. Muhammad, J. Wang, "Blockchain-Enabled Distributed Security Framework for Next-Generation IoT: An Edge Cloud and Software-Defined Network-Integrated Approach," IEEE Internet of Things Journal, vol. 7, no. 7, pp. 6143-6149, 2020, doi: 10.1109/jiot.2020.2977196.

[12] P. Blanchard, E. M. E. Mhamdi, R. Guerraoui, J. Stainer, "Byzantine-Tolerant Machine Learning," arXiv:1703.02757, 2017.

[13] D. Yin, Y. Chen, K. Ramchandran, P. Bartlett, "Byzantine-Robust Distributed Learning: Towards Optimal Statistical Rates," arXiv:1803.01498, 2018.

[14] M. Baruch, G. Baruch, Y. Goldberg, "A Little Is Enough: Circumventing Defenses For Distributed Learning," arXiv:1902.06156, 2019.

[15] E. Bagdasaryan, A. Veit, Y. Hua, D. Estrin, V. Shmatikov, "How To Backdoor Federated Learning," arXiv:1807.00459, 2018.

[16] X. Li, K. Huang, W. Yang, S. Wang, Z. Zhang, "On the Convergence of FedAvg on Non-IID Data," arXiv:1907.02189, 2019.

[17] P. Kairouz, H. B. McMahan, "Advances and Open Problems in Federated Learning," Foundations and Trends® in Machine Learning, vol. 14, no. 1-2, pp. 1-210, 2021, doi: 10.1561/2200000083.

[18] T. Li, A. K. Sahu, M. Zaheer, M. Sanjabi, A. Talwalkar, V. Smith, "Federated Optimization in Heterogeneous Networks," arXiv:1812.06127, 2018.

[19] S. Reddi, Z. Charles, M. Zaheer, Z. Garrett, K. Rush, J. Konečný et al., "Adaptive Federated Optimization," arXiv:2003.00295, 2020.

[20] A. R. Chowdhury, C. Guo, S. Jha, L. v. d. Maaten, "EIFFeL: Ensuring Integrity for Federated Learning," Proceedings of the 2022 ACM SIGSAC Conference on Computer and Communications Security, pp. 2535-2549, 2022, doi: 10.1145/3548606.3560611.

[21] N. Parvizi, S. Saha, N. Shahriar, "RAID: A Reputation-Based Aggregation for Intrusion Detection in Federated Learning," 2026 IEEE 23rd Consumer Communications &amp; Networking Conference (CCNC), pp. 1-6, 2026, doi: 10.1109/ccnc65079.2026.11366587.

[22] J. Weng, J. Weng, J. Zhang, M. Li, Y. Zhang, W. Luo, "DeepChain: Auditable and Privacy-Preserving Deep Learning with Blockchain-based Incentive," IEEE Transactions on Dependable and Secure Computing, pp. 1-1, 2019, doi: 10.1109/tdsc.2019.2952332.

[23] Y. Lu, X. Huang, Y. Dai, S. Maharjan, Y. Zhang, "Blockchain and Federated Learning for Privacy-Preserved Data Sharing in Industrial IoT," IEEE Transactions on Industrial Informatics, vol. 16, no. 6, pp. 4177-4186, 2020, doi: 10.1109/tii.2019.2942190.

[24] S. R. Pokhrel, J. Choi, "Federated Learning With Blockchain for Autonomous Vehicles: Analysis and Design Challenges," IEEE Transactions on Communications, vol. 68, no. 8, pp. 4734-4746, 2020, doi: 10.1109/tcomm.2020.2990686.

[25] Y. Li, C. Chen, N. Liu, H. Huang, Z. Zheng, Q. Yan, "A Blockchain-Based Decentralized Federated Learning Framework with Committee Consensus," IEEE Network, vol. 35, no. 1, pp. 234-241, 2021, doi: 10.1109/mnet.011.2000263.

[26] H. Kim, J. Park, M. Bennis, S. Kim, "Blockchained On-Device Federated Learning," IEEE Communications Letters, vol. 24, no. 6, pp. 1279-1283, 2020, doi: 10.1109/lcomm.2019.2921755.

[27] Y. Zhou, W. Fang, Y. Shi, K. B. Letaief, "Trustworthy Federated Edge Learning via Blockchain," Wireless Networks, pp. 167-190, 2025, doi: 10.1007/978-3-031-96649-1_9.

[28] S. Kannadhasan, P. Kumari, K. Suresh, B. Mallaiah, A. G., S. Rashid, "Designing a Scalable and Secure IoT Framework Using Federated Learning and Blockchain for Edge-AI Devices," Proceedings of the 1st International Conference on Research and Development in Information, Communication, and Computing Technologies, pp. 598-607, 2025, doi: 10.5220/0013870100004919.

[29] Z. Yang, W. Qi, L. Guo, "Resource management for blockchain enhanced federated learning in wireless edge networks," Scientific Reports, vol. 16, no. 1, 2026, doi: 10.1038/s41598-026-56310-1.

[30] X. He, B. Zhang, H. Cui, Y. Jiang, Y. Liu, "Blockchain-based Auction Mechanism for Federated Learning in Edge-enabled Metaverse," 2025 IEEE Global Blockchain Conference (GBC), pp. 1-6, 2025, doi: 10.1109/gbc60041.2025.11134466.

[31] P. Xiao, S. Zeng, "Federated learning-blockchain synergy for multi-objective replication optimization in dynamic cloud-edge networks," Computer Networks, vol. 277, pp. 112014, 2026, doi: 10.1016/j.comnet.2026.112014.

[32] M. J. Baucas, P. Spachos, "Private Blockchain and Federated Learning-Based Edge-Iot Platform for Secure Urban Noise Monitoring," ICC 2025 - IEEE International Conference on Communications, pp. 1145-1150, 2025, doi: 10.1109/icc52391.2025.11160895.

[33] M. N. Ramadan, M. A. Ali, H. Jaber, M. Alkhedher, "Blockchain-secured IoT-federated learning for industrial air pollution monitoring: A mechanistic approach to exposure prediction and environmental safety," Ecotoxicology and Environmental Safety, vol. 300, pp. 118442, 2025, doi: 10.1016/j.ecoenv.2025.118442.

[34] M. N. Ramadan, M. A. Ali, M. Alkhedher, "Development of a federated learning-enabled IoT framework for indoor air quality and HVAC optimization in healthcare buildings," Journal of Building Engineering, vol. 107, pp. 112758, 2025, doi: 10.1016/j.jobe.2025.112758.

[35] O. Chakraborty, A. Boudguiga, "A Decentralized Federated Learning Using Reputation," Proceedings of the 10th International Conference on Information Systems Security and Privacy, pp. 799-806, 2024, doi: 10.5220/0012428300003648.

[36] F. Javed, J. Mangues-Bafalluy, E. Zeydan, L. Blanco, "Trustworthy Reputation for Federated Learning Leveraging Blockchain: A Demonstration," 2025 IEEE Wireless Communications and Networking Conference (WCNC), pp. 1-3, 2025, doi: 10.1109/wcnc61545.2025.10978588.

[37] X. Cao, M. Fang, J. Liu, N. Z. Gong, "FLTrust: Byzantine-robust Federated Learning via Trust Bootstrapping," Proceedings 2021 Network and Distributed System Security Symposium, 2021, doi: 10.14722/ndss.2021.24434.

[38] S. Sagar, A. Mahmood, "RepuFL: Reputation-Aware Client Selection in Federated Learning for Mobile Networks," 2025 IEEE International Conference on Web Services (ICWS), pp. 255-257, 2025, doi: 10.1109/icws67624.2025.00039.

[39] S. Sagar, A. Mahmood, "ReFLect: A Reputation-based Client Selection for Federated Learning in Mobile Networks," ICC 2026 - IEEE International Conference on Communications, pp. 1-6, 2026, doi: 10.1109/icc59461.2026.11586954.

[40] K. Sun, J. Wu, J. Li, "Reputation-Aware Incentive Mechanism of Federated Learning: A Mean Field Game Approach," 2024 9th IEEE International Conference on Smart Cloud (SmartCloud), pp. 48-53, 2024, doi: 10.1109/smartcloud62736.2024.00016.

[41] M. Xhemrishi, J. Ostman, A. Wachter-Zeh, A. Graell i Amat, "FedGT: Identification of Malicious Clients in Federated Learning With Secure Aggregation," IEEE Transactions on Information Forensics and Security, vol. 20, pp. 2577-2592, 2025, doi: 10.1109/TIFS.2025.3539964.

[42] M. M. Rashid, Y. Xiang, M. P. Uddin, J. Tang, K. Sood, L. Gao, "Trustworthy and Fair Federated Learning via Reputation-Based Consensus and Adaptive Incentives," IEEE Transactions on Information Forensics and Security, vol. 20, pp. 2868-2882, 2025, doi: 10.1109/TIFS.2025.3546841.

[43] J. Dai, H. Huang, Y. Wang, L. Duan, F. Hu, D. Yan et al., "Byzantine-resistant model verification for decentralized federated learning in intelligent transportation systems," Applied Soft Computing, vol. 186, pp. 114193, 2026, doi: 10.1016/j.asoc.2025.114193.

[44] E. Kritharakis, A. Makris, D. Jakovetic, K. Tserpes, "FedGreed: A Byzantine-Robust Loss-Based Aggregation Method for Federated Learning," arXiv:2508.18060, 2025.

[45] E. Kritharakis, D. Jakovetic, A. Makris, K. Tserpes, "Robust Federated Learning under Adversarial Attacks via Loss-Based Client Clustering," arXiv:2508.12672, 2025.

[46] A. Nath, H. Kasyap, "CQSA: Byzantine-robust Clustered Quantum Secure Aggregation in Federated Learning," Proceedings of the International Workshop on Secure and Efficient Federated Learning, pp. 1-6, 2026, doi: 10.1145/3803630.3809169.

[47] R. Pinot, "Byzantine-Robust Federated Learning under Heterogeneity: Personalization and Transfer as a Way Forward?," Proceedings of the International Workshop on Secure and Efficient Federated Learning, pp. 1-1, 2026, doi: 10.1145/3803630.3809173.

[48] A. A. Alnajim, "A Byzantine-Resilient Federated Learning Framework with Cryptographic Gradient Attestation Against Coordinated Model Poisoning Attacks," Electronics, vol. 15, no. 17, pp. 3842, 2026, doi: 10.3390/electronics15173842.

[49] Q. Zhou, "PPBRFL: Privacy-Preserving Byzantine-Robust Federated Learning," Frontiers in Computing and Intelligent Systems, vol. 7, no. 1, pp. 18-24, 2024, doi: 10.54097/6jamgy43.

[50] D. Cajaraville-Aboy, A. Fernández-Vilas, R. P. Díaz-Redondo, M. Fernández-Veiga, "Byzantine-Robust Aggregation for Securing Decentralized Federated Learning," IEEE Access, vol. 13, pp. 190947-190963, 2025, doi: 10.1109/access.2025.3629864.

[51] A. Alsaedi, N. Moustafa, Z. Tari, A. Mahmood, A. Anwar, "TON_IoT Telemetry Dataset: A New Generation Dataset of IoT and IIoT for Data-Driven Intrusion Detection Systems," IEEE Access, vol. 8, pp. 165130-165150, 2020, doi: 10.1109/access.2020.3022862.

[52] E. C. P. Neto, S. Dadkhah, R. Ferreira, A. Zohourian, R. Lu, A. A. Ghorbani, "CICIoT2023: A Real-Time Dataset and Benchmark for Large-Scale Attacks in IoT Environment," Sensors, vol. 23, no. 13, pp. 5941, 2023, doi: 10.3390/s23135941.

[53] V. Tyagi, M. Kayal, A. Prasad, G. Ali, S. Shah, M. Asim, "A Secure Blockchain-Enabled SDN-Based Edge Computing Framework for IoT Healthcare Systems," Computers, Materials & Continua, vol. 89, no. 2, pp. 1-10, 2026, doi: 10.32604/cmc.2026.085763.

[54] P. Berde, M. Gerola, J. Hart, Y. Higuchi, M. Kobayashi, T. Koide et al., "ONOS," Proceedings of the third workshop on Hot topics in software defined networking, pp. 1-6, 2014, doi: 10.1145/2620728.2620744.

[55] I. Mironov, "Rényi Differential Privacy," 2017 IEEE 30th Computer Security Foundations Symposium (CSF), pp. 263-275, 2017, doi: 10.1109/csf.2017.11.

[56] K. Wei, J. Li, M. Ding, C. Ma, H. H. Yang, F. Farokhi et al., "Federated Learning With Differential Privacy: Algorithms and Performance Analysis," IEEE Transactions on Information Forensics and Security, vol. 15, pp. 3454-3469, 2020, doi: 10.1109/tifs.2020.2988575.
