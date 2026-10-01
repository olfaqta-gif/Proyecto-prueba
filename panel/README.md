# Panel de Jarvis

Una página web en tu computadora para **ver a Jarvis y a sus agentes** y **conversar con él**.

Estilo "sala de mando" futurista, como el Jarvis de las películas:

- **Sala de mando (centro):** el núcleo de Jarvis y, alrededor, cada agente como un
  robot. Cuando Jarvis llama a un agente, la línea entre ellos se enciende, el robot se
  anima y dice qué está haciendo ("Leyendo la tienda farmasius.com…").
- **Canal de comunicación (izquierda):** la conversación con Jarvis. Puedes escribir o
  tocar el micrófono 🎙 y hablarle (en Chrome). Con el botón 🔊 Voz, Jarvis lee sus respuestas.
- **Pantalla de resultados (derecha):** muestra en grande la foto, el video o el plan que
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
