"""
S2 (milestone): LABEL EFFICIENCY CURVE - the measurable contribution.
Performance as a function of the number of LABELED runs, for the supervised
reference. This produces the reference line(s) against which a label-efficient
(self/semi-supervised) method must be compared once it exists (Week 3).

Task: per-run root-cause identification on TEP, 21 classes, causal window [21,41),
features = mean+std of the 52 process variables (cached by 04_classics_cv.py).

Protocol (same audited contract as 04/07):
  - StratifiedGroupKFold by run, k=5, seed 42. Test SEALED (dev pool only).
  - For each fold: the training portion has 400 runs/class. We subsample B labeled
    runs per class from it, fit on ONLY those, and evaluate on the fold's FULL
    validation set (so every budget is scored on the same 2100 runs per fold).
  - The labeled subset is drawn with a declared seed BEFORE looking at any score
    (leakage-control rule: never pick the labeled subset by performance).
  - Preprocessing (StandardScaler) is fit inside each fold on the labeled subset only.
  - Budgets B per class: 1..400; B=400 is full supervision and anchors the right end.

Models: logistic regression (C=10), random forest (max_depth=20) and gradient
boosting (lr=0.05) - the three configurations selected in 04. Reporting all three
answers a real question: does the model ranking hold in the low-label regime, or
does it flip?

Outputs: results/label_efficiency_curve.csv, .svg (dependency-free figure),
label_efficiency_env.json. Console: table, ASCII curve, and the headline
"labels needed to reach 90%/95% of full supervision".
"""
import os, json, platform, warnings
N_JOBS = -1  # all cores; no thermal cap (laptop holds ~60-65 C under full load)
import numpy as np
import pandas as pd
import sklearn
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.metrics import f1_score
from sklearn.exceptions import ConvergenceWarning, UndefinedMetricWarning

# At tiny budgets the model is degenerate BY CONSTRUCTION (e.g. 1 sample/class):
# it may not converge, and F1 is undefined for classes it never predicts. Both are
# expected at that end of the curve, not bugs - silence them so the log stays readable.
warnings.filterwarnings("ignore", category=ConvergenceWarning)
warnings.filterwarnings("ignore", category=UndefinedMetricWarning)

BASE = r"C:\Users\melvi\Documents\Maestria\19. Seminario de Tesis II\Anteproyecto - Seminario II"
RES = os.path.join(BASE, "results")
CACHE = os.path.join(RES, "dev_features.parquet")
assert os.path.exists(CACHE), "run 04_classics_cv.py first (needs results/dev_features.parquet)"

K = 5
BUDGETS = [1, 2, 5, 10, 20, 50, 100, 200, 400]   # labeled runs PER CLASS
SEEDS = [5, 17, 42]                              # CV repetition seeds; each also seeds its labeled-subset draw
CLASSES = np.arange(0, 21)
MET = ["Recall@1", "Recall@3", "MRR", "F1macro"]

feat = pd.read_parquet(CACHE)
featcols = [c for c in feat.columns if c.endswith(("_mean", "_std"))]
X = feat[featcols].to_numpy(dtype=float)
y = feat["faultNumber"].to_numpy()
groups = feat["faultNumber"].to_numpy() * 1000 + feat["simulationRun"].to_numpy()
print(f"dev pool: {len(y)} runs | features: {len(featcols)} | classes: {len(CLASSES)} | TEST SEALED")


def make(kind, seed):
    if kind == "logistic":
        return LogisticRegression(max_iter=2000, class_weight="balanced", C=10.0)
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


def sample_labeled(tri, budget, rng):
    """Pick `budget` labeled runs per class from this fold's training portion."""
    picked = []
    for c in CLASSES:
        idx_c = tri[y[tri] == c]
        take = min(budget, len(idx_c))
        picked.append(rng.choice(idx_c, size=take, replace=False))
    return np.concatenate(picked)


ref_splits = list(StratifiedGroupKFold(n_splits=K, shuffle=True, random_state=SEEDS[0]).split(X, y, groups))
max_per_class = min(int((y[tri] == c).sum()) for tri, _ in ref_splits for c in CLASSES)
print(f"training runs available per class in each fold: {max_per_class}")

