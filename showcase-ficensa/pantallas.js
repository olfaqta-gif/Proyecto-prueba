// Las pantallas de la app (recreadas del storyboard) y lo que pasa dentro de cada una.
// Tiempos en segundos desde que empieza cada paso (lt).

// ---- Utilidades de animación (las usa también showcase.js) ----
const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
const prog = (t, a, b) => clamp((t - a) / (b - a));
const eo = (x) => 1 - Math.pow(1 - x, 3);
const eio = (x) => (x < .5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2);
const eb = (x) => { const c1 = 1.9, c3 = c1 + 1; return x <= 0 ? 0 : x >= 1 ? 1 : 1 + c3 * Math.pow(x - 1, 3) + c1 * Math.pow(x - 1, 2); };
const lerp = (a, b, x) => a + (b - a) * x;
// Sube en [a, a+d] y baja en [b, b+d]
const ventana = (t, a, b, d = .25) => Math.min(eo(prog(t, a, a + d)), 1 - eo(prog(t, b, b + d)));

function rng(seed) {
  return () => { seed |= 0; seed = seed + 0x6D2B79F5 | 0; let t = Math.imul(seed ^ seed >>> 15, 1 | seed);
    t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; };
}

// Patrón de polígonos de la app (triángulos en tonos de azul)
function poligonos(w, h, seed, c1 = [27, 63, 142], c2 = [52, 104, 196], cel = 70) {
  const r = rng(seed), cols = Math.ceil(w / cel) + 1, rows = Math.ceil(h / cel) + 1, P = [];
  for (let y = 0; y <= rows; y++) { P.push([]); for (let x = 0; x <= cols; x++)
    P[y].push([x * cel + (r() - .5) * cel * .7, y * cel + (r() - .5) * cel * .7]); }
  let s = `<svg viewBox="0 0 ${w} ${h}" preserveAspectRatio="xMidYMid slice" xmlns="http://www.w3.org/2000/svg">`;
  const col = () => { const k = r(); return `rgb(${c1.map((v, i) => Math.round(lerp(v, c2[i], k))).join(',')})`; };
  for (let y = 0; y < rows; y++) for (let x = 0; x < cols; x++) {
    const a = P[y][x], b = P[y][x + 1], c = P[y + 1][x], d = P[y + 1][x + 1];
    s += `<polygon points="${a} ${b} ${d}" fill="${col()}"/><polygon points="${a} ${d} ${c}" fill="${col()}"/>`;
  }
  return s + '</svg>';
}

const ICO = {
  check: '<svg viewBox="0 0 24 24"><path d="M5 12.5l4.5 4.5L19 7.5" fill="none" stroke="#fff" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round"/></svg>',
  usuario: '<svg viewBox="0 0 32 32" fill="none" stroke="#2450a2" stroke-width="2.4" stroke-linecap="round"><circle cx="13" cy="11" r="5"/><path d="M4 27c1-6 5-9 9-9s8 3 9 9"/><path d="M25 9v8M21 13h8"/></svg>',
  cuenta: '<svg viewBox="0 0 32 32" fill="none" stroke="#2450a2" stroke-width="2.4" stroke-linejoin="round"><rect x="5" y="7" width="22" height="18" rx="3"/><path d="M5 13h22M10 19h6"/></svg>',
  candado: '<svg viewBox="0 0 32 32" fill="none" stroke="#2450a2" stroke-width="2.4"><rect x="7" y="14" width="18" height="13" rx="3"/><path d="M11 14v-4a5 5 0 0110 0v4"/></svg>',
  faceid: '<svg viewBox="0 0 36 36" fill="none" stroke="#2450a2" stroke-width="2.6" stroke-linecap="round"><path d="M3 11V6a3 3 0 013-3h5M25 3h5a3 3 0 013 3v5M33 25v5a3 3 0 01-3 3h-5M11 33H6a3 3 0 01-3-3v-5M12 13v3M24 13v3M18 13v7h-2M13 25c3 2 7 2 10 0"/></svg>',
  correo: '<svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 7l9 6 9-6"/></svg>',
  foco: '<svg viewBox="0 0 48 48" fill="none" stroke="#0b1d48" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round"><path d="M24 6a13 13 0 00-7 24c1 1 2 3 2 5h10c0-2 1-4 2-5A13 13 0 0024 6z" fill="#fff"/><path d="M19 40h10M21 44h6M24 13v6M20 19h8"/></svg>',
};
const TAB = ['Inicio|<path d="M4 11l8-7 8 7v9h-5v-6H9v6H4z"/>', 'Tasa cambio|<path d="M12 3v18M16 7c-1-2-3-2-4-2-2 0-4 1-4 3 0 4 8 2 8 6 0 2-2 3-4 3-2 0-3-1-4-2"/>',
  'Agencias|<path d="M4 20h16M6 20V9h12v11M3 9l9-5 9 5M10 20v-5h4v5"/>', 'Contáctanos|<path d="M4 5h16v11H9l-5 4z"/>', 'Más|<path d="M4 7h16M4 12h16M4 17h16"/>'];

