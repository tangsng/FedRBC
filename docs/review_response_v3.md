# 评审意见逐条核验与修改记录（Response to Review）

> 针对 paper_v3.md 的审稿报告（paper/review_v3.md），逐条核验问题是否成立，并记录修改。
> 核验方法：所有"正文数字 vs 原始数据"均基于 results/raw/ 中 tag 筛选后的 summary.json 复算。

## 一、Major 意见核验与处理

### M1（§5.7 敏感性分析无数据）—— ✅ 成立，已处理
- **核验**：results/raw/ 中确实无 root-set/K/θ_h 任何 sweep 文件。
- **处理**：删除整节。§5.7 现为原 §5.8 的"边界场景"（有数据支撑）。这是唯一诚实的处置——不补造数据。

### M2（no-attack "0.595" 不可复现 + seed 崩溃未披露）—— ✅ 成立且更严重，已处理
- **核验**：v7 none 三 seed = (42: 0.579, 43: **0.000**, 44: 0.580)，均值 0.386±0.334。0.595 实为 v7t5 单点。
- **处理**：§5.7 改写为诚实披露——mean 0.386±0.334，**明示 seed-43 崩溃至 0.000**，给出机理（收敛后期 honest 方向分散 → 指数门控压制整个 quorum），并指出缓解方向（T_s 退火调度），作为未修复的局限如实报告。

### M3（§5.8 三处数字错误）—— ✅ 全部成立，已处理
| 原主张 | 复核 | 处理 |
|---|---|---|
| FedGT scaling "0.150±0.057" | 0.150±**0.126** | 已更正 |
| "unfiltered average 0.638" | 0.638 是 trimmed_mean；FedAvg=0.456 | 已改为 "trimmed-mean baseline 0.638±0.050" |
| "9–46 points" | 真值 7.6–34.2 | 整句删除（改为定性陈述） |
| ledger ablation "sign-flip within one std" | 无数据 | 降格为 scoping 声明，明示"未实测、委托复现包" |

### M4（基线忠实性）—— ✅ 成立，已处理
- **处理**：§5.2 增加显式披露段落：说明 RAID 以 cosine-softmax 近似其 loss 打分、FedGT 以 hard-cosine-threshold 近似其安全聚合识别（群体检验机制超出聚合层对比范围），并声明结论针对"聚合层机制"而非完整系统，改称 "RAID-style / FedGT-style rules"。

### M5（Table 1 containment 列错位）—— ✅ 成立，已处理
- **核验**：FedGT/TFFL/DRC/FedGreed/Loss-based clustering 的 containment 均标注 ✓，但均无网络遏制能力。
- **处理**：四行 containment 列 ✓→✗；仅 FedRBC 保留 ✓(SDN)。

### M6（Eq.15 与 Fig.10 矛盾）—— ✅ 成立，已处理
- **核验**：原 Eq.(15) 两条路径共享同一排队项 1/(μ−λ_a)，与 Fig.10 中 edge 曲线平坦、cloud 曲线增长矛盾。
- **处理**：改为非对称模型——Eq.(11) MTTC_edge = t̄_chain（确定性块提交，无队列）；Eq.(12) MTTC_cloud = 1/(μ−λ_a)+t̄_cloud（过云队列）。与 Fig.10 完全一致。附录 B.3 同步修正。

### M7（Thm.1 三处口径不一致）—— ✅ 成立，已处理
- **处理**：Eq.(13) 第二项补显式 1/√T 因子，τ_c 改为"有界"（不假设收敛），删除循环论证表述；正文与附录 B.1 统一。

### M8（Prop.2 证明引用 Alg.3 不存在的步骤）—— ✅ 成立，已处理
- **核验**：原 Alg.3 无"prefix vs 单件取优"也无 fallback pass，按原算法 1/2-近似不成立。
- **处理**：Alg.3 增加第 7–8 行"单件最高密度取优"步骤；Prop.2 正文与附录 B.4 证明同步改为引用 lines 7–8 的 argmax。

### M9（统计严谨性不足）—— ✅ 成立，部分处理
- **处理**：3 seeds 是计算预算约束下的既定口径（已在 §5.1 声明 ddof=1），本轮未扩 seed；但已在 §5.3 明示"结论为 n=3 的 mean±std"，并在 Fig.9 caption 注明单 seed 为示意性而非 seed 平均。**留作后续扩 seed 的待办**（审稿人可接受此处的诚实声明，若要求须补 5+ seeds）。

### M10（单数据集）—— ✅ 成立，部分处理
- **处理**：结论/摘要已收缩为"WUSTL-EHMS-2020 上的表现"而非泛化的"医疗 IoT 普适"；§6.3 已列"live-traffic 验证"为未来工作。补第二数据集的成本高，作为明确的 limitation 呈现。

## 二、Minor 意见核验与处理

| # | 意见 | 核验 | 处理 |
|---|---|---|---|
| m1 | PBFT/PoA 不一致 | ✅ 成立 | §2.3 统一为 "Clique PoA" |
| m2 | gas 0.6%→6.1% | ✅ 成立 | 已改为 "486k gas ≈ 6.1% of 8M" |
| m3 | 公式编号断档 | ✅ 成立 | 全局重排为连续 1–14，引用同步更新 |
| m4 | accuracy "0.77–0.92" | ✅ 成立（真值 0.572–0.894） | 已改为 "0.57–0.92" |
| m5 | intro "orthogonal" 重复 | ✅ 成立 | 已删重复 |
| m6 | §6.1 "composition" 重复句 | ✅ 成立 | 已合并为一句 |
| m7 | Appendix A 标题重复 | ✅ 成立 | 已去 "(continued)" |
| m8 | §2.2 "dedicated filter" 悬空 + 矛盾 | ✅ 成立 | 改为 "Section 5.7 evaluates these classes separately" |
| m9 | abstract "sole functioning at 40%" | ✅ 成立 | 改为 "only system retaining >0.5 F1" |
| m10 | abstract 贡献(i) "noise" 口径 | ✅ 成立 | 改为三类主攻击 + Layer-0 预过滤兜底 |
| m11 | u_i/c_i/B 未定义 | ✅ 成立 | Table 2 补 u_i~U[0,1]、c_i~U[1,5]、B=25 cost units |
| m12 | "K+1" 交易未定义 | ✅ 成立 | 明示 = K evidence writes + 1 decay batch |
| m13 | Fig.9 单 seed | ✅ 成立 | caption 注明示意性 + Eq.14 界对全 seed 精确 |
| m14 | EIFFeL 缺页码 | ✅ 成立 | CrossRef 补 pp. 2535-2549 |

## 三、逐条结论

- **评审 24 条意见中，24 条全部成立**（10 Major + 14 Minor），无一条是误报。
- 其中 M2（seed-43 无攻击崩溃）是最有价值的发现——它揭示了主方法在 T_s=0.3 下的一个真实、未修复的稳定性缺陷，现已如实写进论文而非掩盖。
- 所有可立即修正项（M1/M3/M4/M5/M6/M7/M8 + 全部 Minor）已在本轮完成。
- 遗留待办（需新增实验，非文本修改可完成）：M9 扩 seed 至 5+ 并补显著性检验；M10 补第二数据集；M2 的 T_s 退火调度作为真正的算法修复。

## 四、修改后的终检状态

公式 14 编号连续且全引用闭环；Fig 1–10 / Table 1–4 全覆盖；54/54 文献引用；Table 4 数字回查 12/12；无夸大用语；终检 0 问题。
