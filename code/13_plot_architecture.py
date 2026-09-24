r"""
Figure 1: the advisory architecture, drawn as the loop it is.

Renders the four pieces pre-registered in PROTOCOLO.md ("Figure 1 in text"):
perceive, score, reason, decide; the observe action that closes the loop; the
dashed boundary that is the guard, with the operator outside it; and where the
Table II number is measured. Every constant shown is read from
results/agente_env.json rather than typed in, so the drawing cannot drift from
the run.

Outputs:
  results/architecture_loop.pdf  <- vector, the one the paper includes
  results/architecture_loop.png  <- 300 dpi raster, for quick viewing

Reads results/agente_env.json (produced by 12_agente_v1.py). The figure rules
this file implements, and the layout decisions behind it, are in PROTOCOLO.md.
"""
import os
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")           # no GUI needed
import matplotlib.pyplot as plt
from matplotlib.path import Path
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle

BASE = os.path.dirname(os.path.abspath(__file__))
if not os.path.isfile(os.path.join(BASE, "requirements.txt")):
    BASE = os.path.dirname(BASE)      # the scripts live in code/, the project one level up
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
assert env["max_moves"] == 1, "the figure says observe runs at most once; agente_env.json disagrees"

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "DejaVu Serif"],
    "font.size": 8,
    "figure.dpi": 300,
})

BLUE, ORANGE, GREEN, GREY = "#1f5fa8", "#c1531a", "#2e7d32", "#555555"
FILL, FILL_OP = "#eef3fa", "#eef6ee"
EDGE_C, FILL_C = "#9bb3cf", "#fbfcfe"   # the copilot boundary

# Both IEEE columns plus the gutter. No tight bbox, so LaTeX does not rescale the
# text and 7.5 pt on paper is 7.5 pt here.
W_IN, H_IN = 7.16, 2.45
fig, ax = plt.subplots(figsize=(W_IN, H_IN))
X1, Y1 = 100.0, 100.0 * H_IN / W_IN
ax.set_xlim(0, X1)
ax.set_ylim(0, Y1)
ax.axis("off")

BOXES = [
    dict(key="perceive", kind="stage", n="1", title="Perceive", lines=[
        (r"window $[%d,%d)$" % (W0, W1), "n"),
        (r"alarm at $%d\sigma$" % K, "n")]),
    dict(key="score", kind="stage", n="2", title="Score", lines=[
        ("the fold's 1D-CNN,", "n"),
        ("never retrained", "n")]),
    dict(key="reason", kind="stage", n="3", title="Reason", lines=[
        ("%d documents, by" % NDOC, "n"),
        ("symptom similarity", "n"),
        ("rules, not an LLM", "i")]),
    dict(key="decide", kind="stage", n="4", title="Decide", lines=[
        ("answer if 2 and 3 agree", "n"),
        (r"and conf $\geq %.2f$; else" % TAU, "n"),
        ("observe, escalate, defer", "n")]),
    dict(key="operator", kind="op", n="", title="Operator", lines=[
        ("approves", "n"),
        ("or rejects", "n")]),
]

# Box widths are measured, not guessed: every line is rendered once off-screen at
# its real size and the box is made wide enough for the longest of them. If the row
# does not fit the span the script stops, instead of shipping a figure that spills
# past the column.
FS = 7.5
PAD_X, GAP, GAP_OP, ARROW, PADC = 1.5, 1.2, 2.6, 2.8, 1.7
BH, BY0, Y_LOOP, NUDGE = 14.0, 14.8, 7.8, 1.0

renderer = fig.canvas.get_renderer()


def text_units(txt, fs, italic=False, bold=False):
    """Width of a string in axis units, measured at the size it will be drawn."""
    t = ax.text(0, 0, txt, fontsize=fs, style=("italic" if italic else "normal"),
                fontweight=("bold" if bold else "normal"))
    bb = t.get_window_extent(renderer=renderer)
    t.remove()
    return bb.transformed(ax.transData.inverted()).width


