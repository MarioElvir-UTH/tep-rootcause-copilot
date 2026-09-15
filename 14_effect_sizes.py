r"""
Paired fold-by-fold differences and effect sizes for every comparison the paper makes.

Four rules this script exists to satisfy (Week 4):
  1. Same seeds, same folds. The difference is computed fold by fold and then
     averaged by seed, never by subtracting two loose means.
  2. The effect size is reported: Cohen's d = difference / pooled standard deviation.
  3. With three seeds almost nothing is "significant"; the paired t is reported
     with its degrees of freedom so the reader can see how little it settles.
  4. The word "significant" is never used without a test and a p-value.

Nothing is retrained. The three scripts that produced the results build the folds
identically (groups = faultNumber*1000 + simulationRun, StratifiedGroupKFold k=5,
shuffle, random_state=seed), so fold f of seed s is the same set of runs everywhere:
  - classics  -> refit on the cached features, which is cheap
  - networks  -> scored from the checkpoint saved for that fold, never retrained
  - agent arms-> read straight out of results/logs/decisiones.jsonl

Outputs:
  results/per_fold_f1.csv    <- macro-F1 of every model on every one of the 15 folds
  results/effect_sizes.csv   <- one row per declared comparison
"""
import os
import json
import numpy as np
import pandas as pd
import torch
from torch import nn
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.metrics import f1_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier

BASE = r"C:\Users\melvi\Documents\Maestria\19. Seminario de Tesis II\Anteproyecto - Seminario II"
RES = os.path.join(BASE, "results")
MODELS = os.path.join(RES, "models")
LOG = os.path.join(RES, "logs", "decisiones.jsonl")
K, EST_SEEDS = 5, [5, 17, 42]
CLASSES = np.arange(21)
N_JOBS = -1

for p in (os.path.join(RES, "dev_features.parquet"), os.path.join(RES, "dev_windows.npy"),
          MODELS, LOG):
    assert os.path.exists(p), "missing %s: run the pipeline first" % p

feat = pd.read_parquet(os.path.join(RES, "dev_features.parquet"))
featcols = [c for c in feat.columns if c.endswith(("_mean", "_std"))]
X = feat[featcols].to_numpy()
y = feat["faultNumber"].to_numpy()
groups = feat["faultNumber"].to_numpy() * 1000 + feat["simulationRun"].to_numpy()
Xwin = np.load(os.path.join(RES, "dev_windows.npy"))
print("dev runs: %d | features: %d | window: %s" % (len(y), len(featcols), Xwin.shape[1:]))

# selected configurations, as recorded by 04 and 11
BEST = {"logistic": {"C": 10.0}, "rf": {"max_depth": 20}, "hgb": {"learning_rate": 0.05}}
LR = json.load(open(os.path.join(RES, "dl_env.json"), encoding="utf-8"))["selected_lr"]


def make_est(name, seed):
    steps = [("sc", StandardScaler())]
    if name == "logistic":
        steps.append(("clf", LogisticRegression(max_iter=2000, class_weight="balanced",
                                                C=BEST[name]["C"])))
    elif name == "rf":
        steps.append(("clf", RandomForestClassifier(n_estimators=300, max_depth=BEST[name]["max_depth"],
                                                    class_weight="balanced", n_jobs=N_JOBS,
                                                    random_state=seed)))
    else:
        steps.append(("clf", HistGradientBoostingClassifier(learning_rate=BEST[name]["learning_rate"],
                                                            random_state=seed)))
    return Pipeline(steps)


def make_net(kind):
    if kind == "mlp":
        return nn.Sequential(nn.Linear(104, 64), nn.ReLU(), nn.Dropout(0.2),
                             nn.Linear(64, 32), nn.ReLU(), nn.Dropout(0.2),
                             nn.Linear(32, 21))
    return nn.Sequential(nn.Conv1d(52, 32, 5, padding=2), nn.BatchNorm1d(32), nn.ReLU(),
                         nn.Conv1d(32, 64, 3, padding=1), nn.BatchNorm1d(64), nn.ReLU(),
                         nn.AdaptiveAvgPool1d(1), nn.Flatten(), nn.Dropout(0.2),
                         nn.Linear(64, 21))


def net_f1(kind, seed, fold, vai):
    """Score the checkpoint saved for this fold. Its standardization is reused, never refitted."""
    ck = torch.load(os.path.join(MODELS, "%s_seed%d_fold%d.pt" % (kind, seed, fold)),
                    weights_only=False)
    net = make_net(kind)
    net.load_state_dict(ck["state_dict"])
    net.eval()
    A = (X if kind == "mlp" else Xwin)[vai]
    t = torch.from_numpy(np.ascontiguousarray((A - ck["mean"]) / ck["std"])).float()
    with torch.no_grad():
        proba = torch.softmax(net(t), dim=1).numpy()
    return float(f1_score(y[vai], CLASSES[np.argmax(proba, axis=1)], average="macro"))


