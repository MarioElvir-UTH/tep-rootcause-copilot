r"""
Opens the sealed test set once and scores on it the 15 models the validation scored.

Procedure: PROTOCOLO.md, "The procedure that opens the test set".

  python code/27_test_once.py --dev-check   scores the validation folds with this same
                                            code and compares with results/per_fold_*.csv.
                                            Never opens *_Testing. Writes nothing.
  python code/27_test_once.py               opens the test. Refuses to run unless the tree
                                            is clean, HEAD carries the tag and results/test/
                                            does not exist; then repeats the dev check and
                                            stops before reading *_Testing unless it passes.

For each seed (5, 17, 42) and fold (0-4): the classics are refit on the fold's training
portion with the same seed, the networks are the saved results/models/*_seed<S>_fold<F>.pt,
and the agent fits its alarm limits, signatures and correlation on the same portion.
Nothing is fitted on test runs.

Writes (test mode): results/test/twins.csv, test_per_fold.csv, test_summary.csv,
test_paired.csv, decisions_test.csv.gz, test_env.json.
"""
import os, sys, json, ast, time, hashlib, platform, subprocess, argparse
from datetime import datetime, timezone
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import sklearn
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.metrics import f1_score

BASE = os.path.dirname(os.path.abspath(__file__))
if not os.path.isfile(os.path.join(BASE, "requirements.txt")):
    BASE = os.path.dirname(BASE)
DATA = os.path.join(BASE, "dataverse_files")
RES = os.path.join(BASE, "results")
MODELS = os.path.join(RES, "models")
OUT = os.path.join(RES, "test")
TAG = "test-procedure"

# ---------------- frozen configuration (checked against the validation outputs below) ----------------
VARS = [f"xmeas_{i}" for i in range(1, 42)] + [f"xmv_{i}" for i in range(1, 12)]
ONSET = {"dev": 21, "test": 161}   # first faulty sample in *_Training and *_Testing
W, MOVE = 20, 10                   # 20 scored steps; observe moves the window by 10
READ = W + MOVE
PRE = 20                           # samples 1..20, before either onset (twin check)
K, EST_SEEDS = 5, [5, 17, 42]
CLASSES = np.arange(0, 21)
CLASSIC_CFG = {"logistic": {"C": 10.0}, "rf": {"max_depth": 20},
               "hgb": {"learning_rate": 0.05}}
ALARM_K, CORR_GROUP, TAU, FLOOD_N = 3.0, 0.8, 0.50, 10
FUSION_W, MAX_MOVES = 0.25, 1
ACTIONS = ["generate", "observe", "defer", "alert"]
ROWS = ["trivial", "logistic", "rf", "hgb", "mlp", "cnn", "ablation", "lookup", "proposed"]
ARMS = ["ablation", "lookup", "proposed"]


def check_frozen():
    """The constants above must be the ones validation selected and used."""
    env = json.load(open(os.path.join(RES, "agente_env.json"), encoding="utf-8"))
    assert env["alarm_k"] == ALARM_K and env["corr_group"] == CORR_GROUP
    assert env["tau"] == TAU and env["flood_n"] == FLOOD_N
    assert env["selected_w"] == FUSION_W and env["max_moves"] == MAX_MOVES
    assert env["move"] == MOVE and env["scored_steps"] == W
    assert env["read_samples"] == [ONSET["dev"], ONSET["dev"] + READ]
    dl = json.load(open(os.path.join(RES, "dl_env.json"), encoding="utf-8"))
    assert dl["selected_lr"] == {"mlp": 0.01, "cnn": 0.01}
    cl = pd.read_csv(os.path.join(RES, "classics_cv_comparison.csv"))["model"].tolist()
    sel = {m.split(" ", 1)[0]: ast.literal_eval(m.split(" ", 1)[1]) for m in cl if "{" in m}
    assert sel == CLASSIC_CFG, sel
    meta = json.load(open(os.path.join(BASE, "splits", "partition_meta.json"), encoding="utf-8"))
    assert meta["onset_first_fault_sample"] == {"train_pool": ONSET["dev"],
                                                "test_pool": ONSET["test"]}


