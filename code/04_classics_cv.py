"""
Train and compare the classic baselines under the validation contract.
Task: root-cause identification per run on TEP (Rieth), 21 classes (0=normal,1-20=faults).
Features: mean+std of the 52 process variables over the causal window [onset, onset+20).
Models: logistic regression, random forest, gradient boosting (HistGB).
Protocol:
  - Frozen partition: dev = *_Training runs, test = *_Testing (SEALED, never loaded).
  - CV: StratifiedGroupKFold by run, k=5. Preprocessing (StandardScaler) inside a
    Pipeline -> fit within each fold. Groups = run (with one window per run this
    coincides with stratified KFold, but keeps the group=run contract explicit).
  - Small grid, declared beforehand, same effort (3 points) for all models.
    Hyperparameter SELECTION uses a separate seed (0); PERFORMANCE ESTIMATE uses
    3 seeds (5,17,42) -> mean +/- std. Test not touched.
Primary metric: macro-F1 (the frozen protocol metric; hyperparameter selection and
the best-model choice both use it, so what is tuned is what is reported).
Secondary: Recall@3, the one Table II reports; Recall@1 and MRR are computed
but not reported. Plus per-class F1 / confusion matrix of the
best model (out-of-fold, seed 42).
"""
import os, json, platform
N_JOBS = -1  # all cores; no thermal cap (laptop holds ~60-65 C under full load)
import numpy as np
import pandas as pd
import pyreadr
import sklearn
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.metrics import f1_score, confusion_matrix

BASE = os.path.dirname(os.path.abspath(__file__))
if not os.path.isfile(os.path.join(BASE, "requirements.txt")):
    BASE = os.path.dirname(BASE)      # the scripts live in code/, the project one level up
DATA = os.path.join(BASE, "dataverse_files")
RES = os.path.join(BASE, "results"); os.makedirs(RES, exist_ok=True)
ERR = os.path.join(RES, "errors")
os.makedirs(ERR, exist_ok=True)
VARS = [f"xmeas_{i}" for i in range(1, 42)] + [f"xmv_{i}" for i in range(1, 12)]
ONSET_TRAIN, W = 21, 20
K, SEL_SEED, EST_SEEDS = 5, 0, [5, 17, 42]
GRIDS = {
    "logistic": [{"C": 0.1}, {"C": 1.0}, {"C": 10.0}],
    "rf":       [{"max_depth": None}, {"max_depth": 10}, {"max_depth": 20}],
    "hgb":      [{"learning_rate": 0.05}, {"learning_rate": 0.1}, {"learning_rate": 0.2}],
}
CLASSES = np.arange(0, 21)

# ---------- features (cached) ----------
FEAT_CACHE = os.path.join(RES, "dev_features.parquet")
if os.path.exists(FEAT_CACHE):
    feat = pd.read_parquet(FEAT_CACHE)
    print("loaded cached dev features:", FEAT_CACHE)
else:
    def feats(fname):
        res = pyreadr.read_r(os.path.join(DATA, fname)); df = res[list(res.keys())[0]]; del res
        sub = df[df["sample"].between(ONSET_TRAIN, ONSET_TRAIN + W - 1)]
        g = sub.groupby(["faultNumber", "simulationRun"])[VARS].agg(["mean", "std"])
        g.columns = [f"{v}_{s}" for v, s in g.columns]; g = g.reset_index()
        g["faultNumber"] = g["faultNumber"].astype(int); g["simulationRun"] = g["simulationRun"].astype(int)
        del df, sub; return g
    feat = pd.concat([feats("TEP_FaultFree_Training.RData"), feats("TEP_Faulty_Training.RData")], ignore_index=True)
    feat.to_parquet(FEAT_CACHE); print("extracted + cached dev features:", FEAT_CACHE)

featcols = [c for c in feat.columns if c.endswith(("_mean", "_std"))]
X = feat[featcols].to_numpy()
y = feat["faultNumber"].to_numpy()
groups = (feat["faultNumber"].to_numpy() * 1000 + feat["simulationRun"].to_numpy())
print(f"dev runs: {len(y)} | features: {len(featcols)} | classes: {len(np.unique(y))}")


def make_est(name, params, seed):
    steps = [("sc", StandardScaler())]
    if name == "logistic":
        steps.append(("clf", LogisticRegression(max_iter=2000, class_weight="balanced", C=params["C"])))
    elif name == "rf":
        steps.append(("clf", RandomForestClassifier(n_estimators=300, max_depth=params["max_depth"],
                                                     class_weight="balanced", n_jobs=N_JOBS, random_state=seed)))
    elif name == "hgb":
        steps.append(("clf", HistGradientBoostingClassifier(learning_rate=params["learning_rate"], random_state=seed)))
    return Pipeline(steps)


def rank_metrics(yt, proba, classes):
    order = np.argsort(-proba, axis=1); ranked = np.asarray(classes)[order]
    pos = (ranked == np.asarray(yt).reshape(-1, 1)).argmax(axis=1)
    top1 = ranked[:, 0]
    macro = [np.mean(top1[yt == c] == c) for c in np.unique(yt)]
    return {"Recall@1": float(np.mean(pos < 1)), "Recall@3": float(np.mean(pos < 3)),
            "MRR": float(np.mean(1.0 / (pos + 1))), "macroRecall@1": float(np.mean(macro))}


