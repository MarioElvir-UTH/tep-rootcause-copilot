"""
S2: model cost - training time (seconds) + inference latency (ms) for Table II.

Both are REPRODUCIBLE measures (rule 2):
  - train_s: median wall-clock seconds to fit one model on the development pool.
  - inference_ms: median time to score ONE episode, AMORTIZED over a full batch
    (median batch-predict time / batch size). Amortizing removes the single-call
    Python overhead that made a one-episode timing jump run-to-run, so this number
    reproduces; it is the model's per-episode inference compute.
Models: logistic regression, random forest, and gradient boosting; plus the trivial
floor. Fit on the mean+std features from 04's cache; test untouched.
"""
import os, json, time, platform
import numpy as np
import pandas as pd
import sklearn
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier

BASE = r"C:\Users\melvi\Documents\Maestria\19. Seminario de Tesis II\Anteproyecto - Seminario II"
RES = os.path.join(BASE, "results")
CACHE = os.path.join(RES, "dev_features.parquet")
assert os.path.exists(CACHE), "run 04_classics_cv.py first (needs results/dev_features.parquet)"
SEED, TRAIN_REPS, INFER_REPS = 42, 3, 7

feat = pd.read_parquet(CACHE)
featcols = [c for c in feat.columns if c.endswith(("_mean", "_std"))]
X = feat[featcols].to_numpy(dtype=float)
y = feat["faultNumber"].to_numpy()
CLASSES = np.arange(0, 21)
print(f"dev pool: {len(y)} runs | features: {len(featcols)}")


def make_logistic():
    return Pipeline([("sc", StandardScaler()),
                     ("clf", LogisticRegression(max_iter=2000, class_weight="balanced", C=10.0))])
def make_rf():
    return Pipeline([("sc", StandardScaler()),
                     ("clf", RandomForestClassifier(n_estimators=300, max_depth=20, class_weight="balanced",
                                                    n_jobs=-1, random_state=SEED))])
def make_hgb():
    return Pipeline([("sc", StandardScaler()),
                     ("clf", HistGradientBoostingClassifier(learning_rate=0.05, random_state=SEED))])


def train_seconds(make_est, reps=TRAIN_REPS):
    ts = []
    for _ in range(reps):
        est = make_est()
        t = time.perf_counter(); est.fit(X, y); ts.append(time.perf_counter() - t)
    return float(np.median(ts))


def trivial_fit_seconds():
    t = time.perf_counter()
    np.array([(y == c).sum() for c in CLASSES], float)  # "training" = class frequencies
    return time.perf_counter() - t


def amortized_ms_per_episode(predict_batch, reps=INFER_REPS):
    for _ in range(2):
        predict_batch(X)                          # warm up
    ts = []
    for _ in range(reps):
        t = time.perf_counter(); predict_batch(X); ts.append((time.perf_counter() - t) * 1000.0)
    return float(np.median(ts)) / len(X)          # ms per episode


# --- training time (median seconds to fit one model on the dev pool) ---
tr_trivial = float(np.median([trivial_fit_seconds() for _ in range(5)]))
tr_log = train_seconds(make_logistic)
tr_rf = train_seconds(make_rf)
tr_hgb = train_seconds(make_hgb)

# --- inference: fit once, then amortized per-episode latency (RF single-threaded) ---
pipe_log = make_logistic().fit(X, y)
pipe_rf = make_rf().fit(X, y); pipe_rf.named_steps["clf"].n_jobs = 1
pipe_hgb = make_hgb().fit(X, y)
freq = np.array([(y == c).sum() for c in CLASSES], float); freq = freq / freq.sum()

inf_trivial = amortized_ms_per_episode(lambda Xb: np.tile(freq, (len(Xb), 1)))
inf_log = amortized_ms_per_episode(lambda Xb: pipe_log.predict_proba(Xb))
inf_rf = amortized_ms_per_episode(lambda Xb: pipe_rf.predict_proba(Xb))
inf_hgb = amortized_ms_per_episode(lambda Xb: pipe_hgb.predict_proba(Xb))

rows = [
    {"model": "Trivial (majority class)", "train_s": round(tr_trivial, 4), "inference_ms": round(inf_trivial, 4)},
    {"model": "Logistic regression",      "train_s": round(tr_log, 3),     "inference_ms": round(inf_log, 4)},
    {"model": "Random forest",            "train_s": round(tr_rf, 3),      "inference_ms": round(inf_rf, 4)},
    {"model": "Gradient boosting",        "train_s": round(tr_hgb, 3),     "inference_ms": round(inf_hgb, 4)},
]

print("\n============ MODEL COST (train seconds on dev pool + amortized inference ms/episode; median) ============")
for r in rows:
    print(f"  {r['model']:<28} train {r['train_s']:>9.3f} s | inference {r['inference_ms']:>9.4f} ms/episode")
pd.DataFrame(rows).to_csv(os.path.join(RES, "inference_time.csv"), index=False)

env = {"python": platform.python_version(), "numpy": np.__version__, "pandas": pd.__version__,
       "scikit-learn": sklearn.__version__, "seed": SEED, "train_reps": TRAIN_REPS, "infer_reps": INFER_REPS,
       "note": "train_s = median seconds to fit one model on the dev pool (RF n_jobs=-1); "
               "inference_ms = amortized ms per episode (median batch-predict time / batch size), RF single-threaded"}
with open(os.path.join(RES, "inference_time_env.json"), "w", encoding="utf-8") as f:
    json.dump(env, f, indent=2)
print("\nsaved: results/inference_time.csv, inference_time_env.json")