# ---------------- guards (test mode) ----------------
def git(*args):
    r = subprocess.run(["git", *args], cwd=BASE, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"git {' '.join(args)} failed: {r.stderr.strip()}")
    return r.stdout.strip()


def guards():
    if os.path.exists(OUT):
        sys.exit("results/test/ already exists: the test has been opened. Stopping.")
    if git("status", "--porcelain"):
        sys.exit("The working tree is not clean. Commit first, then tag.")
    if TAG not in git("tag", "--points-at", "HEAD").split():
        sys.exit(f"HEAD does not carry the tag '{TAG}'. Stopping.")


def sha256(path, n=16):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()[:n]


# ---------------- development pool (cached by 04 and 12) ----------------
feat = pd.read_parquet(os.path.join(RES, "dev_features.parquet"))
FEATCOLS = [c for c in feat.columns if c.endswith(("_mean", "_std"))]
Y = feat["faultNumber"].to_numpy()
GROUPS = feat["faultNumber"].to_numpy() * 1000 + feat["simulationRun"].to_numpy()
DEV_ID = feat[["faultNumber", "simulationRun"]].astype(int).to_numpy()
DEV_X64 = feat[FEATCOLS].to_numpy()                 # classics (04) and MLP scoring (14)
DEV_X32 = feat[FEATCOLS].to_numpy(np.float32)       # fold assignment, as 11 and 12 draw it
DEV_EXT = np.load(os.path.join(RES, "dev_windows_ext.npy"))   # (N, 52, 30), what 12 saw
assert len(DEV_EXT) == len(Y)

KB = json.load(open(os.path.join(BASE, "kb", "tep_kb.json"), encoding="utf-8"))
DOCS = {d["clase"]: d for d in KB["documentos"]}
DOCUMENTED = {c for c, d in DOCS.items() if d["causa_documentada"] and c != 0}
VAR_OF = {c: set(DOCS[c]["variables_documentadas"]) for c in DOCS}
DOCVAR = np.zeros((21, 52), np.float32)
for _c, _d in DOCS.items():
    for _v in _d["variables_documentadas"]:
        DOCVAR[_c, VARS.index(_v)] = 1.0


def folds(seed):
    sgkf = StratifiedGroupKFold(n_splits=K, shuffle=True, random_state=seed)
    return list(sgkf.split(DEV_X32, Y, GROUPS))


# ---------------- test pool: read once, same layout as the development caches ----------------
def read_rdata(fname, first, last):
    import pyreadr
    res = pyreadr.read_r(os.path.join(DATA, fname))
    df = res[list(res.keys())[0]]
    del res
    sub = df[df["sample"].between(first, last)].copy()
    del df
    sub["faultNumber"] = sub["faultNumber"].astype(int)
    sub["simulationRun"] = sub["simulationRun"].astype(int)
    return sub.sort_values(["faultNumber", "simulationRun", "sample"]).reset_index(drop=True)


def to_windows(sub, first, n_steps):
    """(runs, 52, n_steps) windows and their (faultNumber, simulationRun) ids."""
    s = sub[sub["sample"].between(first, first + n_steps - 1)]
    n = len(s) // n_steps
    assert len(s) == n * n_steps, "incomplete window"
    fn = s["faultNumber"].to_numpy().reshape(n, n_steps)
    sr = s["simulationRun"].to_numpy().reshape(n, n_steps)
    assert (fn == fn[:, :1]).all() and (sr == sr[:, :1]).all(), "misaligned windows"
    smp = s["sample"].to_numpy().reshape(n, n_steps)
    assert (smp == np.arange(first, first + n_steps)).all(), "unexpected sample numbers"
    X = s[VARS].to_numpy(np.float32).reshape(n, n_steps, len(VARS)).transpose(0, 2, 1)
    return np.ascontiguousarray(X), np.stack([fn[:, 0], sr[:, 0]], axis=1)