rows = []
for kind in ["logistic", "rf", "hgb"]:
    for B in BUDGETS:
        acc = {m: [] for m in MET}
        for s in SEEDS:
            sgkf = StratifiedGroupKFold(n_splits=K, shuffle=True, random_state=s)
            for f, (tri, vai) in enumerate(sgkf.split(X, y, groups)):
                rng = np.random.default_rng(1000 * s + f)      # declared, fixed before scoring
                lab = sample_labeled(tri, B, rng)
                sc = StandardScaler().fit(X[lab])              # fit on labeled subset only
                clf = make(kind, seed=s).fit(sc.transform(X[lab]), y[lab])
                p = clf.predict_proba(sc.transform(X[vai]))
                for m, v in metrics(y[vai], p, clf.classes_).items():
                    acc[m].append(v)
        n_lab = B * len(CLASSES)
        row = {"model": kind, "budget_per_class": B, "labeled_runs": n_lab,
               "pct_of_dev_labels": 100.0 * n_lab / (max_per_class * len(CLASSES)),
               "n_measurements": len(acc["Recall@1"])}
        for m in MET:
            row[f"{m}_mean"] = float(np.mean(acc[m])); row[f"{m}_std"] = float(np.std(acc[m]))
        rows.append(row)
        print(f"  {kind:<8} B={B:>3}/class ({n_lab:>5} labels, {row['pct_of_dev_labels']:5.1f}%) "
              f"Recall@1 = {row['Recall@1_mean']:.4f} +/- {row['Recall@1_std']:.3f}")

df = pd.DataFrame(rows)
df.to_csv(os.path.join(RES, "label_efficiency_curve.csv"), index=False)

# ---------------- headline: how few labels reach X% of full supervision ----------------
TRIVIAL = 1.0 / 21.0
print("\n" + "=" * 94)
print("LABEL EFFICIENCY CURVE  (StratifiedGroupKFold-by-run k=5, 3 seeds (5,17,42); mean +/- std; TEST SEALED)")
print("=" * 94)
summary = {}
for kind in ["logistic", "rf", "hgb"]:
    d = df[df.model == kind].sort_values("budget_per_class")
    full = float(d[d.budget_per_class == max_per_class]["Recall@1_mean"].iloc[0])
    summary[kind] = {"full_supervision_Recall@1": full}
    print(f"\n{kind.upper()}  (full supervision = {full:.4f} at {max_per_class}/class)")
    print(f"  {'B/class':>8}{'labels':>8}{'% labels':>10}{'Recall@1':>18}{'% of full':>11}")
    for _, r in d.iterrows():
        print(f"  {int(r.budget_per_class):>8}{int(r.labeled_runs):>8}{r.pct_of_dev_labels:>9.1f}%"
              f"{r['Recall@1_mean']:>11.4f}+/-{r['Recall@1_std']:<5.3f}{100*r['Recall@1_mean']/full:>10.1f}%")
    for frac in (0.90, 0.95):
        hit = d[d["Recall@1_mean"] >= frac * full]
        if len(hit):
            h = hit.iloc[0]
            summary[kind][f"labels_for_{int(frac*100)}pct"] = int(h.labeled_runs)
            print(f"  -> reaches {int(frac*100)}% of full supervision with {int(h.budget_per_class)} labeled runs/class "
                  f"({int(h.labeled_runs)} labels = {h.pct_of_dev_labels:.1f}% of the labels)")

# ---------------- ASCII curve (immediate visual) ----------------
print("\nASCII curve - Recall@1 vs labeled runs per class (scale 0 to 0.70)")
for kind in ["logistic", "rf", "hgb"]:
    d = df[df.model == kind].sort_values("budget_per_class")
    print(f"  [{kind}]")
    for _, r in d.iterrows():
        bar = "#" * int(round(50 * r["Recall@1_mean"] / 0.70))
        print(f"    B={int(r.budget_per_class):>3}/class {r['Recall@1_mean']:.3f} |{bar}")
print(f"  trivial floor = {TRIVIAL:.4f} |{'#' * int(round(50 * TRIVIAL / 0.70))}")

# ---------------- SVG figure (no external plotting library available) ----------------
W, H = 760, 460
ML, MR, MT, MB = 78, 150, 34, 62
PW, PH = W - ML - MR, H - MT - MB
YMAX = 0.75
COLORS = {"logistic": "#2e7d32", "rf": "#c1531a", "hgb": "#1f5fa8"}
LBL = {"logistic": "Logistic regression (C 10)", "rf": "Random forest (depth 20)",
       "hgb": "Gradient boosting (lr 0.05)"}


def sx(b):
    return ML + PW * (np.log10(b) / np.log10(max_per_class))


def sy(v):
    return MT + PH * (1.0 - v / YMAX)


svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
       f'font-family="Georgia, serif" font-size="12">',
       f'<rect width="{W}" height="{H}" fill="#ffffff"/>']
svg.append(f'<text x="{ML}" y="20" font-size="14" font-weight="bold" fill="#111">'
           f'Label efficiency: root-cause identification on TEP</text>')
