"""Offline word timings: map script phrases onto Kokoro speech segments found by
ffmpeg silencedetect, then spread words inside each segment by character length.
(Whisper/Parakeet can't be downloaded in this environment.) Writes
.hyperframes/word_timings.json and fills audio_meta.json voices[].words."""
import json, re, subprocess
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
# phrase groups per line, in the order spoken; each group = one detected speech segment
GROUPS = {
 1: ["Tus clientes están en todas partes:", "un correo aquí, una hoja de cálculo allá, un chat que nadie ve."],
 2: ["HubSpot empieza por el centro:", "un CRM.", "Contactos,", "empresas, negocios y tickets, en una sola ficha por cliente."],
 3: ["Se conecta Marketing Hub:", "emails, anuncios y formularios atraen visitantes… y los convierten en leads."],
 4: ["Sales Hub recoge ese lead:", "pipeline, reuniones, cotizaciones… hasta cerrar la venta."],
 5: ["Y Service Hub cuida al cliente después: tickets, chat, ayuda.", "Y todo el equipo ve el mismo historial."],
 6: ["Y si lo necesitas, más piezas:", "Content para tu web, Operations para tus datos, Commerce para cobrar."],
 7: ["Por encima trabaja Breeze, la IA de HubSpot:", "usa esos datos para escribir, resumir y responder por ti."],
 8: ["Un centro, muchas piezas, un mismo cliente.", "Así funciona HubSpot."],
}
def segments(path):
    out = subprocess.run(["ffmpeg","-hide_banner","-i",path,"-af","silencedetect=noise=-38dB:d=0.12","-f","null","-"],capture_output=True,text=True).stderr
    marks = [(k, float(v)) for k, v in re.findall(r"silence_(start|end): ([0-9.]+)", out)]
    segs, cur = [], 0.0
    for k, v in marks:
        if k == "start":
            if v - cur > 0.05: segs.append((cur, v))
        else: cur = v
    return segs
meta = json.loads((ROOT/"audio_meta.json").read_text())
allw = {}
for v in meta["voices"]:
    n = v["frame"]; segs = segments(str(ROOT/v["path"])); groups = GROUPS[n]
    assert len(segs) == len(groups), (n, segs, groups)
    words = []
    for (a, b), g in zip(segs, groups):
        toks = g.split(); w = [len(re.sub(r"\W", "", t)) + 1.5 for t in toks]; tot = sum(w); t = a
        for tok, ww in zip(toks, w):
            d = (b - a) * ww / tot; words.append({"text": tok, "start": round(t, 3), "end": round(t + d, 3)}); t += d
    v["words"] = words; allw[n] = words
(ROOT/"audio_meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False))
(ROOT/".hyperframes/word_timings.json").write_text(json.dumps(allw, indent=1, ensure_ascii=False))
for n, ws in allw.items():
    print(n, " ".join(f"{x['text']}@{x['start']}" for x in ws))
