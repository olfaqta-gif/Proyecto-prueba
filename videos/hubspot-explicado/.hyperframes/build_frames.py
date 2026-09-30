"""Builds compositions/frames/NN-*.html for hubspot-explicado.

All 8 frames share ONE diagram world (same coordinates as the confirmed sketch,
storyboard.html / build_storyboard.py) so the video reads as one diagram assembling.
Cue times (CUES) are estimates paced to the voiceover; when real TTS word timings
exist, update CUES + DUR and re-run — nothing else changes.

Seek-safety: one paused GSAP timeline per frame, fromTo entrances only, no CSS
transitions/keyframes, no randomness, no repeat.
"""
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "compositions" / "frames"
W, H = 1920, 1080

C = dict(navy="#213343", navy2="#1B2A38", o="#FF7A59", cream="#F5F8FA",
         muted="#A9B7C4", hint="#5C7185", border="#33475B", ink75="rgba(33,51,67,0.75)")

# ---- the shared world (percent of canvas, identical to the sketch) ----
NODES = {
    "crm":        (50, 42, "crm", ["contactos", "empresas", "negocios", "tickets"], "core"),
    "marketing":  (17, 42, "marketing hub", ["emails", "anuncios", "formularios"], "hub"),
    "ventas":     (83, 42, "sales hub", ["pipeline", "reuniones", "cotizaciones"], "hub"),
    "servicio":   (50, 74, "service hub", ["tickets", "chat", "ayuda"], "hub"),
    "content":    (24, 11, "content", ["web · blog"], "mini"),
    "operations": (50, 9,  "operations", ["datos"], "mini"),
    "commerce":   (76, 11, "commerce", ["cobros"], "mini"),
}
HUBS = ["marketing", "ventas", "servicio"]
MINIS = ["content", "operations", "commerce"]

def px(nid):
    x, y = NODES[nid][:2]
    return x * W / 100, y * H / 100

def wire_len(nid):
    (x1, y1), (x2, y2) = px("crm"), px(nid)
    return round(math.hypot(x2 - x1, y2 - y1), 1)

# camera states: (x, y, scale) with transform-origin 0 0
def cam(origin_pct=None, s=1.0, extra_y=0.0):
    if origin_pct is None:
        return (0.0, 0.0, 1.0)
    ox, oy = origin_pct[0] * W / 100, origin_pct[1] * H / 100
    return (round(ox * (1 - s), 2), round(oy * (1 - s) + extra_y, 2), s)

CAM = {
    "full": cam(),
    "left": cam((27, 45), 1.3),
    "right": cam((73, 45), 1.3),
    "low": cam((50, 70), 1.12),
    "wide": cam((50, 50), 0.96),
    "emblem": cam((50, 50), 0.55, extra_y=-0.30 * H * 0.55),
}

DUR = {"01": 6, "02": 8, "03": 7, "04": 7, "05": 8, "06": 7, "07": 7, "08": 8}

FRAGMENTS = [  # frame 01/02 scattered pieces: (x%, y%, label, rot)
    (16, 22, "correo", -6), (42, 16, "hoja de cálculo", 4), (72, 24, "chat", -3),
    (28, 42, "notas", 5), (82, 58, "facturas", -5), (88, 36, "whatsapp", 3), (56, 44, "post-it", -2),
]

FONT_FACES = "\n".join(
    f"@font-face{{font-family:'Barlow';font-weight:{w};font-style:normal;src:url('assets/fonts/barlow-latin-{w}-normal.woff2') format('woff2')}}"
    for w in (400, 600, 700, 800, 900)
) + "\n" + "\n".join(
    f"@font-face{{font-family:'IBM Plex Mono';font-weight:{w};font-style:normal;src:url('assets/fonts/ibm-plex-mono-latin-{w}-normal.woff2') format('woff2')}}"
    for w in (400, 500)
)

