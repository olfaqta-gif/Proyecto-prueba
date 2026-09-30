"""Generates storyboard.html (static sketch sheet) for hubspot-explicado.

One diagram "world" drawn in every cell; each frame shows a different subset of
nodes + a camera transform, so the sheet reads as ONE diagram assembling.
Coordinates are % of the 16:9 cell. Content stays in the top ~83% (caption keep-out).
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VERSION = "v1"

# node id -> (x%, y%, label, tags, size)
NODES = {
    "crm":        (50, 42, "crm", ["contactos", "empresas", "negocios", "tickets"], "core"),
    "marketing":  (17, 42, "marketing hub", ["emails", "anuncios", "formularios"], "hub"),
    "ventas":     (83, 42, "sales hub", ["pipeline", "reuniones", "cotizaciones"], "hub"),
    "servicio":   (50, 74, "service hub", ["tickets", "chat", "ayuda"], "hub"),
    "content":    (24, 11, "content", ["web · blog"], "mini"),
    "operations": (50, 9,  "operations", ["datos"], "mini"),
    "commerce":   (76, 11, "commerce", ["cobros"], "mini"),
}

FRAGMENTS = [  # frame 1 scattered pieces: (x, y, label, rot)
    (16, 22, "correo", -6), (42, 16, "hoja de cálculo", 4), (72, 24, "chat", -3),
    (28, 42, "notas", 5), (82, 58, "facturas", -5), (88, 36, "whatsapp", 3), (56, 44, "post-it", -2),
]

def node_html(nid, active=(), dim=(), small_tags=True):
    x, y, label, tags, kind = NODES[nid]
    cls = f"node {kind}" + (" active" if nid in active else "") + (" dim" if nid in dim else "")
    tag_html = "".join(f"<span>{t}</span>" for t in tags)
    return (f'<div class="{cls}" style="left:{x}%;top:{y}%"><b>{label}</b>'
            f'<i class="tags">{tag_html}</i></div>')

def line_svg(pairs, hot=()):
    out = []
    for a, b in pairs:
        x1, y1 = NODES[a][:2]; x2, y2 = NODES[b][:2]
        cls = "hot" if (a, b) in hot or b in hot else ""
        out.append(f'<line class="{cls}" x1="{x1}" y1="{y1*0.5625}" x2="{x2}" y2="{y2*0.5625}"/>')
    return ('<svg class="wires" viewBox="0 0 100 56.25" preserveAspectRatio="none">'
            + "".join(out) + "</svg>")

def dot(x, y, label):
    return f'<div class="dot" style="left:{x}%;top:{y}%"><em>{label}</em></div>'

def world(nodes, lines, extra="", cam="", active=(), dim=(), hot=()):
    inner = line_svg(lines, hot) + "".join(node_html(n, active, dim) for n in nodes) + extra
    return f'<div class="world" style="{cam}">{inner}</div>'

HUB_LINES = [("crm", "marketing"), ("crm", "ventas"), ("crm", "servicio")]
MINI_LINES = [("crm", "content"), ("crm", "operations"), ("crm", "commerce")]

FRAMES = [
    dict(n="01", name="todo disperso", t="0–6s", seam="cut → zoom-through",
         body="".join(f'<div class="frag" style="left:{x}%;top:{y}%;transform:translate(-50%,-50%) rotate({r}deg)">{l}<u></u></div>' for x, y, l, r in FRAGMENTS)
              + '<div class="kicker k-tl">01 / el problema</div>'
              + '<div class="statement">tus clientes están <span class="o">en todas partes</span></div>',
         note="<b>Primero se mueve:</b> los fragmentos aparecen uno a uno al nombrarlos (correo · hoja · chat), cada uno con su puntito de cliente. Seam: zoom-through hacia el centro."),
    dict(n="02", name="el centro: el crm", t="6–14s", seam="zoom-through",
         body=world(["crm"], [], active=("crm",))
              + '<div class="kicker k-tl">02 / el centro</div>'
              + '<div class="caption-l">una sola ficha <span class="o">por cliente</span></div>',
         note="<b>Primero se mueve:</b> los fragmentos del 01 son absorbidos al centro y se funden en el nodo «crm»; sus 4 etiquetas aparecen al nombrarlas. El nodo ya no se mueve en todo el video."),
    dict(n="03", name="marketing hub", t="14–21s", seam="crossfade",
         body=world(["crm", "marketing"], [("crm", "marketing")], dot(33, 42, "visitante → lead"),
                    cam="transform:scale(1.3);transform-origin:30% 45%", active=("marketing",), hot=("marketing",))
              + '<div class="kicker k-tl">03 / atraer</div>',
         note="<b>Primero se mueve:</b> la cámara se acerca a la izquierda; «marketing hub» se engancha con una línea naranja. Emails · anuncios · formularios al nombrarlos; el punto «visitante» cruza la línea y se vuelve «lead»."),
    dict(n="04", name="sales hub", t="21–28s", seam="crossfade",
         body=world(["crm", "marketing", "ventas"], [("crm", "marketing"), ("crm", "ventas")],
                    dot(67, 42, "lead → cliente") + '<div class="pipe" style="left:83%;top:58%"><span>nuevo</span><span>propuesta</span><span class="o">ganado</span></div>',
                    cam="transform:scale(1.3);transform-origin:70% 45%", active=("ventas",), dim=("marketing",), hot=("ventas",))
              + '<div class="kicker k-tl">04 / vender</div>',
         note="<b>Primero se mueve:</b> la cámara pasa a la derecha; «sales hub» se engancha. El mismo punto viaja marketing → crm → ventas y avanza por 3 columnas del pipeline hasta «ganado»."),
    dict(n="05", name="service hub", t="28–36s", seam="crossfade",
         body=world(["crm", "marketing", "ventas", "servicio"], HUB_LINES,
                    dot(50, 60, "")+'<div class="kicker" style="left:53%;top:58%">ticket abierto</div>',
                    cam="transform:scale(1.12);transform-origin:50% 70%", active=("servicio",), hot=("marketing", "ventas", "servicio"))
              + '<div class="kicker k-tl">05 / cuidar</div>',
         note="<b>Primero se mueve:</b> la cámara baja; «service hub» se engancha. Se abre un ticket y en «el mismo historial» las tres líneas se encienden a la vez (callback de 03 y 04)."),
    dict(n="06", name="y además", t="36–43s", seam="crossfade",
         body=world(list(NODES), HUB_LINES + MINI_LINES, cam="transform:scale(0.96)",
                    active=("content", "operations", "commerce"), hot=("content", "operations", "commerce"))
              + '<div class="kicker k-bl">06 / más piezas</div>',
         note="<b>Primero se mueve:</b> el plano se abre un poco; content · operations · commerce se enganchan arriba de golpe, uno por palabra (regla de tres), con un «clic» cada uno."),
    dict(n="07", name="breeze, la ia", t="43–50s", seam="crossfade",
         body=world(list(NODES), HUB_LINES + MINI_LINES, cam="transform:scale(0.96)",
                    hot=tuple(NODES))
              + '<div class="breeze">breeze · ia</div>'
              + '<div class="verbs"><span>escribe</span><span>resume</span><span>responde</span></div>'
              + '<div class="kicker k-bl">07 / la ia</div>',
         note="<b>Primero se mueve:</b> un pulso naranja nace en el crm y recorre cada línea hasta todos los nodos; «breeze · ia» aparece; los 3 verbos entran al nombrarlos."),
    dict(n="08", name="así funciona hubspot", t="50–58s", seam="zoom-through (entrada)",
         body=world(list(NODES), HUB_LINES + MINI_LINES, cam="transform:scale(0.55) translateY(-30%)")
              + '<div class="final">un centro. muchas piezas.<br><span class="o">un mismo cliente.</span></div>'
              + '<div class="kicker k-br">así funciona hubspot</div>',
         note="<b>Primero se mueve:</b> alejamiento lento; el diagrama entero queda pequeño y quieto arriba. La frase entra en tres golpes. <b>Frame sostenido:</b> nada se mueve en los últimos ~2 s."),
]

CSS = """
@font-face{font-family:Barlow;font-weight:400;src:url(assets/fonts/barlow-latin-400-normal.woff2)}
@font-face{font-family:Barlow;font-weight:600;src:url(assets/fonts/barlow-latin-600-normal.woff2)}
@font-face{font-family:Barlow;font-weight:700;src:url(assets/fonts/barlow-latin-700-normal.woff2)}
@font-face{font-family:Barlow;font-weight:800;src:url(assets/fonts/barlow-latin-800-normal.woff2)}
@font-face{font-family:Barlow;font-weight:900;src:url(assets/fonts/barlow-latin-900-normal.woff2)}
@font-face{font-family:'IBM Plex Mono';font-weight:400;src:url(assets/fonts/ibm-plex-mono-latin-400-normal.woff2)}
@font-face{font-family:'IBM Plex Mono';font-weight:500;src:url(assets/fonts/ibm-plex-mono-latin-500-normal.woff2)}
:root{--navy:#213343;--navy2:#1B2A38;--o:#FF7A59;--cream:#F5F8FA;--muted:#A9B7C4;--hint:#5C7185;--border:#33475B}
*{box-sizing:border-box;margin:0;padding:0}
body{background:#0f1820;color:var(--cream);font-family:Barlow,sans-serif;padding:40px 32px}
header{max-width:1500px;margin:0 auto 28px;display:flex;align-items:end;justify-content:space-between;gap:24px;flex-wrap:wrap}
h1{font-weight:900;font-size:44px;letter-spacing:-.03em;text-transform:lowercase}
h1 small{font:500 14px 'IBM Plex Mono';color:var(--o);letter-spacing:.14em;margin-left:10px;vertical-align:middle}
.dek{color:var(--muted);font-size:17px;margin-top:6px}
.tag{font:500 12px 'IBM Plex Mono';letter-spacing:.14em;text-transform:uppercase;border:1px solid var(--border);padding:8px 12px;color:var(--muted)}
.grid{max-width:1500px;margin:0 auto;display:grid;grid-template-columns:repeat(3,1fr);gap:28px}
@media(max-width:1100px){.grid{grid-template-columns:repeat(2,1fr)}}
@media(max-width:700px){.grid{grid-template-columns:1fr}}
.cell{aspect-ratio:16/9;container-type:inline-size;background:var(--navy);position:relative;overflow:hidden;border:1px solid var(--border)}
.cell::after{content:"";position:absolute;left:0;right:0;bottom:0;height:17%;border-top:1px dashed rgba(169,183,196,.18);pointer-events:none}
.world{position:absolute;inset:0}
.wires{position:absolute;inset:0;width:100%;height:100%}
.wires line{stroke:var(--hint);stroke-width:.25}
.wires line.hot{stroke:var(--o);stroke-width:.35}
.node{position:absolute;transform:translate(-50%,-50%);text-align:center;background:var(--navy2);border:1px solid var(--border);padding:1.1cqw 1.6cqw;white-space:nowrap}
.node b{display:block;font-weight:800;font-size:2.2cqw;letter-spacing:-.02em;line-height:1}
.node .tags{display:flex;gap:.6cqw;justify-content:center;margin-top:.7cqw;font-style:normal}
.node .tags span{font:500 .8cqw 'IBM Plex Mono';letter-spacing:.12em;text-transform:uppercase;color:var(--muted)}
.node.core{background:var(--o);color:var(--navy);border:0;border-radius:50%;width:17cqw;height:17cqw;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:0}
.node.core b{font-size:4.2cqw;font-weight:900}
.node.core .tags{flex-wrap:wrap;width:12cqw}
.node.core .tags span{color:rgba(33,51,67,.75)}
.node.mini{padding:.7cqw 1.1cqw}.node.mini b{font-size:1.5cqw}.node.mini .tags span{font-size:.7cqw}
.node.active{border-color:var(--o)}
.node.hub.active b,.node.mini.active b{color:var(--o)}
.node.dim{opacity:.45}
.dot{position:absolute;width:1.4cqw;height:1.4cqw;border-radius:50%;background:var(--o);transform:translate(-50%,-50%);box-shadow:0 0 0 .5cqw rgba(255,122,89,.18)}
.dot em{position:absolute;top:1.9cqw;left:50%;transform:translateX(-50%);font:500 .8cqw 'IBM Plex Mono';letter-spacing:.12em;text-transform:uppercase;color:var(--o);white-space:nowrap;font-style:normal}
.pipe{position:absolute;transform:translate(-50%,0);display:flex;gap:.4cqw}
.pipe span{font:500 .75cqw 'IBM Plex Mono';letter-spacing:.1em;text-transform:uppercase;border-top:1px solid var(--border);padding:.5cqw .6cqw;color:var(--muted)}
.pipe span.o{color:var(--o);border-color:var(--o)}
.frag{position:absolute;font-weight:700;font-size:1.9cqw;color:var(--muted);border:1px solid var(--border);padding:.6cqw 1cqw;background:var(--navy2);white-space:nowrap}
.frag u{position:absolute;right:-.5cqw;top:-.5cqw;width:1cqw;height:1cqw;border-radius:50%;background:var(--o)}
.kicker{position:absolute;font:500 .9cqw 'IBM Plex Mono';letter-spacing:.14em;text-transform:uppercase;color:var(--o)}
.k-tl{left:5.5cqw;top:4cqw}.k-bl{left:5.5cqw;bottom:20%}.k-br{right:5.5cqw;top:4cqw}
.statement{position:absolute;left:5.5cqw;bottom:20%;font-weight:900;font-size:4.5cqw;letter-spacing:-.03em;line-height:1;max-width:60cqw}
.caption-l{position:absolute;left:5.5cqw;bottom:20%;font-weight:700;font-size:2.8cqw;letter-spacing:-.02em}
.o{color:var(--o)}
.breeze{position:absolute;left:61%;top:30%;transform:translate(-50%,-50%);font:500 1cqw 'IBM Plex Mono';letter-spacing:.14em;text-transform:uppercase;color:var(--navy);background:var(--o);padding:.4cqw .8cqw}
.verbs{position:absolute;right:5.5cqw;bottom:20%;display:flex;flex-direction:column;align-items:flex-end;font-weight:900;font-size:2.8cqw;letter-spacing:-.03em;line-height:1}
.verbs span:nth-child(2){opacity:.6}.verbs span:nth-child(3){opacity:.3}
.final{position:absolute;left:5.5cqw;bottom:20%;font-weight:900;font-size:5.2cqw;letter-spacing:-.04em;line-height:.95}
.meta{display:flex;justify-content:space-between;font:500 12px 'IBM Plex Mono';letter-spacing:.12em;text-transform:uppercase;color:var(--muted);margin-top:10px}
.meta b{color:var(--cream);font-weight:500}
.note{font-size:15px;line-height:1.45;color:var(--muted);margin-top:6px}.note b{color:var(--cream)}
.chip{display:inline-block;margin-top:8px;font:500 11px 'IBM Plex Mono';letter-spacing:.12em;text-transform:uppercase;color:var(--o);border:1px solid var(--o);padding:4px 8px}
.info{background:var(--navy);border:1px solid var(--border);padding:22px;font-size:15px;line-height:1.5;color:var(--muted)}
.info h3{font:500 12px 'IBM Plex Mono';letter-spacing:.14em;text-transform:uppercase;color:var(--o);margin-bottom:12px}
.seams{display:flex;flex-wrap:wrap;gap:6px}.seams span{border:1px solid var(--border);padding:4px 8px;font:500 11px 'IBM Plex Mono';color:var(--cream)}
.sw{display:flex;gap:8px;margin:8px 0 14px}.sw i{width:44px;height:44px;border:1px solid var(--border)}
"""

def build():
    cells = []
    for f in FRAMES:
        cells.append(f'''<article>
  <div class="cell" id="frame-{f["n"]}">{f["body"]}</div>
  <div class="meta"><b>{f["n"]} · {f["name"]}</b><span>{f["t"]}</span></div>
  <p class="note">{f["note"]}</p>
  <span class="chip">{f["seam"]}</span>
</article>''')
    seam_map = " → ".join(f"{f['n']}" for f in FRAMES)
    cells.append(f'''<article class="info"><h3>mapa de transiciones</h3>
  <div class="seams"><span>01 cut</span><span>→02 zoom-through</span><span>→03 crossfade</span><span>→04 crossfade</span><span>→05 crossfade</span><span>→06 crossfade</span><span>→07 crossfade</span><span>→08 zoom-through</span></div>
  <p style="margin-top:14px">Un solo diagrama: el nodo <b style="color:var(--cream)">crm</b> nace en 02 y no se mueve. 03–07 son el mismo escenario con la cámara moviéndose; los crossfades hacen que se lea como un plano continuo. Línea discontinua inferior = zona reservada para subtítulos.</p></article>''')
    cells.append('''<article class="info"><h3>tokens (frame.md · broadside remezclado)</h3>
  <div class="sw"><i style="background:#213343"></i><i style="background:#1B2A38"></i><i style="background:#FF7A59"></i><i style="background:#F5F8FA"></i><i style="background:#A9B7C4"></i><i style="background:#33475B"></i></div>
  <p><b style="color:var(--cream)">Barlow 900</b> en minúsculas (display) · <b style="color:var(--cream)">IBM Plex Mono</b> mayúsculas 0.14em (etiquetas). Naranja = único acento. Plano, sin sombras, líneas de 1px.</p>
  <p style="margin-top:10px"><b style="color:var(--cream)">Prohibido:</b> UI falsa de HubSpot, logos, cifras inventadas, tarjetas nuevas en cada escena (slideshow), movimiento sin significado.</p></article>''')
    html = f'''<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Storyboard · Cómo funciona HubSpot {VERSION}</title><style>{CSS}</style></head><body>
<header><div><h1>cómo funciona hubspot <small>{VERSION}</small></h1>
<p class="dek">Un diagrama que se arma pieza a pieza: el CRM en el centro y cada Hub enganchándose a él.</p></div>
<span class="tag">1920×1080 · ~58 s · 8 escenas · voz es</span></header>
<main class="grid">{"".join(cells)}</main></body></html>'''
    (ROOT / "storyboard.html").write_text(html, encoding="utf-8")

if __name__ == "__main__":
    build()
