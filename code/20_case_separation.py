"""
How far apart the costly cases are, in sigmas of normal operation.

For each pair of the three episodes, reports the largest difference in any of the
52 variables in sigmas of normal operation, using the alarm limits of seed 5,
fold 0, which is where all three episodes were decided, and the same distance
restricted to the variables that crossed the band, which is what the copilot
acted on.

Two control rows put those distances on a scale: 300 random pairs drawn on the
same simulation run, and 300 drawn from two runs of one fault. Their columns hold
medians, not maxima, which results/errors/README.md spells out.

A figure of the three windows was built and dropped: two of its three panels came
out visually identical, because two of the episodes really are almost the same
data. The number says it better.

The last section takes the same question to its limit: runs whose window is
byte-identical to the normal run with the same number, how many there are per
fault, the ceiling they put on Recall@1, and what the proposed copilot did with
them.

Reads:  results/dev_features.parquet, results/dev_windows_ext.npy,
        results/logs/decisiones.jsonl
Writes: results/errors/case_separation.csv, results/errors/twin_runs.csv,
        results/errors/twin_runs_summary.csv
"""
import os
import json

import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedGroupKFold

BASE = os.path.dirname(os.path.abspath(__file__))
if not os.path.isfile(os.path.join(BASE, "requirements.txt")):
    BASE = os.path.dirname(BASE)      # the scripts live in code/, the project one level up
RES = os.path.join(BASE, "results")
ERR = os.path.join(RES, "errors")
os.makedirs(ERR, exist_ok=True)

VARS = [f"xmeas_{i}" for i in range(1, 42)] + [f"xmv_{i}" for i in range(1, 12)]
W, MOVE, ALARM_K, K, SEED, FOLD = 20, 10, 3.0, 5, 5, 0
PAIRS_PER_CONTROL = 300

CASES = [(15, 12), (18, 37), (9, 12)]

feat = pd.read_parquet(os.path.join(RES, "dev_features.parquet"))
y = feat["faultNumber"].to_numpy()
groups = y * 1000 + feat["simulationRun"].to_numpy()
rid = feat[["faultNumber", "simulationRun"]].astype(int).to_numpy()
Xtab = feat[[c for c in feat.columns if c.endswith(("_mean", "_std"))]].to_numpy(np.float32)
X = np.load(os.path.join(RES, "dev_windows_ext.npy"))

# the limits of seed 5 fold 0, fitted on the normal runs of its training portion
tri = list(StratifiedGroupKFold(K, shuffle=True, random_state=SEED).split(Xtab, y, groups))[FOLD][0]
nor = tri[y[tri] == 0]
m = X[nor][:, :, :W].mean(axis=(0, 2))
s = X[nor][:, :, :W].std(axis=(0, 2))
Z = (X - m[None, :, None]) / s[None, :, None]

idx = lambda f, r: int(np.flatnonzero((rid[:, 0] == f) & (rid[:, 1] == r))[0])


def alarmed(i):
    """The variables that crossed the band in either window, as the agent sees it."""
    a = set()
    for off in (0, MOVE):
        seg = Z[i][:, off:off + W]
        a |= set(np.flatnonzero((np.abs(seg) > ALARM_K).any(axis=1)))
    return sorted(a)


rows = []
for a in range(len(CASES)):
    for b in range(a + 1, len(CASES)):
        ia, ib = idx(*CASES[a]), idx(*CASES[b])
        d = np.abs(Z[ia] - Z[ib]).max(axis=1)
        both = sorted(set(alarmed(ia)) | set(alarmed(ib)))
        rows.append({
            "pair": "IDV(%d)[%d] vs IDV(%d)[%d]" % (CASES[a] + CASES[b]),
            "same_run": int(CASES[a][1] == CASES[b][1]),
            "max_sigma_all_52": round(float(d.max()), 4),
            "max_sigma_alarmed": round(float(d[both].max()), 4),
            "min_sigma_alarmed": round(float(d[both].min()), 4),
            "widest_variable": VARS[int(np.argmax(d))],
        })

# the two controls, which is where the first reading of this went wrong
rng = np.random.default_rng(0)
same_run, same_fault = [], []
while len(same_run) < PAIRS_PER_CONTROL:
    r = int(rng.integers(1, 501))
    f1, f2 = rng.choice(21, 2, replace=False)
    a = np.flatnonzero((rid[:, 0] == f1) & (rid[:, 1] == r))
    b = np.flatnonzero((rid[:, 0] == f2) & (rid[:, 1] == r))
    if len(a) and len(b):
        same_run.append(float(np.abs(Z[a[0]] - Z[b[0]]).max()))
