"""
S2 - Prompt 2: domain-knowledge features for TEP root-cause identification.
Task: per-run 21-class diagnosis (0=normal, 1-20=fault/IDV), decided on the causal
early window [onset, onset+20) (3-min sampling -> ~60 min of data, 20 samples).

Physics recap (why these features): the TEP is a closed-loop chemical plant
(reactor / condenser / separator / recycle compressor / stripper). A fault shows up
(a) as a DEVIATION of the 52 variables from normal operation, and (b) because the
loop is closed, as COMPENSATING controller action on the manipulated valves (XMV).
Faults differ in HOW the signature appears: sustained offset, inflated variability,
slow drift, transient excursion, or a specific loop working harder.

Seven domain feature families (5-12, as asked), all calculable at 3-min sampling:
  1. level      (window mean)            -> steady operating point; feed/composition
                                            steps shift levels (e.g. IDV1,2,6).
  2. fluctuation (window std)            -> random-variation faults inflate variance
                                            (e.g. IDV8,10,11,12).
  3. trend      (linear slope / sample)  -> slow-drift faults ramp a variable
                                            (e.g. IDV13 kinetics drift).
  4. range      (max - min)              -> transient excursion right after onset
                                            (step faults jump).
  5. deviation  (z vs TRAIN-normal)      -> how far / which way each var moved from
                                            nominal; most directly diagnostic. Baseline
                                            computed ONLY from training-fold normal runs.
  6. control effort (mean |dXMV|)        -> valve activity; in closed loop a fault is
                                            counteracted by valves moving (which loop?).
  7. feed/flow ratios                    -> mass-balance couplings a fault breaks:
                                            A/(A+C) feed ratio (targets IDV1), purge/recycle.

NOT computable at this sampling/resolution (declared, not faked):
  - Frequency-domain features (FFT / dominant oscillation frequency): 3-min sampling
    gives Nyquist = 1/6 min^-1 and a 20-sample window gives ~1/60 min^-1 resolution,
    far too coarse to characterize oscillation spectra reliably.
  - Fast valve-stiction limit-cycle metrics (IDV14/15 chatter): the cycles are faster
    than a 3-min sample; we can only see the slow envelope (captured by std/range/effort).
  - Lead-lag cross-correlation between coupled variables: 20 samples with 3-min lag
    resolution makes lag estimates too noisy to trust.

Protocol (same contract as Prompts 1-2): partition by run, StratifiedGroupKFold-by-run
k=5 (seed 42), preprocessing + normal-baseline fit INSIDE each fold, test SEALED.
Reports: (a) CV metrics of domain features vs mean+std-only ablation on identical folds;
(b) family-level permutation importance (mean +/- std over folds); (c) leakage audit.
"""
import os, json, platform
N_JOBS = -1  # all cores; no thermal cap (laptop holds ~60-65 C under full load)
import numpy as np
import pandas as pd
import pyreadr
import sklearn
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.metrics import f1_score

BASE = os.path.dirname(os.path.abspath(__file__))
if not os.path.isfile(os.path.join(BASE, "requirements.txt")):
    BASE = os.path.dirname(BASE)      # the scripts live in code/, the project one level up
DATA = os.path.join(BASE, "dataverse_files")
RES = os.path.join(BASE, "results"); os.makedirs(RES, exist_ok=True)

XMEAS = [f"xmeas_{i}" for i in range(1, 42)]
XMV = [f"xmv_{i}" for i in range(1, 12)]
VARS = XMEAS + XMV
ONSET, W = 21, 20
K, SEEDS, C_LOGREG = 5, [5, 17, 42], 10.0
CLASSES = np.arange(0, 21)
EPS = 1e-9
# window index t = 0..19 (constant per run): sums for the closed-form slope
N_W, T_SUM, T2_SUM = W, 190, 2470
SLOPE_DEN = N_W * T2_SUM - T_SUM ** 2  # = 13300

# ---------------- base features (split-independent, cached) ----------------
FEAT_CACHE = os.path.join(RES, "dev_domain_features.parquet")
if os.path.exists(FEAT_CACHE):
    feat = pd.read_parquet(FEAT_CACHE)
    print("loaded cached domain features:", FEAT_CACHE)