for b in BOXES:
    # a numbered box also has to fit its badge, which sits left of the title
    need = [text_units(b["title"], FS, bold=True) + (4.6 if b["n"] else 0)]
    need += [text_units(t, FS, m == "i") for t, m in b["lines"] if t]
    b["w"] = max(need) + 2 * PAD_X
    b["_widest"] = max(zip(need, [b["title"]] + [t for t, _ in b["lines"] if t]))[1]

stages, op = BOXES[:4], BOXES[4]
inner = sum(b["w"] for b in stages) + GAP * 3
# DCS and plant sit over their arrows, nudged outward so neither lands on a box
# edge or on the boundary. Both are wider than the arrow they label, so what hangs
# past each end is reserved here rather than discovered as a cropped word.
OV = [max(0.0, text_units(s, FS) / 2.0 + NUDGE - ARROW / 2.0) for s in ("DCS", "plant")]
# the boundary's right edge lives inside the gap that already separates Decide from
# the Operator, so on that side it costs nothing of its own
total = OV[0] + ARROW + PADC + inner + GAP_OP + op["w"] + ARROW + OV[1]
print("row uses %.1f of %.0f units, %.2f cm of %.2f cm"
      % (total, X1, total / X1 * W_IN * 2.54, W_IN * 2.54))
for _b in BOXES:
    print("   %-9s %5.1f units   widest: %s" % (_b["key"], _b["w"], _b["_widest"]))
assert total <= X1 + 0.5, (
    "the row needs %.1f of %.0f units: shorten a line or widen the figure" % (total, X1))

x = (X1 - total) / 2.0 + OV[0] + ARROW + PADC
for b in stages:
    b["x0"], b["x1"] = x, x + b["w"]
    x = b["x1"] + GAP
op["x0"] = stages[-1]["x1"] + GAP_OP
op["x1"] = op["x0"] + op["w"]
B = {b["key"]: b for b in BOXES}

YM = BY0 + BH / 2.0
CX0, CX1 = B["perceive"]["x0"] - PADC, B["decide"]["x1"] + PADC
CY0, CY1 = Y_LOOP - 5.4, BY0 + BH + 4.8

# ---------------------------------------------- the copilot boundary, as geometry
# The operator is drawn outside this frame on purpose: the advisory guard is then
# something a reader can see rather than something Section III has to promise.
ax.add_patch(FancyBboxPatch((CX0, CY0), CX1 - CX0, CY1 - CY0,
                            boxstyle="round,pad=0,rounding_size=2.0",
                            linewidth=0.8, edgecolor=EDGE_C, facecolor=FILL_C,
                            linestyle=(0, (4, 3)), zorder=1))
ax.text(CX0 + 2.2, CY1 - 2.4, "copilot: advises, never writes to the process",
        ha="left", va="center", fontsize=FS, style="italic", color=GREY, zorder=5)


def rounded(pts, r):
    """Polyline through pts with the corners rounded, so the path reads as a circuit."""
    verts, codes = [pts[0]], [Path.MOVETO]
    for i in range(1, len(pts) - 1):
        p0, p1, p2 = (np.array(p, float) for p in (pts[i - 1], pts[i], pts[i + 1]))
        a = p1 + (p0 - p1) / np.linalg.norm(p0 - p1) * r
        c = p1 + (p2 - p1) / np.linalg.norm(p2 - p1) * r
        verts += [tuple(a), tuple(p1), tuple(c)]
        codes += [Path.LINETO, Path.CURVE3, Path.CURVE3]
    verts.append(pts[-1])
    codes.append(Path.LINETO)
    return Path(verts, codes)


