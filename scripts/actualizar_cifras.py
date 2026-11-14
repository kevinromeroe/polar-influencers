#!/usr/bin/env python3
"""actualizar_cifras.py: actualiza las métricas de datos/reporte.js con las lecturas del día.

Uso (desde la raíz del repo):
    python scripts/actualizar_cifras.py lecturas.json            # reescribe datos/reporte.js
    python scripts/actualizar_cifras.py lecturas.json --prueba   # solo muestra los cambios

Después: revisar en local y regenerar los PDF (ver docs/RUNBOOK.md).

Reglas validadas por Kevin (13-nov-2026). No se cambian sin su aprobación:
1. Las campañas no se congelan: se actualizan aunque el cliente las haya aprobado.
2. Una cifra SOLO se actualiza si SUBE. Si la lectura es menor se conserva la anterior y se informa.
3. Nada se borra: las salidas y filas vienen del cliente. Si varias salidas comparten el mismo enlace,
   todas reciben las mismas cifras (el reporte cuenta sus reproducciones una sola vez).
4. Me gusta ocultos (hl:1): siguen «ocultos», nunca se ponen en 0 ni se reemplazan.
5. Instagram muestra los me gusta redondeados desde ~1.000 («1.2K»). Este reporte todavía no muestra
   «≈», así que una cifra redondeada NO se usa: se conserva la exacta y se avisa para decidir con Kevin.
6. Solo cambian las métricas, `corte` y `corteTexto`. La conversación (conv) y los textos no se tocan.

Formato de lecturas.json (lo escribe Claude al leer las redes; ver docs/RUNBOOK.md):
{
  "fecha": "2026-11-13",
  "publicaciones": {
    "DezduFDMRWa": {"views": 3669, "likes": "185", "comments": "33", "shares": "19"},
    "7702146885305388294": {"views": 628, "likes": 39, "comments": 30, "shares": 8, "saves": 5}
  }
}
Clave: código de Instagram (lo que va después de /p/, /reel/ o /reels/) o id del video de TikTok.
Vacío o null = la red no mostró el número: no se toca.
"""
import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATOS = ROOT / "datos" / "reporte.js"
CLAVES = {"views": "v", "likes": "l", "comments": "c", "shares": "s", "saves": "g"}
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
         "septiembre", "octubre", "noviembre", "diciembre"]


def cifra(v):
    """(número, es_aproximado) o None. «1.2K» → (1200, True); «1,234» → (1234, False)."""
    if v is None or isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return int(v), False
    t = str(v).strip().replace(" ", " ")
    if not t:
        return None
    m = re.fullmatch(r"([\d.,]+)\s*(K|M|mil|mill\.?|millones)?", t, re.I)
    if not m:
        raise ValueError(f"Cifra no reconocida: {v!r}")
    num, suf = m.group(1), (m.group(2) or "").lower()
    if suf:
        mult = 1_000 if suf in ("k", "mil") else 1_000_000
        return int(round(float(num.replace(",", ".")) * mult)), True
    return int(num.replace(",", "").replace(".", "")), False


def codigo(url: str) -> str | None:
    m = re.search(r"/(?:reels?|p)/([^/?]+)", url) or re.search(r"/video/(\d+)", url)
    return m.group(1) if m else None


def actualizar(texto: str, lecturas: dict) -> tuple[str, list[str], list[str]]:
    """Devuelve (texto nuevo, cambios, avisos)."""
    pubs = {str(k): v for k, v in (lecturas.get("publicaciones") or {}).items()}
    cambios, avisos, vistos = [], [], set()

    def fila(mm):
        url, met = mm.group(1), mm.group(2)
        cod = codigo(url)
        vals = {k: int(v) for k, v in re.findall(r"(\w+):(-?\d+)", met)}
        med = pubs.get(cod)
        if med is None:
            return mm.group(0)
        vistos.add(cod)
        for campo, k in CLAVES.items():
            c = cifra(med.get(campo))
            if c is None or k not in vals:
                continue
            v, aprox = c
            if k == "l" and vals.get("hl"):
                continue
            if aprox:
                avisos.append(f"{cod} {campo}: Instagram muestra {med.get(campo)!r} (redondeado); se conserva {vals[k]}")
                continue
            if v > vals[k]:
                cambios.append(f"{cod} {k}: {vals[k]} → {v}")
                vals[k] = v
            elif v < vals[k]:
                cambios.append(f"{cod} {k}: se conserva {vals[k]} (lectura menor: {v})")
        orden = [k for k in ("v", "l", "c", "s", "g", "hl") if k in vals]
        return f'"{url}",{{' + ",".join(f"{k}:{vals[k]}" for k in orden) + "}"

    nuevo = re.sub(r'"(https://www\.(?:instagram|tiktok)\.com/[^"]+)",\{([^}]*)\}', fila, texto)
    for cod in sorted(set(pubs) - vistos):
        avisos.append(f"{cod}: no está en el reporte (las salidas nuevas se agregan a mano, ver docs/RUNBOOK.md)")
    f = date.fromisoformat(lecturas["fecha"])
    nuevo, n1 = re.subn(r'corte:"[^"]*"', f'corte:"{f.isoformat()}"', nuevo, count=1)
    nuevo, n2 = re.subn(r'corteTexto:"[^"]*"', f'corteTexto:"{f.day} de {MESES[f.month - 1]} de {f.year}"', nuevo, count=1)
    if not (n1 and n2):
        raise SystemExit("No encontré corte/corteTexto en datos/reporte.js")
    return nuevo, sorted(set(cambios)), avisos


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("lecturas")
    ap.add_argument("--prueba", action="store_true", help="no escribe nada")
    a = ap.parse_args()
    lect = json.loads(Path(a.lecturas).read_text(encoding="utf-8"))
    texto = DATOS.read_text(encoding="utf-8")
    nuevo, cambios, avisos = actualizar(texto, lect)
    print("\n".join(cambios) or "Sin cambios.")
    for x in avisos:
        print("AVISO", x)
    if not a.prueba:
        DATOS.write_text(nuevo, encoding="utf-8")
        print("Escrito: datos/reporte.js")


if __name__ == "__main__":
    main()
