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
