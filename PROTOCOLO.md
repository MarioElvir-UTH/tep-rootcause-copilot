# PROTOCOLO / Experimental configuration

> Canonical protocol for the paper. It **overrides whatever the results say
> afterwards**: what is decided after seeing a number is not protocol, it is
> tuning on the result.
>
> The seven sentences below are the paper's *Experimental Configuration*
> section. They used to be copied from here into Overleaf by hand and the two
> drifted, so the direction is now the other way: `siete.py` generates them from
> the `.tex`, which is the reviewed wording, and the two are compared on every
> check.
>
> **Primary metric: macro-averaged $F_1$** (confirmed 2026-09-12). Recall@1,
> Recall@3 and MRR are secondary, and the abstract, the objectives and the
> figure were reconciled to that choice.

## Table II: generated, not written here

The table is no longer typed in this file, and it is no longer typed in the
manuscript either. `results/tabla2.json` holds every number, one row per model,
with the primary and the secondary metric given per seed rather than already
averaged; `resultados.py` turns that file into `paper/tabla2.tex` and splices it
into the `.tex` between two markers. The caption stays in the manuscript, because
the prose belongs to the authors and the numbers belong to the run.

```
python code/resultados.py      write the table and the paragraph, splice them
python code/resultados.py --check   compare only, non-zero if the paper has drifted
```

This section used to carry the table in full. It was removed because it had
drifted: seven of its eight cost cells no longer matched the run. Keeping a
second copy here is the same failure the generator exists to prevent, so the
copy is gone rather than corrected. The version that drifted is in the git
history if it is ever needed.

Rows: trivial floor + three classics (one linear, two tree ensembles) + the two
networks + the two agent arms. The floor and the classics come from
`classics_cv_comparison.csv`, the networks from `dl_comparison.csv`, the agent
arms from `agente_comparison.csv`, and every cost cell from `17_cost_table.py`,
which measures all of them in a single run on one machine. Best macro-$F_1$ and
best Recall@3 are in bold, and they are the ablation's. The proposed method does
not win the primary metric and the table says so: what retrieval buys is
reported separately in Section V, not hidden here.

A third arm was measured and is deliberately absent from Table II: `lookup`,
which grounds the recommendation by citing the document of the predicted class.
It shares the classifier with the ablation, so its macro-$F_1$ and Recall@3 are
identical to the ablation row and adding it would repeat two numbers. It is
reported where it differs, on grounding and root-alarm identification, in the
text of Section V.

One cost column: it reads size / training seconds / amortized per-episode
inference latency, all measured on the same run and the same machine. The key to
those three units lives in the column header, `Cost (size / s / ms)`, not in the
caption. Measured, that costs nothing: the Cost column is already wider than the
header because its data cells set the width, and the table is 248.4pt against
the 252pt of an IEEE column with or without it.

The caption follows a fixed shape, so that a reader can judge the protocol
without leaving the table:

> [primary metric] on validation, mean +- standard deviation over [k] folds x
> [s] seeds, [scheme and grouping], [dataset] dataset.

which currently reads: *Macro F1 on validation, mean +- standard deviation over
five folds x three seeds, stratified group k-fold grouped by simulation run,
Tennessee Eastman Process dataset.* It renders in three lines of a single IEEE
column, which is accepted: the shape matters more than the length. Recall@3 is
not named in the caption because it is named in its own column header. Collapsing
the three values into one column is what lets the table fit a single IEEE column
at `\footnotesize` with `\tabcolsep` 3pt. The `Cost` header is centred with
`\multicolumn` because the column itself is right-aligned for the numbers.

## Experimental configuration: the classics paragraph (seven sentences)

> Section IV of the paper is now exactly these seven sentences and nothing
> else. It used to carry two further paragraphs, one for the two networks and
> one for the copilot, which declared every constant a reviewer needs to judge
> the pre-registration; they were cut on 2026-09-15 to bring the paper from
> eight pages to seven. Those constants were never duplicated here and are not
> duplicated now: they live in `Week 3 pre-registration` and `Proposed method
> pre-registration` further down, and `results/dl_env.json` and
> `results/agente_env.json` record what actually ran.
>
> What the paper therefore no longer declares, and what has to find a home if a
> reviewer needs it: the comparison convention (paired fold by fold, averaged by
> seed, with the effect size $d$); the sentence that no result is called
> significant and none carries a $p$-value; the agent constants $k = 3$,
> correlation $0.8$, $\tau = 0.50$, the flood threshold of 10 variables, the
> move of 10 samples that is 30 minutes of plant time, and the fusion weight
> $0.25$; the three arms declared before running; that root-alarm scoring
> excludes IDV 16 to IDV 20; and that the reasoning step is rule-based rather
> than a language model, which is what the zero-token claim rests on.

