# PROTOCOLO / Experimental configuration

> Canonical protocol for the paper (the ONLY protocol document; replaces the
> earlier `protocolo_validacion.md`). The paragraph below is the *Experimental
> Configuration* section: it is pasted almost verbatim into Overleaf and it
> **overrides whatever the results say afterwards**.
>
> **Primary metric: macro-averaged $F_1$** (confirmed 2026-09-12, matching Dr.
> Loo's Week-2 figure and Table II). Recall@1, Recall@3 and MRR are secondary.
> The `.tex` (Evaluation, Abstract, objective 4) and the figure were reconciled
> to this choice.

## Table II (LaTeX, IEEEtran): classics filled, proposed method pending

```latex
\begin{table}[!t]
\centering
\caption{Root-cause identification on the Tennessee Eastman Process:
macro-averaged $F_1$ on validation, mean $\pm$ standard deviation over
five folds $\times$ three seeds, grouped by simulation run, under an
identical hyperparameter search for every model.}
\label{tab:results}
\begin{tabular}{@{}lccc@{}}
\toprule
Model & Macro $F_1$ & Recall@3 & Inference (ms) \\
\midrule
Trivial (majority class)     & $0.004 \pm 0.000$          & $0.143 \pm 0.000$          & $<0.001$ \\
Logistic regression          & $\mathbf{0.652 \pm 0.005}$ & $\mathbf{0.733 \pm 0.003}$ & $0.003$ \\
Random forest                & $0.638 \pm 0.005$          & $0.703 \pm 0.006$          & $0.081$ \\
Gradient boosting            & $0.640 \pm 0.005$          & $0.654 \pm 0.007$          & $0.073$ \\
Proposed method (Weeks 3--4) & \emph{por llenar}          & \emph{por llenar}          & \emph{por llenar} \\
\bottomrule
\end{tabular}
\end{table}
```

Rows: trivial floor + three classics (one linear, two tree ensembles) + proposed
method. The floor and the classics are filled from `classics_cv_comparison.csv`
(run under this exact protocol); the empty proposed-method row is the Weeks 3--4
commitment. Best macro-$F_1$ and best Recall@3 in bold (logistic regression). The
cost column is the amortized per-episode inference latency (ms, reproducible),
from `10_inference_time.py`.

## Experimental configuration (seven sentences)

*Experimental configuration.* (1) The primary dataset is the public Tennessee
Eastman Process in the large-scale simulation release of Rieth et al.,
comprising 500 runs per class over 21 root-cause classes (1 normal and 20
faults), with one simulation run as the unit of observation. (2) Data are
grouped by simulation run and stratified by class under a fixed seed (42): a
held-out test set of 10,500 runs is sealed from the start and opened only once,
while a development pool of 10,500 runs is used for all tuning, with the
partition indices saved to disk. (3) Each run is summarized by the mean and
standard deviation of its 52 process variables over a causal early window (20
samples after fault onset), and feature standardization is fit inside each
cross-validation fold on the training portion only. (4) The compared models are
a trivial majority-class baseline, a multinomial logistic regression over the
standardized features, a random forest, and gradient boosting, all implemented
in scikit-learn 1.9.1; the three learned models span one linear and two
tree-ensemble inductive biases, so the comparison does not presuppose which one
suits this representation. (5) Hyperparameters are chosen from a small,
pre-declared grid of three configurations per model (logistic regression inverse
regularization strength C in {0.1, 1, 10}; random forest maximum depth in {none,
10, 20} with 300 trees; gradient boosting learning rate in {0.05, 0.1, 0.2}),
giving every model
the same search effort, with model selection on the primary metric and on a
seed (0) separate from the estimation seeds. (6) Performance is estimated by repeated stratified group
k-fold cross-validation by run (k = 5; three seeds: 5, 17, 42), reporting the
mean and standard deviation over the 15 resulting folds; the primary metric is
the macro-averaged F1 score, with Recall@1, Recall@3, and mean reciprocal rank
as secondary metrics, and per-episode inference latency (in milliseconds) as a
cost measure. (7) All
experiments run on a single machine on CPU (Intel Core i5-13420H, 12 threads)
with Python 3.14.2 and fixed seeds
throughout; the code, the frozen partition, and the pinned environment
(requirements.txt) are available in the project repository
https://github.com/MarioElvir-UTH/tep-rootcause-copilot; per-model training time
on the development pool is about 3 s (logistic regression), 6 s (random forest),
and 20 s (gradient boosting), and negligible for the trivial baseline.

## Consistency check (paragraph vs. code vs. table)

- Dataset (Rieth; 500/class; 21 classes; unit = run) -> matches `01`/`02`. OK
- Partition (by run, stratified, seed 42; test 10,500 sealed; dev 10,500; saved
  to disk, sha256 f55e7729a298e23c) -> matches `02_make_partition.py`. OK
- Features (mean+std of 52 vars; causal window 20 samples; scaler fit in-fold)
  -> matches `04`/`05`. OK
- Models (trivial, logistic regression, random forest, gradient boosting;
  scikit-learn 1.9.1) -> matches `04`. OK
- Grid + equal effort + selection seed 0 -> matches `04`. OK
- Validation (StratifiedGroupKFold by run, k=5, seeds 5/17/42, 15 folds,
  mean +- std) -> matches `04`-`08`. OK
- Trivial numbers (macro-F1 0.004; Recall@1 0.048) -> from `04`
  (0.0043 / 0.0476). OK
- **Primary metric = macro-F1** -> reconciled 2026-09-12 across the `.tex`
  (Evaluation, Abstract, objective 4) and the figure; `protocolo_validacion.md`
  removed so this file is the only protocol. OK
- Inference time (ms) -> amortized per-episode latency (`10_inference_time.py`,
  reproducible; rounded to 2 sig figs in the table): trivial <0.01, random forest
  0.05, gradient boosting 0.03. OK
- Per-model training time (s) -> median fit on the dev pool
  (`10_inference_time.py`): trivial <0.01, random forest ~6, gradient boosting ~8. OK
- Repository (GitHub, university e-mail) -> not created yet. [PENDIENTE]
- PR-AUC (used in Dr. Loo's example) -> NOT computed; Recall@1 used as the
  secondary instead. If PR-AUC is required, [PENDIENTE].