def css(fid):
    p = f"f{fid}"
    return f"""
{FONT_FACES}
#root{{position:absolute;inset:0;width:{W}px;height:{H}px;overflow:hidden;container-type:size;font-family:'Barlow',sans-serif;color:{C['cream']}}}
.{p}-bg{{position:absolute;inset:0;background-color:{C['navy']};background-image:linear-gradient(rgba(51,71,91,.28) 1px,transparent 1px),linear-gradient(90deg,rgba(51,71,91,.28) 1px,transparent 1px);background-size:6cqw 6cqw;background-position:center}}
.{p}-cam{{position:absolute;inset:0}}
.{p}-world{{position:absolute;left:0;top:0;width:{W}px;height:{H}px;transform-origin:0 0;will-change:transform}}
.{p}-wires{{position:absolute;left:0;top:0;width:{W}px;height:{H}px;overflow:visible}}
.{p}-wires line{{fill:none;stroke-linecap:butt}}
.{p}-nw{{position:absolute;width:0;height:0}}
.{p}-node{{position:absolute;left:0;top:0;transform:translate(-50%,-50%);}}
.{p}-in{{background:{C['navy2']};border:1px solid {C['border']};padding:1.1cqw 1.6cqw;text-align:center;white-space:nowrap}}
.{p}-in b{{display:block;font-weight:800;font-size:2.2cqw;letter-spacing:-.02em;line-height:1;text-transform:lowercase}}
.{p}-tags{{display:flex;gap:.7cqw;justify-content:center;margin-top:.8cqw}}
.{p}-tags span{{display:inline-block;font:500 .85cqw 'IBM Plex Mono',monospace;letter-spacing:.12em;text-transform:uppercase;color:{C['muted']}}}
.{p}-core{{width:17cqw;height:17cqw;border-radius:50%;background:{C['o']};color:{C['navy']};display:flex;flex-direction:column;align-items:center;justify-content:center}}
.{p}-core b{{font-weight:900;font-size:4.4cqw;letter-spacing:-.04em;line-height:1}}
.{p}-core .{p}-tags{{flex-wrap:wrap;width:12.5cqw;row-gap:.35cqw;column-gap:.9cqw}}
.{p}-core .{p}-tags span{{color:{C['navy']};font-size:.95cqw}}
.{p}-mini{{padding:.7cqw 1.1cqw}} .{p}-mini b{{font-size:1.6cqw}} .{p}-mini .{p}-tags span{{font-size:.8cqw}}
.{p}-act{{border-color:{C['o']}}} .{p}-act b{{color:{C['o']}}}
.{p}-dot{{position:absolute;left:0;top:0;width:0;height:0}}
.{p}-dot i{{position:absolute;left:-.8cqw;top:-.8cqw;width:1.6cqw;height:1.6cqw;border-radius:50%;background:{C['o']};box-shadow:0 0 0 .55cqw rgba(255,122,89,.2)}}
.{p}-dot em{{position:absolute;left:0;top:1.4cqw;transform:translateX(-50%);font:500 .95cqw 'IBM Plex Mono',monospace;letter-spacing:.12em;text-transform:uppercase;color:{C['o']};white-space:nowrap;font-style:normal}}
.{p}-dot em span{{position:absolute;left:50%;top:0;transform:translateX(-50%)}}
.{p}-kicker{{position:absolute;font:500 1cqw 'IBM Plex Mono',monospace;letter-spacing:.14em;text-transform:uppercase;color:{C['o']}}}
.{p}-ov{{position:absolute;inset:0}}
.{p}-o{{color:{C['o']}}}
.{p}-w{{display:inline-block;white-space:pre}}
"""

# ---------- markup helpers ----------
def node(fid, nid, cls_extra=""):
    x, y, label, tags, kind = NODES[nid]
    p = f"f{fid}"
    X, Y = px(nid)
    inner_cls = {"core": f"{p}-core", "hub": f"{p}-in", "mini": f"{p}-in {p}-mini"}[kind]
    tag_html = "".join(f'<span id="{p}-{nid}-t{i}">{t}</span>' for i, t in enumerate(tags))
    return (f'<div class="{p}-nw" style="left:{X:.1f}px;top:{Y:.1f}px"><div class="{p}-node">'
            f'<div id="{p}-{nid}" class="{inner_cls} {cls_extra}"><b id="{p}-{nid}-n">{label}</b>'
            f'<div class="{p}-tags">{tag_html}</div></div></div></div>')

