"""
S1 - Step 2: Define and FREEZE the train/validation/test partition (before any model).

Grouping restriction: one simulation run = one unit. All samples/windows of the
  same run stay in the same split (split BY RUN), stratified by class.
Temporal restriction: TEP runs are independent simulations, so there is NO
  chronological order across runs; a "train-before-test" split does not apply at
  the run level. Temporal causality is enforced WITHIN each run via causal feature
  windows in the feature/model steps (only data up to the decision time).

Design: standard Rieth split.
  - train_pool = *_Training files (dev): split by run into train / validation.
  - test_pool  = *_Testing files: held-out test, opened once.
Fixed seed; run indices saved to disk (manifest CSV + metadata JSON) so the
partition is always the same.
"""
import os, json, hashlib
import numpy as np
import pandas as pd

BASE = os.path.dirname(os.path.abspath(__file__))
if not os.path.isfile(os.path.join(BASE, "requirements.txt")):
    BASE = os.path.dirname(BASE)      # the scripts live in code/, the project one level up
OUT = os.path.join(BASE, "splits")
os.makedirs(OUT, exist_ok=True)

SEED = 42
VAL_FRACTION = 0.20            # of the training-pool runs, per class
RUNS_PER_CLASS = 500           # verified in Step 1 (identical in every file)
CLASSES = list(range(0, 21))   # 0 = normal, 1..20 = faults
ONSET = {"train_pool": 21, "test_pool": 161}  # first FAULT sample (documented onset 1h/8h)

rng = np.random.default_rng(SEED)
n_val = int(round(RUNS_PER_CLASS * VAL_FRACTION))  # 100 per class

rows = []
# Training pool -> train / val, stratified by class, split by run
for c in CLASSES:
    runs = np.arange(1, RUNS_PER_CLASS + 1)
    val_runs = set(rng.permutation(runs)[:n_val].tolist())
    for r in runs:
        rows.append(("train_pool", c, int(r), "val" if r in val_runs else "train"))
# Testing pool -> held-out test (opened once)
for c in CLASSES:
    for r in range(1, RUNS_PER_CLASS + 1):
        rows.append(("test_pool", c, int(r), "test"))

man = pd.DataFrame(rows, columns=["pool", "faultNumber", "simulationRun", "split"])

# ---- sanity checks ----
assert man.duplicated(subset=["pool", "faultNumber", "simulationRun"]).sum() == 0, "duplicate run assignment"
tp = man[man.pool == "train_pool"]
overlap = (set(map(tuple, tp[tp.split == "train"][["faultNumber", "simulationRun"]].values)) &
           set(map(tuple, tp[tp.split == "val"][["faultNumber", "simulationRun"]].values)))
assert len(overlap) == 0, "train/val run overlap"

# ---- save ----
man_path = os.path.join(OUT, "partition_manifest.csv")
man.to_csv(man_path, index=False)
sha = hashlib.sha256(open(man_path, "rb").read()).hexdigest()[:16]

meta = {
    "seed": SEED,
    "unit": "one simulation run = (pool, faultNumber, simulationRun)",
    "grouping": "split by run; all samples/windows of a run stay in one split; stratified by class",
    "temporal": "runs are independent simulations (no cross-run order); causality enforced within-run via causal windows later",
    "design": "standard Rieth split: train_pool=*_Training (train+val), test_pool=*_Testing (test, opened once)",
    "val_fraction_of_train_pool": VAL_FRACTION,
    "runs_per_class": RUNS_PER_CLASS,
    "classes": CLASSES,
    "onset_first_fault_sample": ONSET,
    "source_files": {
        "train_pool": ["TEP_FaultFree_Training.RData (class 0)", "TEP_Faulty_Training.RData (classes 1-20)"],
        "test_pool": ["TEP_FaultFree_Testing.RData (class 0)", "TEP_Faulty_Testing.RData (classes 1-20)"],
    },
    "counts": {
        "train_runs": int((man.split == "train").sum()),
        "val_runs": int((man.split == "val").sum()),
        "test_runs": int((man.split == "test").sum()),
    },
    "manifest_sha256_16": sha,
}
with open(os.path.join(OUT, "partition_meta.json"), "w", encoding="utf-8") as f:
    json.dump(meta, f, indent=2, ensure_ascii=False)

# ---- report ----
print("saved:", man_path)
print("saved:", os.path.join(OUT, "partition_meta.json"))
print("manifest sha256[:16]:", sha, "(seed", SEED, ")")
print("\ntotal run assignments:", len(man))
print("\nruns by split:")
print(man.groupby("split").size().to_string())
print("\nruns per class per split (0=normal, 1-20=faults):")
print(man.pivot_table(index="faultNumber", columns="split",
                      values="simulationRun", aggfunc="count", fill_value=0).to_string())
print("\nfirst rows of manifest:")
print(man.head(3).to_string(index=False))
print("\nsanity: no run in >1 split (pool-wise) OK; train/val disjoint OK")
