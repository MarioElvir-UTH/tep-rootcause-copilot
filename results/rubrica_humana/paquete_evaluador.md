# Rubrica humana: los treinta textos

Cada texto es una recomendacion que el copiloto le pondria enfrente a un operador
de planta durante un episodio de alarmas. Debajo de cada uno esta lo que el
copiloto tenia delante cuando lo produjo, y los tres documentos que recupero.

**Se califica 1 para si, 0 para no, en la hoja aparte. No dejes nada en blanco.**


- **H1.** Da una causa y dos alternativas, en ese orden, en seis frases o menos.
- **H2.** El documento citado existe y dice lo que el texto le atribuye.
- **H3.** Donde el clasificador y la recuperacion no coinciden, el texto lo declara en vez de esconderlo.
- **H4.** Actuarias con esto a las tres de la manana sin hacer otra pregunta.
- **H5.** El texto afirma algo que la evidencia recuperada no sostiene. La evidencia recuperada son los tres documentos de abajo, no solo el citado.  *(invertido: aqui el si es la respuesta mala)*

Ninguno de los cinco pregunta si el diagnostico fue correcto. Eso ya esta medido
aparte. Lo que se califica aqui es el texto.

No abras `results/rubrica_humana/muestra.csv`: lleva la respuesta de cada
episodio. Califica los treinta antes de mirarlo, y no compares tu hoja con la de
la otra persona: el desacuerdo entre ustedes es un resultado que se reporta, no
un problema que resolver.

---


## Texto 01

El episodio no registra variables en alarma, de modo que no hay alarmas observadas sobre las que apoyar la lectura. La hipotesis mas probable del clasificador es operacion normal y las dos alternativas son IDV(20) y despues IDV(18), ambas documentadas en el corpus como perturbaciones desconocidas, sin causa ni variables atribuidas. El documento recuperado no coincide con esa hipotesis: es IDV(7), perdida de presion en el cabezal de C con disponibilidad reducida en la corriente 4, que el corpus asocia a xmeas_4 y xmv_4, ninguna de las cuales esta aqui en alarma. Los otros dos documentos recuperados son IDV(5) e IDV(12), con puntajes proximos al de IDV(7). Sin alarmas y con esa discrepancia entre clasificador y documento, el copiloto no se compromete con una recomendacion y entrega el episodio a la persona a cargo. La decision final es del operador.

<details>
<summary>Lo que el copiloto tenia delante</summary>

- variables en alarma: **0**, tasa 0.0000 de la ventana
- primeras alarmas: ninguna
- raiz por cronologia: ninguna   |   raiz por conocimiento: ninguna
- hipotesis del clasificador: Operacion normal (0.182), IDV(20) (0.173), IDV(18) (0.137)
- documentos recuperados: IDV(7) (0.0749), IDV(5) (0.0687), IDV(12) (0.0658)
- **documento citado: IDV(7)**
- clasificador y documento: **NO coinciden**
- accion del copiloto: **defer**

**Los tres documentos recuperados, completos:**

- **IDV(7)** (clase 7, escalon)
  - Perdida de presion en el cabezal de C, con disponibilidad reducida en la corriente 4.
  - sintomas: Caida de presion que limita la disponibilidad de la alimentacion combinada A y C.
  - variables documentadas: xmeas_4, xmv_4
- **IDV(5)** (clase 5, escalon)
  - Escalon en la temperatura de entrada del agua de enfriamiento del condensador.
  - sintomas: Cambio brusco en el circuito de enfriamiento del condensador, que se refleja en el separador.
  - variables documentadas: xmeas_22, xmv_11
- **IDV(12)** (clase 12, variacion aleatoria)
  - Variacion aleatoria en la temperatura de entrada del agua de enfriamiento del condensador.
  - sintomas: Fluctuacion irregular en el circuito de enfriamiento del condensador, reflejada en el separador.
  - variables documentadas: xmeas_22, xmv_11

</details>


## Texto 02

El episodio registra 5 variables en alarma, con una tasa de 0,10 en la ventana, y las primeras en aparecer son xmv_5, xmeas_21 y xmeas_5. La hipotesis mas probable del clasificador es IDV(19) y las dos alternativas son IDV(16) y despues IDV(7). El documento recuperado no coincide con esa hipotesis: es IDV(20), y tanto IDV(20) como IDV(19) e IDV(16) estan documentados en el corpus como perturbaciones desconocidas, sin causa ni variables afectadas, de modo que aqui no se les atribuye ninguna. Los otros dos documentos recuperados son IDV(5) e IDV(7), con puntajes menores que el de IDV(20). Con la discrepancia entre clasificador y documento, y sin causa documentada que sostener, el copiloto no se compromete con una recomendacion y entrega el episodio a la persona a cargo. La decision final es del operador.

<details>
<summary>Lo que el copiloto tenia delante</summary>

- variables en alarma: **5**, tasa 0.0962 de la ventana
- primeras alarmas: xmv_5, xmeas_21, xmeas_5
- raiz por cronologia: xmv_5   |   raiz por conocimiento: xmeas_21
- hipotesis del clasificador: IDV(19) (1.000), IDV(16) (0.000), IDV(7) (0.000)
- documentos recuperados: IDV(20) (0.0929), IDV(5) (0.0662), IDV(7) (0.0630)
- **documento citado: IDV(20)**
- clasificador y documento: **NO coinciden**
- accion del copiloto: **defer**

**Los tres documentos recuperados, completos:**

- **IDV(20)** (clase 20, desconocida)
  - La fuente original documenta esta perturbacion como desconocida. No se le atribuye causa ni variables afectadas.
  - sintomas: No documentados en la fuente.
  - variables documentadas: ninguna
- **IDV(5)** (clase 5, escalon)
  - Escalon en la temperatura de entrada del agua de enfriamiento del condensador.
  - sintomas: Cambio brusco en el circuito de enfriamiento del condensador, que se refleja en el separador.
  - variables documentadas: xmeas_22, xmv_11
- **IDV(7)** (clase 7, escalon)
  - Perdida de presion en el cabezal de C, con disponibilidad reducida en la corriente 4.
  - sintomas: Caida de presion que limita la disponibilidad de la alimentacion combinada A y C.
  - variables documentadas: xmeas_4, xmv_4

</details>


## Texto 03

El copiloto reporta este episodio como avalancha de alarmas: 10 variables en alarma, con una tasa de 0,19 en la ventana, y xmeas_23, xmeas_1 y xmv_3 como primeras en aparecer. La hipotesis mas probable del clasificador es operacion normal y las dos alternativas son IDV(18), documentada en el corpus como desconocida, y despues IDV(10). El documento recuperado no coincide con esa hipotesis: es IDV(1), escalon en la relacion de alimentacion A/C de la corriente 4, que el corpus asocia a xmeas_4 y xmv_4, ninguna de las cuales figura entre las primeras alarmas. Las que si figuran, xmeas_1 y xmv_3, son las variables que el corpus documenta para IDV(6), perdida de alimentacion de A en la corriente 1, el segundo documento recuperado. Por la carga de alarmas y por esa discrepancia, lo que se reporta es la avalancha de alarmas y no una recomendacion de causa raiz. La decision final es del operador.

<details>
<summary>Lo que el copiloto tenia delante</summary>

- variables en alarma: **10**, tasa 0.1923 de la ventana
- primeras alarmas: xmeas_23, xmeas_1, xmv_3
- raiz por cronologia: xmeas_23   |   raiz por conocimiento: xmv_11
- hipotesis del clasificador: Operacion normal (0.179), IDV(18) (0.165), IDV(10) (0.126)
- documentos recuperados: IDV(1) (0.0677), IDV(6) (0.0578), IDV(2) (0.0523)
- **documento citado: IDV(1)**
- clasificador y documento: **NO coinciden**
- accion del copiloto: **alert**

**Los tres documentos recuperados, completos:**

- **IDV(1)** (clase 1, escalon)
  - Escalon en la relacion de alimentacion A/C de la corriente 4, manteniendo constante la composicion de B.
  - sintomas: Cambio sostenido en la alimentacion combinada de A y C. Al alterarse la proporcion entre reactivos, el lazo de control reacciona sobre el flujo de esa corriente.
  - variables documentadas: xmeas_4, xmv_4
- **IDV(6)** (clase 6, escalon)
  - Perdida de alimentacion de A, corriente 1.
  - sintomas: Caida marcada y sostenida de la alimentacion de A. Es una de las perturbaciones de efecto mas visible en el proceso.
  - variables documentadas: xmeas_1, xmv_3
- **IDV(2)** (clase 2, escalon)
  - Escalon en la composicion de B de la corriente 4, manteniendo constante la relacion A/C.
  - sintomas: Cambio sostenido en la composicion de la corriente de alimentacion combinada. El inerte B altera el balance del reciclo.
  - variables documentadas: xmeas_4, xmv_4

</details>


## Texto 04

El episodio registra 16 variables en alarma, con una tasa de 0,31 en la ventana, y las primeras en aparecer son xmeas_16, xmeas_20 y xmeas_29. La causa raiz mas probable es IDV(1), hipotesis en la que coinciden el clasificador y el documento recuperado, que la describe como escalon en la relacion de alimentacion A/C de la corriente 4, con la composicion de B constante. Ese documento asocia la perturbacion a xmeas_4 y xmv_4, y ninguna de las dos esta entre las primeras alarmas; la raiz por conocimiento es xmeas_22, que el corpus documenta para IDV(12), la segunda hipotesis del clasificador. Las dos alternativas son IDV(12) y despues IDV(8), y ninguna de las dos figura entre los documentos recuperados. Los otros dos documentos recuperados son IDV(6) e IDV(13), con puntajes menores que el de IDV(1). La decision final es del operador.

