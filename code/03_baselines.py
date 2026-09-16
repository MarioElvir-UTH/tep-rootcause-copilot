"""
S1 - Steps 3 & 4: two baselines for root-cause identification (per run, 21 classes).
  a) Trivial baseline: predict by TRAIN class frequency (floor).
  b) Classic baseline: Random Forest on per-run features.
Same frozen partition (splits/partition_manifest.csv). Same metrics: Recall@1,
Recall@3, MRR, macro-Recall@1. Evaluated on VALIDATION (test stays sealed).
Feature = mean+std of the 52 process variables over a CAUSAL early window
[onset, onset+W): only data up to the decision point (respects temporal causality).
Fixed seed; library versions declared at the end.
"""
import os, json, platform
import numpy as np
import pandas as pd
import pyreadr
import sklearn
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier

SEED = 42
W = 20  # causal window length (samples after onset) = 1 h of post-onset data
BASE = os.path.dirname(os.path.abspath(__file__))
if not os.path.isfile(os.path.join(BASE, "requirements.txt")):
    BASE = os.path.dirname(BASE)      # the scripts live in code/, the project one level up
DATA = os.path.join(BASE, "dataverse_files")
np.random.seed(SEED)

VARS = [f"xmeas_{i}" for i in range(1, 42)] + [f"xmv_{i}" for i in range(1, 12)]  # 52
ONSET_TRAIN = 21  # first fault sample in the training pool

man = pd.read_csv(os.path.join(BASE, "splits", "partition_manifest.csv"))
train_pool = man[man.pool == "train_pool"].copy()
split_of = {(int(r.faultNumber), int(r.simulationRun)): r.split for r in train_pool.itertuples()}


def features_from_file(fname, onset):
    """mean+std of the 52 vars over the causal window [onset, onset+W) per run."""
    res = pyreadr.read_r(os.path.join(DATA, fname))
    df = res[list(res.keys())[0]]
    del res
    sub = df[df["sample"].between(onset, onset + W - 1)]
    g = sub.groupby(["faultNumber", "simulationRun"])[VARS].agg(["mean", "std"])
    g.columns = [f"{v}_{s}" for v, s in g.columns]
    g = g.reset_index()
    g["faultNumber"] = g["faultNumber"].astype(int)
    g["simulationRun"] = g["simulationRun"].astype(int)
    del df, sub
    return g


# Build train-pool feature table (class 0 + faults 1-20) from the TRAINING files only
feat = pd.concat([
    features_from_file("TEP_FaultFree_Training.RData", ONSET_TRAIN),
    features_from_file("TEP_Faulty_Training.RData", ONSET_TRAIN),
], ignore_index=True)
feat["split"] = [split_of[(f, r)] for f, r in zip(feat.faultNumber, feat.simulationRun)]

featcols = [c for c in feat.columns if c.endswith(("_mean", "_std"))]
tr = feat[feat.split == "train"]
va = feat[feat.split == "val"]
Xtr, ytr = tr[featcols].to_numpy(), tr["faultNumber"].to_numpy()
Xva, yva = va[featcols].to_numpy(), va["faultNumber"].to_numpy()
print(f"features: {len(featcols)} | train runs: {len(ytr)} | val runs: {len(yva)} | window=[{ONSET_TRAIN},{ONSET_TRAIN+W})")

# Standardize: fit on TRAIN only (no leakage)
sc = StandardScaler().fit(Xtr)
Xtr_s, Xva_s = sc.transform(Xtr), sc.transform(Xva)

CLASSES = np.arange(0, 21)


def rank_metrics(y_true, proba, classes):
    classes = np.asarray(classes)
    order = np.argsort(-proba, axis=1)
    ranked = classes[order]
    true = np.asarray(y_true).reshape(-1, 1)
    pos = (ranked == true).argmax(axis=1)  # 0-based rank of the true class
    top1 = ranked[:, 0]
    macro = [np.mean(top1[(true.ravel() == c)] == c) for c in np.unique(true)]
    return {
        "Recall@1": float(np.mean(pos < 1)),
        "Recall@3": float(np.mean(pos < 3)),
        "MRR": float(np.mean(1.0 / (pos + 1))),
        "macroRecall@1": float(np.mean(macro)),
    }


# a) Trivial baseline: score every val run by TRAIN class frequency
freq = np.array([(ytr == c).sum() for c in CLASSES], dtype=float)
proba_trivial = np.tile(freq / freq.sum(), (len(yva), 1))
m_trivial = rank_metrics(yva, proba_trivial, CLASSES)

# b) Classic baseline: Random Forest
rf = RandomForestClassifier(n_estimators=300, max_depth=None, n_jobs=-1,
                            class_weight="balanced", random_state=SEED)
rf.fit(Xtr_s, ytr)
proba_rf = rf.predict_proba(Xva_s)  # columns follow rf.classes_
m_rf = rank_metrics(yva, proba_rf, rf.classes_)

# ---- comparative table ----
table = pd.DataFrame(
    [{"baseline": "Trivial (class frequency)", **m_trivial},
     {"baseline": "Classic (Random Forest)", **m_rf}]
)[["baseline", "Recall@1", "Recall@3", "MRR", "macroRecall@1"]]

os.makedirs(os.path.join(BASE, "results"), exist_ok=True)
table.to_csv(os.path.join(BASE, "results", "baseline_comparison.csv"), index=False)

pd.set_option("display.float_format", lambda x: f"{x:.4f}")
print("\n================ BASELINE COMPARISON (evaluated on VALIDATION; test sealed) ================")
print(table.to_string(index=False))
print("\n(Chance level for 21 balanced classes: Recall@1 = 1/21 = %.4f, Recall@3 = 3/21 = %.4f)"
      % (1/21, 3/21))

versions = {
    "python": platform.python_version(),
    "numpy": np.__version__, "pandas": pd.__version__,
    "scikit-learn": sklearn.__version__, "pyreadr": pyreadr.__version__ if hasattr(pyreadr, "__version__") else "0.5.6",
    "seed": SEED, "window_W": W, "onset_train": ONSET_TRAIN,
}
with open(os.path.join(BASE, "results", "baseline_env.json"), "w", encoding="utf-8") as f:
    json.dump(versions, f, indent=2)
print("\nLibrary versions / config:")
for k, v in versions.items():
    print(f"  {k}: {v}")
