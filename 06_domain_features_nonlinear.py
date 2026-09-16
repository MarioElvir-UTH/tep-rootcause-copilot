"""
S2 - Prompt 2 (optional follow-up): do the domain-knowledge features help a NONLINEAR
model, unlike the linear case?

In 05_domain_features.py the 7 domain families gave NO Recall@1 gain over mean+std for
LOGISTIC regression (0.6526 vs 0.6564): for a linear model the extra columns are largely
redundant/collinear. Trees and gradient boosting can exploit interactions and thresholds
that a linear model cannot, so the domain features (variability, drift, excursion,
deviation-from-normal, control effort) might add value here. This script tests exactly
that, on the SAME folds, and reports family-level permutation importance per model.

Same contract: partition by run, StratifiedGroupKFold-by-run k=5 (seed 42), the
normal-baseline (deviation feature) fit INSIDE each fold, test SEALED. Reuses the cached
base features from 05 (results/dev_domain_features.parquet). Models use the Prompt-1
winning configs: RF max_depth=20 / n_estimators=300; HistGB learning_rate=0.05.
"""
import os, json, platform
N_JOBS = -1  # all cores; no thermal cap (laptop holds ~60-65 C under full load)
import numpy as np
import pandas as pd
import sklearn
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.metrics import f1_score

BASE = os.path.dirname(os.path.abspath(__file__))
if not os.path.isfile(os.path.join(BASE, "requirements.txt")):
    BASE = os.path.dirname(BASE)      # the scripts live in code/, the project one level up
RES = os.path.join(BASE, "results")
CACHE = os.path.join(RES, "dev_domain_features.parquet")
assert os.path.exists(CACHE), "run 05_domain_features.py first to build the feature cache"

XMEAS = [f"xmeas_{i}" for i in range(1, 42)]
XMV = [f"xmv_{i}" for i in range(1, 12)]
VARS = XMEAS + XMV
K, SEEDS = 5, [5, 17, 42]
R_PERM = 5
EPS = 1e-9

feat = pd.read_parquet(CACHE)
RATIO_COLS = ["ratio_A_over_AC", "ratio_purge_recycle"]
base_cols = ([f"mean_{v}" for v in VARS] + [f"std_{v}" for v in VARS] +
             [f"range_{v}" for v in VARS] + [f"slope_{v}" for v in VARS] +
             [f"effort_{v}" for v in XMV] + RATIO_COLS)
dev_cols = [f"dev_{v}" for v in VARS]
all_cols = base_cols + dev_cols
FAMILIES = {
    "level (mean)":         [f"mean_{v}" for v in VARS],
    "fluctuation (std)":    [f"std_{v}" for v in VARS],
    "range (max-min)":      [f"range_{v}" for v in VARS],
    "trend (slope)":        [f"slope_{v}" for v in VARS],
    "control effort (XMV)": [f"effort_{v}" for v in XMV],
    "feed/flow ratios":     RATIO_COLS,
    "deviation vs normal":  dev_cols,
}
col_pos = {c: i for i, c in enumerate(all_cols)}
fam_idx = {fam: np.array([col_pos[c] for c in cols]) for fam, cols in FAMILIES.items()}
mean_idx = np.array([col_pos[f"mean_{v}"] for v in VARS])
meanstd_idx = np.array([col_pos[c] for c in [f"mean_{v}" for v in VARS] + [f"std_{v}" for v in VARS]])

Xbase = feat[base_cols].to_numpy(dtype=float)
y = feat["faultNumber"].to_numpy()
groups = feat["faultNumber"].to_numpy() * 1000 + feat["simulationRun"].to_numpy()
print(f"dev runs: {len(y)} | base: {len(base_cols)} | +deviation: {len(dev_cols)} | total: {len(all_cols)}")


def make(kind, seed):
    if kind == "rf":
        return RandomForestClassifier(n_estimators=300, max_depth=20, class_weight="balanced",
                                      n_jobs=N_JOBS, random_state=seed)
    return HistGradientBoostingClassifier(learning_rate=0.05, random_state=seed)


def metrics(yt, proba, cls):
    order = np.argsort(-proba, axis=1); ranked = np.asarray(cls)[order]
    pos = (ranked == np.asarray(yt).reshape(-1, 1)).argmax(axis=1)
    return {"Recall@1": float(np.mean(pos < 1)), "Recall@3": float(np.mean(pos < 3)),
            "MRR": float(np.mean(1.0 / (pos + 1))),
            "F1macro": float(f1_score(yt, np.asarray(cls)[np.argmax(proba, axis=1)], average="macro"))}


