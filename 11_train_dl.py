r"""
The first deep-learning row of Table II, under the pre-registered contract.

Everything here was fixed in PROTOCOLO.md ("Week 3 pre-registration") BEFORE this
script was written or run. Nothing below may be retuned after seeing a score.

Two networks, on purpose:
  v1a MLP    on the SAME 104 features the classics received  -> isolates ARCHITECTURE
  v1b 1D-CNN on the RAW causal window 20 x 52 sensors        -> isolates REPRESENTATION

THE SIX RULES (each one is marked [R#] where it is enforced in the code):
  [R1] Same frozen partition as Week 2: same cache, same seed, same grouping by run.
  [R2] Standardization fit INSIDE the fold, on the training portion only. No augmentation.
  [R3] Early stopping looks at validation, never at test. Test files are never opened.
  [R4] Three seeds, mean +- std. The seed also fixes weight initialization.
  [R5] Same search effort as each classic: 3 pre-declared configurations.
  [R6] Cost recorded in the same run: parameters, training seconds, inference ms, machine.

Outputs: results/dl_comparison.csv, results/errors/dl_confusion_matrix.csv,
         results/dl_env.json,
and one loss curve per estimation run in results/curves/.
"""
import os, json, time, platform, copy
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.model_selection import StratifiedGroupKFold, train_test_split
from sklearn.metrics import f1_score, confusion_matrix
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE = r"C:\Users\melvi\Documents\Maestria\19. Seminario de Tesis II\Anteproyecto - Seminario II"
DATA = os.path.join(BASE, "dataverse_files")
RES = os.path.join(BASE, "results")
ERR = os.path.join(RES, "errors")
os.makedirs(ERR, exist_ok=True)
CURVES = os.path.join(RES, "curves")
os.makedirs(CURVES, exist_ok=True)
# One trained model per fold and seed, so the agent scores WITHOUT retraining and
# without leakage: each fold is scored by the model fitted on its own training
# portion. Saving a single model fitted on the whole pool would leak every
# validation run into its own training set.
MODELS = os.path.join(RES, "models")
os.makedirs(MODELS, exist_ok=True)

# ---------------- pre-registered constants (PROTOCOLO.md, do not change) ----------------
VARS = [f"xmeas_{i}" for i in range(1, 42)] + [f"xmv_{i}" for i in range(1, 12)]
ONSET, W = 21, 20                 # causal window [21, 41), 20 steps x 52 sensors
K, SEL_SEED, EST_SEEDS = 5, 0, [5, 17, 42]
LR_GRID = [1e-2, 3e-3, 1e-3]      # [R5] 3 configurations, the same count each classic got
MAX_EPOCHS, PATIENCE, BATCH = 60, 10, 256
INNER_VAL = 0.20
CLASSES = np.arange(0, 21)
MET = ["Recall@1", "Recall@3", "MRR", "F1macro"]

# ---------------- data ----------------
feat = pd.read_parquet(os.path.join(RES, "dev_features.parquet"))
featcols = [c for c in feat.columns if c.endswith(("_mean", "_std"))]
Xtab = feat[featcols].to_numpy(np.float32)
y = feat["faultNumber"].to_numpy()
groups = feat["faultNumber"].to_numpy() * 1000 + feat["simulationRun"].to_numpy()  # [R1]

WIN_CACHE = os.path.join(RES, "dev_windows.npy")
if os.path.exists(WIN_CACHE):
    Xwin = np.load(WIN_CACHE)
    print("loaded cached raw windows:", WIN_CACHE)