def to_features(sub, first):
    """Mean and std over the scored window, built as 04 builds the development cache."""
    s = sub[sub["sample"].between(first, first + W - 1)]
    g = s.groupby(["faultNumber", "simulationRun"])[VARS].agg(["mean", "std"])
    g.columns = [f"{v}_{st}" for v, st in g.columns]
    g = g.reset_index()
    return g[FEATCOLS], g[["faultNumber", "simulationRun"]].to_numpy()


def load_pool(files, onset):
    sub = pd.concat([read_rdata(f, 1, onset + READ - 1) for f in files], ignore_index=True)
    feats, fid = to_features(sub, onset)
    ext, eid = to_windows(sub, onset, READ)
    pre, pid = to_windows(sub, 1, PRE)
    assert (fid == eid).all() and (eid == pid).all()
    return {"x64": feats.to_numpy(), "ext": ext, "pre": pre, "id": eid, "y": eid[:, 0]}


# ---------------- twin check: raw data only, before any model sees a test run ----------------
def twin_mask(A):
    keys = pd.Series([np.ascontiguousarray(a).tobytes() for a in A])
    return (keys.map(keys.value_counts()) > 1).to_numpy()


def twin_check(T, dev):
    dev_pre = {tuple(i): a.tobytes() for i, a in zip(dev["id"], dev["pre"])}
    dev_any = set(dev_pre.values())
    scored, moved = twin_mask(T["ext"][:, :, :W]), twin_mask(T["ext"][:, :, MOVE:MOVE + W])
    same_k = np.array([dev_pre.get(tuple(i)) == a.tobytes() for i, a in zip(T["id"], T["pre"])])
    any_k = np.array([a.tobytes() in dev_any for a in T["pre"]])
    out = []
    for c in CLASSES:
        s = T["y"] == c
        out.append({"class": int(c), "runs": int(s.sum()),
                    "twin_scored_window": int(scored[s].sum()),
                    "twin_moved_window": int(moved[s].sum()),
                    "pre_onset_equal_dev_same_number": int(same_k[s].sum()),
                    "pre_onset_equal_any_dev_run": int(any_k[s].sum())})
    return pd.DataFrame(out)


# ---------------- models ----------------
def make_est(name, seed):
    p = CLASSIC_CFG[name]
    if name == "logistic":
        clf = LogisticRegression(max_iter=2000, class_weight="balanced", C=p["C"])
    elif name == "rf":
        clf = RandomForestClassifier(n_estimators=300, max_depth=p["max_depth"],
                                     class_weight="balanced", n_jobs=-1, random_state=seed)
    else:
        clf = HistGradientBoostingClassifier(learning_rate=p["learning_rate"], random_state=seed)
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


def load_net(kind, seed, fold):
    ck = torch.load(os.path.join(MODELS, f"{kind}_seed{seed}_fold{fold}.pt"), weights_only=False)
    assert ck["seed"] == seed and ck["kind"] == kind
    net = make_net(kind)
    net.load_state_dict(ck["state_dict"])
    net.eval()
    return net, ck["mean"], ck["std"]


def net_proba(net, mean, std, X):
    t = torch.from_numpy(np.ascontiguousarray((X - mean) / std)).float()
    with torch.no_grad():
        return torch.softmax(net(t), dim=1).numpy()


def proba_metrics(yt, proba, classes):
    classes = np.asarray(classes)
    ranked = classes[np.argsort(-proba, axis=1)]
    pos = (ranked == np.asarray(yt).reshape(-1, 1)).argmax(axis=1)
    return {"F1macro": float(f1_score(yt, classes[np.argmax(proba, axis=1)], average="macro")),
            "Recall@1": float(np.mean(pos < 1)), "Recall@3": float(np.mean(pos < 3))}


# ---------------- the agent: same functions as 12_agente_v1.py ----------------
def fit_alarm_limits(Xw, idx_train):
    normal = idx_train[Y[idx_train] == 0]
    m = Xw[normal].mean(axis=(0, 2), keepdims=True)
    s = Xw[normal].std(axis=(0, 2), keepdims=True)
    return m, np.where(s < 1e-8, 1.0, s)


