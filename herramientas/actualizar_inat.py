#!/usr/bin/env python3
"""Trae las observaciones de iNaturalist hechas en torno a San Blas Reserva
Ambiental y genera datos-inat.js (y descarga las fotos con licencia libre a
img/inat/).

Uso (desde la carpeta del repositorio):
    python herramientas/actualizar_inat.py            # consulta iNaturalist
    python herramientas/actualizar_inat.py --sin-red  # usa la copia guardada

Con red: consulta todas las observaciones en un círculo alrededor de la
reserva (ajustes-inat.json → «zona»), las agrupa por especie y guarda el
resultado en herramientas/inat-cache.tsv. Sin red (--sin-red): regenera
datos-inat.js a partir de esa copia; útil cuando api.inaturalist.org no está
accesible pero sí las fotos (inaturalist-open-data.s3.amazonaws.com).

Los nombres canarios, los estatus (endémica, invasora…), los alias y las
especies que hay que excluir se corrigen a mano en herramientas/ajustes-inat.json.

Solo usa la biblioteca estándar de Python 3 y respeta la API de iNaturalist
(una petición por segundo como máximo).

Licencias: solo se usan fotos con licencia Creative Commons (o CC0). Cada foto
lleva su autor y su licencia, que la web muestra en la ficha. Si quieren excluir
las licencias «NC» (no comercial), quítenlas de LICENCIAS.
"""
import csv, json, os, sys, time, urllib.parse, urllib.request

API = "https://api.inaturalist.org/v1"
FOTOS = "https://inaturalist-open-data.s3.amazonaws.com/photos"
LICENCIAS = {"cc0", "cc-by", "cc-by-sa", "cc-by-nc", "cc-by-nc-sa", "cc-by-nd", "cc-by-nc-nd"}
GRUPO = {"Plantae": "plantas", "Aves": "aves", "Insecta": "insectos", "Reptilia": "reptiles",
         "Arachnida": "aracnidos", "Mollusca": "moluscos", "Mammalia": "mamiferos",
         "Fungi": "hongos", "Actinopterygii": "peces", "Amphibia": "otros", "Animalia": "otros",
         "Chromista": "otros", "Protozoa": "otros"}
RANGOS = {"species", "subspecies", "variety", "form", "hybrid"}
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(RAIZ, "herramientas", "inat-cache.tsv")
CACHE_TAX = os.path.join(RAIZ, "herramientas", "taxonomia-cache.tsv")
CACHE_EXTRA = os.path.join(RAIZ, "herramientas", "extra-cache.tsv")
AJUSTES = os.path.join(RAIZ, "herramientas", "ajustes-inat.json")
AGENTE = "SanBlasCatalogo/1.0 (catalogo educativo)"
COLUMNAS = ["taxon_id", "cientifico", "subtaxones", "grupo_inat", "nombre_es", "nombre_en", "nombre_de",
            "establecimiento", "observaciones", "investigacion", "observadores", "primera", "ultima",
            "foto_id", "licencia", "ext", "credito", "ubicacion_aproximada"]


def pedir(ruta, **params):
    url = f"{API}{ruta}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": AGENTE, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        datos = json.load(r)
    time.sleep(1.1)
    return datos


