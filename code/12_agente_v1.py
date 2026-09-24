r"""
The proposed method: the copilot agent v1, and its ablation.

Everything here was fixed in PROTOCOLO.md ("Figure 1 in text" and "Extension:
alarms, actions and the loop") BEFORE this script was written or run.

THE FOUR PIECES OF THE LOOP (each marked [P1]..[P4] where it is implemented):
  [P1] PERCEIVES  the alarm flow and the process variables of the run
  [P2] SCORES     the saved 1D-CNN of that fold, never retrained. The alarm rate is
                  logged beside it but no decision uses it; decide only reads the
                  alarm count, for the flood guard
  [P3] REASONS    retrieval by symptoms over kb/tep_kb.json. RULES, not a language
                  model. The fixed prompt sits in prompts/razona.txt, unused here.
  [P4] DECIDES    one action from the declared list, each with the same guard

  [LOOP]  the action `observe` moves the window, so what is perceived next is not
          what was perceived before. That is what makes this a loop.
  [GUARD] the copilot only suggests. There is no code path to the process.
  [HUMAN] the operator reviews before any decision reaches the plant.
  [MEAS]  the Table II number is computed from the decision log and the labels,
          at the output of decide. Never from generated text.

THE ABLATION: the same loop with [P3] removed, so decide sees only the classifier.

Outputs: results/logs/decisiones.jsonl, results/logs/decisiones_muestra.jsonl
(the committed sample), results/agente_comparison.csv, results/agente_env.json,
results/agent_scores.npz (the score vectors 21 reads) and the extended-window
cache results/dev_windows_ext.npy.
"""
import os, json, time, platform
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.metrics import f1_score

BASE = os.path.dirname(os.path.abspath(__file__))
if not os.path.isfile(os.path.join(BASE, "requirements.txt")):
    BASE = os.path.dirname(BASE)      # the scripts live in code/, the project one level up
DATA = os.path.join(BASE, "dataverse_files")
RES = os.path.join(BASE, "results")
MODELS = os.path.join(RES, "models")
LOGS = os.path.join(RES, "logs")
os.makedirs(LOGS, exist_ok=True)

# ---------------- pre-registered constants (PROTOCOLO.md, do not change) ----------------
VARS = [f"xmeas_{i}" for i in range(1, 42)] + [f"xmv_{i}" for i in range(1, 12)]
ONSET, W, MOVE = 21, 20, 10        # score 20 steps; `observe` advances by 10
READ = W + MOVE                    # samples 21..51 are read, 20 are scored
K, SEL_SEED, EST_SEEDS = 5, 0, [5, 17, 42]
ALARM_K = 3.0                      # alarm when |z| > 3 sigma of normal operation
CORR_GROUP = 0.8                   # alarms grouped above this correlation on normal
TAU = 0.50                         # confidence needed to commit
FLOOD_N = 10                       # variables in alarm that count as a flood
W_GRID = [0.25, 0.50, 0.75]        # 3 configurations, same effort every model got
MAX_MOVES = 1                      # the loop terminates
CLASSES = np.arange(0, 21)
ACTIONS = ["generate", "observe", "defer", "alert"]

# ---------------- knowledge base ----------------
KB = json.load(open(os.path.join(BASE, "kb", "tep_kb.json"), encoding="utf-8"))
DOCS = {d["clase"]: d for d in KB["documentos"]}
DOCUMENTED = {c for c, d in DOCS.items() if d["causa_documentada"] and c != 0}
VAR_OF = {c: set(DOCS[c]["variables_documentadas"]) for c in DOCS}
# DOCVAR[c, v] = 1 when document c names variable v. Lets the knowledge-driven
# prioritization weight an alarm by the retrieval mass of the documents that
# mention its variable.
DOCVAR = np.zeros((21, 52), np.float32)
for _c, _d in DOCS.items():
    for _v in _d["variables_documentadas"]:
        DOCVAR[_c, VARS.index(_v)] = 1.0
print(f"knowledge base: {KB['_meta']['n_documentos']} documents, "
      f"{len(DOCUMENTED)} faults with a documented cause "
      f"({sorted(set(range(1, 21)) - DOCUMENTED)} excluded from the root-alarm metric)")

