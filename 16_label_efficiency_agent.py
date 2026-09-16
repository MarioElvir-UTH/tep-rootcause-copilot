r"""
Panel B of the main figure: how the root-cause rubric scales with the number of
labeled runs, on the same budgets as the classical curve of 08_label_efficiency.py.

The point of the figure is that the two panels can disagree. The classifier's
macro-F1 and the root-alarm rate are different results, and the number of labels
each one needs is a separate question. The chronological baseline is label-free by
construction and is drawn flat as the reference the knowledge-driven ordering has
to beat.

Everything is retrained at every budget, because that is what the question asks:
the network, the alarm limits fit on the normal runs of the labeled subset, and
the class signatures of the symptom retrieval. The subsample is drawn with the
same declared rule as 08: rng(1000*seed + fold), so a budget contains the runs
of every smaller budget.

Budgets, seeds, folds and guards are the ones already fixed; nothing here is tuned.

Output:
  results/label_efficiency_agent.csv
"""
import os
import json
import time
import numpy as np
import pandas as pd
import torch
from torch import nn
from sklearn.model_selection import StratifiedGroupKFold, train_test_split
from sklearn.metrics import f1_score

BASE = os.path.dirname(os.path.abspath(__file__))
if not os.path.isfile(os.path.join(BASE, "requirements.txt")):
    BASE = os.path.dirname(BASE)      # the scripts live in code/, the project one level up
RES = os.path.join(BASE, "results")
OUT = os.path.join(RES, "label_efficiency_agent.csv")

# every constant below is the one already declared, read from the run stamps
env = json.load(open(os.path.join(RES, "agente_env.json"), encoding="utf-8"))
dlv = json.load(open(os.path.join(RES, "dl_env.json"), encoding="utf-8"))
ALARM_K, CORR_GROUP, TAU = env["alarm_k"], env["corr_group"], env["tau"]
FLOOD_N, MOVE, MAX_MOVES = env["flood_n"], env["move"], env["max_moves"]
BEST_W = env["selected_w"]
ONSET, W = env["read_samples"][0], env["scored_steps"]
LR = dlv["selected_lr"]["cnn"]
MAX_EPOCHS, PATIENCE, BATCH, INNER_VAL = 60, 10, 256, 0.20
K, EST_SEEDS = 5, dlv["est_seeds"]
BUDGETS = [1, 2, 5, 10, 20, 40, 50, 100, 200, 400]     # labeled runs PER CLASS, as in 08
CLASSES = np.arange(21)

KB = json.load(open(os.path.join(BASE, "kb", "tep_kb.json"), encoding="utf-8"))
DOCS = {d["clase"]: d for d in KB["documentos"]}
VARS = [c[:-5] for c in pd.read_parquet(os.path.join(RES, "dev_features.parquet")).columns
        if c.endswith("_mean")]
VAR_OF = {c: set(DOCS[c]["variables_documentadas"]) for c in DOCS}
DOCUMENTED = {c for c, d in DOCS.items() if d["causa_documentada"] and c != 0}
DOCVAR = np.zeros((21, len(VARS)), np.float32)
for _c, _d in DOCS.items():
    for _v in _d["variables_documentadas"]:
        DOCVAR[_c, VARS.index(_v)] = 1.0

feat = pd.read_parquet(os.path.join(RES, "dev_features.parquet"))
y = feat["faultNumber"].to_numpy()
groups = feat["faultNumber"].to_numpy() * 1000 + feat["simulationRun"].to_numpy()
Xfull = np.load(os.path.join(RES, "dev_windows_ext.npy"))   # [onset, onset+W+MOVE)
print("dev runs: %d | extended window: %s | budgets: %s" % (len(y), Xfull.shape[1:], BUDGETS))


def slice_window(moved):
    off = MOVE if moved else 0
    return np.ascontiguousarray(Xfull[:, :, off:off + W])


def make_cnn():
    return nn.Sequential(nn.Conv1d(len(VARS), 32, 5, padding=2), nn.BatchNorm1d(32), nn.ReLU(),
                         nn.Conv1d(32, 64, 3, padding=1), nn.BatchNorm1d(64), nn.ReLU(),
                         nn.AdaptiveAvgPool1d(1), nn.Flatten(), nn.Dropout(0.2),
                         nn.Linear(64, 21))


