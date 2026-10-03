# Media kit de Isabella

Su carta de presentación para **marcas, tiendas y otras creadoras**: un PDF de dos páginas que
se manda cuando una marca pregunta "¿me pasas tus números?" o cuando Isabella quiere proponer
una colaboración.

**Página 1:** foto, nombre, usuario, una frase sobre ella, sus temas; seguidores, vistas por
video, interacción y guardados; seguidores por red y cuánto crecieron en 30 días; quién la sigue
(mujeres, edades, ciudades) y sus 3 publicaciones más vistas.
**Página 2:** cómo pueden trabajar juntas (reel, historias, carrusel, en vivo, sorteo, contenido
para la marca), por qué con ella, los productos que recomienda, tarifas (opcional) y contacto.

**Cómo se usa:** *"Isa, hazme mi media kit"*. Los números salen solos de lo que guardó la Analista
de redes con las capturas de Isabella: no se inventa nada y lo que no hay no sale. Cada vez que
manda capturas nuevas, se vuelve a armar y queda al día.

```bash
python3 mediakit/kit.py armar [--dias 90]   # salida/media-kit.html, .pdf, -1.png, -2.png
python3 mediakit/kit.py audiencia --red instagram --mujeres 86 --edades "18-24:14,25-34:41" --lugares "Miami:31,Houston:9"
python3 mediakit/kit.py falta               # lo que falta completar
python3 mediakit/kit.py demo                # ejemplo con números inventados (lleva el sello EJEMPLO)
```

- `perfil.json` (se crea de `perfil.ejemplo.json`): nombre, usuario, foto, frase, ciudad, correo,
  WhatsApp, temas, colaboraciones, "por qué conmigo", productos favoritos (ids de `asesora/catalogo.json`),
  marcas y tarifas. Lo que ya está en `marca/voz-isabella.md` se usa solo.
- `datos/audiencia.json`: quién la sigue, de la captura de "Audiencia" (la guarda la Analista).
- El PDF y las imágenes salen con Chromium (`playwright`). Si no está, se abre `media-kit.html` y
  se toca «Guardar como PDF».

Lo que queda en cada computadora (no se sube): `perfil.json`, `datos/` y `salida/`.