# ---------------- data ----------------
feat = pd.read_parquet(os.path.join(RES, "dev_features.parquet"))
y = feat["faultNumber"].to_numpy()
groups = feat["faultNumber"].to_numpy() * 1000 + feat["simulationRun"].to_numpy()
run_id = feat[["faultNumber", "simulationRun"]].astype(int).to_numpy()
Xtab = feat[[c for c in feat.columns if c.endswith(("_mean", "_std"))]].to_numpy(np.float32)

EXT_CACHE = os.path.join(RES, "dev_windows_ext.npy")
if os.path.exists(EXT_CACHE):
    Xext = np.load(EXT_CACHE)
    print("loaded cached extended windows:", EXT_CACHE)
else:
    import pyreadr

    def windows(fname):                       # only *_Training is ever opened
        res = pyreadr.read_r(os.path.join(DATA, fname))
        df = res[list(res.keys())[0]]
        del res
        sub = df[df["sample"].between(ONSET, ONSET + READ - 1)].sort_values(
            ["faultNumber", "simulationRun", "sample"])
        n = len(sub) // READ
        assert len(sub) % READ == 0, "incomplete extended window in " + fname
        fn = sub["faultNumber"].to_numpy().reshape(n, READ)
        sr = sub["simulationRun"].to_numpy().reshape(n, READ)
        assert (fn == fn[:, :1]).all() and (sr == sr[:, :1]).all(), "misaligned"
        X = sub[VARS].to_numpy(np.float32).reshape(n, READ, len(VARS))
        idx = pd.DataFrame({"faultNumber": fn[:, 0].astype(int),
                            "simulationRun": sr[:, 0].astype(int)})
        del df, sub
        return X, idx

    Xa, ia = windows("TEP_FaultFree_Training.RData")
    Xb, ib = windows("TEP_Faulty_Training.RData")
    Xall = np.concatenate([Xa, Xb])
    iall = pd.concat([ia, ib], ignore_index=True)
    pos = iall.reset_index().set_index(["faultNumber", "simulationRun"])["index"]
    order = pos.loc[list(zip(feat["faultNumber"].astype(int),
                             feat["simulationRun"].astype(int)))].to_numpy()
    Xext = np.ascontiguousarray(Xall[order].transpose(0, 2, 1))   # (N, 52, 30)
    np.save(EXT_CACHE, Xext)
    print("extracted + cached extended windows:", EXT_CACHE)

assert len(Xext) == len(y) and Xext.shape[1] == 52 and Xext.shape[2] == READ
print(f"dev pool: {len(y)} runs | read {READ} samples, score {W} | TEST SEALED")


def slice_window(moved):
    """The 20 scored steps: 21..41 before moving, 31..51 after. [LOOP]"""
    s = MOVE if moved else 0
    return Xext[:, :, s:s + W]


# ---------------- the model of the fold, loaded and never retrained [P2] ----------------
def make_cnn():
    return nn.Sequential(nn.Conv1d(52, 32, 5, padding=2), nn.BatchNorm1d(32), nn.ReLU(),
                         nn.Conv1d(32, 64, 3, padding=1), nn.BatchNorm1d(64), nn.ReLU(),
                         nn.AdaptiveAvgPool1d(1), nn.Flatten(), nn.Dropout(0.2),
                         nn.Linear(64, 21))


def load_fold_model(seed, fold):
    ck = torch.load(os.path.join(MODELS, f"cnn_seed{seed}_fold{fold}.pt"), weights_only=False)
    net = make_cnn()
    net.load_state_dict(ck["state_dict"])
    net.eval()
    return net, ck["mean"], ck["std"]


def classifier_proba(net, mean, std, Xw):
    """The saved standardization is reused, never refitted, also when the window moved."""
    t = torch.from_numpy(np.ascontiguousarray((Xw - mean) / std))
    with torch.no_grad():
        return torch.softmax(net(t), dim=1).numpy()


