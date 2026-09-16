"""How far apart the costly cases are, in sigmas of normal operation.

A figure of the three windows was built and dropped: two of the three panels came
out visually identical, because two of the episodes really are almost the same
data. The number says it better than the picture, so this script produces the
number instead.

For each pair of the three episodes it reports the largest difference in any of
the 52 variables, in sigmas of normal operation, using the alarm limits of the
fold each episode was decided in. It also reports the same distance restricted to
the variables that crossed the band, which is what the copilot acted on.

Two controls are included because the first reading of this was wrong. Sharing a
simulation-run index does NOT generally make two episodes alike: over 300 random
pairs the median separation between two faults on the same run is larger than
between two runs of the same fault. What is true is that the low tail belongs
entirely to same-run pairs, and the two confusing episodes sit in it.

Reads:  results/dev_features.parquet, results/dev_windows_ext.npy
Writes: results/errors/case_separation.csv
"""
import os

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
