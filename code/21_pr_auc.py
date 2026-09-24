"""PR-AUC for every row of Table II, under the same protocol as the rest.

Asked for because the metric appears in the advisor's example and this study does
not compute it. On 21 balanced classes it is reported as the macro-averaged
average precision, one class against the rest, which is the area under the
precision-recall curve estimated without interpolation.

It is scored fold by fold on the same partition, the same 5 folds and the same
three seeds, so it can be read beside the macro-F1 of Table II and compared the
same way. The test set is not touched.

Where each score vector comes from:
  - the trivial floor   class priors of the training portion, constant per fold
  - the three classics  refitted with the configuration selected on seed 0
  - the two networks    the checkpoints saved by 11_train_dl.py, not retrained
  - the agent arms      results/agent_scores.npz, the fused vector the agent
                        ranked with, saved by 12_agente_v1.py

Reads:  results/dev_features.parquet, results/dev_windows.npy,
        results/models/*.pt, results/agent_scores.npz
Writes: results/pr_auc.csv, results/pr_auc_per_fold.csv
"""
import os
import json

import numpy as np
import pandas as pd
import torch
from torch import nn
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.metrics import average_precision_score, f1_score

BASE = os.path.dirname(os.path.abspath(__file__))
if not os.path.isfile(os.path.join(BASE, "requirements.txt")):
    BASE = os.path.dirname(BASE)      # the scripts live in code/, the project one level up
RES = os.path.join(BASE, "results")
MODELS = os.path.join(RES, "models")
K, SEEDS, CLASSES = 5, [5, 17, 42], np.arange(21)
N_JOBS = -1

# the configurations selected on seed 0, as 04_classics_cv.py reports them
CFG = {"logistic": {"C": 10.0}, "rf": {"max_depth": 20}, "hgb": {"learning_rate": 0.05}}

feat = pd.read_parquet(os.path.join(RES, "dev_features.parquet"))
y = feat["faultNumber"].to_numpy()
groups = y * 1000 + feat["simulationRun"].to_numpy()
# float32, where 04 and 14 fit the classics in float64: the refits here differ in
# the last digits, so their f1_mean_here matches Table II to about the third decimal
Xtab = feat[[c for c in feat.columns if c.endswith(("_mean", "_std"))]].to_numpy(np.float32)
Xwin = np.load(os.path.join(RES, "dev_windows.npy"))
Z = np.load(os.path.join(RES, "agent_scores.npz"), allow_pickle=True)


def macro_ap(yt, proba):
    """Average precision per class against the rest, averaged over the classes
    present in this fold. A class absent from the fold has no curve to compute."""
    present = [c for c in CLASSES if (yt == c).any()]
    return float(np.mean([average_precision_score((yt == c).astype(int), proba[:, c])
                          for c in present]))


def make_est(name, seed):
    p = CFG[name]
    if name == "logistic":
        clf = LogisticRegression(max_iter=2000, class_weight="balanced", C=p["C"])
    elif name == "rf":
        clf = RandomForestClassifier(n_estimators=300, max_depth=p["max_depth"],
                                     class_weight="balanced", n_jobs=N_JOBS,
                                     random_state=seed)
    else:
        clf = HistGradientBoostingClassifier(learning_rate=p["learning_rate"],
                                             random_state=seed)
    return Pipeline([("sc", StandardScaler()), ("clf", clf)])


def make_net(kind):
    if kind == "mlp":
        return nn.Sequential(nn.Linear(104, 64), nn.ReLU(), nn.Dropout(0.2),
                             nn.Linear(64, 32), nn.ReLU(), nn.Dropout(0.2),
                             nn.Linear(32, 21))
    return nn.Sequential(nn.Conv1d(52, 32, 5, padding=2), nn.BatchNorm1d(32), nn.ReLU(),
                         nn.Conv1d(32, 64, 3, padding=1), nn.BatchNorm1d(64), nn.ReLU(),
                         nn.AdaptiveAvgPool1d(1), nn.Flatten(), nn.Dropout(0.2),
                         nn.Linear(64, 21))