*Experimental configuration.* (1) The primary dataset is the public TEP release of Rieth et al., comprising
500 runs per class over 21 root-cause classes (1 normal and 20 faults), with
one simulation run as the unit of observation and process variables sampled
every three minutes, which is what converts every window length quoted below
into plant time. (2) Data are grouped by simulation run and stratified by
class under a fixed seed (42): a held-out test set of 10,500 runs is sealed
from the start and opened only once, while a development pool of 10,500 runs
is used for all tuning, with the partition indices saved to disk. (3) Each run
is summarized by the mean and standard deviation of its 52 process variables
over a causal early window (20 samples after fault onset), and feature
standardization is fit inside each cross-validation fold on the training
portion only. (4) The compared models are a trivial majority-class baseline, a
multinomial logistic regression over the standardized features, a random
forest, and gradient boosting, all implemented in scikit-learn 1.9.1; the
three learned models span one linear and two tree-ensemble inductive biases,
so the comparison does not presuppose which one suits this representation. (5)
Hyperparameters are chosen from a small, pre-declared grid of three
configurations per model (logistic regression inverse regularization strength
C in {0.1, 1, 10}; random forest maximum depth in {none, 10, 20} with 300
trees; gradient boosting learning rate in {0.05, 0.1, 0.2}), giving every
model the same search effort, with model selection on the primary metric and
on a seed (0) separate from the estimation seeds. (6) Performance is estimated
by repeated stratified group k-fold cross-validation by run (k = 5; three
seeds: 5, 17, 42), reporting the mean and standard deviation over the 15
resulting folds; the primary metric is the macro-averaged F_1 score, with
top-k accuracy reported as Recall@1 and Recall@3 and mean reciprocal rank as
secondary metrics, and per-episode inference latency (in milliseconds) as a
cost measure. (7) All experiments run on a single machine on CPU (Intel Core
i5-13420H, 12 threads) with Python 3.14.2 and fixed seeds throughout; the
code, the frozen partition, and the pinned environment (requirements.txt) are
available in the project repository
https://github.com/MarioElvir-UTH/tep-rootcause-copilot, and per-model
training time on the development pool is about 3 s (logistic regression), 6 s
(random forest), and 8 s (gradient boosting), and negligible for the trivial
baseline.

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

> **Measured, and not met.** This bar sat declared and unmeasured until
> 2026-09-15, because nothing in the pipeline scored the network alone at each
> budget: 08 measures the classics and 16 measures the agent arms, which are the
> network inside the loop. 16 now also scores it once, without the loop and
> without retrieval, which costs no extra training, because that network is
> already trained at every budget. The result is negative and is reported as
> such: the network alone is behind the leading classic at every budget up to
> 25% of the labels (0.5414 against 0.5809 at 10%, 0.5835 against 0.6245 at
> 25%) and ahead only at 50% and
> 100%. The copilot has the same shape, so the late crossover belongs to the
> representation and not to the agent. The label grid also gained the 10% point
> that the Week 3 note asked for and that had been replaced by 12.5%.

## Proposed method pre-registration: the copilot (written BEFORE running anything)

> Declared 2026-09-14, before a single line of the copilot was written. Same rule
> as the Week 3 block: what is decided after seeing a score is not protocol, it is
> tuning on the result. This is the row that carries the contribution promised in
> the anteproyecto, and it is deliberately the minimum version that produces a
> number, not the full system.

The network is not the contribution. The contribution is what sits on top of it:
a copilot that perceives an episode, scores the hypotheses, reasons over retrieved
evidence, and hands the operator a recommendation it can trace.

### The trap this design avoids

If retrieval were keyed by the class the classifier predicted, the whole component
would be a dictionary lookup wearing a costume: it would always find the document
of the predicted class, the with-and-without ablation would be favourable by
construction, and the rubric would secretly re-measure the classification accuracy
already in Table II. **Retrieval therefore starts from the observed symptoms, not
from the predicted label**, so it can agree or disagree with the classifier, and
that disagreement is itself information for the operator.

### Documents and index are separate on purpose

