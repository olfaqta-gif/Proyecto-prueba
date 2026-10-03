# Asesora de rutinas

Para que cuando una clienta pregunte **"¿qué me recomiendas para mi piel?"** reciba en minutos
su rutina de mañana y noche, y en vez de comprar un producto compre su rutina.

**Cómo se usa:** Isabella le pega a Isa el mensaje de la clienta (o una captura del chat) y le
dice *"Isa, ármale una rutina"*. La asesora entiende su tipo de piel y lo que le preocupa, elige
los productos Farmasi y entrega:

- una **tarjeta** (imagen 1080×1920, sirve para WhatsApp y para historias) con su nombre, cada
  paso con la foto del producto, cuándo se usa (mañana, noche o una vez por semana) y cuáles son
  los **esenciales** para empezar;
- el **mensaje ya escrito** para mandarle, que termina con "¿Te armo el kit esencial o la rutina completa?";
- a la clienta **anotada en la libreta** como «Interesada», con su piel y los productos que le interesan.

En la página de la tarjeta Isabella toca «Copiar mensaje», «Abrir su chat» y «Guardar imagen»,
y la manda. Nada se envía solo. Al costado también ve cómo se usa cada producto, por si la clienta pregunta.

## Cómo elige

`catalogo.json` tiene los 34 productos de cuidado de la piel de Dr. C. Tuna que puede recomendar,
cada uno con su paso, para qué piel y qué necesidad es, y el texto en español. Para cada paso
gana el que mejor calce con su piel y lo que más le preocupa; si empatan, el mejor calificado y
más comprado de la tienda.

- **Esenciales:** limpiador, un sérum para lo que más le preocupa, crema y protector solar.
- **Rutina completa:** suma tónico, un segundo sérum para la otra preocupación (cada uno en su
  momento: la vitamina C de día, el retinol de noche), contorno de ojos si hay ojeras o arrugas,
  desmaquillante si se maquilla y un mimo semanal (mascarilla o exfoliante).
- **Piel sensible, embarazo o algo de salud** (rosácea, dermatitis, medicamentos…): solo
  productos suaves, sin retinol ni exfoliante, y el mensaje le sugiere consultarlo con su médico.
- Farmasi US no vende protector solar: ese paso dice "el de siempre".

## `rutina.py` (solo Python estándar)

```bash
python3 asesora/rutina.py armar consulta.json       # tarjeta + mensaje + libreta
python3 asesora/rutina.py armar --nombre Lucía --piel mixta --necesidad granitos --necesidad manchas
python3 asesora/rutina.py opciones                  # pieles, necesidades y productos por paso
python3 asesora/rutina.py lista                     # rutinas que ya se armaron
python3 asesora/rutina.py demo                      # 3 de ejemplo en rutinas/ejemplos/ (no tocan la libreta)
```

La consulta:

| campo | qué es |
|---|---|
| `nombre`, `usuario`, `red`, `telefono` | quién es (con teléfono, «Abrir su chat» abre WhatsApp con el mensaje escrito) |
| `mensaje` | lo que escribió ella, tal cual (si faltan `piel` o `necesidades`, se deducen de aquí) |
| `piel` | `grasa`, `mixta`, `normal`, `seca`, `sensible`, `madura` (una o dos) |
| `necesidades` | en orden: `granitos`, `brillo`, `poros`, `manchas`, `opaca`, `resequedad`, `sensibilidad`, `arrugas`, `firmeza`, `textura`, `ojeras`, `maquillaje` |
| `elegir` | cambiar un paso: `{"tratar": "serum-vitamina-c"}` (los ids salen en `opciones`) |
| `quitar` | productos que no van (ya los tiene, no le gustan) |
| `texto_whatsapp` | el mensaje en la voz de Isabella (si no, se escribe uno) |

Queda en `rutinas/<fecha>-<nombre>.html`, `.png` (si hay Chromium con `playwright`; si no, la
página tiene el botón «Guardar imagen») y `.json`. `rutinas/` queda solo en esta computadora.

## Fotos y reseñas

`python3 asesora/preparar.py` trae de farmasius.com la foto, el nombre oficial y las reseñas de
cada producto del catálogo (`tienda.json` e `img/`). Se corre de nuevo si se agrega un producto
a `catalogo.json`. Sin precios.
