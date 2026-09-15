r"""
Every cost cell of Table II, measured in one run so the eight rows are comparable.

The cost column reads size / training seconds / inference milliseconds. Before this
script only four of those twenty-four numbers came from a file: the classical
training and inference times of 10_inference_time.py. The sizes were not computed
anywhere, and the two network training times in the table contradicted
dl_comparison.csv. This script produces all of them together.

What "size" counts, per row, is what the model has to store to make a decision:
  trivial            the 21 class priors
  logistic           coefficients and intercepts
  random forest      decision nodes over the 300 trees
  gradient boosting  decision nodes over all boosted predictors
  networks           trainable parameters
  agent arms         the network, plus the per-variable alarm limits, plus the
                     retrieval structures that arm actually uses. The ablation has
                     no retrieval, so it carries neither the document-variable
                     matrix nor the class signatures; the proposed arm carries both.

Timing follows 10_inference_time.py so the numbers stay comparable with it:
  train_s        median wall-clock seconds to fit one model on the whole dev pool
  inference_ms   median batch-predict time divided by the batch, which removes the
                 single-call Python overhead and is what actually reproduces

The two agent rows train nothing: they load the network saved for each fold. Their
per-decision latency is measured by 12_agente_v1.py, which owns the loop, and is
carried here with its source named rather than re-implemented and measured twice.

Run it on an idle machine: wall-clock times move with load, which the caption says.

Output:
  results/cost_table.csv
"""
import os
import json
import time
import numpy as np
import pandas as pd
import torch
from torch import nn
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.model_selection import train_test_split

BASE = r"C:\Users\melvi\Documents\Maestria\19. Seminario de Tesis II\Anteproyecto - Seminario II"
RES = os.path.join(BASE, "results")
CACHE = os.path.join(RES, "dev_features.parquet")
assert os.path.exists(CACHE), "run 04_classics_cv.py first"

# 15 inference repetitions, not the 7 of step 10: the random forest was the one
# number that moved between runs (0.052 to 0.082 ms), and a longer median settles it.
SEED, TRAIN_REPS, INFER_REPS = 42, 3, 15
N_JOBS = -1
CLASSES = np.arange(21)

env = json.load(open(os.path.join(RES, "agente_env.json"), encoding="utf-8"))
dlv = json.load(open(os.path.join(RES, "dl_env.json"), encoding="utf-8"))
LR = dlv["selected_lr"]
MAX_EPOCHS, PATIENCE, BATCH, INNER_VAL = 60, 10, 256, 0.20

feat = pd.read_parquet(CACHE)
featcols = [c for c in feat.columns if c.endswith(("_mean", "_std"))]
X = feat[featcols].to_numpy(dtype=float)
y = feat["faultNumber"].to_numpy()
Xwin = np.load(os.path.join(RES, "dev_windows.npy"))
NVAR = Xwin.shape[1]
print("dev pool: %d runs | features: %d | window: %s" % (len(y), X.shape[1], Xwin.shape[1:]))


# ---------------------------------------------------------------- the models
def make_logistic():
    return Pipeline([("sc", StandardScaler()),
                     ("clf", LogisticRegression(max_iter=2000, class_weight="balanced", C=10.0))])


def make_rf():
    return Pipeline([("sc", StandardScaler()),
                     ("clf", RandomForestClassifier(n_estimators=300, max_depth=20,
                                                    class_weight="balanced", n_jobs=N_JOBS,
                                                    random_state=SEED))])


def make_hgb():
    return Pipeline([("sc", StandardScaler()),
                     ("clf", HistGradientBoostingClassifier(learning_rate=0.05, random_state=SEED))])


