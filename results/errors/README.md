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
| `costly_errors.md` | the three faults the copilot read as a healthy plant, each with its episode id, seed and fold | selected by `18_worst_errors.py`, written by hand |

## The two confusion matrices are not the same thing as `worst_errors.csv`

The matrices are counts of raw predictions. `worst_errors.csv` is the agent's
behaviour: it is computed at the output of `decide`, so it also records what the
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

`python run_all.py` writes the four data files. Steps 04 and 11 produce the
confusion matrices as a side effect of training; step 18 produces the rest.