# ---------------- [P1] perceive: the alarm layer ----------------
def fit_alarm_limits(Xw, idx_train):
    """Limits from NORMAL runs of the training portion only. No labeled fault is used."""
    normal = idx_train[y[idx_train] == 0]
    m = Xw[normal].mean(axis=(0, 2), keepdims=True)
    s = Xw[normal].std(axis=(0, 2), keepdims=True)
    return m, np.where(s < 1e-8, 1.0, s)


def perceive(Xw, m, s):
    z = (Xw - m) / s                                   # (n, 52, W)
    over = np.abs(z) > ALARM_K
    alarming = over.any(axis=2)                        # (n, 52)
    first = np.where(alarming, over.argmax(axis=2), W)  # first crossing step
    peak = np.abs(z).max(axis=2)
    dev = (Xw.mean(axis=2) - m[0, :, 0]) / s[0, :, 0]   # deviation profile (n, 52)
    return alarming, first, peak, dev


def priority_order(alarming, first, peak, i):
    """Earliest crossing first, ties broken by how far the value exceeds the band."""
    idx = np.flatnonzero(alarming[i])
    if idx.size == 0:
        return idx
    return idx[np.lexsort((-peak[i, idx], first[i, idx]))]


def priority_knowledge(alarming_i, first_i, p_ret):
    """The PROPOSAL for RQ1: an alarm rises when the retrieved evidence names its
    variable. Ties broken by earliest crossing. Only exists where retrieval does."""
    idx = np.flatnonzero(alarming_i)
    if idx.size == 0:
        return idx
    w = p_ret @ DOCVAR                     # retrieval mass naming each variable
    return idx[np.lexsort((first_i[idx], -w[idx]))]


def group_alarms(order, corr):
    """Alarms whose variables correlate above the threshold on normal operation
    collapse into one group, which is what the operator would be shown."""
    kept, seen = [], set()
    for v in order:
        if v in seen:
            continue
        kept.append(v)
        seen.update(np.flatnonzero(corr[v] >= CORR_GROUP).tolist())
    return kept


# ---------------- [P3] reason: retrieval by symptoms, RULES ----------------
def fit_signatures(dev_train, idx_train):
    sig = np.zeros((21, 52), np.float32)
    for c in CLASSES:
        sel = idx_train[y[idx_train] == c]
        sig[c] = dev_train[sel].mean(axis=0)
    return sig


def retrieve(dev_i, alarming_i, sig):
    """Query = the deviation profile restricted to the variables that alarmed, so the
    alarms actually drive retrieval. Falls back to the full profile if none fired."""
    used_alarms = bool(alarming_i.any())
    q = dev_i * alarming_i if used_alarms else dev_i
    qn = np.linalg.norm(q)
    if qn < 1e-8:
        q, qn = dev_i, max(np.linalg.norm(dev_i), 1e-8)
    cos = (sig @ q) / (np.linalg.norm(sig, axis=1) * qn + 1e-12)
    e = np.exp(cos - cos.max())
    return e / e.sum(), used_alarms


# ---------------- [P4] decide: one action, each with its guard ----------------
def decide(p_cls, p_ret, n_alarm, moved, arm, w):
    top_cls = int(np.argmax(p_cls))
    conf = float(p_cls[top_cls])
    if arm == "proposed":
        score = (1.0 - w) * p_cls + w * p_ret
        top_ret = int(np.argmax(p_ret))
        agree = (top_cls == top_ret)
        ready = agree and conf >= TAU
    else:                    # ablation and lookup: the classifier ranks alone, so the
        score = p_cls        # only thing that changes between them is the citation
        top_ret, agree = None, None
        ready = conf >= TAU
    if top_cls == 0 and n_alarm >= FLOOD_N:
        return "alert", score, agree, conf
    if ready:
        return "generate", score, agree, conf
    if not moved:
        return "observe", score, agree, conf
    return "defer", score, agree, conf


# ---------------- one fold, both window positions precomputed ----------------
# el vector de puntuacion de cada episodio, que 21_pr_auc.py necesita y el
# log de decisiones no guarda porque solo lleva el top-3
SCORES = []