while len(same_fault) < PAIRS_PER_CONTROL:
    f = int(rng.integers(0, 21))
    r1, r2 = rng.choice(np.arange(1, 501), 2, replace=False)
    a = np.flatnonzero((rid[:, 0] == f) & (rid[:, 1] == r1))
    b = np.flatnonzero((rid[:, 0] == f) & (rid[:, 1] == r2))
    if len(a) and len(b):
        same_fault.append(float(np.abs(Z[a[0]] - Z[b[0]]).max()))

for name, v in (("control: two faults, same run", same_run),
                ("control: one fault, two runs", same_fault)):
    v = np.array(v)
    rows.append({
        "pair": "%s (n=%d)" % (name, len(v)),
        "same_run": int("same run" in name),
        "max_sigma_all_52": round(float(np.median(v)), 4),   # median, not max, for a control
        "max_sigma_alarmed": round(float(np.percentile(v, 10)), 4),
        "min_sigma_alarmed": round(float(np.percentile(v, 90)), 4),
        "widest_variable": "share under 2 sigma: %.0f%%" % (100 * float((v < 2).mean())),
    })

out = pd.DataFrame(rows)
out.to_csv(os.path.join(ERR, "case_separation.csv"), index=False)
print(out.to_string(index=False))
print()
print("For the control rows the three sigma columns are median, p10 and p90,")
print("not a maximum: they describe a distribution, not one pair.")
print("\nwrote results/errors/case_separation.csv")


# ---------------- twin runs: separation exactly zero ----------------
# Rieth et al. seed each simulation run by its number, the same in every class, so
# a fault that has not yet reached any of the 52 variables leaves its run
# byte-identical to the normal run with the same number. Those episodes cannot be
# told apart by any model that reads the window, which puts a ceiling on Recall@1.
# Measured on the raw windows, in the window that is scored and in the one the
# observe action moves to.
def twin_groups(A):
    """Group runs whose window is byte-identical; keep only groups of two or more."""
    keys = pd.Series([np.ascontiguousarray(A[i]).tobytes() for i in range(len(A))])
    size = keys.map(keys.value_counts()).to_numpy()
    return keys, size > 1


windows = {"scored [21,41)": X[:, :, :W], "moved [31,51)": X[:, :, MOVE:MOVE + W]}
twin_of, summary = {}, []
for name, A in windows.items():
    keys, tw = twin_groups(A)
    n_groups = int((keys[tw].value_counts() > 1).sum())
    lost = int(tw.sum()) - n_groups             # one run per group can be right
    twin_of[name] = tw
    summary += [(name, "runs in twin groups", int(tw.sum())),
                (name, "twin groups", n_groups),
                (name, "ceiling on Recall@1 for any model", round(1 - lost / len(y), 4))]

per_fault = []
for f in sorted(set(y[twin_of["scored [21,41)"]]) - {0}):
    sel = y == f
    per_fault.append({"fault": int(f), "runs": int(sel.sum()),
                      "twin_scored_window": int(twin_of["scored [21,41)"][sel].sum()),
                      "twin_moved_window": int(twin_of["moved [31,51)"][sel].sum())})
pd.DataFrame(per_fault).to_csv(os.path.join(ERR, "twin_runs.csv"), index=False)

# what the proposed copilot did with them, from the decision log of step 12
TWIN = {tuple(k) for k in rid[twin_of["scored [21,41)"]].tolist()}
cnt = {True: np.zeros(4), False: np.zeros(4)}  # episodes, deferred, window moved, top-1 right
with open(os.path.join(RES, "logs", "decisiones.jsonl"), encoding="utf-8") as fh:
    for line in fh:
        z = json.loads(line)
        if z["arm"] != "proposed":
            continue
        cnt[tuple(z["id"]) in TWIN] += [1, z["decide"]["accion"] == "defer",
                                        z["costo"]["iteraciones"] == 2,
                                        z["decide"]["top3"][0] == z["label"]]
for twin, label in ((True, "twin episodes"), (False, "other episodes")):
    n, dfr, mov, ok = cnt[twin]
    summary += [("proposed arm, " + label, "episodes (three seeds)", int(n)),
                ("proposed arm, " + label, "share deferred", round(dfr / n, 4)),
                ("proposed arm, " + label, "share that moved the window", round(mov / n, 4)),
                ("proposed arm, " + label, "top-1 correct", round(ok / n, 4))]
summ = pd.DataFrame(summary, columns=["scope", "measure", "value"], dtype=object)  # counts stay integers
summ.to_csv(os.path.join(ERR, "twin_runs_summary.csv"), index=False)

print("\n" + pd.DataFrame(per_fault).to_string(index=False))
print("\n" + summ.to_string(index=False))
print("\nwrote results/errors/twin_runs.csv and results/errors/twin_runs_summary.csv")
