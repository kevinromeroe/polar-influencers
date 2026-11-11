# Runbook · Reporte de influencers Alimentos Polar

## Fuentes de datos

- **TikTok:** estadísticas públicas del video (`__UNIVERSAL_DATA_FOR_REHYDRATION__` → `statsV2`): reproducciones, me gusta, comentarios, compartidos y guardados. No requiere sesión.
- **Instagram:** `/api/v1/media/<id>/info/` con la sesión de Instagram del navegador (Claude en Chrome). Se usa `ig_play_count` como reproducciones; las de Facebook (`fb_play_count`) no se suman. Los guardados no son públicos.
- **Me gusta ocultos:** la API devuelve un valor de relleno (3). Esas piezas llevan `hl:1`, muestran "ocultos" y quedan fuera del promedio de engagement.
- **Comentarios:** Instagram `/api/v1/media/<id>/comments/` y TikTok `/api/comment/list/`. No cuentan los del creador ni los de las cuentas de marca. Se clasifican leyéndolos (positivo, neutro o crítico, más temas). No se guardan nombres de usuario.
- **Campaña UGC:** el enlace no tiene que ser de la cuenta del creador. Validar solo que el enlace exista. Si varias salidas usan el mismo enlace, sus reproducciones cuentan una vez en los totales.

## Actualizar las cifras

1. Captura las métricas y los comentarios con Claude en Chrome. Para listas largas, deja la lectura corriendo en segundo plano en la página y consúltala después, porque una sola llamada se corta a los 45 segundos.
2. Edita solo `datos/reporte.js`:
   - `corte` y `corteTexto`;
   - métricas en `rows`;
   - conteos, temas, citas y hallazgo de cada marca en `conv`.
3. Revisa en local con un servidor estático:

   ```
   python -m http.server 8813
   ```

   Abre http://localhost:8813. Revisa:
   - que cada pestaña abra;
   - que los hallazgos coincidan con las cifras;
   - que no haya errores en la consola.
4. Regenera los PDF:

   ```
   python scripts/render_pdf.py
   ```

5. Haz commit y push. GitHub Pages publica en uno o dos minutos.

## Agregar una salida

Agrega una fila en `rows` con el orden `[marca, creador, red, enlace, métricas, etiqueta, nota]`. Si el enlace todavía no llega, usa `null` en enlace y métricas: la salida cuenta en la inversión y aparece como "aún no tiene enlace".

Al 12 de noviembre de 2026 no hay salidas pendientes: las 42 de la base del cliente tienen enlace verificado.
