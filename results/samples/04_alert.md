# Action `alert`: alarm flood while the top class is normal

First episode of seed 42, proposed arm, that ends in `alert`: number 19,
`id [0, 81]`, fold 0. Ground truth: **class 0, normal operation**, and the
classifier's top class is also normal operation, so the copilot is right about the
state of the process.

`alert` is the rarest action, 8 of the 10,500 episodes of seed 42, which is 0.1%.
It fires on a specific contradiction: the process looks normal to the classifier
while the plant is showing a flood of alarms.

## The log line it was drafted from

```json
{"id": [0, 81], "seed": 42, "fold": 0, "arm": "proposed",
 "percibe": {"n_alarmas": 14, "tasa": 0.2692,
             "primeras": ["xmv_1", "xmeas_7", "xmeas_16"], "mostradas": 9,
             "raiz_cronologica": "xmv_1", "raiz_conocimiento": "xmeas_21"},
 "puntua": {"top3": [0, 18, 9], "prob": [0.1944, 0.1667, 0.1246]},
 "razona": {"docs": ["IDV(7)", "IDV(5)", "IDV(6)"],
            "score": [0.1199, 0.1011, 0.0679], "cita": "IDV(7)", "uso_alarmas": true},
 "decide": {"accion": "alert", "guarda": "solo sugiere, no actua",
            "top3": [0, 18, 13], "concuerda": false},
 "costo": {"segundos": null, "iteraciones": 1, "tokens": 0},
 "label": 0}
```

## What the copilot would say to the operator

> Catorce variables entraron en alarma en esta ventana y, tras agrupar las que
> estan correlacionadas en operacion normal, se presentan al operador como nueve
> alarmas; las primeras en aparecer son xmv_1, xmeas_7 y xmeas_16. El clasificador
> situa como hipotesis mas probable la operacion normal, con una probabilidad de
> 0.19, seguida de IDV(18) e IDV(9). Esa combinacion, una inundacion de alarmas
> junto a una hipotesis de operacion normal, es la condicion que el copiloto
> escala: no afirma una causa, advierte la contradiccion. La evidencia recuperada
> apunta a IDV(7), perdida de presion en el cabezal de C, con disponibilidad
> reducida en la corriente 4, y no coincide con el clasificador, por lo que se
> presentan ambas. Priorizando por la evidencia recuperada la alarma raiz seria
> xmeas_21, mientras que por orden cronologico seria xmv_1. La decision final es
> del operador.

## What this shows

Three mechanisms are visible at once in a single episode.

**Alarm rationalization.** Fourteen alarms become nine after alarms whose variables
correlate at $0.8$ or above on normal operation are collapsed into one group. That
is a 36% reduction in what the operator is asked to read, on the episode with the
heaviest alarm load in this sample.

**The two prioritizations, side by side.** Chronological order puts `xmv_1` first
because it crossed its band earliest. Weighting by retrieved evidence puts
`xmeas_21` first instead. That weight is the retrieval mass of **every** document
naming the variable, not only of the document cited: `xmeas_21` is named by IDV(4),
which is not among the three documents shown, so a variable can rise on evidence
spread across the corpus rather than on a single match. This is the comparison
behind RQ1, visible on one episode: $0.349$ against $0.619$ across the run.

**The flood guard doing its job.** The classifier is not confident about anything
here, $0.19$ on its top class, and it disagrees with the retrieval. Rather than
commit or silently defer, the copilot escalates, because a plant showing 14
variables out of band while the model says "normal" is exactly the situation an
operator should be told about. The copilot names the contradiction; it does not
resolve it, and it does not act.
