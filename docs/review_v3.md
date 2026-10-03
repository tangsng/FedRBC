# Peer Review Report — paper_v3.md (FedRBC, 投稿 CMC)

> 评审人核对记录（审稿证据底稿）：所有“正文数字 vs 原始数据”复核均基于 results/raw/ 中 tag 筛选后的 summary.json（fedrbc=v7, 基线=bl, n=3 seeds, ddof=1）。本报告同时保存于 paper/review_v3.md。

## 推荐意见：Major Revision（大修）

---

## 一、总体评价

**优点（值得肯定）：**
- 研究问题真实且有价值：鲁棒聚合的"检测无执行、信任无记忆"两大空档定位准确，闭环遏制叙事完整；
- 方法链路清晰：Eq.(5)(7)(8) 三层机制与威胁模型 §2.2 逐类对齐，Table 3 → Table 4 的"覆盖矩阵预测结果表"论证结构好；
- 主表（Table 4）12 组数字经复核**全部与原始数据一致**（±0.001 内）；
- EIFFeL sybil 的 AUC=nan 如实标注 collapse，FedGT 大方差如实呈现（0.333/0.360/0.352），α=0.1 全系统崩溃如实披露——结果呈现的诚实度总体较高；
- β=10%（FedGT 0.581 > 0.570）与 α=1.0（0.392 > 0.380）两处不利点未隐瞒。

**致命缺陷：** §5.7 与 §5.8 的消融/敏感性数字**在提供的实验产物中无任何原始数据支撑**，且 §5.8 多处数字与原始数据**不符**（详见 Major 1–3）。此外主方法在无攻击场景存在未被披露的 seed 级崩溃（Major 2）。

---

## 二、Major Issues（必须解决）

### M1.（最严重）§5.7 敏感性分析整节无数据支撑
位置：§5.7 全节（root-set sweep 0.578→0.55→0.49；K sweep "K=6 丢 4 分、K=14 丢 2 分"；θ_h sweep "轨迹不可区分"）。
性质：**结果类数字无出处**。results/raw/ 中不存在任何 root-set-size / K / θ_h 的 sweep 配置文件。§5.1 声称"one script reproduces every figure and table of this section"，与事实矛盾。
要求：补跑三组 sweep 并给出图表，或整节删除。在数据补齐前，该节构成不可复现的主张。

### M2.（最严重）§5.8 "no-attack tax" 数字错误，且掩盖了主方法的不稳定性
位置：§5.8 "FedRBC's F1 is 0.595 against 0.639 for FedGT"。
复核结果：**0.595 不可复现**。原始数据（fedrbc tag=v7, none, 3 seeds）= **0.386±0.334**，其中 **seed 43 崩溃至 F1=0.000**。0.595 实为另一配置（v7t5, T_s=0.5）seed 42 的单点值。
性质：(a) 数据错误/配置错引；(b) **未披露主配置（T_s=0.3）在无攻击时 1/3 seed 训练崩溃**——这与 §4.3 "skewed-but-benign update retains an O(1) weight" 的稳定性主张直接冲突，必须解释（怀疑与证据加权 exp(s/0.3) 在收敛后期 honest 方向分散时过度压制有关）并给出修复或如实报告。
要求：重报 no-attack 三 seed 完整结果（含崩溃），分析崩溃机理；全文所有引用 0.595 处更正。

### M3. §5.8 其余三处数字与原始数据不符
| 正文主张 | 复核值 | 性质 |
|---|---|---|
| FedGT scaling "0.150±**0.057**" | 0.150±**0.126** | std 错误 |
| "0.638 for an **unfiltered average**" | 0.638 是 **trimmed_mean**；FedAvg 实为 0.456±0.379（且 seed 43 崩溃 0.000） | 方法名错标，且掩盖了 FedAvg 也不稳定的事实 |
| "4-point premium buys **9–46 points**" | Table 4 对最强基线差距为 8.8–34.2（对 EIFFeL 崩溃为 57.8），无任何口径得 46 | 区间数字无出处（疑似旧基线残留） |
| §5.8 ledger ablation "sign-flip accuracy within one std" | **无任何原始数据** | 无出处主张 |