| Piece | What it is | Where it comes from |
|---|---|---|
| **Document** (what gets cited to the operator) | Public description of the fault | Downs and Vogel 1993, citable. **No corrective procedures** |
| **Retrieval index** | A symptom signature per fault | Estimated **inside each fold**, training portion only |

This is how retrieval-augmented systems are built: documents carry the evidence a
human reads, an index maps a query to them. Learning the index from data is
standard and, fitted per fold, leaks nothing. What may never be invented is the
text shown to the human.

**Not claimed:** the knowledge base carries fault descriptions and symptom context
only. TEP is a simulation, it has no maintenance history, so there are no
corrective procedures to cite and none will be written. Plant documentation stays
an additional corpus, never a dependency and never ground truth.

### Knowledge base

- 21 short Spanish documents, one per class (normal plus IDV 1 to 20), versioned in
  the repository so a reviewer gets the same corpus.
- Each holds the fault name, the public description of the disturbance, and the
  variables it is documented to affect.

### Query: the symptom profile of an episode

- Baseline: the mean and standard deviation of each of the 52 process variables
  over the normal-operation runs **of the training portion of the fold**.
- The episode's profile is the signed standardized deviation of its window mean
  from that baseline, one value per variable.

### Index: the symptom signature of each fault

- For each class, the centroid of the deviation profiles of its training runs.
- 21 signatures of 52 values each, fitted per fold.

### Retrieval and fusion

- Retrieval ranks the 21 documents by cosine similarity between the episode
  profile and each signature, turned into a distribution by a softmax at
  temperature 1.
- The copilot's ranking fuses the two opinions:
  `score = (1 - w) * classifier probability + w * retrieval distribution`.
- **Pre-declared grid of 3 configurations**, the same count every other model
  received: `w` in {0.25, 0.50, 0.75}, selected by macro-F1 on seed 0.
- Classifier: the v1b 1D-CNN, the best model of the Week 3 row, unchanged.

### Ablation: does the agent contribute

- **Without retrieval**: `w = 0`, the classifier alone.
- **With retrieval**: the selected `w`.
- The gap between the two, on macro-F1 over the same 15 folds, is the agent's
  contribution. If it is smaller than the standard deviation it is not a
  contribution, and that is what gets reported.

### Rubric: quality of the root cause, automatic and deterministic

Scored per episode, 0 to 3 points. It is automatic on purpose: a human rubric
cannot be reproduced by a reviewer running one command.

- +1 if the recommended root cause is the true one.
- +1 if the cited document is the one of the true root cause.
- +1 if the true root cause appears among the 3 retrieved documents shown.

Reported as the mean over episodes, with mean +- standard deviation over the 15
folds, and with the same breakdown for the ablation arm.

### Confidence signal

Episodes are split by whether the classifier and the retrieval agree on the top
hypothesis. Accuracy is reported on each subset, together with the share of
episodes in each. A recommendation the operator should distrust is one where the
two disagree, which is operationally useful and costs nothing to compute.

### Rules, unchanged

Same frozen partition and the same 15 folds (StratifiedGroupKFold by run, k = 5,
seeds 5, 17, 42), macro-F1 primary and Recall@3 secondary, mean +- standard
deviation, every statistic fitted inside the fold, test sealed. Cost reported on
the same run and the same machine: index size, retrieval milliseconds per episode,
and the end-to-end copilot latency. Script: `12_copilot_rag.py`, added to
`run_all.py`, so one command still reproduces everything.

> **What this became.** Two details of the paragraph above aged and are corrected
> here rather than rewritten above, because a pre-registration that is edited to
> look right afterwards is worth nothing. The script is `12_agente_v1.py`, not
> `12_copilot_rag.py`: the name changed when the alarm layer and the action loop
> were added to what had been planned as a retrieval step. And the cost column of
> Table II does not report index size, retrieval milliseconds and end-to-end
> latency separately; it reports what every other row reports, so the eight rows
> can be compared: stored numbers, training seconds and inference milliseconds
> per episode, which for this row are 18,405, 0 and 0.184. The retrieval time is
> inside that last figure rather than beside it.

## Figure 1 in text: the four pieces, the guard, the person, the measured point

> This is the figure of the article written as text, so the drawing and the code
> cannot drift apart. Declared 2026-09-14, before the agent exists.

**1. Perceives.** The alarm flow and the process variables of the run: the causal
window of 20 steps over 52 variables, plus the alarm events derived from it.

**2. Scores.** The fault classifier, which is the saved v1b 1D-CNN of that fold
loaded from disk and never retrained, plus the alarm rate of the window.