def consultar(zona):
    """Observaciones de la zona → filas por especie (mismo formato que la copia)."""
    obs, ultimo = [], 0
    while True:
        d = pedir("/observations", lat=zona["lat"], lng=zona["lng"], radius=zona["radio_km"],
                  verifiable="true", per_page=200, order_by="id", order="asc", id_above=ultimo)
        obs += d["results"]
        if len(d["results"]) < 200:
            break
        ultimo = d["results"][-1]["id"]
    especies = {}
    for o in obs:
        t = o.get("taxon")
        if not t or t.get("rank") not in RANGOS:
            continue
        sid = t.get("min_species_taxon_id") or t["id"]
        e = especies.setdefault(sid, {"sub": set(), "n": 0, "r": 0, "u": set(), "d": [], "ocultas": 0})
        if t["id"] != sid:
            e["sub"].add(t["name"])
        e["n"] += 1
        e["r"] += o.get("quality_grade") == "research"
        e["u"].add(o["user"]["login"])
        if o.get("observed_on"):
            e["d"].append(o["observed_on"])
        e["ocultas"] += bool(o.get("obscured"))
    taxones = {}
    ids = list(especies)
    for loc in ("es", "en", "de"):
        for i in range(0, len(ids), 30):
            for t in pedir("/taxa/" + ",".join(map(str, ids[i:i + 30])), locale=loc)["results"]:
                x = taxones.setdefault(t["id"], {"t": t, "cn": {}})
                x["cn"][loc] = t.get("preferred_common_name") or ""
    filas = []
    for sid, e in especies.items():
        x = taxones.get(sid)
        if not x:
            continue
        t, p = x["t"], (x["t"].get("default_photo") or {})
        lic = p.get("license_code") or ""
        em = (t.get("establishment_means") or {}).get("establishment_means", "") if isinstance(t.get("establishment_means"), dict) else ""
        d = sorted(e["d"])
        filas.append({
            "taxon_id": sid, "cientifico": t["name"], "subtaxones": ";".join(sorted(e["sub"])),
            "grupo_inat": t.get("iconic_taxon_name") or "", "nombre_es": x["cn"].get("es", ""),
            "nombre_en": x["cn"].get("en", ""), "nombre_de": x["cn"].get("de", ""), "establecimiento": em,
            "observaciones": e["n"], "investigacion": e["r"], "observadores": len(e["u"]),
            "primera": d[0] if d else "", "ultima": d[-1] if d else "",
            "foto_id": p.get("id", "") if lic else "", "licencia": lic,
            "ext": (p.get("medium_url") or "").rsplit(".", 1)[-1] if lic else "",
            "credito": (p.get("attribution") or "").split(", uploaded by")[0] if lic else "",
            "ubicacion_aproximada": 1 if e["ocultas"] == e["n"] else 0})
    filas.sort(key=lambda f: f["cientifico"])
    with open(CACHE, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, COLUMNAS, delimiter="\t", lineterminator="\n")
        w.writeheader()
        w.writerows(filas)
    print(f"{len(obs)} observaciones, {len(filas)} especies guardadas en {os.path.relpath(CACHE, RAIZ)}")


def consultar_taxonomia(aj):
    """Reino, clase, orden y familia de todas las especies (iNaturalist + datos.js)."""
    def fila(t, nombre):
        anc = {a["rank"]: a["name"] for a in t.get("ancestors", [])}
        return {"cientifico": nombre, "reino": anc.get("kingdom", ""), "clase": anc.get("class", ""),
                "orden": anc.get("order", ""), "familia": anc.get("family", "")}
    filas, vistas = [], set()
    for f in leer_cache():
        if f["cientifico"] in aj.get("excluir", {}):
            continue
        nombre = aj.get("alias", {}).get(f["cientifico"], f["cientifico"])
        t = pedir(f"/taxa/{f['taxon_id']}")["results"][0]
        filas.append(fila(t, " ".join(nombre.split()[:2])))
        vistas.add(" ".join(nombre.lower().split()[:2]))
    for c in sorted(con_ficha() - vistas):
        nombre = c[:1].upper() + c[1:]
        res = [t for t in pedir("/taxa", q=nombre, rank="species", per_page=10)["results"] if t["name"].lower() == c]
        if not res:
            print("  sin taxonomía:", nombre, file=sys.stderr)
            continue
        filas.append(fila(pedir(f"/taxa/{res[0]['id']}")["results"][0], nombre))
    with open(CACHE_TAX, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, ["cientifico", "reino", "clase", "orden", "familia"], delimiter="\t", lineterminator="\n")
        w.writeheader()
        w.writerows(filas)
    print(f"Taxonomía de {len(filas)} especies guardada en {os.path.relpath(CACHE_TAX, RAIZ)}")