def run_fold(seed, fold, tri, vai, arm, w, fh=None):
    net, mean, std = load_fold_model(seed, fold)
    pack, t_inf = {}, 0.0
    for moved in (False, True):
        Xw = slice_window(moved)
        m, s = fit_alarm_limits(Xw, tri)                       # [R2] inside the fold
        alarming, first, peak, dev = perceive(Xw, m, s)
        sig = fit_signatures(dev, tri)
        corr = np.corrcoef(dev[tri[y[tri] == 0]].T)
        corr = np.nan_to_num(corr)
        # The per-episode latency starts here. The fit above needs every training
        # run perceived, so the episodes are perceived again on their own, under the
        # clock, together with the network that scores them; perceive works run by
        # run, so their rows come out the same and are written back.
        t = time.perf_counter()
        for full, part in zip((alarming, first, peak, dev), perceive(Xw[vai], m, s)):
            full[vai] = part
        p_cls = classifier_proba(net, mean, std, Xw[vai])
        t_inf += time.perf_counter() - t
        pack[moved] = (alarming, first, peak, dev, sig, corr, p_cls)

    # the loop is timed episode by episode, leaving out what only bookkeeping needs:
    # the score vector kept for 21_pr_auc.py and the line written to the log
    rows, t_loop = [], 0.0
    for j, i in enumerate(vai):
        t = time.perf_counter()
        moved, iters = False, 0
        while True:
            iters += 1
            alarming, first, peak, dev, sig, corr, p_cls = pack[moved]
            pc = p_cls[j]
            n_alarm = int(alarming[i].sum())
            if arm == "proposed":
                pr, used_al = retrieve(dev[i], alarming[i], sig)
            elif arm == "lookup":
                pr, used_al = pc, False     # grounding keyed by the predicted class
            else:
                pr, used_al = None, None
            action, score, agree, conf = decide(pc, pr, n_alarm, moved, arm, w)
            if action == "observe" and not moved and MAX_MOVES >= 1:
                moved = True
                continue
            break
        order = priority_order(alarming, first, peak, i)          # RQ1 baseline
        order_kb = (priority_knowledge(alarming[i], first[i], pr)  # RQ1 proposal
                    if pr is not None else order)
        shown = group_alarms(order, corr)
        top3 = np.argsort(-score)[:3]
        rows.append({
            "y": int(y[i]), "top3": top3, "n_alarm": n_alarm,
            "raw_alarms": int(order.size), "shown_alarms": len(shown),
            "root_chrono": VARS[order[0]] if order.size else None,
            "root_kb": VARS[order_kb[0]] if order_kb.size else None,
            "ret3": (np.argsort(-pr)[:3] if pr is not None else None),
            "action": action, "iters": iters, "agree": agree,
        })
        t_loop += time.perf_counter() - t
        SCORES.append((seed, fold, arm, int(i), int(y[i]), score.astype(np.float32)))
        if fh is not None:
            fh.write(json.dumps({
                "id": [int(run_id[i][0]), int(run_id[i][1])], "seed": seed, "fold": fold,
                "arm": arm,
                "percibe": {"n_alarmas": n_alarm, "tasa": round(n_alarm / 52, 4),
                            "primeras": [VARS[v] for v in order[:3].tolist()],
                            "mostradas": len(shown),
                            "raiz_cronologica": VARS[order[0]] if order.size else None,
                            "raiz_conocimiento": VARS[order_kb[0]] if order_kb.size else None},
                "puntua": {"top3": [int(c) for c in np.argsort(-pc)[:3]],
                           "prob": [round(float(pc[c]), 4) for c in np.argsort(-pc)[:3]]},
                "razona": (None if pr is None else
                           {"docs": [DOCS[int(c)]["nombre"] for c in np.argsort(-pr)[:3]],
                            "score": [round(float(pr[c]), 4) for c in np.argsort(-pr)[:3]],
                            "cita": DOCS[int(np.argmax(pr))]["nombre"],
                            "uso_alarmas": used_al}),
                "decide": {"accion": action, "guarda": "solo sugiere, no actua",
                           "top3": [int(c) for c in top3], "concuerda": agree},
                "costo": {"segundos": None, "iteraciones": iters, "tokens": 0},
                "label": int(y[i]),
            }, ensure_ascii=False) + "\n")
    return rows, t_inf + t_loop


