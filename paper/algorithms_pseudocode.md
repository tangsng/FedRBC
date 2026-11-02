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