else:
    def base_features_from_file(fname):
        res = pyreadr.read_r(os.path.join(DATA, fname)); df = res[list(res.keys())[0]]; del res
        sub = df[df["sample"].between(ONSET, ONSET + W - 1)].copy()
        keys = ["faultNumber", "simulationRun"]
        sub = sub.sort_values(keys + ["sample"])
        sub["tt"] = (sub["sample"] - ONSET).astype(float)  # 0..19
        # mean / std / max / min in one pass
        agg = sub.groupby(keys)[VARS].agg(["mean", "std", "max", "min"])
        mean_df = agg.xs("mean", axis=1, level=1).add_prefix("mean_")
        std_df = agg.xs("std", axis=1, level=1).add_prefix("std_")
        rng_df = (agg.xs("max", axis=1, level=1) - agg.xs("min", axis=1, level=1)).add_prefix("range_")
        # slope (units per 3-min sample): (n*S_tx - S_t*S_x) / (n*S_t2 - S_t^2)
        tx = sub[VARS].multiply(sub["tt"], axis=0); tx[keys] = sub[keys].values
        txsum = tx.groupby(keys)[VARS].sum()
        xsum = sub.groupby(keys)[VARS].sum()
        slope_df = ((N_W * txsum - T_SUM * xsum) / SLOPE_DEN).add_prefix("slope_")
        # control effort: mean absolute successive difference of the XMV within the window
        d = sub.groupby(keys)[XMV].diff().abs()
        d[keys] = sub[keys].values
        eff_df = d.groupby(keys).mean().add_prefix("effort_")
        out = pd.concat([mean_df, std_df, rng_df, slope_df, eff_df], axis=1).reset_index().copy()
        del df, sub, agg, tx, d
        return out

    feat = pd.concat([base_features_from_file("TEP_FaultFree_Training.RData"),
                      base_features_from_file("TEP_Faulty_Training.RData")], ignore_index=True)
    # feed/flow ratios from window means (mass-balance couplings), safe division.
    # Build via concat (not per-column insert) to avoid DataFrame fragmentation.
    ratios = pd.DataFrame({
        "ratio_A_over_AC": feat["mean_xmeas_1"] / (feat["mean_xmeas_4"] + EPS),        # targets IDV1
        "ratio_purge_recycle": feat["mean_xmeas_10"] / (feat["mean_xmeas_5"] + EPS),
    })
    feat = pd.concat([feat, ratios], axis=1).copy()
    feat["faultNumber"] = feat["faultNumber"].astype(int)
    feat["simulationRun"] = feat["simulationRun"].astype(int)
    feat = feat.fillna(0.0)  # std of a flat signal, etc.
    feat.to_parquet(FEAT_CACHE)
    print("extracted + cached domain features:", FEAT_CACHE)

# ---------------- column bookkeeping / families ----------------
RATIO_COLS = ["ratio_A_over_AC", "ratio_purge_recycle"]
base_cols = ([f"mean_{v}" for v in VARS] + [f"std_{v}" for v in VARS] +
             [f"range_{v}" for v in VARS] + [f"slope_{v}" for v in VARS] +
             [f"effort_{v}" for v in XMV] + RATIO_COLS)
dev_cols = [f"dev_{v}" for v in VARS]
all_cols = base_cols + dev_cols
FAMILIES = {
    "level (mean)":            [f"mean_{v}" for v in VARS],
    "fluctuation (std)":       [f"std_{v}" for v in VARS],
    "range (max-min)":         [f"range_{v}" for v in VARS],
    "trend (slope)":           [f"slope_{v}" for v in VARS],
    "control effort (XMV)":    [f"effort_{v}" for v in XMV],
    "feed/flow ratios":        RATIO_COLS,
    "deviation vs normal":     dev_cols,
}
col_pos = {c: i for i, c in enumerate(all_cols)}
fam_idx = {fam: np.array([col_pos[c] for c in cols]) for fam, cols in FAMILIES.items()}
mean_idx = np.array([col_pos[f"mean_{v}"] for v in VARS])  # to build dev in-fold

Xbase = feat[base_cols].to_numpy(dtype=float)
y = feat["faultNumber"].to_numpy()
groups = feat["faultNumber"].to_numpy() * 1000 + feat["simulationRun"].to_numpy()
meanstd_idx = np.array([col_pos[c] for c in [f"mean_{v}" for v in VARS] + [f"std_{v}" for v in VARS]])
print(f"dev runs: {len(y)} | base features: {len(base_cols)} | +deviation: {len(dev_cols)} "
      f"| total: {len(all_cols)} | families: {len(FAMILIES)}")


def metrics(yt, proba, cls):
    order = np.argsort(-proba, axis=1); ranked = np.asarray(cls)[order]
    pos = (ranked == np.asarray(yt).reshape(-1, 1)).argmax(axis=1)
    return {"Recall@1": float(np.mean(pos < 1)), "Recall@3": float(np.mean(pos < 3)),
            "MRR": float(np.mean(1.0 / (pos + 1))),
            "F1macro": float(f1_score(yt, np.asarray(cls)[np.argmax(proba, axis=1)], average="macro"))}


def fit_logreg(Xtr, ytr):
    sc = StandardScaler().fit(Xtr)
    clf = LogisticRegression(max_iter=3000, class_weight="balanced", C=C_LOGREG)
    clf.fit(sc.transform(Xtr), ytr)
    return sc, clf


def top1(sc, clf, X, yt):
    p = clf.predict_proba(sc.transform(X))
    return float(np.mean(clf.classes_[np.argmax(p, axis=1)] == yt))


# ---------------- CV: domain features vs mean+std ablation + permutation importance ----------------
# repeated CV: K folds x 3 seeds {5,17,42} (protocol repetitions), same scheme as 04
folds_all = [(tri, vai) for seed in SEEDS
             for tri, vai in StratifiedGroupKFold(n_splits=K, shuffle=True, random_state=seed).split(Xbase, y, groups)]
