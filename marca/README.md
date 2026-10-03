# Marca de Isabella

- `voz-isabella.md`: su personalidad (cómo habla, su piel, qué quiere mostrar). La leen todos los agentes.
- `kit.json`: sus colores, letras, portadas de destacados y reglas (los mismos de su página web).

## Kit de marca (`kit.py`)

Para que todo lo que publica se vea de la misma marca, sin diseñar nada:

- **Portadas de destacados** (`portadas`): 8 portadas 1080×1920 con su ícono y nombre (Rutinas, Mi piel,
  Maquillaje, Favoritos, Opiniones, Cómo pedir, Únete, Sobre mí). En Instagram: abre el destacado ›
  Editar destacado › Editar portada › elige la imagen.
- **Historias listas** (`historia <tipo>`): Isa la arma con el texto que Isabella le da y sale la imagen
  para subir. Tipos: `nuevo` (producto con su foto), `opinion` (lo que dijo una clienta), `oferta`,
  `pregunta` (con espacio para la encuesta), `rutina` (pasos) y `gracias` (por su pedido). Revisa que el
  texto no prometa resultados ni ponga precios que ella no dio.
- **Fondos vacíos** (`fondos`): las mismas 6 plantillas sin texto, para escribir encima en Instagram.
- **Guía de marca** (`guia`): colores con su código, letras (y cuáles elegir en Instagram), portadas y reglas.
  Si alguien le hace un diseño, se la manda.

```bash
python3 marca/kit.py portadas
python3 marca/kit.py historia nuevo --producto 1002167 --titulo "Vitamin C Glow Serum" --texto "Luz desde el primer día"
python3 marca/kit.py historia opinion --texto "Me encantó" --quien "Carla" --producto 1000290 --titulo "Tea Tree Face Cream"
python3 marca/kit.py historia rutina --titulo "Mi rutina de noche" --paso Limpia --paso Sérum --paso Crema
python3 marca/kit.py fondos
python3 marca/kit.py guia
python3 marca/kit.py demo
```

Las imágenes salen con Chromium (`playwright`); si no está, se abre el `.html` y se toma captura.
Queda en `salida/` (solo en cada computadora). La foto del producto sale del agente de contenido o del
scraper, o se baja de farmasius.com.
