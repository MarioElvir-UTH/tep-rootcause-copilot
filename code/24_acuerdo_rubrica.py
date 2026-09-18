"""
24_acuerdo_rubrica.py - agreement and per-item results of the human rubric.

Written BEFORE the sheets came back, on purpose. Writing it afterwards, with the
answers on screen, is an invitation to pick the statistic that looks best, which
is the same failure the sampling rule was committed early to avoid.

Reports, per item, exactly the three things PROTOCOLO.md declares:

    Cohen's kappa, raw percent agreement, and both raters' marginals

All three, never one. H2 is expected to be almost all yes, and kappa is unstable
under a marginal that lopsided: it can sit near zero while the raters agree on
29 of 30 texts. Reporting it alone would mislead in either direction, so this
script refuses to print any of the three without the other two.

Four decisions, each of which could have gone the other way:

  - **No pooled score.** There is no third adjudicator, so each rater is reported
    separately. Averaging the two would invent a consensus that nobody reached.
  - **No rubric total.** H5 is inverted, where yes is the bad answer, so a total
    would add a penalty to four rewards. The items are reported point by point.
  - **Kappa can be undefined, and says so.** When both raters use one category for
    every text, the expected agreement is 1 and kappa is 0/0. That is printed as
    undefined, never as 0 and never as 1.
  - **A bootstrap interval, because n is 30.** A bare kappa over thirty texts is
    noisier than it looks. Percentile interval over texts, 10,000 resamples,
    seed declared below. Resamples where kappa is undefined are counted and
    reported rather than dropped in silence.

Per stratum only the rater means and raw agreement are reported, not kappa: the
strata are 14, 4, 9 and 3 texts, and a kappa over three texts is noise with a
Greek letter on it.

Reads results/rubrica_humana/{hoja_*.csv, muestra.csv}. Writes acuerdo.csv and
acuerdo_por_estrato.csv beside them. Not part of run_all.py: the human rubric is
declared as not reproducible by the command.
"""
import os
import sys
import csv
import json

import numpy as np

BASE = os.path.dirname(os.path.abspath(__file__))
if not os.path.isfile(os.path.join(BASE, "requirements.txt")):
    BASE = os.path.dirname(BASE)      # the scripts live in code/, the project one level up
OUT = os.path.join(BASE, "results", "rubrica_humana")

RATERS = ["josue", "christian"]
ITEMS = ["H1", "H2", "H3", "H4", "H5"]
INVERTIDO = {"H5"}                    # the one where yes is the bad answer
B, SEED = 10000, 20260917             # bootstrap resamples, and the declared seed

PREGUNTA = {
    "H1": "una causa y dos alternativas, en ese orden, en seis frases o menos",
    "H2": "el documento citado existe y dice lo que el texto le atribuye",
    "H3": "donde hay discrepancia, el texto la declara en vez de esconderla",
    "H4": "actuarias con esto a las tres de la manana sin otra pregunta",
    "H5": "el texto afirma algo que la evidencia recuperada no sostiene",
}


def lee_hoja(r):
    """One rater's sheet as {texto: {item: 0|1}}, refusing anything incomplete."""
    p = os.path.join(OUT, "hoja_%s.csv" % r)
    if not os.path.isfile(p):
        raise SystemExit("ABORT - falta %s" % p)
    filas, malas = {}, []
    with open(p, encoding="utf-8") as fh:
        for fila in csv.DictReader(fh):
            t = int(fila["texto"])
            v = {}
            for it in ITEMS:
                s = (fila.get(it) or "").strip()
                if s not in ("0", "1"):
                    malas.append("texto %2d, %s: %r" % (t, it, s))
                else:
                    v[it] = int(s)
            filas[t] = v
    if malas:
        print("ABORT - la hoja de %s tiene %d casillas sin 0 o 1:" % (r, len(malas)))
        for m in malas[:12]:
            print("    " + m)
        if len(malas) > 12:
            print("    ... y %d mas" % (len(malas) - 12))
        print("\n   Se califica 1 para si, 0 para no, sin dejar nada en blanco.")
        raise SystemExit(1)
    return filas


def kappa(a, b):
    """Cohen's kappa for two binary raters, and None when it is undefined.

    Undefined is a real outcome here, not an error: if both raters answer yes to
    every text, expected agreement is 1 and the formula is 0/0. Returning 0 would
    read as "no agreement" and returning 1 as "perfect", and both are claims the
    data does not support.
    """
    a, b = np.asarray(a), np.asarray(b)
    n = len(a)
    po = float(np.mean(a == b))
    pa1, pb1 = float(np.mean(a)), float(np.mean(b))
    pe = pa1 * pb1 + (1 - pa1) * (1 - pb1)
    if abs(1.0 - pe) < 1e-12:
        return None, po, n
    return (po - pe) / (1 - pe), po, n


def intervalo(a, b, rng):
    """Percentile interval for kappa, resampling texts. Undefined draws are counted."""
    a, b = np.asarray(a), np.asarray(b)
    n = len(a)
    ks, indef = [], 0
    for idx in rng.integers(0, n, size=(B, n)):
        k, _, _ = kappa(a[idx], b[idx])
        if k is None:
            indef += 1
        else:
            ks.append(k)
    if not ks:
        return None, None, indef
    return float(np.percentile(ks, 2.5)), float(np.percentile(ks, 97.5)), indef


