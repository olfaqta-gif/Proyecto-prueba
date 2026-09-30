// Genera keynote/presentacion.html: un solo archivo autocontenido (GSAP y fuente incluidos)
// que presenta index.html como keynote: clic / → para avanzar, animaciones reales.
// Uso: node build-keynote.mjs
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";

const dir = new URL(".", import.meta.url);
const read = (f, enc = "utf8") => readFileSync(new URL(f, dir), enc);

let html = read("index.html");
const gsap = read("assets/gsap.min.js");
const font = readFileSync(new URL("assets/Inter.woff2", dir)).toString("base64");

function replaceOnce(src, from, to) {
  if (!src.includes(from)) throw new Error(`No se encontró: ${from}`);
  return src.replace(from, () => to);
}

html = replaceOnce(html, '<script src="./assets/gsap.min.js"></script>', `<script>${gsap}</script>`);
html = replaceOnce(html, 'url("./assets/Inter.woff2")', `url(data:font/woff2;base64,${font})`);
html = replaceOnce(html, '<meta name="viewport" content="width=1920, height=1080" />', '<meta name="viewport" content="width=device-width, initial-scale=1" />');

const style = `
    <style>
      html, body { width: 100vw !important; height: 100vh !important; background: #000 !important; }
      #root { position: absolute !important; left: 0; top: 0; width: 1920px !important; height: 1080px !important; transform-origin: 0 0; }
      #root [data-start] { visibility: hidden; }
      #kn-bar {
        position: fixed; left: 50%; bottom: 18px; transform: translateX(-50%);
        display: flex; align-items: center; gap: 6px; padding: 6px 8px; border-radius: 999px;
        background: rgba(10, 14, 24, 0.72); border: 1px solid rgba(255, 255, 255, 0.14);
        font: 600 14px/1 system-ui, sans-serif; color: #fff; z-index: 10;
        opacity: 0.25; transition: opacity 0.25s;
      }
      #kn-bar:hover, body.kn-ui #kn-bar { opacity: 1; }
      #kn-bar button {
        all: unset; cursor: pointer; min-width: 36px; height: 36px; padding: 0 10px; box-sizing: border-box;
        display: grid; place-items: center; border-radius: 999px;
      }
      #kn-bar button:hover { background: rgba(255, 255, 255, 0.14); }
      #kn-count { padding: 0 8px; font-variant-numeric: tabular-nums; }
      #kn-notes {
        position: fixed; left: 16px; right: 16px; bottom: 72px; max-width: 900px; margin: 0 auto;
        padding: 14px 18px; border-radius: 12px; background: rgba(10, 14, 24, 0.9);
        border: 1px solid rgba(255, 255, 255, 0.14); color: #fff; font: 400 17px/1.45 system-ui, sans-serif;
        display: none; z-index: 10;
      }
      body.kn-show-notes #kn-notes { display: block; }
    </style>
  </head>`;
html = replaceOnce(html, "  </head>", style);