def wires(fid, nids, hot=(), pulse=()):
    """base (hint) lines for nids; orange overlay lines for hot; dash pulse lines for pulse."""
    p = f"f{fid}"
    cx, cy = px("crm")
    out = []
    for n in nids:
        X, Y = px(n); L = wire_len(n)
        out.append(f'<line id="{p}-w-{n}" x1="{cx:.1f}" y1="{cy:.1f}" x2="{X:.1f}" y2="{Y:.1f}" stroke="{C["hint"]}" stroke-width="2" stroke-dasharray="{L}" stroke-dashoffset="0"/>')
    for n in hot:
        X, Y = px(n); L = wire_len(n)
        out.append(f'<line id="{p}-h-{n}" x1="{cx:.1f}" y1="{cy:.1f}" x2="{X:.1f}" y2="{Y:.1f}" stroke="{C["o"]}" stroke-width="3" stroke-dasharray="{L}" stroke-dashoffset="0"/>')
    for n in pulse:
        X, Y = px(n); L = wire_len(n)
        out.append(f'<line id="{p}-p-{n}" x1="{cx:.1f}" y1="{cy:.1f}" x2="{X:.1f}" y2="{Y:.1f}" stroke="{C["o"]}" stroke-width="5" stroke-dasharray="90 {L + 200}" stroke-dashoffset="90"/>')
    return f'<svg class="{p}-wires" viewBox="0 0 {W} {H}">{"".join(out)}</svg>'

def dot(fid, labels, x, y):
    p = f"f{fid}"
    spans = "".join(f'<span id="{p}-dl{i}" data-layout-allow-overlap>{l}</span>' for i, l in enumerate(labels))
    return f'<div id="{p}-dot" class="{p}-dot" data-layout-allow-overlap style="transform:translate({x}px,{y}px)"><i></i><em>{spans}</em></div>'

def words(fid, key, text_parts):
    """text_parts: list of (text, is_orange). Returns spans with ids f..-key-i."""
    p = f"f{fid}"
    out = []
    for i, (t, o) in enumerate(text_parts):
        cls = f"{p}-w" + (f" {p}-o" if o else "")
        out.append(f'<span id="{p}-{key}{i}" class="{cls}">{t}</span>')
    return "".join(out)

# ---------- JS helpers (emit timeline lines) ----------
def J_appear(sel, t, d=0.6, rise=12):
    return f'tl.fromTo("{sel}",{{opacity:0,y:{rise}}},{{opacity:1,y:0,duration:{d},ease:"power3.out"}},{t});'

def J_fade(sel, t, d=0.5, a=0, b=1):
    return f'tl.fromTo("{sel}",{{opacity:{a}}},{{opacity:{b},duration:{d},ease:"power2.out"}},{t});'

def J_draw(sel, L, t, d=0.7):
    return f'tl.fromTo("{sel}",{{attr:{{"stroke-dashoffset":{L}}}}},{{attr:{{"stroke-dashoffset":0}},duration:{d},ease:"power3.inOut"}},{t});'

def J_pulse(sel, L, t, d=1.3):
    return f'tl.fromTo("{sel}",{{attr:{{"stroke-dashoffset":90}}}},{{attr:{{"stroke-dashoffset":{-L}}},duration:{d},ease:"power2.inOut"}},{t});'

def J_cam(sel, a, b, t, d, ease="power3.inOut"):
    return (f'tl.fromTo("{sel}",{{x:{a[0]},y:{a[1]},scale:{a[2]}}},'
            f'{{x:{b[0]},y:{b[1]},scale:{b[2]},duration:{d},ease:"{ease}"}},{t});')

def J_move(sel, a, b, t, d, ease="power2.inOut"):
    return f'tl.fromTo("{sel}",{{x:{a[0]},y:{a[1]}}},{{x:{b[0]},y:{b[1]},duration:{d},ease:"{ease}"}},{t});'

