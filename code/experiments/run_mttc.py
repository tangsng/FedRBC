#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTTC 闭环遏制延迟 emulation（§5.5, Eq. 15-18, Thm 2 验证）。
对比边缘本地验证路径 vs 云端重复验证路径（基准论文方案）的平均遏制时间。
参数标注来源；输出 CSV 供 Fig 7。
"""
import os, argparse
import numpy as np
import pandas as pd

def mttc_edge(D_detect, k, T_b, D_sdn, D_edge_verify):
    """Eq. 15：边缘本地验证 + 链上确认 + SDN 规则下发。"""
    return D_detect + D_edge_verify + k * T_b + D_sdn

def mttc_cloud(D_detect, k, T_b, D_sdn, D_net, mu_c, lam):
    """Eq. 16-17：云端排队验证（M/M/1）。lam -> mu_c 时发散。"""
    rho = lam / mu_c
    if rho >= 1.0:
        return np.inf, rho
    D_verify = 1.0 / (mu_c - lam)          # Eq. 17（时间单位归一化为秒需乘尺度，见下）
    return D_detect + 2 * D_net + D_verify + k * T_b + D_sdn, rho

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(os.path.dirname(__file__), "..", "..", "results", "raw", "mttc.csv"))
    # 参数（任意一致时间单位；取值依据见论文 §6.6：文献与典型测量范围）
    ap.add_argument("--D-detect", type=float, default=0.8)
    ap.add_argument("--D-edge-verify", type=float, default=0.2)
    ap.add_argument("--D-net", type=float, default=1.5, help="边缘-云单向时延")
    ap.add_argument("--D-sdn", type=float, default=0.3, help="ONOS 规则下发时延")
    ap.add_argument("--k", type=int, default=2, help="确认区块数")
    ap.add_argument("--T-b", type=float, default=1.0, help="出块间隔")
    ap.add_argument("--mu-c", type=float, default=2.0, help="云验证服务率")
    args = ap.parse_args()

    rows = []
    for lam in np.linspace(0.2, 1.9, 18):
        e = mttc_edge(args.D_detect, args.k, args.T_b, args.D_sdn, args.D_edge_verify)
        c, rho = mttc_cloud(args.D_detect, args.k, args.T_b, args.D_sdn,
                            args.D_net, args.mu_c, lam)
        rows.append(dict(lambda_a=round(lam, 3), rho=round(rho, 3),
                         mttc_edge=e, mttc_cloud=c,
                         delta=(c - e) if np.isfinite(c) else np.nan))
    df = pd.DataFrame(rows)
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    df.to_csv(args.out, index=False)
    print(df.to_string(index=False))
    print("[mttc] 已写出 %s" % os.path.abspath(args.out))

if __name__ == "__main__":
    main()