def cv_fold_metrics(name, params, seed):
    sgkf = StratifiedGroupKFold(n_splits=K, shuffle=True, random_state=seed)
    out = []
    for tri, vai in sgkf.split(X, y, groups):
        est = make_est(name, params, seed); est.fit(X[tri], y[tri])
        cls = est.named_steps["clf"].classes_
        proba = est.predict_proba(X[vai])
        m = rank_metrics(y[vai], proba, cls)
        m["F1macro"] = float(f1_score(y[vai], cls[np.argmax(proba, axis=1)], average="macro"))
        out.append(m)
    return out


def trivial_fold_metrics(seed):
    sgkf = StratifiedGroupKFold(n_splits=K, shuffle=True, random_state=seed)
    out = []
    for tri, vai in sgkf.split(X, y, groups):
        freq = np.array([(y[tri] == c).sum() for c in CLASSES], float)
        proba = np.tile(freq / freq.sum(), (len(vai), 1))
        m = rank_metrics(y[vai], proba, CLASSES)
        m["F1macro"] = float(f1_score(y[vai], np.full(len(vai), CLASSES[np.argmax(freq)]), average="macro"))
        out.append(m)
    return out


# ---------- hyperparameter selection (seed 0) ----------
best_cfg = {}
print("\nhyperparameter selection (seed %d, best mean macro-F1):" % SEL_SEED)
for name in ["logistic", "rf", "hgb"]:
    scored = []
    for cfg in GRIDS[name]:
        folds = cv_fold_metrics(name, cfg, SEL_SEED)
        scored.append((float(np.mean([d["F1macro"] for d in folds])),
                       float(np.mean([d["Recall@1"] for d in folds])), cfg))
    best = max(scored, key=lambda t: t[0]); best_cfg[name] = best[2]
    alt = max(scored, key=lambda t: t[1])          # what the old Recall@1 rule would pick
    print(f"  {name}: {best[2]}  (macro-F1={best[0]:.4f})")
    for f1m, r1, cfg in scored:
        print(f"      {str(cfg):<30} macro-F1={f1m:.4f}   Recall@1={r1:.4f}")
    print("      criterion check: Recall@1 would pick %s -> %s"
          % (alt[2], "SAME" if alt[2] == best[2] else "DIFFERENT"))

# ---------- performance estimate (3 seeds -> mean +/- std) ----------
METRICS = ["Recall@1", "Recall@3", "MRR", "F1macro"]
rows = []
def summarize(label, folds):
    return {"model": label, **{m: (np.mean([d[m] for d in folds]), np.std([d[m] for d in folds])) for m in METRICS}}

rows.append(summarize("Trivial (freq)", sum((trivial_fold_metrics(s) for s in EST_SEEDS), [])))
for name in ["logistic", "rf", "hgb"]:
    folds = sum((cv_fold_metrics(name, best_cfg[name], s) for s in EST_SEEDS), [])
    rows.append(summarize(f"{name} {best_cfg[name]}", folds))

print("\n==================== CLASSIC BASELINES  (StratifiedGroupKFold-by-run, k=5, 3 seeds; mean +/- std; TEST SEALED) ====================")
hdr = f"{'model':<34}" + "".join(f"{m:>18}" for m in METRICS)
print(hdr); print("-" * len(hdr))
tab = []
for r in rows:
    line = f"{r['model']:<34}" + "".join(f"{r[m][0]:>10.4f}+/-{r[m][1]:<5.3f}" for m in METRICS)
    print(line)
    tab.append({"model": r["model"], **{f"{m}_mean": r[m][0] for m in METRICS}, **{f"{m}_std": r[m][1] for m in METRICS}})
pd.DataFrame(tab).to_csv(os.path.join(RES, "classics_cv_comparison.csv"), index=False)

# ---------- best model: out-of-fold per-class F1 + confusion matrix (seed 42) ----------
best_model = max(["logistic", "rf", "hgb"],
                 key=lambda n: np.mean([d["F1macro"] for d in cv_fold_metrics(n, best_cfg[n], 42)]))
sgkf = StratifiedGroupKFold(n_splits=K, shuffle=True, random_state=42)
oof = np.full(len(y), -1)
for tri, vai in sgkf.split(X, y, groups):
    est = make_est(best_model, best_cfg[best_model], 42); est.fit(X[tri], y[tri])
    cls = est.named_steps["clf"].classes_
    oof[vai] = cls[np.argmax(est.predict_proba(X[vai]), axis=1)]
f1c = f1_score(y, oof, average=None, labels=CLASSES)
print(f"\nBest model (out-of-fold, seed 42): {best_model} {best_cfg[best_model]}")
print("per-class F1 (0=normal, 1-20=faults):")
print("  " + "  ".join(f"{c}:{f1c[c]:.2f}" for c in CLASSES))
print("hard faults -> F1  3:%.2f  9:%.2f  15:%.2f" % (f1c[3], f1c[9], f1c[15]))
cm = confusion_matrix(y, oof, labels=CLASSES)
pd.DataFrame(cm, index=CLASSES, columns=CLASSES).to_csv(
    os.path.join(ERR, "best_model_confusion_matrix.csv"))

versions = {"python": platform.python_version(), "numpy": np.__version__, "pandas": pd.__version__,
            "scikit-learn": sklearn.__version__, "cv": f"StratifiedGroupKFold k={K}",
            "sel_seed": SEL_SEED, "est_seeds": EST_SEEDS, "window": [ONSET_TRAIN, ONSET_TRAIN + W]}
with open(os.path.join(RES, "classics_cv_env.json"), "w") as f:
    json.dump(versions, f, indent=2)
print("\nsaved: results/classics_cv_comparison.csv, "
      "results/errors/best_model_confusion_matrix.csv, classics_cv_env.json")
print("versions:", versions)