def sample_labeled(tri, budget, rng):
    """The declared rule of 08: `budget` labeled runs per class from this fold's training portion."""
    picked = []
    for c in CLASSES:
        idx_c = tri[y[tri] == c]
        picked.append(rng.choice(idx_c, size=min(budget, len(idx_c)), replace=False))
    return np.concatenate(picked)


def train_cnn(lab, seed):
    """Train on the labeled subset only. Standardization from that subset, nothing else."""
    Xw = slice_window(False)
    torch.manual_seed(seed)
    np.random.seed(seed)
    # stratify only when the inner split can hold one run of every class; with a
    # handful of labels per class it cannot, and an unstratified draw is the honest
    # fallback rather than a crash.
    strat = y[lab] if (INNER_VAL * len(lab) >= 21 and
                       np.bincount(y[lab], minlength=21).min() >= 2) else None
    tr, va = train_test_split(lab, test_size=INNER_VAL, random_state=seed, stratify=strat)
    m = Xw[tr].mean(axis=(0, 2), keepdims=True)
    s = Xw[tr].std(axis=(0, 2), keepdims=True)
    s = np.where(s < 1e-8, 1.0, s)
    net = make_cnn()
    opt = torch.optim.Adam(net.parameters(), lr=LR)
    lossf = nn.CrossEntropyLoss()
    Xtr = torch.from_numpy(((Xw[tr] - m) / s)).float()
    ytr = torch.from_numpy(y[tr]).long()
    Xva = torch.from_numpy(((Xw[va] - m) / s)).float()
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


def proba(net, m, s, Xw):
    t = torch.from_numpy(np.ascontiguousarray((Xw - m) / s)).float()
    with torch.no_grad():
        return torch.softmax(net(t), dim=1).numpy()


def perceive(Xw, m, s):
    z = (Xw - m) / s
    over = np.abs(z) > ALARM_K
    alarming = over.any(axis=2)
    first = np.where(alarming, over.argmax(axis=2), W)
    peak = np.abs(z).max(axis=2)
    dev = (Xw.mean(axis=2) - m[0, :, 0]) / s[0, :, 0]
    return alarming, first, peak, dev


def root_hits(alarming, first, peak, dev, sig, p_ret, idx, arm_uses_retrieval):
    """Root alarm by time, and by retrieved evidence. Only on faults with a documented cause."""
    hits_c, hits_k = [], []
    for j, i in enumerate(idx):
        c = y[i]
        if c not in DOCUMENTED:
            continue
        on = np.flatnonzero(alarming[i])
        if on.size == 0:
            continue
        chrono = on[np.lexsort((-peak[i, on], first[i, on]))][0]
        hits_c.append(VARS[chrono] in VAR_OF[c])
        if arm_uses_retrieval:
            w = p_ret[j] @ DOCVAR
            kb = on[np.lexsort((first[i, on], -w[on]))][0]
        else:
            kb = chrono
        hits_k.append(VARS[kb] in VAR_OF[c])
    return (float(np.mean(hits_c)) if hits_c else np.nan,
            float(np.mean(hits_k)) if hits_k else np.nan,
            len(hits_c))


def retrieve_all(dev_v, alarming_v, sig):
    """Vectorized symptom retrieval: the query is the deviation profile restricted to alarms."""
    q = np.where(alarming_v, dev_v, 0.0)
    flat = np.linalg.norm(q, axis=1) < 1e-8
    q[flat] = dev_v[flat]
    qn = np.maximum(np.linalg.norm(q, axis=1), 1e-8)
    cos = (q @ sig.T) / (np.linalg.norm(sig, axis=1)[None, :] * qn[:, None] + 1e-12)
    e = np.exp(cos - cos.max(axis=1, keepdims=True))
    return e / e.sum(axis=1, keepdims=True)