**3. Reasons.** Proposes the root cause from the documents retrieved by symptom
similarity and from the first alarms of the episode. **Implemented with rules,
not with a language model, and declared as such.** The fixed prompt and the model
and version constants live in `prompts/razona.txt` so a language model can be
connected later without changing the architecture.

**4. Decides.** One action from the declared list, each with its guard.

**The loop.** The action `observe` moves the window forward, so what is perceived
next is not what was perceived before. That is what makes this a loop and not a
pipeline: the same episode can be seen twice, differently, because the agent
chose to look again.

**The guard, on every action.** The copilot only suggests. It never writes a
setpoint, never trips equipment, never acts on the process. There is no code path
from the agent to the plant.

**Where the person is.** The operator reviews before any decision reaches the
plant, the machine or production. The agent proposes, prioritizes and explains;
the human approves, edits or rejects. The article states this.

**Where the number is measured.** The Table II figure is computed from
`results/logs/decisiones.jsonl` and the labels, at the output of `decide`, using
the final ranking. **Never from generated text.** What the reasoning piece
produces is judged apart, with the rubric.

**The ablation row, with its name.** `Sin agente (ablacion)`: the same loop with
the reasoning piece removed, so `decide` sees only the classifier and no
retrieved evidence. Same partition, same metric, same seeds.

## Extension: alarms, actions and the loop (written BEFORE running anything)

> Extends the copilot declaration above on 2026-09-14, still before any copilot
> code exists. Reason for the extension: an agent that always runs the same steps
> in the same order is not an agent, and the alarm layer the title promises was
> never implemented.

### The alarm layer

The paper has always said an alarm layer is derived from the process variables by
configured limits. It is declared here and implemented now.

- **Limits**, fitted **inside the fold** on the training portion: for each of the
  52 variables, the mean and standard deviation over normal-operation runs only.
- **An alarm fires** for variable `v` at sample `t` when the value leaves the band
  `mean_v +- k * std_v`, with **k = 3** pre-declared, the usual three-sigma
  convention. No limit is taken from any labelled fault run.
- **Alarm flow**: the ordered list of (variable, first crossing sample) inside the
  window.
- **Alarm rate**: alarming variables divided by 52, used by `puntua`.
- **First alarms**: the 3 earliest alarming variables, used by `razona`.
- **Priority**: alarms ordered by earliest crossing, ties broken by how far the
  value exceeds the band.
- **Grouping**: alarms whose variables correlate above **0.8** on normal
  operation, correlation computed **inside the fold**, are reported as one group.

### What is claimed about alarms, and what is not

- **Root alarm, evaluated on 15 of the 20 faults.** A root alarm counts as correct
  when the top-priority alarm sits on a variable that the public description
  associates with the true fault. **IDV 16 to 20 are documented as unknown in the
  source, so no mapping can be written for them honestly and they are excluded
  from this metric, which is declared in the article.** Class 0 has no root alarm.
- **Alarm reduction, on all 21 classes.** How many alarms the operator would see
  before prioritizing and grouping, and how many after. This needs no per-fault
  ground truth, so it covers the whole set.
- **The mapping is permissive, and that is declared.** Several faults share the
  same documented variables because they disturb the same stream or the same
  cooling circuit: IDV 1, 2, 7, 8 and 10 all point at stream 4, IDV 3 and 9 at
  the D feed, IDV 4, 11 and 14 at the reactor cooling circuit, IDV 5, 12 and 15
  at the condenser circuit. So the metric asks whether the top alarm sits on a
  variable documented for the true fault, **not** whether it identifies the fault
  uniquely, which is a different question and is already answered by Table II.
  With about 2 documented variables out of 52, hitting one by chance is near 4
  per cent, so the metric still has room to discriminate.
- **Two prioritizations, so RQ1 has an answer.** The research question asks
  whether data-driven alarm rationalization finds the root alarm better than a
  simple baseline. Ordering alarms by time **is** that baseline, so it cannot
  also be the proposal. Both are computed on the same episodes and reported side
  by side:
  - **Chronological, the baseline**: earliest crossing first, ties broken by how
    far the value leaves the band. It uses no knowledge at all.
  - **Knowledge-driven, the proposal**: each alarming variable is weighted by the
    retrieval mass of the documents that name it, so an alarm on a variable the
    retrieved evidence associates with the fault rises to the top. Ties broken by
    earliest crossing. It exists only in the proposed arm, because the ablation
    has no retrieval, and that is part of what the ablation demonstrates.
  - Reported as `RootAlarmChrono` and `RootAlarmKB`. The alarm reduction metric
    keeps using the chronological order, because grouping is about which alarms
    collapse together and not about which one leads.
