r"""
The main figure, in two panels.

Panel A  macro-F1 against the percentage of labeled runs, for the three classical
         models and for the label-anchored arm of the copilot, which scores as
         the ablation does.
Panel B  root-alarm identification on the same budgets: ordering alarms by time,
         and ordering them by retrieved evidence in each of the two grounded arms.

Reads results/label_efficiency_curve.csv (from 08) and
results/label_efficiency_agent.csv (from 16). Panel B is skipped if the second
file is absent, so the figure still builds from the classics alone.

Outputs:
  results/label_efficiency_curve.pdf  <- vector, the one the paper includes
  results/label_efficiency_curve.png  <- 300 dpi raster, for quick viewing

The figure rules this file implements are declared in PROTOCOLO.md.
"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")           # no GUI needed
import matplotlib.pyplot as plt

BASE = os.path.dirname(os.path.abspath(__file__))
if not os.path.isfile(os.path.join(BASE, "requirements.txt")):
    BASE = os.path.dirname(BASE)      # the scripts live in code/, the project one level up
RES = os.path.join(BASE, "results")
CSV = os.path.join(RES, "label_efficiency_curve.csv")
CSV_AG = os.path.join(RES, "label_efficiency_agent.csv")
assert os.path.exists(CSV), "run 08_label_efficiency.py first"

TRIVIAL_F1 = 0.004   # macro-F1 of the trivial baseline (from 04; 0.0043)

# Okabe-Ito, safe for the common colour vision deficiencies, and paired with a
# distinct dash pattern and marker so the series survive a grayscale print.
STYLE = {
    "logistic": dict(color="#0072B2", marker="^", ls="-",             label="Logistic regression"),
    "rf":       dict(color="#D55E00", marker="s", ls=(0, (4, 2)),     label="Random forest"),
    "hgb":      dict(color="#009E73", marker="o", ls=(0, (1, 2)),     label="Gradient boosting"),
    "copilot":  dict(color="#000000", marker="D", ls=(0, (6, 2, 1, 2)), label="Copilot, label-anchored"),
}
STYLE_B = {
    "chrono":   dict(color="#666666", marker="v", ls=(0, (1, 2)),     label="By time"),
    "lookup":   dict(color="#000000", marker="D", ls=(0, (6, 2, 1, 2)), label="By evidence, label-anchored"),
    "proposed": dict(color="#CC79A7", marker="P", ls="-",             label="By evidence, symptoms"),
}

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "DejaVu Serif"],
    # 8 pt everywhere: the figure is emitted at exactly one column, so LaTeX does
    # not rescale it and 8 pt on paper is 8 pt here.
    "font.size": 8, "axes.labelsize": 8, "axes.titlesize": 8,
    "xtick.labelsize": 8, "ytick.labelsize": 8, "legend.fontsize": 7,
    "axes.linewidth": 0.6, "lines.linewidth": 1.2, "lines.markersize": 3.2,
    "figure.dpi": 300,
})

df = pd.read_csv(CSV)
ag = pd.read_csv(CSV_AG) if os.path.exists(CSV_AG) else None
if ag is None:
    print("note: results/label_efficiency_agent.csv not found, drawing panel A only")

COL_CM = 8.89 / 2.54                       # one IEEE column, in inches
fig, axes = plt.subplots(2 if ag is not None else 1, 1, figsize=(COL_CM, 9.0 / 2.54 if ag is not None else 2.65),
                         sharex=True, constrained_layout=True)
axes = np.atleast_1d(axes)
axA = axes[0]


def por_semilla(d, col):
    """media por presupuesto y desviacion entre las medias de cada semilla.

    Promediar los 15 pliegues de una vez mezcla la variacion del reparto con la
    de la semilla. El paper compara promediando por semilla primero, y la banda
    de esta figura es esa misma dispersion."""
    m = d.groupby(["pct_of_dev_labels", "seed"])[col].mean().reset_index()
    g = m.groupby("pct_of_dev_labels")[col].agg(["mean", "std"]).reset_index()
    g["std"] = m.groupby("pct_of_dev_labels")[col].std(ddof=0).to_numpy()
    return g

def band(ax, x, m, s, st):
    ax.fill_between(x, m - s, m + s, color=st["color"], alpha=0.13, linewidth=0)
    ax.plot(x, m, color=st["color"], marker=st["marker"], linestyle=st["ls"], label=st["label"])


# ---------------------------------------------------------------- panel A
for kind in ("logistic", "rf", "hgb"):
    d = df[df.model == kind].sort_values("pct_of_dev_labels")
    band(axA, d["pct_of_dev_labels"].to_numpy(), d["F1macro_mean"].to_numpy(),
         d["F1macro_std_over_seeds"].to_numpy(), STYLE[kind])
if ag is not None:
    g = por_semilla(ag[ag.arm == "lookup"], "F1macro")
    band(axA, g["pct_of_dev_labels"].to_numpy(), g["mean"].to_numpy(), g["std"].to_numpy(), STYLE["copilot"])

ceiling = float(df[df.pct_of_dev_labels == 100]["F1macro_mean"].max())
axA.axhline(ceiling, color="#3a3a3a", linestyle=(0, (5, 3)), linewidth=0.8)
axA.text(0.22, ceiling + 0.02, "classical ceiling (%.2f)" % ceiling, fontsize=6.5, color="#444444")
axA.axhline(TRIVIAL_F1, color="#999999", linestyle=(0, (2, 3)), linewidth=0.8)
# a la derecha del primer presupuesto: con la figura mas baja, ahi abajo a la
# izquierda ya pasa la curva de gradient boosting
axA.text(1.5, TRIVIAL_F1 + 0.02, "trivial baseline (%.3f)" % TRIVIAL_F1, fontsize=6.5, color="#777777")
axA.set_ylabel(r"Macro $F_1$ (0 to 1)")
axA.set_ylim(0.0, 0.85)
axA.legend(loc="lower right", frameon=False, ncol=1, handlelength=2.6)
axA.set_title("(a)  Identifying the fault", fontsize=8, loc="left", pad=3)

# ---------------------------------------------------------------- panel B
if ag is not None:
    axB = axes[1]
    g = por_semilla(ag[ag.arm == "lookup"], "RootAlarmChrono")
    band(axB, g["pct_of_dev_labels"].to_numpy(), g["mean"].to_numpy(), g["std"].to_numpy(), STYLE_B["chrono"])
    for arm in ("lookup", "proposed"):
        g = por_semilla(ag[ag.arm == arm], "RootAlarmKB")
        band(axB, g["pct_of_dev_labels"].to_numpy(), g["mean"].to_numpy(), g["std"].to_numpy(), STYLE_B[arm])
    axB.set_ylabel("Root alarm found\n(fraction of episodes)")
    axB.set_ylim(0.0, 0.85)
    axB.legend(loc="lower right", frameon=False, handlelength=2.6)
    axB.set_title("(b)  Naming the alarm that started it", fontsize=8, loc="left", pad=3)
    bottom = axB
else:
    bottom = axA

ticks = sorted(df["pct_of_dev_labels"].unique())


def readable(ts, gap=0.18):
    """Label a budget only if it clears the previous label on the log axis.

    Every budget keeps its tick mark, so each measured point stays locatable;
    what is dropped is only the text. Without this, 10 and 12.5 are 0.097 apart
    in log10 against a 0.30 typical gap, and they print as "1012.5"."""
    out, last = [], None
    for t in ts:
        if last is None or np.log10(t) - np.log10(last) >= gap:
            out.append("%g" % t)
            last = t
        else:
            out.append("")
    return out


bottom.set_xscale("log")
bottom.set_xticks(ticks)
bottom.set_xticklabels(readable(ticks))
bottom.minorticks_off()
bottom.set_xlabel("Labeled runs (% of the development pool, log scale)")
bottom.set_xlim(0.2, 130)
for ax in axes:
    ax.grid(True, which="major", color="#e8e8e8", linewidth=0.5)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)

# No bbox_inches="tight": it would change the emitted width and make LaTeX rescale
# the text below 8 pt. The figure is already exactly one column wide.
for ext in ("pdf", "png"):
    out = os.path.join(RES, "label_efficiency_curve." + ext)
    # CreationDate=None keeps the PDF byte-identical across runs. Without it the
    # file carries a timestamp, so every re-run shows up as a change to a figure
    # whose content did not move: seven bytes of noise in a repository whose
    # claim is that re-running reproduces the results. 13_plot_architecture.py
    # has done this since it was written; this figure was missed.
    fig.savefig(out, metadata={"CreationDate": None} if ext == "pdf" else None)
    print("wrote", out)
plt.close(fig)

# ---------------------------------------------------------------- what it says
if ag is not None:
    lk = ag[ag.arm == "lookup"].groupby("pct_of_dev_labels")[["F1macro", "RootAlarmKB"]].mean()
    top_f1, top_rk = lk.loc[100.0, "F1macro"], lk.loc[100.0, "RootAlarmKB"]
    print("\nlabels needed to reach 90% of the value at full supervision (label-anchored arm):")
    for col, top, name in (("F1macro", top_f1, "macro-F1"), ("RootAlarmKB", top_rk, "root alarm")):
        hit = lk[lk[col] >= 0.90 * top]
        if len(hit):
            print("  %-11s %.4f at full supervision, 90%% of it (%.4f) reached with %g%% of the labels"
                  % (name, top, 0.90 * top, hit.index[0]))