else:
    import pyreadr

    def windows(fname):                      # [R3] only *_Training is ever opened
        res = pyreadr.read_r(os.path.join(DATA, fname))
        df = res[list(res.keys())[0]]
        del res
        sub = df[df["sample"].between(ONSET, ONSET + W - 1)].sort_values(
            ["faultNumber", "simulationRun", "sample"])
        n = len(sub) // W
        assert len(sub) % W == 0, "incomplete window in " + fname
        fn = sub["faultNumber"].to_numpy().reshape(n, W)
        sr = sub["simulationRun"].to_numpy().reshape(n, W)
        assert (fn == fn[:, :1]).all() and (sr == sr[:, :1]).all(), "misaligned windows"
        X = sub[VARS].to_numpy(np.float32).reshape(n, W, len(VARS))
        idx = pd.DataFrame({"faultNumber": fn[:, 0].astype(int),
                            "simulationRun": sr[:, 0].astype(int)})
        del df, sub
        return X, idx

    Xa, ia = windows("TEP_FaultFree_Training.RData")
    Xb, ib = windows("TEP_Faulty_Training.RData")
    Xall = np.concatenate([Xa, Xb])
    iall = pd.concat([ia, ib], ignore_index=True)
    # align row-for-row with the feature cache so labels and groups match exactly
    pos = iall.reset_index().set_index(["faultNumber", "simulationRun"])["index"]
    order = pos.loc[list(zip(feat["faultNumber"].astype(int),
                             feat["simulationRun"].astype(int)))].to_numpy()
    Xwin = np.ascontiguousarray(Xall[order].transpose(0, 2, 1))   # -> (N, 52, 20) channels first
    np.save(WIN_CACHE, Xwin)
    print("extracted + cached raw windows:", WIN_CACHE)

assert len(Xwin) == len(y), "window cache out of sync with the feature cache"
print(f"dev pool: {len(y)} runs | tabular: {Xtab.shape[1]} features | "
      f"raw window: {Xwin.shape[1]} sensors x {Xwin.shape[2]} steps | TEST SEALED")


# ---------------- models (exact sizes declared in PROTOCOLO.md) ----------------
def make_net(kind):
    if kind == "mlp":
        return nn.Sequential(nn.Linear(104, 64), nn.ReLU(), nn.Dropout(0.2),
                             nn.Linear(64, 32), nn.ReLU(), nn.Dropout(0.2),
                             nn.Linear(32, 21))
    return nn.Sequential(nn.Conv1d(52, 32, 5, padding=2), nn.BatchNorm1d(32), nn.ReLU(),
                         nn.Conv1d(32, 64, 3, padding=1), nn.BatchNorm1d(64), nn.ReLU(),
                         nn.AdaptiveAvgPool1d(1), nn.Flatten(), nn.Dropout(0.2),
                         nn.Linear(64, 21))


def n_params(kind):
    return sum(p.numel() for p in make_net(kind).parameters())


def standardize(kind, tr, ap):
    """[R2] statistics computed on the training portion of THIS fold only."""
    if kind == "mlp":
        m = tr.mean(0, keepdims=True)
        s = tr.std(0, keepdims=True)
    else:                                   # per channel, over runs and time
        m = tr.mean(axis=(0, 2), keepdims=True)
        s = tr.std(axis=(0, 2), keepdims=True)
    s = np.where(s < 1e-8, 1.0, s)
    return [(a - m) / s for a in ap], m, s


def rank_metrics(yt, proba):
    order = np.argsort(-proba, axis=1)
    ranked = CLASSES[order]
    pos = (ranked == np.asarray(yt).reshape(-1, 1)).argmax(axis=1)
    return {"Recall@1": float(np.mean(pos < 1)), "Recall@3": float(np.mean(pos < 3)),
            "MRR": float(np.mean(1.0 / (pos + 1))),
            "F1macro": float(f1_score(yt, CLASSES[np.argmax(proba, axis=1)], average="macro"))}