// Marca pequeña (las cintas del logo) para la barra de la app
const MARCA = '<svg class="mk" viewBox="0 0 720 790"><path d="M30 762C300 520 400 250 440 15L710 145C560 430 330 650 30 762Z" fill="#fdd10b"/><path d="M30 762C250 620 420 480 532 343L690 513C480 660 260 740 30 762Z" fill="#95c94a" opacity=".95"/><path d="M30 762C160 740 270 705 377 657L398 760C280 770 150 770 30 762Z" fill="#12c0f0"/></svg>';
const HDR = `<div class="hdr">${MARCA}<div class="sep"></div>Apertura Cuenta</div>`;
const FTR = (s) => `<div class="ftr"><div class="poly">${poligonos(390, 66, s, [24, 58, 130], [44, 92, 180], 30)}</div></div>`;
const STP = (n) => '<div class="stp">' + [1, 2, 3, 4].map((i) =>
  `<div class="n ${i < n ? 'ok' : i === n ? 'on' : ''}">${i <= n ? i : ''}</div>` + (i < 4 ? `<div class="l ${i < n ? 'ok' : ''}"></div>` : '')).join('') + '</div>';
const TECLADO = '<div class="kb">' + ['qwertyuiop', 'asdfghjklñ'].map((r) => '<div class="row">' + [...r].map((k) => `<div class="k" data-k="${k}">${k}</div>`).join('') + '</div>').join('')
  + '<div class="row"><div class="k f m">⇧</div>' + [...'zxcvbnm'].map((k) => `<div class="k" data-k="${k}">${k}</div>`).join('') + '<div class="k f m">⌫</div></div>'
  + '<div class="row"><div class="k f m">123</div><div class="k f" data-k="@">@</div><div class="k w" data-k=" ">espacio</div><div class="k f" data-k=".">.</div><div class="k f m">ir</div></div></div>';
const TECLADO_NUM = '<div class="kp">' + '123456789'.split('').map((k) => `<div class="k" data-k="${k}">${k}</div>`).join('')
  + '<div class="k v"></div><div class="k" data-k="0">0</div><div class="k v">⌫</div></div>';

function dniFrente(D) {
  return `<div class="dni frente"><div class="bd"><b>REPÚBLICA DE HONDURAS<br><span style="font-weight:600;font-size:6.5px">DOCUMENTO NACIONAL DE IDENTIFICACIÓN</span></b><div class="flag"></div></div>
    <div class="ph">${CARA_DNI}</div>
    <div class="ln"><p><span>NOMBRE</span><b>${D.nombre}</b></p><p><span>NACIMIENTO</span><b>14 / 03 / 1990</b></p>
      <p><span>No. DE IDENTIDAD</span><b>${D.dni}</b></p><p><span>VENCE</span><b>14 / 03 / 2032</b></p></div>
    <svg class="firma" viewBox="0 0 70 26"><path d="M2 18c6-14 10 6 14-4s6-8 8 2 6-10 10-4 4 8 10 0 10 4 16-2" fill="none" stroke="#223" stroke-width="1.6"/></svg>
    <div class="holo"></div></div>`;
}
function dniAtras(D) {
  const r = rng(7); let bars = '';
  for (let i = 0; i < 64; i++) bars += `<i style="width:${1 + Math.floor(r() * 3)}px"></i>`;
  return `<div class="dni atras"><div class="bd"><b>REGISTRO NACIONAL DE LAS PERSONAS</b><div class="flag"></div></div>
    <div class="bars">${bars}</div>
    <div class="tx">LUGAR DE NACIMIENTO: FRANCISCO MORAZÁN, TEGUCIGALPA<br>DOMICILIO: COL. PALMIRA · ESTADO CIVIL: SOLTERO</div>
    <div class="mrz">IDHND${D.dni.replace(/-/g, '')}&lt;&lt;&lt;&lt;&lt;<br>9003145M3203148HND&lt;&lt;&lt;&lt;&lt;&lt;<br>LOPEZ&lt;&lt;JOSE&lt;ANTONIO&lt;&lt;&lt;&lt;&lt;</div></div>`;
}