# ---------------- metrics, computed FROM the log rows and the labels [MEAS] ----------------
def score_rows(rows):
    yt = np.array([r["y"] for r in rows])
    top1 = np.array([r["top3"][0] for r in rows])
    hit3 = np.array([r["y"] in list(r["top3"]) for r in rows])
    out = {"F1macro": float(f1_score(yt, top1, average="macro")),
           "Recall@1": float(np.mean(top1 == yt)), "Recall@3": float(np.mean(hit3))}
    # root alarm: only on faults with a documented cause.
    # Chronological is the RQ1 baseline, knowledge-driven is the RQ1 proposal.
    for key, name in (("root_chrono", "RootAlarmChrono"), ("root_kb", "RootAlarmKB")):
        ev = [r for r in rows if r["y"] in DOCUMENTED and r[key]]
        out[name] = (float(np.mean([r[key] in VAR_OF[r["y"]] for r in ev]))
                     if ev else float("nan"))
    out["RootAlarm_n"] = len([r for r in rows if r["y"] in DOCUMENTED and r["root_chrono"]])
    # alarm reduction: all 21 classes, no per-fault ground truth needed
    raw = np.array([r["raw_alarms"] for r in rows], float)
    shown = np.array([r["shown_alarms"] for r in rows], float)
    out["AlarmsRaw"] = float(raw.mean())
    out["AlarmsShown"] = float(shown.mean())
    out["AlarmReduction"] = float(1 - shown.sum() / max(raw.sum(), 1e-9))
    # Rubric, decomposed. An arm that cites nothing reports R2, R3 and the total as
    # NOT APPLICABLE, never as zero: an absence is not a failure, and scoring it as
    # zero would turn a structural gap into an inflated gain.
    out["R1"] = float((top1 == yt).mean())
    if rows[0]["ret3"] is not None:
        out["R2"] = float(np.mean([r["ret3"][0] == r["y"] for r in rows]))
        out["R3"] = float(np.mean([r["y"] in list(r["ret3"]) for r in rows]))
        out["Grounding"] = out["R2"] + out["R3"]
        out["Rubric"] = out["R1"] + out["R2"] + out["R3"]
    else:
        out["R2"] = out["R3"] = out["Grounding"] = out["Rubric"] = float("nan")
    # Confidence signal: only meaningful where TWO opinions exist. Where they do not,
    # it is n/a, not the overall accuracy wearing a different label.
    two = any(r["agree"] is not None for r in rows)
    ag = np.array([r["agree"] is True for r in rows])
    out["AgreeShare"] = float(ag.mean()) if two else float("nan")
    out["AccAgree"] = (float(np.mean(top1[ag] == yt[ag]))
                       if (two and ag.any()) else float("nan"))
    out["AccDisagree"] = (float(np.mean(top1[~ag] == yt[~ag]))
                          if (two and (~ag).any()) else float("nan"))
    for a in ACTIONS:
        out["act_" + a] = float(np.mean([r["action"] == a for r in rows]))
    out["iters"] = float(np.mean([r["iters"] for r in rows]))
    return out


def cv(arm, w, seed, fh=None):
    sgkf = StratifiedGroupKFold(n_splits=K, shuffle=True, random_state=seed)
    per_fold, secs = [], []
    for f, (tri, vai) in enumerate(sgkf.split(Xtab, y, groups)):
        rows, s = run_fold(seed, f, tri, vai, arm, w, fh)
        per_fold.append(score_rows(rows))
        secs.append(s / len(vai))
    return per_fold, secs


MET_A = ["F1macro", "Recall@1", "Recall@3", "AccAgree", "AccDisagree"]
MET_B = ["RootAlarmChrono", "RootAlarmKB", "AlarmReduction", "R1", "R2", "R3", "Rubric"]
ARMS = (("ablation", "Sin agente (ablacion)"), ("lookup", "Anclaje por etiqueta"),
        ("proposed", "Metodo propuesto"))