const player = `
    <div id="kn-notes"></div>
    <div id="kn-bar">
      <button id="kn-prev" title="Anterior (←)">&#8592;</button>
      <span id="kn-count">1 / 1</span>
      <button id="kn-next" title="Siguiente (→, espacio, clic)">&#8594;</button>
      <button id="kn-notes-btn" title="Notas del presentador (N)">Notas</button>
      <button id="kn-full" title="Pantalla completa (F)">&#x26F6;</button>
    </div>
    <script>
      (function () {
        var tl = window.__timelines.main;
        var root = document.getElementById("root");
        var manifest = JSON.parse(document.querySelector('script[type="application/hyperframes-slideshow+json"]').textContent);
        var slides = manifest.slides;

        // Puntos de parada: cada fragmento, o la mitad de la diapositiva si no tiene.
        var holds = [];
        slides.forEach(function (s, i) {
          var times = s.fragments && s.fragments.length ? s.fragments : [(s.startTime + s.endTime) / 2];
          times.forEach(function (t) { holds.push({ slide: i, t: t }); });
        });

        // Visibilidad de clips según su ventana de tiempo (lo que hace el runtime de HyperFrames).
        var clips = Array.prototype.filter.call(root.querySelectorAll("[data-start]"), function (el) { return el !== root; });
        function vis() {
          var t = tl.time();
          clips.forEach(function (el) {
            var s = parseFloat(el.dataset.start), d = parseFloat(el.dataset.duration);
            el.style.visibility = t >= s && t < s + d ? "visible" : "hidden";
          });
        }

        function fit() {
          var s = Math.min(innerWidth / 1920, innerHeight / 1080);
          root.style.transform = "translate(" + (innerWidth - 1920 * s) / 2 + "px," + (innerHeight - 1080 * s) / 2 + "px) scale(" + s + ")";
        }
        addEventListener("resize", fit);
        fit();

        var idx = 0, anim = null;
        function ui() {
          var h = holds[idx];
          document.getElementById("kn-count").textContent = h.slide + 1 + " / " + slides.length;
          document.getElementById("kn-notes").textContent = slides[h.slide].notes || "";
        }
        function playTo(t) {
          if (anim) anim.kill();
          anim = tl.tweenTo(t, { ease: "none", onUpdate: vis });
        }
        function go(i, animate) {
          if (i < 0 || i >= holds.length) return;
          var prev = holds[idx];
          idx = i;
          var h = holds[i];
          if (!animate) {
            if (anim) anim.kill();
            tl.seek(h.t, false);
            vis();
          } else if (h.slide !== prev.slide) {
            // Nueva diapositiva: arranca desde su inicio y reproduce su entrada.
            tl.seek(slides[h.slide].startTime, false);
            vis();
            playTo(h.t);
          } else {
            playTo(h.t);
          }
          ui();
        }
        function next() { if (idx < holds.length - 1) go(idx + 1, true); }
        function prev() { go(idx - 1, false); }

        document.getElementById("kn-next").onclick = function (e) { e.stopPropagation(); next(); };
        document.getElementById("kn-prev").onclick = function (e) { e.stopPropagation(); prev(); };
        document.getElementById("kn-notes-btn").onclick = function (e) { e.stopPropagation(); document.body.classList.toggle("kn-show-notes"); };
        function full() {
          if (document.fullscreenElement) document.exitFullscreen();
          else if (document.documentElement.requestFullscreen) document.documentElement.requestFullscreen();
        }
        document.getElementById("kn-full").onclick = function (e) { e.stopPropagation(); full(); };
        document.addEventListener("click", function (e) { if (!e.target.closest("#kn-bar, #kn-notes")) next(); });
        document.addEventListener("keydown", function (e) {
          var k = e.key;
          if (k === "ArrowRight" || k === " " || k === "PageDown" || k === "Enter") { e.preventDefault(); next(); }
          else if (k === "ArrowLeft" || k === "PageUp" || k === "Backspace") { e.preventDefault(); prev(); }
          else if (k === "n" || k === "N") document.body.classList.toggle("kn-show-notes");
          else if (k === "f" || k === "F") full();
          else if (k === "Home") go(0, false);
        });
        var hideTimer;
        document.addEventListener("mousemove", function () {
          document.body.classList.add("kn-ui");
          clearTimeout(hideTimer);
          hideTimer = setTimeout(function () { document.body.classList.remove("kn-ui"); }, 1800);
        });

        // Arranque: reproduce la entrada de la portada.
        tl.seek(0, false);
        vis();
        playTo(holds[0].t);
        ui();
      })();
    </script>
  </body>`;
html = replaceOnce(html, "  </body>", player);

mkdirSync(new URL("keynote/", dir), { recursive: true });
writeFileSync(new URL("keynote/presentacion.html", dir), html);
console.log("keynote/presentacion.html generado (" + Math.round(html.length / 1024) + " KB)");