### M4. 基线"忠实性"存疑（对比公平性）
位置：§5.2。
问题：(a) 论文称 FedGT 为 "malicious-client identification with secure aggregation"，但其真实机制（群体检验/哈明距离/抗 dropout 设计，见其 TIFS 原文）与本文实现的"cos≥0 硬阈值"相去甚远——这实际是一个 **hard-cosine-filter strawman**，却以 FedGT 之名报告；(b) RAID 以 cosine-softmax 近似其 loss 改善打分，文中有一句脚注式说明但不够醒目；(c) 全部基线为作者自行"简化重实现"，未与原作者代码对齐验证。
要求：§5.2 明确披露"简化重实现，机制以 X 近似原文的 Y"，并讨论近似可能引入的偏差；或改称 "FedGT-style hard identification"。否则 Table 4 对 FedGT 的结论（"brittle"）可能部分来自实现而非原方法。

### M5. Table 1 覆盖标记错位（事实错误）
位置：Table 1。
复核：FedGT 行标注 Network containment=✓、Evaluation vs model-layer attacks=✗——**两者均与事实相反**（FedGT 无网络遏制，但其正是针对 model-layer Byzantine 攻击的评估）。TFFL/DRC、FedGreed、Loss-based clustering 三行的 containment=✓ 同样可疑（这些方法均无 SDN/网络遏制能力）。✓/✗ 疑似列错位。
要求：逐行逐列重核 Table 1。

### M6. Eq.(15) 与 Fig.10 矛盾
位置：§4.5 / Fig.10。
问题：Eq.(15) 中 edge 与 cloud 共享同一排队项 1/(μ−λ_a)，意味着两条曲线应随 ρ 同步增长；但 Fig.10 中 edge 曲线全程平坦（≈3.3 s），说明 edge 路径并未经过该 M/M/1 队列——与公式直接矛盾。
要求：或修模型（edge 路径的到达/服务率不同、或链上路径无排队），或修图，并解释 3.3 s 平坦值的构成。

### M7. Thm.1 陈述与证明不一致
位置：§4.6 vs Appendix B.1。
问题：Eq.(17) 第二项 O((β+ε̄_r)τ_c G) **不含 1/√T**，正文却称其"vanishes as τ_c contracts"；B.1 证明又给出 O((β+ε̄_r)τ_c G/√T)。三处口径互相矛盾。另：τ_c→0 依赖 ‖Δ_root‖→0 的收敛性，本身依赖待证结论，存在循环论证风险。
要求：统一为带 √T 的显式常数形式（即 B.1 的式子），并补充 τ_c(t) 收缩的独立论证或改为假设。

### M8. Prop.2 证明引用了 Alg.3 中不存在的步骤
位置：Appendix B.4 vs Alg.3。
问题：证明称 "taking the better of the two (Alg. 3 takes the maximal prefix...)" 且提及 "fallback pass"——Alg.3 既无"prefix vs 单件取优"步骤，也无 fallback pass。按所列算法，1/2-近似不成立（反例：单件密度最高但 prefix 提前被 K 截断）。
要求：修改 Alg.3 加入取优步骤，或弱化命题。

### M9. 统计严谨性不足
问题：全程仅 3 seeds、无任何显著性检验（无 paired t / Wilcoxon / 置信区间检验）；多处结论（如 "variance is the smallest"）建立在 n=3 的 std 上。
要求：至少对 Table 4 主结论补配对检验或多 seed（≥5）；对 0.000±0.000 与崩溃 seed 的极端情形改用非参数口径。

### M10. 数据集与模型单一
问题：仅 WUSTL-EHMS-2020（16,318 flows）+ 单一 2 层 MLP 支撑全部结论；TON_IoT/CICIoT2023 已引却未用。对医疗 IoT 的普适主张（abstract/conclusion）超出单数据集证据范围。
要求：至少补一个数据集或一种更深模型；或收缩结论表述。

---

## 三、Minor Issues

