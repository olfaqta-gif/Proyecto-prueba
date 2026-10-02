// Extras de motion graphics. Corre después de agente-contenido/plantilla/base.js
// (ya llenó los textos y dejó get() y momento()).

// Íconos de línea (cuadrícula de 24). Cada trazo se dibuja solo, uno tras otro.
const ICONOS = {
  check: ['M4 12.5l5 5L20 6.5'],
  x: ['M6 6l12 12', 'M18 6L6 18'],
  gota: ['M12 3c3.6 4.6 6 7.9 6 11a6 6 0 0 1-12 0c0-3.1 2.4-6.4 6-11z', 'M9 14.5a3 3 0 0 0 3 3'],
  sol: ['M12 7.5a4.5 4.5 0 1 1 0 9a4.5 4.5 0 1 1 0-9z', 'M12 2v2.5', 'M12 19.5V22', 'M2 12h2.5', 'M19.5 12H22', 'M4.9 4.9l1.8 1.8', 'M17.3 17.3l1.8 1.8', 'M4.9 19.1l1.8-1.8', 'M17.3 6.7l1.8-1.8'],
  luna: ['M20 14.5A8.5 8.5 0 1 1 9.5 4a6.5 6.5 0 0 0 10.5 10.5z', 'M16 4.5v3', 'M14.5 6h3'],
  hoja: ['M5 19c0-8.5 5.5-14 15-15c-.8 10-6.5 15-15 15z', 'M5 19l8.5-8.5'],
  corazon: ['M12 20s-7.5-4.6-7.5-10.2A4.2 4.2 0 0 1 12 7.3a4.2 4.2 0 0 1 7.5 2.5C19.5 15.4 12 20 12 20z'],
  estrella: ['M12 3l2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17l-5.4 2.9 1-6.1-4.4-4.3 6.1-.9z'],
  reloj: ['M12 3a9 9 0 1 1 0 18a9 9 0 1 1 0-18z', 'M12 7v5.5l3.5 2'],
  chispa: ['M11 3l1.9 5.6L18.5 10.5l-5.6 1.9L11 18l-1.9-5.6L3.5 10.5l5.6-1.9z', 'M19 15v5', 'M16.5 17.5h5'],
  escudo: ['M12 3l7.5 3v5.5c0 5-3.2 8.4-7.5 9.9c-4.3-1.5-7.5-4.9-7.5-9.9V6z', 'M8.8 12.2l2.2 2.2 4.3-4.4'],
  cara: ['M12 3a9 9 0 1 1 0 18a9 9 0 1 1 0-18z', 'M9 10v.5', 'M15 10v.5', 'M8.3 14.3c2 2.3 5.4 2.3 7.4 0'],
  labios: ['M2.5 12c3-4.2 6.2-5.2 9.5-3c3.3-2.2 6.5-1.2 9.5 3c-3 5-6.3 6.5-9.5 6.5S5.5 17 2.5 12z', 'M2.5 12c3.2 1.2 6.4 1.6 9.5 1.6s6.3-.4 9.5-1.6'],
  ojo: ['M2 12s3.8-7 10-7s10 7 10 7s-3.8 7-10 7S2 12 2 12z', 'M12 9a3 3 0 1 1 0 6a3 3 0 1 1 0-6z'],
  frasco: ['M9.5 2.5h5v3.2l2.2 2.3V20a1.5 1.5 0 0 1-1.5 1.5H8.8A1.5 1.5 0 0 1 7.3 20V8l2.2-2.3z', 'M7.3 12h9.4', 'M7.3 17h9.4'],
  taza: ['M4 9h13v4.5A5.5 5.5 0 0 1 11.5 19h-2A5.5 5.5 0 0 1 4 13.5z', 'M17 10.5h1.5a2.6 2.6 0 0 1 0 5.2H16.6', 'M8 2.5c-.8 1.2.8 2.3 0 3.6', 'M12 2.5c-.8 1.2.8 2.3 0 3.6'],
  cabello: ['M5 21c0-9.5 2.6-17 7-17s7 7.5 7 17', 'M9.5 21c0-6.5 1-12 2.5-12s2.5 5.5 2.5 12', 'M12 4v5'],
  pincel: ['M18.5 3.5l2 2-9.3 9.3-2.6.6.6-2.6z', 'M8.6 15.4C6.5 15.2 4 16.6 4 20.5c2.8 0 5.3-1.4 4.6-5.1z'],
  calendario: ['M4 6h16v14.5H4z', 'M4 10.5h16', 'M8.5 3.5v4.5', 'M15.5 3.5v4.5', 'M8 14.5h2', 'M14 14.5h2'],
  bombilla: ['M9 18h6', 'M10 21h4', 'M12 3a6 6 0 0 1 4 10.5c-.8.8-1 1.6-1 2.5H9c0-.9-.2-1.7-1-2.5A6 6 0 0 1 12 3z'],
  lupa: ['M10.5 3.5a7 7 0 1 1 0 14a7 7 0 1 1 0-14z', 'M15.5 15.5L21 21'],
  flecha: ['M4 12h15', 'M13 6l6 6-6 6'],
  guardar: ['M6 3h12v18l-6-4.2L6 21z'],
  compartir: ['M21 3L3 10.5l7.5 3L13.5 21z', 'M10.5 13.5L21 3'],
  mensaje: ['M4 4.5h16v11.5H9.5L4 20.5z', 'M8 9h8', 'M8 12.5h5'],
  regalo: ['M4 10.5h16V21H4z', 'M3 7h18v3.5H3z', 'M12 7v14', 'M12 7C10 3 5.5 3.6 7 7', 'M12 7c2-4 6.5-3.4 5 0'],
  mano: ['M8 13V5.5a1.5 1.5 0 0 1 3 0V11', 'M11 10V4a1.5 1.5 0 0 1 3 0v6', 'M14 10V5.5a1.5 1.5 0 0 1 3 0V14c0 4-2.5 7-6.5 7c-3 0-4.5-1.6-6-4l-1.8-3a1.5 1.5 0 0 1 2.5-1.6L8 15'],
  dormir: ['M3 18h18', 'M5 18v-6.5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2V18', 'M14 3.5h4l-4 4h4'],
  agua: ['M12 3c3.6 4.6 6 7.9 6 11a6 6 0 0 1-12 0c0-3.1 2.4-6.4 6-11z', 'M9 14.5a3 3 0 0 0 3 3'],
};
ICONOS.vaso = ['M6 3h12l-1.6 17a1.5 1.5 0 0 1-1.5 1.3H9.1a1.5 1.5 0 0 1-1.5-1.3z', 'M6.7 9h10.6'];
ICONOS.seguir = ICONOS.corazon;
ICONOS.escribir = ICONOS.mensaje;
ICONOS.sueno = ICONOS.dormir;