def J_swap(out_sel, in_sel, t):
    return (f'tl.fromTo("{out_sel}",{{opacity:1}},{{opacity:0,duration:0.02}},{t});'
            f'tl.fromTo("{in_sel}",{{opacity:0}},{{opacity:1,duration:0.02}},{t});')

def J_border(sel, t, a, b, d=0.3):
    return f'tl.fromTo("{sel}",{{borderColor:"{a}"}},{{borderColor:"{b}",duration:{d},ease:"power2.out"}},{t});'

def J_color(sel, t, a, b, d=0.3):
    return f'tl.fromTo("{sel}",{{color:"{a}"}},{{color:"{b}",duration:{d},ease:"power2.out"}},{t});'

def J_words(fid, key, n, t0, step=0.12, d=0.55):
    p = f"f{fid}"
    return "".join(J_appear(f"#{p}-{key}{i}", round(t0 + i * step, 3), d, 18) for i in range(n))

# ---------- page assembly ----------
def seek_safe(js):
    """Every fromTo after the first on the same target gets immediateRender:false, so
    pre-first-tween seeks keep the first tween's from-state (lint: gsap_repeated_fromto_without_baseline)."""
    import re
    seen = set()
    out = []
    for stmt in re.split(r"(?<=;)", js):
        m = re.search(r'tl\.fromTo\("([^"]+)"', stmt)
        if m:
            sel = m.group(1)
            if sel in seen:
                stmt = stmt.replace("},{", "},{immediateRender:false,", 1)
            seen.add(sel)
        out.append(stmt)
    return "".join(out)

def page(fid, name, body_world, body_overlay, js):
    js = seek_safe(js)
    p = f"f{fid}"
    comp = f"{fid}-{name}"
    D = DUR[fid]
    return f"""<template>
  <style>{css(fid)}</style>
  <div id="root" data-composition-id="{comp}" data-width="{W}" data-height="{H}">
    <div id="{p}-bg" class="{p}-bg clip" data-start="0" data-duration="{D}" data-track-index="0"></div>
    <div id="{p}-camclip" class="{p}-cam clip" data-start="0" data-duration="{D}" data-track-index="1">
      <div id="{p}-world" class="{p}-world">{body_world}</div>
    </div>
    <div id="{p}-ovclip" class="{p}-ov clip" data-start="0" data-duration="{D}" data-track-index="2">{body_overlay}</div>
  </div>
  <script src="assets/vendor/gsap.min.js"></script>
  <script>
    (function () {{
      const tl = gsap.timeline({{ paused: true }});
      {js}
      tl.to({{}}, {{ duration: 0 }}, {D});
      window.__timelines = window.__timelines || {{}};
      window.__timelines["{comp}"] = tl;
    }})();
  </script>
</template>
"""

def cam_set(fid, state):
    x, y, s = CAM[state]
    return f'<!-- cam {state} -->', f'tl.set("#f{fid}-world",{{x:{x},y:{y},scale:{s}}},0);'