# y grid + labels
for v in np.arange(0, YMAX + 1e-9, 0.1):
    yy = sy(v)
    svg.append(f'<line x1="{ML}" y1="{yy:.1f}" x2="{ML+PW}" y2="{yy:.1f}" stroke="#e6e6e6"/>')
    svg.append(f'<text x="{ML-10}" y="{yy+4:.1f}" text-anchor="end" fill="#444">{v:.1f}</text>')
# x ticks
for b in BUDGETS:
    xx = sx(b)
    svg.append(f'<line x1="{xx:.1f}" y1="{MT}" x2="{xx:.1f}" y2="{MT+PH}" stroke="#f2f2f2"/>')
    svg.append(f'<text x="{xx:.1f}" y="{MT+PH+18}" text-anchor="middle" fill="#444">{b}</text>')
svg.append(f'<line x1="{ML}" y1="{MT+PH}" x2="{ML+PW}" y2="{MT+PH}" stroke="#333"/>')
svg.append(f'<line x1="{ML}" y1="{MT}" x2="{ML}" y2="{MT+PH}" stroke="#333"/>')
svg.append(f'<text x="{ML+PW/2:.0f}" y="{H-22}" text-anchor="middle" fill="#111">'
           f'Labeled runs per class (log scale)</text>')
svg.append(f'<text transform="translate(20,{MT+PH/2:.0f}) rotate(-90)" text-anchor="middle" fill="#111">'
           f'Recall@1</text>')
# trivial floor
yf = sy(TRIVIAL)
svg.append(f'<line x1="{ML}" y1="{yf:.1f}" x2="{ML+PW}" y2="{yf:.1f}" stroke="#999" '
           f'stroke-dasharray="5,4"/>')
svg.append(f'<text x="{ML+PW+8}" y="{yf+4:.1f}" fill="#777">trivial floor {TRIVIAL:.3f}</text>')
# series
for kind in ["logistic", "rf", "hgb"]:
    d = df[df.model == kind].sort_values("budget_per_class")
    xs = [sx(b) for b in d.budget_per_class]
    ms = list(d["Recall@1_mean"]); ss = list(d["Recall@1_std"])
    band = " ".join(f"{x:.1f},{sy(m+s):.1f}" for x, m, s in zip(xs, ms, ss))
    band += " " + " ".join(f"{x:.1f},{sy(m-s):.1f}" for x, m, s in zip(reversed(xs), reversed(ms), reversed(ss)))
    svg.append(f'<polygon points="{band}" fill="{COLORS[kind]}" fill-opacity="0.13"/>')
    line = " ".join(f"{x:.1f},{sy(m):.1f}" for x, m in zip(xs, ms))
    svg.append(f'<polyline points="{line}" fill="none" stroke="{COLORS[kind]}" stroke-width="2.2"/>')
    for x, m in zip(xs, ms):
        svg.append(f'<circle cx="{x:.1f}" cy="{sy(m):.1f}" r="3.2" fill="{COLORS[kind]}"/>')
    full = ms[-1]
    svg.append(f'<line x1="{ML}" y1="{sy(full):.1f}" x2="{ML+PW}" y2="{sy(full):.1f}" '
               f'stroke="{COLORS[kind]}" stroke-width="1" stroke-dasharray="3,4" stroke-opacity="0.6"/>')
# legend
ly = MT + 12
for kind in ["logistic", "rf", "hgb"]:
    svg.append(f'<line x1="{ML+PW+10}" y1="{ly}" x2="{ML+PW+34}" y2="{ly}" stroke="{COLORS[kind]}" stroke-width="2.2"/>')
    svg.append(f'<text x="{ML+PW+38}" y="{ly+4}" fill="#222" font-size="11">{LBL[kind]}</text>')
    ly += 20
svg.append(f'<text x="{ML+PW+10}" y="{ly+6}" fill="#666" font-size="10">dashed = full supervision</text>')
svg.append('</svg>')
svg_path = os.path.join(RES, "label_efficiency_curve.svg")
with open(svg_path, "w", encoding="utf-8") as f:
    f.write("\n".join(svg))

env = {"python": platform.python_version(), "numpy": np.__version__, "pandas": pd.__version__,
       "scikit-learn": sklearn.__version__, "cv": f"StratifiedGroupKFold k={K}", "cv_seeds": SEEDS,
       "budgets_per_class": BUDGETS, "subset_draw": "rng(1000*seed+fold)", "window": [21, 41],
       "summary": summary}
with open(os.path.join(RES, "label_efficiency_env.json"), "w", encoding="utf-8") as f:
    json.dump(env, f, indent=2)
print(f"\nsaved: results/label_efficiency_curve.csv, label_efficiency_curve.svg, label_efficiency_env.json")
print("NOTE: this is the SUPERVISED REFERENCE line. The label-efficient (self/semi-supervised)")
print("      method is the second line and requires the Week-3 model; it is not plotted yet.")
