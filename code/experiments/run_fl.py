#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FedRBC 单次 FL 实验入口（argparse 全参数化）。
用法示例：
  python run_fl.py --method fedrbc --alpha 0.5 --beta 0.2 --attack label_flip --seed 42
输出：
  results/raw/<run_name>_rounds.csv   逐轮指标
  results/raw/<run_name>_summary.json 最终汇总（含配置回写，可复现）
  results/raw/<run_name>_rep.npy      声誉历史（仅 fedrbc）
"""
import os, sys, time, argparse
import numpy as np
import torch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from data.download import download, load_and_preprocess
from data.partition import dirichlet_partition
from models.mlp import MLPIDS
from algorithms.base import FLEngine
from algorithms.robust import agg_fedavg, agg_krum, agg_trimmed_mean, agg_fltrust
from algorithms.fedrbc import agg_fedrbc, evidence_scores
from algorithms.baselines_new import agg_raid, agg_fedgreed, agg_fedgt, agg_eiffel
from algorithms.reputation import ReputationLedger
from algorithms.selection import (gen_client_profiles, random_select, rep_aware_select)
from utils.common import set_seed, get_logger, save_json, CSVLogger
from utils.attack import (make_byzantine_set, apply_model_attacks,
                          make_backdoor_override, add_trigger, TRIG_IDX, TRIG_VAL)

METHODS = ["fedavg", "fedprox", "krum", "trimmed_mean", "fltrust", "fedrbc",
           "raid", "fedgt", "eiffel"]
# 模型层攻击（仿真威胁模型）：训练正常进行，update 在聚合前被篡改
MODEL_ATTACKS = ("scaling", "sign_flip", "sybil", "noise", "lie")

def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--method", choices=METHODS, default="fedrbc")
    ap.add_argument("--data-dir", default=os.path.join(os.path.dirname(__file__), "..", "..", "data"))
    ap.add_argument("--dataset", choices=["wustl", "ciciot"], default="wustl",
                    help="数据集：wustl=WUSTL-EHMS-2020，ciciot=CICIoT2023（第二数据集）")
    ap.add_argument("--out-dir", default=os.path.join(os.path.dirname(__file__), "..", "..", "results", "raw"))
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--n-clients", type=int, default=20)
    ap.add_argument("--k-per-round", type=int, default=10)
    ap.add_argument("--rounds", type=int, default=60)
    ap.add_argument("--local-epochs", type=int, default=2)
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--lr", type=float, default=0.05)
    ap.add_argument("--momentum", type=float, default=0.9)
    ap.add_argument("--eta-g", type=float, default=1.0)
    ap.add_argument("--prox-mu", type=float, default=0.1)
    ap.add_argument("--alpha", type=float, default=0.5, help="Dirichlet Non-IID 浓度")
    ap.add_argument("--beta", type=float, default=0.2, help="Byzantine 比例")
    ap.add_argument("--attack", choices=["none", "label_flip", "scaling", "sign_flip", "sybil", "noise",
                                          "lie", "backdoor"],
                    default="label_flip")
    ap.add_argument("--dp-sigma", type=float, default=0.0,
                    help="中心化 DP：聚合结果加 N(0, (sigma*C/sqrt(K))^2)，C=当轮 median delta 范数；0=关闭")
    ap.add_argument("--root-poison", type=float, default=0.0,
                    help="root set 被污染比例（标签翻转注入），模拟 root-set poisoning")
    ap.add_argument("--no-memory", dest="memory", action="store_false",
                    help="声誉每轮重置 r0（无跨轮记忆消融）")
    ap.add_argument("--root-size", type=int, default=500,
                    help="root 验证集规模（敏感性分析用）")
    ap.add_argument("--attack-gamma", type=float, default=5.0, help="scaling/sybil 幅度放大系数")
    ap.add_argument("--noise-sigma", type=float, default=1.0, help="noise 攻击范数倍数")
    # FedRBC 超参
    ap.add_argument("--tau-c", type=float, default=5.0, help="更新裁剪阈值（基础值）")
    ap.add_argument("--tau-c1", type=float, default=None,
                    help="时间退火目标值 tau_c1（默认 None=不启用旧改进 A）")
    ap.add_argument("--gate-p", type=float, default=1.0,
                    help="软门控幂次 p（1.0=ReLU）")
    ap.add_argument("--adaptive", action="store_true", default=False,
                    help="启用改进 D：声誉熵自适应门控")
    ap.add_argument("--tau-lo", type=float, default=2.0, help="自适应裁剪下界")
    ap.add_argument("--tau-hi", type=float, default=6.0, help="自适应裁剪上界")
    ap.add_argument("--p-lo", type=float, default=0.6, help="自适应门控幂下界")
    ap.add_argument("--p-hi", type=float, default=1.4, help="自适应门控幂上界")
    ap.add_argument("--root-align", action="store_true", default=False,
                    help="改进 E1：root-对齐范数归一化")
    ap.add_argument("--rep-gate-alpha", type=float, default=0.0,
                    help="改进 E2：声誉即时门控强度 (s'=s*r^alpha；0=关闭)")
    ap.add_argument("--tau-rel", type=float, default=None,
                    help="相对裁剪 κ：τ_c=κ·‖Δ_root‖（给出则覆盖固定 tau-c）")
    ap.add_argument("--z-thresh", type=float, default=None,
                    help="Layer-0 MAD 范数预过滤阈值（给出则启用，如 2.0）")
    ap.add_argument("--soft-T", type=float, default=None,
                    help="softmax 证据门控温度（给出则启用，如 0.3）")
    ap.add_argument("--soft-T-anneal", type=float, default=None,
                    help="温度退火目标值：训练后期 T_s 线性升至该值（如 2.0），缓解 no-attack 崩溃")
    ap.add_argument("--gamma", type=float, default=0.3, help="声誉更新步长")
    ap.add_argument("--kappa", type=float, default=2.0, help="惩罚加速因子")
    ap.add_argument("--lambda-dec", type=float, default=0.01, help="声誉时间衰减")
    ap.add_argument("--theta-h", type=float, default=0.3)
    ap.add_argument("--theta-m", type=float, default=0.0)
    # 评估阈值（默认固定 0.5；本地已用类别加权 CE 处理不平衡）
    ap.add_argument("--threshold", type=float, default=0.5,
                    help="决策阈值（默认 0.5）")
    # 消融开关
    ap.add_argument("--rep-weight", action="store_true", default=True)
    ap.add_argument("--no-rep-weight", dest="rep_weight", action="store_false")
    ap.add_argument("--selection", choices=["rep", "random"], default=None,
                    help="默认：fedrbc=rep，其余=random")
    ap.add_argument("--decay", action="store_true", default=True)
    ap.add_argument("--no-decay", dest="decay", action="store_false")
    ap.add_argument("--penalty", action="store_true", default=True)
    ap.add_argument("--no-penalty", dest="penalty", action="store_false")
    ap.add_argument("--budget", type=float, default=25.0, help="选择时延预算 B")
    ap.add_argument("--tag", default="")
    ap.add_argument("--gpu", type=int, default=0)
    return ap.parse_args()

def main():
    args = parse_args()
    os.environ["CUDA_VISIBLE_DEVICES"] = str(args.gpu)
    set_seed(args.seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    lg = get_logger("run_fl")

    selection = args.selection or ("rep" if args.method == "fedrbc" else "random")
    # 文件名含 dataset 前缀，避免 wustl 与 ciciot 同名互相覆盖
    ds_tag = "" if args.dataset == "wustl" else args.dataset + "_"
    run_name = "%s%s_a%s_b%s_%s_s%d%s" % (
        ds_tag, args.method, args.alpha, args.beta, args.attack, args.seed,
        ("_" + args.tag) if args.tag else "")
    lg.info("run=%s | device=%s | selection=%s" % (run_name, device, selection))

    # ---------- 数据 ----------
    if args.dataset == "ciciot":
        from data.download_ciciot import download as dl_cic, load_and_preprocess as lp_cic
        csv_path = dl_cic(os.path.abspath(args.data_dir))
        X_tr, y_tr, X_te, y_te, X_root, y_root, _, feat_dim = lp_cic(csv_path, seed=args.seed)
    else:
        csv_path = download(os.path.abspath(args.data_dir))
        X_tr, y_tr, X_te, y_te, X_root, y_root, _, feat_dim = load_and_preprocess(
            csv_path, root_size=args.root_size, seed=args.seed)
    parts = dirichlet_partition(y_tr, args.n_clients, alpha=args.alpha, seed=args.seed)
    X_parts = [X_tr[idx] for idx in parts]
    y_parts = [y_tr[idx] for idx in parts]
    data_weights = [len(idx) for idx in parts]

    # ---------- root-set poisoning（R2.3）：按比例翻转 root 集标签 ----------
    if args.root_poison > 0.0:
        rp_rng = np.random.default_rng(args.seed + 4242)
        n_poison = int(round(args.root_poison * len(y_root)))
        if n_poison > 0:
            pidx = rp_rng.choice(len(y_root), size=n_poison, replace=False)
            y_root = np.asarray(y_root).copy()
            y_root[pidx] = 1 - y_root[pidx]
            lg.info("root-set poisoned: %d/%d labels flipped (eps=%.0f%%)"
                    % (n_poison, len(y_root), 100 * args.root_poison))

    # ---------- 攻击 ----------
    is_model_attack = args.attack in MODEL_ATTACKS
    byz_set = make_byzantine_set(args.n_clients, args.beta, args.seed) if args.attack != "none" else set()
    lg.info("Byzantine clients (%d, attack=%s): %s" % (len(byz_set), args.attack, sorted(byz_set)))

    # ---------- 引擎与账本 ----------
    # 模型层攻击：训练正常（不传 byz_set 给引擎），update 在聚合前篡改；
    # 数据层攻击（label_flip / backdoor）：backdoor 通过 data_override 注入触发样本。
    is_bd = (args.attack == "backdoor")
    engine = FLEngine(lambda: MLPIDS(in_dim=feat_dim), X_parts, y_parts,
                      X_root, y_root, X_te, y_te, device,
                      byz_set=(set() if (is_model_attack or is_bd) else byz_set),
                      local_epochs=args.local_epochs,
                      batch=args.batch, lr=args.lr, momentum=args.momentum,
                      prox_mu=(args.prox_mu if args.method == "fedprox" else 0.0),
                      seed=args.seed)
    # backdoor：为每个恶意客户端预生成植入触发的本地数据（frac=0.3 样本 -> 攻击类）
    bd_data = {}
    if is_bd:
        for cid in byz_set:
            bd_data[cid] = make_backdoor_override(X_parts[cid], y_parts[cid],
                                                  np.random.default_rng(args.seed + cid),
                                                  frac=0.3)
    ledger = ReputationLedger(args.n_clients, gamma=args.gamma, kappa=args.kappa,
                              lambda_dec=(args.lambda_dec if args.decay else 0.0),
                              theta_h=args.theta_h,
                              theta_m=(args.theta_m if args.penalty else -2.0))
    profiles = gen_client_profiles(args.n_clients, args.seed)
    rng = np.random.default_rng(args.seed + 999)
    n_byz_round = int(round(args.beta * args.k_per_round))

    csv = CSVLogger(os.path.join(os.path.abspath(args.out_dir), run_name + "_rounds.csv"),
                    ["round", "acc", "f1", "auc", "loss_proxy", "round_sec"])
    t_start = time.time()
    best_f1, final = 0.0, {}
    for t in range(1, args.rounds + 1):
        t0 = time.time()
        # ---- 客户端选择（Eq. 13-14） ----
        if selection == "rep":
            sel = rep_aware_select(ledger.weights(), profiles["u"], profiles["c"],
                                   args.k_per_round, args.budget)
        else:
            sel = random_select(args.n_clients, args.k_per_round, rng)
        # ---- 本地训练（Eq. 4） ----
        if is_bd:
            deltas = torch.stack([engine.local_train(cid, data_override=bd_data[cid])
                                   if cid in byz_set else engine.local_train(cid)
                                   for cid in sel])
        else:
            deltas = torch.stack([engine.local_train(cid) for cid in sel])
        # ---- 模型层攻击注入（聚合前篡改恶意客户端 update） ----
        if is_model_attack and byz_set:
            byz_local = [j for j, cid in enumerate(sel) if cid in byz_set]
            deltas = apply_model_attacks(deltas, byz_local, args.attack, rng,
                                         gamma=args.attack_gamma,
                                         noise_sigma=args.noise_sigma)
        # ---- 聚合 ----
        if args.method in ("fedavg", "fedprox"):
            agg = agg_fedavg(deltas, [data_weights[i] for i in sel])
        elif args.method == "krum":
            agg = agg_krum(deltas, n_byz=n_byz_round)
        elif args.method == "trimmed_mean":
            agg = agg_trimmed_mean(deltas, trim_ratio=min(args.beta, 0.4))
        elif args.method == "fltrust":
            root_delta = engine.root_update()
            agg = agg_fltrust(deltas, root_delta)
        elif args.method == "raid":
            root_delta = engine.root_update()
            agg = agg_raid(deltas, None, [data_weights[i] for i in sel], root_delta=root_delta)
        elif args.method == "fedgt":
            root_delta = engine.root_update()
            agg = agg_fedgt(deltas, [data_weights[i] for i in sel], root_delta=root_delta)
        elif args.method == "eiffel":
            agg = agg_eiffel(deltas, trim_beta=min(max(args.beta, 0.1), 0.4))
        elif args.method == "fedrbc":
            root_delta = engine.root_update()
            agg, scores, violations = agg_fedrbc(deltas, root_delta,
                                     ledger.weights()[sel],
                                     [data_weights[i] for i in sel],
                                     tau_c=args.tau_c,
                                     use_rep_weight=args.rep_weight,
                                     gate_p=args.gate_p,
                                     round_idx=t,
                                     total_rounds=args.rounds,
                                     tau_c1=args.tau_c1,
                                     adaptive=args.adaptive,
                                     tau_lo=args.tau_lo, tau_hi=args.tau_hi,
                                     p_lo=args.p_lo, p_hi=args.p_hi,
                                     root_align=args.root_align,
                                     rep_gate_alpha=args.rep_gate_alpha,
                                     tau_rel=args.tau_rel,
                                     z_thresh=args.z_thresh,
                                     soft_T=args.soft_T,
                                     soft_T_anneal=args.soft_T_anneal)
            ledger.update(sel, scores, violations)  # Eq. 11-12（合约模拟，含违规分支）
            if not args.memory:
                ledger.reset()  # 无跨轮记忆消融：每轮重置回 r0
        # ---- 中心化 DP：聚合结果加高斯噪声（敏感度 S=C/K 的 sigma 倍） ----
        if args.dp_sigma > 0.0:
            C = deltas.norm(dim=1).median()
            agg = agg + torch.randn_like(agg) * (args.dp_sigma * C / float(deltas.size(0)) ** 0.5)
        engine.apply_update(agg, eta_g=args.eta_g)
        # ---- 评估 ----
        m = engine.evaluate(threshold=args.threshold)
        if is_bd:
            # ASR：benign 测试样本植入触发器后被预测为攻击类的比例
            with torch.no_grad():
                Xb = engine.X_te[engine.y_te == 0] if isinstance(engine.X_te, torch.Tensor) \
                    else torch.from_numpy(engine.X_te[engine.y_te == 0]).to(device)
                Xtr = Xb.clone().to(device)
                Xtr[:, list(TRIG_IDX)] = TRIG_VAL
                m["asr"] = float((engine.global_model(Xtr).argmax(dim=1) == 1).float().mean())
        best_f1 = max(best_f1, m["f1"])
        csv.log([t, "%.5f" % m["acc"], "%.5f" % m["f1"], "%.5f" % m["auc"], "", "%.2f" % (time.time() - t0)])
        if t % 10 == 0 or t == 1:
            lg.info("round %3d | acc=%.4f f1=%.4f auc=%.4f" % (t, m["acc"], m["f1"], m["auc"]))
        final = m

    # ---------- 落盘 ----------
    out_dir = os.path.abspath(args.out_dir)
    if args.method == "fedrbc":
        np.save(os.path.join(out_dir, run_name + "_rep.npy"), np.array(ledger.history))
    summary = dict(run_name=run_name, config=vars(args), byz_clients=sorted(byz_set),
                   final=final, best_f1=best_f1, wall_sec=time.time() - t_start,
                   selection=selection)
    save_json(summary, os.path.join(out_dir, run_name + "_summary.json"))
    lg.info("DONE %s | final f1=%.4f best f1=%.4f | %.1fs" %
            (run_name, final["f1"], best_f1, summary["wall_sec"]))

if __name__ == "__main__":
    main()