# =====================================================================
def f01():
    fid, p = "01", "f01"
    frags = []
    js = [J_fade(f"#{p}-k", 0.1, 0.5)]
    for i, (x, y, l, r) in enumerate(FRAGMENTS):
        X, Y = x * W / 100, y * H / 100
        frags.append(f'<div class="{p}-nw" style="left:{X:.0f}px;top:{Y:.0f}px"><div class="{p}-node">'
                     f'<div id="{p}-fr{i}"><div style="transform:rotate({r}deg)"><div id="{p}-fc{i}" class="{p}-in" style="padding:.9cqw 1.4cqw;position:relative">'
                     f'<b style="font-size:2.3cqw;font-weight:700;color:{C["muted"]}">{l}</b>'
                     f'<i id="{p}-fd{i}" style="position:absolute;right:-.7cqw;top:-.7cqw;width:1.4cqw;height:1.4cqw;border-radius:50%;background:{C["o"]}"></i>'
                     f'</div></div></div></div></div>')
    cues = [1.9, 2.7, 3.6, 4.2, 4.4, 4.6, 4.8]
    for i, t in enumerate(cues):
        js.append(f'tl.fromTo("#{p}-fc{i}",{{opacity:0,y:16}},{{opacity:1,y:0,duration:0.55,ease:"power3.out"}},{t});')
        js.append(f'tl.fromTo("#{p}-fd{i}",{{scale:0}},{{scale:1,duration:0.35,ease:"power3.out"}},{t + 0.25});')
    # closing in: each fragment drifts 2% toward center (finite)
    for i, (x, y, l, r) in enumerate(FRAGMENTS):
        dx = round((50 - x) * W / 100 * 0.04, 1); dy = round((42 - y) * H / 100 * 0.04, 1)
        js.append(f'tl.fromTo("#{p}-fr{i}",{{x:0,y:0}},{{x:{dx},y:{dy},duration:1.2,ease:"power2.inOut"}},4.8);')
    stmt = words(fid, "s", [("tus ", 0), ("clientes ", 0), ("están ", 0), ("en ", 1), ("todas ", 1), ("partes", 1)])
    js.append(J_words(fid, "s", 6, 0.4, 0.14))
    overlay = (f'<div id="{p}-k" class="{p}-kicker" style="left:5.5cqw;top:4cqw">01 / el problema</div>'
               f'<div style="position:absolute;left:5.5cqw;bottom:20%;font-weight:900;font-size:6cqw;letter-spacing:-.035em;line-height:1.08;max-width:62cqw">{stmt}</div>')
    return page(fid, "todo-disperso", "".join(frags), overlay, "\n      ".join(js))

def f02():
    fid, p = "02", "f02"
    frags = []
    js = [J_fade(f"#{p}-k", 0.1, 0.5)]
    cx, cy = px("crm")
    for i, (x, y, l, r) in enumerate(FRAGMENTS):
        X, Y = x * W / 100, y * H / 100
        frags.append(f'<div class="{p}-nw" style="left:{X:.0f}px;top:{Y:.0f}px"><div class="{p}-node">'
                     f'<div id="{p}-fr{i}"><div style="transform:rotate({r}deg)"><div class="{p}-in" style="padding:.9cqw 1.4cqw">'
                     f'<b style="font-size:2.3cqw;font-weight:700;color:{C["muted"]}">{l}</b></div></div></div></div></div>')
        js.append(f'tl.fromTo("#{p}-fr{i}",{{x:0,y:0,scale:1,opacity:1}},{{x:{cx - X:.1f},y:{cy - Y:.1f},scale:0.2,opacity:0,duration:1.1,ease:"power3.inOut"}},{0.25 + i * 0.03:.2f});')
    world = "".join(frags) + node(fid, "crm")
    js.append(f'tl.fromTo("#{p}-crm",{{scale:0.2,opacity:0}},{{scale:1,opacity:1,duration:0.9,ease:"power3.out"}},0.75);')
    js.append(J_appear(f"#{p}-crm-n", 1.5, 0.6, 8))
    for i, t in enumerate([3.0, 3.6, 4.2, 4.8]):
        js.append(J_appear(f"#{p}-crm-t{i}", t, 0.45, 8))
    cap = words(fid, "c", [("una ", 0), ("sola ", 0), ("ficha ", 0), ("por ", 1), ("cliente", 1)])
    js.append(J_words(fid, "c", 5, 5.5, 0.12))
    overlay = (f'<div id="{p}-k" class="{p}-kicker" style="left:5.5cqw;top:4cqw">02 / el centro</div>'
               f'<div style="position:absolute;left:5.5cqw;bottom:20%;font-weight:700;font-size:3.4cqw;letter-spacing:-.02em;line-height:1">{cap}</div>')
    return page(fid, "el-centro-crm", world, overlay, "\n      ".join(js))

