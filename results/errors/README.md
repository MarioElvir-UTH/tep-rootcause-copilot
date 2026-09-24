# Errors: where the copilot is wrong, and how wrong

Everything the paper says about failure comes from this directory. It was split
out of `results/` so that the error evidence sits in one place instead of being
scattered among the score tables.

| File | What it holds | Written by |
|---|---|---|
| `best_model_confusion_matrix.csv` | 21 x 21 confusion matrix of the best classical model | `04_classics_cv.py` |
| `dl_confusion_matrix.csv` | the same for the 1D-CNN, so the two representations can be compared class by class | `11_train_dl.py` |
| `worst_errors.csv` | per class: F1, Recall@1, Recall@3, which class it is taken for and how often, how often it was called normal operation, and how often the loop moved the window or deferred | `18_worst_errors.py` |
| `root_alarm_recall.csv` | root-alarm recall at N = 1 to 5, for each of the three arms, with the number of episodes each was scored on | `18_worst_errors.py` |
| `case_separation.csv` | how far apart the three costly episodes are, in standard deviations of normal operation, with two controls | `20_case_separation.py` |
| `twin_runs.csv`, `twin_runs_summary.csv` | per fault, how many runs are byte-identical to the normal run with the same number, in the scored and the moved window; the Recall@1 ceiling that sets for any model; and what the proposed copilot did with those episodes (PROTOCOLO.md, "Twin runs") | `20_case_separation.py` |
| `wait_vs_f1.csv` | whether making the copilot wait predicts how well a class is then identified, over the faults and over all classes | `18_worst_errors.py` |
| `costly_errors.md` | the three faults the copilot read as a healthy plant, each with its episode id, seed and fold | selected by `18_worst_errors.py`, written by hand |

## One column in `case_separation.csv` means two different things

Read this before quoting that file. The three sigma columns hold, **for the three
episode-pair rows**, the maximum and the extremes over the alarmed variables, as
their names say. **For the two control rows** they hold the median, the p10 and
the p90 over 300 sampled pairs, because a maximum over 300 pairs is an outlier
and says nothing about how far apart two episodes usually are.

**What the controls turned out to show, which was not the first reading.**
Sharing a simulation-run index does **not** generally make two episodes alike:
over 300 random pairs, the median separation between two faults on the same run
is *larger* than between two runs of the same fault. What is true is narrower and
more interesting: the low tail of the distribution belongs entirely to same-run
pairs, and the two confusing episodes sit in it.

So `max_sigma_all_52 = 11.6757` on the control row is a **median**, not a maximum,
and any text that quotes it has to call it "a median of 11.7"; the article does
not quote it. The script says so at the point where it writes the row, and it
prints the same warning when it runs.
Anyone reading the CSV on its own would get it wrong, which is why it is here too.

## Which faults make the copilot wait, and whether that predicts anything

The article says a second window helps when the evidence is late and does not
when it never arrives, and gives one contrast, IDV(14) against IDV(15). The class
by class version is here, from `worst_errors.csv`, with a correlation the article
does not give.

**Four faults never wait at all**, `moves_window` exactly zero: their signature
is already in the first window.

| Fault | per-class F1 |
|---|--:|
| IDV(6) | 1.000 |
| IDV(7) | 0.997 |
| IDV(5) | 0.985 |
| IDV(1) | 0.926 |

**Four wait in more than 99% of their episodes**, and the outcome could hardly
be more different:

| Fault | waits | per-class F1 |
|---|--:|--:|
| IDV(15) | 99.9% | 0.149 |
| IDV(14) | 99.7% | **0.999** |
| IDV(9) | 99.6% | 0.372 |
| IDV(13) | 99.3% | 0.433 |

IDV(14) and IDV(15) wait equally and end at 0.999 and 0.149. Waiting is not a
proxy for difficulty, and `wait_vs_f1.csv` puts a number on how weak the link
is: **-0.54 over the twenty faults**.

One class is deliberately missing from the second table because it is not a
fault: **normal operation waits in 99.7% of its episodes** and is identified at
0.207, so the copilot hesitates over a healthy plant about as often as over its
hardest fault. Including it moves the correlation to -0.56, which is why
`wait_vs_f1.csv` reports both scopes and a text that quotes it has to name one.

## The two confusion matrices are not the same thing as `worst_errors.csv`

The matrices are counts of raw predictions. `worst_errors.csv` is the agent's
behavior: it is computed at the output of `decide`, so it also records what the
loop did about the error, which is the part that matters for an operator. A
class can be confused often and still be handled well, if the agent defers
instead of asserting.

## `costly_errors.md` is the only file here not produced by the pipeline

It is prose, drafted outside the reproducible path and declared as such in
`PROTOCOLO.md`. The three episodes it discusses were selected by a rule fixed in
advance, and `18_worst_errors.py` prints them, so the selection is reproducible
even though the writing is not. No number in the paper depends on it.

It used to live in `results/samples/`, whose rule is one episode per action
(generate, observe, defer, alert). It never matched that rule, and it is here
now.

## Reproducing

`python code/run_all.py` writes the eight data files. Steps 04 and 11 produce the
confusion matrices as a side effect of training, step 20 produces
`case_separation.csv` and the two `twin_runs` files, and step 18 produces the
rest.
