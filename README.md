# Agentic AI Copilot for Operator Decision Support: Reproducible Pipeline

Root-cause identification on the **Tennessee Eastman Process (TEP)** under a
label-scarce, causally-windowed protocol. This repository reproduces every
number in **Table II** and the **label-efficiency figure** of the paper, from
the raw TEP data to the final CSV/figure, with a single command.

> Paper: *"Agentic AI Copilot for Operator Decision Support: Alarm
> Rationalization and Root-Cause Diagnosis in DCS-Based Industrial Plants"*
> (under preparation). Maestría en Automatización Industrial, UTH Honduras.

## Authors

- Mario Elvir, UTH Honduras
- Josué Rivera, UTH Honduras
- Christian Barahona, UTH Honduras
- Luis Loo, PhD(c), UTH Honduras (co-author and academic advisor)

---

## Reproducible baseline: the graded core

Everything here is produced by code in this repository. **What does not run does
not count.** After placing the data (Section 2), a fresh clone reproduces the
baseline with a single command:

```bash
python run_all.py
```

The reproducible baseline is four checkable pieces, each traceable to a script and
a number:

| Requirement | Where in the repo | Reproduced by | Number |
|---|---|---|---|
| Script that **loads and describes** the data | `01_explore_data.py` | step 1 of `run_all.py` | schema, 21 classes, quality checks |
| **Frozen partition**, committed to the repo | `splits/partition_manifest.csv`, `splits/partition_meta.json` | `02_make_partition.py` (seed 42) | sha256 `f55e7729a298e23c` |
| **Trivial** baseline, with its number | `results/classics_cv_comparison.csv` | `03_baselines.py`, `04_classics_cv.py` | F1-macro **0.004 ± 0.000** |
| **Simple model**, with its number | `results/classics_cv_comparison.csv` | `04_classics_cv.py` | Logistic regression **0.652 ± 0.005**; Random forest **0.638 ± 0.005**; Gradient boosting **0.640 ± 0.005** (F1-macro) |

