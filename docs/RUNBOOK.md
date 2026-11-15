# Runbook · Reporte de influencers Alimentos Polar

## Reglas de actualización (validadas por Kevin, 13 nov 2026)

- Las campañas **no se congelan**: se actualizan aunque el cliente las haya aprobado. Más interacciones = más valor para el cliente.
- Una cifra **solo se actualiza si sube**. Si la lectura nueva es menor, se conserva la anterior.
- **Nada se borra.** Las salidas vienen de la base del cliente. Si dos salidas comparten el mismo enlace, eso es correcto (contenido compartido): las dos llevan las mismas cifras y las reproducciones cuentan una vez en los totales.
- **Me gusta ocultos**: se quedan como "ocultos" (`hl:1`), nunca en 0.
- **Cifras redondeadas**: Instagram muestra los me gusta redondeados desde ~1.000 (`1.2K`). Este reporte todavía no tiene el símbolo «≈», así que el script no usa cifras redondeadas: conserva la exacta y avisa. Si aparece el aviso, se decide con Kevin (LCI ya muestra «≈»).
- Textos de conversación y hallazgos curados se mantienen; los nuevos los escribe Claude. Los hallazgos con cifras del resumen se recalculan solos en `index.html`.
- Todo esto vive en `scripts/actualizar_cifras.py` y lo prueba `tests/test_actualizar.py`.

## Fuentes de datos

| Red | Qué | Cómo |
|---|---|---|
| Instagram | me gusta, comentarios, compartidos | Pantalla de la publicación con sesión: Claude en Chrome del OptiPlex, perfil `Default` (kevinromeroe). |
| Instagram | reproducciones | Apify (`vistas_apify.py` de la skill `levantamiento-redes`). Ojo: `videoPlayCount` puede incluir Facebook; antes se usaba `ig_play_count` (solo Instagram). Revisar saltos mayores a 15 %. |
| TikTok | reproducciones, me gusta, comentarios, compartidos, guardados | `__UNIVERSAL_DATA_FOR_REHYDRATION__` → `statsV2` en la página del video. No requiere sesión. |
| Comentarios | clasificación de la conversación | Se leen en pantalla y se clasifican (positivo, neutro, crítico; temas). No se guardan nombres de usuario ni se cuentan los del creador o la marca. |

- La API interna de Instagram (`/api/v1/media/…`) **ya no se usa**: está bloqueada desde Chrome.
- **Campaña UGC:** el enlace no tiene que ser de la cuenta del creador. Validar solo que el enlace exista.

## Actualizar las cifras

Corre en el OptiPlex (`~/repos/polar-influencers`), en una rama `actualizacion/<fecha>`.

1. **Leer las redes con Claude en Chrome** (perfil kevinromeroe; comprobar que instagram.com tiene la sesión iniciada).
   - Ritmo prudente: pausa de 5 a 10 s entre publicaciones y máximo ~40 páginas de Instagram por sesión. Si aparece verificación, `/challenge` o "actividad inusual": parar, no hacer clic y avisar a Kevin.
   - Instagram, en `https://www.instagram.com/p/<código>/`, leer la barra de acciones:

     ```js
     const s=document.querySelector('main section'); const w=document.createTreeWalker(s,5); const o=[]; let n;
     while(n=w.nextNode()){ if(n.nodeType==1&&n.tagName.toLowerCase()=='svg'&&n.getAttribute('aria-label')) o.push('['+n.getAttribute('aria-label')+']');
       else if(n.nodeType==3&&n.textContent.trim()&&!n.parentElement.closest('svg')) o.push(n.textContent.trim()); }
     o.join(' ')   // «[Like] 185 [Comment] 33 [Share] 19 [Save]». Sin número = oculto o 0.
     ```
   - TikTok, en la página del video (esperar ~6 s a que cargue; la URL redirige):

     ```js
     JSON.parse(document.getElementById('__UNIVERSAL_DATA_FOR_REHYDRATION__').textContent)
       .__DEFAULT_SCOPE__['webapp.video-detail'].itemInfo.itemStruct.statsV2
     ```