<details>
<summary>Lo que el copiloto tenia delante</summary>

- variables en alarma: **16**, tasa 0.3077 de la ventana
- primeras alarmas: xmeas_16, xmeas_20, xmeas_29
- raiz por cronologia: xmeas_16   |   raiz por conocimiento: xmeas_22
- hipotesis del clasificador: IDV(1) (0.998), IDV(12) (0.001), IDV(8) (0.001)
- documentos recuperados: IDV(1) (0.1024), IDV(6) (0.0690), IDV(13) (0.0681)
- **documento citado: IDV(1)**
- clasificador y documento: **coinciden**
- accion del copiloto: **generate**

**Los tres documentos recuperados, completos:**

- **IDV(1)** (clase 1, escalon)
  - Escalon en la relacion de alimentacion A/C de la corriente 4, manteniendo constante la composicion de B.
  - sintomas: Cambio sostenido en la alimentacion combinada de A y C. Al alterarse la proporcion entre reactivos, el lazo de control reacciona sobre el flujo de esa corriente.
  - variables documentadas: xmeas_4, xmv_4
- **IDV(6)** (clase 6, escalon)
  - Perdida de alimentacion de A, corriente 1.
  - sintomas: Caida marcada y sostenida de la alimentacion de A. Es una de las perturbaciones de efecto mas visible en el proceso.
  - variables documentadas: xmeas_1, xmv_3
- **IDV(13)** (clase 13, deriva lenta)
  - Deriva lenta en la cinetica de reaccion.
  - sintomas: Cambio gradual y progresivo en el comportamiento del reactor. Al ser lenta, en una ventana temprana apenas se separa de la operacion normal.
  - variables documentadas: xmeas_7, xmeas_9

</details>


## Texto 05

El episodio registra 25 variables en alarma, con una tasa de 0,48 en la ventana, y las primeras en aparecer son xmeas_20, xmeas_9 y xmeas_21. La causa raiz mas probable es IDV(1), hipotesis en la que coinciden el clasificador y el documento recuperado, que la describe como escalon en la relacion de alimentacion A/C de la corriente 4, con la composicion de B constante. Ese documento asocia la perturbacion a xmeas_4 y xmv_4: ninguna de las dos esta entre las primeras alarmas, y la raiz que senala el conocimiento es xmeas_21, que tampoco figura entre las variables documentadas para IDV(1). Las dos alternativas son IDV(8) y despues IDV(5), y ninguna aparece entre los documentos recuperados. Los otros dos documentos recuperados son IDV(13) e IDV(6), con puntajes menores que el de IDV(1). La decision final es del operador.

<details>
<summary>Lo que el copiloto tenia delante</summary>

- variables en alarma: **25**, tasa 0.4808 de la ventana
- primeras alarmas: xmeas_20, xmeas_9, xmeas_21
- raiz por cronologia: xmeas_20   |   raiz por conocimiento: xmeas_21
- hipotesis del clasificador: IDV(1) (1.000), IDV(8) (0.000), IDV(5) (0.000)
- documentos recuperados: IDV(1) (0.1182), IDV(13) (0.0676), IDV(6) (0.0668)
- **documento citado: IDV(1)**
- clasificador y documento: **coinciden**
- accion del copiloto: **generate**

**Los tres documentos recuperados, completos:**

- **IDV(1)** (clase 1, escalon)
  - Escalon en la relacion de alimentacion A/C de la corriente 4, manteniendo constante la composicion de B.
  - sintomas: Cambio sostenido en la alimentacion combinada de A y C. Al alterarse la proporcion entre reactivos, el lazo de control reacciona sobre el flujo de esa corriente.
  - variables documentadas: xmeas_4, xmv_4
- **IDV(13)** (clase 13, deriva lenta)
  - Deriva lenta en la cinetica de reaccion.
  - sintomas: Cambio gradual y progresivo en el comportamiento del reactor. Al ser lenta, en una ventana temprana apenas se separa de la operacion normal.
  - variables documentadas: xmeas_7, xmeas_9
- **IDV(6)** (clase 6, escalon)
  - Perdida de alimentacion de A, corriente 1.
  - sintomas: Caida marcada y sostenida de la alimentacion de A. Es una de las perturbaciones de efecto mas visible en el proceso.
  - variables documentadas: xmeas_1, xmv_3

</details>


## Texto 06

El episodio registra 22 variables en alarma, con una tasa de 0,42 en la ventana, y las primeras en aparecer son xmeas_11, xmeas_22 y xmeas_18. La causa raiz mas probable es IDV(5), hipotesis en la que coinciden el clasificador y el documento recuperado, que la describe como escalon en la temperatura de entrada del agua de enfriamiento del condensador, reflejado en el separador. La variable xmeas_22 esta entre las primeras alarmas y es una de las que ese documento asocia a la perturbacion, junto con xmv_11; la raiz por conocimiento del episodio es xmeas_4, que no esta entre esas dos. Las dos alternativas son IDV(12) y despues IDV(6), perdida de alimentacion de A en la corriente 1 segun el tercer documento recuperado. El segundo documento recuperado es IDV(7), perdida de presion en el cabezal de C, que no esta entre las tres hipotesis del clasificador. La decision final es del operador.

<details>
<summary>Lo que el copiloto tenia delante</summary>

- variables en alarma: **22**, tasa 0.4231 de la ventana
- primeras alarmas: xmeas_11, xmeas_22, xmeas_18
- raiz por cronologia: xmeas_11   |   raiz por conocimiento: xmeas_4
- hipotesis del clasificador: IDV(5) (1.000), IDV(12) (0.000), IDV(6) (0.000)
- documentos recuperados: IDV(5) (0.1270), IDV(7) (0.0923), IDV(6) (0.0612)
- **documento citado: IDV(5)**
- clasificador y documento: **coinciden**
- accion del copiloto: **generate**

**Los tres documentos recuperados, completos:**

- **IDV(5)** (clase 5, escalon)
  - Escalon en la temperatura de entrada del agua de enfriamiento del condensador.
  - sintomas: Cambio brusco en el circuito de enfriamiento del condensador, que se refleja en el separador.
  - variables documentadas: xmeas_22, xmv_11
- **IDV(7)** (clase 7, escalon)
  - Perdida de presion en el cabezal de C, con disponibilidad reducida en la corriente 4.
  - sintomas: Caida de presion que limita la disponibilidad de la alimentacion combinada A y C.
  - variables documentadas: xmeas_4, xmv_4
- **IDV(6)** (clase 6, escalon)
  - Perdida de alimentacion de A, corriente 1.
  - sintomas: Caida marcada y sostenida de la alimentacion de A. Es una de las perturbaciones de efecto mas visible en el proceso.
  - variables documentadas: xmeas_1, xmv_3

</details>


## Texto 07

El episodio registra 8 variables en alarma, con una tasa de 0,15 en la ventana, y las primeras en aparecer son xmeas_8, xmeas_16 y xmeas_7. La hipotesis mas probable del clasificador es operacion normal y las dos alternativas son IDV(18) y despues IDV(20), ambas documentadas en el corpus como desconocidas, sin causa ni variables atribuidas. El documento recuperado no coincide con esa hipotesis: es IDV(5), escalon en la temperatura de entrada del agua de enfriamiento del condensador, que el corpus asocia a xmeas_22 y xmv_11, y xmv_11 es la raiz que senala el conocimiento en este episodio. Los otros dos documentos recuperados son IDV(7), perdida de presion en el cabezal de C, e IDV(19), registrado tambien como perturbacion desconocida. Con esa discrepancia entre clasificador y documento, el copiloto no se compromete con una recomendacion y entrega el episodio a la persona a cargo. La decision final es del operador.

<details>
<summary>Lo que el copiloto tenia delante</summary>

- variables en alarma: **8**, tasa 0.1538 de la ventana
- primeras alarmas: xmeas_8, xmeas_16, xmeas_7
- raiz por cronologia: xmeas_8   |   raiz por conocimiento: xmv_11
- hipotesis del clasificador: Operacion normal (0.196), IDV(18) (0.158), IDV(20) (0.124)
- documentos recuperados: IDV(5) (0.0971), IDV(7) (0.0902), IDV(19) (0.0698)
- **documento citado: IDV(5)**
- clasificador y documento: **NO coinciden**
- accion del copiloto: **defer**

**Los tres documentos recuperados, completos:**

- **IDV(5)** (clase 5, escalon)
  - Escalon en la temperatura de entrada del agua de enfriamiento del condensador.
  - sintomas: Cambio brusco en el circuito de enfriamiento del condensador, que se refleja en el separador.
  - variables documentadas: xmeas_22, xmv_11
- **IDV(7)** (clase 7, escalon)
  - Perdida de presion en el cabezal de C, con disponibilidad reducida en la corriente 4.
  - sintomas: Caida de presion que limita la disponibilidad de la alimentacion combinada A y C.
  - variables documentadas: xmeas_4, xmv_4
- **IDV(19)** (clase 19, desconocida)
  - La fuente original documenta esta perturbacion como desconocida. No se le atribuye causa ni variables afectadas.
  - sintomas: No documentados en la fuente.
  - variables documentadas: ninguna

</details>


## Texto 08

