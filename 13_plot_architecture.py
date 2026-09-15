r"""
Figure 1: the advisory architecture, drawn as the loop it actually is.

Renders the four pieces pre-registered in PROTOCOLO.md ("Figure 1 in text"):
perceive, score, reason, decide; the observe action that closes the loop; the
guard (the copilot never reaches the process); where the person is; and where the
Table II number is measured.

Drawn by code for the same reason the label-efficiency figure is: a diagram that
is redrawn by hand cannot drift away from the pipeline without someone noticing,
and every constant shown here is read from results/agente_env.json rather than
typed into the drawing.

Outputs:
  results/architecture_loop.pdf  <- vector, \includegraphics in the paper
  results/architecture_loop.png  <- 300 dpi raster, for quick viewing / slides

Reads results/agente_env.json (produced by 12_agente_v1.py). Decoupled from the
experiment on purpose: restyling the figure never re-runs the agent.
"""
import os
import json
import matplotlib
matplotlib.use("Agg")           # no GUI needed
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

BASE = r"C:\Users\melvi\Documents\Maestria\19. Seminario de Tesis II\Anteproyecto - Seminario II"
RES = os.path.join(BASE, "results")
ENV = os.path.join(RES, "agente_env.json")
assert os.path.exists(ENV), "run 12_agente_v1.py first"

# Constants come from the run, never from the drawing.
env = json.load(open(ENV, encoding="utf-8"))
K = env["alarm_k"]                     # alarm threshold, in standard deviations
TAU = env["tau"]                       # confidence guard on generate
MOVE = env["move"]                     # samples the observe action advances
FLOOD = env["flood_n"]                 # variables in alarm that trigger alert
NDOC = env["kb_documents"]             # documents in the knowledge base
W0 = env["read_samples"][0]
W1 = W0 + env["scored_steps"]
MIN_PER_SAMPLE = 3                     # TEP samples every 3 minutes
assert "rules" in env["razona"], "the figure says rule-based; agente_env.json disagrees"

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "DejaVu Serif"],
    "font.size": 7,
    "figure.dpi": 300,
})

BLUE, ORANGE, GREEN, GREY = "#1f5fa8", "#c1531a", "#2e7d32", "#555555"
FILL, FILL_OP = "#eef3fa", "#eef6ee"

BX0, BX1 = 14.0, 72.0                  # stage boxes; margins hold loop and note
CX = (BX0 + BX1) / 2.0
LOOP_X = 6.5                           # vertical channel of the feedback arrow
GAP, GAP_WIDE = 4.6, 6.4               # vertical space left for the arrows
LINE_H, PAD_V = 3.3, 6.4               # per body line, and title + padding

# ---------------------------------------------------------------- the layout
# Stacked top-down so no coordinate is guessed and nothing can overlap: each
# block declares its lines, its height follows, and the next one starts below it.
BLOCKS = [
    dict(kind="ext", title="DCS: 52 process variables and alarm events", lines=[], gap=GAP),
    dict(kind="stage", title="1  Perceive", gap=GAP, lines=[
        (f"causal window $[{W0},{W1})$, "
         f"{(W1 - W0) * MIN_PER_SAMPLE} min after onset", "n"),
        (f"a variable is in alarm at ${K:.0f}\\sigma$", "n"),
        ("correlated alarms collapse into one group", "n")]),
    dict(kind="stage", title="2  Score", gap=GAP, lines=[
        ("the 1D-CNN saved for this fold,", "n"),
        ("loaded from disk, never retrained", "n")]),
    dict(kind="stage", title="3  Reason", gap=GAP, lines=[
        ("retrieval by symptom similarity", "n"),
        (f"over {NDOC} documents, one per class", "n"),
        ("rules, not a language model", "i")]),
    dict(kind="stage", title="4  Decide", gap=GAP_WIDE, lines=[
        (f"generate (confidence $\\geq {TAU:.2f}$)", "n"),
        (f"observe  |  defer  |  alert ($\\geq {FLOOD}$ alarms)", "n"),
        ("one action per step, each with its guard", "i")]),
    dict(kind="op", title="Operator: approves, edits or rejects", lines=[], gap=GAP_WIDE),
    dict(kind="ext", title="Plant", lines=[], gap=0.0, narrow=True),
]

for b in BLOCKS:
    b["h"] = (PAD_V + LINE_H * len(b["lines"])) if b["lines"] else 6.6

TOP = sum(b["h"] + b["gap"] for b in BLOCKS)
y = TOP
for b in BLOCKS:
    b["y1"] = y
    b["y0"] = y - b["h"]
    y = b["y0"] - b["gap"]

fig, ax = plt.subplots(figsize=(3.45, 3.45 * TOP / 100.0 * 1.06))
ax.set_xlim(0, 100)
ax.set_ylim(0, TOP)
ax.axis("off")