# ---------------- agent arms, straight from the decision log ----------------
print("reading the decision log ...")
agent = {}
with open(LOG, encoding="utf-8") as fh:
    for line in fh:
        r = json.loads(line)
        agent.setdefault((r["arm"], r["seed"], r["fold"]), [[], []])
        agent[(r["arm"], r["seed"], r["fold"])][0].append(r["label"])
        agent[(r["arm"], r["seed"], r["fold"])][1].append(r["decide"]["top3"][0])
ARMS = sorted({k[0] for k in agent})
print("arms in the log: %s" % ", ".join(ARMS))

# ---------------- per-fold macro-F1 for every model ----------------
PF = os.path.join(RES, "per_fold_f1.csv")
CACHED = (os.path.exists(PF) and set(pd.read_csv(PF).columns) >=
          {"seed", "fold", "trivial", "logistic", "rf", "hgb", "mlp", "cnn"} | set(ARMS))

rows = []
for seed in ([] if CACHED else EST_SEEDS):
    sgkf = StratifiedGroupKFold(n_splits=K, shuffle=True, random_state=seed)
    for fold, (tri, vai) in enumerate(sgkf.split(X, y, groups)):
        rec = {"seed": seed, "fold": fold}
        # trivial: the most frequent training class, ranked by frequency
        top = np.bincount(y[tri], minlength=21).argmax()
        rec["trivial"] = float(f1_score(y[vai], np.full(len(vai), top), average="macro"))
        for name in ("logistic", "rf", "hgb"):
            est = make_est(name, seed).fit(X[tri], y[tri])
            cls = est.named_steps["clf"].classes_
            pred = cls[np.argmax(est.predict_proba(X[vai]), axis=1)]
            rec[name] = float(f1_score(y[vai], pred, average="macro"))
        for kind in ("mlp", "cnn"):
            rec[kind] = net_f1(kind, seed, fold, vai)
        for arm in ARMS:
            yt, yp = agent[(arm, seed, fold)]
            rec[arm] = float(f1_score(np.array(yt), np.array(yp), average="macro"))
        rows.append(rec)
        print("  seed %2d fold %d  " % (seed, fold)
              + "  ".join("%s %.4f" % (k, rec[k]) for k in ("logistic", "cnn", "ablation", "proposed")))

if CACHED:
    per_fold = pd.read_csv(PF)
    print("reusing results/per_fold_f1.csv (delete it to refit the classics from scratch)")
else:
    per_fold = pd.DataFrame(rows)
    per_fold.to_csv(PF, index=False)
    print("\nwrote results/per_fold_f1.csv  (%d folds x %d models)"
          % (len(per_fold), len(per_fold.columns) - 2))


# ---------------- explanation quality, per fold, from the same log ----------------
# The point of the ablation is that these are a SEPARATE result from the classifier
# F1: documents are expected to move the root-cause rubric and to leave the ranking
# alone. Reported per fold so the difference can be paired like any other.
KB = json.load(open(os.path.join(BASE, "kb", "tep_kb.json"), encoding="utf-8"))
DOCS = {d["clase"]: d for d in KB["documentos"]}
NAME_OF = {d["nombre"]: d["clase"] for d in KB["documentos"]}
VAR_OF = {c: set(DOCS[c]["variables_documentadas"]) for c in DOCS}
DOCUMENTED = {c for c, d in DOCS.items() if d["causa_documentada"] and c != 0}

expl = {}
with open(LOG, encoding="utf-8") as fh:
    for line in fh:
        r = json.loads(line)
        k = (r["arm"], r["seed"], r["fold"])
        e = expl.setdefault(k, {"chrono": [], "kb": [], "r2": [], "r3": []})
        y = r["label"]
        if y in DOCUMENTED:
            for src, key in (("raiz_cronologica", "chrono"), ("raiz_conocimiento", "kb")):
                v = r["percibe"][src]
                if v:
                    e[key].append(v in VAR_OF[y])
        rz = r["razona"]
        if rz and rz.get("docs"):
            cited = [NAME_OF.get(n, -1) for n in rz["docs"]]
            e["r2"].append(cited[0] == y)
            e["r3"].append(y in cited[:3])