def perceive(Xw, m, s):
    z = (Xw - m) / s
    over = np.abs(z) > ALARM_K
    alarming = over.any(axis=2)
    first = np.where(alarming, over.argmax(axis=2), W)
    peak = np.abs(z).max(axis=2)
    dev = (Xw.mean(axis=2) - m[0, :, 0]) / s[0, :, 0]
    return alarming, first, peak, dev


def priority_order(alarming, first, peak, i):
    idx = np.flatnonzero(alarming[i])
    if idx.size == 0:
        return idx
    return idx[np.lexsort((-peak[i, idx], first[i, idx]))]


def priority_knowledge(alarming_i, first_i, p_ret):
    idx = np.flatnonzero(alarming_i)
    if idx.size == 0:
        return idx
    w = p_ret @ DOCVAR
    return idx[np.lexsort((first_i[idx], -w[idx]))]


def group_alarms(order, corr):
    kept, seen = [], set()
    for v in order:
        if v in seen:
            continue
        kept.append(v)
        seen.update(np.flatnonzero(corr[v] >= CORR_GROUP).tolist())
    return kept


def fit_signatures(dev_train, idx_train):
    sig = np.zeros((21, 52), np.float32)
    for c in CLASSES:
        sig[c] = dev_train[idx_train[Y[idx_train] == c]].mean(axis=0)
    return sig


def retrieve(dev_i, alarming_i, sig):
    used = bool(alarming_i.any())
    q = dev_i * alarming_i if used else dev_i
    qn = np.linalg.norm(q)
    if qn < 1e-8:
        q, qn = dev_i, max(np.linalg.norm(dev_i), 1e-8)
    cos = (sig @ q) / (np.linalg.norm(sig, axis=1) * qn + 1e-12)
    e = np.exp(cos - cos.max())
    return e / e.sum(), used


def decide(p_cls, p_ret, n_alarm, moved, arm, w):
    top_cls = int(np.argmax(p_cls))
    conf = float(p_cls[top_cls])
    if arm == "proposed":
        score = (1.0 - w) * p_cls + w * p_ret
        agree = top_cls == int(np.argmax(p_ret))
        ready = agree and conf >= TAU
    else:
        score, agree = p_cls, None
        ready = conf >= TAU
    if top_cls == 0 and n_alarm >= FLOOD_N:
        return "alert", score, agree
    if ready:
        return "generate", score, agree
    if not moved:
        return "observe", score, agree
    return "defer", score, agree


def agent_fold(seed, fold, tri, E):
    """The three arms on the evaluation set E. Limits, signatures and correlation come
    from the development runs of the fold's training portion."""
    net, mean, std = load_net("cnn", seed, fold)
    pack = {}
    for moved in (False, True):
        s0 = MOVE if moved else 0
        Xd, Xe = DEV_EXT[:, :, s0:s0 + W], E["ext"][:, :, s0:s0 + W]
        m, s = fit_alarm_limits(Xd, tri)
        dev_d = perceive(Xd, m, s)[3]
        sig = fit_signatures(dev_d, tri)
        corr = np.nan_to_num(np.corrcoef(dev_d[tri[Y[tri] == 0]].T))
        pack[moved] = (*perceive(Xe, m, s), sig, corr, net_proba(net, mean, std, Xe))

    out = {}
    for arm in ARMS:
        w = FUSION_W if arm == "proposed" else 0.0
        rows = []
        for i in range(len(E["y"])):
            moved, iters = False, 0
            while True:
                iters += 1
                alarming, first, peak, dev, sig, corr, p_cls = pack[moved]
                pc = p_cls[i]
                n_alarm = int(alarming[i].sum())
                if arm == "proposed":
                    pr = retrieve(dev[i], alarming[i], sig)[0]
                elif arm == "lookup":
                    pr = pc
                else:
                    pr = None
                action, score, agree = decide(pc, pr, n_alarm, moved, arm, w)
                if action == "observe" and not moved and MAX_MOVES >= 1:
                    moved = True
                    continue
                break
            order = priority_order(alarming, first, peak, i)
            order_kb = priority_knowledge(alarming[i], first[i], pr) if pr is not None else order
            top3 = np.argsort(-score)[:3]
            rows.append({"seed": seed, "fold": fold, "arm": arm,
                         "faultNumber": int(E["id"][i][0]), "simulationRun": int(E["id"][i][1]),
                         "y": int(E["y"][i]), "top1": int(top3[0]), "top2": int(top3[1]),
                         "top3": int(top3[2]), "action": action, "iters": iters, "agree": agree,
                         "n_alarm": n_alarm, "raw_alarms": int(order.size),
                         "shown_alarms": len(group_alarms(order, corr)),
                         "root_chrono": VARS[order[0]] if order.size else None,
                         "root_kb": VARS[order_kb[0]] if order_kb.size else None,
                         "ret1": int(np.argmax(pr)) if pr is not None else None,
                         "ret_top3": [int(c) for c in np.argsort(-pr)[:3]] if pr is not None else None})
        out[arm] = rows
    return out