def control(A, Bv):
    """Cross-check kappa against scikit-learn, which is already a dependency."""
    try:
        from sklearn.metrics import cohen_kappa_score
    except Exception:
        return "   control: scikit-learn no disponible, kappa sin verificar"
    peor = 0.0
    for it in ITEMS:
        a, b = A[it], Bv[it]
        k, _, _ = kappa(a, b)
        if k is None:
            continue
        peor = max(peor, abs(k - float(cohen_kappa_score(a, b))))
    return "   control: kappa coincide con scikit-learn, peor diferencia %.2e" % peor


def main():
    hojas = {r: lee_hoja(r) for r in RATERS}
    textos = sorted(hojas[RATERS[0]])
    for r in RATERS[1:]:
        if sorted(hojas[r]) != textos:
            raise SystemExit("ABORT - las dos hojas no cubren los mismos textos")

    estrato = {}
    with open(os.path.join(OUT, "muestra.csv"), encoding="utf-8") as fh:
        for fila in csv.DictReader(fh):
            estrato[int(fila["texto"])] = fila["estrato"]

    A = {it: np.array([hojas[RATERS[0]][t][it] for t in textos]) for it in ITEMS}
    Bv = {it: np.array([hojas[RATERS[1]][t][it] for t in textos]) for it in ITEMS}
    rng = np.random.default_rng(SEED)

    print("=" * 78)
    print("RUBRICA HUMANA  -  %d textos, %s y %s, sin tercero que desempate"
          % (len(textos), RATERS[0], RATERS[1]))
    print("=" * 78)

    filas = []
    for it in ITEMS:
        a, b = A[it], Bv[it]
        k, po, n = kappa(a, b)
        lo, hi, indef = intervalo(a, b, rng)
        filas.append({
            "item": it, "pregunta": PREGUNTA[it], "n": n,
            "marginal_%s" % RATERS[0]: round(float(a.mean()), 4),
            "marginal_%s" % RATERS[1]: round(float(b.mean()), 4),
            "acuerdo_crudo": round(po, 4),
            "kappa": "indefinida" if k is None else round(k, 4),
            "ic95_bajo": "" if lo is None else round(lo, 4),
            "ic95_alto": "" if hi is None else round(hi, 4),
            "remuestreos_indefinidos": indef,
            "invertido": it in INVERTIDO,
        })
        print("\n%s  %s" % (it, PREGUNTA[it]))
        if it in INVERTIDO:
            print("    (invertido: aqui el si es la respuesta mala)")
        print("    marginales   %-10s %.3f     %-10s %.3f"
              % (RATERS[0], a.mean(), RATERS[1], b.mean()))
        print("    acuerdo crudo   %.3f  (%d de %d textos)" % (po, int((a == b).sum()), n))
        if k is None:
            print("    kappa           indefinida: las dos hojas usan una sola categoria,")
            print("                    asi que el acuerdo esperado es 1 y la formula es 0/0")
        else:
            ic = "" if lo is None else "   IC95 [%+.3f, %+.3f]" % (lo, hi)
            print("    kappa           %+.3f%s" % (k, ic))
            if indef:
                print("                    %d de %d remuestreos quedaron indefinidos"
                      % (indef, B))

    print("\n" + "-" * 78)
    print("H5 aparte: un solo si descalifica ese texto")
    for r, M in zip(RATERS, (A, Bv)):
        cuales = [t for t, v in zip(textos, M["H5"]) if v == 1]
        print("    %-10s %d de %d textos con algo afuera de la evidencia%s"
              % (r, len(cuales), len(textos),
                 ("   textos " + ", ".join(map(str, cuales))) if cuales else ""))
    amb = [t for t, x, y in zip(textos, A["H5"], Bv["H5"]) if x == 1 and y == 1]
    print("    los dos     %d texto(s)%s"
          % (len(amb), ("   " + ", ".join(map(str, amb))) if amb else ""))

    print("\n" + "-" * 78)
    print("Por estrato. Sin kappa: con 14, 4, 9 y 3 textos seria ruido con letra griega.")
    por_estrato = []
    for e in ["generate_correcto", "generate_equivocado", "defer", "alert"]:
        idx = [i for i, t in enumerate(textos) if estrato[t] == e]
        if not idx:
            continue
        print("\n  %-22s n = %d" % (e, len(idx)))
        for it in ITEMS:
            a, b = A[it][idx], Bv[it][idx]
            por_estrato.append({
                "estrato": e, "item": it, "n": len(idx),
                "media_%s" % RATERS[0]: round(float(a.mean()), 4),
                "media_%s" % RATERS[1]: round(float(b.mean()), 4),
                "acuerdo_crudo": round(float(np.mean(a == b)), 4),
            })
            print("     %s   %-10s %.3f   %-10s %.3f   acuerdo %.3f"
                  % (it, RATERS[0], a.mean(), RATERS[1], b.mean(), np.mean(a == b)))

    for nombre, datos in (("acuerdo.csv", filas),
                          ("acuerdo_por_estrato.csv", por_estrato)):
        p = os.path.join(OUT, nombre)
        with open(p, "w", encoding="utf-8", newline="\n") as fh:
            w = csv.DictWriter(fh, fieldnames=list(datos[0]), lineterminator="\n")
            w.writeheader()
            w.writerows(datos)
        print("\nwrote", p)

    print("\n" + control(A, Bv))
    print("\nNo se imprime un total de la rubrica, y es a proposito: H5 esta")
    print("invertido, asi que sumarlo con H1 a H4 restaria un castigo a cuatro")
    print("premios. Los items se reportan uno por uno, como declara PROTOCOLO.md.")
    print("Tampoco se promedian los dos evaluadores: sin tercero que desempate,")
    print("promediarlos inventaria un consenso que nadie alcanzo.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