def dev_in_fold(tri):
    normal_tr = tri[y[tri] == 0]
    nm = Xbase[normal_tr][:, mean_idx].mean(axis=0)
    ns = Xbase[normal_tr][:, mean_idx].std(axis=0) + EPS
    return (Xbase[:, mean_idx] - nm) / ns


MET = ["Recall@1", "Recall@3", "MRR", "F1macro"]
folds_all = [(seed, tri, vai) for seed in SEEDS
             for tri, vai in StratifiedGroupKFold(n_splits=K, shuffle=True, random_state=seed).split(Xbase, y, groups)]
rng = np.random.default_rng(0)
rows_out, imp_out = [], []

for kind in ["rf", "hgb"]:
    ms_folds, full_folds = [], []
    imp = {fam: [] for fam in FAMILIES}
    for seed, tri, vai in folds_all:
        # mean+std only (104)
        m1 = make(kind, seed); m1.fit(Xbase[tri][:, meanstd_idx], y[tri])
        ms_folds.append(metrics(y[vai], m1.predict_proba(Xbase[vai][:, meanstd_idx]), m1.classes_))
        # + domain families (deviation built in-fold) -> 273
        Xf = np.hstack([Xbase, dev_in_fold(tri)])
        m2 = make(kind, seed); m2.fit(Xf[tri], y[tri])
        proba2 = m2.predict_proba(Xf[vai]); full_folds.append(metrics(y[vai], proba2, m2.classes_))
        base_rec = float(np.mean(m2.classes_[np.argmax(proba2, axis=1)] == y[vai]))
        # family permutation importance on the full model
        Xva, yva = Xf[vai], y[vai]
        for fam, idx in fam_idx.items():
            drops = []
            for _ in range(R_PERM):
                Xp = Xva.copy(); perm = rng.permutation(len(vai)); Xp[:, idx] = Xp[perm][:, idx]
                rec = float(np.mean(m2.classes_[np.argmax(m2.predict_proba(Xp), axis=1)] == yva))
                drops.append(base_rec - rec)
            imp[fam].append(float(np.mean(drops)))

    def summ(folds, m): v = [d[m] for d in folds]; return np.mean(v), np.std(v)
    name = {"rf": "Random Forest (max_depth=20)", "hgb": "HistGB (lr=0.05)"}[kind]
    print(f"\n============ {name} | CV k=5, 3 seeds (5,17,42), mean +/- std | TEST SEALED ============")
    hdr = f"{'feature set':<26}" + "".join(f"{m:>16}" for m in MET); print(hdr); print("-" * len(hdr))
    for label, folds in [("mean+std only (104)", ms_folds), ("+ domain families (273)", full_folds)]:
        s = {m: summ(folds, m) for m in MET}
        print(f"{label:<26}" + "".join(f"{s[m][0]:>9.4f}+/-{s[m][1]:<4.3f}" for m in MET))
        rows_out.append({"model": name, "feature_set": label, **{m: summ(folds, m)[0] for m in MET}})
    gain = summ(full_folds, "Recall@1")[0] - summ(ms_folds, "Recall@1")[0]
    print(f"  -> Recall@1 gain from domain features: {gain:+.4f}")

    ranked = sorted(((fam, np.mean(v), np.std(v)) for fam, v in imp.items()), key=lambda r: -r[1])
    print(f"  family permutation importance (drop in Recall@1; mean +/- std over folds):")
    for fam, mu, sd in ranked:
        print(f"    {fam:<24}{len(FAMILIES[fam]):>4}c  {mu:>8.4f}+/-{sd:<5.3f}")
        imp_out.append({"model": name, "family": fam, "n_cols": len(FAMILIES[fam]),
                        "perm_importance_mean": mu, "perm_importance_std": sd})

pd.DataFrame(rows_out).to_csv(os.path.join(RES, "domain_nonlinear_comparison.csv"), index=False)
pd.DataFrame(imp_out).to_csv(os.path.join(RES, "domain_nonlinear_importance.csv"), index=False)
env = {"python": platform.python_version(), "numpy": np.__version__, "pandas": pd.__version__,
       "scikit-learn": sklearn.__version__, "cv": f"StratifiedGroupKFold k={K}", "seeds": SEEDS,
       "models": ["RandomForest max_depth=20 n_est=300", "HistGB lr=0.05"], "perm_repeats": R_PERM}
with open(os.path.join(RES, "domain_nonlinear_env.json"), "w", encoding="utf-8") as f:
    json.dump(env, f, indent=2)
print("\nsaved: results/domain_nonlinear_comparison.csv, domain_nonlinear_importance.csv, domain_nonlinear_env.json")
print("versions:", env)