def score_rows(rows):
    yt = np.array([r["y"] for r in rows])
    top1 = np.array([r["top1"] for r in rows])
    hit3 = np.array([r["y"] in (r["top1"], r["top2"], r["top3"]) for r in rows])
    o = {"F1macro": float(f1_score(yt, top1, average="macro")),
         "Recall@1": float(np.mean(top1 == yt)), "Recall@3": float(np.mean(hit3))}
    for key, name in (("root_chrono", "RootAlarmChrono"), ("root_kb", "RootAlarmKB")):
        ev = [r for r in rows if r["y"] in DOCUMENTED and r[key]]
        o[name] = float(np.mean([r[key] in VAR_OF[r["y"]] for r in ev])) if ev else np.nan
    raw = sum(r["raw_alarms"] for r in rows)
    o["AlarmReduction"] = float(1 - sum(r["shown_alarms"] for r in rows) / max(raw, 1e-9))
    if rows[0]["ret_top3"] is not None:
        o["Grounding"] = float(np.mean([r["ret_top3"][0] == r["y"] for r in rows]) +
                               np.mean([r["y"] in r["ret_top3"] for r in rows]))
    else:
        o["Grounding"] = np.nan
    ag = np.array([r["agree"] is True for r in rows])
    two = any(r["agree"] is not None for r in rows)
    o["AgreeShare"] = float(ag.mean()) if two else np.nan
    o["AccAgree"] = float(np.mean(top1[ag] == yt[ag])) if two and ag.any() else np.nan
    o["AccDisagree"] = float(np.mean(top1[~ag] == yt[~ag])) if two and (~ag).any() else np.nan
    for a in ACTIONS:
        o["act_" + a] = float(np.mean([r["action"] == a for r in rows]))
    return o


# ---------------- one fold: every row of Table II on the evaluation set E ----------------
def score_fold(seed, fold, tri, E):
    res = {}
    freq = np.array([(Y[tri] == c).sum() for c in CLASSES], float)
    res["trivial"] = proba_metrics(E["y"], np.tile(freq / freq.sum(), (len(E["y"]), 1)), CLASSES)
    res["trivial"]["F1macro"] = float(f1_score(
        E["y"], np.full(len(E["y"]), CLASSES[np.argmax(freq)]), average="macro"))
    for name in CLASSIC_CFG:
        est = make_est(name, seed).fit(DEV_X64[tri], Y[tri])
        res[name] = proba_metrics(E["y"], est.predict_proba(E["x64"]), est.named_steps["clf"].classes_)
    # MLP standardized in float64, then cast, as 14 scores it for Table II
    for kind, key in (("mlp", "x64"), ("cnn", "ext")):
        net, mean, std = load_net(kind, seed, fold)
        X = E[key] if kind == "mlp" else E[key][:, :, :W]
        res[kind] = proba_metrics(E["y"], net_proba(net, mean, std, X), CLASSES)
    decisions = agent_fold(seed, fold, tri, E)
    for arm in ARMS:
        res[arm] = score_rows(decisions[arm])
    return res, decisions


