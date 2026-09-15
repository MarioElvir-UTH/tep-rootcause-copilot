# The error that costs most: three faults the copilot read as a healthy plant

**These texts produce no reported number.** Same standing as the rest of this
directory: drafted outside the pipeline, not reproduced by `python run_all.py`.

## Why these three, and not three others

The rule was fixed before looking at any episode:

> The first episode in decision-log order, for each of the three worst-classified
> faults that the copilot called normal operation.

`18_worst_errors.py` applies it. "Worst-classified" is per-class macro-F1 on the
proposed arm; "called normal operation" means the top-ranked class was class 0.
The rule targets what this work treats as the costliest error, a real alarm buried
under the avalanche, and it leaves no room to pick a flattering example.

| Fault | per-class F1 | Episode | Seed | Fold |
|---|--:|---|--:|--:|
| IDV(15) | 0.149 | `[15, 12]` | 5 | 0 |
| IDV(18) | 0.315 | `[18, 37]` | 5 | 0 |
| IDV(9) | 0.372 | `[9, 12]` | 5 | 0 |

## What the three have in common

**None of them became a wrong answer.** All three ended in `defer`: the classifier
and the retrieval disagreed, so the copilot handed the episode to the operator
instead of asserting anything. Across the whole run the copilot answers
"normal operation" in **0 of 12,898** answers; when its top class is normal it
always defers or alerts. The costly error is real, but it reaches the operator as
silence rather than as a false all-clear.

**In two of the three, the true fault is in the short list.** IDV(15) is ranked
second and IDV(9) third, both inside the three entries the operator is shown. The
copilot did not fail to see them; it failed to put them first.

---

## Case 1: IDV(15), the stuck valve

```json
{"id": [15, 12], "seed": 5, "fold": 0, "arm": "proposed",
 "percibe": {"n_alarmas": 4, "tasa": 0.0769,
             "primeras": ["xmv_1", "xmeas_21", "xmeas_2"], "mostradas": 4,
             "raiz_cronologica": "xmv_1", "raiz_conocimiento": "xmeas_21"},
 "puntua": {"top3": [0, 15, 10], "prob": [0.2229, 0.1446, 0.1318]},
 "razona": {"docs": ["IDV(5)", "IDV(8)", "IDV(13)"],
            "score": [0.0566, 0.0546, 0.0541], "cita": "IDV(5)", "uso_alarmas": true},
 "decide": {"accion": "defer", "guarda": "solo sugiere, no actua",
            "top3": [0, 15, 10], "concuerda": false},
 "costo": {"segundos": null, "iteraciones": 2, "tokens": 0}, "label": 15}
```

> El clasificador situa como hipotesis mas probable la operacion normal, con una
> probabilidad de 0.22, seguida de IDV(15) e IDV(10); ninguna alcanza el umbral de
> confianza de 0.50. La evidencia recuperada por similitud de sintomas apunta a
> IDV(5), y no coincide con el clasificador, por lo que se presentan ambas. En
> esta ventana cuatro variables entraron en alarma; la primera en orden
> cronologico es xmv_1 y, priorizando por la evidencia recuperada, xmeas_21. El
> copiloto ya avanzo la ventana treinta minutos y sigue sin confianza suficiente.
> Por la baja confianza y la discrepancia, traslada el caso al operador. La
> decision final es del operador.

**What it shows.** The source document for IDV(15) calls it "historically one of
the most difficult disturbances to isolate", and the copilot agrees with that
assessment in the only way it can: it ranks the fault second, never gets above
$0.22$ on anything, and stops. The retrieval is no help here, citing IDV(5) and
missing IDV(15) entirely, and the knowledge-driven root alarm picks `xmeas_21`
while the document names `xmv_11` and `xmeas_22`. Two of the copilot's three
mechanisms fail on this episode and the third, the guard, is what keeps the
failure from reaching the operator as an assertion.

---

## Case 2: IDV(18), the one the source leaves undocumented