# ---------------- one fold ----------------
def run_fold(kind, lr, seed, tri, vai, tag=None, verbose=False, save_path=None):
    X = Xtab if kind == "mlp" else Xwin
    torch.manual_seed(seed)                               # [R4] the seed fixes weight init
    np.random.seed(seed)
    # [R2] inner split for early stopping, carved from the TRAINING portion only.
    # One window per run means a row-level split cannot break the group rule [R1].
    itr, iva = train_test_split(np.arange(len(tri)), test_size=INNER_VAL,
                                stratify=y[tri], random_state=seed)
    (Xtr, Xiv, Xva), mu, sd = standardize(kind, X[tri][itr],
                                          [X[tri][itr], X[tri][iva], X[vai]])
    t_tr = torch.from_numpy(np.ascontiguousarray(Xtr))
    l_tr = torch.from_numpy(y[tri][itr]).long()
    t_iv = torch.from_numpy(np.ascontiguousarray(Xiv))
    l_iv = torch.from_numpy(y[tri][iva]).long()
    t_va = torch.from_numpy(np.ascontiguousarray(Xva))

    net = make_net(kind)
    lossf = nn.CrossEntropyLoss()          # unweighted: the design is balanced
    opt = torch.optim.Adam(net.parameters(), lr=lr)
    g = torch.Generator().manual_seed(seed)
    best, best_state, wait = float("inf"), None, 0
    hist_tr, hist_iv = [], []
    t0 = time.perf_counter()
    for ep in range(MAX_EPOCHS):
        net.train()
        perm = torch.randperm(len(l_tr), generator=g)
        tot = 0.0
        for b in range(0, len(perm), BATCH):
            sel = perm[b:b + BATCH]
            opt.zero_grad()
            L = lossf(net(t_tr[sel]), l_tr[sel])
            L.backward()
            opt.step()
            tot += L.item() * len(sel)
        net.eval()
        with torch.no_grad():
            Liv = lossf(net(t_iv), l_iv).item()            # [R3] validation, never test
        hist_tr.append(tot / len(l_tr))
        hist_iv.append(Liv)
        if verbose:
            mark = "  *" if Liv < best else ""
            print(f"      ep {ep + 1:>2}/{MAX_EPOCHS}  train {hist_tr[-1]:.4f}  "
                  f"val {Liv:.4f}{mark}", flush=True)
        if Liv < best:
            best, best_state, wait = Liv, copy.deepcopy(net.state_dict()), 0
        else:
            wait += 1
            if wait >= PATIENCE:
                if verbose:
                    print(f"      early stop at epoch {ep + 1} (patience {PATIENCE})", flush=True)
                break
    train_s = time.perf_counter() - t0
    net.load_state_dict(best_state)
    net.eval()
    if save_path:
        # the standardization statistics travel with the weights, so the agent can
        # reproduce this fold's preprocessing exactly without refitting anything
        torch.save({"state_dict": net.state_dict(), "mean": mu, "std": sd,
                    "kind": kind, "lr": lr, "seed": seed, "epochs": len(hist_tr)},
                   save_path)
    with torch.no_grad():
        proba = torch.softmax(net(t_va), dim=1).numpy()    # outer fold: SCORE ONLY
    if tag:
        fig, ax = plt.subplots(figsize=(4, 2.6))
        ax.plot(hist_tr, label="training loss")
        ax.plot(hist_iv, "--", label="validation loss")
        ax.axvline(int(np.argmin(hist_iv)), color="green", ls=":", lw=0.9)
        ax.set_xlabel("epoch")
        ax.set_ylabel("loss")
        ax.set_title(tag, fontsize=8)
        ax.legend(fontsize=7, frameon=False)
        fig.tight_layout()
        fig.savefig(os.path.join(CURVES, f"curve_{tag}.png"), dpi=150)
        plt.close(fig)
    return rank_metrics(y[vai], proba), proba, train_s, len(hist_tr)


def cv_metrics(kind, lr, seed, verbose=False, tag_prefix=None, oof=None, save_models=False):
    sgkf = StratifiedGroupKFold(n_splits=K, shuffle=True, random_state=seed)   # [R1]
    out, secs, eps = [], [], []
    for f, (tri, vai) in enumerate(sgkf.split(Xtab, y, groups)):
        tag = f"{tag_prefix}_seed{seed}_fold{f}" if tag_prefix else None
        sp = (os.path.join(MODELS, f"{kind}_seed{seed}_fold{f}.pt")
              if (tag_prefix or save_models) else None)
        if verbose:
            print(f"    [{kind}] seed {seed} fold {f}", flush=True)
        m, proba, s, e = run_fold(kind, lr, seed, tri, vai, tag=tag, verbose=verbose,
                                  save_path=sp)
        out.append(m)
        secs.append(s)
        eps.append(e)
        if oof is not None:
            oof[vai] = CLASSES[np.argmax(proba, axis=1)]
    return out, secs, eps


# ---------------- [R5] selection: 3 configurations, seed 0, by macro-F1 ----------------
print("\nhyperparameter selection (seed %d, best mean macro-F1; 3 configurations per model):"
      % SEL_SEED)