def f03():
    fid, p = "03", "f03"
    L = wire_len("marketing")
    world = (wires(fid, ["marketing"], hot=["marketing"]) + node(fid, "crm") + node(fid, "marketing", f"{p}-act")
             + dot(fid, ["visitante", "lead"], 610, 453.6))
    js = [J_cam(f"#{p}-world", CAM["full"], CAM["left"], 0.0, 1.1), J_fade(f"#{p}-k", 0.2, 0.5),
          J_draw(f"#{p}-w-marketing", L, 1.0, 0.7), J_draw(f"#{p}-h-marketing", L, 1.0, 0.7),
          J_appear(f"#{p}-marketing", 1.45, 0.6)]
    for i, t in enumerate([2.6, 3.1, 3.7]):
        js.append(J_appear(f"#{p}-marketing-t{i}", t, 0.45, 8))
    js.append(f'tl.fromTo("#{p}-dot",{{opacity:0,scale:0.4}},{{opacity:1,scale:1,duration:0.4,ease:"power3.out"}},4.3);')
    js.append(J_fade(f"#{p}-dl1", 0, 0.01, 0, 0))
    js.append(J_move(f"#{p}-dot", (610, 453.6), (700, 453.6), 5.2, 1.2))
    js.append(J_swap(f"#{p}-dl0", f"#{p}-dl1", 5.8))
    overlay = f'<div id="{p}-k" class="{p}-kicker" style="left:5.5cqw;top:4cqw">03 / atraer</div>'
    return page(fid, "marketing-hub", world, overlay, "\n      ".join(js))

def f04():
    fid, p = "04", "f04"
    L = wire_len("ventas")
    sx, sy = px("ventas")
    cols = [(sx - 125, "nuevo"), (sx, "propuesta"), (sx + 125, "ganado")]
    pipe = "".join(
        f'<div class="{p}-nw" style="left:{x:.0f}px;top:{sy + 172:.0f}px"><div class="{p}-node">'
        f'<div id="{p}-pc{i}" style="border-top:2px solid {C["border"]};padding:.6cqw .5cqw 0;width:6.2cqw;text-align:center;'
        f'font:500 .9cqw \'IBM Plex Mono\',monospace;letter-spacing:.1em;text-transform:uppercase;color:{C["muted"]}">{l}</div></div></div>'
        for i, (x, l) in enumerate(cols))
    world = (wires(fid, ["marketing", "ventas"], hot=["ventas"]) + node(fid, "crm")
             + f'<div id="{p}-mkw" style="opacity:.45">{node(fid, "marketing")}</div>' + node(fid, "ventas", f"{p}-act")
             + pipe + dot(fid, ["lead", "cliente"], 700, 453.6))
    js = [J_cam(f"#{p}-world", CAM["left"], CAM["right"], 0.0, 1.1), J_fade(f"#{p}-k", 0.2, 0.5),
          J_fade(f"#{p}-dl1", 0, 0.01, 0, 0),
          J_draw(f"#{p}-w-ventas", L, 1.0, 0.7), J_draw(f"#{p}-h-ventas", L, 1.0, 0.7),
          J_appear(f"#{p}-ventas", 1.45, 0.6),
          J_move(f"#{p}-dot", (700, 453.6), (1250, 453.6), 1.0, 1.3)]
    for i, t in enumerate([2.5, 3.1, 3.7]):
        js.append(J_appear(f"#{p}-ventas-t{i}", t, 0.45, 8))
    for i in range(3):
        js.append(J_appear(f"#{p}-pc{i}", 4.2 + i * 0.1, 0.45, 8))
    py = sy + 112
    js.append(J_move(f"#{p}-dot", (1250, 453.6), (cols[0][0], py), 4.7, 0.6))
    js.append(J_move(f"#{p}-dot", (cols[0][0], py), (cols[1][0], py), 5.35, 0.4))
    js.append(J_move(f"#{p}-dot", (cols[1][0], py), (cols[2][0], py), 5.85, 0.4))
    js.append(J_color(f"#{p}-pc2", 6.2, C["muted"], C["o"]))
    js.append(J_border(f"#{p}-pc2", 6.2, C["border"], C["o"]))
    js.append(J_swap(f"#{p}-dl0", f"#{p}-dl1", 6.2))
    overlay = f'<div id="{p}-k" class="{p}-kicker" style="left:5.5cqw;top:4cqw">04 / vender</div>'
    return page(fid, "sales-hub", world, overlay, "\n      ".join(js))

