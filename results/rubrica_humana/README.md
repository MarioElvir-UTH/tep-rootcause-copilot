# Human rubric: the sample, the sheets, and what may be opened when

Thirty episodes drawn by `code/22_muestra_rubrica.py` under the rule
pre-registered in `PROTOCOLO.md`, section *"Human rubric: the sampling rule, the
raters and the items"*, which was committed **before** the draw was run.

**This rubric produces no number in Table II.** It is declared as not reproducible
by `python run_all.py`, and the draw script is deliberately not one of its 23
steps: the draw is deterministic, the scoring by two people is not.

## What is here

| File | What it is | Who may open it |
|---|---|---|
| `muestra.csv` | the key: which text is which episode, with the true label | **nobody** until both sheets are back |
| `entradas_redaccion.jsonl` | the three inputs `prompts/razona.txt` declares, per episode, with the ground truth removed | whoever drafts, **and the raters** |
| `redaccion.md` | the drafting brief for step 3, to be run in a separate session | whoever drafts |
| `textos/texto_NN.md` | the thirty texts | the raters |
| `paquete_evaluador.md` | **what a rater is handed**: the thirty texts, what the copilot had in front of it, and the three retrieved documents in full | the raters |
| `hoja_josue.csv` | blank scoring sheet, shuffled order | Josué Rivera |
| `hoja_christian.csv` | the same sheet, same order | Christian Barahona |

The sheets carry a text number and nothing else: no label, no probability, no
episode id, no indication of whether the copilot was right.

**The raters do get `entradas_redaccion.jsonl`, and they need it.** H3 asks
whether the text states a disagreement between classifier and retrieval. If the
text hid one, there is no way to know it existed without the input record. That
file carries no ground truth, so handing it over does not break the blind.

## The five items

Score **1 for yes, 0 for no**, and leave nothing blank.

| | Question |
|---|---|
| H1 | Does it give one cause and two alternatives, in that order, in six sentences or fewer? |
| H2 | Does the cited document exist in `kb/tep_kb.json` and say what the text claims it says? |
| H3 | Where classifier and retrieval disagree, does the text state the disagreement instead of hiding it? |
| H4 | Would you act on this at three in the morning without asking another question? |
| H5 | Does the text assert anything the retrieved evidence does not support? |

**H5 is the one where yes is the bad answer.** A single yes disqualifies that text
and is reported apart from the mean, because the claim this repository makes is
that nothing is invented.

None of the five asks whether the diagnosis was correct. That is R1, already
measured automatically over 31,500 episodes.

## What a machine checks, and what it does not

`code/23_verifica_textos.py` gates the texts on **form only**: thirty files
present, six sentences or fewer, no bullets, one paragraph, nothing extra. Form
is not what this rubric is about, so enforcing it is fair, and it keeps two people
from spending their evening on a formatting slip.

It does **not** check whether the citation exists, whether the cited document says
what the text claims, or whether anything was invented. Those are H2, H3 and H5.
Filtering them beforehand would leave the human rubric with nothing to measure,
and a high score would become a property of that script rather than of the
copilot.

> The machine checks the form, the people check the substance.

The consequence is declared: **H1's mechanical part is machine-enforced before
rating**, so a high H1 is not evidence about the copilot. What H1 still measures
is the part no script can settle, one cause and two alternatives in that order.

## What this sample is, and what it is not

It is **stratified**, not random: fourteen correct answers, four wrong ones, nine
deferrals and three alerts. The four wrong answers are forced on purpose, because
the copilot answers correctly on 96.9% of what it answers and a uniform draw would
have shown the raters almost no errors.

So **the rubric mean is not an estimate of anything about the population of
episodes**, and neither the article nor the top-level README may present it as
one. Results are reported per stratum.

Two consequences recorded after the draw and not corrected, since changing the
rule after seeing the result is what the pre-registration exists to prevent:

- All four wrong answers are the same confusion, IDV(8) reported as IDV(1). That
  pair is 97 of the 135 wrong answers available. The raters see **one failure mode
  four times, not four failure modes.**
- Only one arm is rated. The comparison against `Anclaje por etiqueta`, which the
  three-arm design exists to make possible, was dropped for time. **The human
  rubric is descriptive, not comparative.**

## Order

1. Commit the rule. Done, before the draw.
2. Draw. Done.
3. Draft the thirty texts in a separate session, following `redaccion.md`. Done
   on 2026-09-17, in a session opened on the project folder so that none of this
   project's memory was in scope. All thirty pass `23_verifica_textos.py`, and
   the only thing that session changed in the repository is `textos/`.
4. Build the package with `python code/25_paquete_evaluador.py`, hand each rater
   that document and their own sheet, and rate blind. **Pending.** Shuffling is
   already in the text numbers: they do not follow the strata.
5. Run `python code/24_acuerdo_rubrica.py`. It reports Cohen's kappa, raw percent
   agreement and both raters' marginals per item, plus a bootstrap interval, and
   the means per stratum. **It was written before either sheet was filled in**,
   for the same reason the sampling rule was committed before the draw.
   Disagreements are reported as disagreements: there is no third adjudicator,
   no pooled score and no rubric total.
