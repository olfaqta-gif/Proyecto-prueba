# Video conceptual: Agentes de IA de Banco Ficensa en HubSpot

Video estilo SaaS, sobrio y corporativo (sin voz, sonido sutil), que muestra cuatro agentes
trabajando dentro de HubSpot. 1920×1080, 30 fps, ~67 s.

**Resultado:** `agentes-hubspot.mp4`

## Guion

| Tiempo | Escena |
|---|---|
| 0–5 s | Logo de Banco Ficensa · "Agentes de IA que trabajan dentro de nuestro CRM" |
| 5–12 s | Mapa: HubSpot/Breeze al centro conectado con los cuatro agentes |
| 12–24 s | **01 Prospección:** investiga 6 empresas, redacta un correo personalizado, agenda la reunión |
| 23–35 s | **02 Atención al cliente:** responde un chat con la base de conocimiento, agenda cita, escala un caso a un asesor |
| 35–47 s | **03 Calidad de datos:** fusiona duplicados, completa industria y región, la calidad sube de 61% a 97% |
| 46–59 s | **04 Negocios:** mueve el pipeline, marca un negocio en riesgo, crea tareas y muestra el pronóstico |
| 58–67 s | Resumen de los cuatro agentes · "Más tiempo para lo que importa: nuestros clientes." · logo |

Cada agente usa un color del logo de Ficensa (azul, cian, verde, amarillo).
Todos los datos son de ejemplo.

## Cómo regenerarlo

```bash
node render.js                       # cuadros -> out/frames.mp4 y out/cues.json
node audio.js 67.5                   # audio sutil -> out/audio.wav
ffmpeg -i out/frames.mp4 -i out/audio.wav -c:v copy -c:a aac -b:a 192k -shortest agentes-hubspot.mp4
node render.js stills 18 30          # capturas sueltas para revisar
```

Textos y cifras se editan en `agentes.html` (arreglos `AG`, `COMP`, `CH`, `DR`, `DEALS` y
el texto `EMAIL`). Los tiempos de cada escena están en `TL`, `SCN` y `OUT`.