El episodio registra 19 variables en alarma, con una tasa de 0,37 en la ventana, y las primeras en aparecer son xmv_5, xmeas_20 y xmeas_16. La causa raiz mas probable es IDV(1), hipotesis en la que coinciden el clasificador y el documento recuperado, que la describe como escalon en la relacion de alimentacion A/C de la corriente 4, con la composicion de B constante. Ese documento asocia la perturbacion a xmeas_4 y xmv_4: ninguna de las dos esta entre las primeras alarmas, aunque la raiz por conocimiento del episodio apunta a xmeas_4. Las dos alternativas son IDV(8) y despues IDV(14), y ninguna de ellas figura entre los documentos recuperados. Los otros dos documentos recuperados son IDV(13) e IDV(6), con puntajes menores que el de IDV(1). La decision final es del operador.

<details>
<summary>Lo que el copiloto tenia delante</summary>

- variables en alarma: **19**, tasa 0.3654 de la ventana
- primeras alarmas: xmv_5, xmeas_20, xmeas_16
- raiz por cronologia: xmv_5   |   raiz por conocimiento: xmeas_4
- hipotesis del clasificador: IDV(1) (1.000), IDV(8) (0.000), IDV(14) (0.000)
- documentos recuperados: IDV(1) (0.1175), IDV(13) (0.0683), IDV(6) (0.0657)
- **documento citado: IDV(1)**
- clasificador y documento: **coinciden**
- accion del copiloto: **generate**

**Los tres documentos recuperados, completos:**

- **IDV(1)** (clase 1, escalon)
  - Escalon en la relacion de alimentacion A/C de la corriente 4, manteniendo constante la composicion de B.
  - sintomas: Cambio sostenido en la alimentacion combinada de A y C. Al alterarse la proporcion entre reactivos, el lazo de control reacciona sobre el flujo de esa corriente.
  - variables documentadas: xmeas_4, xmv_4
- **IDV(13)** (clase 13, deriva lenta)
  - Deriva lenta en la cinetica de reaccion.
  - sintomas: Cambio gradual y progresivo en el comportamiento del reactor. Al ser lenta, en una ventana temprana apenas se separa de la operacion normal.
  - variables documentadas: xmeas_7, xmeas_9
- **IDV(6)** (clase 6, escalon)
  - Perdida de alimentacion de A, corriente 1.
  - sintomas: Caida marcada y sostenida de la alimentacion de A. Es una de las perturbaciones de efecto mas visible en el proceso.
  - variables documentadas: xmeas_1, xmv_3

</details>


## Texto 09

El episodio registra 3 variables en alarma, con una tasa de 0,06 en la ventana, y las primeras en aparecer son xmv_10, xmeas_9 y xmeas_21. La hipotesis mas probable del clasificador es IDV(14) y las dos alternativas son IDV(12) y despues IDV(7). El documento recuperado no coincide con esa hipotesis: es IDV(17), que el corpus documenta como perturbacion desconocida, sin causa ni variables afectadas, y por eso aqui no se le atribuye ninguna. Los otros dos documentos recuperados son IDV(3), escalon en la temperatura de alimentacion de D en la corriente 2, e IDV(4), escalon en la temperatura de entrada del agua de enfriamiento del reactor, que el corpus asocia a xmeas_21 y xmv_10, ambas entre las primeras alarmas de este episodio. Ante la discrepancia entre el clasificador y el documento recuperado, el copiloto no se compromete con una recomendacion y entrega el episodio a la persona a cargo. La decision final es del operador.

<details>
<summary>Lo que el copiloto tenia delante</summary>

- variables en alarma: **3**, tasa 0.0577 de la ventana
- primeras alarmas: xmv_10, xmeas_9, xmeas_21
- raiz por cronologia: xmv_10   |   raiz por conocimiento: xmeas_21
- hipotesis del clasificador: IDV(14) (1.000), IDV(12) (0.000), IDV(7) (0.000)
- documentos recuperados: IDV(17) (0.1112), IDV(3) (0.0859), IDV(4) (0.0666)
- **documento citado: IDV(17)**
- clasificador y documento: **NO coinciden**
- accion del copiloto: **defer**

**Los tres documentos recuperados, completos:**

- **IDV(17)** (clase 17, desconocida)
  - La fuente original documenta esta perturbacion como desconocida. No se le atribuye causa ni variables afectadas.
  - sintomas: No documentados en la fuente.
  - variables documentadas: ninguna
- **IDV(3)** (clase 3, escalon)
  - Escalon en la temperatura de alimentacion de D, corriente 2.
  - sintomas: Cambio sostenido en las condiciones de la alimentacion de D. Es una perturbacion de baja magnitud, historicamente dificil de distinguir de la operacion normal.
  - variables documentadas: xmeas_2, xmv_1
- **IDV(4)** (clase 4, escalon)
  - Escalon en la temperatura de entrada del agua de enfriamiento del reactor.
  - sintomas: Cambio brusco en el circuito de enfriamiento del reactor. El control compensa actuando sobre el flujo de agua de enfriamiento.
  - variables documentadas: xmeas_21, xmv_10

</details>


## Texto 10

El episodio registra 6 variables en alarma, con una tasa de 0,12 en la ventana, y las primeras en aparecer son xmeas_16, xmeas_7 y xmeas_13. La causa raiz mas probable es IDV(8), hipotesis en la que coinciden el clasificador y el documento recuperado, que la describe como variacion aleatoria en la composicion de A, B y C de la corriente 4, sin un escalon claro. Ese documento asocia la perturbacion a xmeas_4 y xmv_4, y ninguna de las dos figura entre las primeras alarmas; la raiz por conocimiento es xmeas_7, que el corpus documenta para IDV(13), el tercer documento recuperado. Las dos alternativas son IDV(2) y despues IDV(13), deriva lenta en la cinetica de reaccion. Los tres documentos recuperados quedaron con puntajes muy proximos entre si. La decision final es del operador.

<details>
<summary>Lo que el copiloto tenia delante</summary>

- variables en alarma: **6**, tasa 0.1154 de la ventana
- primeras alarmas: xmeas_16, xmeas_7, xmeas_13
- raiz por cronologia: xmeas_16   |   raiz por conocimiento: xmeas_7
- hipotesis del clasificador: IDV(8) (0.994), IDV(2) (0.002), IDV(13) (0.002)
- documentos recuperados: IDV(8) (0.0790), IDV(1) (0.0773), IDV(13) (0.0768)
- **documento citado: IDV(8)**
- clasificador y documento: **coinciden**
- accion del copiloto: **generate**

**Los tres documentos recuperados, completos:**

- **IDV(8)** (clase 8, variacion aleatoria)
  - Variacion aleatoria en la composicion de A, B y C de la corriente 4.
  - sintomas: Fluctuacion irregular y sostenida en la composicion de la alimentacion combinada, sin un escalon claro.
  - variables documentadas: xmeas_4, xmv_4
- **IDV(1)** (clase 1, escalon)
  - Escalon en la relacion de alimentacion A/C de la corriente 4, manteniendo constante la composicion de B.
  - sintomas: Cambio sostenido en la alimentacion combinada de A y C. Al alterarse la proporcion entre reactivos, el lazo de control reacciona sobre el flujo de esa corriente.
  - variables documentadas: xmeas_4, xmv_4
- **IDV(13)** (clase 13, deriva lenta)
  - Deriva lenta en la cinetica de reaccion.
  - sintomas: Cambio gradual y progresivo en el comportamiento del reactor. Al ser lenta, en una ventana temprana apenas se separa de la operacion normal.
  - variables documentadas: xmeas_7, xmeas_9

</details>


## Texto 11

El episodio no registra variables en alarma, de modo que la lectura no se apoya en alarmas observadas sino en el clasificador y en el documento recuperado. La causa raiz mas probable es IDV(13), hipotesis en la que coinciden el clasificador y el documento recuperado, que la describe como deriva lenta en la cinetica de reaccion, con un cambio gradual en el comportamiento del reactor que en una ventana temprana apenas se separa de la operacion normal. Ese documento asocia la perturbacion a xmeas_7 y xmeas_9, y ninguna de las dos esta aqui en alarma. Las dos alternativas son IDV(8) y despues IDV(17), que el corpus documenta como perturbacion desconocida: no le atribuye causa ni variables afectadas, y aqui tampoco se le atribuye ninguna. La decision final es del operador.

<details>
<summary>Lo que el copiloto tenia delante</summary>

- variables en alarma: **0**, tasa 0.0000 de la ventana
- primeras alarmas: ninguna
- raiz por cronologia: ninguna   |   raiz por conocimiento: ninguna
- hipotesis del clasificador: IDV(13) (0.512), IDV(8) (0.215), IDV(17) (0.204)
- documentos recuperados: IDV(13) (0.0610), IDV(3) (0.0598), IDV(17) (0.0559)
- **documento citado: IDV(13)**
- clasificador y documento: **coinciden**
- accion del copiloto: **generate**

**Los tres documentos recuperados, completos:**

- **IDV(13)** (clase 13, deriva lenta)
  - Deriva lenta en la cinetica de reaccion.
  - sintomas: Cambio gradual y progresivo en el comportamiento del reactor. Al ser lenta, en una ventana temprana apenas se separa de la operacion normal.
  - variables documentadas: xmeas_7, xmeas_9
- **IDV(3)** (clase 3, escalon)
  - Escalon en la temperatura de alimentacion de D, corriente 2.
  - sintomas: Cambio sostenido en las condiciones de la alimentacion de D. Es una perturbacion de baja magnitud, historicamente dificil de distinguir de la operacion normal.
  - variables documentadas: xmeas_2, xmv_1