# ----------------------------------------------------------------------- the boxes
for b in BOXES:
    edge, fill = (GREEN, FILL_OP) if b["kind"] == "op" else (BLUE, FILL)
    ax.add_patch(FancyBboxPatch((b["x0"], BY0), b["w"], BH,
                                boxstyle="round,pad=0,rounding_size=1.1",
                                linewidth=0.9, edgecolor=edge, facecolor=fill, zorder=2))
    cx = (b["x0"] + b["x1"]) / 2.0
    ty = BY0 + BH - 3.2
    ax.text(cx + (2.3 if b["n"] else 0), ty, b["title"], ha="center", va="center",
            fontsize=FS, fontweight="bold", color=edge, zorder=3)
    if b["n"]:
        # the stage number rides the border, so it costs the box no inner width
        bx = cx - text_units(b["title"], FS, bold=True) / 2.0 + 0.4
        ax.add_patch(Circle((bx, ty), 1.7, facecolor=edge, edgecolor="none", zorder=3))
        ax.text(bx, ty, b["n"], ha="center", va="center", fontsize=6.4,
                fontweight="bold", color="white", zorder=4)
    # center the body lines in the space under the title, so a box with two lines
    # does not leave a gap at the bottom
    body = [l for l in b["lines"] if l[0]]
    top, bot = BY0 + BH - 5.2, BY0 + 1.2
    for j, (txt, mode) in enumerate(body):
        yj = (top + bot) / 2.0 + (len(body) - 1) / 2.0 * 3.4 - 3.4 * j
        ax.text(cx, yj, txt, ha="center", va="center", fontsize=FS, zorder=3,
                color=(ORANGE if mode == "i" else "#1a1a1a"),
                style=("italic" if mode == "i" else "normal"))

for a, c in zip(stages, stages[1:]):
    ax.add_patch(FancyArrowPatch((a["x1"] + 0.3, YM), (c["x0"] - 0.3, YM),
                                 arrowstyle="-|>", mutation_scale=7, linewidth=1.0,
                                 color="#333333", zorder=4))

# ------------------------------------------------ what enters, and what leaves
ax.add_patch(FancyArrowPatch((CX0 - ARROW, YM), (B["perceive"]["x0"] - 0.3, YM),
                             arrowstyle="-|>", mutation_scale=7, linewidth=1.0,
                             color=GREY, zorder=4))
ax.text(CX0 - ARROW / 2.0 - NUDGE, YM + 3.2, "DCS", ha="center", va="center",
        fontsize=FS, color=GREY)

# the only path out of the boundary, and it lands on a person
ax.add_patch(FancyArrowPatch((B["decide"]["x1"] + 0.3, YM), (op["x0"] - 0.3, YM),
                             arrowstyle="-|>", mutation_scale=7, linewidth=1.0,
                             color=GREEN, zorder=4))
ax.add_patch(FancyArrowPatch((op["x1"] + 0.3, YM), (op["x1"] + ARROW, YM),
                             arrowstyle="-|>", mutation_scale=7, linewidth=1.0,
                             color=GREEN, zorder=4))
ax.text(op["x1"] + ARROW / 2.0 + NUDGE, YM + 3.2, "plant", ha="center", va="center",
        fontsize=FS, color=GREEN)

# -------------------------------------------------------------------- the loop
# The observe action sends the agent back to perception with the window moved: the
# one thing that makes this a loop and not a pipeline.
xa = (B["decide"]["x0"] + B["decide"]["x1"]) / 2.0
xb = (B["perceive"]["x0"] + B["perceive"]["x1"]) / 2.0
ax.add_patch(FancyArrowPatch(
    path=rounded([(xa, BY0), (xa, Y_LOOP), (xb, Y_LOOP), (xb, BY0 - 0.3)], 3.2),
    arrowstyle="-|>", mutation_scale=7, linewidth=1.2, color=ORANGE, zorder=4))
ax.text((xa + xb) / 2.0, Y_LOOP - 3.0,
        r"$observe$: the window advances %d samples, %d min of plant time, at most once"
        % (MOVE, MOVE * MIN_PER_SAMPLE),
        ha="center", va="center", fontsize=FS, color=ORANGE, zorder=5)

# ------------------------------------------------ where the number is measured
ax.text(xa, BY0 + BH + 2.5, r"macro-$F_1$ measured here", ha="center", va="center",
        fontsize=FS, color="#1a1a1a", zorder=5)
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
