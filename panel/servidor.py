#!/usr/bin/env python3
"""Panel de Isa: una página en tu computadora para ver a Isa y sus agentes y
conversar con ella.

Uso (desde la carpeta del proyecto):
    python3 panel/servidor.py            → abre http://localhost:8765 en el navegador
    python3 panel/servidor.py --puerto 9000 --sin-navegador

Por detrás usa Claude Code (el programa `claude`) con tu propia cuenta, así que no hace
falta ninguna clave extra. Los agentes se leen solos de `.claude/agents/` y las
habilidades de `.claude/skills/`: si se crea un agente nuevo, aparece al recargar.
Solo Python estándar.
"""
import argparse
import hashlib
import json
import mimetypes
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

RAIZ = Path(__file__).resolve().parent.parent
PANEL = Path(__file__).resolve().parent
AGENTES = RAIZ / ".claude" / "agents"
HABILIDADES = RAIZ / ".claude" / "skills"
JEFE = "isa"

# Herramientas que Isa y sus agentes pueden usar sin pedir permiso en la terminal
# (en la página no hay terminal donde aprobarlas). Se puede cambiar en panel/config.json.
CONFIG_BASE = {
    "herramientas": [
        "Agent", "Task", "Skill", "Read", "Glob", "Grep", "Write", "Edit",
        "TodoWrite", "WebSearch", "WebFetch",
        "Bash(python3:*)", "Bash(python:*)", "Bash(node:*)", "Bash(ls:*)",
        "Bash(cat:*)", "Bash(cp:*)", "Bash(mkdir:*)", "Bash(ffmpeg:*)",
        "Bash(ffprobe:*)", "Bash(pip:*)", "Bash(npm:*)", "Bash(npx:*)",
        "Bash(head:*)", "Bash(tail:*)", "Bash(wc:*)", "Bash(find:*)", "Bash(du:*)",
        "Bash(date:*)",
    ],
    "modelo": "",
}

# Color de la luz de cada robot (el panel es azul oscuro).
COLORES = ["#5be3b0", "#ffc15e", "#ff8a7a", "#7fb2ff", "#a99bff", "#4cc9ff",
           "#f59bd0", "#c6f36b"]

# Proceso de Claude que está corriendo ahora (solo uno a la vez).
_actual = {"proceso": None}
_candado = threading.Lock()


def leer_config():
    config = dict(CONFIG_BASE)
    archivo = PANEL / "config.json"
    if archivo.exists():
        try:
            config.update(json.loads(archivo.read_text(encoding="utf-8")))
        except (OSError, ValueError) as e:
            print(f"Aviso: no pude leer panel/config.json ({e}); uso lo de siempre.")
    return config


def leer_ficha(archivo):
    """Separa el encabezado (--- nombre: ... ---) del texto de un agente o habilidad."""
    texto = archivo.read_text(encoding="utf-8")
    datos, cuerpo = {}, texto
    if texto.startswith("---"):
        partes = texto.split("---", 2)
        if len(partes) == 3:
            for linea in partes[1].splitlines():
                if ":" in linea:
                    clave, valor = linea.split(":", 1)
                    datos[clave.strip()] = valor.strip()
            cuerpo = partes[2].strip()
    return datos, cuerpo


def icono_para(nombre, texto):
    for t in (nombre.lower(), texto.lower()):  # primero el nombre, luego la descripción
        icono = _icono_en(t)
        if icono:
            return icono
    return "🤖"


def _icono_en(t):
    for palabras, icono in [
        (("scraper", "busca", "investig", "lector"), "🔎"),
        (("estrateg", "plan", "calendario"), "🗓️"),
        (("educa", "profe", "enseñ"), "🎓"),
        (("contenido", "anuncio", "video", "creador"), "🎬"),
        (("cliente", "crm", "pedido", "venta"), "🤝"),
        (("foto", "imagen", "diseño"), "🎨"),
        (("mensaje", "whatsapp", "correo"), "💬"),
        (("dato", "análisis", "analiz", "número"), "📊"),
    ]:
        if any(p in t for p in palabras):
            return icono
    return None


CARAS = 4  # cuántas caras de robot dibuja la página


def _libre(nombre, opciones, usados):
    """Elige siempre la misma opción para un agente (según su nombre), sin repetir."""
    inicio = int(hashlib.md5(nombre.encode("utf-8")).hexdigest(), 16) % len(opciones)
    for k in range(len(opciones)):
        opcion = opciones[(inicio + k) % len(opciones)]
        if opcion not in usados or len(usados) >= len(opciones):
            usados.add(opcion)
            return opcion
    return opciones[inicio]


