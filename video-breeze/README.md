# Video conceptual: Breeze AI dentro de HubSpot

Simulación estilo SaaS (sin voz, solo sonidos) de un agente Breeze que recibe tres peticiones
y devuelve resultados con motion graphics. 1920×1080, 30 fps, ~58 s.

**Resultado:** `breeze-hubspot.mp4`

## Guion

| Tiempo | Escena |
|---|---|
| 0–4 s | Intro: destello de Breeze, título "Breeze AI" |
| 4–9 s | Barrido circular a HubSpot: la UI de Contactos se arma en 3D, los KPIs cuentan |
| 9–22 s | Se abre Breeze → *"Genera un gráfico de los negocios creados este mes vs los creados el mes pasado"* → gráfico de barras animado (412 vs 547, ▲ 32.8 %) e insight |
| 22–34 s | *"¿Qué negocios tienen más probabilidad de cerrar esta semana?"* → ranking con anillos de probabilidad y pronóstico ponderado L 5.97M |
| 34–47 s | *"Asigna un propietario a los contactos sin dueño según su región"* → contador 58,270 → 0, barras por ejecutivo, y la UI se actualiza (KPI en 0, columna Propietario llena) |
| 48–58 s | Outro: "Pregunta. Decide. Actúa." → logo Breeze AI |

Todos los datos son de ejemplo (empresas, correos, ejecutivos y montos ficticios).

## Cómo regenerarlo

Requiere Node + Playwright (Chromium) y ffmpeg.

```bash
node render.js                 # cuadros -> out/frames.mp4 y out/cues.json
node audio.js 57.64            # banda sonora sintetizada -> out/audio.wav
ffmpeg -i out/frames.mp4 -i out/audio.wav -c:v copy -c:a aac -b:a 192k -shortest breeze-hubspot.mp4
node render.js stills 15 30    # capturas sueltas para revisar
```

- `breeze.html`: toda la animación; `seek(t)` dibuja el instante `t`. Textos, preguntas y cifras
  se editan en los arreglos `R`, `ROWS`, `DEALS` y `REG`. Los tiempos de cada ronda se encadenan solos.
- `audio.js`: efectos (tecleo, whoosh, pops, campanas, impactos, conteos) y música de fondo
  generados por síntesis, sincronizados con los `CUES` que exporta la página. No usa archivos de terceros.
