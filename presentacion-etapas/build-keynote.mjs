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
      <button id="kn-back" title="Volver a la presentación (Esc)">&#8617; Volver</button>
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

        // Secuencias: la principal y los anexos (ramificaciones).
        var seqs = { main: { label: "", slides: manifest.slides } };
        (manifest.slideSequences || []).forEach(function (q) { seqs[q.id] = q; });

        // Puntos de parada de una diapositiva: sus fragmentos, o su mitad si no tiene.
        function holdsOf(sl) {
          return sl.fragments && sl.fragments.length ? sl.fragments : [(sl.startTime + sl.endTime) / 2];
        }

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

        // Pila de navegación: [{ seq, slide, frag }]. El último elemento es la posición actual.
        var stack = [{ seq: "main", slide: 0, frag: 0 }];
        var anim = null;
        function cur() { return stack[stack.length - 1]; }
        function slideOf(pos) { return seqs[pos.seq].slides[pos.slide]; }

        function ui() {
          var pos = cur(), q = seqs[pos.seq];
          var label = pos.seq === "main" ? "" : "Anexo · ";
          document.getElementById("kn-count").textContent = label + (pos.slide + 1) + " / " + q.slides.length;
          document.getElementById("kn-back").style.display = stack.length > 1 ? "" : "none";
          document.getElementById("kn-notes").textContent = slideOf(pos).notes || "";
        }
        var target = null;
        // Si hay una animación en curso, se completa de golpe antes de la siguiente.
        function finish() {
          if (anim) { anim.kill(); anim = null; }
          if (target !== null) { tl.seek(target, false); vis(); target = null; }
        }
        function playTo(t) {
          var dist = Math.abs(t - tl.time());
          target = t;
          anim = tl.tweenTo(t, {
            ease: "none",
            onUpdate: vis,
            onComplete: function () { target = null; anim = null; },
          });
          anim.timeScale(Math.max(1, dist / 2.5)); // ninguna animación dura más de 2.5 s
        }
        function show(animate, entering) {
          var pos = cur(), sl = slideOf(pos), t = holdsOf(sl)[pos.frag];
          finish();
          if (!animate) {
            tl.seek(t, false);
            vis();
          } else {
            if (entering) {
              // Nueva diapositiva: arranca desde su inicio y reproduce su entrada.
              tl.seek(sl.startTime, false);
              vis();
            }
            playTo(t);
          }
          ui();
        }

        function next() {
          var pos = cur(), q = seqs[pos.seq];
          if (pos.frag + 1 < holdsOf(slideOf(pos)).length) { pos.frag++; show(true, false); }
          else if (pos.slide + 1 < q.slides.length) { pos.slide++; pos.frag = 0; show(true, true); }
          else if (stack.length > 1) back();
        }
        function prev() {
          var pos = cur();
          if (pos.frag > 0) { pos.frag--; show(false); }
          else if (pos.slide > 0) { pos.slide--; pos.frag = holdsOf(slideOf(pos)).length - 1; show(false); }
          else if (stack.length > 1) back();
        }
        function back() {
          if (stack.length > 1) { stack.pop(); show(false); }
        }
        function enterBranch(id) {
          if (!seqs[id]) return;
          stack.push({ seq: id, slide: 0, frag: 0 });
          show(true, true);
        }
        function goHome() { stack = [{ seq: "main", slide: 0, frag: 0 }]; show(false); }

        document.getElementById("kn-next").onclick = function (e) { e.stopPropagation(); next(); };
        document.getElementById("kn-prev").onclick = function (e) { e.stopPropagation(); prev(); };
        document.getElementById("kn-back").onclick = function (e) { e.stopPropagation(); back(); };
        document.getElementById("kn-notes-btn").onclick = function (e) { e.stopPropagation(); document.body.classList.toggle("kn-show-notes"); };
        function full() {
          if (document.fullscreenElement) document.exitFullscreen();
          else if (document.documentElement.requestFullscreen) document.documentElement.requestFullscreen();
        }
        document.getElementById("kn-full").onclick = function (e) { e.stopPropagation(); full(); };
        document.addEventListener("click", function (e) {
          if (e.target.closest("#kn-bar, #kn-notes")) return;
          // Botón de anexo dentro de la diapositiva (solo si ya está visible).
          var hot = e.target.closest("[data-kn-hotspot]");
          if (hot && parseFloat(getComputedStyle(hot).opacity) > 0.5) { enterBranch(hot.getAttribute("data-kn-hotspot")); return; }
          next();
        });
        document.addEventListener("keydown", function (e) {
          var k = e.key;
          if (k === "ArrowRight" || k === " " || k === "PageDown" || k === "Enter") { e.preventDefault(); next(); }
          else if (k === "ArrowLeft" || k === "PageUp" || k === "Backspace") { e.preventDefault(); prev(); }
          else if (k === "Escape") back();
          else if (k === "n" || k === "N") document.body.classList.toggle("kn-show-notes");
          else if (k === "f" || k === "F") full();
          else if (k === "Home") goHome();
        });
        var hideTimer;
        document.addEventListener("mousemove", function () {
          document.body.classList.add("kn-ui");
          clearTimeout(hideTimer);
          hideTimer = setTimeout(function () { document.body.classList.remove("kn-ui"); }, 1800);
        });

        // Arranque: reproduce la entrada de la portada.
        show(true, true);
      })();
    </script>
  </body>`;
html = replaceOnce(html, "  </body>", player);

mkdirSync(new URL("keynote/", dir), { recursive: true });
writeFileSync(new URL("keynote/presentacion.html", dir), html);
console.log("keynote/presentacion.html generado (" + Math.round(html.length / 1024) + " KB)");