best_lr = {}
for kind in ["mlp", "cnn"]:
    scored = []
    for lr in LR_GRID:
        folds, _, _ = cv_metrics(kind, lr, SEL_SEED)
        scored.append((float(np.mean([d["F1macro"] for d in folds])), lr))
        print(f"      {kind}  lr={lr:<7} macro-F1={scored[-1][0]:.4f}", flush=True)
    top = max(scored, key=lambda t: t[0])
    best_lr[kind] = top[1]
    print(f"  {kind}: lr={top[1]}  (macro-F1={top[0]:.4f})", flush=True)

# The agent selects its own fusion weight on the SAME selection seed, and it must
# score with models it did not train, so the seed-0 folds are trained once with the
# selected learning rate and saved. Without this the agent would have no models on
# seed 0 and would be forced to select on an estimation seed, which would
# contaminate the estimate.
print("\nsaving selection-seed models (seed %d) so the agent can select on it:" % SEL_SEED)
for kind in ["mlp", "cnn"]:
    cv_metrics(kind, best_lr[kind], SEL_SEED, save_models=True)
    print(f"  {kind}: 5 folds saved", flush=True)

# ---------------- [R4] estimation: 3 seeds x 5 folds = 15, mean +- std ----------------
print("\nestimation (15 folds; loss printed per epoch so the curve can be watched live):")
rows, oof_all = [], {}
for kind in ["mlp", "cnn"]:
    folds, secs, eps = [], [], []
    oof = np.full(len(y), -1)
    for s in EST_SEEDS:
        fo, se, ep = cv_metrics(kind, best_lr[kind], s, verbose=True,
                                tag_prefix=kind, oof=(oof if s == 42 else None))
        folds += fo
        secs += se
        eps += ep
    oof_all[kind] = oof
    r = {"model": kind, "lr": best_lr[kind], "params": n_params(kind),
         "epochs_median": float(np.median(eps)), "train_s_median_fold": float(np.median(secs))}
    for m in MET:
        r[f"{m}_mean"] = float(np.mean([d[m] for d in folds]))
        r[f"{m}_std"] = float(np.std([d[m] for d in folds]))
    rows.append(r)

# ---------------- [R6] cost on the full dev pool, same run, same machine ----------------
print("\ncost (full dev pool, same machine):")
for r in rows:
    kind = r["model"]
    X = Xtab if kind == "mlp" else Xwin
    itr, iva = train_test_split(np.arange(len(y)), test_size=INNER_VAL, stratify=y,
                                random_state=42)
    (Xtr, Xiv), _, _ = standardize(kind, X[itr], [X[itr], X[iva]])
    t_tr = torch.from_numpy(np.ascontiguousarray(Xtr))
    l_tr = torch.from_numpy(y[itr]).long()
    t_iv = torch.from_numpy(np.ascontiguousarray(Xiv))
    l_iv = torch.from_numpy(y[iva]).long()
    torch.manual_seed(42)
    net = make_net(kind)
    lossf = nn.CrossEntropyLoss()
    opt = torch.optim.Adam(net.parameters(), lr=r["lr"])
    g = torch.Generator().manual_seed(42)
    best, wait = float("inf"), 0
    t0 = time.perf_counter()
    for ep in range(MAX_EPOCHS):
        net.train()
        perm = torch.randperm(len(l_tr), generator=g)
        for b in range(0, len(perm), BATCH):
            sel = perm[b:b + BATCH]
            opt.zero_grad()
            L = lossf(net(t_tr[sel]), l_tr[sel])
            L.backward()
            opt.step()
        net.eval()
        with torch.no_grad():
            Liv = lossf(net(t_iv), l_iv).item()
        if Liv < best:
            best, wait = Liv, 0
        else:
            wait += 1
            if wait >= PATIENCE:
                break
    r["train_s"] = round(time.perf_counter() - t0, 3)
    Xf = standardize(kind, X, [X])[0][0]
    t_all = torch.from_numpy(np.ascontiguousarray(Xf))
    with torch.no_grad():
        for _ in range(2):
            net(t_all)
        ts = []
        for _ in range(7):
            t = time.perf_counter()
            net(t_all)
            ts.append((time.perf_counter() - t) * 1000.0)
    r["inference_ms"] = round(float(np.median(ts)) / len(y), 4)
    print(f"  {kind:<4} params {r['params']:>6}  train {r['train_s']:>8.3f} s  "
          f"inference {r['inference_ms']:.4f} ms/episode", flush=True)