def generar_taxonomia(aj):
    """taxonomia.js: para cada especie, [nombre científico, nombre en español] de reino, clase, orden y familia."""
    nombres = aj.get("nombres_rangos", {})
    with open(CACHE_TAX, encoding="utf-8") as f:
        filas = list(csv.DictReader(f, delimiter="\t"))
    datos = {}
    for r in filas:
        clave = " ".join(r["cientifico"].lower().split()[:2])
        datos[clave] = {k: [r[k], nombres.get(r[k], "")] for k in ("reino", "clase", "orden", "familia") if r[k]}
    sin = sorted({r[k] for r in filas for k in ("reino", "clase", "orden", "familia") if r[k] and r[k] not in nombres})
    if sin:
        print("  rangos sin nombre en español (añádanlos a nombres_rangos):", ", ".join(sin), file=sys.stderr)
    js = ("/* Generado por herramientas/actualizar_inat.py — no editar a mano.\n"
          " * Clasificación (iNaturalist) para el selector de nivel del alumnado. */\n"
          "window.TAXONOMIA = {\n" + ",\n".join(f"{json.dumps(k, ensure_ascii=False)}: {json.dumps(v, ensure_ascii=False)}" for k, v in sorted(datos.items())) + "\n};\n")
    with open(os.path.join(RAIZ, "taxonomia.js"), "w", encoding="utf-8") as f:
        f.write(js)
    print(f"{len(datos)} especies en taxonomia.js")


def leer_cache(extra=True):
    """Especies de la zona y, además, las de «anadir» (vistas por el equipo)."""
    filas = []
    for ruta in (CACHE, CACHE_EXTRA) if extra else (CACHE,):
        if os.path.exists(ruta):
            with open(ruta, encoding="utf-8") as f:
                filas += list(csv.DictReader(f, delimiter="\t"))
    vistos, unicas = set(), []
    for f in filas:
        if f["taxon_id"] not in vistos:
            vistos.add(f["taxon_id"]); unicas.append(f)
    return unicas


def consultar_extra(aj):
    """Ficha básica de las especies de «anadir» que no salen en la zona."""
    zona = {f["taxon_id"] for f in leer_cache(extra=False)}
    filas = []
    for tid in [k for k in aj.get("anadir", {}) if k.isdigit() and k not in zona]:
        cn = {}
        for loc in ("es", "en", "de"):
            t = pedir(f"/taxa/{tid}", locale=loc)["results"][0]
            cn[loc] = t.get("preferred_common_name") or ""
        p = t.get("default_photo") or {}
        lic = p.get("license_code") or ""
        filas.append({"taxon_id": tid, "cientifico": t["name"], "subtaxones": "", "grupo_inat": t.get("iconic_taxon_name") or "",
                      "nombre_es": cn["es"], "nombre_en": cn["en"], "nombre_de": cn["de"], "establecimiento": "",
                      "observaciones": 0, "investigacion": 0, "observadores": 0, "primera": "", "ultima": "",
                      "foto_id": p.get("id", "") if lic else "", "licencia": lic,
                      "ext": (p.get("medium_url") or "").rsplit(".", 1)[-1] if lic else "",
                      "credito": (p.get("attribution") or "").split(", uploaded by")[0] if lic else "",
                      "ubicacion_aproximada": 0})
    with open(CACHE_EXTRA, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, COLUMNAS, delimiter="\t", lineterminator="\n")
        w.writeheader()
        w.writerows(filas)


def descargar(url, destino):
    req = urllib.request.Request(url, headers={"User-Agent": AGENTE})
    with urllib.request.urlopen(req, timeout=60) as r, open(destino, "wb") as f:
        f.write(r.read())