- **IDV(17)** (clase 17, desconocida)
  - La fuente original documenta esta perturbacion como desconocida. No se le atribuye causa ni variables afectadas.
  - sintomas: No documentados en la fuente.
  - variables documentadas: ninguna

</details>


## Texto 12

El episodio registra 22 variables en alarma, con una tasa de 0,42 en la ventana, y las primeras en aparecer son xmeas_22, xmeas_11 y xmeas_21. La causa raiz mas probable es IDV(12), hipotesis en la que coinciden el clasificador y el documento recuperado, que la describe como variacion aleatoria en la temperatura de entrada del agua de enfriamiento del condensador, reflejada en el separador. La primera alarma, xmeas_22, es una de las variables que ese documento asocia a la perturbacion, junto con xmv_11. Las dos alternativas son IDV(14) y despues IDV(6), ninguna de las cuales aparece entre los documentos recuperados. Los otros dos documentos recuperados son IDV(19) e IDV(16), que el corpus registra como perturbaciones desconocidas y a las que no atribuye causa ni variables. La decision final es del operador.

<details>
<summary>Lo que el copiloto tenia delante</summary>

- variables en alarma: **22**, tasa 0.4231 de la ventana
- primeras alarmas: xmeas_22, xmeas_11, xmeas_21
- raiz por cronologia: xmeas_22   |   raiz por conocimiento: xmeas_4
- hipotesis del clasificador: IDV(12) (1.000), IDV(14) (0.000), IDV(6) (0.000)
- documentos recuperados: IDV(12) (0.0884), IDV(19) (0.0732), IDV(16) (0.0681)
- **documento citado: IDV(12)**
- clasificador y documento: **coinciden**
- accion del copiloto: **generate**

**Los tres documentos recuperados, completos:**

- **IDV(12)** (clase 12, variacion aleatoria)
  - Variacion aleatoria en la temperatura de entrada del agua de enfriamiento del condensador.
  - sintomas: Fluctuacion irregular en el circuito de enfriamiento del condensador, reflejada en el separador.
  - variables documentadas: xmeas_22, xmv_11
- **IDV(19)** (clase 19, desconocida)
  - La fuente original documenta esta perturbacion como desconocida. No se le atribuye causa ni variables afectadas.
  - sintomas: No documentados en la fuente.
  - variables documentadas: ninguna
- **IDV(16)** (clase 16, desconocida)
  - La fuente original documenta esta perturbacion como desconocida. No se le atribuye causa ni variables afectadas.
  - sintomas: No documentados en la fuente.
  - variables documentadas: ninguna

</details>


## Texto 13

El episodio registra 12 variables en alarma, con una tasa de 0,23 en la ventana, y las primeras en aparecer son xmeas_16, xmeas_20 y xmeas_29. La causa raiz mas probable es IDV(1), hipotesis en la que coinciden el clasificador y el documento recuperado, que la describe como escalon en la relacion de alimentacion A/C de la corriente 4, con la composicion de B constante. Ese documento asocia la perturbacion a xmeas_4 y xmv_4, y ninguna de las dos esta entre las primeras alarmas; la raiz por conocimiento es xmeas_1, que el corpus documenta para IDV(6). Las dos alternativas son IDV(8) y despues IDV(6), perdida de alimentacion de A en la corriente 1, que es ademas el segundo documento recuperado. El tercer documento recuperado es IDV(15), valvula de agua de enfriamiento del condensador pegada. La decision final es del operador.

<details>
<summary>Lo que el copiloto tenia delante</summary>

- variables en alarma: **12**, tasa 0.2308 de la ventana
- primeras alarmas: xmeas_16, xmeas_20, xmeas_29
- raiz por cronologia: xmeas_16   |   raiz por conocimiento: xmeas_1
- hipotesis del clasificador: IDV(1) (0.983), IDV(8) (0.017), IDV(6) (0.000)
- documentos recuperados: IDV(1) (0.1038), IDV(6) (0.0758), IDV(15) (0.0641)
- **documento citado: IDV(1)**
- clasificador y documento: **coinciden**
- accion del copiloto: **generate**

**Los tres documentos recuperados, completos:**

- **IDV(1)** (clase 1, escalon)
  - Escalon en la relacion de alimentacion A/C de la corriente 4, manteniendo constante la composicion de B.
  - sintomas: Cambio sostenido en la alimentacion combinada de A y C. Al alterarse la proporcion entre reactivos, el lazo de control reacciona sobre el flujo de esa corriente.
  - variables documentadas: xmeas_4, xmv_4
- **IDV(6)** (clase 6, escalon)
  - Perdida de alimentacion de A, corriente 1.
  - sintomas: Caida marcada y sostenida de la alimentacion de A. Es una de las perturbaciones de efecto mas visible en el proceso.
  - variables documentadas: xmeas_1, xmv_3
- **IDV(15)** (clase 15, valvula pegada)
  - Valvula de agua de enfriamiento del condensador pegada.
  - sintomas: La accion de control sobre el enfriamiento del condensador deja de traducirse en cambio de flujo. Historicamente una de las perturbaciones mas dificiles de aislar.
  - variables documentadas: xmv_11, xmeas_22

</details>


## Texto 14

El episodio registra 14 variables en alarma, con una tasa de 0,27 en la ventana, y las primeras en aparecer son xmeas_20, xmeas_21 y xmeas_16. La causa raiz mas probable es IDV(1), hipotesis en la que coinciden el clasificador y el documento recuperado, que la describe como escalon en la relacion de alimentacion A/C de la corriente 4, con la composicion de B constante. Ese documento asocia la perturbacion a xmeas_4 y xmv_4, y ninguna de las dos esta entre las primeras alarmas; la raiz por conocimiento es xmeas_21, que el corpus documenta para IDV(4), la segunda hipotesis del clasificador. Las dos alternativas son IDV(4) y despues IDV(5), y ninguna figura entre los documentos recuperados. Los otros dos documentos recuperados son IDV(8) e IDV(6), con puntajes menores que el de IDV(1). La decision final es del operador.

<details>
<summary>Lo que el copiloto tenia delante</summary>

- variables en alarma: **14**, tasa 0.2692 de la ventana
- primeras alarmas: xmeas_20, xmeas_21, xmeas_16
- raiz por cronologia: xmeas_20   |   raiz por conocimiento: xmeas_21
- hipotesis del clasificador: IDV(1) (0.956), IDV(4) (0.041), IDV(5) (0.003)
- documentos recuperados: IDV(1) (0.1020), IDV(8) (0.0769), IDV(6) (0.0720)
- **documento citado: IDV(1)**
- clasificador y documento: **coinciden**
- accion del copiloto: **generate**

**Los tres documentos recuperados, completos:**

- **IDV(1)** (clase 1, escalon)
  - Escalon en la relacion de alimentacion A/C de la corriente 4, manteniendo constante la composicion de B.
  - sintomas: Cambio sostenido en la alimentacion combinada de A y C. Al alterarse la proporcion entre reactivos, el lazo de control reacciona sobre el flujo de esa corriente.
  - variables documentadas: xmeas_4, xmv_4
- **IDV(8)** (clase 8, variacion aleatoria)
  - Variacion aleatoria en la composicion de A, B y C de la corriente 4.
  - sintomas: Fluctuacion irregular y sostenida en la composicion de la alimentacion combinada, sin un escalon claro.
  - variables documentadas: xmeas_4, xmv_4
- **IDV(6)** (clase 6, escalon)
  - Perdida de alimentacion de A, corriente 1.
  - sintomas: Caida marcada y sostenida de la alimentacion de A. Es una de las perturbaciones de efecto mas visible en el proceso.
  - variables documentadas: xmeas_1, xmv_3

</details>


## Texto 15

El episodio registra 4 variables en alarma, con una tasa de 0,08 en la ventana, y las primeras en aparecer son xmv_10, xmeas_9 y xmeas_23. La causa raiz mas probable es IDV(4), hipotesis en la que coinciden el clasificador y el documento recuperado, que la describe como escalon en la temperatura de entrada del agua de enfriamiento del reactor. La primera alarma del episodio, xmv_10, es una de las variables que ese documento asocia a la perturbacion, junto con xmeas_21, y es tambien la raiz que senala el conocimiento. Las dos alternativas son IDV(11) y despues IDV(5); IDV(11), variacion aleatoria en la temperatura de entrada del agua de enfriamiento del reactor, es el tercer documento recuperado. El segundo documento recuperado es IDV(14), valvula de agua de enfriamiento del reactor pegada, que no aparece entre las tres hipotesis del clasificador. La decision final es del operador.

<details>
<summary>Lo que el copiloto tenia delante</summary>

- variables en alarma: **4**, tasa 0.0769 de la ventana
- primeras alarmas: xmv_10, xmeas_9, xmeas_23
- raiz por cronologia: xmv_10   |   raiz por conocimiento: xmv_10
- hipotesis del clasificador: IDV(4) (1.000), IDV(11) (0.000), IDV(5) (0.000)
- documentos recuperados: IDV(4) (0.1075), IDV(14) (0.0844), IDV(11) (0.0676)
- **documento citado: IDV(4)**
- clasificador y documento: **coinciden**
- accion del copiloto: **generate**

**Los tres documentos recuperados, completos:**

- **IDV(4)** (clase 4, escalon)
  - Escalon en la temperatura de entrada del agua de enfriamiento del reactor.
  - sintomas: Cambio brusco en el circuito de enfriamiento del reactor. El control compensa actuando sobre el flujo de agua de enfriamiento.
  - variables documentadas: xmeas_21, xmv_10