2. **Vistas de Instagram con Apify**:
   ```
   python3 ~/.claude/skills/levantamiento-redes/scripts/vistas_apify.py polar-influencers --desde lecturas.json
   ```
   y copiar cada valor a `views` de su código en las lecturas.
3. **Guardar las lecturas** en `~/datos/crudos/polar-influencers/lecturas-<AAAA-MM-DD>.json` (formato en la cabecera de `scripts/actualizar_cifras.py`; las cifras se copian tal como se ven, p. ej. `"1.2K"`). Esa carpeta entra al backup diario.
4. **Aplicar las reglas**:
   ```
   python3 scripts/actualizar_cifras.py ~/datos/crudos/polar-influencers/lecturas-<fecha>.json --prueba
   python3 scripts/actualizar_cifras.py ~/datos/crudos/polar-influencers/lecturas-<fecha>.json
   python3 -m unittest discover tests
   ```
   Revisar los avisos (cifras redondeadas, saltos grandes, publicaciones que no están en el reporte).
5. **Conversación** (`conv` en `datos/reporte.js`): solo si hay comentarios nuevos que cambien conteos o temas. Los textos existentes se mantienen.
6. **Revisar en local** con `python3 -m http.server 8813` → http://localhost:8813: cada pestaña abre, los hallazgos coinciden con las cifras, sin errores en la consola.
7. **Mostrar la vista previa a Kevin.** Él revisa el resultado, no la rama. Nada se publica sin su aprobación.
8. **PDF**: `python scripts/render_pdf.py` (necesita Playwright con Chromium; en el OptiPlex todavía no está instalado, se generan en el PC de Kevin).
9. Commit en la rama, fusionar a `main` y push. GitHub Pages publica en uno o dos minutos. Verificar en https://polar.datalitica.com.co que la fecha de corte cambió.

Historial: 13 nov 2026, primera actualización con este proceso (`lecturas-2026-11-13.json`; reproducciones 177,3 mil → 181,9 mil).

## Agregar una salida

Agrega una fila en `rows` con el orden `[marca, creador, red, enlace, métricas, etiqueta, nota]`. Si el enlace todavía no llega, usa `null` en enlace y métricas: la salida cuenta en la inversión y aparece como "aún no tiene enlace".

Al 13 de noviembre de 2026 no hay salidas pendientes: las 42 de la base del cliente tienen enlace verificado.

## Corrida automática (desde el 14 de noviembre de 2026)

Corre sola en el OptiPlex **lunes y jueves a las 7:00** (`~/ops/influencers/corrida.sh`, crontab). Decisión de Kevin: sin vista previa; **se publica sola si pasa el control automático** y, si no, no se publica y avisa en el resumen de WhatsApp.

1. `lista.py` arma la lista de publicaciones del reporte.
2. **Instagram va completo por Apify** (vistas, me gusta, comentarios y seguidores, `apify_ig.py`): la sesión de Instagram en Chrome pidió verificación. Apify no da compartidos: esa cifra se conserva. **TikTok y YouTube** los lee Claude en Chrome (sin sesión, nunca abre Instagram).
3. `validar_corrida.py`: se frena si se leyó menos del 80 % de las publicaciones o aparece una que no está en el reporte; una cifra que sube más de 30 % y más de 1.000 de golpe no se aplica (se conserva la anterior) y se informa.
4. `scripts/actualizar_cifras.py` aplica las reglas de este documento, pruebas, build/PDF, push y verificación en línea.
5. Si fallan las pruebas o el build, el trabajo queda en una rama `fallida/<fecha>-<repo>` y no se publica.

Esta sección reemplaza los pasos manuales de lectura por Chrome para Instagram; el resto de las reglas sigue igual.
