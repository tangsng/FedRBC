# Datasets

The datasets used by FedRBC are **third-party and are not redistributed here**. Download them with the provided scripts (recommended) or manually from the links below, then place them in this directory (or pass `--data-dir` to any script).

| Dataset | File | Size | Rows | Used for |
|---|---|---|---|---|
| WUSTL-EHMS-2020 | `wustl-ehms-2020.csv` | 3.8 MB | 16,318 flows | Primary benchmark (all main results) |
| CICIoT2023 | `part-00000-...csv` | ~70 MB | 238,687 flows | Cross-dataset generalization (§5.8) |

---

## 1. WUSTL-EHMS-2020

Healthcare IoT traffic captured on a real hospital testbed (ECG patches, bedside monitors, infusion pumps, imaging gateways) with MITM attacks (spoofing / injection).

- **Official page:** <https://www.cse.wustl.edu/~jain/ehms/index.html>
- **Direct CSV:** <https://www.cse.wustl.edu/~jain/ehms/ftp/wustl-ehms-2020_with_attacks_categories.csv>
- **Mirror (if the lab server is unreachable):** Kaggle — search *"WUSTL EHMS 2020"* (see the note printed by `code/data/download.py`).

Automatic download:

```bash
python code/data/download.py --data-dir data
```

Preprocessing applied by the code (`code/data/download.py` + `run_fl.py`):

- binary label: `benign` vs. attack (MITM spoofing / injection categories merged)
- 40+ numeric flow features, standardized with `StandardScaler`
- attack prevalence ≈ **12.5%** (the minority class that F1/AUC target)
- 500 samples held out as the server-side **root set** $\mathcal{D}_r$

<details>
<summary>BibTeX</summary>

```bibtex
@article{hady2020intrusion,
  title   = {Intrusion Detection System for Healthcare Systems Using Medical and
             Network Data: A Comparison Study},
  author  = {Hady, Ahmad Ali and Ghubaish, Ashraf and Salman, Tara and
             Unal, Devrim and Jain, Raj},
  journal = {IEEE Access},
  volume  = {8},
  pages   = {106576--106584},
  year    = {2020},
  doi     = {10.1109/ACCESS.2020.3000421}
}
```

</details>

---

## 2. CICIoT2023

Large-scale IoT attack benchmark (33 attack types). We use **partition 0** only, which keeps the task comparable in scale to WUSTL-EHMS-2020.

- **Paper:** Sensors 2023, <https://doi.org/10.3390/s23135941>
- **Partition 0 (GitHub LFS media URL, verified working):**
  <https://media.githubusercontent.com/media/val-co/CIC-IoT-2023-Dataset/master/part-00000-363d1ba3-8ab5-4f96-bc25-4d5862db7cb9-c000.csv>

> Note: fetching the file through the ordinary `raw.githubusercontent.com` path returns a Git-LFS pointer (133 bytes), not the data. Use the `media.githubusercontent.com` URL above, or the downloader script.

Automatic download:

```bash
python code/data/download_ciciot.py --data-dir data
```

Preprocessing applied by the code (`code/data/download_ciciot.py`):

- binary label: `benign*` categories vs. all attack categories (the benign class is named `benigntraffic`)
- numeric features only, constant/invalid columns dropped → 40 features
- the raw partition is ~97.7% attack, so attacks are **down-sampled to a 3:1 attack:benign ratio** to keep detection a minority-class problem
- resulting training set ≈ 17,920 samples

<details>
<summary>BibTeX</summary>

```bibtex
@article{neto2023ciciot2023,
  title   = {CICIoT2023: A Real-Time Dataset and Benchmark for Large-Scale
             Attacks in IoT Environment},
  author  = {Neto, Euclides Carlos Pinto and Dadkhah, Sajjad and Ferreira, Raphael
             and Zohourian, Abdollah and Lu, Rongxing and Ghorbani, Ali A.},
  journal = {Sensors},
  volume  = {23},
  number  = {13},
  pages   = {5941},
  year    = {2023},
  doi     = {10.3390/s23135941}
}
```

</details>

---

## Expected layout after download

```
data/
├── wustl-ehms-2020.csv
└── ciciot2023_part0.csv
```

`data/*.csv` is listed in `.gitignore` — downloaded datasets stay local and are never committed.