- **IDV(14)** (clase 14, valvula pegada)
  - Valvula de agua de enfriamiento del reactor pegada.
  - sintomas: La accion de control sobre el enfriamiento del reactor deja de traducirse en cambio de flujo. Se observa demanda de control sin respuesta proporcional.
  - variables documentadas: xmv_10, xmeas_21
- **IDV(11)** (clase 11, variacion aleatoria)
  - Variacion aleatoria en la temperatura de entrada del agua de enfriamiento del reactor.
  - sintomas: Fluctuacion irregular en el circuito de enfriamiento del reactor, con respuesta continua del control de enfriamiento.
  - variables documentadas: xmeas_21, xmv_10

</details>


## Texto 16

El episodio registra 2 variables en alarma, con una tasa de 0,04 en la ventana, y las primeras en aparecer son xmeas_35 y xmeas_9. La hipotesis mas probable del clasificador es IDV(3) y las dos alternativas son IDV(9) y despues IDV(17), que el corpus registra como perturbacion desconocida, sin causa ni variables atribuidas. El documento recuperado no coincide con la hipotesis del clasificador: es IDV(16), tambien documentado como desconocido, de modo que la evidencia recuperada no sostiene ninguna causa concreta y aqui no se le atribuye una. Los otros dos documentos recuperados son Operacion normal, que describe el proceso en su modo base sin perturbacion inyectada, e IDV(15), valvula de agua de enfriamiento del condensador pegada. Con esa discrepancia entre clasificador y documento, el copiloto no se compromete con una recomendacion y entrega el episodio a la persona a cargo. La decision final es del operador.

<details>
<summary>Lo que el copiloto tenia delante</summary>

- variables en alarma: **2**, tasa 0.0385 de la ventana
- primeras alarmas: xmeas_35, xmeas_9
- raiz por cronologia: xmeas_35   |   raiz por conocimiento: xmeas_9
- hipotesis del clasificador: IDV(3) (0.893), IDV(9) (0.030), IDV(17) (0.018)
- documentos recuperados: IDV(16) (0.0582), Operacion normal (0.0572), IDV(15) (0.0555)
- **documento citado: IDV(16)**
- clasificador y documento: **NO coinciden**
- accion del copiloto: **defer**

**Los tres documentos recuperados, completos:**

- **IDV(16)** (clase 16, desconocida)
  - La fuente original documenta esta perturbacion como desconocida. No se le atribuye causa ni variables afectadas.
  - sintomas: No documentados en la fuente.
  - variables documentadas: ninguna
- **Operacion normal** (clase 0, sin falla)
  - El proceso opera en su modo base sin perturbacion inyectada. Las variables se mantienen dentro de sus bandas normales y las desviaciones observadas corresponden al ruido propio de la simulacion.
  - sintomas: Ninguna variable sale de forma sostenida de la banda de operacion normal.
  - variables documentadas: ninguna
- **IDV(15)** (clase 15, valvula pegada)
  - Valvula de agua de enfriamiento del condensador pegada.
  - sintomas: La accion de control sobre el enfriamiento del condensador deja de traducirse en cambio de flujo. Historicamente una de las perturbaciones mas dificiles de aislar.
  - variables documentadas: xmv_11, xmeas_22

</details>


## Texto 17

El episodio registra 3 variables en alarma, con una tasa de 0,06 en la ventana, y las primeras en aparecer son xmv_10, xmeas_9 y xmeas_22. La causa raiz mas probable es IDV(4), hipotesis en la que coinciden el clasificador y el documento recuperado, que la describe como escalon en la temperatura de entrada del agua de enfriamiento del reactor, con el control compensando sobre el flujo de agua de enfriamiento. La primera alarma, xmv_10, es una de las variables que ese documento asocia a la perturbacion, junto con xmeas_21, y es tambien la raiz que senala el conocimiento. Las dos alternativas son IDV(11), variacion aleatoria en el mismo circuito de enfriamiento del reactor segun el segundo documento recuperado, y despues IDV(7). El tercer documento recuperado es IDV(14), valvula de agua de enfriamiento del reactor pegada, que no esta entre las tres hipotesis del clasificador. La decision final es del operador.

<details>
<summary>Lo que el copiloto tenia delante</summary>

- variables en alarma: **3**, tasa 0.0577 de la ventana
- primeras alarmas: xmv_10, xmeas_9, xmeas_22
- raiz por cronologia: xmv_10   |   raiz por conocimiento: xmv_10
- hipotesis del clasificador: IDV(4) (1.000), IDV(11) (0.000), IDV(7) (0.000)
- documentos recuperados: IDV(4) (0.1080), IDV(11) (0.0923), IDV(14) (0.0759)
- **documento citado: IDV(4)**
- clasificador y documento: **coinciden**
- accion del copiloto: **generate**

**Los tres documentos recuperados, completos:**

- **IDV(4)** (clase 4, escalon)
  - Escalon en la temperatura de entrada del agua de enfriamiento del reactor.
  - sintomas: Cambio brusco en el circuito de enfriamiento del reactor. El control compensa actuando sobre el flujo de agua de enfriamiento.
  - variables documentadas: xmeas_21, xmv_10
- **IDV(11)** (clase 11, variacion aleatoria)
  - Variacion aleatoria en la temperatura de entrada del agua de enfriamiento del reactor.
  - sintomas: Fluctuacion irregular en el circuito de enfriamiento del reactor, con respuesta continua del control de enfriamiento.
  - variables documentadas: xmeas_21, xmv_10
- **IDV(14)** (clase 14, valvula pegada)
  - Valvula de agua de enfriamiento del reactor pegada.
  - sintomas: La accion de control sobre el enfriamiento del reactor deja de traducirse en cambio de flujo. Se observa demanda de control sin respuesta proporcional.
  - variables documentadas: xmv_10, xmeas_21

</details>


## Texto 18

El episodio registra 37 variables en alarma, con una tasa de 0,71 en la ventana, y las primeras en aparecer son xmeas_7, xmeas_16 y xmeas_4. La causa raiz mas probable es IDV(7), hipotesis en la que coinciden el clasificador y el documento recuperado, que la describe como perdida de presion en el cabezal de C con disponibilidad reducida en la corriente 4. Ese documento asocia la perturbacion a xmeas_4 y xmv_4, y xmeas_4 aparece entre las primeras alarmas y es ademas la raiz que senala el conocimiento. Las dos alternativas son IDV(5), escalon en la temperatura de entrada del agua de enfriamiento del condensador, y despues IDV(6). El tercer documento recuperado es IDV(16), que el corpus documenta como perturbacion desconocida y al que no atribuye causa ni variables. La decision final es del operador.

<details>
<summary>Lo que el copiloto tenia delante</summary>

- variables en alarma: **37**, tasa 0.7115 de la ventana
- primeras alarmas: xmeas_7, xmeas_16, xmeas_4
- raiz por cronologia: xmeas_7   |   raiz por conocimiento: xmeas_4
- hipotesis del clasificador: IDV(7) (1.000), IDV(5) (0.000), IDV(6) (0.000)
- documentos recuperados: IDV(7) (0.1183), IDV(5) (0.0842), IDV(16) (0.0749)
- **documento citado: IDV(7)**
- clasificador y documento: **coinciden**
- accion del copiloto: **generate**

**Los tres documentos recuperados, completos:**

- **IDV(7)** (clase 7, escalon)
  - Perdida de presion en el cabezal de C, con disponibilidad reducida en la corriente 4.
  - sintomas: Caida de presion que limita la disponibilidad de la alimentacion combinada A y C.
  - variables documentadas: xmeas_4, xmv_4
- **IDV(5)** (clase 5, escalon)
  - Escalon en la temperatura de entrada del agua de enfriamiento del condensador.
  - sintomas: Cambio brusco en el circuito de enfriamiento del condensador, que se refleja en el separador.
  - variables documentadas: xmeas_22, xmv_11
- **IDV(16)** (clase 16, desconocida)
  - La fuente original documenta esta perturbacion como desconocida. No se le atribuye causa ni variables afectadas.
  - sintomas: No documentados en la fuente.
  - variables documentadas: ninguna

</details>


## Texto 19

El episodio registra 11 variables en alarma, con una tasa de 0,21 en la ventana, y las primeras en aparecer son xmeas_9, xmeas_21 y xmeas_30. La causa raiz mas probable es IDV(2), hipotesis en la que coinciden el clasificador y el documento recuperado, que la describe como escalon en la composicion de B de la corriente 4, con la relacion A/C constante y el inerte B alterando el balance del reciclo. Ese documento asocia la perturbacion a xmeas_4 y xmv_4, y ninguna de las dos esta entre las primeras alarmas ni es la raiz que senala el conocimiento, que aqui es xmeas_21. Las dos alternativas son IDV(14) y despues IDV(7), que tampoco figuran entre los documentos recuperados. Los otros dos documentos recuperados son IDV(13) e IDV(1), con puntajes menores que el de IDV(2). La decision final es del operador.

<details>
<summary>Lo que el copiloto tenia delante</summary>

- variables en alarma: **11**, tasa 0.2115 de la ventana
- primeras alarmas: xmeas_9, xmeas_21, xmeas_30
- raiz por cronologia: xmeas_9   |   raiz por conocimiento: xmeas_21
- hipotesis del clasificador: IDV(2) (1.000), IDV(14) (0.000), IDV(7) (0.000)
- documentos recuperados: IDV(2) (0.1179), IDV(13) (0.0671), IDV(1) (0.0656)
- **documento citado: IDV(2)**
- clasificador y documento: **coinciden**
- accion del copiloto: **generate**

**Los tres documentos recuperados, completos:**