Baseline only, skipping the auxiliary domain-feature analyses (~18-20 min): run
`02_make_partition.py`, `03_baselines.py`, `04_classics_cv.py`, `10_inference_time.py`
in that order (see the [Fast path](#3-reproduce) below).

---

## What this reproduces

- **Table II**: trivial floor, three classical baselines, two networks (MLP, 1D-CNN),
  and the copilot agent with its ablation
  (F1-macro primary; Recall@1/Recall@3/MRR secondary; per-episode inference latency as cost).
- **The agent measurements**: root-alarm identification with and without knowledge,
  the decomposed grounding rubric over three arms, and the action distribution
  (`results/agente_comparison.csv`, `results/logs/decisiones_muestra.jsonl`).
- **Label-efficiency curve**: F1-macro / Recall@k vs. fraction of labels used
  (`results/label_efficiency_curve.{csv,pdf,png}`).
- A **cross-validation leakage audit** (4 checks) confirming the protocol is honest.

**Task definition (deliberately harder than typical TEP benchmarks):** one label
per simulation run, an early **causal window `[21, 41)`** (decision made with data
available at the moment, never the future), and **21 root-cause classes**
(1 normal + 20 faults). This is why F1-macro ≈ 0.65 is expected and is *not*
comparable to the 90%+ figures reported by full-trajectory TEP studies: it buys
operational validity (latency measurable, real-time faithful).

---

## 1. Environment

Tested on **Python 3.14.2 (Windows 11)**. `requirements.txt` cannot pin the
interpreter itself, so use that version (or a virtual environment created from it):

```bash
python -m pip install -r requirements.txt
```

Core dependencies: `numpy`, `pandas`, `scikit-learn`, `pyreadr` (reads the `.RData`
files), `pyarrow` (parquet caches), `matplotlib` (figure). See `requirements.txt`
for exact pinned versions.

**Reference machine** for every runtime quoted in this README: Intel Core
i5-13420H (8 cores / 12 threads), 32 GB RAM, Windows 11, **CPU only, no GPU
required**. The scripts use all available cores (`N_JOBS = -1`), so wall-clock
times scale with core count. Results do not: the seeds fix every number.

## 2. Get the data (not stored in this repo)

The raw TEP simulation data is **not redistributed here**: it is large (~1.34 GB)
and publicly hosted at its canonical source. Download the four `.RData` files from:

> Rieth, C. A., Amsel, B. D., Tran, R., & Cook, M. B. (2017). *Additional
> Tennessee Eastman Process Simulation Data for Anomaly Detection Evaluation.*
> **Harvard Dataverse, V1.** DOI: [10.7910/DVN/6C3JR1](https://doi.org/10.7910/DVN/6C3JR1)

Place them exactly here (folder name `dataverse_files/`):

| File | Size | Role |
|---|--:|---|
| `TEP_FaultFree_Training.RData` | 24.7 MB | class 0, training pool |
| `TEP_Faulty_Training.RData`    | 494 MB  | classes 1-20, training pool |
| `TEP_FaultFree_Testing.RData`  | 47.3 MB | class 0, **test pool (sealed)** |
| `TEP_Faulty_Testing.RData`     | 837 MB  | classes 1-20, **test pool (sealed)** |

```
dataverse_files/
├── TEP_FaultFree_Training.RData
├── TEP_Faulty_Training.RData
├── TEP_FaultFree_Testing.RData
└── TEP_Faulty_Testing.RData
```

## 3. Reproduce

**Everything (one command, 12 CPU threads, no GPU):**

```bash
python run_all.py
```

Runs the 13 steps in dependency order, stops at the first failure, and lists the
result files produced. Re-running yields identical numbers (fixed seeds + the
frozen partition on disk). The **test set stays sealed throughout**: no
`*_Testing` file is opened for scoring.

Steps 1-10 were measured at about 80 min on the reference machine; steps 11 and
12 (network training over 15 folds and the agent over three arms) add to that.
Wall-clock is indicative and moves with processor and load.

**Fast path, just Table II (~18-20 min):** run only the core steps:

```bash
python 02_make_partition.py   # freeze the by-run split (seed 42)
python 03_baselines.py        # trivial + RF on the frozen split
python 04_classics_cv.py      # logistic + RF + Gradient Boosting, grouped CV -> Table II
python 10_inference_time.py   # training time + inference latency (Table II cost)
```

Add `08_label_efficiency.py` then `09_plot_label_efficiency.py` to regenerate the
figure (both need the feature cache built by step 04).

**Agent rows of Table II:** `11_train_dl.py` (needs PyTorch, writes one checkpoint
per fold to `results/models/`) then `12_agente_v1.py`, which reuses those
checkpoints and does not retrain.

## 4. Expected results (frozen)

`results/classics_cv_comparison.csv`, `results/dl_comparison.csv`,
`results/agente_comparison.csv` and `results/inference_time.csv` should match:

| Model | F1-macro | Recall@3 | Inference |
|---|---|---|---|
| Trivial (majority) | 0.004 ± 0.000 | 0.143 ± 0.000 | < 0.001 ms |
| Logistic regression | 0.652 ± 0.005 | 0.733 ± 0.003 | 0.003 ms |
| Random forest | 0.638 ± 0.005 | 0.703 ± 0.006 | 0.081 ms |
| Gradient boosting | 0.640 ± 0.005 | 0.654 ± 0.007 | 0.073 ms |
| Neural net v1a (MLP) | 0.652 ± 0.013 | 0.754 ± 0.017 | < 0.001 ms |
| Neural net v1b (1D-CNN) | 0.696 ± 0.006 | 0.786 ± 0.007 | 0.004 ms |
| **No agent (ablation)** | **0.752 ± 0.009** | **0.852 ± 0.010** | 0.103 ms |
| Copilot v1 (proposed) | 0.741 ± 0.008 | 0.845 ± 0.009 | 0.203 ms |

The MLP sees the same 104 features as the classics and ties logistic regression;
the 1D-CNN sees the raw `20 x 52` window and beats it by 0.044 macro-F1, about
seven times the fold-to-fold standard deviation. The gain comes from the
representation, not from the architecture.

The last two rows are the same 1D-CNN placed inside the agent loop. Both gain
0.056 macro-F1 over scoring it once, because the loop moves the observation
window forward in 66% of decisions. That gain belongs to the loop and is present
in both arms, so the ablation does not measure it; what the ablation isolates is
retrieval, and retrieval costs 0.011 macro-F1. **The proposed method does not beat
its own ablation on the primary metric.** What retrieval does buy is measured
separately and reported in the paper. Ordering alarms chronologically identifies
the root alarm in 0.349 of the episodes whose cause the source documents;
weighting each alarm by retrieved evidence raises that to 0.619 for the
label-anchored arm (`lookup`, the third arm produced by `12_agente_v1.py`) and to
0.383 for the proposed symptom-based arm, while the same prioritization with no
knowledge at all changes nothing. What the proposed arm alone provides is a
confidence signal: classifier and retrieval agree on 42.7% of episodes and are
then right 94.0% of the time, against 60.4% when they disagree. The `lookup` arm
shares its classifier with the ablation, so its F1-macro and Recall@3 repeat that
row and it is not listed above.

Mean ± std over **15 folds** (StratifiedGroupKFold-by-run, k=5, seeds {5,17,42};
selection seed 0). Determinism is further guaranteed by the committed partition
manifest: `splits/partition_meta.json` stores `manifest_sha256_16 = f55e7729a298e23c`,
which `02_make_partition.py` reproduces exactly.

## 5. Repository layout

```
01_explore_data.py              schema, class counts, data-quality checks
02_make_partition.py            freeze the by-run partition (seed 42) -> splits/
03_baselines.py                 trivial + Random Forest on the frozen split
04_classics_cv.py               logistic + RF + Gradient Boosting w/ CV -> Table II + cache
05_domain_features.py           domain-knowledge features + permutation importance
06_domain_features_nonlinear.py do domain features help nonlinear models?
07_cv_audit.py                  cross-validation leakage audit (4 checks)
08_label_efficiency.py          label-efficiency curve (the measurable contribution)
09_plot_label_efficiency.py     render the figure (PDF/PNG)
10_inference_time.py            training time + inference latency (Table II cost)
11_train_dl.py                  deep learning v1: MLP + 1D-CNN, curves -> results/curves/
12_agente_v1.py                 copilot agent v1: alarm layer, loop, three arms -> Table II
checkpoint_datos.py             live data checkpoint (integrity evidence)
run_all.py                      one-command reproducible pipeline (all of the above)
requirements.txt                pinned environment
PROTOCOLO.md                    canonical experimental protocol
references.bib                  bibliography
kb/                             reproducible TEP knowledge base (21 documents, JSON)
prompts/                        fixed reasoning prompt, declared and not executed (see below)
splits/                         frozen partition manifest + metadata (committed)
results/                        result tables (CSV), env stamps (JSON), figure (PDF/PNG)
```

Feature caches (`results/*.parquet`, `results/*.npy`), the per-fold network
checkpoints (`results/models/`), the full decision log
(`results/logs/decisiones.jsonl`, 94,500 lines) and the raw data are intentionally
**not** committed: all of them are regenerated deterministically from the steps
above. A 1,000-line sample of the decision log is committed as
`results/logs/decisiones_muestra.jsonl`.

**The reasoning step is rule-based, not a language model.** `12_agente_v1.py`
produces the recommendation from a fixed template over the retrieved documents, so
the pipeline runs offline with no API key and reproduces exactly.
`prompts/razona.txt` is the prompt that a language-model version would use; it is
**declared and not executed**, and no number in this repository depends on it.
`results/agente_env.json` records this.

## 6. AI assistance declaration

AI coding assistants (Claude / Claude Code) were used to help implement the
pipeline scripts, this documentation, and the analysis in this repository. That
use is declared here in full, and it changes nothing about how the results are
judged: **every number and figure is produced by code in this repository that runs
end-to-end** (`python run_all.py`). No agent output was accepted as a result
without verification: the pipeline was re-executed from the raw data, the
frozen-partition integrity hash was re-checked (`f55e7729a298e23c`, matched), and
every Table II value was confirmed to reproduce. What does not run is not reported.

## 7. License / contact

Data © Rieth et al. 2017 (Harvard Dataverse), used under its terms; not
redistributed here. Code released for academic reproducibility. Contact: the
authors (see Team / Authors above), UTH Honduras.