- The mapping rule itself is declared in `kb/tep_kb.json`: only the measured or
  manipulated variables that correspond directly to the stream or equipment the
  source names, never downstream effects, because those would be our inference
  rather than documentation.
- Not claimed: that the root alarm is known for IDV 16 to 20.

### The action space, each with its guard

| Condition | Action | Guard |
|---|---|---|
| Classifier and retrieval agree on the top hypothesis and the top probability is at least `tau` | **generate** the recommendation with its cited document | suggests only |
| They disagree, or the top probability is below `tau`, and the window has not been moved yet | **observe**: advance the window by 10 samples and run the loop once more | suggests only |
| They still disagree after one move | **defer**: hand the operator the 3 hypotheses flagged as uncertain | suggests only |
| The top hypothesis is normal but the alarm rate is above the flood threshold | **alert**: report that alarms are firing without a diagnosis | suggests only |

- `tau` is pre-declared at **0.50**.
- **The flood threshold is pre-declared at 10 variables in alarm** inside the
  window. ANSI/ISA-18.2 calls a flood more than 10 alarms in a 10-minute window
  per operator; we count distinct variables in alarm inside the 60-minute causal
  window and keep the same count of 10, which is lenient relative to the
  standard and is declared as such rather than tuned.
- **The window can move, so the data read is wider than the scored window.** The
  agent reads samples 21 to 51 of the run and scores 20 of them: 21 to 41 before
  moving, 31 to 51 after. This stays causal, since sample 51 is simply the later
  decision moment, and it never touches the sealed test pool.
- **When the window moves, the standardization of the saved model is reused**, not
  refitted. Refitting on the moved window would be fitting a statistic on the data
  being scored.
- `observe` advances to the window starting 10 samples later and scores **the same
  20 steps** the model was trained on, so nothing is fed a shape it never saw.
  It stays causal: it only uses data available at the later decision moment.
- **At most one move**, so the loop terminates and latency is bounded.
- The cost of `observe` is 10 samples of plant time, which is 30 minutes at the
  TEP sampling rate. That is the accuracy against latency trade-off the agent
  makes, and it is reported.

### Retrieval, now informed by the alarms

The query is the deviation profile **restricted to the variables that alarmed**,
so the alarms actually drive the retrieval. If no variable alarms, the full
profile is used and the line records it. Everything else stays as declared above:
per-fold signatures, cosine similarity, softmax at temperature 1.

### The decision log

`results/logs/decisiones.jsonl`, one JSON line per decision, with the four pieces
in every line so the group can check them before looking at any number:

- identity: fault number, simulation run, fold, seed, arm (proposed or ablation)
- perceives: alarm count, alarm rate, the first alarms
- scores: the 3 top classes with their probabilities
- reasons: the 3 retrieved documents with their scores, and the one cited
- decides: the action, the final 3 hypotheses, the guard
- cost: seconds, iterations, tokens (zero, the reasoning piece is rules)
- label: the true class, written last and never read by the agent

**The metric is computed from this file and the labels**, which is what makes the
ablation and the figure possible.

### The rubric, twice

- **Automatic**, inside the pipeline, 0 to 3 per episode as already declared. It
  is what a reviewer reproduces with one command.
- **Human**, on a sample of **30 episodes** drawn with a declared seed, scored by
  **2 people** with their agreement reported. It measures whether the explanation
  is useful to a person, which no automatic score can settle. It is declared as
  not reproducible by the command, and reported apart.

### Three arms, and a rubric that is not allowed to flatter us

Comparing the rubric of a system that retrieves against one that does not is
generous by construction: the arm without retrieval **cannot** score the two
grounding points, so counting them as zero turns an absence into a defeat and
inflates the gain. Two corrections are declared, both before running:

**The rubric is decomposed and reported point by point.**

| Point | What it measures | Comparable without retrieval |
|---|---|---|
| R1 | the recommended root cause is the true one | yes |
| R2 | the cited document is the one of the true fault | no |
| R3 | the true fault is among the 3 documents shown | no |

For an arm that produces no citation, R2, R3 and the rubric total are reported as
**not applicable**, never as zero. R1 is the comparable part.