```json
{"id": [18, 37], "seed": 5, "fold": 0, "arm": "proposed",
 "percibe": {"n_alarmas": 2, "tasa": 0.0385, "primeras": ["xmeas_30", "xmeas_10"],
             "mostradas": 1, "raiz_cronologica": "xmeas_30",
             "raiz_conocimiento": "xmeas_30"},
 "puntua": {"top3": [0, 15, 20], "prob": [0.2059, 0.1857, 0.136]},
 "razona": {"docs": ["IDV(2)", "IDV(3)", "IDV(7)"],
            "score": [0.0896, 0.0549, 0.0493], "cita": "IDV(2)", "uso_alarmas": true},
 "decide": {"accion": "defer", "guarda": "solo sugiere, no actua",
            "top3": [0, 15, 20], "concuerda": false},
 "costo": {"segundos": null, "iteraciones": 2, "tokens": 0}, "label": 18}
```

> El clasificador situa como hipotesis mas probable la operacion normal, con una
> probabilidad de 0.21, seguida de IDV(15) e IDV(20). La evidencia recuperada
> apunta a IDV(2) y no coincide con el clasificador. En esta ventana solo dos
> variables entraron en alarma y, tras agrupar las correlacionadas, se presenta
> una sola al operador: xmeas_30. Debe advertirse que la perturbacion de fondo
> puede ser una de las que la fuente documenta como desconocidas, en cuyo caso no
> existe documento que citar. Por la baja confianza y la discrepancia, el copiloto
> traslada el caso al operador. La decision final es del operador.

**What it shows.** This is the hardest case in the paper for an honest reason: the
source documents IDV(18) as an unknown disturbance, with no cause and no affected
variables. The true class is not in the top three, so the operator's short list
does not contain it, and it cannot: there is no document describing what to look
for. The copilot is working without the evidence the method depends on. Episodes
like this are why IDV(16) to IDV(20) are excluded from the root-alarm metric,
which is a limit of the corpus rather than of the copilot, and why the paper says
so instead of scoring them as failures.

---

## Case 3: IDV(9), the fluctuation that stays small

```json
{"id": [9, 12], "seed": 5, "fold": 0, "arm": "proposed",
 "percibe": {"n_alarmas": 4, "tasa": 0.0769,
             "primeras": ["xmv_1", "xmeas_21", "xmeas_2"], "mostradas": 4,
             "raiz_cronologica": "xmv_1", "raiz_conocimiento": "xmeas_21"},
 "puntua": {"top3": [0, 13, 9], "prob": [0.2005, 0.1778, 0.1579]},
 "razona": {"docs": ["IDV(5)", "IDV(13)", "IDV(8)"],
            "score": [0.056, 0.0537, 0.0536], "cita": "IDV(5)", "uso_alarmas": true},
 "decide": {"accion": "defer", "guarda": "solo sugiere, no actua",
            "top3": [0, 13, 9], "concuerda": false},
 "costo": {"segundos": null, "iteraciones": 2, "tokens": 0}, "label": 9}
```

> El clasificador situa como hipotesis mas probable la operacion normal, con una
> probabilidad de 0.20, seguida de IDV(13) e IDV(9). La evidencia recuperada
> apunta a IDV(5) y no coincide con el clasificador, por lo que se presentan
> ambas. En esta ventana cuatro variables entraron en alarma; la primera en orden
> cronologico es xmv_1 y, priorizando por la evidencia recuperada, xmeas_21. El
> copiloto ya avanzo la ventana treinta minutos sin ganar confianza. Por la baja
> confianza y la discrepancia, traslada el caso al operador. La decision final es
> del operador.

**What it shows.** This is the episode where the knowledge-driven ordering loses to
the clock. The document for IDV(9) names `xmeas_2` and `xmv_1`, and `xmv_1` is
exactly the alarm that crossed its band first: ordering by time finds the root
alarm here, and weighting by retrieved evidence moves `xmeas_21` to the front and
misses it. The retrieval that produced that weighting cites IDV(5), IDV(13) and
IDV(8), none of them the true fault, so the evidence it is reasoning from is
wrong and the prioritization inherits the error. The fault itself is still in the
operator's short list, third. Across the run the knowledge-driven ordering beats
the chronological one, $0.383$ against $0.359$ in this arm, but the average is not
a guarantee per episode, and this is one of the episodes on the losing side.

---

## What would change it

All three are deferred because the classifier and the retrieval disagree, and in
two of the three the fault is already in the short list. Ranking with the
classifier and keeping symptom retrieval as an independent check, which the paper
names as future work, would answer on these episodes instead of deferring, at the
cost of losing the disagreement that currently protects the operator from a wrong
confident answer. Which of the two an operator prefers is a question about the
plant, not about the benchmark.