def mayuscula(s):
    s = (s or "").strip()
    return s[:1].upper() + s[1:]


def con_ficha():
    """Especies que ya tienen ficha y foto propias en datos.js (no hace falta bajar su foto)."""
    import re
    with open(os.path.join(RAIZ, "datos.js"), encoding="utf-8") as f:
        return {" ".join(c.lower().split()[:2]) for c in re.findall(r'cientifico:\s*"([^"]+)"', f.read())}


def generar(aj):
    os.makedirs(os.path.join(RAIZ, "img", "inat"), exist_ok=True)
    propias = con_ficha()
    salida, excluidas = [], []
    for f in leer_cache():
        cient = f["cientifico"]
        if cient in aj.get("excluir", {}):
            excluidas.append(cient)
            continue
        nombre = {"es": aj.get("nombres_es", {}).get(cient) or mayuscula(f["nombre_es"]),
                  "en": mayuscula(f["nombre_en"]), "de": mayuscula(f["nombre_de"])}
        nombre = {k: v for k, v in nombre.items() if v}
        estatus = list(aj.get("estatus", {}).get(cient, []))
        if not estatus and f["establecimiento"] == "introduced":
            estatus.append("introducida")
        if f["ubicacion_aproximada"] == "1":
            estatus.append("aproximada")
        if f["taxon_id"] in aj.get("anadir", {}):
            estatus.append("vista-reserva")
        foto = None
        nombre_final = aj.get("alias", {}).get(cient, cient)
        if f["licencia"] in LICENCIAS and f["foto_id"] and " ".join(nombre_final.lower().split()[:2]) not in propias:
            ext = f["ext"] or "jpg"
            ruta = f"img/inat/{f['taxon_id']}.{ext.lower()}"
            destino = os.path.join(RAIZ, ruta)
            if not os.path.exists(destino):
                try:
                    descargar(f"{FOTOS}/{f['foto_id']}/medium.{ext}", destino)
                    time.sleep(0.5)
                except Exception as e:
                    print("  sin foto:", cient, e, file=sys.stderr)
                    ruta = None
            if ruta:
                foto = {"src": ruta, "tipo": "foto", "credito": f["credito"], "licencia": f["licencia"],
                        "url": f"https://www.inaturalist.org/photos/{f['foto_id']}"}
        salida.append({"taxon_id": int(f["taxon_id"]), "cientifico": nombre_final,
                       "nombre": nombre, "grupo": GRUPO.get(f["grupo_inat"], "otros"),
                       "observaciones": int(f["observaciones"]), "investigacion": int(f["investigacion"]),
                       "observadores": int(f["observadores"]), "ultima": f["ultima"],
                       "estatus": estatus, "foto": foto})
    salida.sort(key=lambda x: (-x["observaciones"], x["cientifico"]))
    datos = {"actualizado": time.strftime("%Y-%m-%d"), "zona": aj["zona"], "especies": salida}
    js = ("/* Generado por herramientas/actualizar_inat.py — no editar a mano.\n"
          " * Observaciones de iNaturalist en un radio de "
          f"{aj['zona']['radio_km']} km alrededor de San Blas Reserva Ambiental. */\n"
          f"window.INAT = {json.dumps(datos, ensure_ascii=False, indent=1)};\n")
    with open(os.path.join(RAIZ, "datos-inat.js"), "w", encoding="utf-8") as f:
        f.write(js)
    print(f"{len(salida)} especies en datos-inat.js" + (f" (excluidas: {', '.join(excluidas)})" if excluidas else ""))


def main():
    with open(AJUSTES, encoding="utf-8") as f:
        aj = json.load(f)
    if "--sin-red" not in sys.argv:
        consultar(aj["zona"])
        consultar_extra(aj)
        consultar_taxonomia(aj)
    generar(aj)
    generar_taxonomia(aj)


if __name__ == "__main__":
    main()
