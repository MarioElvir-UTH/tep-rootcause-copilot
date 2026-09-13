r"""
S2 figure: publication-quality label efficiency curve,
macro-F1 versus the percentage of labeled runs, with the supervised ceiling drawn.
Reads results/label_efficiency_curve.csv (produced by 08_label_efficiency.py).

Outputs:
  results/label_efficiency_curve.pdf  <- vector, \includegraphics in the paper
  results/label_efficiency_curve.png  <- 300 dpi raster, for quick viewing / slides

Decoupled from the experiment on purpose: restyling the figure never re-runs the models.
"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")           # no GUI needed
import matplotlib.pyplot as plt

BASE = r"C:\Users\melvi\Documents\Maestria\19. Seminario de Tesis II\Anteproyecto - Seminario II"
RES = os.path.join(BASE, "results")
CSV = os.path.join(RES, "label_efficiency_curve.csv")
assert os.path.exists(CSV), "run 08_label_efficiency.py first"

TRIVIAL_F1 = 0.004   # macro-F1 of the trivial majority-class baseline (from 04; 0.0043)
STYLE = {
    "logistic": dict(color="#2e7d32", marker="^", label="Logistic regression (C 10)"),
    "rf":       dict(color="#c1531a", marker="s", label="Random forest (depth 20)"),
    "hgb":      dict(color="#1f5fa8", marker="o", label="Gradient boosting (lr 0.05)"),
}

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "DejaVu Serif"],
    "font.size": 8, "axes.labelsize": 8, "axes.titlesize": 8,
    "xtick.labelsize": 7, "ytick.labelsize": 7, "legend.fontsize": 7,
    "axes.linewidth": 0.6, "lines.linewidth": 1.3, "lines.markersize": 3.4,
    "figure.dpi": 300,
})

df = pd.read_csv(CSV)
fig, ax = plt.subplots(figsize=(3.5, 2.65))

for kind, st in STYLE.items():
    d = df[df.model == kind].sort_values("pct_of_dev_labels")
    x = d["pct_of_dev_labels"].to_numpy()
    m = d["F1macro_mean"].to_numpy()
    s = d["F1macro_std"].to_numpy()
    ax.fill_between(x, m - s, m + s, color=st["color"], alpha=0.15, linewidth=0)
    ax.plot(x, m, color=st["color"], marker=st["marker"], label=st["label"])

# reference line: supervised ceiling = best macro-F1 at 100% of the labels
ceiling = float(df[df.pct_of_dev_labels == 100]["F1macro_mean"].max())
ax.axhline(ceiling, color="#3a3a3a", linestyle=(0, (5, 3)), linewidth=0.9)
ax.text(0.22, ceiling + 0.013, f"supervised ceiling ({ceiling:.2f}, all labels)", fontsize=6, color="#444444")

# trivial floor
ax.axhline(TRIVIAL_F1, color="#999999", linestyle=(0, (2, 3)), linewidth=0.8)
ax.text(0.22, TRIVIAL_F1 + 0.013, f"trivial baseline ({TRIVIAL_F1:.3f})", fontsize=6, color="#777777")

ax.set_xscale("log")
ticks = sorted(df["pct_of_dev_labels"].unique())
ax.set_xticks(ticks)
ax.set_xticklabels([f"{t:g}" for t in ticks])
ax.minorticks_off()
ax.set_xlabel("Labeled runs (% of development pool, log scale)")
ax.set_ylabel(r"Macro $F_1$")
ax.set_ylim(0.0, 0.72)
ax.set_xlim(0.2, 130)
ax.grid(True, which="major", color="#e8e8e8", linewidth=0.5)
ax.set_axisbelow(True)
for side in ("top", "right"):
    ax.spines[side].set_visible(False)
ax.legend(loc="lower right", frameon=False, bbox_to_anchor=(1.0, 0.10))

fig.tight_layout(pad=0.3)
pdf = os.path.join(RES, "label_efficiency_curve.pdf")
png = os.path.join(RES, "label_efficiency_curve.png")
fig.savefig(pdf, bbox_inches="tight")
fig.savefig(png, bbox_inches="tight")
plt.close(fig)

print("saved:")
print(" ", pdf)
print(" ", png)
print(f"\nmacro-F1 vs % labels | supervised ceiling = {ceiling:.4f} | matplotlib {matplotlib.__version__}")
print(r"LaTeX usage:  \includegraphics[width=\columnwidth]{label_efficiency_curve.pdf}")