def make_net(kind):
    if kind == "mlp":
        return nn.Sequential(nn.Linear(X.shape[1], 64), nn.ReLU(), nn.Dropout(0.2),
                             nn.Linear(64, 32), nn.ReLU(), nn.Dropout(0.2),
                             nn.Linear(32, 21))
    return nn.Sequential(nn.Conv1d(NVAR, 32, 5, padding=2), nn.BatchNorm1d(32), nn.ReLU(),
                         nn.Conv1d(32, 64, 3, padding=1), nn.BatchNorm1d(64), nn.ReLU(),
                         nn.AdaptiveAvgPool1d(1), nn.Flatten(), nn.Dropout(0.2),
                         nn.Linear(64, 21))


# ---------------------------------------------------------------- the meters
def train_seconds(fit_once, reps=TRAIN_REPS):
    ts = []
    for _ in range(reps):
        t = time.perf_counter()
        fit_once()
        ts.append(time.perf_counter() - t)
    return float(np.median(ts))


def amortized_ms(predict_batch, batch, reps=INFER_REPS):
    for _ in range(2):
        predict_batch(batch)                       # warm up
    ts = []
    for _ in range(reps):
        t = time.perf_counter()
        predict_batch(batch)
        ts.append((time.perf_counter() - t) * 1000.0)
    return float(np.median(ts)) / len(batch)


def train_net(kind):
    """One fit on the whole dev pool, under the declared contract, so the seconds are
    comparable with the classics rather than with a per-fold median."""
    A = X if kind == "mlp" else Xwin
    torch.manual_seed(SEED)
    np.random.seed(SEED)
    tr, va = train_test_split(np.arange(len(y)), test_size=INNER_VAL,
                              random_state=SEED, stratify=y)
    ax = (0,) if kind == "mlp" else (0, 2)
    m = A[tr].mean(axis=ax, keepdims=True)
    s = np.where(A[tr].std(axis=ax, keepdims=True) < 1e-8, 1.0, A[tr].std(axis=ax, keepdims=True))
    net = make_net(kind)
    opt = torch.optim.Adam(net.parameters(), lr=LR[kind])
    lossf = nn.CrossEntropyLoss()
    Xtr = torch.from_numpy((A[tr] - m) / s).float()
    ytr = torch.from_numpy(y[tr]).long()
    Xva = torch.from_numpy((A[va] - m) / s).float()
    yva = torch.from_numpy(y[va]).long()
    best, best_state, bad = np.inf, None, 0
    for _ in range(MAX_EPOCHS):
        net.train()
        perm = torch.randperm(len(Xtr))
        for i in range(0, len(perm), BATCH):
            b = perm[i:i + BATCH]
            opt.zero_grad()
            lossf(net(Xtr[b]), ytr[b]).backward()
            opt.step()
        net.eval()
        with torch.no_grad():
            vl = float(lossf(net(Xva), yva))
        if vl < best - 1e-5:
            best, best_state, bad = vl, {k: v.clone() for k, v in net.state_dict().items()}, 0
        else:
            bad += 1
            if bad >= PATIENCE:
                break
    net.load_state_dict(best_state)
    net.eval()
    return net, m, s


rows = []

# ---------------------------------------------------------------- trivial
print("\nmeasuring ...")
freq = np.array([(y == c).sum() for c in CLASSES], float)
freq = freq / freq.sum()
tr_s = train_seconds(lambda: np.array([(y == c).sum() for c in CLASSES], float), reps=5)
inf = amortized_ms(lambda Xb: np.tile(freq, (len(Xb), 1)), X)
rows.append(dict(row="Trivial", size=len(CLASSES), size_is="class priors",
                 train_s=tr_s, inference_ms=inf, source="17_cost_table.py"))
print("  trivial done")

