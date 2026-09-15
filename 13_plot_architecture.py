r"""
Figure 1: the advisory architecture, drawn as the loop it actually is.

Laid out across both columns, left to right, because the thing being shown is a
sequence. The DCS and the plant are the arrows at the two ends rather than boxes:
they are context, and spending box width on them would shrink the four stages that
are the subject.

Renders the four pieces pre-registered in PROTOCOLO.md ("Figure 1 in text"):
perceive, score, reason, decide; the observe action that closes the loop; the
guard (the copilot never reaches the process); where the person is; and where the
Table II number is measured.

Drawn by code for the same reason the label-efficiency figure is: a diagram that
is redrawn by hand cannot drift away from the pipeline without someone noticing,
and every constant shown here is read from results/agente_env.json rather than
typed into the drawing.

Outputs:
  results/architecture_loop.pdf  <- vector, \includegraphics* in the paper
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
NVAR = 52                              # process variables of the TEP
W0 = env["read_samples"][0]
W1 = W0 + env["scored_steps"]
MIN_PER_SAMPLE = 3                     # TEP samples every 3 minutes
assert "rules" in env["razona"], "the figure says rule-based; agente_env.json disagrees"

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "DejaVu Serif"],
    "font.size": 8,
    "figure.dpi": 300,
})

BLUE, ORANGE, GREEN, GREY = "#1f5fa8", "#c1531a", "#2e7d32", "#555555"
FILL, FILL_OP = "#eef3fa", "#eef6ee"

# Both IEEE columns plus the gutter. No tight bbox, so LaTeX does not rescale the
# text and 7 pt on paper is 7 pt here.
W_IN, H_IN = 7.16, 2.30
fig, ax = plt.subplots(figsize=(W_IN, H_IN))
X1, Y1 = 100.0, 100.0 * H_IN / W_IN
ax.set_xlim(0, X1)
ax.set_ylim(0, Y1)
ax.axis("off")

BOXES = [
    dict(key="perceive", kind="stage", title="1  Perceive", lines=[
        (r"window $[%d,%d)$" % (W0, W1), "n"),
        (r"alarm at $%d\sigma$" % K, "n")]),
    dict(key="score", kind="stage", title="2  Score", lines=[
        ("the fold's 1D-CNN,", "n"),
        ("never retrained", "n")]),
    dict(key="reason", kind="stage", title="3  Reason", lines=[
        ("%d documents, by" % NDOC, "n"),
        ("symptom similarity", "n"),
        ("rules, not an LLM", "i")]),
    dict(key="decide", kind="stage", title="4  Decide", lines=[
        (r"conf $\geq %.2f$: answer" % TAU, "n"),
        ("else observe, defer", "n")]),
    dict(key="operator", kind="op", title="Operator", lines=[
        ("approves", "n"),
        ("or rejects", "n")]),
]

# Box widths are measured, not guessed: every line is rendered once off-screen at
# its real size and the box is made wide enough for the longest of them. If the row
# does not fit the span the script stops, instead of shipping a figure that spills
# past the column.
FS_TITLE, FS_BODY, FS_ITAL = 8.0, 8.0, 8.0
PAD_X, GAP, ARROW = 1.5, 1.2, 4.2
BY0, BH = Y1 - 21.0, 14.5

renderer = fig.canvas.get_renderer()


def text_units(txt, fs, italic=False):
    """Width of a string in axis units, measured at the size it will be drawn."""
    t = ax.text(0, 0, txt, fontsize=fs, style=("italic" if italic else "normal"))
    bb = t.get_window_extent(renderer=renderer)
    t.remove()
    return bb.transformed(ax.transData.inverted()).width


for b in BOXES:
    need = [text_units(b["title"], FS_TITLE)]
    need += [text_units(t, FS_ITAL if m == "i" else FS_BODY, m == "i")
             for t, m in b["lines"] if t]
    b["w"] = max(need) + 2 * PAD_X
    b["_widest"] = max(zip(need, [b["title"]] + [t for t, _ in b["lines"] if t]))[1]

total = ARROW * 2 + sum(b["w"] for b in BOXES) + GAP * (len(BOXES) - 1)
print("row uses %.1f of %.0f units, %.2f cm of %.2f cm"
      % (total, X1, total / X1 * W_IN * 2.54, W_IN * 2.54))
for _b in BOXES:
    print("   %-9s %5.1f units   widest: %s" % (_b["key"], _b["w"], _b["_widest"]))
assert total <= X1 + 0.5, (
    "the row needs %.1f of %.0f units: shorten a line or widen the figure" % (total, X1))
x = (X1 - (total - 2 * ARROW)) / 2.0
for b in BOXES:
    b["x0"] = x
    b["x1"] = x + b["w"]
    x = b["x1"] + GAP
B = {b["key"]: b for b in BOXES}

for b in BOXES:
    edge, fill = (GREEN, FILL_OP) if b["kind"] == "op" else (BLUE, FILL)
    ax.add_patch(FancyBboxPatch((b["x0"], BY0), b["w"], BH,
                                boxstyle="round,pad=0,rounding_size=1.1",
                                linewidth=0.9, edgecolor=edge, facecolor=fill, zorder=2))
    cx = (b["x0"] + b["x1"]) / 2.0
    ax.text(cx, BY0 + BH - 3.2, b["title"], ha="center", va="center",
            fontsize=8.0, fontweight="bold", color=edge, zorder=3)
    # centre the body lines in the space under the title, so a box with two lines
    # does not leave a gap at the bottom
    body = [l for l in b["lines"] if l[0]]
    top, bot = BY0 + BH - 5.0, BY0 + 1.2
    for j, (txt, mode) in enumerate(body):
        yj = (top + bot) / 2.0 + (len(body) - 1) / 2.0 * 3.6 - 3.6 * j
        ax.text(cx, yj, txt, ha="center", va="center",
                fontsize=8.0, zorder=3,
                color=(ORANGE if mode == "i" else "#1a1a1a"),
                style=("italic" if mode == "i" else "normal"))

YM = BY0 + BH / 2.0
for a, c in zip(BOXES, BOXES[1:]):
    ax.add_patch(FancyArrowPatch((a["x1"] + 0.3, YM), (c["x0"] - 0.3, YM),
                                 arrowstyle="-|>", mutation_scale=7, linewidth=1.0,
                                 color="#333333", zorder=4))

# ----------------------------------------------- the two ends, as arrows not boxes
ax.add_patch(FancyArrowPatch((B["perceive"]["x0"] - ARROW, YM), (B["perceive"]["x0"] - 0.3, YM),
                             arrowstyle="-|>", mutation_scale=7, linewidth=1.0,
                             color=GREY, zorder=4))
ax.text(B["perceive"]["x0"] - ARROW / 2.0, YM + 3.2, "DCS",
        ha="center", va="center", fontsize=8.0, color=GREY)

ax.add_patch(FancyArrowPatch((B["operator"]["x1"] + 0.3, YM), (B["operator"]["x1"] + ARROW, YM),
                             arrowstyle="-|>", mutation_scale=7, linewidth=1.0,
                             color=GREEN, zorder=4))
ax.text(B["operator"]["x1"] + ARROW / 2.0, YM + 3.2, "plant",
        ha="center", va="center", fontsize=8.0, color=GREEN)

# ------------------------------------------------------------------- the loop
# The observe action sends the agent back to perception with the window moved: the
# one thing that makes this a loop and not a pipeline.
y_loop = BY0 - 6.2
xa = (B["decide"]["x0"] + B["decide"]["x1"]) / 2.0
xb = (B["perceive"]["x0"] + B["perceive"]["x1"]) / 2.0
for seg in [((xa, BY0), (xa, y_loop)), ((xa, y_loop), (xb, y_loop))]:
    ax.add_patch(FancyArrowPatch(*seg, arrowstyle="-", linewidth=1.1, color=ORANGE, zorder=4))
ax.add_patch(FancyArrowPatch((xb, y_loop), (xb, BY0 - 0.3), arrowstyle="-|>",
                             mutation_scale=7, linewidth=1.1, color=ORANGE, zorder=4))
ax.text((xa + xb) / 2.0, y_loop - 2.6,
        r"$observe$: the window advances %d samples, %d min of plant time, at most once"
        % (MOVE, MOVE * MIN_PER_SAMPLE),
        ha="center", va="center", fontsize=8.0, color=ORANGE, zorder=5)

# ------------------------------------------------- where the number is measured
ax.text(xa, BY0 + BH + 2.6, r"macro-$F_1$ measured here", ha="center", va="center",
        fontsize=8.0, color="#1a1a1a", zorder=5)
ax.add_patch(FancyArrowPatch((xa, BY0 + BH + 1.4), (xa, BY0 + BH + 0.3),
                             arrowstyle="-|>", mutation_scale=6, linewidth=0.7,
                             color=GREY, zorder=4))

fig.subplots_adjust(left=0.002, right=0.998, top=0.995, bottom=0.005)
for ext in ("pdf", "png"):
    out = os.path.join(RES, "architecture_loop." + ext)
    # CreationDate=None keeps the PDF byte-identical across runs: without it every
    # re-run shows up as a change to a file whose content did not change, which is
    # noise in a repository whose claim is that re-running reproduces the results.
    fig.savefig(out, metadata={"CreationDate": None} if ext == "pdf" else None)
    print("wrote", out)
plt.close(fig)

print("\nconstants read from agente_env.json: window [%d,%d), k=%.0f, tau=%.2f, "
      "move=%d, flood=%d, docs=%d" % (W0, W1, K, TAU, MOVE, FLOOD, NDOC))
