# Action `defer`: the copilot holds, and says why

First episode of seed 42, proposed arm, that ends in `defer`: number 1,
`id [0, 1]`, fold 0. Ground truth: **class 0, normal operation**. The classifier's
top class is also normal operation, so holding costs nothing here, but the copilot
does not know that: it holds because two of its guards failed at once.

This is the most common action in the run, 58.9% of the episodes of seed 42.

## The log line it was drafted from

```json
{"id": [0, 1], "seed": 42, "fold": 0, "arm": "proposed",
 "percibe": {"n_alarmas": 1, "tasa": 0.0192, "primeras": ["xmeas_9"], "mostradas": 1,
             "raiz_cronologica": "xmeas_9", "raiz_conocimiento": "xmeas_9"},
 "puntua": {"top3": [0, 9, 18], "prob": [0.1813, 0.1449, 0.1436]},
 "razona": {"docs": ["IDV(4)", "IDV(12)", "IDV(15)"],
            "score": [0.0539, 0.0529, 0.0511], "cita": "IDV(4)", "uso_alarmas": true},
 "decide": {"accion": "defer", "guarda": "solo sugiere, no actua",
            "top3": [0, 9, 18], "concuerda": false},
 "costo": {"segundos": null, "iteraciones": 2, "tokens": 0},
 "label": 0}
```

## What the copilot would say to the operator

> La hipotesis mas probable del clasificador es operacion normal, con una
> probabilidad de 0.18, seguida de IDV(9) e IDV(18); ninguna alcanza el umbral de
> confianza de 0.50. La evidencia recuperada por similitud de sintomas apunta en
> otra direccion: el documento IDV(4) describe un escalon en la temperatura de
> entrada del agua de enfriamiento del reactor y asocia esa condicion a las
> variables xmeas_21 y xmv_10. El clasificador y el documento recuperado no
> coinciden, y esa discrepancia se informa en lugar de ocultarse. En esta ventana
> una sola variable entro en alarma, xmeas_9, que es tambien la primera en orden
> cronologico. Por la baja confianza y por la discrepancia, el copiloto no emite
> una recomendacion y traslada el caso al operador. La decision final es del
> operador.

## What this shows

Both guards are visible in the text. The top probability is $0.18$, below the
$\tau = 0.50$ threshold, and `concuerda` is `false`, so the classifier and the
retrieval point at different causes. Either one alone is enough to keep the copilot
from committing; here both hold.

The disagreement is stated rather than resolved, which is what the fixed prompt
requires and what the paper argues is the value of a retrieval that is independent
of the classifier. An arm that grounds by looking up the predicted class cannot
produce this sentence, because it agrees with itself by construction.

Note also `iteraciones: 2`: the agent observed first, advanced the window by 30
minutes of plant time, looked again, and still chose to hold. See `02_observe.md`.
