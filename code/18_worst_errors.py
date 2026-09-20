r"""
The error that costs most: what the macro average hides.

Opens the average four ways:

  1. the per-class confusion, and the five worst classes with what they are taken for
  2. the split that matters on the floor: a fault read as normal operation, which is
     the real alarm buried under the avalanche, against normal operation read as a
     fault, which is a false alarm
  3. root-alarm recall within the first N alarms the operator is shown, not only at
     the first one, because an operator reads a short list and not a single line
  4. the three episodes of the discussion, picked by the rule PROTOCOLO.md declares:
     the first episode in decision-log order, for each of the three worst-classified
     faults the copilot called normal operation

Recall@N cannot come from the decision log, which keeps only the first three alarms
and the single root pick, so the alarm ordering is recomputed here from the saved
checkpoints exactly as 12_agente_v1.py builds it: alarm limits from the normal runs
of each fold's training portion, retrieval over the class signatures of that fold,
and the same knowledge-driven priority.

Outputs:
  results/errors/worst_errors.csv      per class: F1, recall, what it is taken for
  results/errors/root_alarm_recall.csv root-alarm recall at N = 1 to 5, per arm
"""
import os
import json
import numpy as np
import pandas as pd
import torch
from torch import nn
from sklearn.model_selection import StratifiedGroupKFold

BASE = os.path.dirname(os.path.abspath(__file__))
if not os.path.isfile(os.path.join(BASE, "requirements.txt")):
    BASE = os.path.dirname(BASE)      # the scripts live in code/, the project one level up
RES = os.path.join(BASE, "results")
ERR = os.path.join(RES, "errors")
os.makedirs(ERR, exist_ok=True)
MODELS = os.path.join(RES, "models")
LOG = os.path.join(RES, "logs", "decisiones.jsonl")
N_MAX = 5

env = json.load(open(os.path.join(RES, "agente_env.json"), encoding="utf-8"))
ALARM_K, TAU, FLOOD_N = env["alarm_k"], env["tau"], env["flood_n"]
MOVE, MAX_MOVES, BEST_W = env["move"], env["max_moves"], env["selected_w"]
ONSET, W = env["read_samples"][0], env["scored_steps"]
K, EST_SEEDS = 5, [5, 17, 42]
CLASSES = np.arange(21)

kb = json.load(open(os.path.join(BASE, "kb", "tep_kb.json"), encoding="utf-8"))
NAME = {d["clase"]: d["nombre"] for d in kb["documentos"]}
VAR_OF = {d["clase"]: set(d["variables_documentadas"]) for d in kb["documentos"]}
DOCUMENTED = {d["clase"] for d in kb["documentos"] if d["causa_documentada"] and d["clase"] != 0}

feat = pd.read_parquet(os.path.join(RES, "dev_features.parquet"))
y = feat["faultNumber"].to_numpy()
groups = feat["faultNumber"].to_numpy() * 1000 + feat["simulationRun"].to_numpy()
VARS = [c[:-5] for c in feat.columns if c.endswith("_mean")]
Xfull = np.load(os.path.join(RES, "dev_windows_ext.npy"))
DOCVAR = np.zeros((21, len(VARS)), np.float32)
for c, d_ in ((d["clase"], d) for d in kb["documentos"]):
    for v in d_["variables_documentadas"]:
        DOCVAR[c, VARS.index(v)] = 1.0

# ---------------------------------------------------------------- 1 and 2, from the log
recs = []
with open(LOG, encoding="utf-8") as fh:
    for pos, line in enumerate(fh):
        r = json.loads(line)
        recs.append(dict(pos=pos, arm=r["arm"], seed=r["seed"], fold=r["fold"],
                         run=tuple(r["id"]), y=r["label"], top1=r["decide"]["top3"][0],
                         top3=tuple(r["decide"]["top3"]), act=r["decide"]["accion"],
                         iters=r["costo"]["iteraciones"]))
log = pd.DataFrame(recs)
pro = log[log.arm == "proposed"].reset_index(drop=True)
print("episodios del brazo propuesto: %d" % len(pro))

per = []
for c in CLASSES:
    m = pro.y == c
    rec1 = float((pro.loc[m, "top1"] == c).mean())
    rec3 = float(pro.loc[m, "top3"].apply(lambda t: c in t).mean())
    pre = float((pro.loc[pro.top1 == c, "y"] == c).mean()) if (pro.top1 == c).any() else 0.0
    f1 = 2 * pre * rec1 / (pre + rec1) if pre + rec1 else 0.0
    wrong = pro.loc[m & (pro.top1 != c), "top1"]
    taken = int(wrong.value_counts().idxmax()) if len(wrong) else -1
    per.append(dict(clase=int(c), nombre=NAME[c], F1=f1, Recall1=rec1, Recall3=rec3,
                    taken_for=NAME.get(taken, "-"), taken_for_class=taken,
                    taken_times=int((wrong == taken).sum()) if taken >= 0 else 0,
                    called_normal=int((pro.loc[m, "top1"] == 0).sum()),
                    moves_window=float((pro.loc[m, "iters"] == 2).mean()),
                    defers=float((pro.loc[m, "act"] == "defer").mean())))