df = pd.DataFrame(rows)
df.to_csv(os.path.join(RES, "dl_comparison.csv"), index=False)

# ---------------- report + the sentence (honest reporting) ----------------
cls = pd.read_csv(os.path.join(RES, "classics_cv_comparison.csv"))
cls = cls[~cls.model.str.contains("Trivial")]
bi = cls["F1macro_mean"].idxmax()
best_name = cls.loc[bi, "model"]
best_f1 = float(cls.loc[bi, "F1macro_mean"])
best_sd = float(cls.loc[bi, "F1macro_std"])

print("\n" + "=" * 96)
print("DEEP LEARNING v1  (StratifiedGroupKFold-by-run k=5, 3 seeds; mean +/- std; TEST SEALED)")
print("=" * 96)
hdr = (f"{'model':<26}" + "".join(f"{m:>18}" for m in MET)
       + f"{'params':>9}{'train s':>10}{'inf ms':>9}")
print(hdr)
print("-" * len(hdr))
for r in rows:
    label = "v1a MLP" if r["model"] == "mlp" else "v1b 1D-CNN"
    print(f"{label:<26}"
          + "".join(f"{r[m + '_mean']:>10.4f}+/-{r[m + '_std']:<5.3f}" for m in MET)
          + f"{r['params']:>9}{r['train_s']:>10.3f}{r['inference_ms']:>9.4f}")
print(f"\nbest classic: {best_name}  macro-F1 = {best_f1:.4f} +/- {best_sd:.4f}")

for r in rows:
    label = "v1a MLP" if r["model"] == "mlp" else "v1b 1D-CNN"
    d = r["F1macro_mean"] - best_f1
    pooled = max(r["F1macro_std"], best_sd)
    if abs(d) <= pooled:
        verdict = (f"does NOT differ: the gap ({d:+.4f}) is smaller than the standard "
                   f"deviation ({pooled:.4f}), so it is not a difference")
    elif d > 0:
        verdict = f"BEATS the best classic by {d:+.4f} macro-F1"
    else:
        verdict = f"does NOT beat the best classic, it falls short by {d:+.4f} macro-F1"
    print(f"  {label}: {verdict}.")

# per-class F1 of the better network, to back the "most likely cause" sentence
bk = max(rows, key=lambda r: r["F1macro_mean"])["model"]
oof = oof_all[bk]
f1c = f1_score(y, oof, average=None, labels=CLASSES)
hard = [int(c) for c in CLASSES if f1c[c] < 0.90]
easy = [int(c) for c in CLASSES if c not in hard]
pd.DataFrame(confusion_matrix(y, oof, labels=CLASSES), index=CLASSES, columns=CLASSES).to_csv(
    os.path.join(ERR, "dl_confusion_matrix.csv"))
print(f"\nout-of-fold per-class F1 (seed 42, {bk}): {len(easy)} classes at F1>=0.90 "
      f"(mean {f1c[easy].mean():.3f}), {len(hard)} hard classes (mean {f1c[hard].mean():.3f})")
print("  hard classes:", ", ".join(f"{c}:{f1c[c]:.2f}" for c in hard))

env = {"python": platform.python_version(), "torch": torch.__version__,
       "numpy": np.__version__, "cv": f"StratifiedGroupKFold k={K}", "sel_seed": SEL_SEED,
       "est_seeds": EST_SEEDS, "window": [ONSET, ONSET + W], "lr_grid": LR_GRID,
       "batch": BATCH, "max_epochs": MAX_EPOCHS, "patience": PATIENCE,
       "inner_val": INNER_VAL, "selected_lr": best_lr,
       "machine": "Intel Core i5-13420H, 12 threads, CPU only"}
with open(os.path.join(RES, "dl_env.json"), "w", encoding="utf-8") as f:
    json.dump(env, f, indent=2)
print("\nsaved: results/dl_comparison.csv, results/errors/dl_confusion_matrix.csv, dl_env.json, "
      f"and {len(rows) * len(EST_SEEDS) * K} loss curves in results/curves/")