def run_all_folds(eval_set):
    per_fold, log = [], []
    for seed in EST_SEEDS:
        for fold, (tri, vai) in enumerate(folds(seed)):
            t = time.perf_counter()
            E = eval_set(vai)
            res, dec = score_fold(seed, fold, tri, E)
            for row in ROWS:
                per_fold.append({"seed": seed, "fold": fold, "row": row, **res[row]})
            for arm in ARMS:
                log += dec[arm]
            print(f"  seed {seed} fold {fold}: copilot macro-F1 {res['proposed']['F1macro']:.4f}, "
                  f"ablation {res['ablation']['F1macro']:.4f}  ({time.perf_counter() - t:.0f} s)",
                  flush=True)
    return pd.DataFrame(per_fold), log


# ---------------- validation reference: the per-fold tables behind Table II ----------------
VAL_F1 = pd.read_csv(os.path.join(RES, "per_fold_f1.csv")).set_index(["seed", "fold"])
VAL_R3 = pd.read_csv(os.path.join(RES, "per_fold_recall3.csv")).set_index(["seed", "fold"])
VAL_EXTRA = {("RootAlarmChrono", a): f"rootchrono_{a}" for a in ARMS}
VAL_EXTRA.update({("RootAlarmKB", a): f"rootkb_{a}" for a in ARMS})
VAL_EXTRA.update({("Grounding", a): f"grounding_{a}" for a in ("lookup", "proposed")})


def loader_check():
    """The reader used for *_Testing, run on *_Training, must rebuild the development caches."""
    dev = load_pool(["TEP_FaultFree_Training.RData", "TEP_Faulty_Training.RData"], ONSET["dev"])
    where = {tuple(i): k for k, i in enumerate(dev["id"])}
    order = np.array([where[tuple(i)] for i in DEV_ID])
    d_feat = float(np.abs(dev["x64"][order] - DEV_X64).max())
    d_ext = float(np.abs(dev["ext"][order] - DEV_EXT).max())
    print(f"  reader  features max |diff| {d_feat:.2e}, windows max |diff| {d_ext:.2e}")
    return max(d_feat, d_ext), dev


def dev_check():
    print("dev check: the .RData reader against the development caches")
    worst, dev = loader_check()
    print("dev check: validation folds through this script, compared with results/per_fold_*.csv")

    def dev_set(vai):
        return {"x64": DEV_X64[vai], "ext": DEV_EXT[vai], "id": DEV_ID[vai], "y": Y[vai]}

    pf, _ = run_all_folds(dev_set)
    checks = [(row, "F1macro", VAL_F1, row) for row in ROWS]
    checks += [(row, "Recall@3", VAL_R3, row) for row in ROWS]
    checks += [(arm, met, VAL_F1, col) for (met, arm), col in VAL_EXTRA.items()]
    for row, met, ref, col in checks:
        got = pf[pf["row"] == row].set_index(["seed", "fold"])[met]
        d = float(np.nanmax(np.abs(got.to_numpy() - ref.loc[got.index, col].to_numpy())))
        worst = max(worst, d)
        print(f"  {row:<9} {met:<16} max |diff| {d:.2e}  {'OK' if d < 1e-9 else 'DIFFERENT'}")
    passed = worst < 1e-9
    print(f"\ndev check {'PASSED' if passed else 'FAILED'} (largest difference {worst:.2e})")
    return passed, dev


# ---------------- summary: test next to validation ----------------
def summarize(pf):
    out = []
    for row in ROWS:
        t = pf[pf["row"] == row]
        out.append({"row": row,
                    "val_F1macro_mean": VAL_F1[row].mean(), "val_F1macro_std": VAL_F1[row].std(ddof=0),
                    "test_F1macro_mean": t["F1macro"].mean(), "test_F1macro_std": t["F1macro"].std(ddof=0),
                    "val_Recall@3_mean": VAL_R3[row].mean(), "val_Recall@3_std": VAL_R3[row].std(ddof=0),
                    "test_Recall@3_mean": t["Recall@3"].mean(), "test_Recall@3_std": t["Recall@3"].std(ddof=0)})
    return pd.DataFrame(out)