def net_proba(kind, seed, fold, vai):
    ck = torch.load(os.path.join(MODELS, "%s_seed%d_fold%d.pt" % (kind, seed, fold)),
                    weights_only=False)
    net = make_net(kind)
    net.load_state_dict(ck["state_dict"])
    net.eval()
    X = (Xtab if kind == "mlp" else Xwin)[vai]
    X = (X - ck["mean"]) / ck["std"]
    with torch.no_grad():
        return torch.softmax(net(torch.from_numpy(X.astype(np.float32))), 1).numpy()


ROWS = {"Trivial": "floor", "Logistic reg.": "classic", "Random forest": "classic",
        "Gradient boost.": "classic", "v1a MLP": "net", "v1b 1D-CNN": "net",
        "No agent (abl.)": "agent", "Copilot v1": "agent"}
KEY = {"Logistic reg.": "logistic", "Random forest": "rf", "Gradient boost.": "hgb",
       "v1a MLP": "mlp", "v1b 1D-CNN": "cnn",
       "No agent (abl.)": "ablation", "Copilot v1": "proposed"}

per_fold = []
for seed in SEEDS:
    sgkf = StratifiedGroupKFold(n_splits=K, shuffle=True, random_state=seed)
    for fold, (tri, vai) in enumerate(sgkf.split(Xtab, y, groups)):
        yt = y[vai]
        for name, kind in ROWS.items():
            if kind == "floor":
                prior = np.bincount(y[tri], minlength=21).astype(float)
                proba = np.tile(prior / prior.sum(), (len(vai), 1))
            elif kind == "classic":
                est = make_est(KEY[name], seed).fit(Xtab[tri], y[tri])
                proba = np.zeros((len(vai), 21))
                proba[:, est.named_steps["clf"].classes_] = est.predict_proba(Xtab[vai])
            elif kind == "net":
                proba = net_proba(KEY[name], seed, fold, vai)
            else:
                m = (Z["arm"] == KEY[name]) & (Z["seed"] == seed) & (Z["fold"] == fold)
                idx = Z["idx"][m]
                order = np.argsort(idx)                  # the agent logged in fold order
                assert np.array_equal(np.sort(idx), np.sort(vai)), \
                    "%s seed %d fold %d: the episodes do not match the fold" % (name, seed, fold)
                proba = Z["score"][m][order]
                yt_agent = Z["y"][m][order]
                yt_here = y[np.sort(vai)]
                assert np.array_equal(yt_agent, yt_here), "labels out of order"
                per_fold.append({"seed": seed, "fold": fold, "model": name,
                                 "pr_auc": macro_ap(yt_here, proba),
                                 "f1": float(f1_score(yt_here, proba.argmax(1),
                                                      average="macro"))})
                continue
            per_fold.append({"seed": seed, "fold": fold, "model": name,
                             "pr_auc": macro_ap(yt, proba),
                             "f1": float(f1_score(yt, proba.argmax(1), average="macro"))})
        print("  seed %2d fold %d done" % (seed, fold), flush=True)

pf = pd.DataFrame(per_fold)
pf.to_csv(os.path.join(RES, "pr_auc_per_fold.csv"), index=False)

out = []
for name in ROWS:
    d = pf[pf.model == name]
    by_seed = d.groupby("seed")["pr_auc"].mean()
    out.append({"model": name,
                "pr_auc_mean": round(float(d.pr_auc.mean()), 4),
                "pr_auc_std_over_folds": round(float(d.pr_auc.std(ddof=0)), 4),
                "pr_auc_std_over_seeds": round(float(by_seed.std(ddof=0)), 4),
                "f1_mean_here": round(float(d.f1.mean()), 4)})
res = pd.DataFrame(out)
res.to_csv(os.path.join(RES, "pr_auc.csv"), index=False)

print()
print(res.to_string(index=False))
print()
print("wrote results/pr_auc.csv and results/pr_auc_per_fold.csv")
print("Chance level for 21 balanced classes is 1/21 = %.4f." % (1 / 21))
print("f1_mean_here is a control: it should match the macro-F1 of Table II to")
print("about the third decimal for every row (the classics are refitted here on")
print("float32 features, which moves the last digits), and it is what says the")
print("score vectors are the right ones.")