// Retrato ilustrado (el mismo del DNI y de la prueba de vida)
function caraSVG(id = '') {
  return `<svg viewBox="0 0 262 262" xmlns="http://www.w3.org/2000/svg">
    <path d="M30 262c6-50 44-70 101-70s95 20 101 70z" fill="#1e2a44"/>
    <path d="M108 170h46v34c-10 10-36 10-46 0z" fill="#c99671"/>
    <g ${id ? `id="${id}cab"` : ''}>
      <ellipse cx="72" cy="122" rx="11" ry="18" fill="#cf9b75"/><ellipse cx="190" cy="122" rx="11" ry="18" fill="#cf9b75"/>
      <ellipse cx="131" cy="118" rx="60" ry="74" fill="#e0b18c"/>
      <g ${id ? `id="${id}ras"` : ''}>
        <path d="M84 150c8 36 30 50 47 50s39-14 47-50c-6 10-14 14-20 14-8-6-18-8-27-8s-19 2-27 8c-6 0-14-4-20-14z" fill="#3a2a22"/>
        <path d="M100 98c8-5 18-5 24-1M138 97c6-4 16-4 24 1" stroke="#2c1e17" stroke-width="5" stroke-linecap="round" fill="none"/>
        <ellipse cx="112" cy="114" rx="6" ry="6.5" fill="#2a1d16"/><ellipse cx="150" cy="114" rx="6" ry="6.5" fill="#2a1d16"/>
        <circle cx="114" cy="112" r="1.8" fill="#fff"/><circle cx="152" cy="112" r="1.8" fill="#fff"/>
        <path d="M131 118v20c-4 2-8 3-10 2" stroke="#b9805e" stroke-width="3.5" fill="none" stroke-linecap="round"/>
        <path d="M114 160c10 6 24 6 34 0" stroke="#7a3d33" stroke-width="5" fill="none" stroke-linecap="round"/>
      </g>
      <path d="M70 108c-4-44 22-70 62-70 38 0 64 22 60 68-6-18-14-30-30-34-18 8-48 8-70 0-12 6-18 18-22 36z" fill="#2c1e17"/>
    </g></svg>`;
}
const CARA_DNI = caraSVG();

const LAPTOP = '<svg class="lap" viewBox="0 0 150 120"><rect x="22" y="8" width="106" height="74" rx="6" fill="#eaf0fb" stroke="#2450a2" stroke-width="4"/><rect x="32" y="18" width="86" height="54" rx="3" fill="#fff"/><path d="M40 30h40M40 40h70M40 50h55M40 60h30" stroke="#95c94a" stroke-width="4" stroke-linecap="round" class="lns"/><path d="M8 92h134l-8 14H16z" fill="#2450a2"/><rect x="60" y="94" width="30" height="4" rx="2" fill="#9fb3d9"/></svg>';
const MAPA = '<svg viewBox="0 0 338 150"><rect width="338" height="150" fill="#e7edf3"/><path d="M0 40L338 70M0 110L338 96M80 0L120 150M220 0L250 150M0 75L338 30" stroke="#fff" stroke-width="10"/><path d="M160 0L180 150" stroke="#fdd10b" stroke-width="8"/><rect x="20" y="10" width="40" height="22" rx="3" fill="#cfe3c4"/><rect x="270" y="105" width="50" height="30" rx="3" fill="#cfe3c4"/><g class="pin" transform="translate(176 72)"><path d="M0 0c-14-14-14-34 0-34s14 20 0 34z" transform="scale(1)" fill="#2450a2"/><circle cx="0" cy="-20" r="5" fill="#fff"/></g></svg>';
const OK_GRANDE = '<svg class="ok" viewBox="0 0 70 70"><circle cx="35" cy="35" r="33" fill="#0a9a48"/><path class="okp" d="M20 36l10 10 20-22" fill="none" stroke="#fff" stroke-width="6" stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="48" stroke-dashoffset="48"/></svg>';

