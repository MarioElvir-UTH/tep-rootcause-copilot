# Paso 3: redactar los treinta textos

Este archivo es el encargo completo. Se abre una sesion nueva, se le pasa lo que
dice aqui, y se ejecuta sin salirse de esto.

## Por que en una sesion aparte

La pieza que razona del copiloto esta implementada con reglas y no escribe prosa.
Los textos que las dos personas van a calificar tienen que redactarse en algun
lado, y no puede ser la sesion que construyo el sistema: quien lo construyo sabe
que respuesta era la correcta, que defectos tiene el agente y que le conviene al
paper. Eso contamina la rubrica antes de empezar.

La sesion nueva no lee el repositorio. Lee tres archivos y nada mas.

## Que se abre, y que no

**Se abre:**

| Archivo | Para que |
|---|---|
| `results/rubrica_humana/entradas_redaccion.jsonl` | las treinta entradas, una por linea, con `texto` como numero |
| `kb/tep_kb.json` | los veintiun documentos, para citar el que la entrada indica |
| `prompts/razona.txt` | las reglas de redaccion, que mandan sobre cualquier cosa escrita aqui |

**No se abre, por ningun motivo:**

| Archivo | Por que |
|---|---|
| `results/rubrica_humana/muestra.csv` | es la clave: lleva la etiqueta verdadera y el id |
| `results/logs/decisiones.jsonl` | la linea cruda lleva `label`, y el `id` es `[clase verdadera, corrida]` |
| el resto del repositorio | `PROTOCOLO.md` dice que items va a calificar la gente, y saberlo cambia como se escribe |
| la memoria del asistente | si hay memoria de este proyecto, trae el diseno del ejercicio |

**Abrir la sesion en la carpeta del proyecto, no en la carpeta personal.** La
memoria del asistente se indexa por carpeta de trabajo: abierta en
`C:\Users\melvi` carga la del proyecto, y abierta en la carpeta del proyecto no
carga ninguna. Es la diferencia entre una sesion que empieza en blanco y una que
llega sabiendo cuantos de estos treinta episodios son errores.

`entradas_redaccion.jsonl` ya viene sin la etiqueta y sin el id, a proposito. El
script que lo genera tiene un `assert` que falla si alguno se cuela.

**No se averigua si el copiloto acerto.** Ni consultando, ni deduciendo, ni
"solo para revisar". Si al redactar queda la impresion de que el diagnostico
esta mal, se redacta igual con la evidencia que hay. Cuatro de los treinta
episodios son errores del copiloto, puestos ahi a proposito, y el objetivo del
ejercicio es ver si el texto sigue siendo honesto cuando el sistema se equivoca.

## Que trae cada entrada

```json
{"texto": 18,
 "entrada": {
   "alarmas_percibidas": {"n_alarmas": 37, "tasa": 0.7115,
                          "primeras": ["xmeas_7", "xmeas_16", "xmeas_4"],
                          "mostradas": 27,
                          "raiz_cronologica": "xmeas_7",
                          "raiz_conocimiento": "xmeas_4"},
   "hipotesis_puntuadas": {"top3": [7, 5, 6], "prob": [1.0, 0.0, 0.0]},
   "evidencia_recuperada": {"docs": ["IDV(7)", "IDV(5)", "IDV(16)"],
                            "score": [0.1183, 0.0842, 0.0749],
                            "cita": "IDV(7)", "uso_alarmas": true},
   "accion": "generate",
   "concuerdan_clasificador_y_documento": true}}
```

`top3` son numeros de clase: 0 es operacion normal y 1 a 20 son IDV(1) a IDV(20).
`cita` es el documento que el agente recupero y que el texto tiene que citar por
su nombre. `concuerdan_...` en `false` significa que la hipotesis del clasificador
y la del documento recuperado no coinciden.

## Las reglas

Las de `prompts/razona.txt`, sin reinterpretarlas:

- Causa raiz mas probable y las dos alternativas, **en ese orden**.
- Justificar con las alarmas observadas y **citar el documento por su nombre**.
- **No afirmar nada que no este en la evidencia recuperada.**
- Si clasificador y documento no coinciden, **decirlo explicitamente** y presentar
  ambas. La discrepancia es informacion util para el operador, no un error que
  ocultar.