mean = lambda v: float(np.mean(v)) if v else float("nan")
for (arm, seed, fold), e in expl.items():
    m = (per_fold.seed == seed) & (per_fold.fold == fold)
    per_fold.loc[m, "rootchrono_" + arm] = mean(e["chrono"])
    per_fold.loc[m, "rootkb_" + arm] = mean(e["kb"])
    per_fold.loc[m, "grounding_" + arm] = (mean(e["r2"]) + mean(e["r3"])) if e["r2"] else float("nan")
per_fold.to_csv(PF, index=False)
print("added per-fold root-alarm and grounding for %d arms" % len(ARMS))

# ---------------- the declared comparisons ----------------
COMPARISONS = [
    ("cnn", "logistic", "the convolutional network against the best classic"),
    ("mlp", "logistic", "the perceptron against the best classic, at equal input"),
    ("cnn", "mlp", "raw window against summary features"),
    ("ablation", "cnn", "the loop, against the same network scored once"),
    ("ablation", "proposed", "retrieval removed, against the proposed method"),
    ("lookup", "proposed", "label anchoring against symptom retrieval"),
    # Reading the ablation: documents are expected to move the explanation and to
    # leave the classifier alone. These two comparisons test exactly that.
    ("rootkb_lookup", "rootchrono_lookup", "root alarm: knowledge against chronology"),
    ("rootkb_proposed", "rootchrono_proposed", "root alarm: symptom retrieval against chronology"),
    ("grounding_lookup", "grounding_proposed", "grounding: label anchoring against symptom retrieval"),
]

out = []
for a, b, label in COMPARISONS:
    if a not in per_fold.columns or b not in per_fold.columns:
        continue
    # [rule 1] fold by fold, then averaged by seed
    per_fold["_d"] = per_fold[a] - per_fold[b]
    by_seed = per_fold.groupby("seed")["_d"].mean()
    diff = float(by_seed.mean())
    sd_seed = float(by_seed.std(ddof=1))
    # [rule 2] Cohen's d on the pooled standard deviation across the 15 folds
    sa, sb = per_fold[a].std(ddof=1), per_fold[b].std(ddof=1)
    pooled = float(np.sqrt((sa ** 2 + sb ** 2) / 2.0))
    d = diff / pooled if pooled > 0 else float("nan")
    # [rule 3] paired t over the three seed means, df = 2, and over the 15 folds, df = 14
    t_seed = diff / (sd_seed / np.sqrt(len(by_seed))) if sd_seed > 0 else float("nan")
    sd_fold = float(per_fold["_d"].std(ddof=1))
    t_fold = diff / (sd_fold / np.sqrt(len(per_fold))) if sd_fold > 0 else float("nan")
    # do the mean +- std intervals of the two rows overlap?
    ma, mb = per_fold[a].mean(), per_fold[b].mean()
    lo_a, hi_a, lo_b, hi_b = ma - sa, ma + sa, mb - sb, mb + sb
    overlap = not (lo_a > hi_b or lo_b > hi_a)
    out.append({
        "better": a, "worse": b, "comparison": label,
        "mean_a": round(ma, 4), "std_a": round(sa, 4),
        "mean_b": round(mb, 4), "std_b": round(sb, 4),
        "paired_diff": round(diff, 4), "std_over_seeds": round(sd_seed, 4),
        "cohens_d": round(d, 2),
        "t_seeds_df2": round(t_seed, 2), "t_folds_df14": round(t_fold, 2),
        "intervals_overlap": overlap,
        "size": ("negligible" if abs(d) < 0.2 else "small" if abs(d) < 0.5
                 else "medium" if abs(d) < 0.8 else "large"),
    })

eff = pd.DataFrame(out)
eff.to_csv(os.path.join(RES, "effect_sizes.csv"), index=False)

print("\n" + "=" * 100)
print("PAIRED DIFFERENCES AND EFFECT SIZES  (fold by fold, then averaged by seed)")
print("=" * 100)
for r in out:
    print("\n%s" % r["comparison"])
    print("  %-10s %.4f +- %.4f      %-10s %.4f +- %.4f"
          % (r["better"], r["mean_a"], r["std_a"], r["worse"], r["mean_b"], r["std_b"]))
    print("  paired difference : %+.4f  (std over the three seeds %.4f)"
          % (r["paired_diff"], r["std_over_seeds"]))
    print("  Cohen's d         : %+.2f  (%s)" % (r["cohens_d"], r["size"]))
    print("  paired t          : %.2f over seeds (df 2, threshold 4.30)   "
          "%.2f over folds (df 14, threshold 2.14)" % (r["t_seeds_df2"], r["t_folds_df14"]))
    print("  mean +- std intervals overlap: %s" % ("YES, report as comparable"
                                                   if r["intervals_overlap"] else "no"))
print("\nwrote results/effect_sizes.csv")
print("\nNote: no claim of statistical significance is made anywhere from these numbers.")