def equipo():
    """Isa + todos los agentes y habilidades que existan ahora mismo en las carpetas."""
    jefe = {"nombre": "Isa", "id": JEFE, "icono": "🧠", "color": "#4cc9ff",
            "rol": "Jefa de operaciones",
            "que_hace": "La jefa. Conversa contigo y decide qué agente trabaja."}
    agentes, habilidades = [], []
    usados_color, usados_cara = set(), set()
    if AGENTES.is_dir():
        for archivo in sorted(AGENTES.glob("*.md")):
            datos, _ = leer_ficha(archivo)
            nombre = datos.get("name", archivo.stem)
            descripcion = datos.get("description", "")
            agentes.append({
                "id": nombre,
                "nombre": datos.get("apodo") or nombre.replace("-", " ").title(),
                "rol": descripcion.split(".")[0],
                "icono": datos.get("icono") or icono_para(nombre, descripcion),
                "color": datos.get("color-panel") or _libre(nombre, COLORES, usados_color),
                "cara": _libre(nombre, list(range(CARAS)), usados_cara),
                "que_hace": descripcion,
                "herramientas": datos.get("tools", ""),
                "archivo": str(archivo.relative_to(RAIZ)),
            })
    if HABILIDADES.is_dir():
        for archivo in sorted(HABILIDADES.glob("*/SKILL.md")):
            datos, _ = leer_ficha(archivo)
            nombre = datos.get("name", archivo.parent.name)
            if nombre == JEFE:
                continue
            habilidades.append({"id": nombre, "nombre": nombre.replace("-", " ").capitalize(),
                                "que_hace": datos.get("description", "")})
    return {"jefe": jefe, "agentes": agentes, "habilidades": habilidades}


def trabajos_recientes(limite=24):
    """Lo último que produjeron los agentes: videos, planes y vitrinas."""
    patrones = [
        ("agente-contenido/salida", "**/*.mp4", "Video"),
        ("planificador/planes", "*.html", "Plan"),
        ("lector-farmasi/salida", "vitrina.html", "Vitrina"),
        ("lector-farmasi/salida", "*/producto.jpg", "Producto"),
        ("agente-contenido/salida", "**/previa*.jpg", "Previa"),
        ("reunion/actas", "*.html", "Reunión"),
    ]
    encontrados = []
    for carpeta, patron, tipo in patrones:
        base = RAIZ / carpeta
        if base.is_dir():
            for f in base.glob(patron):
                encontrados.append((f.stat().st_mtime, tipo, f))
    encontrados.sort(reverse=True)
    return [{"tipo": tipo, "ruta": str(f.relative_to(RAIZ)), "fecha": fecha}
            for fecha, tipo, f in encontrados[:limite]]