**A third arm gives grounding a fair baseline.**

| Arm | Ranking | Citation |
|---|---|---|
| `Sin agente (ablacion)` | classifier alone | none |
| `Anclaje por etiqueta` | classifier alone | the document of the **predicted class** |
| `Metodo propuesto` | classifier fused with symptom retrieval | the document found by **symptom retrieval** |

The middle arm is the dictionary lookup this design deliberately refused as the
proposal. As a **baseline** it is exactly right: it is what anyone would do
without symptom retrieval, and it makes R2 and R3 comparable. It shares the
ranking and the actions of the ablation, so the only thing that changes between
them is whether a citation exists.

**Declared in advance, because it may not flatter the proposal:** the classifier
is strong and symptom retrieval is a simple centroid, so label lookup may well
cite the right document more often than symptom retrieval does. If it does, that
is reported. The claim for symptom retrieval was never that it is a better
document finder; it is that it is an **independent** opinion, and independence is
what produces the confidence signal and the answer to RQ1, neither of which a
lookup keyed by the classifier can give.

### The qualitative sample, drafted outside the pipeline

The reasoning piece is rules, so nothing in the measured path writes prose. To
still show what the copilot would say to an operator, a small qualitative sample
is drafted **outside** the reproducible path:

- **One episode per action** (generate, observe, defer, alert), picked by a
  declared rule: the first episode in `decisiones.jsonl` order that ends in that
  action, on seed 42. If an action never fires, that is recorded instead.
- Its recommendation text is drafted with an AI assistant **from the line already
  written in the decision log**, and committed as a static file under
  `results/samples/`.
- **Stated in the article**: these texts are illustrative, were written outside
  the pipeline, are **not** reproduced by the command, and **produce no reported
  number**. Every measured quantity comes from the rules path.
- The fixed prompt stays in `prompts/razona.txt` so a language model can take over
  the reasoning piece later without changing the architecture.

### Table II gets two rows

`Sin agente (ablacion)` and `Metodo propuesto (copiloto v1)`, both with mean +-
standard deviation over the same 15 folds and their cost, followed by the
sentence: the proposed method beats the system without the agent by so much, or it
does not and the most likely cause is such. Not beating the ablation and
explaining it is a valid outcome; not having the ablation is not.

Script: `12_agente_v1.py`, added to `run_all.py`.

## Why three costly cases and not five

Five cases were considered. It stays at three, and the reason is in the numbers
rather than in taste. Ten faults qualify, meaning
the copilot ranked normal operation first on at least one episode of each. By
per-class F1 the first three are separated by real gaps, 0.149, 0.315 and 0.372,
but the fourth and the fifth are IDV(20) at 0.43184 and IDV(13) at 0.43245: six
ten-thousandths apart, with IDV(17) not far behind. Cutting at five forces a
tiebreaker that was never declared, and choosing one after seeing the scores is
the thing this file exists to prevent. The sentence "the rule leaves no room to
pick a flattering example" would stop being true.

The three also share a mechanism, which is what makes them worth a discussion:
all three ended in `defer` and all three read as a healthy plant. IDV(20) and
IDV(13) defer in 75% and 94% of their episodes and would repeat the finding
without adding one.

## Human rubric: the sampling rule, the raters and the items (written BEFORE drawing the sample)

Dated 2026-09-17. The section "The rubric, twice" above committed to thirty
episodes, a declared seed, two raters and their agreement. It did not say which
episodes, which items, who rates, or how agreement is computed. This section
fixes all four, and it is committed before the sample is drawn. Nothing above is
edited: a pre-registration that is rewritten to look right afterwards is worth
nothing.

### One arm, and what that costs

The original intent was to compare arms, which is why `Anclaje por etiqueta`
exists as a baseline: it is what makes R2 and R3 comparable. That comparison is
dropped here for time. Only the `proposed` arm is rated, thirty texts rather than
sixty.

The consequence is declared rather than discovered: **the human rubric is
descriptive, not comparative.** It reports whether this copilot's explanation is
usable by a person. It does not, and may not be reported as if it does, show that
symptom retrieval explains better than label anchoring. That question stays
unmeasured, and the article says so.

### Who rates, and who may not

Josue Rivera and Christian Barahona rate. Mario Elvir is excluded because he
built the system: the same reason the copilot is not exercised by the session
that wrote it. He draws the sample and holds the key.

**There is no third adjudicator.** Disagreements are reported as disagreements,
per item. Resolving them would produce a single tidy number that hides the one
thing two raters were hired to reveal.

