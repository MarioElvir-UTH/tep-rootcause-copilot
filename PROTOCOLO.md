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
\caption{Root-cause identification on the TEP: macro-averaged $F_1$ on
validation, mean $\pm$ standard deviation over five folds $\times$ three seeds,
grouped by simulation run, under an identical hyperparameter search for every
model. Rows v1a and v1b are the networks. Cost is measured on the same run and
machine (Intel Core i5-13420H, 12 threads, CPU only) and reads as size /
training seconds / amortized inference milliseconds per episode, where size
counts stored coefficients for the linear model and the networks and decision
nodes for the tree ensembles.}
\label{tab:results}
\footnotesize
\setlength{\tabcolsep}{3pt}
\begin{tabular}{@{}lccr@{}}
\toprule
Model & Macro $F_1$ & Recall@3 & \multicolumn{1}{c}{\shortstack{Cost \\ {\scriptsize (size / s / ms)}}} \\
\midrule
Trivial         & $0.004 \pm 0.000$ & $0.143 \pm 0.000$ & 21 / $<$0.01 / $<$0.001 \\
Logistic reg.   & $0.652 \pm 0.005$ & $0.733 \pm 0.003$ & 2,205 / 3 / 0.003 \\
Random forest   & $0.638 \pm 0.005$ & $0.703 \pm 0.006$ & 98,740 / 6 / 0.081 \\
Gradient boost. & $0.640 \pm 0.005$ & $0.654 \pm 0.007$ & 67,499 / 20 / 0.073 \\
\midrule
v1a MLP         & $0.652 \pm 0.013$ & $0.754 \pm 0.017$ & 9,493 / 3 / $<$0.001 \\
v1b 1D-CNN      & $\mathbf{0.696 \pm 0.006}$ & $\mathbf{0.786 \pm 0.007}$ & 16,117 / 17 / 0.004 \\
\midrule
Proposed method & \multicolumn{3}{c}{\emph{por llenar} (Week 4)} \\
\bottomrule
\end{tabular}
\end{table}
```

Rows: trivial floor + three classics (one linear, two tree ensembles) + the two
networks + proposed method. The floor and the classics come from
`classics_cv_comparison.csv`, the networks from `dl_comparison.csv`, and the cost
figures from `10_inference_time.py` and `11_train_dl.py`, all run under this exact
protocol. The empty proposed-method row is the Week 4 commitment. Best macro-$F_1$
and best Recall@3 in bold (v1b 1D-CNN).

One cost column, following the Week 3 table template: it reads size / training
seconds / amortized per-episode inference latency, all measured on the same run
and the same machine. Collapsing the three cost values into a single column is
what lets the table fit one IEEE column again, at `\footnotesize` with
`\tabcolsep` 3pt; it was compiled and confirmed to fit. The `Cost` header is
centred with `\multicolumn` because the column itself is right-aligned for the
numbers. The exact column layout is still open and may be revisited when the
formatting pass happens at the end.

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

## Week 3 pre-registration: the neural network row (written BEFORE running anything)

> Declared 2026-09-13, before any network was trained. Rule being honoured: what
> is decided after seeing the number is not protocol, it is tuning on the result.
> Architecture, parameter count, exact input, maximum epochs and the stopping
> criterion are fixed here and are not to be changed once a score is known.

### Why a recurrent network (LSTM/GRU) is discarded

Discarded on purpose, and the reason is the window length, not preference. A
recurrent model is the right choice "when what happened far away inside the
window matters", and its honest size assumes a window of 30 to 120 steps. **Our
causal window is 20 steps**, which is one hour of plant time: TEP samples every
3 minutes, so fault onset at sample 21 for training runs is 1 h and at sample 161
for test runs is 8 h. In 20 steps there is no "far away", so a recurrent would
add parameters without adding reach, and at this window length it is precisely
the kind of row a reviewer discards. Worth revisiting only if the window is ever
lengthened past 30 steps.

### V1a. MLP (control at equal input)

Purpose: the minimum network that can be set against gradient boosting without
cheating, because it receives exactly what the classics receive. Together with
V1b it separates the effect of the **architecture** from the effect of the
**representation**: V1a vs the classics isolates the first, V1b vs V1a the second.

- Input: the same 104 features (mean and standard deviation of the 52 process
  variables over the causal window), standardized inside each fold on the
  training portion only.
- Layers: 104 -> 64 -> 32 -> 21, ReLU, dropout 0.2.
- Parameters: **9,493** (104*64+64 = 6,720; 64*32+32 = 2,080; 32*21+21 = 693).
  Kept under 10,000: two hidden layers of 64 would give 12,245.

### V1b. 1D-CNN (the main network)

Purpose: local patterns inside the window, a peak, a slope, a shape. This is
where the residual errors live: the 11 hard classes differ in the trajectory
shape, which the per-run mean and standard deviation discard by construction.

- Input: the raw causal window, **20 steps x 52 sensors**, standardized per
  channel inside each fold on the training portion only.
- Layers: Conv1d(52 -> 32, kernel 5, padding 2) + BatchNorm + ReLU ->
  Conv1d(32 -> 64, kernel 3, padding 1) + BatchNorm + ReLU -> global average
  pooling over time -> dropout 0.2 -> Linear(64 -> 21).
- Parameters: **16,117** (8,352 + 64 + 6,208 + 128 + 1,365).

### Training rules common to both networks

- Maximum epochs: **60**.
- Stopping criterion: **early stopping with patience 10**, monitored on an
  **inner 20% validation split carved out of the training portion of each fold**.
  The outer validation fold is used **only to score**, never to pick the epoch.
  This keeps the search effort comparable to the classics, which had no epoch knob.
- Optimizer: Adam, with a pre-declared grid of **3 configurations**, the same
  count every classic received (each classic tried 3). The learning rate is the
  hyperparameter that varies: {1e-2, 3e-3, 1e-3}. Everything else is fixed above.
- Loss: multiclass cross-entropy, unweighted. On this balanced design (500 runs
  per class) that is equivalent to the `class_weight="balanced"` the classics
  used, so the comparison stays level. The binary loss of the workshop example
  does not apply here: the task has 21 classes, not 2.
- Batch size: **256**, fixed for both networks and not tuned. With 6,720 training
  samples per fold after the inner split, that is about 26 steps per epoch.
- Selection: macro-F1 (the primary metric) on seed 0, separate from the
  estimation seeds.
- Estimation: the same 15 folds (StratifiedGroupKFold by run, k = 5, seeds 5, 17,
  42), reported as mean +- std. Test stays sealed.
- **The seed also fixes the weight initialization**, not only the fold split.
  Each of the seeds 5, 17 and 42 seeds the network's initial weights and the
  training shuffling, so the reported std carries the initialization variance the
  same way the classics carried their estimator randomness.
- **No data augmentation.** None is declared, so none may be added after a score
  is seen. If any were ever added, it would be applied inside the training
  portion of the fold only, never before splitting.
- **One window per run**, exactly as in Week 2. This is what makes the group
  split exact: if sliding windows were ever used to enlarge the training set,
  several windows of the same run could land in different folds, which is the
  augmentation leak translated from images to signal.
- Cost reported for each network, measured on the same run and **on the machine
  named in the paper** (Intel Core i5-13420H, 12 threads, CPU only): parameter
  count, training seconds, and amortized inference milliseconds per episode.
- **Training evidence:** one loss figure per run (training and validation loss per
  epoch), saved in `results/curves/` with the model, the seed and the fold in the
  file name. It does not go in the article; it is the evidence that training
  followed the protocol, and it is the first thing reviewed when grading. The
  "stop here" at the minimum of the validation loss is exactly what the early
  stopping declared above implements. Reading the curve is for diagnosis and for
  the discussion, never for re-tuning the number that gets reported: changing the
  architecture, the epochs, the partition, the metric or the seed after seeing a
  score is searching on the result, and the reported std makes it visible.

### The bar to beat

Logistic regression, macro-F1 **0.652 +- 0.005**. Because the standard deviation
is about 0.005, a gap smaller than that is not a difference: a defensible win
needs roughly **0.662** or more. Per label budget the network has to beat the
leader of that range, the random forest between 1% and 5% of the labels and
logistic regression from 12% upward.

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
- Selection criterion -> hyperparameters AND the best model are chosen by
  macro-F1, the primary metric (`04_classics_cv.py`, fixed 2026-09-13; it used to
  select by Recall@1, which contradicted the paper). Verified that Recall@1 would
  select the identical configuration for all three models, so no number changed. OK
- Inference time (ms) -> amortized per-episode latency (`10_inference_time.py`,
  reproducible): trivial <0.001, logistic regression 0.003, random forest 0.081,
  gradient boosting 0.073. OK
- Per-model training time (s) -> median fit on the dev pool
  (`10_inference_time.py`): trivial <0.01, logistic regression ~3, random forest
  ~6, gradient boosting ~20. Wall-clock, so it moves with machine load. OK
- Repository -> public at https://github.com/MarioElvir-UTH/tep-rootcause-copilot
  (code, frozen partition, results, README with the one-command reproduction). OK
- PR-AUC (used in Dr. Loo's example) -> NOT computed; the secondary metrics are
  Recall@1, Recall@3 and MRR, and Table II shows Recall@3. If PR-AUC is
  required, [PENDIENTE].
