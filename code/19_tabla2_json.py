r"""
results/tabla2.json: every number of Table II in one file, read from the run records.

One row per model, with the primary metric and the secondary metric given per seed
rather than already averaged, so the paragraph and the table can be produced without
recomputing anything and without anyone retyping a value. Nothing here is measured:
it is a consolidation of files that other steps already wrote.

  primary    macro-F1 per seed, from results/per_fold_f1.csv
  secondary  Recall@3 per seed, from results/per_fold_recall3.csv
  cost       from results/cost_table.csv, plus the per-decision seconds of
             results/agente_comparison.csv for the arms that have a loop

A field that does not exist for a row is null, never a guess. The two agent rows
train nothing, so their training time is 0 and not null: that is a measured zero.
Tokens are 0 for every row because the reasoning step is rule-based and no language
model is called anywhere in the pipeline; that zero is a property of the design and
is recorded so the table can state it.

Output:
  results/tabla2.json
"""
import os
import json
import numpy as np
import pandas as pd

BASE = os.path.dirname(os.path.abspath(__file__))
if not os.path.isfile(os.path.join(BASE, "requirements.txt")):
    BASE = os.path.dirname(BASE)      # the scripts live in code/, the project one level up
RES = os.path.join(BASE, "results")

f1 = pd.read_csv(os.path.join(RES, "per_fold_f1.csv"))
r3 = pd.read_csv(os.path.join(RES, "per_fold_recall3.csv"))
cost = pd.read_csv(os.path.join(RES, "cost_table.csv")).set_index("row")
ag = pd.read_csv(os.path.join(RES, "agente_comparison.csv")).set_index("arm")

# the eight rows of Table II, in the order the table prints them
ROWS = [
    ("Trivial", "trivial", None, "floor"),
    ("Logistic reg.", "logistic", None, "classic"),
    ("Random forest", "rf", None, "classic"),
    ("Gradient boost.", "hgb", None, "classic"),
    ("v1a MLP", "mlp", None, "network"),
    ("v1b 1D-CNN", "cnn", None, "network"),
    ("No agent (abl.)", "ablation", "ablation", "agent"),
    ("Copilot v1", "proposed", "proposed", "agent"),
]
SEEDS = sorted(f1["seed"].unique().tolist())


def by_seed(df, col):
    """Mean over the folds of each seed: the seed is the unit that repeats."""
    g = df.groupby("seed")[col].mean()
    return {str(s): round(float(g[s]), 6) for s in SEEDS}


out = {
    "_meta": {
        "source": "consolidated by 19_tabla2_json.py from the run records; nothing measured here",
        "primary": "macro-F1 on validation",
        "secondary": "Recall@3 on validation",
        "seeds": SEEDS,
        "folds_per_seed": int(f1.groupby("seed").size().iloc[0]),
        "unit_of_repetition": "seed; each value is the mean over that seed's folds",
        "dispersion_in_table": "std_over_folds, the convention Section IV declares",
        "partition": "frozen by simulation run, test set sealed",
        "reads": ["per_fold_f1.csv", "per_fold_recall3.csv", "cost_table.csv",
                  "agente_comparison.csv"],
    },
    "models": [],
}

for label, key, arm, kind in ROWS:
    c = cost.loc[label]
    row = {
        "name": label,
        "kind": kind,
        "primary_by_seed": by_seed(f1, key),
        "secondary_by_seed": by_seed(r3, key),
        "cost": {
            "parameters": int(c["size"]),
            "parameters_are": c["size_is"],
            # the paper's cost column carries seconds; minutes are given too because
            # that is the unit the request asks for, and both come from one number
            "training_seconds": round(float(c["train_s"]), 3),
            "training_minutes": round(float(c["train_s"]) / 60.0, 4),
            "inference_ms_per_episode": round(float(c["inference_ms"]), 4),
            "seconds_per_decision": (round(float(ag.loc[arm, "s_per_decision"]), 6)
                                     if arm else None),
            # rule-based reasoning: no language model is called anywhere
            "tokens": 0,
            "source": c["source"],
        },
    }
    # Two dispersions, because they answer different questions and the paper uses
    # both: the table quotes the spread over the 15 folds, which is what a reader
    # compares two rows with; the paired analysis of step 14 uses the spread over
    # the three seed means, which is the unit that actually repeats.
    for m, src, col in (("primary", f1, key), ("secondary", r3, key)):
        v = np.array(list(row["%s_by_seed" % m].values()), float)
        row["%s_mean" % m] = round(float(v.mean()), 6)
        row["%s_std_over_seeds" % m] = round(float(v.std(ddof=1)), 6)
        # ddof=0, the divisor the pipeline has used since step 04, so the generated
        # table reproduces the one in the paper instead of quietly shifting every +-
        row["%s_std_over_folds" % m] = round(float(src[col].std(ddof=0)), 6)
    out["models"].append(row)

with open(os.path.join(RES, "tabla2.json"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=2, ensure_ascii=False)

print("results/tabla2.json: %d filas, semillas %s" % (len(out["models"]), SEEDS))
print("\n%-17s %-24s %-24s %s" % ("fila", "macro-F1 por semilla", "Recall@3 por semilla", "costo"))
print("-" * 104)
for r in out["models"]:
    p = " ".join("%.3f" % v for v in r["primary_by_seed"].values())
    s = " ".join("%.3f" % v for v in r["secondary_by_seed"].values())
    k = r["cost"]
    print("%-17s %-24s %-24s %s / %.1f s / %.3f ms"
          % (r["name"], p, s, "{:,}".format(k["parameters"]),
             k["training_seconds"], k["inference_ms_per_episode"]))
nulls = sum(1 for r in out["models"] if r["cost"]["seconds_per_decision"] is None)
print("\ncampos nulos: %d filas sin segundos por decision (las que no tienen lazo)" % nulls)