- **IDV(2)** (clase 2, escalon)
  - Escalon en la composicion de B de la corriente 4, manteniendo constante la relacion A/C.
  - sintomas: Cambio sostenido en la composicion de la corriente de alimentacion combinada. El inerte B altera el balance del reciclo.
  - variables documentadas: xmeas_4, xmv_4
- **IDV(13)** (clase 13, deriva lenta)
  - Deriva lenta en la cinetica de reaccion.
  - sintomas: Cambio gradual y progresivo en el comportamiento del reactor. Al ser lenta, en una ventana temprana apenas se separa de la operacion normal.
  - variables documentadas: xmeas_7, xmeas_9
- **IDV(1)** (clase 1, escalon)
  - Escalon en la relacion de alimentacion A/C de la corriente 4, manteniendo constante la composicion de B.
  - sintomas: Cambio sostenido en la alimentacion combinada de A y C. Al alterarse la proporcion entre reactivos, el lazo de control reacciona sobre el flujo de esa corriente.
  - variables documentadas: xmeas_4, xmv_4

</details>


## Texto 20

El episodio registra 2 variables en alarma, con una tasa de 0,04 en la ventana, y las primeras en aparecer son xmv_10 y xmeas_9. La hipotesis mas probable del clasificador es IDV(11) y las dos alternativas son IDV(14) y despues IDV(7). El documento recuperado no coincide con esa hipotesis: es Operacion normal, que describe el proceso en su modo base, sin perturbacion inyectada y con las desviaciones atribuidas al ruido propio de la simulacion. Los otros dos documentos recuperados son IDV(11), variacion aleatoria en la temperatura de entrada del agua de enfriamiento del reactor, e IDV(4), y ambos asocian la perturbacion a xmeas_21 y xmv_10, de las cuales xmv_10 es la primera alarma del episodio. Con esa discrepancia entre clasificador y documento sin resolver, el copiloto no se compromete con una recomendacion y entrega el episodio a la persona a cargo. La decision final es del operador.

<details>
<summary>Lo que el copiloto tenia delante</summary>

- variables en alarma: **2**, tasa 0.0385 de la ventana
- primeras alarmas: xmv_10, xmeas_9
- raiz por cronologia: xmv_10   |   raiz por conocimiento: xmv_10
- hipotesis del clasificador: IDV(11) (1.000), IDV(14) (0.000), IDV(7) (0.000)
- documentos recuperados: Operacion normal (0.0921), IDV(11) (0.0689), IDV(4) (0.0597)
- **documento citado: Operacion normal**
- clasificador y documento: **NO coinciden**
- accion del copiloto: **defer**

**Los tres documentos recuperados, completos:**

- **Operacion normal** (clase 0, sin falla)
  - El proceso opera en su modo base sin perturbacion inyectada. Las variables se mantienen dentro de sus bandas normales y las desviaciones observadas corresponden al ruido propio de la simulacion.
  - sintomas: Ninguna variable sale de forma sostenida de la banda de operacion normal.
  - variables documentadas: ninguna
- **IDV(11)** (clase 11, variacion aleatoria)
  - Variacion aleatoria en la temperatura de entrada del agua de enfriamiento del reactor.
  - sintomas: Fluctuacion irregular en el circuito de enfriamiento del reactor, con respuesta continua del control de enfriamiento.
  - variables documentadas: xmeas_21, xmv_10
- **IDV(4)** (clase 4, escalon)
  - Escalon en la temperatura de entrada del agua de enfriamiento del reactor.
  - sintomas: Cambio brusco en el circuito de enfriamiento del reactor. El control compensa actuando sobre el flujo de agua de enfriamiento.
  - variables documentadas: xmeas_21, xmv_10

</details>


## Texto 21

El episodio registra 14 variables en alarma, con una tasa de 0,27 en la ventana, y las primeras en aparecer son xmeas_20, xmv_5 y xmeas_21. La causa raiz mas probable es IDV(1), hipotesis en la que coinciden el clasificador y el documento recuperado, que la describe como escalon en la relacion de alimentacion A/C de la corriente 4, con la composicion de B constante. Ese documento asocia la perturbacion a xmeas_4 y xmv_4, y ninguna de las dos esta entre las primeras alarmas ni es la raiz que senala el conocimiento, que aqui es xmeas_21. Las dos alternativas son IDV(5) y despues IDV(12), que no aparecen entre los documentos recuperados. Los otros dos documentos recuperados son IDV(6) e IDV(20), y este ultimo esta registrado en el corpus como perturbacion desconocida, sin causa ni variables atribuidas. La decision final es del operador.

<details>
<summary>Lo que el copiloto tenia delante</summary>

- variables en alarma: **14**, tasa 0.2692 de la ventana
- primeras alarmas: xmeas_20, xmv_5, xmeas_21
- raiz por cronologia: xmeas_20   |   raiz por conocimiento: xmeas_21
- hipotesis del clasificador: IDV(1) (0.994), IDV(5) (0.005), IDV(12) (0.001)
- documentos recuperados: IDV(1) (0.0921), IDV(6) (0.0824), IDV(20) (0.0671)
- **documento citado: IDV(1)**
- clasificador y documento: **coinciden**
- accion del copiloto: **generate**

**Los tres documentos recuperados, completos:**

- **IDV(1)** (clase 1, escalon)
  - Escalon en la relacion de alimentacion A/C de la corriente 4, manteniendo constante la composicion de B.
  - sintomas: Cambio sostenido en la alimentacion combinada de A y C. Al alterarse la proporcion entre reactivos, el lazo de control reacciona sobre el flujo de esa corriente.
  - variables documentadas: xmeas_4, xmv_4
- **IDV(6)** (clase 6, escalon)
  - Perdida de alimentacion de A, corriente 1.
  - sintomas: Caida marcada y sostenida de la alimentacion de A. Es una de las perturbaciones de efecto mas visible en el proceso.
  - variables documentadas: xmeas_1, xmv_3
- **IDV(20)** (clase 20, desconocida)
  - La fuente original documenta esta perturbacion como desconocida. No se le atribuye causa ni variables afectadas.
  - sintomas: No documentados en la fuente.
  - variables documentadas: ninguna

</details>


## Texto 22

El episodio registra 5 variables en alarma, con una tasa de 0,10 en la ventana, y las primeras en aparecer son xmeas_12, xmv_7 y xmeas_22. La hipotesis mas probable del clasificador es IDV(20), documentada en el corpus como perturbacion desconocida, y las dos alternativas son operacion normal y despues IDV(18), tambien registrada como desconocida. El documento recuperado no coincide con esa hipotesis: es IDV(12), variacion aleatoria en la temperatura de entrada del agua de enfriamiento del condensador, que el corpus asocia a xmeas_22 y xmv_11, y xmeas_22 esta entre las primeras alarmas. Los otros dos documentos recuperados son IDV(5) e IDV(7), con puntajes proximos al de IDV(12). Con esa discrepancia entre clasificador y documento, y con el clasificador repartiendo la probabilidad entre sus tres hipotesis, el copiloto no se compromete con una recomendacion y entrega el episodio a la persona a cargo. La decision final es del operador.

<details>
<summary>Lo que el copiloto tenia delante</summary>

- variables en alarma: **5**, tasa 0.0962 de la ventana
- primeras alarmas: xmeas_12, xmv_7, xmeas_22
- raiz por cronologia: xmeas_12   |   raiz por conocimiento: xmeas_22
- hipotesis del clasificador: IDV(20) (0.166), Operacion normal (0.164), IDV(18) (0.147)
- documentos recuperados: IDV(12) (0.0624), IDV(5) (0.0599), IDV(7) (0.0568)
- **documento citado: IDV(12)**
- clasificador y documento: **NO coinciden**
- accion del copiloto: **defer**

**Los tres documentos recuperados, completos:**

- **IDV(12)** (clase 12, variacion aleatoria)
  - Variacion aleatoria en la temperatura de entrada del agua de enfriamiento del condensador.
  - sintomas: Fluctuacion irregular en el circuito de enfriamiento del condensador, reflejada en el separador.
  - variables documentadas: xmeas_22, xmv_11
- **IDV(5)** (clase 5, escalon)
  - Escalon en la temperatura de entrada del agua de enfriamiento del condensador.
  - sintomas: Cambio brusco en el circuito de enfriamiento del condensador, que se refleja en el separador.
  - variables documentadas: xmeas_22, xmv_11
- **IDV(7)** (clase 7, escalon)
  - Perdida de presion en el cabezal de C, con disponibilidad reducida en la corriente 4.
  - sintomas: Caida de presion que limita la disponibilidad de la alimentacion combinada A y C.
  - variables documentadas: xmeas_4, xmv_4

</details>


## Texto 23

El episodio registra 2 variables en alarma, con una tasa de 0,04 en la ventana, y las primeras en aparecer son xmeas_9 y xmv_10. La hipotesis mas probable del clasificador es IDV(11) y las dos alternativas son IDV(14) y despues IDV(7). El documento recuperado con mayor puntaje no coincide con esa hipotesis: es IDV(4), escalon en la temperatura de entrada del agua de enfriamiento del reactor, mientras que IDV(11), variacion aleatoria en ese mismo circuito, quedo tercero en la recuperacion. Los tres documentos recuperados, IDV(4), IDV(14) e IDV(11), asocian la perturbacion a xmv_10 y xmeas_21, y xmv_10 es la raiz que senala el conocimiento en este episodio. Ante la discrepancia entre clasificador y documento, el copiloto no se compromete con una recomendacion y entrega el episodio a la persona a cargo. La decision final es del operador.

