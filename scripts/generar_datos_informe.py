#!/usr/bin/env python3
"""Genera site/datos-informe.json para la web de informes de Plexum (versión 1.2 del pedido).

Elecciones del Mundo, apartado 13: agenda (próximos 60 días) y novedades «elección»
(resultados de los últimos 90 días), sin la Argentina ni EE. UU.
Se toma todo de site/data.json: no se agrega ni se estima nada.
Correr cada vez que se actualiza data.json, antes de publicar.
"""
import json, re, unicodedata
from datetime import datetime, timedelta, timezone
from pathlib import Path

_R = Path(__file__).resolve().parent.parent
BASE = _R / "site" if (_R / "site" / "data.json").exists() else _R
URL = "https://francomartinlopez.github.io/eleccionesglobales/"
EXCLUIR = {"032", "840"}  # Argentina y Estados Unidos
TZ = timezone(timedelta(hours=-3))
REL = {"a": "aliada", "m": "ambigua", "e": "confrontada"}
TIPO = {"presidencial": "Elección presidencial", "legislativa": "Elección legislativa",
        "general": "Elecciones generales", "referendo": "Referendo", "otra": "Elección"}


def slug(t):
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")


def alcance(pais):
    return {"nivel": "país", "provincia": "", "localidad": "", "pais": pais}


def palabras(t, n=60):
    w = t.split()
    return t if len(w) <= n else " ".join(w[:n]).rstrip(",;") + "…"


def main():
    d = json.loads((BASE / "data.json").read_text(encoding="utf-8"))
    paises = d["paises"]
    ahora = datetime.now(TZ)
    hoy = ahora.date().isoformat()
    hasta = (ahora.date() + timedelta(days=60)).isoformat()
    desde = (ahora.date() - timedelta(days=90)).isoformat()

    agenda = []
    for x in sorted(d["calendario"], key=lambda x: x.get("f") or ""):
        f = x.get("f")
        if not f or x["id"] in EXCLUIR or not (hoy <= f <= hasta):
            continue
        ev = f'{x["pais"]}: {TIPO.get(x["tipo"], "Elección").lower()}'
        if x.get("cargos"):
            ev += f' ({x["cargos"]})'
        if x.get("estado") and x["estado"] != "confirmada":
            ev += f' — fecha {x["estado"]}'
        r = {"fecha": f, "evento": ev, "eje": "Política internacional",
             "alcance": alcance(x["pais"]), "rubros": [], "url": URL,
             "fuente_original": x.get("fuente", "")}
        if x.get("res"):
            r["reservas"] = x["res"]
        agenda.append(r)

    novedades = []
    for x in sorted(d["recientes"], key=lambda x: x["f"], reverse=True):
        if x["id"] in EXCLUIR or not (desde <= x["f"] <= hoy):
            continue
        res = f'{TIPO.get(x["tipo"], "Elección")} en {x["pais"]}. '
        if x.get("ganador"):
            res += f'Ganó {x["ganador"]}'
            if x.get("partido") and x["partido"] not in x["ganador"]:
                res += f' ({x["partido"]})'
            if x.get("pct") is not None:
                res += f' con {str(x["pct"]).replace(".", ",")} %'
            res += ". "
        if x.get("parlamento"):
            res += f'{x["parlamento"]}. '
        p = paises.get(x["id"], {})
        if p.get("c") in REL:
            res += f'Relación del gobierno actual con la Argentina: {REL[p["c"]]}.'
        if x.get("res"):
            res += " Dato con reservas."
        r = {"id": f'{x["f"]}-eleccion-{slug(x["pais"])}-{x["tipo"]}',
             "fecha_dato": x["f"],
             "titulo": f'{x["pais"]}: {TIPO.get(x["tipo"], "Elección").lower()}'
                       + (f', ganó {x["ganador"]}' if x.get("ganador") else ""),
             "resumen": palabras(res.strip()), "tipo": "elección",
             "eje": "Política internacional", "alcance": alcance(x["pais"]),
             "rubros": [], "subrubros": [], "exposicion": [], "url": URL,
             "fuente_original": x.get("fuente", "")}
        novedades.append(r)

    out = {"web": "Elecciones del Mundo", "version": "1.0",
           "generado": ahora.replace(microsecond=0).isoformat(),
           "indicadores": [], "novedades": novedades, "agenda": agenda, "faltantes": []}
    (BASE / "datos-informe.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"datos-informe.json: {len(novedades)} novedades, {len(agenda)} eventos de agenda")


if __name__ == "__main__":
    main()
