"""
Check the FORM of the thirty rubric texts, and nothing else.

The gate the drafting step in results/rubrica_humana/redaccion.md runs before the
texts reach the raters. It checks:

  - all thirty files exist, one per drawn episode
  - each is the declared shape: one `# Texto NN` heading and one paragraph
  - six sentences or fewer, and no bullets, which prompts/razona.txt fixes
  - no long dashes, which is a rule of this project
  - nothing else in the file: no notes, no input JSON, no self-assessment

It does NOT check whether the citation exists, whether the cited document says
what the text claims, or whether anything was invented. Those are items H2, H3
and H5, and PROTOCOLO.md, "What a script is allowed to check", says why a script
must leave them alone.

Exit code is non-zero if any text fails, so the drafting session can loop on it.
"""
import os
import re
import sys
import json

BASE = os.path.dirname(os.path.abspath(__file__))
if not os.path.isfile(os.path.join(BASE, "requirements.txt")):
    BASE = os.path.dirname(BASE)      # the scripts live in code/, the project one level up
OUT = os.path.join(BASE, "results", "rubrica_humana")
TEXTOS = os.path.join(OUT, "textos")
ENTRADAS = os.path.join(OUT, "entradas_redaccion.jsonl")

MAX_FRASES = 6                        # prompts/razona.txt: "un maximo de seis frases"
BULLET, MIDDOT = chr(0x2022), chr(0x00b7)
EM, EN = chr(0x2014), chr(0x2013)
VINETA = re.compile(r"^\s*(?:[-*%s%s]|\d+[.)])\s+" % (BULLET, MIDDOT), re.M)
LARGO = re.compile("[%s%s]" % (EM, EN))
# a sentence ends at . ! ? followed by space or end of string. Abbreviations are
# not an issue here: the corpus writes IDV(1), xmeas_7 and plain prose.
FIN = re.compile(r"[.!?](?:\s|$)")


def frases(p):
    return len(FIN.findall(p.strip()))


def revisa(n, raw):
    """Every way this one file can be wrong, as a list of messages."""
    mal = []
    lineas = [l.rstrip() for l in raw.strip().splitlines()]
    if not lineas:
        return ["esta vacio"]

    esperado = "# Texto %02d" % n
    if lineas[0].strip() != esperado:
        mal.append("la primera linea deberia ser %r y es %r" % (esperado, lineas[0].strip()))

    cuerpo = [l for l in lineas[1:] if l.strip()]
    if not cuerpo:
        mal.append("no tiene texto debajo del encabezado")
        return mal
    if len(cuerpo) > 1:
        mal.append("son %d parrafos y debe ser uno solo" % len(cuerpo))
    for l in cuerpo:
        if l.lstrip().startswith("#"):
            mal.append("lleva un encabezado de mas: %r" % l.strip()[:40])

    p = " ".join(cuerpo)
    n_fr = frases(p)
    if n_fr > MAX_FRASES:
        mal.append("tiene %d frases y el maximo es %d" % (n_fr, MAX_FRASES))
    if n_fr == 0:
        mal.append("ninguna frase termina en punto")
    if VINETA.search(raw):
        mal.append("lleva vinetas, y prompts/razona.txt las prohibe")
    if LARGO.search(raw):
        mal.append("lleva guion largo; en este proyecto se usa guion corto o dos puntos")
    return mal


def main():
    if not os.path.isfile(ENTRADAS):
        print("ABORT - falta %s: corre primero code/22_muestra_rubrica.py" % ENTRADAS)
        return 1
    with open(ENTRADAS, encoding="utf-8") as fh:
        numeros = sorted(json.loads(l)["texto"] for l in fh if l.strip())

    if not os.path.isdir(TEXTOS):
        print("ABORT - falta la carpeta %s" % TEXTOS)
        print("   el encargo esta en results/rubrica_humana/redaccion.md")
        return 1

    faltan, fallan, ok = [], [], 0
    for n in numeros:
        p = os.path.join(TEXTOS, "texto_%02d.md" % n)
        if not os.path.isfile(p):
            faltan.append(n)
            continue
        mal = revisa(n, open(p, encoding="utf-8").read())
        if mal:
            fallan.append((n, mal))
        else:
            ok += 1

    print("textos esperados: %d   escritos: %d   en forma: %d"
          % (len(numeros), len(numeros) - len(faltan), ok))
    if faltan:
        print("\nfaltan %d:" % len(faltan))
        print("   " + ", ".join("texto_%02d.md" % n for n in faltan))
    for n, mal in fallan:
        print("\n[!] texto_%02d.md" % n)
        for m in mal:
            print("    - " + m)

    if faltan or fallan:
        print("\nSe revisa solo la forma. El contenido lo califican las dos personas.")
        return 1
    print("\nLos %d estan en forma. El contenido no se revisa aqui, a proposito:" % ok)
    print("si la cita existe, si el documento dice lo que el texto le atribuye y")
    print("si hay algo inventado es H2, H3 y H5, y eso lo califican las personas.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
