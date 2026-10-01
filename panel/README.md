# Panel de Jarvis

Una página web en tu computadora para **ver a Jarvis y a sus agentes** y **conversar con él**.

- A la izquierda ves a Jarvis, a cada agente y lo último que hicieron (videos, planes,
  vitrinas). Cuando un agente está trabajando, su tarjeta se pinta y la luz se pone verde.
- A la derecha conversas con Jarvis como en un chat. Las fotos y videos que te entrega
  se ven ahí mismo.
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