document.querySelectorAll('[data-icono]').forEach(el => {
  const nombre = (el.dataset.icono.startsWith('=') ? get(F, el.dataset.icono.slice(1)) : el.dataset.icono) || 'chispa';
  const trazos = ICONOS[nombre] || ICONOS.chispa;
  const t0 = momento(el.dataset.d || '0');
  const paso = Math.min(0.18, 0.9 / trazos.length);
  el.classList.add('icono');
  el.innerHTML = '<svg viewBox="0 0 24 24">' + trazos.map((d, k) =>
    `<path pathLength="1" d="${d}" style="--d:${(t0 + k * paso).toFixed(3)}s"></path>`).join('') + '</svg>';
});

// Texto cinético: palabra por palabra. *palabras* entre asteriscos quedan resaltadas con marcador.
document.querySelectorAll('[data-kin]').forEach(el => {
  const t0 = momento(el.dataset.kin), paso = parseFloat(el.dataset.paso || '0.08');
  const texto = el.textContent || '';
  el.textContent = '';
  el.classList.add('kin');
  if (![...el.classList].some(c => c.startsWith('kin-'))) el.classList.add('kin-sube');
  let i = 0;
  texto.split(/(\*[^*]+\*)/).forEach(trozo => {
    const marcado = /^\*[^*]+\*$/.test(trozo);
    const palabras = trozo.replace(/\*/g, '').split(/\s+/).filter(Boolean);
    const fin = t0 + (i + palabras.length - 1) * paso + 0.3;
    palabras.forEach((p, k) => {
      const w = document.createElement('span'); w.className = 'w';
      const wi = document.createElement('span'); wi.className = 'wi'; wi.textContent = p;
      wi.style.setProperty('--d', (t0 + i * paso).toFixed(3) + 's');
      if (marcado) {
        wi.classList.add('hl');
        wi.style.setProperty('--dh', fin.toFixed(3) + 's');
        if (k < palabras.length - 1) wi.style.setProperty('margin-right', '-.3em'), wi.style.setProperty('padding-right', '.3em');
      }
      w.appendChild(wi); el.appendChild(w); el.appendChild(document.createTextNode(' '));
      i++;
    });
  });
});

// Contadores: si el número es entero sube desde 0; si no (4.9, 1/2…) solo aparece de golpe.
document.querySelectorAll('[data-numero]').forEach(el => {
  const v = String(get(F, el.dataset.numero) ?? '').trim();
  if (/^\d{1,6}$/.test(v)) { el.classList.add('contador'); el.style.setProperty('--hasta', v); }
  else { el.textContent = v; el.classList.add('pop'); }
});