<details>
<summary>Lo que el copiloto tenia delante</summary>

- variables en alarma: **2**, tasa 0.0385 de la ventana
- primeras alarmas: xmeas_9, xmv_10
- raiz por cronologia: xmeas_9   |   raiz por conocimiento: xmv_10
- hipotesis del clasificador: IDV(11) (1.000), IDV(14) (0.000), IDV(7) (0.000)
- documentos recuperados: IDV(4) (0.0891), IDV(14) (0.0726), IDV(11) (0.0651)
- **documento citado: IDV(4)**
- clasificador y documento: **NO coinciden**
- accion del copiloto: **defer**

**Los tres documentos recuperados, completos:**

- **IDV(4)** (clase 4, escalon)
  - Escalon en la temperatura de entrada del agua de enfriamiento del reactor.
  - sintomas: Cambio brusco en el circuito de enfriamiento del reactor. El control compensa actuando sobre el flujo de agua de enfriamiento.
  - variables documentadas: xmeas_21, xmv_10
- **IDV(14)** (clase 14, valvula pegada)
  - Valvula de agua de enfriamiento del reactor pegada.
  - sintomas: La accion de control sobre el enfriamiento del reactor deja de traducirse en cambio de flujo. Se observa demanda de control sin respuesta proporcional.
  - variables documentadas: xmv_10, xmeas_21
- **IDV(11)** (clase 11, variacion aleatoria)
  - Variacion aleatoria en la temperatura de entrada del agua de enfriamiento del reactor.
  - sintomas: Fluctuacion irregular en el circuito de enfriamiento del reactor, con respuesta continua del control de enfriamiento.
  - variables documentadas: xmeas_21, xmv_10

</details>


## Texto 24

El copiloto reporta este episodio como avalancha de alarmas: 10 variables en alarma, con una tasa de 0,19 en la ventana, y xmeas_23, xmeas_1 y xmv_3 como primeras en aparecer. La hipotesis mas probable del clasificador es operacion normal y las dos alternativas son IDV(18), que el corpus registra como desconocida, y despues IDV(9). El documento recuperado no coincide con esa hipotesis: es IDV(1), escalon en la relacion de alimentacion A/C de la corriente 4, que el corpus asocia a xmeas_4 y xmv_4, ninguna de las cuales figura entre las primeras alarmas. El segundo documento recuperado es IDV(6), perdida de alimentacion de A en la corriente 1, cuyas variables documentadas, xmeas_1 y xmv_3, si estan entre las primeras alarmas; el tercero es IDV(10). Por la carga de alarmas y por esa discrepancia, lo que se reporta es la avalancha de alarmas y no una recomendacion de causa raiz. La decision final es del operador.

<details>
<summary>Lo que el copiloto tenia delante</summary>

- variables en alarma: **10**, tasa 0.1923 de la ventana
- primeras alarmas: xmeas_23, xmeas_1, xmv_3
- raiz por cronologia: xmeas_23   |   raiz por conocimiento: xmv_11
- hipotesis del clasificador: Operacion normal (0.176), IDV(18) (0.143), IDV(9) (0.133)
- documentos recuperados: IDV(1) (0.0700), IDV(6) (0.0599), IDV(10) (0.0573)
- **documento citado: IDV(1)**
- clasificador y documento: **NO coinciden**
- accion del copiloto: **alert**

**Los tres documentos recuperados, completos:**

- **IDV(1)** (clase 1, escalon)
  - Escalon en la relacion de alimentacion A/C de la corriente 4, manteniendo constante la composicion de B.
  - sintomas: Cambio sostenido en la alimentacion combinada de A y C. Al alterarse la proporcion entre reactivos, el lazo de control reacciona sobre el flujo de esa corriente.
  - variables documentadas: xmeas_4, xmv_4
- **IDV(6)** (clase 6, escalon)
  - Perdida de alimentacion de A, corriente 1.
  - sintomas: Caida marcada y sostenida de la alimentacion de A. Es una de las perturbaciones de efecto mas visible en el proceso.
  - variables documentadas: xmeas_1, xmv_3
- **IDV(10)** (clase 10, variacion aleatoria)
  - Variacion aleatoria en la temperatura de alimentacion de C, corriente 4.
  - sintomas: Fluctuacion irregular en las condiciones de la alimentacion combinada A y C.
  - variables documentadas: xmeas_4, xmv_4

</details>


## Texto 25

El episodio registra 19 variables en alarma, con una tasa de 0,37 en la ventana, y las primeras en aparecer son xmeas_11, xmeas_22 y xmeas_16. La causa raiz mas probable es IDV(5), hipotesis en la que coinciden el clasificador y el documento recuperado, que la describe como escalon en la temperatura de entrada del agua de enfriamiento del condensador, reflejado en el separador. La variable xmeas_22 esta entre las primeras alarmas y es una de las que ese documento asocia a la perturbacion, junto con xmv_11; la raiz por conocimiento del episodio, en cambio, es xmeas_4, que no figura entre esas dos. Las dos alternativas son IDV(12) y despues IDV(7), perdida de presion en el cabezal de C segun el segundo documento recuperado. El tercer documento recuperado es IDV(16), documentado en el corpus como perturbacion desconocida, sin causa ni variables atribuidas. La decision final es del operador.

<details>
<summary>Lo que el copiloto tenia delante</summary>

- variables en alarma: **19**, tasa 0.3654 de la ventana
- primeras alarmas: xmeas_11, xmeas_22, xmeas_16
- raiz por cronologia: xmeas_11   |   raiz por conocimiento: xmeas_4
- hipotesis del clasificador: IDV(5) (1.000), IDV(12) (0.000), IDV(7) (0.000)
- documentos recuperados: IDV(5) (0.1155), IDV(7) (0.0804), IDV(16) (0.0720)
- **documento citado: IDV(5)**
- clasificador y documento: **coinciden**
- accion del copiloto: **generate**

**Los tres documentos recuperados, completos:**

- **IDV(5)** (clase 5, escalon)
  - Escalon en la temperatura de entrada del agua de enfriamiento del condensador.
  - sintomas: Cambio brusco en el circuito de enfriamiento del condensador, que se refleja en el separador.
  - variables documentadas: xmeas_22, xmv_11
- **IDV(7)** (clase 7, escalon)
  - Perdida de presion en el cabezal de C, con disponibilidad reducida en la corriente 4.
  - sintomas: Caida de presion que limita la disponibilidad de la alimentacion combinada A y C.
  - variables documentadas: xmeas_4, xmv_4
- **IDV(16)** (clase 16, desconocida)
  - La fuente original documenta esta perturbacion como desconocida. No se le atribuye causa ni variables afectadas.
  - sintomas: No documentados en la fuente.
  - variables documentadas: ninguna

</details>


## Texto 26

El episodio registra 4 variables en alarma, con una tasa de 0,08 en la ventana, y las primeras en aparecer son xmv_10, xmeas_9 y xmeas_37. La causa raiz mas probable es IDV(4), hipotesis en la que coinciden el clasificador y el documento recuperado, que la describe como escalon en la temperatura de entrada del agua de enfriamiento del reactor, con el control compensando sobre el flujo de agua de enfriamiento. La primera alarma del episodio, xmv_10, es una de las variables que ese documento asocia a la perturbacion, junto con xmeas_21, y es tambien la raiz que senala el conocimiento. Las dos alternativas son IDV(11), variacion aleatoria en la temperatura de entrada del agua de enfriamiento del reactor segun el segundo documento recuperado, y despues IDV(5). El tercer documento recuperado es IDV(14), valvula de agua de enfriamiento del reactor pegada, que no esta entre las tres hipotesis del clasificador. La decision final es del operador.

<details>
<summary>Lo que el copiloto tenia delante</summary>

- variables en alarma: **4**, tasa 0.0769 de la ventana
- primeras alarmas: xmv_10, xmeas_9, xmeas_37
- raiz por cronologia: xmv_10   |   raiz por conocimiento: xmv_10
- hipotesis del clasificador: IDV(4) (1.000), IDV(11) (0.001), IDV(5) (0.000)
- documentos recuperados: IDV(4) (0.1056), IDV(11) (0.1004), IDV(14) (0.0722)
- **documento citado: IDV(4)**
- clasificador y documento: **coinciden**
- accion del copiloto: **generate**

**Los tres documentos recuperados, completos:**

- **IDV(4)** (clase 4, escalon)
  - Escalon en la temperatura de entrada del agua de enfriamiento del reactor.
  - sintomas: Cambio brusco en el circuito de enfriamiento del reactor. El control compensa actuando sobre el flujo de agua de enfriamiento.
  - variables documentadas: xmeas_21, xmv_10
- **IDV(11)** (clase 11, variacion aleatoria)
  - Variacion aleatoria en la temperatura de entrada del agua de enfriamiento del reactor.
  - sintomas: Fluctuacion irregular en el circuito de enfriamiento del reactor, con respuesta continua del control de enfriamiento.
  - variables documentadas: xmeas_21, xmv_10
- **IDV(14)** (clase 14, valvula pegada)
  - Valvula de agua de enfriamiento del reactor pegada.
  - sintomas: La accion de control sobre el enfriamiento del reactor deja de traducirse en cambio de flujo. Se observa demanda de control sin respuesta proporcional.
  - variables documentadas: xmv_10, xmeas_21

</details>


## Texto 27