p = pd.DataFrame(per).set_index("clase")
p.to_csv(os.path.join(ERR, "worst_errors.csv"))

faults = p.drop(index=0)
missed = int(faults["called_normal"].sum())                     # a fault read as normal
false_alarm = int((pro.loc[pro.y == 0, "top1"] != 0).sum())      # normal read as a fault
print("\nel error que mas cuesta, en numeros:")
print("  falla leida como operacion normal : %5d de %5d episodios de falla (%.1f%%)"
      % (missed, int((pro.y != 0).sum()), 100.0 * missed / int((pro.y != 0).sum())))
print("  normal leida como falla           : %5d de %5d episodios normales (%.1f%%)"
      % (false_alarm, int((pro.y == 0).sum()), 100.0 * false_alarm / int((pro.y == 0).sum())))

print("\nlos cinco peores por F1:")
print("  %-6s %-18s %6s %8s  %-22s %8s" % ("clase", "nombre", "F1", "Recall@1", "se lee como", "mueve"))
for c, r in p.sort_values("F1").head(5).iterrows():
    print("  %-6d %-18s %6.3f %8.3f  %-22s %7.0f%%"
          % (c, r.nombre, r.F1, r.Recall1, "%s (%d)" % (r.taken_for, r.taken_times), 100 * r.moves_window))


# ---------------------------------------------------------------- 3, recomputed
def make_cnn():
    return nn.Sequential(nn.Conv1d(len(VARS), 32, 5, padding=2), nn.BatchNorm1d(32), nn.ReLU(),
                         nn.Conv1d(32, 64, 3, padding=1), nn.BatchNorm1d(64), nn.ReLU(),
                         nn.AdaptiveAvgPool1d(1), nn.Flatten(), nn.Dropout(0.2),
                         nn.Linear(64, 21))


def slice_window(moved):
    off = MOVE if moved else 0
    return np.ascontiguousarray(Xfull[:, :, off:off + W])


def perceive(Xw, m, s):
    z = (Xw - m) / s
    over = np.abs(z) > ALARM_K
    alarming = over.any(axis=2)
    first = np.where(alarming, over.argmax(axis=2), W)
    peak = np.abs(z).max(axis=2)
    dev = (Xw.mean(axis=2) - m[0, :, 0]) / s[0, :, 0]
    return alarming, first, peak, dev


def retrieve_all(dev_v, al_v, sig):
    q = np.where(al_v, dev_v, 0.0)
    flat = np.linalg.norm(q, axis=1) < 1e-8
    q[flat] = dev_v[flat]
    qn = np.maximum(np.linalg.norm(q, axis=1), 1e-8)
    cos = (q @ sig.T) / (np.linalg.norm(sig, axis=1)[None, :] * qn[:, None] + 1e-12)
    e = np.exp(cos - cos.max(axis=1, keepdims=True))
    return e / e.sum(axis=1, keepdims=True)