rows = []
t_start = time.time()
for B in BUDGETS:
    t_b = time.time()
    for seed in EST_SEEDS:
        sgkf = StratifiedGroupKFold(n_splits=K, shuffle=True, random_state=seed)
        for fold, (tri, vai) in enumerate(sgkf.split(np.zeros((len(y), 1)), y, groups)):
            rng = np.random.default_rng(1000 * seed + fold)     # the declared draw of 08
            lab = sample_labeled(tri, B, rng)
            net, mu, sd = train_cnn(lab, seed)
            normal = lab[y[lab] == 0]
            pack = {}
            for moved in (False, True):
                Xw = slice_window(moved)
                m = Xw[normal].mean(axis=(0, 2), keepdims=True)
                s = np.where(Xw[normal].std(axis=(0, 2), keepdims=True) < 1e-8, 1.0,
                             Xw[normal].std(axis=(0, 2), keepdims=True))
                al, fi, pk, dv = perceive(Xw, m, s)
                sig = np.stack([dv[lab[y[lab] == c]].mean(axis=0) for c in CLASSES]).astype(np.float32)
                pack[moved] = (al, fi, pk, dv, sig, proba(net, mu, sd, Xw[vai]))
            # the network scored once on the first window, no loop and no
            # retrieval: the per-budget bar the Week 3 block declared and that
            # nothing measured. The net is already trained above, so this costs
            # one argmax.
            rows.append({"budget_per_class": B, "labeled_runs": int(len(lab)),
                         "pct_of_dev_labels": round(100.0 * len(lab) / len(tri), 4),
                         "seed": seed, "fold": fold, "arm": "cnn",
                         "F1macro": float(f1_score(y[vai],
                                                   CLASSES[pack[False][5].argmax(1)],
                                                   average="macro")),
                         "RootAlarmChrono": np.nan, "RootAlarmKB": np.nan,
                         "RootAlarm_n": 0})
            for arm in ("lookup", "proposed"):
                # the loop: observe once when the arm is not ready to commit
                al0, fi0, pk0, dv0, sig0, pc0 = pack[False]
                al1, fi1, pk1, dv1, sig1, pc1 = pack[True]
                pr0 = pc0 if arm == "lookup" else retrieve_all(dv0[vai], al0[vai], sig0)
                pr1 = pc1 if arm == "lookup" else retrieve_all(dv1[vai], al1[vai], sig1)
                w = 0.0 if arm == "lookup" else BEST_W
                top0 = pc0.argmax(1)
                conf0 = pc0.max(1)
                agree0 = (top0 == pr0.argmax(1)) if arm == "proposed" else np.ones(len(vai), bool)
                nal0 = al0[vai].sum(1)
                ready0 = agree0 & (conf0 >= TAU)
                flood0 = (top0 == 0) & (nal0 >= FLOOD_N)
                moved = ~(ready0 | flood0) & (MAX_MOVES >= 1)
                sel = lambda a, b: np.where(moved[:, None], b, a) if a.ndim == 2 else np.where(moved, b, a)
                pc = sel(pc0, pc1)
                pr = sel(pr0, pr1)
                score = (1.0 - w) * pc + w * pr
                f1 = float(f1_score(y[vai], CLASSES[score.argmax(1)], average="macro"))
                # root alarm is read on the window the episode ended on
                hc, hk, n = [], [], 0
                for state, mask in ((False, ~moved), (True, moved)):
                    if not mask.any():
                        continue
                    al, fi, pk, dv, sig, _ = pack[state]
                    idx = vai[mask]
                    a, b, c = root_hits(al, fi, pk, dv, sig, (pr1 if state else pr0)[mask], idx, True)
                    if not np.isnan(a):
                        hc.append(a * c); hk.append(b * c); n += c
                rows.append({"budget_per_class": B, "labeled_runs": int(len(lab)),
                             "pct_of_dev_labels": round(100.0 * len(lab) / len(tri), 4),
                             "seed": seed, "fold": fold, "arm": arm, "F1macro": f1,
                             "RootAlarmChrono": sum(hc) / n if n else np.nan,
                             "RootAlarmKB": sum(hk) / n if n else np.nan, "RootAlarm_n": n})
    pd.DataFrame(rows).to_csv(OUT, index=False)
    el = time.time() - t_b
    done = BUDGETS.index(B) + 1
    print("budget %3d/class done in %5.1f min   (%d of %d, elapsed %.1f min, projected total %.1f min)"
          % (B, el / 60, done, len(BUDGETS), (time.time() - t_start) / 60,
             (time.time() - t_start) / 60 / done * len(BUDGETS)), flush=True)

df = pd.DataFrame(rows)
df.to_csv(OUT, index=False)
print("\nwrote %s  (%d rows)" % (OUT, len(df)))
g = df.groupby(["arm", "pct_of_dev_labels"])[["F1macro", "RootAlarmChrono", "RootAlarmKB"]].mean()
print(g.round(4).to_string())
