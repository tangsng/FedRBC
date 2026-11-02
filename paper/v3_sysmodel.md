# 2. System Model and Assumptions

## 2.1 Network and learning model

The deployment comprises $N$ IoT clients, one edge server, a permissioned blockchain (a consortium of hospital IT, device vendors, and the security operations center), and an ONOS SDN controller. Clients hold disjoint private datasets $\{\mathcal{D}_i\}$ whose label marginals are skewed: each client's marginal follows $\mathbf{q}_i \sim \mathrm{Dir}(\alpha\,\mathbf{1}_C)$ with concentration $\alpha$ and $C$ classes — smaller $\alpha$ yields more heterogeneous (non-IID) partitions. The learning objective is the global empirical risk

$$F(\mathbf{w}) = \sum_{i=1}^{N} p_i F_i(\mathbf{w}), \qquad p_i = \frac{|\mathcal{D}_i|}{\sum_j |\mathcal{D}_j|}, \tag{1}$$

where $F_i$ is client $i$'s local empirical loss. In each round $t \in [T]$, the server selects a quorum $\mathcal{S}_t$ of size $K$; each selected client performs $E$ epochs of local stochastic gradient descent (SGD) from the global model $\mathbf{w}_t$ (learning rate $\eta$, batch size $B_{\mathrm{batch}}$) and returns its update

$$\Delta_i = \mathbf{w}_i - \mathbf{w}_t, \tag{2}$$

where $\mathbf{w}_i$ is the client's post-training local model. The unweighted baseline aggregate (FedAvg) is $\mathbf{w}_{t+1} = \mathbf{w}_t + \eta_g\sum_i p_i\Delta_i$ with global step size $\eta_g$, which a single Byzantine client can corrupt arbitrarily [B1].

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

Three assumptions bound the claims, stated honestly. (i) The root set $\mathcal{D}_r$ is representative: a compromised or stale root biases the reference direction itself; quarterly refresh mitigates but does not eliminate this, and root-set poisoning remains an open problem shared with all trust-bootstrapped defenses [B3]. (ii) The permissioned chain provides finality within one round — a 2 s block time on a 3-node Clique proof-of-authority (PoA) cluster suffices, as rounds last tens of seconds; a chain halt degrades the system to per-round gating without memory (Section 5.7). (iii) The SDN fabric can enforce per-device flow rules at the access layer (OpenFlow 1.3+), matching our emulation testbed. A compromised server cannot pair honest updates with fabricated evidence, because evidence is bound to content hashes on-chain and the ledger is publicly auditable.

# 3. Problem Formulation

Given the model of Section 2, the design objectives are fourfold:

**(O1) Convergence under poisoning.** Minimize Eq. (1) despite $\beta \le 0.4$ Byzantine clients: the aggregate must satisfy a descent guarantee of the form $\frac{1}{T}\sum_t \mathbb{E}\|\nabla F(\mathbf{w}_t)\|^2 \le \mathcal{O}(1/\sqrt{T}) + \mathcal{O}((\beta + \epsilon_r)\tau_c G)$, where $\epsilon_r$ is the residual malicious weight — *derived explicitly* from the gate and ledger parameters in Lemma 1 (Eq. 15) rather than assumed — and $G$ bounds honest update norms (Thm. 1; the bound is stated as Eq. (14) in Section 4.6).

**(O2) Bounded suppression.** A persistently malicious client must fall below the quarantine threshold $r_{\mathrm{q}}$ within $T_0$ rounds *independent of its history* (Prop. 1), so that intermittent adversaries cannot farm reputation.

**(O3) Utility-aware selection.** The quorum should maximize $\sum_{i\in\mathcal{S}_t} r_i u_i$ under a latency budget $B$ and per-client participation cost $c_i$, where $r_i$ is reputation and $u_i$ device utility — a 0–1 knapsack requiring an approximation (Prop. 2).

**(O4) Bounded containment.** The mean time from quarantine decision to network-level isolation must be separated from any cloud-roundtrip baseline (Thm. 2).

The challenge is that O1–O4 pull in different directions: O1 favors conservative aggregation, O2–O3 require persistent state that the untrusted server must not control, and O4 requires an executable actuation path. Our solution is to anchor all four in one on-chain trust root, constructed next.
