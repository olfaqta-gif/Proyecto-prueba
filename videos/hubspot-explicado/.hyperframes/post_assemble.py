"""Run after assemble-index.mjs + transitions.mjs inject (they regenerate index.html):
1) GSAP from the local vendored copy (the CDN is unreachable in this environment;
   same file, same sha384 as the CDN build);
2) the Banco Ficensa logo as a root-level corner mark over the whole video
   (root level, so frame transitions — zoom-through, crossfade — never move it)."""
import re
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
p = ROOT / "index.html"
t = p.read_text(encoding="utf-8")
t = re.sub(r'https://cdn\.jsdelivr\.net/npm/gsap@3\.14\.2/dist/gsap\.min\.js"[^>]*>', 'assets/vendor/gsap.min.js">', t)
total = float(re.search(r'data-composition-id="main"[^>]*?data-duration="([\d.]+)"', t, re.S).group(1))
if 'id="el-brand-logo"' not in t:
    D = round(total, 3)
    (ROOT / "compositions" / "brand-logo.html").write_text(f"""<template>
  <style>
    #root {{ position: absolute; inset: 0; width: 1920px; height: 1080px; pointer-events: none; }}
    #brand-logo-card {{ position: absolute; right: 106px; top: 48px; width: 196px; height: 92px; background: #FFFFFF;
      display: flex; align-items: center; justify-content: center; }}
    #brand-logo-card img {{ display: block; height: 64px; width: auto; }}
  </style>
  <div id="root" data-composition-id="brand-logo" data-width="1920" data-height="1080">
    <div id="brand-logo-card" class="clip" data-start="0" data-duration="{D}" data-track-index="0">
      <img src="public/logo-banco-ficensa-trim.png" alt="Banco Ficensa" />
    </div>
  </div>
  <script src="assets/vendor/gsap.min.js"></script>
  <script>
    (function () {{
      const tl = gsap.timeline({{ paused: true }});
      tl.fromTo("#brand-logo-card", {{ opacity: 0, y: -10 }}, {{ opacity: 1, y: 0, duration: 0.6, ease: "power3.out" }}, 0.2);
      tl.to("#brand-logo-card", {{ opacity: 0, duration: 0.4, ease: "power2.in" }}, {round(D - 0.4, 3)});
      tl.to({{}}, {{ duration: 0 }}, {D});
      window.__timelines = window.__timelines || {{}};
      window.__timelines["brand-logo"] = tl;
    }})();
  </script>
</template>
""", encoding="utf-8")
    host = f'''
      <!-- brand mark: Banco Ficensa (user-supplied logo), root level so transitions never move it -->
      <div id="el-brand-logo" data-composition-id="brand-logo" data-composition-src="compositions/brand-logo.html"
        data-start="0" data-duration="{D}" data-track-index="30" data-width="1920" data-height="1080"
        style="position:absolute;inset:0;z-index:50"></div>
'''
    i = t.rfind("\n    </div>", 0, t.index("<script>", t.index('data-composition-id="main"')))
    t = t[:i] + host + t[i:]
p.write_text(t, encoding="utf-8")
print("post_assemble ok · total", total)