def paired(pf):
    """Differences per fold, as validation reports them: mean, std and sign in the 15 folds."""
    def by(row, met):
        return pf[pf["row"] == row].set_index(["seed", "fold"])[met]
    comps = [("macro-F1: proposed - ablation", by("proposed", "F1macro") - by("ablation", "F1macro"))]
    for arm in ARMS:
        comps.append((f"root alarm, {arm}: knowledge - chronological",
                      by(arm, "RootAlarmKB") - by(arm, "RootAlarmChrono")))
    comps.append(("grounding: proposed - lookup", by("proposed", "Grounding") - by("lookup", "Grounding")))
    return pd.DataFrame([{"comparison": n, "mean": d.mean(), "std": d.std(ddof=0),
                          "folds_positive": int((d > 0).sum()), "folds_negative": int((d < 0).sum()),
                          "folds": int(d.notna().sum())} for n, d in comps])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dev-check", action="store_true")
    args = ap.parse_args()
    if not __debug__:
        sys.exit("Run without -O: the data checks are asserts.")
    check_frozen()
    if args.dev_check:
        sys.exit(0 if dev_check()[0] else 1)

    guards()
    t0 = time.perf_counter()
    started = datetime.now(timezone.utc).isoformat(timespec="seconds")
    passed, dev = dev_check()
    if not passed:
        sys.exit("The dev check failed: the models or caches no longer reproduce validation. "
                 "The test was not read.")
    files = ["TEP_FaultFree_Testing.RData", "TEP_Faulty_Testing.RData"]
    print("reading the test pool...", flush=True)
    T = load_pool(files, ONSET["test"])
    print(f"test pool: {len(T['y'])} runs, {len(np.unique(T['y']))} classes")
    assert len(T["y"]) == 10500 and (np.bincount(T["y"], minlength=21) == 500).all()

    tw = twin_check(T, dev)
    os.makedirs(OUT)
    tw.to_csv(os.path.join(OUT, "twins.csv"), index=False)
    print("twin check written before scoring:\n" + tw.to_string(index=False), flush=True)

    print("\nscoring the 15 models on the test pool:", flush=True)
    pf, log = run_all_folds(lambda vai: T)
    pf.to_csv(os.path.join(OUT, "test_per_fold.csv"), index=False)
    pd.DataFrame(log).to_csv(os.path.join(OUT, "decisions_test.csv.gz"), index=False)
    sm = summarize(pf)
    sm.to_csv(os.path.join(OUT, "test_summary.csv"), index=False)
    pr = paired(pf)
    pr.to_csv(os.path.join(OUT, "test_paired.csv"), index=False)

    model_files = sorted(f for f in os.listdir(MODELS)
                         if any(f.endswith(f"_seed{s}_fold{k}.pt") for s in EST_SEEDS for k in range(K)))
    env = {"started_utc": started, "seconds": round(time.perf_counter() - t0),
           "git_head": git("rev-parse", "HEAD"), "tag": TAG,
           "python": platform.python_version(), "numpy": np.__version__,
           "sklearn": sklearn.__version__, "torch": torch.__version__,
           "processor": platform.processor(), "cpu_count": os.cpu_count(),
           "test_files_sha256_16": {f: sha256(os.path.join(DATA, f)) for f in files},
           "models_sha256_16": {f: sha256(os.path.join(MODELS, f)) for f in model_files},
           "window_test": [ONSET["test"], ONSET["test"] + READ], "onset": ONSET}
    with open(os.path.join(OUT, "test_env.json"), "w", encoding="utf-8") as f:
        json.dump(env, f, indent=2)

    pd.set_option("display.width", 200)
    print("\n" + sm.round(3).to_string(index=False))
    print("\n" + pr.round(4).to_string(index=False))
    print(f"\nwritten to results/test/ in {env['seconds']} s. Commit it as it is.")


if __name__ == "__main__":
    main()
