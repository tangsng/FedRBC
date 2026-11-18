"""Cross-validation: brute-force enumeration vs DP vs Alg.3 on small instances.
If DP matches enumeration and Alg.3 matches hand-computed greedy, the large-scale
results are trustworthy. Also prints the winner structure to understand the gap.
"""
import numpy as np
from itertools import combinations

rng = np.random.default_rng(7)

def brute_opt(v, c, B, K, N):
    best = 0.0
    for k in range(0, K + 1):
        for comb in combinations(range(N), k):
            if sum(c[i] for i in comb) <= B + 1e-9:
                s = sum(v[i] for i in comb)
                if s > best:
                    best = s
    return best

def dp_opt_single(v, c_disc, B_cells, K, N):
    NEG = -1.0
    dp = np.full((K + 1, B_cells + 1), NEG)
    dp[0, :] = 0.0
    for i in range(N):
        vi, ci = v[i], c_disc[i]
        prev = dp[:-1, :]  # j-1 layer
        shifted = np.full((K, B_cells + 1), NEG)
        idx = np.arange(B_cells + 1) - ci
        valid = idx >= 0
        shifted[:, valid] = prev[:, idx[valid]]
        cand = shifted + vi
        dp[1:, :] = np.maximum(dp[1:, :], cand)
    return float(dp[:, B_cells].max())

def alg3_single(v, c_disc, d_order_v, d_order_d, B_cells, K, N):
    def greedy(order):
        tot, cost, cnt = 0.0, 0, 0
        for i in order:
            if cnt == K:
                break
            if cost + c_disc[i] <= B_cells:
                tot += v[i]; cost += c_disc[i]; cnt += 1
        return tot
    s_d = greedy(d_order_d)
    s_v = greedy(d_order_v)
    s_1 = max([v[i] for i in range(N) if c_disc[i] <= B_cells] + [0.0])
    return max(s_d, s_v, s_1), s_d, s_v, s_1

def main():
    grid = 0.05
    mismatches_dp, mismatches_a3 = 0, 0
    ratios = []
    for trial in range(300):
        N, K, B = 14, 5, 15.0
        u = rng.random(N)
        c = rng.uniform(1.0, 5.0, N)
        r = rng.uniform(0.3, 1.0, N)
        v = r * u
        B_cells = int(round(B / grid))
        c_disc = np.rint(c / grid).astype(int)
        opt_bf = brute_opt(v, c, B, K, N)          # exact costs
        opt_dp = dp_opt_single(v, c_disc, B_cells, K, N)  # rounded costs
        # compare on the same rounding: brute force with rounded costs
        c_r = c_disc * grid
        opt_bf_r = brute_opt(v, c_r, B, K, N)
        if abs(opt_dp - opt_bf_r) > 1e-6:
            mismatches_dp += 1
            if mismatches_dp <= 2:
                print("DP mismatch trial", trial, "dp=", opt_dp, "bf=", opt_bf_r)
        order_d = list(np.argsort(-v / np.maximum(c, 1e-9), kind="stable"))
        order_v = list(np.argsort(-v, kind="stable"))
        a3, s_d, s_v, s_1 = alg3_single(v, c_disc, order_v, order_d, B_cells, K, N)
        # manual check greedy for first trial
        if trial == 0:
            print("trial0: v=", np.round(v, 3), "c_disc=", c_disc)
            print("  s_d=", round(s_d, 4), " s_v=", round(s_v, 4), " s_1=", round(s_1, 4),
                  " opt=", round(opt_dp, 4))
        if opt_bf_r > 0:
            ratios.append(a3 / opt_bf_r)
    ratios = np.array(ratios)
    print(f"DP vs brute mismatches: {mismatches_dp}/300")
    print(f"small-scale ratio: min={ratios.min():.3f} median={np.median(ratios):.3f} mean={ratios.mean():.3f}")

if __name__ == "__main__":
    main()