def f05():
    fid, p = "05", "f05"
    L = wire_len("servicio")
    cx, cy = px("crm")
    world = (wires(fid, HUBS, hot=HUBS) + node(fid, "crm") + node(fid, "marketing") + node(fid, "ventas")
             + node(fid, "servicio", f"{p}-act") + dot(fid, [""], cx, cy)
             + f'<div id="{p}-tk" class="{p}-kicker" style="left:{cx + 34:.0f}px;top:{648 - 12:.0f}px">ticket abierto</div>')
    js = [J_cam(f"#{p}-world", CAM["right"], CAM["low"], 0.0, 1.1), J_fade(f"#{p}-k", 0.2, 0.5),
          J_draw(f"#{p}-w-servicio", L, 1.0, 0.7), J_draw(f"#{p}-h-servicio", L, 1.0, 0.7),
          J_appear(f"#{p}-servicio", 1.45, 0.6)]
    # marketing/sales highlight overlays start hidden, sweep outward on the payoff
    for n in ["marketing", "ventas"]:
        js.append(J_draw(f"#{p}-h-{n}", wire_len(n), 4.6, 0.9))
    for i, t in enumerate([2.8, 3.4, 3.9]):
        js.append(J_appear(f"#{p}-servicio-t{i}", t, 0.45, 8))
    js.append(f'tl.fromTo("#{p}-dot",{{opacity:0}},{{opacity:1,duration:0.3}},2.8);')
    js.append(J_move(f"#{p}-dot", (cx, cy), (cx, 648), 2.8, 0.8))
    js.append(J_appear(f"#{p}-tk", 3.4, 0.45, 6))
    js.append(J_border(f"#{p}-marketing", 5.3, C["border"], C["o"]))
    js.append(J_border(f"#{p}-ventas", 5.3, C["border"], C["o"]))
    overlay = f'<div id="{p}-k" class="{p}-kicker" style="left:5.5cqw;top:4cqw">05 / cuidar</div>'
    return page(fid, "service-hub", world, overlay, "\n      ".join(js))

def f06():
    fid, p = "06", "f06"
    world = (wires(fid, HUBS + MINIS, hot=HUBS + MINIS) + node(fid, "crm")
             + "".join(node(fid, n) for n in HUBS) + "".join(node(fid, n, f"{p}-act") for n in MINIS))
    js = [J_cam(f"#{p}-world", CAM["low"], CAM["wide"], 0.0, 1.1), J_fade(f"#{p}-k", 0.4, 0.5)]
    for n in HUBS:  # 05's lit wires cool back to hint
        js.append(J_fade(f"#{p}-h-{n}", 0.2, 0.8, 1, 0))
    for n, t in zip(MINIS, [2.8, 4.0, 5.2]):
        Lm = wire_len(n)
        js += [J_draw(f"#{p}-w-{n}", Lm, t - 0.5, 0.6), J_draw(f"#{p}-h-{n}", Lm, t - 0.5, 0.6),
               J_appear(f"#{p}-{n}", t, 0.5), J_appear(f"#{p}-{n}-t0", t + 0.35, 0.4, 6)]
    overlay = f'<div id="{p}-k" class="{p}-kicker" style="left:5.5cqw;bottom:20%">06 / más piezas</div>'
    return page(fid, "y-ademas", world, overlay, "\n      ".join(js))