def ultima_reunion():
    """Notas de la última reunión de equipo, para que cada robot muestre la suya."""
    actas = sorted((RAIZ / "reunion" / "actas").glob("*.json"))
    if not actas:
        return {}
    try:
        acta = json.loads(actas[-1].read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return {"fecha": acta.get("fecha"), "nota_equipo": acta.get("nota_equipo"),
            "informe": str(actas[-1].with_suffix(".html").relative_to(RAIZ)),
            "agentes": {k: {"nota": a.get("nota"), "antes": a.get("nota_anterior")}
                        for k, a in acta.get("agentes", {}).items()}}


def instrucciones_isa():
    archivo = HABILIDADES / JEFE / "SKILL.md"
    cuerpo = leer_ficha(archivo)[1] if archivo.exists() else "Eres Isa."
    return cuerpo + """

## Estás en el panel de Isa
Isabella te escribe desde una página web (el panel), no desde la terminal: no ve comandos
ni puede aprobar permisos. Escribe solo lo que ella necesita leer, en español sencillo.
Cuando entregues un archivo (video, plan, vitrina, foto), escribe su ruta completa desde
la carpeta del proyecto, por ejemplo `agente-contenido/salida/serum/favorito/anuncio-9x16.mp4`:
el panel la convierte en un enlace que abre el archivo.
"""


def ruta_segura(relativa):
    destino = (RAIZ / relativa).resolve()
    if RAIZ not in destino.parents and destino != RAIZ:
        return None
    if ".git" in destino.parts or not destino.is_file():
        return None
    return destino


def resumen_de_herramienta(nombre, entrada):
    """Una línea en español de lo que está haciendo un agente."""
    if nombre == "Bash":
        cmd = entrada.get("command", "")
        if "leer.py" in cmd:
            return "Leyendo la tienda farmasius.com"
        if "generar.py" in cmd:
            return "Fabricando el video"
        if "analizar.py" in cmd:
            return "Analizando el catálogo"
        if "planificar.py" in cmd:
            return "Revisando el plan"
        if "revisar.py reunir" in cmd:
            return "Revisando el trabajo de todo el equipo"
        if "revisar.py" in cmd:
            return "Anotando los acuerdos de la reunión"
        return "Ejecutando una tarea"
    return {
        "Read": "Leyendo un archivo", "Write": "Escribiendo un archivo",
        "Edit": "Corrigiendo un archivo", "Glob": "Buscando archivos",
        "Grep": "Buscando dentro de archivos", "WebSearch": "Buscando en internet",
        "WebFetch": "Leyendo una página web", "Skill": "Usando una habilidad",
        "TodoWrite": "Anotando los pasos",
    }.get(nombre, "Trabajando")


def conversar(mensaje, sesion, enviar):
    """Corre Claude Code con el mensaje y va mandando eventos a la página."""
    claude = shutil.which("claude")
    if not claude:
        enviar({"tipo": "error", "texto": "No encontré Claude Code en esta computadora. "
                "Instálalo (ver panel/README.md) y vuelve a abrir el panel."})
        return
    config = leer_config()
    comando = [claude, "-p", mensaje, "--output-format", "stream-json", "--verbose",
               "--include-partial-messages",
               "--append-system-prompt", instrucciones_isa(),
               "--allowedTools", ",".join(config["herramientas"])]
    if config.get("modelo"):
        comando += ["--model", config["modelo"]]
    if sesion:
        comando += ["--resume", sesion]

    errores = tempfile.TemporaryFile(mode="w+", encoding="utf-8")
    proceso = subprocess.Popen(comando, cwd=RAIZ, stdout=subprocess.PIPE, stderr=errores,
                               stdin=subprocess.DEVNULL, text=True, encoding="utf-8", bufsize=1)
    with _candado:
        _actual["proceso"] = proceso
    llamadas = {}   # id de la llamada → agente que está trabajando
    en_fondo = set()  # llamadas que corren aparte (su resultado llega después)

    def termina(id_llamada):
        agente = llamadas.pop(id_llamada, None)
        en_fondo.discard(id_llamada)
        if agente:
            enviar({"tipo": "agente_termina", "agente": agente})

    try:
        for linea in proceso.stdout:
            try:
                ev = json.loads(linea)
            except ValueError:
                continue
            tipo, sub = ev.get("type"), ev.get("subtype")
            padre = ev.get("parent_tool_use_id")
            if tipo == "system":
                id_llamada = ev.get("tool_use_id")
                if sub == "init":
                    enviar({"tipo": "sesion", "sesion": ev.get("session_id")})
                elif sub == "task_started" and ev.get("is_backgrounded"):
                    en_fondo.add(id_llamada)
                elif sub == "task_progress" and id_llamada in llamadas:
                    enviar({"tipo": "agente_hace", "agente": llamadas[id_llamada],
                            "texto": resumen_de_herramienta(ev.get("last_tool_name"),
                                                            {"command": ev.get("description", "")})})
                elif sub == "task_notification":
                    termina(id_llamada)
            elif tipo == "stream_event" and not padre:
                d = ev.get("event", {})
                if d.get("type") == "content_block_delta" and d["delta"].get("type") == "text_delta":
                    enviar({"tipo": "texto", "texto": d["delta"]["text"]})
                elif d.get("type") == "message_start":
                    enviar({"tipo": "corte"})
            elif tipo == "assistant":
                for bloque in ev.get("message", {}).get("content", []):
                    if bloque.get("type") != "tool_use":
                        continue
                    nombre, entrada = bloque.get("name"), bloque.get("input", {})
                    if nombre in ("Agent", "Task"):
                        agente = entrada.get("subagent_type", "general-purpose")
                        llamadas[bloque["id"]] = agente
                        enviar({"tipo": "agente_empieza", "agente": agente,
                                "tarea": entrada.get("description", "")})
                    elif padre in llamadas:
                        enviar({"tipo": "agente_hace", "agente": llamadas[padre],
                                "texto": resumen_de_herramienta(nombre, entrada)})
                    elif not padre:
                        if nombre == "Bash" and "reunion/revisar.py reunir" in entrada.get("command", ""):
                            enviar({"tipo": "reunion_empieza"})
                        enviar({"tipo": "isa_hace",
                                "texto": resumen_de_herramienta(nombre, entrada)})
            elif tipo == "user" and not padre:
                for bloque in ev.get("message", {}).get("content", []) or []:
                    if isinstance(bloque, dict) and bloque.get("type") == "tool_result":
                        if bloque.get("tool_use_id") not in en_fondo:
                            termina(bloque.get("tool_use_id"))
            elif tipo == "result":
                if ev.get("is_error"):
                    enviar({"tipo": "error", "texto": str(ev.get("result") or "Algo falló.")})
                enviar({"tipo": "sesion", "sesion": ev.get("session_id")})
        proceso.wait()
        if proceso.returncode and proceso.returncode > 0:
            errores.seek(0)
            error = errores.read().strip()
            if error:
                enviar({"tipo": "error", "texto": traducir_error(error)})
    finally:
        for id_llamada in list(llamadas):
            termina(id_llamada)
        errores.close()
        with _candado:
            _actual["proceso"] = None
        enviar({"tipo": "fin"})


def traducir_error(error):
    e = error.lower()
    if "login" in e or "auth" in e or "api key" in e:
        return ("Claude Code no tiene tu cuenta abierta. Abre una terminal, escribe "
                "`claude`, entra con tu cuenta y vuelve a intentar.\n\n(" + error[:300] + ")")
    return error[:600]


class Manejador(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def responder(self, codigo, cuerpo, tipo="application/json; charset=utf-8"):
        datos = cuerpo if isinstance(cuerpo, bytes) else cuerpo.encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(datos)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(datos)

    def do_GET(self):
        url = urlparse(self.path)
        if url.path in ("/", "/index.html"):
            self.responder(200, (PANEL / "pagina.html").read_bytes(), "text/html; charset=utf-8")
        elif url.path.startswith("/panel/") and url.path.endswith(".js"):
            # Programas de la página (la oficina 3D y su librería), solo dentro de panel/
            destino = (PANEL / url.path[len("/panel/"):]).resolve()
            if PANEL in destino.parents and destino.is_file():
                self.responder(200, destino.read_bytes(), "text/javascript; charset=utf-8")
            else:
                self.responder(404, "{}")
        elif url.path == "/api/equipo":
            self.responder(200, json.dumps(equipo(), ensure_ascii=False))
        elif url.path == "/api/reunion":
            self.responder(200, json.dumps(ultima_reunion(), ensure_ascii=False))
        elif url.path == "/api/trabajos":
            self.responder(200, json.dumps(trabajos_recientes(), ensure_ascii=False))
        elif url.path == "/archivo":
            ruta = ruta_segura(parse_qs(url.query).get("ruta", [""])[0])
            if not ruta:
                self.responder(404, "No encontré ese archivo.", "text/plain; charset=utf-8")
                return
            tipo = mimetypes.guess_type(ruta.name)[0] or "application/octet-stream"
            if tipo.startswith("text/"):
                tipo += "; charset=utf-8"
            self.responder(200, ruta.read_bytes(), tipo)
        else:
            self.responder(404, "{}")

    def do_POST(self):
        url = urlparse(self.path)
        largo = int(self.headers.get("Content-Length") or 0)
        try:
            pedido = json.loads(self.rfile.read(largo) or b"{}")
        except ValueError:
            pedido = {}
        if url.path == "/api/parar":
            with _candado:
                proceso = _actual["proceso"]
            if proceso:
                proceso.terminate()
            self.responder(200, "{}")
            return
        if url.path != "/api/conversar":
            self.responder(404, "{}")
            return
        mensaje = (pedido.get("mensaje") or "").strip()
        if not mensaje:
            self.responder(400, json.dumps({"error": "Mensaje vacío"}))
            return
        with _candado:
            ocupado = _actual["proceso"] is not None
        if ocupado:
            self.responder(409, json.dumps({"error": "Isa todavía está trabajando."}))
            return
        self.send_response(200)
        self.send_header("Content-Type", "application/x-ndjson; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()

        def enviar(evento):
            try:
                self.wfile.write((json.dumps(evento, ensure_ascii=False) + "\n").encode("utf-8"))
                self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError):
                pass

        conversar(mensaje, pedido.get("sesion"), enviar)


def main():
    p = argparse.ArgumentParser(description="Panel de Isa")
    p.add_argument("--puerto", type=int, default=8765)
    p.add_argument("--sin-navegador", action="store_true")
    a = p.parse_args()
    servidor = ThreadingHTTPServer(("127.0.0.1", a.puerto), Manejador)
    direccion = f"http://localhost:{a.puerto}"
    print(f"Panel de Isa listo en {direccion}")
    print("Deja esta ventana abierta mientras lo usas. Para cerrarlo: Ctrl+C.")
    if not shutil.which("claude"):
        print("Aviso: no encontré Claude Code (el programa `claude`). Ver panel/README.md.")
    if not a.sin_navegador:
        threading.Timer(1.0, lambda: webbrowser.open(direccion)).start()
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nPanel cerrado.")
        sys.exit(0)


if __name__ == "__main__":
    main()