### Blinded

The rater sees the text and the cited document. The rater does not see the true
label, whether the copilot was right, the classifier's probabilities, or the
episode identifier. Texts are shuffled with the seed below and the key is written
to a separate file that is not opened until both sheets are returned.

### Which thirty episodes

Drawn from `results/logs/decisiones.jsonl`, arm `proposed`, seed 42, with
`numpy.random.default_rng(20260917)`, at random inside each stratum. Correct
means `decide.top3[0] == label`.

| Stratum | Available | Drawn |
|---|--:|--:|
| `generate`, correct | 4,169 | 14 |
| `generate`, wrong | 135 | 4 |
| `defer` | 6,188 | 9 |
| `alert` | 8 | 3 |

**Why the four wrong answers are forced.** The copilot answers correctly on 96.9%
of the episodes it answers, so a uniform draw of eighteen `generate` episodes
yields half an error on average. The raters would judge clarity only where the
system is right, which is the less interesting half: what matters for an
operator-facing system is whether the text stays honest when the diagnosis is
wrong.

**The price, declared here.** The sample is stratified and is not a random sample
of what an operator would meet. The rubric mean is therefore **not** an estimate
of anything about the population of episodes, and neither the article nor the
README may present it as one. Results are reported per stratum.

This also avoids the failure recorded in `results/samples/README.md`, where the
declared rule "the first episode in log order" landed on normal operation three
times out of four, because the fold is ordered by class.

### The items

Five, binary, scored per text.

| Item | Question |
|---|---|
| H1 | Does it give one cause and two alternatives, in that order, in six sentences or fewer? |
| H2 | Does the cited document exist in `kb/tep_kb.json` and say what the text claims it says? |
| H3 | Where classifier and retrieval disagree, does the text state the disagreement instead of hiding it? |
| H4 | Would you act on this at three in the morning without asking another question? |
| H5 | Does the text assert anything absent from the log line and the cited document? |

None of these asks whether the diagnosis was correct. That is R1, already measured
automatically over 31,500 episodes, and an item that re-measured it would be the
trap this file warns about in "The trap this design avoids": a rubric that
secretly re-measures classification accuracy.

**H5 carries the weight and is reported apart from the mean.** A single yes is
disqualifying for that text, because the claim this whole repository makes is that
nothing is invented. H4 is the only subjective item and is expected to be where
the raters agree least.

### Agreement

Reported per item: Cohen's kappa, raw percent agreement, **and** both raters'
marginals. All three, not one. H2 is expected to be almost all yes, and kappa is
unstable under a marginal that lopsided, so reporting it alone would mislead in
either direction.

### Where it lives

Per-rater sheets in `results/rubrica_humana/`, so anyone can recompute kappa from
the raw scores. The draw is reproducible and its script is committed; the scoring
is not, and the human rubric stays **declared as not reproducible** by
`python run_all.py`. The draw script is deliberately not added to `run_all.py`,
which stays at 23 steps, because it feeds a measurement the command cannot
produce.

> **What the draw gave, recorded after running it on 2026-09-17.** The four
> wrong answers are all the same confusion: IDV(8) reported as IDV(1). That is
> not a bad draw, it is what the errors are. Of the 135 wrong `generate`
> episodes, 97 are that one pair, 72% of them, over 13 distinct pairs in all, so
> four uniform draws land on it about a quarter of the time. The consequence is
> real and is reported rather than fixed: **the raters see one failure mode four
> times, not four failure modes.** The rule is not re-drawn and no stratum is
> added inside the errors, because changing the rule after seeing the draw is the
> thing this file exists to prevent. What the error stratum measures is therefore
> whether the text stays honest on the copilot's most common mistake, which is a
> narrower question than the one intended, and the article says so.
>
> Two other properties of the draw, neither of them steered: all thirty episodes
> carry a citation, so H2 is scorable on every text; and classifier and retrieval
> disagree on twelve of the thirty, so H3 has something to measure on twelve.
> No episode of normal operation was drawn, which is expected at 500 of 10,500.

> **A leak found and closed on 2026-09-17, before any text was drafted.** The
> file handed to the drafting step was the raw log line, and the raw log line
> carries `label`. Worse, `id` is `[true class, run]`, so even stripping `label`
> would have left the answer in plain sight. The drafter would have been free to
> write a text better than the evidence the copilot actually had, and H5, which
> asks whether the text asserts anything absent from that evidence, would have had
> nothing left to catch. The file now carries only the three inputs
> `prompts/razona.txt` declares, plus the action and the agreement flag, and
> `22_muestra_rubrica.py` asserts that neither field can reappear. **The draw did
> not change**: `muestra.csv` hashes to the same `0d2f6561...` before and after,
> which is the point of a deterministic rule.

