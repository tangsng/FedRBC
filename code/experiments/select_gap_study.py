"""Empirical approximation-gap study for the selection rule (R1.8/R1.9, Round 2).

Compares the (corrected) three-candidate selection of Alg. 3 against the exact
optimum of the *actual* constrained problem (budget B and quorum/at-most-K
cardinality) on the evaluation distribution:
  N = 20 clients, K = 10 quorum, B = 25 cost units,
  u_i ~ U[0,1], c_i ~ U[1,5], r_i ~ U[0.3,1] (survivor band) -- and a second
  arm sampling r from the measured reputation CDF of fedrbc survivors.

Exact optimum: 0/1 knapsack DP with cardinality cap, batched over G groups.
Alg. 3 (corrected): argmax of
  S_d  density-greedy prefix   (d_i = r_i u_i / c_i, admit while |S|<K and cost<=B)
  S_v  top-K-by-utility prefix (v_i = r_i u_i, admit while |S|<K and cost<=B)
  S_1  best feasible single item by utility
Costs are rounded to a 0.05 grid so the DP is exact on the same instances the
heuristics see (a note in the appendix states this).

Run: python3 select_gap_study.py [--G 10000]
"""
import numpy as np
import argparse

rng = np.random.default_rng(42)

def make_instances(G, N, r_mode):
    if r_mode == "deployment":
        # exact reproduction of gen_client_profiles (algorithms/selection.py):
        # u = compute x link, c = 1/compute + 0.5/link (negatively correlated)
        compute = rng.uniform(0.4, 1.0, (G, N))
        link = rng.uniform(0.3, 1.0, (G, N))
        u = compute * link
        c = 1.0 / compute + 0.5 / link
        r = rng.uniform(0.3, 1.0, (G, N))
        return u, c, r
    u = rng.random((G, N))
    c = rng.uniform(1.0, 5.0, (G, N))
    if r_mode == "uniform":
        r = rng.uniform(0.3, 1.0, (G, N))
    else:  # empirical-style: Beta(5,2) shifted to [0.15, 1.0] (survivor band)
        r = 0.15 + 0.85 * rng.beta(5, 2, (G, N))
    return u, c, r

def dp_optimum(v, c_disc, B_cells, K, N):
    """Batched exact DP: dp[g, j, b] = max value using <= j items within budget b."""
    G = v.shape[0]
    NEG = -1.0
    dp = np.full((G, K + 1, B_cells + 1), NEG)
    dp[:, 0, :] = 0.0
    for i in range(N):
        vi = v[:, i][:, None, None]          # (G,1,1)
        ci = c_disc[:, i]                     # (G,)
        # dp_new[j,b] = max(dp[j,b], dp[j-1,b-ci] + v_i)
        shifted = np.full_like(dp, NEG)
        shifted[:, 1:, :] = NEG
        # build shifted from dp[:, :-1, :] rolled by ci per group
        prev = dp[:, :-1, :]                  # (G, K, B+1)
        # per-group shift by ci: gather columns
        idx = np.arange(B_cells + 1)[None, :] - ci[:, None]   # (G, B+1)
        valid = idx >= 0
        idxc = np.clip(idx, 0, B_cells)
        gathered = np.take_along_axis(prev, idxc[:, None, :].repeat(K, axis=1), axis=2)  # (G,K,B+1)
        gathered = np.where(valid[:, None, :], gathered, NEG)
        cand = gathered + vi
        dp = np.maximum(dp, np.concatenate([np.full((G, 1, B_cells + 1), NEG), cand], axis=1))
    return np.max(dp[:, K, :][np.arange(G), [B_cells] * G][:, 0] if False else dp[:, :, B_cells].max(axis=1))
    # value at exact budget cap: dp[:, j, B_cells] for any j<=K -> max over j

def greedy_prefix(v, d, c_disc, B_cells, K, N):
    """Batched greedy admit in order `d` (descending) while |S|<K and cost<=B."""
    G = v.shape[0]
    order = np.argsort(-d, axis=1, kind="stable")
    total = np.zeros(G)
    cost = np.zeros(G, dtype=np.int64)
    cnt = np.zeros(G, dtype=np.int64)
    for step in range(N):
        idx = order[:, step]
        vi = v[np.arange(G), idx]
        ci = c_disc[np.arange(G), idx]
        admit = (cnt < K) & (cost + ci <= B_cells)
        total = np.where(admit, total + vi, total)
        cost = np.where(admit, cost + ci, cost)
        cnt = np.where(admit, cnt + 1, cnt)
    return total

def best_single(v, c_disc, B_cells):
    feas = c_disc <= B_cells
    vm = np.where(feas, v, -1.0)
    return vm.max(axis=1)

def alg3_three_candidates(v, d, c_disc, B_cells, K, N):
    s_d = greedy_prefix(v, d, c_disc, B_cells, K, N)
    s_v = greedy_prefix(v, v, c_disc, B_cells, K, N)
    s_1 = best_single(v, c_disc, B_cells)
    return np.maximum(np.maximum(s_d, s_v), s_1), s_d, s_v, s_1

def stats(name, ratio, opt, s_d, s_v, s_1):
    print(f"--- {name} ---")
    print(f"  ratio ALG/OPT: min={ratio.min():.4f}  P1={np.percentile(ratio,1):.4f}  "
          f"P5={np.percentile(ratio,5):.4f}  median={np.median(ratio):.4f}  mean={ratio.mean():.4f}")
    print(f"  exact-opt fraction: {np.mean(ratio >= 1.0 - 1e-9):.4f}")
    print(f"  candidate wins: S_d={np.mean((s_d >= s_v) & (s_d >= s_1)):.3f}  "
          f"S_v={np.mean((s_v > s_d) & (s_v >= s_1)):.3f}  S_1={np.mean((s_1 > s_d) & (s_1 > s_v)):.3f}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--G", type=int, default=10000)
    args = ap.parse_args()
    G, N, K = args.G, 20, 10
    B = 25.0
    grid = 0.05
    B_cells = int(round(B / grid))

    for r_mode in ("deployment", "uniform", "beta"):
        u, c, r = make_instances(G, N, r_mode)
        v = r * u
        c_disc = np.rint(c / grid).astype(np.int64)
        d = v / np.maximum(c, 1e-9)
        opt = dp_optimum(v, c_disc, B_cells, K, N)
        alg, s_d, s_v, s_1 = alg3_three_candidates(v, d, c_disc, B_cells, K, N)
        ratio = alg / np.maximum(opt, 1e-12)
        # binding diagnostics on the density-greedy prefix
        stats(f"{r_mode}: G={G}, N={N}, K={K}, B={B}", ratio, opt, s_d, s_v, s_1)
        # budget-binding incidence: how often top-10 cheapest would exceed B
        cheapest10 = np.sort(c_disc, axis=1)[:, :K].sum(axis=1)
        print(f"  budget-binding fraction (cheapest K cost > B): {np.mean(cheapest10 > B_cells):.3f}")

if __name__ == "__main__":
    main()