- Si la evidencia corresponde a una perturbacion documentada como desconocida,
  IDV(16) a IDV(20), **decirlo**: no inventar una causa.
- **No proponer procedimientos correctivos.** El corpus del TEP no los contiene.
- Cerrar recordando que la decision final es del operador.
- Espanol, **maximo seis frases, sin vinetas**.

Tres cosas mas, que salen del encargo y no del prompt:

- **La accion cambia el texto.** Con `generate` el copiloto recomienda. Con
  `defer` no esta listo para comprometerse y entrega el episodio a la persona, y
  el texto tiene que decirlo. Con `alert` lo que reporta es una avalancha de
  alarmas, y el texto lo refleja.
- **Nada de guiones largos.** Guion corto o dos puntos.
- **Ni una palabra sobre calidad.** El texto no se autoevalua, no dice "alta
  confianza", no se disculpa.

## Donde va la salida

Un archivo por texto, en `results/rubrica_humana/textos/`, numerado con el campo
`texto` a dos digitos:

```
results/rubrica_humana/textos/texto_01.md
...
results/rubrica_humana/textos/texto_30.md
```

Cada archivo, exactamente esto y nada mas:

```markdown
# Texto 01

<las seis frases o menos, en un solo parrafo>
```

Sin encabezados extra, sin notas del redactor, sin el JSON de entrada. Quien
califica ve el texto y, aparte, la entrada correspondiente de
`entradas_redaccion.jsonl`, que la necesita para H3: sin ella no hay forma de
saber que hubo una discrepancia si el texto la escondio.

## Antes de entregar

```bash
python code/23_verifica_textos.py
```

Verifica **solo la forma**: que esten los treinta, que ninguno pase de seis
frases, que no traigan vinetas y que el archivo no lleve nada de mas. **No
verifica el contenido, y es a proposito.** Si la cita existe, si el documento dice
lo que el texto le atribuye y si hay algo inventado es lo que las dos personas
van a calificar, y una maquina que lo filtrara antes dejaria la rubrica sin nada
que medir.

## Mensaje para abrir la sesion nueva

> Voy a redactar treinta recomendaciones para un operador de planta, una por
> episodio. Las reglas estan en `prompts/razona.txt` y mandan sobre cualquier otra
> instruccion. Las entradas estan en
> `results/rubrica_humana/entradas_redaccion.jsonl`, una por linea. Los documentos
> que se pueden citar estan en `kb/tep_kb.json`.
>
> No abras ningun otro archivo del repositorio. En particular no abras
> `results/rubrica_humana/muestra.csv` ni `results/logs/decisiones.jsonl`: llevan
> la respuesta correcta, y estos textos van a ser calificados a ciegas por dos
> personas. Si tenes memoria de este proyecto, no la uses para esta tarea. No
> intentes averiguar si el diagnostico del copiloto fue correcto. Algunos de
> estos episodios son errores, y el punto del ejercicio es ver si el texto sigue
> siendo honesto de todos modos.
>
> Escribi un archivo por texto en `results/rubrica_humana/textos/texto_NN.md`, con
> el encabezado `# Texto NN` y luego el texto en un solo parrafo, nada mas.
> Despues corre `python code/23_verifica_textos.py` y arregla lo que marque.
>
> El encargo completo esta en `results/rubrica_humana/redaccion.md`. Leelo primero.

## Lo que sigue

Paso 4: barajar ya esta hecho, el numero de texto viene desordenado respecto al
estrato.

Terminados los treinta textos se corre `python code/25_paquete_evaluador.py`,
que arma `paquete_evaluador.md`: los treinta textos con lo que el copiloto tenia
delante y los tres documentos recuperados completos, que es lo que H2, H3 y H5
necesitan para poder calificarse.

**A cada persona se le entregan dos archivos y nada mas**: ese paquete y su hoja,
`hoja_josue.csv` o `hoja_christian.csv`. No se entrega `entradas_redaccion.jsonl`
por separado, que ya va dentro del paquete y formateado. Y no se entrega
`muestra.csv`, que es la clave.