> **What a script is allowed to check.** `23_verifica_textos.py` gates the texts
> on form alone: thirty files, six sentences or fewer, no bullets, one paragraph,
> nothing extra. It does not check whether the citation exists, whether the cited
> document says what the text claims, or whether anything was invented, because
> those are H2, H3 and H5. A script that filtered them first would leave the human
> rubric measuring itself. The consequence is declared rather than left implicit:
> **H1's mechanical part is machine-enforced before rating**, so a high H1 is not
> evidence about the copilot, and what H1 still measures is the part no script can
> settle, one cause and two alternatives in that order.

### Order of operations

1. Commit this section.
2. Draw the thirty episodes.
3. Draft the thirty texts from the log line and the cited document, following
   `prompts/razona.txt`, outside this repository's measured path.
4. Shuffle, rate blind, return both sheets.
5. Compute agreement and report per stratum.

Steps 1 and 2 in that order are the whole point.

## Consistency check (paragraph vs. code vs. table)

- Dataset (Rieth; 500/class; 21 classes; unit = run) -> matches `01`/`02`. OK
- Partition (by run, stratified, seed 42; test 10,500 sealed; dev 10,500; saved
  to disk, sha256 4cf7e020b0f2faa6) -> matches `02_make_partition.py`. OK

> **Why this hash is not the one an earlier draft cited.** It was
> `f55e7729a298e23c` until 2026-09-16, and the partition did not change: the same
> manifest was being written with CRLF on Windows and LF on Linux, so the file
> hashed differently on each while its contents were identical. A hash that
> depends on the operating system cannot serve as proof that a split is frozen,
> which is what this one is for. The writer now fixes the line terminator and
> `.gitattributes` keeps git from converting it back, so the three platforms
> agree. Continuous integration found this on its first run, by rebuilding the
> manifest on Linux and comparing.

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
  (the abstract, the objectives and the results) and the figure;
  `protocolo_validacion.md` removed so this file is the only protocol. OK
- Selection criterion -> hyperparameters AND the best model are chosen by
  macro-F1, the primary metric (`04_classics_cv.py`, fixed 2026-09-13; it used to
  select by Recall@1, which contradicted the paper). Verified that Recall@1 would
  select the identical configuration for all three models, so no number changed. OK
- Inference time (ms) -> amortized per-episode latency, measured for every row in
  one run by `17_cost_table.py` (`results/cost_table.csv`). Wall-clock, so it moves
  between runs: a full re-run on 2026-09-15 gave 0.052 for the random forest against
  the 0.054 of the run before it, and 0.032 for gradient boosting against 0.031. The
  file is the value; this line is not, and no exact latency is pinned here. OK
- Per-model training time (s) -> same run, same machine: trivial <0.01, logistic
  regression ~3, random forest ~6, gradient boosting ~8. Wall-clock, so it
  moves with machine load. The ~20 s once recorded here for gradient boosting was
  from an earlier run. OK
- Table II is generated -> `19_tabla2_json.py` collects every number into
  `results/tabla2.json` and `resultados.py` renders and splices it, so no cell of
  Table II is typed anywhere. `python code/resultados.py --check` fails if the
  manuscript and the data disagree. OK
- Section IV of the paper -> reduced on 2026-09-15 to the seven sentences above
  and nothing else, which took the paper from eight pages to seven, with the
  bibliography on page 7. What it stopped declaring is listed in the note above
  the paragraph. OK
- Repository -> public at https://github.com/MarioElvir-UTH/tep-rootcause-copilot
  (code, frozen partition, results, README with the one-command reproduction). OK
- PR-AUC -> computed on request by `21_pr_auc.py` (`results/pr_auc.csv`), as the
  macro-averaged average precision over the same folds and seeds. It changes no
  conclusion: the ablation still leads, the proposed method still trails it in all
  15 folds, and the only reordering in the table is between the perceptron and
  logistic regression, the pair already declared comparable. Table II keeps
  Recall@3 because it is what the operator reads and because it was declared
  before any score was seen, while PR-AUC was computed after; the paper reports it
  as a check, not as a criterion. OK