// ---- Las pantallas ----
function crearPantallas(G) {
  const D = G.datos;
  const S = [];

  // 1. Inicio en la App
  S.push({ html: `<div class="top poly">${poligonos(390, 520, 3)}</div>
      <div class="brand"><img src="assets/marca.png"><div>BANCO<span>FICENSA</span></div></div>
      <div class="card"><h4>Inicio de sesión</h4><div class="inp">${D.usuario}</div>
        <div class="fid">${ICO.faceid}</div><div class="o">Ingresar con Face ID<br>o ingresar con contraseña</div></div>
      <div class="quick"><div class="q"><div class="c">${ICO.usuario}</div>Crear<br>usuario</div>
        <div class="q main" id="btnAbrir"><div class="c">${ICO.cuenta}<div class="ring"></div></div>Abrir<br>cuenta</div>
        <div class="q"><div class="c">${ICO.candado}</div>Bloquear<br>usuario</div></div>
      <div class="tab">${TAB.map((x) => { const [n, p] = x.split('|'); return `<div><svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">${p}</svg>${n}</div>`; }).join('')}</div>`,
    taps: [{ at: 2.9, sel: '#btnAbrir .c', hint: 'Toca “Abrir cuenta”' }],
    anim(lt, el) {
      const r = el.querySelector('.ring'), k = prog(lt, 1.2, 2.6);
      r.style.opacity = lt < 1.2 ? 0 : lt < 3.4 ? .9 : 0;
      r.style.transform = `scale(${1 + .12 * Math.sin(k * Math.PI * 4)})`;
    } });

  // 2. Instrucciones de autenticación
  const consejos = ['Ubica tu DNI en un ambiente con buena iluminación.', 'Evita sombras y reflejos sobre el documento.',
    'Colócalo sobre una superficie de color oscuro para lograr contraste.', 'Evita el flash para reducir los reflejos.'];
  S.push({ html: `${HDR}<div class="cuerpo"><div class="ttl" style="font-size:27px;margin-top:8px">AUTENTICACIÓN</div>${STP(1)}
      <ul>${consejos.map((c) => `<li><i>${ICO.check}</i>${c}</li>`).join('')}</ul></div>
      <div class="btn" id="b2">CONTINUAR</div>${FTR(11)}`,
    taps: [{ at: 4.0, sel: '#b2' }],
    sfx: [.5, .85, 1.2, 1.55].map((at) => ({ at, tipo: 'pop' })),
    anim(lt, el) {
      el.querySelectorAll('li').forEach((li, i) => {
        const a = .5 + i * .35, k = eo(prog(lt, a, a + .4));
        li.style.opacity = k; li.style.transform = `translateX(${(1 - k) * 30}px)`;
        li.querySelector('i').style.transform = `scale(${eb(prog(lt, a + .1, a + .45))})`;
      });
    } });

  // 3 y 5. Capturas del DNI
  const camara = (frente) => ({ html: `${HDR}<div class="cuerpo"><div class="ttl">${frente ? 'Captura Frontal' : 'Captura Posterior'}</div>
      <div class="sub">Coloca y encuadra ${frente ? 'el frontal' : 'la parte posterior'} de tu DNI dentro del recuadro y presiona “TOMAR FOTO”.</div>
      <div class="visor"><div class="esq e1"></div><div class="esq e2"></div><div class="esq e3"></div><div class="esq e4"></div>
        ${frente ? dniFrente(D) : dniAtras(D)}<div class="scan"></div><div class="flash"></div><div class="okchip">✓ Foto capturada</div></div>
      <div class="ayuda"><span>☀ Buena luz</span><span>◼ Fondo oscuro</span><span>⚡ Sin flash</span></div></div>
      <div class="btn tf">TOMAR FOTO</div>${FTR(frente ? 21 : 25)}`,
    taps: [{ at: 3.4, sel: '.tf', hint: 'Toma la foto' }],
    sfx: [{ at: 1.8, tipo: 'ok' }, { at: 3.45, tipo: 'shutter' }],
    clase: 's-cam',
    anim(lt, el) {
      const dni = el.querySelector('.dni'), k = eio(prog(lt, .3, 1.7));
      dni.style.transform = `translate(${(1 - k) * 60}px, ${(1 - k) * 34}px) rotate(${(1 - k) * -14}deg) scale(${lerp(.78, 1, k)})`;
      const ok = lt > 1.8;
      el.querySelectorAll('.esq').forEach((e) => { e.style.borderColor = ok ? '#4fd17e' : '#fff'; e.style.transform = `scale(${ok ? 1 + .15 * (1 - eo(prog(lt, 1.8, 2.2))) : 1})`; });
      const sc = el.querySelector('.scan'), sk = (lt * .9) % 1;
      sc.style.top = `${20 + 188 * (sk < .5 ? sk * 2 : 2 - sk * 2)}px`;
      sc.style.opacity = lt > .4 && lt < 3.4 ? 1 : 0;
      el.querySelector('.flash').style.opacity = lt > 3.45 ? 1 - eo(prog(lt, 3.45, 3.95)) : 0;
      const ch = el.querySelector('.okchip'), c = eb(prog(lt, 3.8, 4.2));
      ch.style.opacity = prog(lt, 3.8, 3.95); ch.style.transform = `translateX(-50%) scale(${c})`;
    } });
  S.push(camara(true));

  // 4. Validación de imagen
  let ticks = '';
  for (let i = 0; i < 60; i++) { const a = i / 60 * Math.PI * 2;
    ticks += `<line x1="${105 + Math.cos(a) * 92}" y1="${105 + Math.sin(a) * 92}" x2="${105 + Math.cos(a) * 102}" y2="${105 + Math.sin(a) * 102}" stroke="#0a9a48" stroke-width="3" stroke-linecap="round" opacity="${(.25 + .75 * (i / 60)).toFixed(2)}"/>`; }
  S.push({ html: `<div class="fondo">${HDR}<div class="cuerpo"><div class="ttl" style="font-size:27px;margin-top:8px">AUTENTICACIÓN</div>${STP(1)}
        <ul style="list-style:none;margin-top:30px">${consejos.map((c) => `<li style="font-size:14px;margin-bottom:16px">${c}</li>`).join('')}</ul></div>${FTR(11)}</div><div class="velo"></div>
      <div class="val"><div class="anillo"><svg viewBox="0 0 210 210"><g class="tk">${ticks}</g>
          <circle cx="105" cy="105" r="80" fill="none" stroke="#e1e7f0" stroke-width="8"/>
          <circle class="arc" cx="105" cy="105" r="80" fill="none" stroke="#95c94a" stroke-width="8" stroke-linecap="round" stroke-dasharray="502.65" stroke-dashoffset="502.65" transform="rotate(-90 105 105)"/>
          <circle class="dot" cx="105" cy="105" r="62" fill="#0a9a48"/>
          <path class="chk" d="M78 106l18 18 37-40" fill="none" stroke="#fff" stroke-width="12" stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="90" stroke-dashoffset="90"/></svg></div>
        <div class="lbl">VALIDANDO</div><div class="lbl2">Estamos revisando tu imagen…</div></div>`,
    sfx: [{ at: 3.2, tipo: 'exito' }],
    anim(lt, el) {
      el.querySelector('.tk').setAttribute('transform', `rotate(${lt * 120} 105 105)`);
      el.querySelector('.arc').setAttribute('stroke-dashoffset', 502.65 * (1 - eio(prog(lt, .4, 3.1))));
      const d = el.querySelector('.dot'), k = eb(prog(lt, 3.1, 3.5));
      d.setAttribute('r', 62 * k);
      el.querySelector('.chk').setAttribute('stroke-dashoffset', 90 * (1 - eo(prog(lt, 3.3, 3.7))));
      const listo = lt > 3.3;
      el.querySelector('.lbl').textContent = listo ? '¡IMAGEN VÁLIDA!' : 'VALIDANDO' + '.'.repeat(Math.floor(lt * 3) % 4);
      el.querySelector('.lbl').style.color = listo ? '#0a9a48' : '';
      el.querySelector('.lbl2').textContent = listo ? 'Tu DNI se leyó correctamente' : 'Estamos revisando tu imagen…';
      el.querySelector('.anillo').style.transform = `scale(${1 + .08 * Math.sin(prog(lt, 3.1, 3.7) * Math.PI)})`;
    } });

  S.push(camara(false));

  // 6. Prueba de vida
  S.push({ html: `${HDR}<div class="cam"></div><div class="q6">Gira tu rostro a la derecha</div>
      <div class="cara"><div class="mask">${caraSVG('v')}</div>
        <svg viewBox="0 0 290 290"><circle cx="145" cy="145" r="138" fill="none" stroke="rgba(255,255,255,.35)" stroke-width="6"/>
          <circle class="arc" cx="145" cy="145" r="138" fill="none" stroke="#fdd10b" stroke-width="9" stroke-linecap="round" stroke-dasharray="867.1" stroke-dashoffset="867.1" transform="rotate(-90 145 145)"/>
          <g class="okc" opacity="0"><circle cx="232" cy="52" r="26" fill="#0a9a48"/><path d="M220 52l8 8 16-17" stroke="#fff" stroke-width="5" fill="none" stroke-linecap="round" stroke-linejoin="round"/></g></svg></div>
      <svg class="flecha" viewBox="0 0 50 50"><path d="M10 25h28M28 13l12 12-12 12" stroke="#fdd10b" stroke-width="6" fill="none" stroke-linecap="round" stroke-linejoin="round"/></svg>
      <div class="estado">VALIDANDO</div>`,
    sfx: [{ at: 3.6, tipo: 'exito' }],
    anim(lt, el) {
      const giro = eio(prog(lt, 1.0, 2.2)) - eio(prog(lt, 2.7, 3.3));
      el.querySelector('#vras').setAttribute('transform', `translate(${giro * 30} 0) scale(${1 - giro * .06} 1)`);
      el.querySelector('#vcab').setAttribute('transform', `translate(${giro * 8} 0)`);
      const listo = lt > 3.5;
      const arc = el.querySelector('.arc');
      arc.setAttribute('stroke-dashoffset', 867.1 * (1 - eio(prog(lt, .7, 3.4))));
      arc.setAttribute('stroke', listo ? '#4fd17e' : '#fdd10b');
      const ok = el.querySelector('.okc'), k = eb(prog(lt, 3.5, 3.9));
      ok.setAttribute('opacity', k > 0 ? 1 : 0); ok.setAttribute('transform', `translate(232 52) scale(${k}) translate(-232 -52)`);
      const f = el.querySelector('.flecha'), fa = ventana(lt, .6, 2.4);
      f.style.opacity = fa; f.style.transform = `translateX(${Math.sin(lt * 8) * 6}px)`;
      const e = el.querySelector('.estado');
      e.textContent = listo ? '¡ROSTRO VERIFICADO!' : 'VALIDANDO';
      e.style.color = listo ? '#4fd17e' : '#fff';
      el.querySelector('.q6').textContent = lt < 2.6 ? 'Gira tu rostro a la derecha' : lt < 3.5 ? 'Ahora mira al frente' : 'Prueba de vida completada';
    } });

  // 7. Datos de contacto
  S.push({ html: `${HDR}<div class="cuerpo"><div class="ttl">MIS DATOS<br>PERSONALES</div>${STP(2)}
      <div class="campo"><label>Número de teléfono móvil</label><div class="inp" id="i7a"><span class="pre">+504</span><span class="v"></span></div></div>
      <div class="campo"><label>Correo electrónico</label><div class="inp" id="i7b"><span class="v"></span></div></div>
      <div class="btn" id="b7" style="margin-top:22px">CONTINUAR</div></div>${TECLADO}`,
    escribir: [{ sel: '#i7a', texto: D.telefono, at: .6, dur: 1.0, ph: 'xxxx-xxxx' },
      { sel: '#i7b', texto: D.correo, at: 1.9, dur: 1.5, ph: 'Correo electrónico' }],
    taps: [{ at: 4.1, sel: '#b7' }] });

  // 8. Verificación OTP
  S.push({ html: `${HDR}<div class="cuerpo"><div class="ttl">VERIFICACIÓN</div>
      <div class="msg">Hemos enviado un código de verificación a tu correo. Este tiene duración de un minuto.</div>
      <div class="otp">${'<div></div>'.repeat(6)}</div><div class="timer">El código vence en <b>00:59</b></div>
      <div class="btn" id="b8">CONTINUAR</div></div>${TECLADO_NUM}
      <div class="notif"><div class="ic">${ICO.correo}</div><p><b>Banco Ficensa · ahora</b>Tu código de verificación es ${D.otp.slice(0, 3)} ${D.otp.slice(3)}</p></div>`,
    otp: { at: 1.4, dur: 1.4 },
    sfx: [{ at: .45, tipo: 'notif' }],
    taps: [{ at: 4.0, sel: '#b8' }],
    anim(lt, el) {
      const n = el.querySelector('.notif'), k = ventana(lt, .45, 2.3, .4);
      n.style.transform = `translateY(${(1 - k) * -150}px)`; n.style.opacity = k;
      const s = Math.max(0, 59 - Math.floor(lt * 1.6));
      el.querySelector('.timer b').textContent = `00:${String(s).padStart(2, '0')}`;
    } });

  // 9. Datos de domicilio
  S.push({ html: `${HDR}<div class="cuerpo"><div class="ttl">MIS DATOS PERSONALES</div>
      <div class="campo"><label>Municipio</label><div class="inp sel" id="i9m"><span class="ph">Selecciona</span></div></div>
      <div class="campo"><label>Dirección de la residencia</label><div class="inp" id="i9a"><span class="v"></span></div></div>
      <div class="campo"><label>Dirección (otra referencia)</label><div class="inp" id="i9b"><span class="v"></span></div></div>
      <div class="campo"><label>Barrio o colonia</label><div class="inp" id="i9c"><span class="v"></span></div></div></div>
      <div class="btn" id="b9">CONTINUAR</div>${TECLADO}`,
    escribir: [{ sel: '#i9a', texto: D.direccion, at: 1.0, dur: 1.4 }, { sel: '#i9b', texto: D.referencia, at: 2.55, dur: .8 },
      { sel: '#i9c', texto: D.barrio, at: 3.45, dur: .45 }],
    taps: [{ at: .55, sel: '#i9m' }, { at: 4.4, sel: '#b9' }],
    anim(lt, el) {
      const m = el.querySelector('#i9m');
      m.innerHTML = lt > .7 ? D.municipio : '<span class="ph">Selecciona</span>';
      m.classList.toggle('foco', lt > .5 && lt < .95);
    } });

  // 10. Selección de agencia
  S.push({ html: `${HDR}<div class="cuerpo"><div class="ttl">ELIGE TU AGENCIA<br>MÁS CERCANA</div>${STP(3)}
      <div class="campo"><label>Localidad</label><div class="inp sel">${D.municipio}</div></div>
      <div class="campo" style="position:relative"><label>Agencias</label><div class="inp sel" id="i10"><span class="ph">Selecciona una agencia</span></div>
        <div class="drop" style="top:64px">${D.agencias.map((a) => `<div>${a}</div>`).join('')}</div></div>
      <div class="mapa">${MAPA}</div></div>
      <div class="btn" id="b10">SOLICITAR</div>${FTR(41)}`,
    taps: [{ at: 1.0, sel: '#i10' }, { at: 2.4, sel: '.drop div' }, { at: 3.9, sel: '#b10', hint: 'Presiona “Solicitar”' }],
    anim(lt, el) {
      const dr = el.querySelector('.drop'), k = ventana(lt, 1.05, 2.5, .22);
      dr.style.opacity = k > 0 ? 1 : 0; dr.style.transform = `scaleY(${k})`;
      dr.querySelectorAll('div').forEach((d, i) => d.classList.toggle('hl', lt > 1.9 && i === 0));
      const sel = el.querySelector('#i10');
      sel.innerHTML = lt > 2.45 ? D.agencias[0] : '<span class="ph">Selecciona una agencia</span>';
      sel.classList.toggle('foco', lt > .95 && lt < 2.5);
      const m = el.querySelector('.mapa'), mk = eo(prog(lt, 2.5, 3.0));
      m.style.opacity = .35 + .65 * mk;
      el.querySelector('.mapa .pin').setAttribute('transform', `translate(176 ${72 - 30 * (1 - eb(prog(lt, 2.5, 3.0)))}) scale(${.4 + .6 * eb(prog(lt, 2.5, 3.0))})`);
    } });

  // 11. Invitación a Banca en Línea
  S.push({ html: `${HDR}<div class="cuerpo">${LAPTOP}<div class="t1">TE INVITAMOS A CONOCER</div><div class="t2">NUESTRA BANCA EN LÍNEA</div>
      <div class="msg">Te hemos enviado a tu correo electrónico tus credenciales temporales para ingresar a Banca en Línea. Por seguridad, cámbialas en tu primer ingreso.</div></div>
      <div class="btn" id="b11">CONTINUAR</div>${FTR(51)}`,
    taps: [{ at: 4.0, sel: '#b11' }],
    anim(lt, el) {
      const l = el.querySelector('.lap'), k = eb(prog(lt, .3, .9));
      l.style.transform = `scale(${k}) translateY(${Math.sin(lt * 2.4) * 3}px)`;
      el.querySelectorAll('.lns').forEach((p) => { p.style.strokeDasharray = 300; p.style.strokeDashoffset = 300 * (1 - eo(prog(lt, .8, 1.8))); });
      [['.t1', .7], ['.t2', .9], ['.msg', 1.2]].forEach(([s, a]) => { const e = el.querySelector(s), q = eo(prog(lt, a, a + .5));
        e.style.opacity = q; e.style.transform = `translateY(${(1 - q) * 18}px)`; });
    } });

  // 12. Confirmación
  S.push({ html: `<div style="position:absolute;inset:0">${HDR}<div class="cuerpo">${LAPTOP}<div class="t1" style="font-size:21px;font-weight:800;color:#2450a2;text-align:center;margin-top:26px">TE INVITAMOS A CONOCER</div></div>${FTR(51)}</div>
      <div class="dim" style="opacity:.55"></div>
      <div class="modal"><div class="mh">Notificación</div>${OK_GRANDE}
        <p>Cuenta creada exitosamente, credenciales enviadas a su correo. Comuníquese al Call Center si necesita asistencia.</p>
        <div class="btn verde" id="b12">Cerrar</div></div>`,
    sfx: [{ at: .4, tipo: 'exito' }],
    taps: [{ at: 4.2, sel: '#b12', hint: 'Presiona “Cerrar”' }],
    anim(lt, el) {
      const m = el.querySelector('.modal'), k = eb(prog(lt, .3, .8)), out = eo(prog(lt, 4.45, 4.8));
      m.style.transform = `scale(${lerp(.6, 1, k) * (1 - out * .3)})`; m.style.opacity = Math.min(prog(lt, .3, .5), 1 - out);
      el.querySelector('.dim').style.opacity = .55 * (1 - out);
      el.querySelector('.okp').setAttribute('stroke-dashoffset', 48 * (1 - eo(prog(lt, .7, 1.1))));
    } });

  // 13. Pantalla final de la app (cierre del video)
  S.push({ html: `<div class="poly">${poligonos(390, 842, 61)}</div><div class="centro"><img src="assets/marca.png">
      <h3>¡Bienvenido a<br>Banco Ficensa!</h3><p>Tu cuenta está lista</p></div>`, extra: true,
    anim(lt, el) {
      const c = el.querySelector('.centro'), k = eb(prog(lt, .1, .7));
      c.style.transform = `scale(${lerp(.7, 1, k)})`; c.style.opacity = prog(lt, .1, .3);
    } });

  return S;
}
