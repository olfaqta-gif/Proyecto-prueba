// Motor común: llena los textos de la ficha, aplica los tiempos y deja exportar cuadro por cuadro.
// generar.py define antes: T (tiempos del estilo), F (ficha), IMG (foto), W y H (tamaño del formato).
const get = (o, path) => path.split('.').reduce((v, k) => (v == null ? v : v[k]), o);
const root = document.documentElement;
root.dataset.paleta = F.paleta || 'coral';

// Textos de la ficha (textContent: nunca se interpreta HTML de la ficha)
document.querySelectorAll('[data-txt]').forEach(el => { el.textContent = get(F, el.dataset.txt) ?? ''; });
// Bloques opcionales: si la ficha no trae el dato, el bloque no aparece
document.querySelectorAll('[data-si]').forEach(el => { if (!get(F, el.dataset.si)) el.remove(); });
document.querySelectorAll('[data-img]').forEach(el => { el.src = IMG; });

// Cuántos elementos tiene una lista de la ficha (p. ej. el "3" de "3 razones")
document.querySelectorAll('[data-cuenta]').forEach(el => { el.textContent = (get(F, el.dataset.cuenta) || []).length; });

// Texto palabra por palabra (estilo subtítulo de TikTok): cada palabra entra el tiempo de data-paso después
document.querySelectorAll('[data-palabras]').forEach(el => {
  const t0 = get(T, el.dataset.palabras), paso = parseFloat(get(T, el.dataset.paso || '') ?? 0.14);
  const words = (el.textContent || '').split(/\s+/).filter(Boolean);
  el.textContent = '';
  words.forEach((w, i) => {
    const s = document.createElement('span');
    s.className = 'palabra';
    s.textContent = w;
    s.style.setProperty('--d', (t0 + i * paso) + 's');
    el.appendChild(s);
    el.appendChild(document.createTextNode(' '));
  });
});

// Tiempos: un solo archivo por estilo mueve video y sonido a la vez
// Acepta "producto.dato", "razon.r1+0.35" o un número de segundos
const momento = k => { if (/^[\d.]+$/.test(k)) return parseFloat(k); const m = k.match(/^([\w.]*?)\s*([+-]\s*[\d.]+)?$/); return (m[1] ? get(T, m[1]) : 0) + parseFloat((m[2] || '0').replace(/\s/g, '')); };
const sec = k => momento(k) + 's';
document.querySelectorAll('[data-d]').forEach(el => el.style.setProperty('--d', sec(el.dataset.d)));
document.querySelectorAll('[data-in]').forEach(el => el.style.setProperty('--in', sec(el.dataset.in)));
document.querySelectorAll('[data-out]').forEach(el => el.style.setProperty('--out', sec(el.dataset.out)));

const sparks = document.getElementById('sparks');
if (sparks) {
  for (let i = 0; i < 38; i++) {
    const s = document.createElement('div');
    s.className = 'spark';
    const r = n => (Math.sin(i * 99.13 + n) + 1) / 2;   // determinista: mismo video en cada render
    s.style.left = (r(1) * W) + 'px';
    s.style.top = (H * 0.47 + r(2) * H * 0.57) + 'px';
    s.style.setProperty('--dur', (5 + r(3) * 6).toFixed(2) + 's');
    s.style.setProperty('--dl', (-r(4) * 10).toFixed(2) + 's');
    s.style.width = s.style.height = (8 * (0.4 + r(5) * 1.2)) + 'px';
    sparks.appendChild(s);
  }
}

// Textos largos: reduce la letra hasta que quepan en el alto de data-lineas líneas (defecto 3)
window.__ajustar = () => {
  document.querySelectorAll('.fit').forEach(el => {
    const cs = getComputedStyle(el);
    const lh = parseFloat(cs.lineHeight) || parseFloat(cs.fontSize) * 1.1;
    let size = parseFloat(cs.fontSize);
    const maxH = lh * (parseFloat(el.dataset.lineas || '3') + 0.2);
    while ((el.scrollHeight > maxH || el.scrollWidth > el.clientWidth + 2) && size > 22) {
      size -= 2; el.style.fontSize = size + 'px';
      el.querySelectorAll('.serif').forEach(s => s.style.fontSize = (size * 1.08) + 'px');
    }
  });
  // Botón: una sola línea aunque la palabra clave sea larga
  document.querySelectorAll('.btn').forEach(el => {
    const max = Math.min(W, H * 1.2) * 0.84;
    let size = parseFloat(getComputedStyle(el).fontSize);
    while (el.offsetWidth > max && size > 22) { size -= 2; el.style.fontSize = size + 'px'; }
  });
};
document.fonts.ready.then(window.__ajustar);

const stage = document.getElementById('stage');
function fit(){ const k = Math.min(innerWidth / W, innerHeight / H); stage.style.transform = `scale(${k})`; }
addEventListener('resize', fit); fit();
// Un solo reloj para todas las animaciones CSS: permite exportar cuadro por cuadro
window.__seek = t => document.getAnimations().forEach(a => { a.pause(); a.currentTime = t * 1000; });
if (!location.search.includes('render')) {
  const t0 = performance.now();
  (function tick(){ window.__seek(((performance.now() - t0) / 1000) % T.duracion); requestAnimationFrame(tick); })();
}
