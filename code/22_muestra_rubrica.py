"""
22_muestra_rubrica.py - draw the thirty episodes of the human rubric.

Implements the rule pre-registered in PROTOCOLO.md, "Human rubric: the sampling
rule, the raters and the items", which was committed before this script was run.
The rule is not re-stated here in prose: it is read off the constants below, and
any change to them is a change to the pre-registration and has to be argued there.

  arm `proposed`, seed 42, at random inside each stratum with rng(20260917)

      generate, correct   14        defer    9
      generate, wrong      4        alert    3

Deliberately NOT part of run_all.py, which stays at 23 steps. The draw is
reproducible; the scoring by two people is not, and the human rubric is declared
as not reproducible by the command. Adding it would suggest otherwise.

Writes to results/rubrica_humana/:
  muestra.csv            the key: which text is which episode. The raters must
                         not open this until both sheets are back.
  lineas_log.jsonl       the thirty raw log lines, which is all the drafting step
                         is allowed to read, together with the cited document.
  hoja_<rater>.csv       one blank scoring sheet per rater, in shuffled order,
                         carrying no label, no probability and no episode id.

Refuses to overwrite a scoring sheet that already has marks in it.
"""
import os
import sys
import csv
import json

import numpy as np

BASE = os.path.dirname(os.path.abspath(__file__))
if not os.path.isfile(os.path.join(BASE, "requirements.txt")):
    BASE = os.path.dirname(BASE)      # the scripts live in code/, the project one level up
RES = os.path.join(BASE, "results")
LOG = os.path.join(RES, "logs", "decisiones.jsonl")
OUT = os.path.join(RES, "rubrica_humana")

ARM, SEED_LOG, RNG_SEED = "proposed", 42, 20260917
RATERS = ["josue", "christian"]
ITEMS = ["H1", "H2", "H3", "H4", "H5"]
# stratum -> how many to draw. The order here is the order of muestra.csv.
PLAN = [("generate_correcto", 14), ("generate_equivocado", 4),
        ("defer", 9), ("alert", 3)]


def stratum_of(d):
    """Which pre-registered stratum an episode falls in, or None if it is not eligible."""
    a = d["decide"]["accion"]
    if a == "generate":
        return "generate_correcto" if d["decide"]["top3"][0] == d["label"] \
            else "generate_equivocado"
    return a if a in ("defer", "alert") else None


def main():
    assert os.path.isfile(LOG), "run 12_agente_v1.py first: %s is missing" % LOG

    pools = {k: [] for k, _ in PLAN}
    with open(LOG, encoding="utf-8") as fh:
        for line in fh:
            d = json.loads(line)
            if d["arm"] != ARM or d["seed"] != SEED_LOG:
                continue
            s = stratum_of(d)
            if s in pools:
                pools[s].append(d)

    print("pool (arm %s, seed %d):" % (ARM, SEED_LOG))
    for k, n in PLAN:
        print("   %-20s %6d available, drawing %2d" % (k, len(pools[k]), n))
        assert len(pools[k]) >= n, (
            "stratum %s has %d episodes and the rule asks for %d" % (k, len(pools[k]), n))

    rng = np.random.default_rng(RNG_SEED)
    drawn = []
    for k, n in PLAN:
        # sort by id first: dict order depends on how the file was written, and the
        # draw has to depend only on the declared seed
        pool = sorted(pools[k], key=lambda d: (d["fold"], d["id"]))
        for i in rng.choice(len(pool), size=n, replace=False):
            drawn.append((k, pool[int(i)]))
    assert len(drawn) == sum(n for _, n in PLAN)

    os.makedirs(OUT, exist_ok=True)

    # the shuffled order the raters see, so consecutive texts are not one stratum
    order = rng.permutation(len(drawn))
    texto_de = {int(j): i + 1 for i, j in enumerate(order)}   # episode index -> text number

    key = os.path.join(OUT, "muestra.csv")
    with open(key, "w", encoding="utf-8", newline="\n") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["texto", "estrato", "fold", "id", "accion", "label", "top1",
                    "cita", "concuerda", "n_alarmas"])
        for i, (k, d) in enumerate(drawn):
            w.writerow([texto_de[i], k, d["fold"], json.dumps(d["id"]),
                        d["decide"]["accion"], d["label"], d["decide"]["top3"][0],
                        (d["razona"] or {}).get("cita", ""),
                        d["decide"].get("concuerda"),
                        d["percibe"]["n_alarmas"]])
    print("\nwrote", key, "  <- the key, not for the raters")

    src = os.path.join(OUT, "lineas_log.jsonl")
    with open(src, "w", encoding="utf-8", newline="\n") as fh:
        for i, (_, d) in enumerate(drawn):
            fh.write(json.dumps({"texto": texto_de[i], "log": d}, ensure_ascii=False) + "\n")
    print("wrote", src, "  <- all the drafting step may read")

    for r in RATERS:
        p = os.path.join(OUT, "hoja_%s.csv" % r)
        if os.path.isfile(p):
            with open(p, encoding="utf-8") as fh:
                marked = [ln for ln in list(csv.reader(fh))[1:] if any(c.strip() for c in ln[1:])]
            if marked:
                print("SKIP  %s already has %d scored rows, not overwriting"
                      % (os.path.basename(p), len(marked)))
                continue
        with open(p, "w", encoding="utf-8", newline="\n") as fh:
            w = csv.writer(fh, lineterminator="\n")
            w.writerow(["texto"] + ITEMS + ["nota"])
            for t in range(1, len(drawn) + 1):
                w.writerow([t] + [""] * (len(ITEMS) + 1))
        print("wrote", p, "  <- blank, shuffled, no label and no id")

    print("\nH1..H5 are declared in PROTOCOLO.md. Score 1 for yes, 0 for no, and")
    print("leave nothing blank; H5 is the one where yes is the bad answer.")
    print("Draw is deterministic: rng(%d) over the pools printed above." % RNG_SEED)


if __name__ == "__main__":
    sys.exit(main())