# ---------------- select the fusion weight: 3 configurations, seed 0, by macro-F1 ----------------
print("\nfusion weight selection (seed %d, 3 configurations, by macro-F1):" % SEL_SEED)
scored = []
for w in W_GRID:
    pf, _ = cv("proposed", w, SEL_SEED)
    scored.append((float(np.mean([d["F1macro"] for d in pf])), w))
    print(f"      w={w:<5} macro-F1={scored[-1][0]:.4f}", flush=True)
BEST_W = max(scored, key=lambda t: t[0])[1]
print(f"  selected w = {BEST_W}", flush=True)

# ---------------- estimation: both arms, 3 seeds x 5 folds ----------------
print("\nestimation (15 folds per arm; the decision log is written as it runs):")
rows_out = []
with open(os.path.join(LOGS, "decisiones.jsonl"), "w", encoding="utf-8") as fh:
    for arm, w in (("ablation", 0.0), ("lookup", 0.0), ("proposed", BEST_W)):
        allf, allsec = [], []
        for s in EST_SEEDS:
            pf, sec = cv(arm, w, s, fh)
            allf += pf
            allsec += sec
            print(f"    [{arm}] seed {s}: macro-F1 "
                  f"{np.mean([d['F1macro'] for d in pf]):.4f}", flush=True)
        # median over the 15 folds, not the mean: each fold is timed once, and one
        # fold slowed by something else on the machine should not move the row
        r = {"arm": arm, "w": w, "s_per_decision": float(np.median(allsec))}
        print(f"    [{arm}] ms per episode over the 15 folds: min {1000 * min(allsec):.3f}, "
              f"median {1000 * np.median(allsec):.3f}, max {1000 * max(allsec):.3f}", flush=True)
        for m in list(allf[0].keys()):
            vals = [d[m] for d in allf if not np.isnan(d[m])]
            r[m + "_mean"] = float(np.mean(vals)) if vals else float("nan")
            r[m + "_std"] = float(np.std(vals)) if vals else float("nan")
        rows_out.append(r)

df = pd.DataFrame(rows_out)
df.to_csv(os.path.join(RES, "agente_comparison.csv"), index=False)

# ---------------- report and the sentence ----------------
by = {r["arm"]: r for r in rows_out}
ab, lk, pr = by["ablation"], by["lookup"], by["proposed"]


def cell(r, m):
    """An arm that cites nothing prints n/a, never a zero."""
    v = r[m + "_mean"]
    return f"{'n/a':>19} " if np.isnan(v) else f"{v:>12.4f}+/-{r[m + '_std']:<6.3f}"


def table(title, mets):
    hdr = f"{'arm':<26}" + "".join(f"{m:>20}" for m in mets)
    print("\n" + "=" * len(hdr))
    print(title)
    print("=" * len(hdr))
    print(hdr)
    print("-" * len(hdr))
    for key, name in ARMS:
        print(f"{name:<26}" + "".join(cell(by[key], m) for m in mets))


table("DECISION QUALITY  (same partition, same metric, 3 seeds; mean +/- std)", MET_A)
table("ALARMS AND GROUNDING  (n/a means the arm produces no citation, so there is "
      "nothing to score)", MET_B)

d = pr["F1macro_mean"] - ab["F1macro_mean"]
pooled = max(pr["F1macro_std"], ab["F1macro_std"])
print()
if abs(d) <= pooled:
    print(f"macro-F1 against the ablation: no difference. The gap {d:+.4f} sits inside "
          f"the standard deviation ({pooled:.4f}).")
elif d > 0:
    print(f"macro-F1 against the ablation: the agent ADDS {d:+.4f}.")
else:
    print(f"macro-F1 against the ablation: the agent SUBTRACTS {d:+.4f}. "
          f"Reported, not hidden.")

dg = pr["Grounding_mean"] - lk["Grounding_mean"]
pg = max(pr["Grounding_std"], lk["Grounding_std"])
print(f"grounding (R2+R3, out of 2) against the label lookup: symptom retrieval "
      f"{pr['Grounding_mean']:.4f} vs {lk['Grounding_mean']:.4f} ({dg:+.4f}, sd {pg:.4f})")
