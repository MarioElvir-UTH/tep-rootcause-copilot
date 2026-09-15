# Action `generate`: the copilot commits, and is wrong

First episode of seed 42, proposed arm, that ends in `generate`: number 44,
`id [0, 195]`, fold 0. Ground truth: **class 0, normal operation**. The copilot
states IDV(8). **This episode is a failure, and it is the one the declared rule
selected.**

It is worth keeping precisely because of that. The classifier is confident
($0.64$, above the $\tau = 0.50$ guard) and the retrieval agrees with it, which is
the condition the paper reports as the reliable one: 94.0% correct when the two
agree. This episode is part of the remaining 6%.

## The log line it was drafted from

```json
{"id": [0, 195], "seed": 42, "fold": 0, "arm": "proposed",
 "percibe": {"n_alarmas": 0, "tasa": 0.0, "primeras": [], "mostradas": 0,
             "raiz_cronologica": null, "raiz_conocimiento": null},
 "puntua": {"top3": [8, 3, 15], "prob": [0.6448, 0.0755, 0.0653]},
 "razona": {"docs": ["IDV(8)", "IDV(10)", "IDV(15)"],
            "score": [0.0683, 0.0664, 0.0641], "cita": "IDV(8)", "uso_alarmas": false},
 "decide": {"accion": "generate", "guarda": "solo sugiere, no actua",
            "top3": [8, 3, 15], "concuerda": true},
 "costo": {"segundos": null, "iteraciones": 2, "tokens": 0},
 "label": 0}
```

## What the copilot would say to the operator

> La causa raiz mas probable es IDV(8), variacion aleatoria en la composicion de
> A, B y C de la corriente 4, con una probabilidad de 0.64; las alternativas son
> IDV(3) e IDV(15). El documento recuperado por similitud de sintomas es IDV(8),
> que describe una fluctuacion irregular y sostenida en la composicion de la
> alimentacion combinada, sin un escalon claro, y asocia esa condicion a las
> variables xmeas_4 y xmv_4. El clasificador y la evidencia recuperada coinciden
> en esta hipotesis. Debe advertirse que ninguna variable entro en alarma en esta
> ventana, de modo que la hipotesis se apoya en el perfil de desviacion y no en
> alarmas observadas. No se proponen procedimientos correctivos porque el corpus
> del proceso no los contiene. La decision final es del operador.

## What this shows

The text is faithful to the log: it reports the probability that was scored, cites
the document that was retrieved, and states the agreement that was recorded. It
also surfaces the one signal that should have given the operator pause, **zero
variables in alarm**, which the log records as `n_alarmas: 0`.

That is the useful part of the failure. The copilot commits on a deviation profile
with no alarm behind it, and a reader of the recommendation can see that from the
recommendation itself. The confidence signal reported in the paper is a population
statistic, not a guarantee on any single episode, and this file is what that
distinction looks like in practice.
