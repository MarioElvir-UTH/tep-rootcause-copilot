"""
26_precision_kappa.py - what n = 30 buys, and what it does not.

PROTOCOLO.md committed to thirty episodes on 2026-09-14 without recording a
reason. The number is a convention, not a calculation, and this script is what
turns that admission into something checkable instead of a feeling.

It simulates two raters who agree on a fixed share of items and asks how precisely
kappa can be recovered at several sample sizes. Nothing here uses the real sheets,
which are blank: it is a property of the estimator and the sample size, knowable
before anyone scores anything, which is why it is committed before they do.

The raw agreement is included because at this sample size it is the statistic that
carries the weight, and the protocol's rule of reporting all three is doing real
work rather than being thorough for its own sake.

Not part of run_all.py. Prints a table; writes nothing.
"""
import sys

import numpy as np

SEED, R = 7, 20000                    # replicates per cell, and the declared seed
P_ACUERDO = 0.85                      # how often the two raters land on the same answer
TAMANOS = (30, 50, 100, 200)


def kappa(a, b):
    """Cohen's kappa, or nan where the expected agreement is 1 and it is undefined."""
    po = np.mean(a == b)
    pa, pb = np.mean(a), np.mean(b)
    pe = pa * pb + (1 - pa) * (1 - pb)
    return np.nan if abs(1 - pe) < 1e-12 else (po - pe) / (1 - pe)


def simula(rng, n, p_si, p_acuerdo=P_ACUERDO):
    """Distribution of the kappa estimate, and of the raw agreement, over R panels."""
    ks, pos = [], []
    for _ in range(R):
        a = (rng.random(n) < p_si).astype(int)
        b = np.where(rng.random(n) < p_acuerdo, a, 1 - a)
        k = kappa(a, b)
        pos.append(float(np.mean(a == b)))
        if not np.isnan(k):
            ks.append(k)
    lo, hi = np.percentile(ks, [2.5, 97.5])
    plo, phi = np.percentile(pos, [2.5, 97.5])
    return np.mean(ks), lo, hi, (hi - lo) / 2, (phi - plo) / 2, 1 - len(ks) / R


def tabla(rng, p_si, titulo):
    print("\n%s" % titulo)
    print("    n     kappa medio      IC95 de kappa        +- kappa   +- acuerdo crudo")
    for n in TAMANOS:
        m, lo, hi, h, ph, indef = simula(rng, n, p_si)
        extra = "   (%.1f%% indefinidas)" % (100 * indef) if indef > 0.005 else ""
        print("  %3d        %+.2f         [%+.2f, %+.2f]         %.2f          %.2f%s"
              % (n, m, lo, hi, h, ph, extra))


def main():
    rng = np.random.default_rng(SEED)
    print("Dos evaluadores que coinciden en %.0f%% de los items." % (100 * P_ACUERDO))
    print("%d paneles simulados por celda, semilla %d, intervalo percentil." % (R, SEED))

    tabla(rng, 0.5, "Prevalencia equilibrada, mitad de sies:")
    tabla(rng, 0.9, "Prevalencia desbalanceada, 90% de sies, como se espera en H2:")

    print("\nLectura: a n = 30 y prevalencia equilibrada, un kappa verdadero de 0.70")
    print("se reporta en cualquier parte entre 0.40 y 0.93, que cruza tres categorias")
    print("de la escala que todo el mundo cita. Desbalanceado, el intervalo cruza el")
    print("cero: H2 no podra descartar acuerdo nulo ni aunque los dos coincidan en 85")
    print("de cada 100. El acuerdo crudo, en cambio, aguanta este tamano.")
    print("\nPor eso el articulo reporta el intervalo y no el punto, y no usa")
    print("etiquetas como 'acuerdo sustancial' que treinta textos no sostienen.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
