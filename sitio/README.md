# Página web de Isabella

Página de una sola hoja (`index.html`) para que las clientas conozcan a Isabella, jueguen,
dejen sus datos y le escriban. Sobria y elegante, con transiciones suaves. Gratis: no
necesita servidor.

## Qué tiene

- **Cuatro gestos**: sus cuatro imprescindibles, con la foto que cambia mientras bajas.
- **La selección**: 10 productos con fotos reales de la tienda, filtros (piel / maquillaje)
  y una ficha con galería, qué tiene, cómo se usa y sus tonos. Sin precios.
- **Mi lista**: la clienta guarda lo que le gusta y se lo manda a Isabella por WhatsApp.
- **Rasca tu regalo**: tarjeta para rascar con un regalo de bienvenida (descuento, envío
  gratis o muestra) y un código. Para apartarlo deja nombre, WhatsApp y, si quiere, su
  cumpleaños. Un regalo por persona en cada celular.
- **Descubre tu ritual**: test de 4 preguntas que arma la rutina de mañana, noche y maquillaje.
- **Aprende conmigo**: los videos del Profe (`agente-educativo/`), en versión liviana.
- **Escríbeme**: arma el mensaje y abre WhatsApp.

Todos los mensajes empiezan con "vengo de tu página web", así el agente de comunidad sabe de
dónde llegó la clienta.

## Lo que se llena

En `index.html`, el bloque `ISABELLA` al empezar el `<script>`:

- `whatsapp`, `instagram`, `tiktok` y `foto` de Isabella.
- `regalos`: los descuentos del juego y qué tan seguido sale cada uno (`peso`). Solo pon
  regalos que Isabella de verdad pueda dar.
- `hojaGoogle`: para guardar solita cada clienta en una hoja de Google (abajo).

Mientras falten el WhatsApp o el Instagram, la página muestra un aviso de "vista previa".

## Productos y fotos

`productos.json` dice qué productos van y su texto en español. Para traer de la tienda las
fotos, las reseñas y los tonos al día:

```bash
python3 sitio/preparar.py
```

Escribe `productos.js` y baja las fotos a `img/productos/`. Si una foto de la tienda no
sirve (un cartel con porcentajes, una bolsa…), pon su número en `quitar_fotos`.

## Guardar las clientas en la libreta (gratis, una sola vez)

1. Crea una hoja nueva en Google Sheets.
2. Menú **Extensiones → Apps Script**, borra lo que hay y pega `hoja-google.gs`. Guarda.
3. **Implementar → Nueva implementación → Aplicación web**. "Ejecutar como": tú.
   "Quién tiene acceso": cualquier persona. Copia el enlace que termina en `/exec`.
4. Pega ese enlace en `hojaGoogle` dentro de `index.html`.
5. En la hoja: **Compartir → Cualquier persona con el enlace puede ver**, y trae las clientas a
   la libreta con:

```bash
python3 clientas/libreta.py sincronizar "<enlace de la hoja>"
```

Cada clienta entra con su nombre, WhatsApp, cumpleaños, piel, lo que le interesa y
"vino por: página web".

## Verla y publicarla

Abre `sitio/index.html` en el navegador. Para tenerla en internet gratis se puede usar
GitHub Pages.