if dg < -pg:
    print("  -> the lookup cites the right document more often, exactly as declared in "
          "advance. Symptom retrieval is not a better document finder; it is an "
          "INDEPENDENT one, and that independence is what the confidence signal and "
          "the RQ1 answer rest on, neither of which a lookup keyed by the classifier "
          "can give.")
elif dg > pg:
    print("  -> symptom retrieval cites the right document more often than the lookup.")
else:
    print("  -> no difference between the two groundings.")
print(f"\nactions taken (proposed): " + ", ".join(
    f"{a} {pr['act_' + a + '_mean']:.1%}" for a in ACTIONS))
print(f"mean iterations per decision: {pr['iters_mean']:.3f}  "
      f"(1.0 means the loop never moved the window)")
print(f"alarms: {pr['AlarmsRaw_mean']:.1f} raw -> {pr['AlarmsShown_mean']:.1f} shown "
      f"({pr['AlarmReduction_mean']:.1%} fewer)")
rc, rk = pr["RootAlarmChrono_mean"], pr["RootAlarmKB_mean"]
sr = max(pr["RootAlarmChrono_std"], pr["RootAlarmKB_std"])
print(f"\nRQ1, root alarm on {int(pr['RootAlarm_n_mean'])} episodes per fold "
      f"(only the {len(DOCUMENTED)} faults with a documented cause):")
print(f"  chronological baseline {rc:.4f}  vs  knowledge-driven {rk:.4f}   "
      f"({rk - rc:+.4f}, standard deviation {sr:.4f})")
if abs(rk - rc) <= sr:
    print("  -> no difference: retrieval does not beat chronology at finding the root alarm.")
elif rk > rc:
    print("  -> retrieval DOES find the root alarm better than the chronological baseline.")
else:
    print("  -> retrieval is WORSE than chronology here. Reported, not hidden.")

# A small static sample travels with the repository as evidence; the full log is
# regenerated by the command and is too large to version on every run.
_p = os.path.join(LOGS, "decisiones.jsonl")
_lines = open(_p, encoding="utf-8").readlines()
with open(os.path.join(LOGS, "decisiones_muestra.jsonl"), "w", encoding="utf-8") as f:
    # first and last 500 lines: in the order the log is written that is the
    # ablation (seed 5, fold 0) and the proposed arm (seed 42, fold 4); the lookup
    # arm and the other seeds are not in the sample
    f.writelines(_lines[:500] + _lines[-500:])
print(f"\ndecision log: {len(_lines)} lines; a 1000-line sample is committed as evidence")

env = {"python": platform.python_version(), "torch": torch.__version__,
       "alarm_k": ALARM_K, "corr_group": CORR_GROUP, "tau": TAU, "flood_n": FLOOD_N,
       "w_grid": W_GRID, "selected_w": BEST_W, "max_moves": MAX_MOVES,
       "read_samples": [ONSET, ONSET + READ], "scored_steps": W, "move": MOVE,
       "razona": "rules (symptom retrieval); prompts/razona.txt is NOT executed",
       "kb_documents": KB["_meta"]["n_documentos"],
       "root_alarm_excluded": sorted(set(range(1, 21)) - DOCUMENTED),
       "machine": "Intel Core i5-13420H, 12 threads, CPU only"}
with open(os.path.join(RES, "agente_env.json"), "w", encoding="utf-8") as f:
    json.dump(env, f, indent=2, ensure_ascii=False)
print("\nsaved: results/agente_comparison.csv, agente_env.json, logs/decisiones.jsonl")


# ---------------- the score vectors, for the precision-recall analysis ----------------
_sc = np.stack([r[5] for r in SCORES]) if SCORES else np.zeros((0, 21), np.float32)
np.savez_compressed(
    os.path.join(RES, "agent_scores.npz"),
    seed=np.array([r[0] for r in SCORES], np.int16),
    fold=np.array([r[1] for r in SCORES], np.int8),
    arm=np.array([r[2] for r in SCORES]),
    idx=np.array([r[3] for r in SCORES], np.int32),
    y=np.array([r[4] for r in SCORES], np.int8),
    score=_sc)
print("wrote results/agent_scores.npz  (%d episodes x %d classes)" % _sc.shape)