| # | 位置 | 问题 |
|---|---|---|
| m1 | §2.3 vs §5.1 | "3-node **PBFT**" vs "3-node **PoA**" 术语不一致（Clique PoA ≠ PBFT） |
| m2 | §4.1/§5.6 | gas 算术：48.6k×10=486k≈**6.1%** of 8M，正文写 "0.6% of a block for the full K=10 writes"（混淆单次与整轮） |
| m3 | 全文 | 公式编号不连续：1,4,5,6,7,8,9,11,12,13,15,17,20（缺 2,3,10,14,16,18,19,21） |
| m4 | §5.3 | "accuracy nearly flat (0.77–**0.92**)" 与 Table 4 矛盾：EIFFeL label-flip Acc=**0.572**、FedGT=0.645 |
| m5 | §1.2 | "yet robustness remains orthogonal to it: these systems ... treat robustness as orthogonal to the ledger" —— "orthogonal" 重复，编辑残留 |
| m6 | §6.1 | "FedRBC's advantage is the composition..." 连续出现两次（编辑残留） |
| m7 | Appendix A | 标题重复（"# Appendix A. Algorithms" + "(continued)"） |
| m8 | §2.2 | "statistically indistinguishable from a dedicated filter" —— dedicated filter(DGF) 已删稿，交叉引用悬空；且 §5.8 新数字（0.603 vs 0.150）恰证明"差异巨大"，叙述自相矛盾 |
| m9 | Abstract | "sole functioning system at a 40% Byzantine ratio" 与 §5.4 的 FedGT 0.393 不完全相符（0.393 非全崩），建议改 "the only system retaining >0.5" |
| m10 | Abstract/贡献(i) | 贡献(i) 称 "defeating magnitude, direction, collusion, **and noise**"，而评估主口径为三类（noise 仅 §5.8 边界讨论），口径不一 |
| m11 | Table 2 | u_i、c_i 的生成方式未给（selection 可复现性缺口）；budget B=25 的单位未定义 |
| m12 | §5.6 | "K+1 transactions per round" 的 "+1"（decay batch?）未在前文定义 |
| m13 | Fig.9 | 单 seed 轨迹用于支持 Prop.1 的"经验吻合"，建议叠 ≥3 seeds 或注明局限 |
| m14 | [22] EIFFeL | 文献条目缺页码（仅 DOI），建议补全 |

---

## 四、正文结果数字逐项核对表（非表格数字）

| 正文位置 | 主张 | 复核 | 结论 |
|---|---|---|---|
| §5.3 | 0.604/0.885, 0.578/0.889, 0.505/0.837 及各基线值 | 与 raw 一致 | ✅ |
| §5.3 | FedGT 方差 0.33–0.36 | 0.333/0.360/0.352 | ✅ |
| §5.3 | 3.6% (e^{-1/0.3}) | 0.0357 | ✅ |
| §5.4 | β 扫描 0.570/0.580/0.578/0.535；FedGT 0.581/0.074/0.393 | 一致 | ✅ |
| §5.4 | α=0.5: 0.578 vs 0.236；α=1.0: 0.392 vs 0.380；α=0.1 全≤0.02 | 一致（0.017/0.000/0.000/0.000） | ✅ |
| §5.6 | 开销 0.77/0.77/0.71/0.76 s | 一致 | ✅ |
| §5.8 | FedRBC scaling 0.603±0.068 | 一致 | ✅ |
| §5.8 | FedGT scaling 0.150±0.057 | 0.150±**0.126** | ❌ std 错 |
| §5.8 | FedGT noise 0.518 / FedRBC noise 0.565 | 一致 | ✅ |
| §5.8 | FedRBC none **0.595** | v7 实为 **0.386±0.334（含 0.000 崩溃）** | ❌❌ 严重 |
| §5.8 | FedGT none 0.639 | 一致 | ✅ |
| §5.8 | "unfiltered average 0.638" | 0.638=trimmed_mean；FedAvg=0.456 | ❌ 错标 |
| §5.8 | "9–46 points" | 无口径可得 46 | ❌ 无出处 |
| §5.7 | 三组 sweep 全部数字 | **无 raw 数据** | ❌❌ 无出处 |
| §5.8 | ledger ablation | **无 raw 数据** | ❌ 无出处 |
| §6.2 | "up to 14 F1 points"（软门控劣化） | 仅开发日志，无 raw | ⚠️ 建议补数据或降格为定性陈述 |
| §4.4/B.2 | T_0=2（⌈ln0.3/ln0.4⌉=2） | 1.315→2 | ✅ |

---

## 五、结论

方法与主表实验质量尚可、诚实度总体较高，但 §5.7/§5.8 存在**无数据支撑的整段主张**与**错误数字**，且暴露出主方法无攻击场景的未披露不稳定（seed 级崩溃）。上述问题触及相关主张的可信性，须大修：补齐 M1–M3 数据并更正全部错误数字、澄清 M4–M8 的模型/算法/证明矛盾、按 M9–M10 增强统计与数据集，再行复审。