print("\nrecomputando el orden de alarmas para el Recall@N ...")
hits = {(arm, n): [] for arm in ("chrono", "lookup", "proposed") for n in range(1, N_MAX + 1)}
for seed in EST_SEEDS:
    sgkf = StratifiedGroupKFold(n_splits=K, shuffle=True, random_state=seed)
    for fold, (tri, vai) in enumerate(sgkf.split(np.zeros((len(y), 1)), y, groups)):
        ck = torch.load(os.path.join(MODELS, "cnn_seed%d_fold%d.pt" % (seed, fold)), weights_only=False)
        net = make_cnn(); net.load_state_dict(ck["state_dict"]); net.eval()
        normal = tri[y[tri] == 0]
        pack = {}
        for moved in (False, True):
            Xw = slice_window(moved)
            m = Xw[normal].mean(axis=(0, 2), keepdims=True)
            sd = Xw[normal].std(axis=(0, 2), keepdims=True)
            sd = np.where(sd < 1e-8, 1.0, sd)
            al, fi, pk, dv = perceive(Xw, m, sd)
            sig = np.stack([dv[tri[y[tri] == c]].mean(axis=0) for c in CLASSES]).astype(np.float32)
            t = torch.from_numpy(np.ascontiguousarray((Xw[vai] - ck["mean"]) / ck["std"])).float()
            with torch.no_grad():
                pc = torch.softmax(net(t), dim=1).numpy()
            pack[moved] = (al, fi, pk, dv, sig, pc)
        for arm in ("lookup", "proposed"):
            al0, fi0, pk0, dv0, sig0, pc0 = pack[False]
            al1, fi1, pk1, dv1, sig1, pc1 = pack[True]
            pr0 = pc0 if arm == "lookup" else retrieve_all(dv0[vai], al0[vai], sig0)
            pr1 = pc1 if arm == "lookup" else retrieve_all(dv1[vai], al1[vai], sig1)
            agree0 = (pc0.argmax(1) == pr0.argmax(1)) if arm == "proposed" else np.ones(len(vai), bool)
            ready0 = agree0 & (pc0.max(1) >= TAU)
            flood0 = (pc0.argmax(1) == 0) & (al0[vai].sum(1) >= FLOOD_N)
            moved = ~(ready0 | flood0) & (MAX_MOVES >= 1)
            for j, i in enumerate(vai):
                c = y[i]
                if c not in DOCUMENTED:
                    continue
                al, fi, pk, _, _, _ = pack[bool(moved[j])]
                on = np.flatnonzero(al[i])
                if on.size == 0:
                    continue
                w = (pr1 if moved[j] else pr0)[j] @ DOCVAR
                order_k = on[np.lexsort((fi[i, on], -w[on]))]
                order_c = on[np.lexsort((-pk[i, on], fi[i, on]))]
                for n in range(1, N_MAX + 1):
                    hits[(arm, n)].append(any(VARS[v] in VAR_OF[c] for v in order_k[:n]))
                    if arm == "proposed":                       # chronology is the same for both
                        hits[("chrono", n)].append(any(VARS[v] in VAR_OF[c] for v in order_c[:n]))
    print("  semilla %d lista" % seed, flush=True)

rr = pd.DataFrame([{"ordering": a, "N": n, "recall": float(np.mean(hits[(a, n)])),
                    "episodes": len(hits[(a, n)])}
                   for a in ("chrono", "lookup", "proposed") for n in range(1, N_MAX + 1)])
rr.to_csv(os.path.join(ERR, "root_alarm_recall.csv"), index=False)
print("\nRECALL DE LA ALARMA RAIZ DENTRO DE LAS PRIMERAS N ALARMAS")
print("  %-28s %s" % ("orden", "  ".join("N=%d" % n for n in range(1, N_MAX + 1))))
for a, lab in (("chrono", "por tiempo"), ("lookup", "por evidencia, anclaje"),
               ("proposed", "por evidencia, sintomas")):
    v = rr[rr.ordering == a].sort_values("N")["recall"].to_numpy()
    print("  %-28s %s" % (lab, "  ".join("%.3f" % x for x in v)))

# ---------------------------------------------------------------- 4, the three cases
print("\nLOS TRES CASOS, POR LA REGLA DECLARADA")
worst_faults = [c for c in p.drop(index=0).sort_values("F1").index if p.loc[c, "called_normal"] > 0][:3]
picked = []
for c in worst_faults:
    ep = pro[(pro.y == c) & (pro.top1 == 0)].iloc[0]
    picked.append(ep)
    print("  %-10s F1 %.3f   primer episodio llamado normal: id %s, semilla %d, pliegue %d"
          % (NAME[c], p.loc[c, "F1"], list(ep.run), ep.seed, ep.fold))
# ------------------------------------------- 5, does waiting predict difficulty
# The article says the correlation between how often a class makes the copilot
# wait and how well it is then identified is -0.54. That number had no source in
# this repository and was computed by hand, which is the one thing the rest of
# the pipeline exists to avoid. It is written here so a reviewer can check it.
#
# The scope matters and is the reason a hand computation is easy to get wrong:
# over the twenty faults it is -0.54, over all twenty-one classes it is -0.56,
# because normal operation waits in 99.7% of its episodes and is identified at
# 0.207. The article says "over the twenty faults" and means it.
esperar = p["moves_window"].to_numpy()
acierto = p["F1"].to_numpy()
filas = []
for etiqueta, m in (("20 faults", p.index != 0), ("all 21 classes", p.index == p.index)):
    x, y = esperar[m], acierto[m]
    filas.append({"scope": etiqueta, "n": int(m.sum()),
                  "pearson_wait_vs_f1": round(float(np.corrcoef(x, y)[0, 1]), 4)})
pd.DataFrame(filas).to_csv(os.path.join(ERR, "wait_vs_f1.csv"), index=False)
print("\nESPERAR PREDICE DIFICULTAD?")
for f in filas:
    print("  %-16s n=%2d   r = %+.4f" % (f["scope"], f["n"], f["pearson_wait_vs_f1"]))
print("  (la del articulo es la de las 20 fallas; operacion normal espera en el")
print("   99.7% de sus episodios y acierta 0.207, asi que incluirla la mueve)")

print("\nwrote results/errors/worst_errors.csv, root_alarm_recall.csv and wait_vs_f1.csv")
