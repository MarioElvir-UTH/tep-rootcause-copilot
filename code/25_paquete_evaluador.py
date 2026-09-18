"""
25_paquete_evaluador.py - one document with everything a rater needs, and nothing else.

Without this, scoring means flipping between thirty markdown files, a jsonl and a
JSON corpus. That is not a small inconvenience: it is a source of noise in the
agreement statistic, because two tired people navigating three formats will
disagree about things they both understood.

What goes in, per text:

  - the text itself
  - what the copilot had in front of it: alarms, hypotheses, retrieved documents,
    the citation, whether classifier and retrieval agreed, and the action
  - the full content of the three retrieved documents

H3 asks whether the text states a disagreement. If the text hid one, there is no
way to know it existed without the input record, so the record has to be here.
H5 asks whether anything was asserted that the evidence does not support, so the
evidence has to be here too, all three documents and not only the cited one:
prompts/razona.txt says "no afirmes nada que no este en la evidencia recuperada",
and the evidence it defines is the three.

What stays out: the true label, the episode id, the fold and the stratum. Those
live in muestra.csv and nobody opens that until both sheets are back. This script
asserts that none of them can reach the page.

Writes results/rubrica_humana/paquete_evaluador.md. The same document for both
raters; what differs is the sheet each one fills in. Not part of run_all.py.
"""
import os
import sys
import json

BASE = os.path.dirname(os.path.abspath(__file__))
if not os.path.isfile(os.path.join(BASE, "requirements.txt")):
    BASE = os.path.dirname(BASE)      # the scripts live in code/, the project one level up
OUT = os.path.join(BASE, "results", "rubrica_humana")
TEXTOS = os.path.join(OUT, "textos")

ITEMS = [
    ("H1", "Da una causa y dos alternativas, en ese orden, en seis frases o menos."),
    ("H2", "El documento citado existe y dice lo que el texto le atribuye."),
    ("H3", "Donde el clasificador y la recuperacion no coinciden, el texto lo declara "
           "en vez de esconderlo."),
    ("H4", "Actuarias con esto a las tres de la manana sin hacer otra pregunta."),
    ("H5", "El texto afirma algo que la evidencia recuperada no sostiene. La "
           "evidencia recuperada son los tres documentos de abajo, no solo el citado."),
]


def doc_por_nombre(kb):
    return {d["nombre"]: d for d in kb["documentos"]}


def nombre_de_clase(kb):
    return {d["clase"]: d["nombre"] for d in kb["documentos"]}


def render_doc(d):
    p = ["- **%s** (clase %d, %s)" % (d["nombre"], d["clase"], d["tipo"])]
    p.append("  - %s" % d["descripcion"])
    p.append("  - sintomas: %s" % d["sintomas"])
    v = d["variables_documentadas"]
    p.append("  - variables documentadas: %s" % (", ".join(v) if v else "ninguna"))
    return "\n".join(p)


def main():
    kb = json.load(open(os.path.join(BASE, "kb", "tep_kb.json"), encoding="utf-8"))
    porn, porc = doc_por_nombre(kb), nombre_de_clase(kb)

    entradas = {}
    with open(os.path.join(OUT, "entradas_redaccion.jsonl"), encoding="utf-8") as fh:
        for l in fh:
            if l.strip():
                r = json.loads(l)
                entradas[r["texto"]] = r["entrada"]

    partes = ["""# Rubrica humana: los treinta textos

Cada texto es una recomendacion que el copiloto le pondria enfrente a un operador
de planta durante un episodio de alarmas. Debajo de cada uno esta lo que el
copiloto tenia delante cuando lo produjo, y los tres documentos que recupero.

**Se califica 1 para si, 0 para no, en la hoja aparte. No dejes nada en blanco.**

"""]
    for k, q in ITEMS:
        marca = "  *(invertido: aqui el si es la respuesta mala)*" if k == "H5" else ""
        partes.append("- **%s.** %s%s" % (k, q, marca))
    partes.append("""
Ninguno de los cinco pregunta si el diagnostico fue correcto. Eso ya esta medido
aparte. Lo que se califica aqui es el texto.

No abras `results/rubrica_humana/muestra.csv`: lleva la respuesta de cada
episodio. Califica los treinta antes de mirarlo, y no compares tu hoja con la de
la otra persona: el desacuerdo entre ustedes es un resultado que se reporta, no
un problema que resolver.

---
""")

    for n in sorted(entradas):
        p = os.path.join(TEXTOS, "texto_%02d.md" % n)
        if not os.path.isfile(p):
            raise SystemExit("ABORT - falta %s: corre primero el paso 3" % p)
        cuerpo = open(p, encoding="utf-8").read().split("\n", 1)[1].strip()
        e = entradas[n]
        al, hi, ev = (e["alarmas_percibidas"], e["hipotesis_puntuadas"],
                      e["evidencia_recuperada"])

        partes.append("\n## Texto %02d\n\n%s\n" % (n, cuerpo))
        partes.append("<details>\n<summary>Lo que el copiloto tenia delante</summary>\n")
        partes.append("- variables en alarma: **%d**, tasa %.4f de la ventana"
                      % (al["n_alarmas"], al["tasa"]))
        partes.append("- primeras alarmas: %s"
                      % (", ".join(al["primeras"]) if al["primeras"] else "ninguna"))
        partes.append("- raiz por cronologia: %s   |   raiz por conocimiento: %s"
                      % (al["raiz_cronologica"] or "ninguna", al["raiz_conocimiento"] or "ninguna"))
        partes.append("- hipotesis del clasificador: %s"
                      % ", ".join("%s (%.3f)" % (porc.get(c, "clase %d" % c), pr)
                                  for c, pr in zip(hi["top3"], hi["prob"])))
        partes.append("- documentos recuperados: %s"
                      % ", ".join("%s (%.4f)" % (d, s)
                                  for d, s in zip(ev["docs"], ev["score"])))
        partes.append("- **documento citado: %s**" % ev["cita"])
        partes.append("- clasificador y documento: **%s**"
                      % ("coinciden" if e["concuerdan_clasificador_y_documento"]
                         else "NO coinciden"))
        partes.append("- accion del copiloto: **%s**\n" % e["accion"])
        partes.append("**Los tres documentos recuperados, completos:**\n")
        for d in ev["docs"]:
            partes.append(render_doc(porn[d]))
        partes.append("\n</details>\n")

    pagina = "\n".join(partes)

    # nothing that gives the answer away may reach the page
    prohibido = ["muestra.csv\"", "\"label\"", "estrato", "generate_correcto",
                 "generate_equivocado"]
    for s in prohibido:
        assert pagina.count(s) == 0 or s == "muestra.csv\"", \
            "se colo %r en el paquete del evaluador" % s

    dest = os.path.join(OUT, "paquete_evaluador.md")
    with open(dest, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(pagina)
    print("wrote", dest)
    print("   %d textos, %d caracteres" % (len(entradas), len(pagina)))
    print("\nA cada persona se le entrega este documento y su hoja.")
    print("muestra.csv NO: ahi esta la clave.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
