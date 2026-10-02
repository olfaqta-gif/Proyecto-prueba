# Showcase: Apertura de Cuenta (App Banco Ficensa)

Video de 80 s en 16:9 (1920×1080, 30 fps) que muestra cómo se abre una cuenta desde la App, armado a partir del storyboard (`assets/storyboard.jpg`) y del logo.

**Resultado:** `salida/showcase-apertura-cuenta-16x9.mp4`

## Qué incluye
- **Intro:** el logo se arma (primero las cintas, después el texto), luego un barrido con las cintas amarilla, verde y celeste y una portada con el título palabra por palabra.
- **12 pasos:** las pantallas de la app están hechas en HTML y animadas (dedo que toca, onda del toque, globos de ayuda, texto que se escribe con la tecla que se ilumina, escaneo y flash del DNI, validación, prueba de vida, OTP con notificación, lista de agencias, confeti).
- **Panel:** capítulos que avanzan, número grande, título, descripción, **tarjeta de TIP** en cada paso y barra de progreso de 12 segmentos.
- **Cierre:** "¡Así de fácil!" con resumen, barrido a blanco, logo y llamado a la acción.
- **Audio:** música corporativa sintetizada (sin licencias) y efectos sincronizados con cada animación.

## Cómo editarlo
Los textos, los tips, los datos de ejemplo y los tiempos están en `guion.js`. Las pantallas de la app están en `pantallas.js`.

```bash
# Vista en vivo: abre showcase.html en el navegador (barra espaciadora = pausa; #t=30 empieza en el segundo 30)
export NODE_PATH=/opt/node22/lib/node_modules
node render.cjs eventos /tmp/eventos.json                 # línea de tiempo de sonidos
python3 musica.py /tmp/eventos.json /tmp/audio.wav        # música + efectos (necesita numpy y scipy)
node render.cjs video /tmp/f 6                            # cuadros (6 pestañas en paralelo)
ffmpeg -framerate 30 -i /tmp/f/f_%05d.jpg -i /tmp/audio.wav -c:v libx264 -pix_fmt yuv420p -crf 19 \
  -c:a aac -b:a 192k -shortest -movflags +faststart salida/showcase-apertura-cuenta-16x9.mp4
```

## Para revisar antes de publicar
- Los datos (JLOPEZ08, José Antonio López, DNI, teléfono, correo, código) son **ficticios**.
- Solo "Oficina Principal Tegucigalpa" viene del storyboard; **las otras agencias son de ejemplo**.
- El DNI y el rostro son ilustraciones, no fotos reales.
- Los textos del storyboard tenían letras corruptas: los reescribí. Hay que validar los tips y los mensajes con el banco.
