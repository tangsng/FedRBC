# Cover Letter

October 1, 2026

Dear Editor-in-Chief,

We are pleased to submit our manuscript entitled **"FedRBC: Blockchain-Enabled Reputation-Weighted Robust Federated Learning for Privacy-Preserving Healthcare IoT Edge Networks"** for consideration as a Research Article in *Computers, Materials & Continua* (CMC).

Hospital IoT devices are simultaneously the most valuable and the most vulnerable part of a medical network: a handful of compromised devices can poison the very intrusion-detection model that every device relies on, and most robust-federated-learning defenses either collapse under colluding adversaries or stop at detection without any enforceable containment. Our manuscript addresses this gap with FedRBC, a framework that closes the loop from robust aggregation to network-level quarantine. The key contributions are:

1. A reference-guided, reputation-weighted robust aggregation rule (RWRA) that neutralizes sign-flip, Sybil-collusion, and label-flip attacks within one mechanism, with adaptive magnitude clipping bounding norm attacks;
2. An on-chain reputation contract that makes per-client trust immutable, auditable, and directly consumable by both client selection and containment decisions, with proven geometric suppression of persistent adversaries;
3. An SDN-actuated containment path with a closed-form mean-time-to-containment (MTTC) analysis, measured on a containerized testbed;
4. A comprehensive evaluation over five seeds and two datasets (WUSTL-EHMS-2020 and CICIoT2023), in which FedRBC attains the highest F1 and AUC in every attack scenario with the smallest seed-to-seed variance, remains the only system above 0.5 F1 at a 40% Byzantine ratio, and reduces MTTC by 50–80% relative to a cloud-roundtrip baseline at sub-second per-round overhead.

We believe this work fits squarely within the scope of CMC's readership in secure, blockchain-enabled edge intelligence for healthcare IoT, and complements recent CMC publications on blockchain-SDN edge frameworks by providing theorem-level guarantees and an executable, reproducible evaluation.

**Declarations.** We confirm the following:

- This manuscript is original, has not been published previously (in whole or in part), and is not under consideration by any other journal.
- All authors have read and approved the final version of the manuscript and accept full responsibility for its delivery and content.
- All authors meet the authorship criteria of the ICMJE recommendations and have made substantial contributions to the work.
- There are no ethical, legal, or copyright issues associated with this work. The study does not involve human or animal subjects (Ethics Approval: Not applicable).
- The authors declare no conflicts of interest. The funders had no role in the design of the study; in the collection, analyses, or interpretation of data; in the writing of the manuscript; or in the decision to publish the results.
- We confirm our willingness to pay the Article Processing Charge (APC) if the manuscript is accepted for publication.
- The source code and raw data supporting the findings are openly available at https://github.com/tangsng/FedRBC.

**Suggested reviewers** (optional; no conflicts of interest with the authors):

*(To be completed by the corresponding author in the submission system, if required.)*

Thank you for your consideration. We look forward to the reviewers' feedback.

Sincerely,

Zhigang Jin, PhD
School of Electrical and Information Engineering, Tianjin University
No 92 Weijin Road, Nankai District, Tianjin 300072, China
E-mail: zgjin@tju.edu.cn
On behalf of all authors
