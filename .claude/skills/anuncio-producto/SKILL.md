---
name: anuncio-producto
description: Agente de contenido Farmasi. Convierte un producto en anuncios de 15 s con música (3 estilos; formatos 9:16, 4:5, 1:1 y 16:9), más el caption listo para publicar. Úsalo cuando pidan un anuncio, reel, post o video de un producto Farmasi.
---

# Agente de contenido: producto Farmasi → video + caption

Todo el motor vive en `agente-contenido/`. Tu trabajo como agente es **llenar una ficha
con buen copy y datos verdaderos**; el script se encarga del diseño, la animación, la
música y el render. Lee `agente-contenido/README.md` si necesitas el detalle de cada campo.

## 1. Reunir la información del producto

Necesitas: nombre exacto, categoría, para quién es, 2 o 3 beneficios, y una foto del
producto (ideal: fondo blanco o transparente, el envase completo).

- Toma los datos de la página oficial de Farmasi o de lo que diga Julio. Si consultas la
  web, anota de dónde salió cada dato.
- La calificación y número de reseñas solo van si los viste publicados. Si no, deja
  `producto.dato` vacío (el bloque desaparece del video).
- **No inventes** porcentajes de resultados, promesas médicas ("cura", "elimina el acné"),
  ni promesas de ingresos. Usa verbos de experiencia: "notarás", "ayuda a", "se siente".
- Si falta la foto, pídela. Si viene con fondo de color, puedes quitarlo con la
  herramienta de Higgsfield `remove_background` antes de usarla.

## 2. Escribir la ficha

Crea `agente-contenido/productos/<slug>/` con la imagen (`producto.jpg|png|webp`) y un
`ficha.json`. Copia uno de los ejemplos (`vitamin-c-glow-serum`, `tea-tree-face-cream`) y
reemplaza todo. Reglas de copy:

- **Gancho** (lo que detiene el scroll): `linea1` nombra un problema o deseo de la clienta
  en sus palabras, `linea2` es la respuesta corta (va en letra cursiva dorada). Máx. ~40 y ~28 caracteres.
- **Beneficios**: 2 o 3, cada uno ≤ 34 caracteres, empezando por lo que ella nota.
- **Cierre**: `frase1` + `frase2` forman una sola idea; `palabra` es la palabra clave que
  ella debe escribirte por mensaje (corta, en mayúsculas, relacionada al producto).
- **Paleta**: `coral`, `dorado`, `verde`, `lavanda` o `rosa`. Elige la que combine con el envase.
- **Estilo** (`estilo`): `clasico` (problema → solución, elegante), `favorito` (tipo TikTok,
  "mi favorito", fondo claro) o `razones` ("3 razones", directo). Para que los anuncios no
  se vean todos iguales, **no repitas el estilo del anuncio anterior**: mira qué estilo
  tienen las fichas más recientes en `productos/` y elige otro, salvo que Julio pida uno.
  Si te piden comparar, usa `--estilo todos`.
- **Textos por estilo** (`estilos.<estilo>`): cada estilo pide un gancho distinto. Escribe
  al menos el del estilo elegido; lo que pongas ahí reemplaza a los campos generales:
  - `favorito`: voz en primera persona ("El té que me tomo cada tarde" / "Y no lleva azúcar"),
    `beneficios.titulo` tipo "Por qué me encanta".
  - `razones`: `gancho.linea1` = "razones para probar" (el número lo pone el video),
    `linea2` = "este té" / "este sérum"; razones un poco más completas (≤ 34 caracteres).
- **Formatos**: por defecto salen los 4 (9:16, 4:5, 1:1, 16:9). Usa `formatos` en la ficha
  solo si Julio pide menos.
- **Aviso**: siempre aclarar "Distribuidora independiente Farmasi" y que los resultados varían.
- **Caption**: primera línea = gancho (se ve antes del "ver más"), luego beneficios con
  emojis, prueba social si existe, y el llamado a escribir la palabra clave. 5–12 hashtags
  en español, mezclando marca (#farmasi), producto y necesidad. Sin el símbolo # en la lista.

Todo en español neutro latino, tuteando, cálido y directo.

## 3. Generar y revisar

```bash
cd agente-contenido
python3 generar.py productos/<slug>
```

El script valida la ficha (errores = no genera; avisos = textos largos). Después **abre
las previas `salida/<slug>/<estilo>/previa-<formato>.jpg` y míralas** (al menos 9x16 y
1x1, que es el más apretado): un cuadro por escena. Revisa que ningún texto se corte, que
el producto se vea completo y que la paleta combine. Corrige la ficha y repite hasta que
se vea bien.

## 4. Voz (opcional)

Si piden narración: escribe un guion de máx. 35 palabras que siga las escenas (gancho →
producto → beneficios → llamado), genéralo con Higgsfield (`generate_audio`, voz de Elena
como en videos anteriores), guárdalo como `productos/<slug>/voz.mp3` y agrega a la ficha
`"voz": {"archivo": "voz.mp3", "inicio": 0.3, "guion": "…"}`. La música baja sola cuando
la voz habla.

## 5. Video final y entrega

```bash
python3 generar.py productos/<slug> --video
```

Entrega los videos `salida/<slug>/<estilo>/anuncio-<formato>.mp4` (dile para qué red
sirve cada formato) y el texto de `salida/<slug>/caption.txt`. Si el proyecto tiene
carpeta compartida (`/mnt/project-files`), copia la carpeta `<estilo>/` y el caption a
`/mnt/project-files/anuncios/<slug>/` y adjúntalos.

**Nunca publiques** en TikTok, Instagram ni ningún otro lado sin que Julio lo pida
explícitamente para ese video.

## Requisitos del entorno

`python3` con `numpy` y `scipy`, `node` con `playwright` (Chromium), y `ffmpeg`.
Si falta numpy/scipy: `python3 -m pip install numpy scipy`.
