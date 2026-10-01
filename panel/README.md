# Panel de Jarvis

Una página web en tu computadora para **ver a Jarvis y a sus agentes** y **conversar con él**.

La oficina de Jarvis, en azul:

- **La oficina (centro):** cada agente es un robot en su escritorio. Cuando Jarvis lo llama,
  el robot va flotando a la mesa de reuniones, bajo el holograma de Jarvis, y un globito
  dice qué está haciendo ("Leyendo la tienda farmasius.com…"). Arriba, la "Misión en curso"
  muestra el pedido, el tiempo y los pasos. Al terminar, el resultado aparece sobre la mesa
  y el robot vuelve a su escritorio.
- **Conversación (izquierda):** la conversación con Jarvis. Puedes escribir o
  tocar el micrófono 🎙 y hablarle (en Chrome). Con el botón 🔊 Voz, Jarvis lee sus respuestas.
- **Visor (derecha):** muestra en grande la foto, el video o el plan que
  Jarvis te entrega. Abajo, el archivo con todo lo que el equipo ha producido.
- Los agentes se leen solos de `.claude/agents/`: si se crea uno nuevo, aparece en el
  panel sin tocar nada.

## Qué necesitas (una sola vez)

1. **Claude Code** instalado y con tu cuenta abierta. En una terminal:
   `claude` → entra con tu cuenta de Claude → ciérralo. El panel usa esa misma cuenta,
   así que no necesitas ninguna clave extra.
2. **Python 3** (en Mac ya viene; en Windows se instala desde python.org).
3. Esta carpeta del proyecto descargada en tu computadora.

## Cómo abrirlo

- **Windows:** doble clic en `panel/abrir-panel.bat`.
- **Mac:** doble clic en `panel/abrir-panel.command`.
- **Cualquiera:** desde la carpeta del proyecto, `python3 panel/servidor.py`.

Se abre solo en el navegador (http://localhost:8765). Deja abierta la ventanita negra
mientras lo usas; para cerrar el panel, ciérrala.

## Bueno saber

- El panel solo funciona en tu computadora: nadie más puede entrar.
- La conversación se recuerda aunque cierres la página. "Nueva conversación" empieza de cero.
- Jarvis y sus agentes pueden usar, sin preguntarte, las herramientas de la lista
  `herramientas` en `servidor.py` (correr los programas del proyecto, leer y escribir
  archivos, buscar en internet). Para cambiarla, crea `panel/config.json` con
  `{"herramientas": [...]}`. Con `{"modelo": "..."}` eliges el modelo.
