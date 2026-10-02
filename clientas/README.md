# Libreta de clientas

La lista de clientas de Isabella: quién le compra, qué compró cada una y **a quién
escribirle hoy**. Se abre en el panel de Isa con el botón **«Clientas»**.

## Qué tiene

- **Para hoy:** tarjetas con lo que hay que hacer, cada una con el mensaje ya escrito
  (se puede cambiar antes de enviarlo):
  - 🔁 **Se le acaba:** a una clienta se le está terminando lo que compró (una semana antes).
    La libreta calcula cuánto le dura cada producto (té 30 días, sérum 45, crema 60,
    máscara de pestañas 90, labial 120…); al anotar el pedido se puede cambiar.
  - 🎂 **Cumpleaños** de la semana.
  - 📦 **Por entregar** (y si falta cobrar).
  - 💬 **¿Cómo le fue?** unos días después de recibir su pedido; si le encantó, pídele una foto
    o un audio para tus redes.
  - 📌 **Recordatorios** que te anotaste ("escribirle el viernes").
  - 👋 **Sin respuesta:** preguntó y no volvió a escribir en 3 días (2 veces como máximo).
  - 📝 **Conócela:** ya compró y a su ficha le falta el cumpleaños, la piel o la ciudad.
  
  «WhatsApp» abre el chat con el mensaje listo; en Instagram, TikTok o Facebook copia el
  mensaje y abre su chat para que solo lo pegues. «Hecho ✓» la quita de la lista.
- **Tablero:** cada clienta en su paso: Preguntó → Interesada → Pidió → Ya lo tiene →
  Clienta fiel. Se arrastran de una columna a otra (o se cambia en su ficha).
- **Clientas:** una tarjeta por clienta. Al tocarla se abre su ficha: datos, piel, cumpleaños,
  pedidos, historial y notas.
- **Pedidos:** todos los pedidos con foto de los productos; se marcan pagados y entregados con un toque.
- **Números:** cuántas hay en cada paso, lo que más te compran y los pedidos por mes.

Los botones **＋ Clienta** y **＋ Pedido** están arriba. Al anotar un pedido, la clienta
pasa sola a "Pidió" (o a "Clienta fiel" si ya había comprado antes).

## Cómo se llena la ficha (también en el botón «¿Cómo funciona?»)

| Cuándo | Qué datos | Quién los pone |
|---|---|---|
| 1. Alguien te escribe | nombre (o @usuario), red, usuario o teléfono, qué preguntó | el agente de comunidad, al leer las capturas de tus mensajes; o Isabella con «＋ Clienta» |
| 2. Te compra | qué compró, si pagó, cuándo lo recibió | Isabella le cuenta a Isa la venta, o «＋ Pedido» y luego «Entregar» |
| 3. Para conocerla (opcional) | cumpleaños, tipo de piel, ciudad | después de su primera compra aparece «Conócela» con el mensaje para preguntarle; lo que conteste se pone con «Editar» o se le cuenta a Isa |

Solo el paso 1 es obligatorio (nombre y por dónde escribirle). Sin el paso 2 no hay avisos de
"se le acaba"; sin el cumpleaños no hay aviso de cumpleaños. Para empezar con las clientas
que Isabella ya tiene, se le pasa a Isa una foto del cuaderno, capturas o la lista escrita.

**Los pasos se mueven solos:** Preguntó (escribió con una pregunta) → Interesada (dijo que lo
quiere) → Pidió (al anotar un pedido) → Ya lo tiene (al entregar el primero) → Clienta fiel
(segunda compra). **En pausa:** no contestó a 2 mensajes seguidos (o Isabella la pone ahí);
si vuelve a escribir, el agente de comunidad la regresa.

## Para Isa y los agentes (`libreta.py`, solo Python estándar)

```
python3 clientas/libreta.py hoy                      # lo que hay que hacer hoy
python3 clientas/libreta.py agregar --nombre "Carla" --usuario carla.m --red instagram --nota "..."
python3 clientas/libreta.py pedido "Carla" --producto "Vitamin C Glow Serum" --pagado [--entregado]
python3 clientas/libreta.py entregado p3
python3 clientas/libreta.py nota|etapa|seguimiento|hecho|lista|buscar|resumen ...
python3 clientas/libreta.py ventas-csv                # le pasa al estratega lo que más se vende
python3 clientas/libreta.py pagina                    # copia para mirar sin el panel (solo lectura)
python3 clientas/libreta.py demo                      # libreta inventada en datos/demo.json para probar
```

## Privacidad

Los datos viven en `clientas/datos/libreta.json`, **solo en esta computadora**: no se suben
al repositorio ni a internet. Para tener una copia de respaldo, copia esa carpeta.
Los precios los pone Isabella (el total de cada pedido es opcional).
