# FedRBC: Blockchain-Enabled Reputation-Weighted Robust Federated Learning for Healthcare IoT Edge Networks

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![PyTorch](https://img.shields.io/badge/PyTorch-1.10%2B-orange)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-Submitted%20to%20CMC-blueviolet)

Official implementation of **FedRBC**, a framework that closes the loop from *robust aggregation* to *network-level containment* against model-poisoning attacks in healthcare IoT (IoMT) federated learning.

FedRBC couples three co-designed components:

1. **Reference-guided robust aggregation (RWRA)** — root-set directional gating (softmax evidence) + adaptive relative clipping + MAD Layer-0 pre-filter.
2. **On-chain reputation ledger** — a smart contract that makes per-client trust immutable, auditable, and persistent across rounds (reward / penalty / grey-zone / temporal decay).
3. **SDN-actuated containment** — ONOS quarantine of devices whose on-chain reputation crosses a threshold, with a closed-form mean-time-to-containment (MTTC) separation over a cloud-roundtrip baseline.

---

## Repository structure

```
.
├── code/                      # Source code
│   ├── algorithms/            # Core methods
│   │   ├── fedrbc.py          # FedRBC aggregation (RWRA, Eq. 3-7)
│   │   ├── reputation.py      # On-chain reputation update (Alg. 2, Eq. 8-9)
│   │   ├── selection.py       # Reputation-aware client selection (Alg. 3, Eq. 11)
│   │   ├── baselines_new.py   # RAID / FedGT / EIFFeL / FedGreed baselines
│   │   ├── robust.py          # Classical robust aggregators (Krum, trimmed mean, ...)
│   │   └── base.py            # FL engine (local SGD, evaluation, NaN guard)
│   ├── data/                  # Dataset download + partitioning
│   │   ├── download.py        # WUSTL-EHMS-2020
│   │   ├── download_ciciot.py # CICIoT2023 (partition 0)
│   │   └── partition.py       # Dirichlet non-IID partitioning
│   ├── experiments/           # Runners, statistics, paper builders
│   │   ├── run_fl.py          # Single experiment entry point
│   │   ├── run_v5.py          # Full main table (5 seeds) + no-attack
│   │   ├── run_sweep_v5.py    # Byzantine-ratio & non-IID sweeps
│   │   ├── run_mttc.py        # MTTC queueing emulation
│   │   ├── stat_test.py       # Paired t-tests / effect sizes
│   │   ├── plots_sim.py       # Result figures (Fig 4-9) + tables
│   │   ├── build_paper_v3.py  # Assemble Markdown manuscript
│   │   ├── build_cmc_latex.py # Generate CMC (Tech Science Press) LaTeX
│   │   └── final_check_v3.py  # Consistency audit of the manuscript
│   └── utils/
│       └── fig_architecture.py# Architecture / sequence diagrams (Fig 1-3)
├── data/
│   └── README.md              # Dataset descriptions + download links
├── results/
│   ├── raw/                   # Raw per-run results (JSON / CSV / NPY)
│   ├── rev1/                  # Extracted revision statistics (CSV + report)
│   └── tables/                # Aggregated result tables (CSV / LaTeX)
├── requirements.txt
├── CITATION.cff
├── LICENSE
└── README.md
```

---

## Datasets

Both datasets are publicly available. **They are not redistributed in this repository** — use the automatic downloaders or the links below.

| Dataset | Role | Size | Download |
|---|---|---|---|
| **WUSTL-EHMS-2020** | Primary benchmark (healthcare IoT, MITM attacks) | 3.8 MB, 16,318 flows | <https://www.cse.wustl.edu/~jain/ehms/index.html> |
| **CICIoT2023** | Second dataset for cross-dataset generalization | ~70 MB (partition 0, 238,687 flows) | <https://media.githubusercontent.com/media/val-co/CIC-IoT-2023-Dataset/master/part-00000-363d1ba3-8ab5-4f96-bc25-4d5862db7cb9-c000.csv> |

Automatic download:

```bash
python code/data/download.py --data-dir data           # WUSTL-EHMS-2020
python code/data/download_ciciot.py --data-dir data    # CICIoT2023 (partition 0)
```

Both scripts fall back to mirrors and verify the checksum/header of the downloaded file. If the WUSTL mirror is unreachable, download the CSV manually from the link above and place it at `data/wustl-ehms-2020.csv`.

Please also cite the original dataset papers (see `data/README.md`).

---

## Installation

```bash
git clone https://github.com/tangsng/FedRBC.git
cd FedRBC

python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Requirements: `numpy`, `pandas`, `scikit-learn`, `scipy`, `matplotlib`, `torch>=1.10` (CPU is sufficient; a GPU accelerates the sweeps).

---

## Reproducing the experiments

Every experiment writes to `results/raw/` with a deterministic filename that encodes method / α / β / attack / seed / tag.

### 1. A single run

FedRBC (with its calibrated parameters):

```bash
python code/experiments/run_fl.py \
    --method fedrbc --alpha 0.5 --beta 0.3 --attack sign_flip \
    --seed 42 --tag v5 --gpu 0 \
    --tau-rel 2.0 --z-thresh 2.0 --soft-T 0.3
```

Baselines (RAID / FedGT / EIFFeL) take no FedRBC-specific flags:

```bash
python code/experiments/run_fl.py --method fedgt --alpha 0.5 --beta 0.3 \
    --attack sign_flip --seed 42 --tag v5 --gpu 0
```

Second dataset:

```bash
python code/experiments/run_fl.py --method fedrbc --dataset ciciot \
    --alpha 0.5 --beta 0.3 --attack sybil --seed 42 --tag v5 --gpu 0 \
    --tau-rel 2.0 --z-thresh 2.0 --soft-T 0.3
```

### 2. Full main table (Table 4 / Fig 4) — 5 seeds × 4 methods × 3 attacks + no-attack

```bash
python code/experiments/run_v5.py --gpu 0 --shard 0 --nshards 2 &
python code/experiments/run_v5.py --gpu 1 --shard 1 --nshards 2 &
wait
```

### 3. Byzantine-ratio and non-IID sweeps (Fig 5, Fig 6)

```bash
python code/experiments/run_sweep_v5.py --gpu 0 --shard 0 --nshards 2 &
python code/experiments/run_sweep_v5.py --gpu 1 --shard 1 --nshards 2 &
wait
```

### 4. MTTC emulation (Fig 9)

```bash
python code/experiments/run_mttc.py --out results/raw/mttc.csv
```

### 5. Figures, tables, and statistics

```bash
python code/utils/fig_architecture.py      # Fig 1-3 (architecture / sequence / reputation flow)
python code/utils/plots_sim.py             # Fig 4-9 + results/tables/table*.csv
python code/experiments/stat_test.py       # Paired t-tests over seeds
python code/experiments/final_check_v3.py  # Manuscript-vs-data consistency audit
```

---

## Results

All numbers in the paper are reproducible from `results/`.

| Paper item | Source |
|---|---|
| Table 4 (main table), Table 5 (cross-dataset) | `results/tables/table5_main.csv`, `table6_overhead.csv` |
| Fig 4-9 (all result figures) | generated by `python code/utils/plots_sim.py` into `results/figures/` (not shipped) |
| Fig 1-3 (architecture / sequence / flow) | generated by `python code/utils/fig_architecture.py` |

*(Figure filenames follow the historical numbering of the plotting script; running the two plotting scripts regenerates every figure from `results/raw/`.)*

### Raw data layout and tag convention

Each run produces up to three files in `results/raw/`:

- `*_summary.json` — final-round metrics (F1 / AUC / accuracy), config, wall-clock
- `*_rounds.csv` — per-round metrics
- `*_rep.npy` — per-client reputation trajectories (FedRBC only)

Tag semantics:

| Tag | Meaning |
|---|---|
| `v5` | **Final data used in the paper** — produced after the numerical-stability (NaN) fix |
| `ciciot_*` prefix | CICIoT2023 (second dataset) runs |
| `v7`, `bl` | Historical runs produced *before* the NaN fix; kept for provenance only, **not** used in the paper |
| `v4nan`, `v4fix`, `v4anneal` | Debugging runs from the NaN-fix investigation |

> **Note on the NaN fix.** Byzantine-robust FL simulations are susceptible to a silent numerical failure: a degenerate (near-zero-norm) client update makes the cosine evidence `0/0`, and the resulting NaN propagates through the reputation vector into the global model, after which the model collapses to single-class prediction. This can be mistaken for a robustness *failure of the method*. FedRBC guards against it by rejecting non-finite evidence at the aggregator and skipping non-finite aggregate updates (`FLEngine.apply_update`). All `v5` results are produced with this guard; see §5.7 of the manuscript.

---

## Main results (WUSTL-EHMS-2020, β = 30%, 5 seeds)

| Attack | FedRBC | RAID (2026) | FedGT (2025) | EIFFeL (2022) |
|---|---|---|---|---|
| Sign-flip | **0.588 ± 0.062** | 0.223 | 0.190 | 0.502 |
| Sybil collusion | **0.570 ± 0.056** | 0.128 | 0.142 | 0.089 |
| Label-flip | **0.561 ± 0.057** | 0.405 | 0.252 | 0.454 |

FedRBC attains the highest F1 and AUC in every scenario with the smallest seed-to-seed variance. Cross-dataset results on CICIoT2023 are in `results/tables/` and §5.8 of the manuscript.

---

## Citation

If you use this code, please cite:

```bibtex
@article{tang2026fedrbc,
  title   = {FedRBC: Blockchain-Enabled Reputation-Weighted Robust Federated Learning
             for Privacy-Preserving Healthcare IoT Edge Networks},
  author  = {Tang, Song and Jin, Zhigang and Wang, Zhiqiang},
  journal = {Computers, Materials \& Continua},
  year    = {2026},
  note    = {Under review}
}
```

See [`CITATION.cff`](CITATION.cff) for machine-readable metadata.

---

## License

Released under the [MIT License](LICENSE).

## Funding

This work is supported by the Hebei Provincial Science and Technology Program Project (Grant No. 25360301D): *Research and Application Demonstration of Key Technologies for Public Data Authorization and Operation Based on Trusted Data Space*.

## Contact

- Song Tang — <tangsng@live.cn>
- Zhigang Jin (corresponding author) — <zgjin@tju.edu.cn>