def f07():
    fid, p = "07", "f07"
    allw = HUBS + MINIS
    world = (wires(fid, allw, hot=MINIS, pulse=allw) + node(fid, "crm")
             + "".join(node(fid, n) for n in allw)
             + f'<div id="{p}-bz" style="position:absolute;left:{0.61 * W:.0f}px;top:{0.30 * H - 18:.0f}px;font:500 1.1cqw \'IBM Plex Mono\',monospace;letter-spacing:.14em;text-transform:uppercase;color:{C["navy"]};background:{C["o"]};padding:.45cqw .9cqw">breeze · ia</div>')
    js = [f'tl.set("#{p}-world",{{x:{CAM["wide"][0]},y:{CAM["wide"][1]},scale:{CAM["wide"][2]}}},0);',
          J_fade(f"#{p}-k", 0.2, 0.5)]
    for n in MINIS:
        js.append(J_fade(f"#{p}-h-{n}", 0.1, 0.7, 1, 0))
    js.append(J_appear(f"#{p}-bz", 0.6, 0.6, 10))
    for n in allw:
        L = wire_len(n)
        js.append(J_pulse(f"#{p}-p-{n}", L, 1.8, 1.3))
        arrive = 1.8 + 1.3 * (L + 90) / (L + 90 + 90)  # approx arrival
        js.append(J_border(f"#{p}-{n}", round(min(arrive, 3.05), 2), C["border"], C["o"], 0.2))
        js.append(J_border(f"#{p}-{n}", 3.4, C["o"], C["border"], 0.5))
    verbs = "".join(f'<span id="{p}-v{i}" style="display:block;opacity:{o}">{v}</span>'
                    for i, (v, o) in enumerate([("escribe", 1), ("resume", .6), ("responde", .3)]))
    for i, t in enumerate([4.2, 4.8, 5.4]):
        o = [1, .6, .3][i]
        js.append(f'tl.fromTo("#{p}-v{i}",{{opacity:0,y:16}},{{opacity:{o},y:0,duration:0.5,ease:"power3.out"}},{t});')
    overlay = (f'<div id="{p}-k" class="{p}-kicker" style="left:5.5cqw;bottom:20%">07 / la ia</div>'
               f'<div style="position:absolute;right:5.5cqw;bottom:20%;text-align:right;font-weight:900;font-size:3.6cqw;letter-spacing:-.03em;line-height:1">{verbs}</div>')
    return page(fid, "breeze-ia", world, overlay, "\n      ".join(js))

def f08():
    fid, p = "08", "f08"
    allw = HUBS + MINIS
    world = wires(fid, allw) + node(fid, "crm") + "".join(node(fid, n) for n in allw)
    js = [J_cam(f"#{p}-world", CAM["wide"], CAM["emblem"], 0.0, 2.0, "power3.out")]
    lines = [[("un ", 0), ("centro.", 0)], [("muchas ", 0), ("piezas.", 0)], [("un ", 1), ("mismo ", 1), ("cliente.", 1)]]
    html_lines = []
    for li, parts in enumerate(lines):
        html_lines.append(f'<div>{words(fid, f"l{li}-", parts)}</div>')
    for li, t in enumerate([2.2, 3.0, 3.9]):
        js.append(J_words(fid, f"l{li}-", len(lines[li]), t, 0.12))
    js.append(J_fade(f"#{p}-k", 4.8, 0.6))
    js.append(f'tl.fromTo("#{p}-camclip, #{p}-ovclip",{{opacity:1}},{{opacity:0,duration:0.4,ease:"power2.in"}},{DUR[fid] - 0.4});')
    overlay = (f'<div id="{p}-k" class="{p}-kicker" style="right:5.5cqw;top:4cqw">así funciona hubspot</div>'
               f'<div style="position:absolute;left:5.5cqw;bottom:20%;font-weight:900;font-size:6.4cqw;letter-spacing:-.04em;line-height:1.06">{"".join(html_lines)}</div>')
    return page(fid, "asi-funciona", world, overlay, "\n      ".join(js))

FRAMES = {"01-todo-disperso": f01, "02-el-centro-crm": f02, "03-marketing-hub": f03, "04-sales-hub": f04,
          "05-service-hub": f05, "06-y-ademas": f06, "07-breeze-ia": f07, "08-asi-funciona": f08}

if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for name, fn in FRAMES.items():
        (OUT / f"{name}.html").write_text(fn(), encoding="utf-8")
        print("wrote", name)