El episodio registra 22 variables en alarma, con una tasa de 0,42 en la ventana, y las primeras en aparecer son xmeas_16, xmeas_20 y xmeas_7. La causa raiz mas probable es IDV(1), hipotesis en la que coinciden el clasificador y el documento recuperado, que la describe como escalon en la relacion de alimentacion A/C de la corriente 4, con la composicion de B constante. Ese documento asocia la perturbacion a xmeas_4 y xmv_4, y ninguna de las dos esta entre las primeras alarmas, aunque xmeas_4 es la raiz que senala el conocimiento. Las dos alternativas son IDV(8) y despues IDV(5), que no figuran entre los documentos recuperados. Los otros dos documentos recuperados son IDV(13) e IDV(16), y este ultimo esta documentado en el corpus como perturbacion desconocida, sin causa ni variables atribuidas. La decision final es del operador.

<details>
<summary>Lo que el copiloto tenia delante</summary>

- variables en alarma: **22**, tasa 0.4231 de la ventana
- primeras alarmas: xmeas_16, xmeas_20, xmeas_7
- raiz por cronologia: xmeas_16   |   raiz por conocimiento: xmeas_4
- hipotesis del clasificador: IDV(1) (1.000), IDV(8) (0.000), IDV(5) (0.000)
- documentos recuperados: IDV(1) (0.1076), IDV(13) (0.0593), IDV(16) (0.0592)
- **documento citado: IDV(1)**
- clasificador y documento: **coinciden**
- accion del copiloto: **generate**

**Los tres documentos recuperados, completos:**

- **IDV(1)** (clase 1, escalon)
  - Escalon en la relacion de alimentacion A/C de la corriente 4, manteniendo constante la composicion de B.
  - sintomas: Cambio sostenido en la alimentacion combinada de A y C. Al alterarse la proporcion entre reactivos, el lazo de control reacciona sobre el flujo de esa corriente.
  - variables documentadas: xmeas_4, xmv_4
- **IDV(13)** (clase 13, deriva lenta)
  - Deriva lenta en la cinetica de reaccion.
  - sintomas: Cambio gradual y progresivo en el comportamiento del reactor. Al ser lenta, en una ventana temprana apenas se separa de la operacion normal.
  - variables documentadas: xmeas_7, xmeas_9
- **IDV(16)** (clase 16, desconocida)
  - La fuente original documenta esta perturbacion como desconocida. No se le atribuye causa ni variables afectadas.
  - sintomas: No documentados en la fuente.
  - variables documentadas: ninguna

</details>


## Texto 28

El episodio registra 4 variables en alarma, con una tasa de 0,08 en la ventana, y las primeras en aparecer son xmeas_28, xmv_1 y xmv_5. La hipotesis mas probable es IDV(20), y en ella coinciden el clasificador y el documento recuperado, pero ese documento la registra como perturbacion desconocida: la fuente original no le atribuye causa ni variables afectadas, y aqui no se le atribuye ninguna. Por eso las alarmas observadas no pueden vincularse a variables documentadas para esa clase. Las dos alternativas son IDV(19), que el corpus tambien documenta como desconocida, y despues IDV(8). Los otros dos documentos recuperados son IDV(7) e IDV(5), con puntajes menores que el de IDV(20). La decision final es del operador.

<details>
<summary>Lo que el copiloto tenia delante</summary>

- variables en alarma: **4**, tasa 0.0769 de la ventana
- primeras alarmas: xmeas_28, xmv_1, xmv_5
- raiz por cronologia: xmeas_28   |   raiz por conocimiento: xmv_1
- hipotesis del clasificador: IDV(20) (0.999), IDV(19) (0.001), IDV(8) (0.000)
- documentos recuperados: IDV(20) (0.1001), IDV(7) (0.0582), IDV(5) (0.0573)
- **documento citado: IDV(20)**
- clasificador y documento: **coinciden**
- accion del copiloto: **generate**

**Los tres documentos recuperados, completos:**

- **IDV(20)** (clase 20, desconocida)
  - La fuente original documenta esta perturbacion como desconocida. No se le atribuye causa ni variables afectadas.
  - sintomas: No documentados en la fuente.
  - variables documentadas: ninguna
- **IDV(7)** (clase 7, escalon)
  - Perdida de presion en el cabezal de C, con disponibilidad reducida en la corriente 4.
  - sintomas: Caida de presion que limita la disponibilidad de la alimentacion combinada A y C.
  - variables documentadas: xmeas_4, xmv_4
- **IDV(5)** (clase 5, escalon)
  - Escalon en la temperatura de entrada del agua de enfriamiento del condensador.
  - sintomas: Cambio brusco en el circuito de enfriamiento del condensador, que se refleja en el separador.
  - variables documentadas: xmeas_22, xmv_11

</details>


## Texto 29

El copiloto reporta este episodio como avalancha de alarmas: 14 variables en alarma, con una tasa de 0,27 en la ventana, y xmv_1, xmeas_7 y xmeas_16 como primeras en aparecer. La hipotesis mas probable del clasificador es operacion normal y las dos alternativas son IDV(20) y despues IDV(9), y el corpus documenta IDV(20) como perturbacion desconocida. El documento recuperado no coincide con esa hipotesis: es IDV(7), perdida de presion en el cabezal de C con disponibilidad reducida en la corriente 4, que el corpus asocia a xmeas_4 y xmv_4, ninguna de las cuales esta entre las primeras alarmas. Los otros dos documentos recuperados son IDV(20), sin causa documentada en la fuente, e IDV(5), escalon en la temperatura de entrada del agua de enfriamiento del condensador, ambos con puntajes proximos al de IDV(7). Por la carga de alarmas y por esa discrepancia, lo que se reporta es la avalancha de alarmas y no una recomendacion de causa raiz. La decision final es del operador.

<details>
<summary>Lo que el copiloto tenia delante</summary>

- variables en alarma: **14**, tasa 0.2692 de la ventana
- primeras alarmas: xmv_1, xmeas_7, xmeas_16
- raiz por cronologia: xmv_1   |   raiz por conocimiento: xmeas_21
- hipotesis del clasificador: Operacion normal (0.178), IDV(20) (0.136), IDV(9) (0.133)
- documentos recuperados: IDV(7) (0.1019), IDV(20) (0.0878), IDV(5) (0.0863)
- **documento citado: IDV(7)**
- clasificador y documento: **NO coinciden**
- accion del copiloto: **alert**

**Los tres documentos recuperados, completos:**

- **IDV(7)** (clase 7, escalon)
  - Perdida de presion en el cabezal de C, con disponibilidad reducida en la corriente 4.
  - sintomas: Caida de presion que limita la disponibilidad de la alimentacion combinada A y C.
  - variables documentadas: xmeas_4, xmv_4
- **IDV(20)** (clase 20, desconocida)
  - La fuente original documenta esta perturbacion como desconocida. No se le atribuye causa ni variables afectadas.
  - sintomas: No documentados en la fuente.
  - variables documentadas: ninguna
- **IDV(5)** (clase 5, escalon)
  - Escalon en la temperatura de entrada del agua de enfriamiento del condensador.
  - sintomas: Cambio brusco en el circuito de enfriamiento del condensador, que se refleja en el separador.
  - variables documentadas: xmeas_22, xmv_11

</details>


## Texto 30

El episodio registra 18 variables en alarma, con una tasa de 0,35 en la ventana, y las primeras en aparecer son xmeas_22, xmeas_11 y xmeas_36. La hipotesis mas probable del clasificador es IDV(12) y las dos alternativas son IDV(14) y despues IDV(7). El documento recuperado no coincide con la primera hipotesis: es IDV(14), valvula de agua de enfriamiento del reactor pegada, que el corpus describe como demanda de control sobre el enfriamiento sin respuesta proporcional en el flujo y asocia a xmv_10 y xmeas_21, ninguna de las cuales esta entre las primeras alarmas. Los otros dos documentos recuperados son IDV(19), registrado en el corpus como perturbacion desconocida, e IDV(13), deriva lenta en la cinetica de reaccion. Con esa discrepancia entre clasificador y documento, el copiloto no se compromete con una recomendacion y entrega el episodio a la persona a cargo. La decision final es del operador.

<details>
<summary>Lo que el copiloto tenia delante</summary>

- variables en alarma: **18**, tasa 0.3462 de la ventana
- primeras alarmas: xmeas_22, xmeas_11, xmeas_36
- raiz por cronologia: xmeas_22   |   raiz por conocimiento: xmeas_4
- hipotesis del clasificador: IDV(12) (1.000), IDV(14) (0.000), IDV(7) (0.000)
- documentos recuperados: IDV(14) (0.0758), IDV(19) (0.0726), IDV(13) (0.0707)
- **documento citado: IDV(14)**
- clasificador y documento: **NO coinciden**
- accion del copiloto: **defer**

**Los tres documentos recuperados, completos:**

- **IDV(14)** (clase 14, valvula pegada)
  - Valvula de agua de enfriamiento del reactor pegada.
  - sintomas: La accion de control sobre el enfriamiento del reactor deja de traducirse en cambio de flujo. Se observa demanda de control sin respuesta proporcional.
  - variables documentadas: xmv_10, xmeas_21
- **IDV(19)** (clase 19, desconocida)
  - La fuente original documenta esta perturbacion como desconocida. No se le atribuye causa ni variables afectadas.
  - sintomas: No documentados en la fuente.
  - variables documentadas: ninguna
- **IDV(13)** (clase 13, deriva lenta)
  - Deriva lenta en la cinetica de reaccion.
  - sintomas: Cambio gradual y progresivo en el comportamiento del reactor. Al ser lenta, en una ventana temprana apenas se separa de la operacion normal.
  - variables documentadas: xmeas_7, xmeas_9

</details>
