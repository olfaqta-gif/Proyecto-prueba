"""Run after audio.mjs generate / fetch-sfx (both rewrite audio_meta.json from the
engine sidecar): restore padded voice durations (breath/hold silences added to
assets/voice/*.wav), re-derive word timings, and place each SFX cue on its beat."""
import json, subprocess, os
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
m = json.loads((ROOT / "audio_meta.json").read_text())
for v in m["voices"]:
    v["duration_s"] = round(float(subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(ROOT / v["path"])]).decode()), 3)
by = {}
for s in m["sfx"]:
    by[os.path.basename(s["file"]).rsplit(".", 1)[0]] = s
PLAN = {1: [("pop", 2.61), ("pop", 3.45), ("pop", 4.73), ("pop", 5.1)], 2: [("whoosh", 0.3), ("click-soft", 0.8)],
        3: [("click-soft", 0.85)], 4: [("click-soft", 0.5), ("ping", 4.6)], 5: [("click-soft", 0.5), ("chime", 3.7)],
        6: [("click-soft", 2.13), ("click-soft", 3.26), ("click-soft", 4.7)], 7: [("sparkle", 2.2)], 8: [("whoosh", 0.0)]}
if by:
    m["sfx"] = [dict(by[n], frame=f, offset_s=o) for f, cues in PLAN.items() for n, o in cues]
(ROOT / "audio_meta.json").write_text(json.dumps(m, indent=2, ensure_ascii=False))
subprocess.run(["python3", str(ROOT / ".hyperframes/word_timings.py")], check=True, stdout=subprocess.DEVNULL)
print("voices", [v["duration_s"] for v in m["voices"]], "sfx", len(m["sfx"]))
