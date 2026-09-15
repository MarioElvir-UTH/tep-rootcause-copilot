# Qualitative sample: what the copilot would say to an operator

**These texts produce no reported number. They are not reproduced by
`python run_all.py`. Every measured quantity in the paper comes from the rules
path, computed at the output of `decide` from `results/logs/decisiones.jsonl`
and the labels, never from prose.**

The reasoning stage of the agent is implemented with rules, so nothing in the
measured path writes prose. This directory exists to still show what the copilot
would put in front of an operator. It was drafted **outside** the reproducible
path, as declared in `PROTOCOLO.md` before the agent was run.

## How the episodes were chosen

The rule was declared in advance and applied mechanically:

> One episode per action (generate, observe, defer, alert), the first episode in
> `decisiones.jsonl` order that ends in that action, on seed 42.

The sample is drawn from the **proposed** arm, the only one whose reasoning stage
produces a citation. Filtering `seed == 42` and `arm == "proposed"` leaves 10,500
episodes, in the order the agent decided them.

| Action | File | Episode | `id` | Outcome |
|---|---|--:|---|---|
| generate | `01_generate.md` | 44 | `[0, 195]` | **wrong**: states IDV(8), the run is normal operation |
| observe | `02_observe.md` | 1 | `[0, 1]` | never terminal, see the file |
| defer | `03_defer.md` | 1 | `[0, 1]` | correct to hold: low confidence and a disagreement |
| alert | `04_alert.md` | 19 | `[0, 81]` | correct: 14 alarms while the top class is normal |

Each file carries the verbatim log line it was drafted from, so anything the prose
asserts can be checked against the record. To pull a line yourself:

```bash
grep -n '"id": \[0, 195\]' results/logs/decisiones.jsonl | grep '"seed": 42' | grep proposed
```

## Two honest notes on this sample

**The declared rule lands on normal-operation runs.** The validation fold is
ordered by class, so the first 100 episodes of seed 42 are class 0 and the first
fault episode is number 101. Three of the four selected episodes therefore have
normal operation as their ground truth. A sample of fault episodes would
illustrate diagnosis better, but choosing one now would mean picking episodes
after seeing them, which is the thing the pre-registration exists to prevent. The
rule is reported as declared and its consequence with it.

**`observe` is not a terminal action.** It is the loop step: when the agent
observes, the window advances and the loop runs again, so the episode ends in some
other action. No episode can "end in observe", and the declared fallback applies:
the fact is recorded rather than worked around. See `02_observe.md`.

## How these texts were drafted

From the log line alone, following `prompts/razona.txt` exactly: Spanish, at most
six sentences, no bullets, the most likely cause and two alternatives in that
order, the retrieved document cited by name, any disagreement between classifier
and retrieval stated explicitly rather than hidden, no corrective procedures
(the TEP corpus contains none), and a closing reminder that the decision belongs
to the operator. Drafted with an AI assistant, as declared in the README of the
repository and in the article.

Nothing in these texts asserts anything absent from the log line and the cited
document in `kb/tep_kb.json`.
