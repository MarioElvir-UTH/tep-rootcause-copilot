r"""
Coverage, precision and the cost of human review, per arm.

An ablation that does not move the primary metric still has to be judged, and it
is judged on two things: the explanation (the rubric, in 12_agente_v1.py) and what
it costs the person. This script measures the second one from the decision log:
how often each arm answers, how often it hands the episode to the operator, how
right it is when it does answer, and how many alarms the operator is shown.

Nothing is recomputed from the models. Every number comes from
results/logs/decisiones.jsonl and results/agente_comparison.csv.

Output:
  results/human_load.csv
"""
import json, os
import numpy as np
import pandas as pd

B = os.path.dirname(os.path.abspath(__file__))
if not os.path.isfile(os.path.join(B, "requirements.txt")):
    B = os.path.dirname(B)      # the scripts live in code/, the project one level up
LOG = os.path.join(B, "results", "logs", "decisiones.jsonl")
ag = pd.read_csv(os.path.join(B, "results", "agente_comparison.csv")).set_index("arm")
dl = pd.read_csv(os.path.join(B, "results", "dl_comparison.csv")).set_index("model")
pf = pd.read_csv(os.path.join(B, "results", "per_fold_f1.csv"))

acc = {}
with open(LOG, encoding="utf-8") as fh:
    for line in fh:
        r = json.loads(line)
        k = (r["arm"], r["seed"], r["fold"])
        e = acc.setdefault(k, {"gen_hit": [], "def_hit": [], "moved": [], "act": []})
        hit = (r["decide"]["top3"][0] == r["label"])
        a = r["decide"]["accion"]
        e["act"].append(a)
        e["moved"].append(r["costo"]["iteraciones"] == 2)
        if a == "generate":
            e["gen_hit"].append(hit)
        elif a == "defer":
            e["def_hit"].append(hit)

arms = sorted({k[0] for k in acc})
rows = []
for arm in arms:
    per = {"gen_rate": [], "def_rate": [], "gen_acc": [], "def_acc": [], "move": []}
    for (a, s, f), e in acc.items():
        if a != arm:
            continue
        n = len(e["act"])
        per["gen_rate"].append(e["act"].count("generate") / n)
        per["def_rate"].append(e["act"].count("defer") / n)
        per["move"].append(float(np.mean(e["moved"])))
        per["gen_acc"].append(float(np.mean(e["gen_hit"])) if e["gen_hit"] else np.nan)
        per["def_acc"].append(float(np.mean(e["def_hit"])) if e["def_hit"] else np.nan)
    cnn = pf["cnn"].mean()
    rows.append({
        "arm": arm,
        "F1": float(ag.loc[arm, "F1macro_mean"]),
        "loop_gain_vs_cnn": float(ag.loc[arm, "F1macro_mean"]) - cnn,
        "move_pct": 100 * float(np.mean(per["move"])),
        "generate_pct": 100 * float(np.mean(per["gen_rate"])),
        "defer_pct": 100 * float(np.mean(per["def_rate"])),
        "acc_when_generate": 100 * float(np.nanmean(per["gen_acc"])),
        "acc_when_defer": 100 * float(np.nanmean(per["def_acc"])),
        "alarms_shown": float(ag.loc[arm, "AlarmsShown_mean"]),
        "alarm_reduction_pct": 100 * float(ag.loc[arm, "AlarmReduction_mean"]),
    })

d = pd.DataFrame(rows).set_index("arm")
pd.set_option("display.width", 200)
print("=" * 104)
print("COBERTURA, PRECISION Y CARGA HUMANA POR BRAZO")
print("=" * 104)
print("%-10s %7s %9s %8s %10s %8s %11s %11s %9s %9s" % (
    "brazo", "F1", "gan.lazo", "mueve%", "genera%", "difiere%",
    "acierto|gen", "acierto|dif", "alarmas", "reduc.%"))
print("-" * 104)
for a in ["ablation", "lookup", "proposed"]:
    r = d.loc[a]
    print("%-10s %7.4f %+9.4f %8.1f %10.1f %8.1f %11.1f %11.1f %9.2f %9.1f" % (
        a, r.F1, r.loop_gain_vs_cnn, r.move_pct, r.generate_pct, r.defer_pct,
        r.acc_when_generate, r.acc_when_defer, r.alarms_shown, r.alarm_reduction_pct))

print()
print("LECTURA:")
ab, pr = d.loc["ablation"], d.loc["proposed"]
print("  la ablacion mueve la ventana en %.0f%% de las decisiones, no en %.0f%%: el 66%% es del propuesto"
      % (ab.move_pct, pr.move_pct))
print("  el propuesto difiere %.0f%% contra %.0f%% de la ablacion: %.1f veces mas carga para el operador"
      % (pr.defer_pct, ab.defer_pct, pr.defer_pct / ab.defer_pct))
print("  pero cuando si responde acierta %.1f%% contra %.1f%%: cambia cobertura por precision"
      % (pr.acc_when_generate, ab.acc_when_generate))
print("  ganancia del lazo sobre la red sola: ablacion %+.4f, propuesto %+.4f"
      % (ab.loop_gain_vs_cnn, pr.loop_gain_vs_cnn))
d.round(4).to_csv(os.path.join(B, "results", "human_load.csv"))
print("\nwrote results/human_load.csv")
