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
│   ├── figures/               # Paper figures (PDF + PNG, 300 dpi)
│   └── tables/                # Aggregated result tables (CSV / LaTeX)
├── requirements.txt
├── CITATION.cff
├── LICENSE
└── README.md
```

---

## Datasets

Both datasets are publicly available. **They are not redistributed in this repository** — use the automatic downloaders or the links below.

| Dataset             | Role                                             | Size                                | Download                                                                                                                                |
| ------------------- | ------------------------------------------------ | ----------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| **WUSTL-EHMS-2020** | Primary benchmark (healthcare IoT, MITM attacks) | 3.8 MB, 16,318 flows                | <https://www.cse.wustl.edu/~jain/ehms/index.html>                                                                                       |
| **CICIoT2023**      | Second dataset for cross-dataset generalization  | ~70 MB (partition 0, 238,687 flows) | <https://media.githubusercontent.com/media/val-co/CIC-IoT-2023-Dataset/master/part-00000-363d1ba3-8ab5-4f96-bc25-4d5862db7cb9-c000.csv> |

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

### 

## Results

All numbers in the paper are reproducible from `results/`.

| Paper item                                    | Source                                                  |
| --------------------------------------------- | ------------------------------------------------------- |
| Table 4 (main table), Table 5 (cross-dataset) | `results/tables/table5_main.csv`, `table6_overhead.csv` |
| Fig 4 (main attacks)                          | `results/figures/fig5_main_attacks.pdf`                 |
| Fig 5 (β sweep)                               | `results/figures/fig7_beta_sweep.pdf`                   |
| Fig 6 (non-IID)                               | `results/figures/fig8_noniid.pdf`                       |
| Fig 7 (convergence)                           | `results/figures/fig6_convergence.pdf`                  |
| Fig 8 (reputation dynamics)                   | `results/figures/fig9_repdyn.pdf`                       |
| Fig 9 (MTTC)                                  | `results/figures/fig10_mttc.pdf`                        |

**