STYLE = {
    "stage": dict(edge=BLUE, fill=FILL, dashed=False),
    "op":    dict(edge=GREEN, fill=FILL_OP, dashed=False),
    "ext":   dict(edge=GREY, fill="#ffffff", dashed=True),
}

for b in BLOCKS:
    st = STYLE[b["kind"]]
    x0, x1 = (36.0, 62.0) if b.get("narrow") else (BX0, BX1)
    ax.add_patch(FancyBboxPatch(
        (x0, b["y0"]), x1 - x0, b["h"],
        boxstyle="round,pad=0,rounding_size=1.5",
        linewidth=0.9, edgecolor=st["edge"], facecolor=st["fill"],
        linestyle=(0, (3, 2)) if st["dashed"] else "solid", zorder=2))
    cx = (x0 + x1) / 2.0
    if not b["lines"]:
        ax.text(cx, (b["y0"] + b["y1"]) / 2.0, b["title"], ha="center", va="center",
                fontsize=7.1, color=st["edge"], zorder=3)
        continue
    ax.text(cx, b["y1"] - 2.9, b["title"], ha="center", va="center",
            fontsize=7.4, fontweight="bold", color=st["edge"], zorder=3)
    for i, (txt, mode) in enumerate(b["lines"]):
        ax.text(cx, b["y1"] - PAD_V + 0.7 - LINE_H * (i + 0.5), txt,
                ha="center", va="center", fontsize=6.4, zorder=3,
                color=(ORANGE if mode == "i" else "#1a1a1a"),
                style=("italic" if mode == "i" else "normal"))

# arrows between consecutive blocks, drawn strictly inside the gaps
for a, b in zip(BLOCKS, BLOCKS[1:]):
    ax.add_patch(FancyArrowPatch(
        (CX, a["y0"] - 0.4), (CX, b["y1"] + 0.4), arrowstyle="-|>",
        mutation_scale=7, linewidth=1.0, color="#333333",
        shrinkA=0, shrinkB=0, zorder=4))

dec = [b for b in BLOCKS if b["title"].startswith("4")][0]
per = [b for b in BLOCKS if b["title"].startswith("1")][0]
op = [b for b in BLOCKS if b["kind"] == "op"][0]
pla = BLOCKS[-1]

# ------------------------------------------------------------------- the loop
# The observe action sends the agent back to perceive with the window moved: the
# one thing that makes this a loop and not a pipeline.
y_out = (dec["y0"] + dec["y1"]) / 2.0
y_in = (per["y0"] + per["y1"]) / 2.0
for seg in [((BX0, y_out), (LOOP_X, y_out)), ((LOOP_X, y_out), (LOOP_X, y_in))]:
    ax.add_patch(FancyArrowPatch(*seg, arrowstyle="-", linewidth=1.1,
                                 color=ORANGE, zorder=4))
ax.add_patch(FancyArrowPatch((LOOP_X, y_in), (BX0, y_in), arrowstyle="-|>",
                             mutation_scale=7, linewidth=1.1, color=ORANGE, zorder=4))
ax.text(LOOP_X - 2.2, (y_out + y_in) / 2.0,
        f"observe: the window advances {MOVE} samples,\n"
        f"{MOVE * MIN_PER_SAMPLE} min of plant time, at most once",
        ha="center", va="center", fontsize=6.3, color=ORANGE,
        rotation=90, linespacing=1.3, zorder=5)

# ------------------------------------------------- where the number is measured
ax.add_patch(FancyArrowPatch((BX1 + 8.0, y_out), (BX1 + 0.6, y_out),
                             arrowstyle="-|>", mutation_scale=6, linewidth=0.7,
                             color=GREY, zorder=4))
ax.text(BX1 + 9.2, y_out, "macro-$F_1$\nmeasured\nhere", ha="left", va="center",
        fontsize=6.3, color="#1a1a1a", linespacing=1.3, zorder=5)

# ------------------------------------------ the guard, and where the person is
ax.text(CX + 1.2, (dec["y0"] + op["y1"]) / 2.0, "  recommendation, ranked and cited",
        ha="left", va="center", fontsize=6.3, color="#1a1a1a", zorder=5)
ax.text(CX + 1.2, (op["y0"] + pla["y1"]) / 2.0, "  only after approval",
        ha="left", va="center", fontsize=6.3, color=GREEN, zorder=5)

fig.tight_layout(pad=0.12)
for ext in ("pdf", "png"):
    out = os.path.join(RES, f"architecture_loop.{ext}")
    fig.savefig(out, bbox_inches="tight", pad_inches=0.02)
    print("wrote", out)
plt.close(fig)

print(f"\nconstants read from agente_env.json: window [{W0},{W1}), k={K:.0f}, "
      f"tau={TAU}, move={MOVE}, flood={FLOOD}, docs={NDOC}")