# ---------------------------------------------------------------- classics
for name, maker in (("Logistic reg.", make_logistic), ("Random forest", make_rf),
                    ("Gradient boost.", make_hgb)):
    tr_s = train_seconds(lambda mk=maker: mk().fit(X, y))
    est = maker().fit(X, y)
    clf = est.named_steps["clf"]
    if name.startswith("Logistic"):
        size = int(clf.coef_.size + clf.intercept_.size)
        what = "coefficients and intercepts"
    elif name.startswith("Random"):
        size = int(sum(e.tree_.node_count for e in clf.estimators_))
        what = "decision nodes over %d trees" % len(clf.estimators_)
    else:
        size = int(sum(p.nodes.shape[0] for stage in clf._predictors for p in stage))
        what = "decision nodes over %d boosted predictors" % sum(len(s) for s in clf._predictors)
    if name.startswith("Random"):
        clf.n_jobs = 1                              # single-threaded, as in step 10
    inf = amortized_ms(lambda Xb, e=est: e.predict_proba(Xb), X)
    rows.append(dict(row=name, size=size, size_is=what, train_s=tr_s,
                     inference_ms=inf, source="17_cost_table.py"))
    print("  %s done" % name)

# ---------------------------------------------------------------- networks
nets = {}
for kind, label in (("mlp", "v1a MLP"), ("cnn", "v1b 1D-CNN")):
    tr_s = train_seconds(lambda k=kind: train_net(k), reps=1)
    net, m, s = train_net(kind)
    nets[kind] = (net, m, s)
    size = int(sum(p.numel() for p in net.parameters()))
    A = X if kind == "mlp" else Xwin
    t = torch.from_numpy(np.ascontiguousarray((A - m) / s)).float()

    def predict(batch, n=net):
        with torch.no_grad():
            return torch.softmax(n(batch), dim=1).numpy()

    inf = amortized_ms(predict, t)
    rows.append(dict(row=label, size=size, size_is="trainable parameters",
                     train_s=tr_s, inference_ms=inf, source="17_cost_table.py"))
    print("  %s done" % label)

# ---------------------------------------------------------------- agent arms
# They load the network saved for each fold, so nothing is trained. Their latency is
# measured where the loop lives, in step 12, and is carried here with its source.
cnn_params = int(sum(p.numel() for p in nets["cnn"][0].parameters()))
limits = 2 * NVAR                                   # one mean and one sd per variable
docvar = 21 * NVAR                                  # which document names which variable
signatures = 21 * NVAR                              # one deviation profile per class
ag = pd.read_csv(os.path.join(RES, "agente_comparison.csv")).set_index("arm")
for arm, label, extra, what in (
        ("ablation", "No agent (abl.)", 0, "network and alarm limits, no retrieval"),
        ("proposed", "Copilot v1", docvar + signatures,
         "network, alarm limits, document-variable matrix and class signatures")):
    rows.append(dict(row=label, size=cnn_params + limits + extra, size_is=what,
                     train_s=0.0, inference_ms=float(ag.loc[arm, "s_per_decision"]) * 1000.0,
                     source="size here; latency from 12_agente_v1.py"))
    print("  %s done" % label)

df = pd.DataFrame(rows)
df.to_csv(os.path.join(RES, "cost_table.csv"), index=False)


def cell(r):
    """The cost column exactly as Table II prints it."""
    sz = "{:,}".format(int(r["size"]))
    # the agent rows train nothing: that is an exact zero, not a small number
    tr = "0" if r["train_s"] == 0 else ("$<$0.01" if r["train_s"] < 0.01 else "%.0f" % r["train_s"])
    inf = "$<$0.001" if r["inference_ms"] < 0.001 else "%.3f" % r["inference_ms"]
    return "%s / %s / %s" % (sz, tr, inf)


print("\n" + "=" * 92)
print("COST TABLE  (one run, idle machine; wall-clock times move with load)")
print("=" * 92)
print("%-17s %10s  %9s  %12s   %s" % ("row", "size", "train s", "inference ms", "cost cell for Table II"))
print("-" * 92)
for r in rows:
    print("%-17s %10s  %9.3f  %12.4f   %s"
          % (r["row"], "{:,}".format(int(r["size"])), r["train_s"], r["inference_ms"], cell(r)))
print("\nwrote results/cost_table.csv")
print("\nwhat size counts, row by row:")
for r in rows:
    print("  %-17s %s" % (r["row"], r["size_is"]))