rng = np.random.default_rng(0)
R_PERM = 5
dom_folds, ms_folds = [], []
imp_acc = {fam: [] for fam in FAMILIES}

for tri, vai in folds_all:
    # deviation feature: baseline from TRAINING-FOLD NORMAL runs only (no leakage)
    normal_tr = tri[y[tri] == 0]
    nm = Xbase[normal_tr][:, mean_idx].mean(axis=0)
    ns = Xbase[normal_tr][:, mean_idx].std(axis=0) + EPS
    dev_all = (Xbase[:, mean_idx] - nm) / ns
    Xfull = np.hstack([Xbase, dev_all])

    # (b) domain features (all 325)
    sc, clf = fit_logreg(Xfull[tri], y[tri])
    proba = clf.predict_proba(sc.transform(Xfull[vai]))
    dom_folds.append(metrics(y[vai], proba, clf.classes_))
    base_rec = float(np.mean(clf.classes_[np.argmax(proba, axis=1)] == y[vai]))

    # (a) ablation: mean+std only (104) on the SAME fold
    scm, clfm = fit_logreg(Xbase[tri][:, meanstd_idx], y[tri])
    pm = clfm.predict_proba(scm.transform(Xbase[vai][:, meanstd_idx]))
    ms_folds.append(metrics(y[vai], pm, clfm.classes_))

    # family-level permutation importance on the validation fold (drop in Recall@1)
    Xva = Xfull[vai]; yva = y[vai]
    for fam, idx in fam_idx.items():
        drops = []
        for _ in range(R_PERM):
            Xp = Xva.copy()
            perm = rng.permutation(len(vai))
            Xp[:, idx] = Xp[perm][:, idx]
            drops.append(base_rec - top1(sc, clf, Xp, yva))
        imp_acc[fam].append(float(np.mean(drops)))


def summ(folds, metric):
    v = [d[metric] for d in folds]; return np.mean(v), np.std(v)

MET = ["Recall@1", "Recall@3", "MRR", "F1macro"]
print("\n============ CV (StratifiedGroupKFold-by-run k=5, 3 seeds (5,17,42); mean +/- std; TEST SEALED) ============")
hdr = f"{'feature set':<28}" + "".join(f"{m:>16}" for m in MET); print(hdr); print("-" * len(hdr))
for label, folds in [("mean+std only (Prompt 1)", ms_folds), ("+ domain families (7)", dom_folds)]:
    mu = {m: summ(folds, m) for m in MET}
    print(f"{label:<28}" + "".join(f"{mu[m][0]:>9.4f}+/-{mu[m][1]:<4.3f}" for m in MET))

imp_rows = sorted(([fam, np.mean(v), np.std(v)] for fam, v in imp_acc.items()), key=lambda r: -r[1])
print("\n---- family permutation importance (drop in Recall@1 when that family is shuffled; mean +/- std over folds) ----")
print(f"{'domain feature family':<26}{'n_cols':>8}{'importance':>16}")
for fam, mu, sd in imp_rows:
    print(f"{fam:<26}{len(FAMILIES[fam]):>8}{mu:>10.4f}+/-{sd:<5.3f}")
pd.DataFrame([{"family": f, "n_cols": len(FAMILIES[f]), "perm_importance_mean": mu, "perm_importance_std": sd}
              for f, mu, sd in imp_rows]).to_csv(os.path.join(RES, "domain_feature_importance.csv"), index=False)

# ---------------- leakage audit (Prompt point 4) ----------------
print("\n---- leakage audit (future / label information) ----")
print("SAFE (built only from the causal window [21,41) and/or training-fold normal runs):")
print("  level, fluctuation, range, trend, control effort, feed/flow ratios -> all within-window, no future used.")
print("  deviation vs normal -> baseline (nm, ns) computed ONLY from training-fold NORMAL runs, inside each fold.")
print("  StandardScaler fit on the training fold only (inside the pipeline).")
print("RISKS AVOIDED (would leak if done differently):")
print("  - full-run statistics (would import post-decision future) -> NOT used; window ends at sample 40.")
print("  - baseline/scaling computed on all data incl. val/test -> NOT done; recomputed per fold from train.")
print("  - known fault onset (1h/8h) as a feature -> NOT used; onset only places the window, same for all runs.")
print("NOT COMPUTED at this sampling/resolution (declared, not faked): frequency-domain features,")
print("  fast valve-stiction limit-cycle metrics, lead-lag cross-correlation (see module docstring).")

env = {"python": platform.python_version(), "numpy": np.__version__, "pandas": pd.__version__,
       "scikit-learn": sklearn.__version__, "cv": f"StratifiedGroupKFold k={K}", "seeds": SEEDS,
       "model": f"LogisticRegression C={C_LOGREG}", "window": [ONSET, ONSET + W], "perm_repeats": R_PERM}
with open(os.path.join(RES, "domain_features_env.json"), "w", encoding="utf-8") as f:
    json.dump(env, f, indent=2)
print("\nsaved: results/domain_feature_importance.csv, domain_features_env.json")
print("versions:", env)
