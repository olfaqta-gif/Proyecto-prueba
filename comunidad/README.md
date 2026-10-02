# Agente de comunidad y ventas

Para que **ningún mensaje se quede sin respuesta y ninguna clienta se pierda**.

**Cómo se usa:** Isabella saca capturas de pantalla de los comentarios y mensajes que le
llegan (Instagram, TikTok, WhatsApp o Facebook), las deja en `comunidad/capturas/` (o se las
pega a Isa en el chat, o le copia el texto) y le dice *"Isa, ayúdame a responder"*. El agente
las lee y le entrega una hoja con una respuesta para cada persona, escrita con su voz.

En la hoja cada tarjeta trae lo que escribió la persona, la respuesta (se puede cambiar
ahí mismo), «Copiar y abrir chat» y «Listo ✓». Lo que está en amarillo (como `[precio]`)
lo completa Isabella. Van primero las que quieren comprar.

Nadie se conecta a sus cuentas ni envía nada: ella copia, pega y envía.

## Las respuestas rápidas

Lo que más se repite (INFO, precio, cómo pedir, envío, tipo de piel, tonos, gracias,
cómo vender Farmasi) se guarda **una sola vez** en el celular como respuesta guardada de
Instagram o respuesta rápida de WhatsApp Business: después se escribe `/info` y aparece el
mensaje completo. El kit con los pasos sale de `respuestas-rapidas.json` en
`respuestas/respuestas-rapidas.html`.

## Precios

Si Isabella quiere que las respuestas lleven sus precios, crea `comunidad/precios.md` con
su lista (producto y precio). Si no existe, las respuestas dicen `[precio]`.

## `responder.py` (solo Python estándar)

- `pendientes`: capturas sin leer y si hay lista de precios.
- `hoja <lote.json>`: arma `respuestas/<fecha>.html`, anota a las interesadas en la libreta de
  clientas (`clientas/libreta.py`), pasa las capturas a `capturas/leidas/` y avisa si alguna
  respuesta promete resultados o dinero, o trae un precio inventado. El lote es una lista de
  conversaciones; mira `ejemplo-lote.json`:

  | campo | qué es |
  |---|---|
  | `red` | instagram, tiktok, whatsapp, facebook |
  | `donde` | comentario, mensaje, historia |
  | `usuario`, `nombre`, `telefono` | quién es (lo que se vea) |
  | `texto` | lo que escribió |
  | `publicacion` | en qué video o post comentó |
  | `intencion` | comprar, precio, producto, envio, negocio, queja, elogio, otro, spam |
  | `producto` | lo que le interesa |
  | `respuesta`, `otra` | la respuesta y otra forma de decirlo (opcional) |
  | `consejo` | un tip para Isabella (opcional) |
  | `captura` | la captura de donde salió |
- `rapidas`: arma el kit de respuestas rápidas.
- `resumen`: cuántos mensajes se han respondido y de qué.

Lo que queda en cada computadora (no se sube al repositorio): `capturas/`, `respuestas/` y `datos/`.
