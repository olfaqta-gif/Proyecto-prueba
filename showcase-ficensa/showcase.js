// Motor del showcase: todo se dibuja a partir del tiempo t (segundos), así el render cuadro por cuadro
// sale idéntico a la vista en el navegador. window.__seek(t) pinta el cuadro; window.__eventos
// lista los momentos con sonido (los lee musica.py).
(() => {
  // Formato (16x9 o 9x16) y versión (completa o corta) llegan en la URL: showcase.html?formato=9x16&version=corta
  const Q = new URLSearchParams(location.search);
  const FMT = Q.get('formato') === '9x16' ? '9x16' : '16x9', VER = Q.get('version') === 'corta' ? 'corta' : 'completa';
  const VERT = FMT === '9x16', W = VERT ? 1080 : 1920, H = VERT ? 1920 : 1080;
  document.body.classList.toggle('v916', VERT);
  const G = window.GUION, V = VER === 'corta' ? G.versiones.corta : {};
  const PASOS = V.pasos || G.pasos.map((p, i) => ({ ...p, pantalla: i + 1 }));
  const CAPS = V.capitulos || G.capitulos;
  const S0 = V.inicioPasos || G.inicioPasos, DP = V.duracionPaso || G.duracionPaso, N = PASOS.length;
  // La animación está escrita en el tiempo de la versión completa: intro de 6,5 s, pasos de 5,4 s y cierre de 9,4 s.
  // Las versiones más cortas la recorren más rápido en cada tramo.
  const DPC = 5.4, SPD = DPC / DP, KI = S0 / 6.5, KO = V.cierre || 1;
  const FIN = S0 + N * DP;            // termina el último paso
  const TOTAL = FIN + 9.4 * KO;
  const SW1 = 2.9, SW2 = FIN + 4.6, SWD = .9;   // barridos de cintas (en tiempo de intro / de cierre)
  const tI = (x) => (x <= 6.5 ? x * KI : S0 + x - 6.5);   // tiempo de intro -> tiempo real
  const tO = (x) => FIN + (x - FIN) * KO;                  // tiempo de cierre -> tiempo real
  const PS = VERT ? .95 : 1;                               // escala del teléfono
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const EV = [];
  const ev = (t, tipo) => EV.push({ t: +t.toFixed(3), tipo });

  // ---------- Construcción ----------
  $('#stage').style.width = W + 'px'; $('#stage').style.height = H + 'px';
  $('#bgpoly').innerHTML = poligonos(VERT ? 1240 : 2080, VERT ? 2080 : 1240, 91, [16, 42, 100], [52, 104, 196], 120);
  const TODAS = crearPantallas(G);
  const PANT = [...PASOS.map((p) => p.pantalla), TODAS.length].map((n) => ({ ...TODAS[n - 1], n }));
  const inicio = (i) => (i < N ? S0 + i * DP : FIN);
  PANT.forEach((p, i) => {
    const d = document.createElement('div');
    d.className = 'scr ' + (p.clase || ''); d.id = 's' + p.n;
    d.innerHTML = p.html + '<div class="dim"></div>';
    $('#screens').appendChild(d); p.el = d; p.t0 = inicio(i);
    p.t1 = i < PANT.length - 1 ? inicio(i + 1) : Infinity;
    const at = (x) => p.t0 + x / SPD;
    (p.taps || []).forEach((tp) => ev(at(tp.at), 'tap'));
    (p.sfx || []).forEach((s) => ev(at(s.at), s.tipo));
    (p.escribir || []).forEach((w) => [...w.texto].forEach((_, k) => ev(at(w.at + k * w.dur / w.texto.length), 'tecla')));
    if (p.otp) for (let k = 0; k < 6; k++) ev(at(p.otp.at + k * p.otp.dur / 6), 'tecla');
    if (i > 0) ev(p.t0, 'swoosh');
  });

  // Portada
  $('#tcTitulo').innerHTML = G.intro.titulo.map((w, i) => `<span class="${i === 2 ? 'hl' : ''}">${w}</span>`).join('');
  $('#tcSub').textContent = G.intro.sub;
  $('#tcChips').innerHTML = G.intro.chips.map((c) => `<div class="chip"><i></i>${c}</div>`).join('');
  $('#tagline').innerHTML = [...'Apertura de cuenta digital'].map((c) => `<span>${c}</span>`).join('');

  // Panel
  const capDe = (paso) => CAPS.findIndex((c) => c.pasos.includes(paso));
  $('#caps').insertAdjacentHTML('beforeend', CAPS.map((c) => `<div class="cp">${c.nombre}</div>`).join(''));
  $('#pns').innerHTML = PASOS.map((p, i) => `<div class="pn"><div class="kick">${p.kicker}</div>
    <div class="fila"><div class="num">${String(i + 1).padStart(2, '0')}</div><div class="tt">${p.titulo}</div></div>
    <div class="ds">${p.texto}</div>
    <div class="tip"><div class="ico">${ICO.foco}</div><div class="tg">TIP</div><div class="tx">${p.tip}</div><div class="bar"></div><div class="brillo"></div></div></div>`).join('');
  $('#segs').innerHTML = '<div class="sg"><i></i></div>'.repeat(N);
  PASOS.forEach((_, i) => ev(S0 + i * DP + 1.3 / SPD, 'tip'));

  // Cierre
  $('#o1t').innerHTML = G.cierre.titulo.split(' ').map((w) => `<span>${w}</span>`).join(' ');
  $('#o1s').textContent = G.cierre.sub;
  $('#o1l').innerHTML = G.cierre.lista.map((x) => `<li><i>${ICO.check}</i>${x}</li>`).join('');
  G.cierre.lista.forEach((_, i) => ev(tO(FIN + 1.5 + i * .3), 'pop'));
  $('#o2t').textContent = G.cierre.cta; $('#o2n').textContent = G.cierre.nota;

  // Confeti (sale de los lados del teléfono)
  const CONF = [], rc = rng(5), COL = ['#fdd10b', '#95c94a', '#12c0f0', '#ffffff', '#0a9a48'];
  const TCONF = S0 + (N - 1) * DP + .4 / SPD;
  const PX = VERT ? 540 : 560, PY = VERT ? 1200 : 760;
  for (let i = 0; i < 110; i++) {
    const lado = i % 2 ? 1 : -1, el = document.createElement('i');
    el.style.background = COL[i % COL.length]; $('#conf').appendChild(el);
    CONF.push({ el, x0: PX + lado * 250, y0: PY, vx: -lado * (60 + rc() * 520) + (rc() - .5) * 200, vy: -(900 + rc() * 700),
      r: rc() * 360, vr: (rc() - .5) * 900, sp: 4 + rc() * 8, d: rc() * .25, s: .6 + rc() * .7 });
  }
  ev(TCONF, 'confeti');

  ev(tI(.3), 'logo'); ev(tI(SW1), 'barrido'); ev(tI(5.85), 'swoosh'); ev(tO(SW2), 'barrido'); ev(tO(SW2 + .7), 'logo');
  EV.sort((a, b) => a.t - b.t);
  window.__eventos = EV; window.__duracion = TOTAL;
  window.__marcas = { inicioPasos: S0, duracionPaso: DP, fin: FIN, barrido2: tO(SW2), total: TOTAL, formato: FMT, version: VER };

  // Posición de un elemento dentro de su pantalla (sin contar transformaciones)
  function posIn(el, root) {
    let x = 0, y = 0, e = el;
    while (e && e !== root) { x += e.offsetLeft; y += e.offsetTop; e = e.offsetParent; }
    return [x + el.offsetWidth / 2, y + el.offsetHeight / 2];
  }

  const sinTildes = (c) => c.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();

  // ---------- Pintar el cuadro t ----------
  function seek(t) {
    const ti = t <= S0 ? t / KI : 6.5 + t - S0;        // reloj de la intro
    const to = t <= FIN ? t : FIN + (t - FIN) / KO;     // reloj del cierre
    // Fondo vivo
    $('#bgpoly').style.transform = `translate(${Math.sin(t * .11) * 40}px, ${Math.cos(t * .09) * 30}px) scale(1.04)`;
    $('#b1').style.transform = `translate(${1250 + Math.sin(t * .23) * 220}px, ${-260 + Math.cos(t * .19) * 120}px)`;
    $('#b2').style.transform = `translate(${-200 + Math.cos(t * .17) * 200}px, ${600 + Math.sin(t * .21) * 140}px)`;
    $('#b3').style.transform = `translate(${700 + Math.sin(t * .15 + 2) * 300}px, ${820 + Math.cos(t * .2) * 100}px)`;
    $('#bgmarca').style.transform = `rotate(${-6 + Math.sin(t * .2) * 2}deg) translateY(${Math.sin(t * .3) * 14}px)`;

    // Intro con el logo
    const ip = $('#intro');
    ip.style.display = ti < SW1 + SWD / 2 ? 'flex' : 'none';
    if (ti < SW1 + SWD) {
      const m = $('#lg .marca'), k = eo(prog(ti, .25, 1.15));
      m.style.clipPath = `circle(${150 * k}% at 0% 100%)`;
      m.style.transform = `scale(${lerp(.55, 1, eb(prog(ti, .25, 1.05)))}) rotate(${(1 - eo(prog(ti, .25, 1.1))) * -18}deg)`;
      const tx = $('#lg .texto'), k2 = eo(prog(ti, .75, 1.5));
      tx.style.clipPath = `inset(0 ${100 * (1 - k2)}% 0 0)`; tx.style.transform = `translateX(${(1 - k2) * -50}px)`;
      $$('#tagline span').forEach((s, i) => { const q = eo(prog(ti, 1.3 + i * .025, 1.6 + i * .025));
        s.style.opacity = q; s.style.transform = `translateY(${(1 - q) * 22}px)`; });
      $('#introbar').style.width = `${420 * eio(prog(ti, 1.5, 2.4))}px`;
      $('#lg').style.transform = `scale(${1 + ti * .012})`;
    }

    // Barridos de cintas (amarillo, verde, celeste)
    const sw = (a) => prog(ti, a, a + SWD);
    const s1 = prog(ti, SW1, SW1 + SWD), s2 = prog(to, SW2, SW2 + SWD), act = (s1 > 0 && s1 < 1) ? s1 : (s2 > 0 && s2 < 1) ? s2 : -1;
    $('#sw').style.display = act < 0 ? 'none' : 'block';
    if (act >= 0) $$('#sw .rb').forEach((b, i) => { b.style.transform = `translateY(${lerp(2600, -2600, eio(act)) + (i - 1) * 380}px)`; });

    // Portada
    const tc = $('#tc');
    tc.style.display = ti > SW1 && ti < 6.6 ? 'flex' : 'none';
    if (ti < 6.6) {
      $$('#tcTitulo span').forEach((s, i) => { const a = 3.45 + i * .09, q = eb(prog(ti, a, a + .55));
        s.style.opacity = prog(ti, a, a + .15); s.style.transform = `translateY(${(1 - q) * 90}px) rotate(${(1 - q) * 6}deg)`; });
      const sq = eo(prog(ti, 4.2, 4.7)); $('#tcSub').style.opacity = sq; $('#tcSub').style.transform = `translateY(${(1 - sq) * 20}px)`;
      $$('#tcChips .chip').forEach((c, i) => { const q = eb(prog(ti, 4.5 + i * .13, 4.95 + i * .13));
        c.style.opacity = prog(ti, 4.5 + i * .13, 4.6 + i * .13); c.style.transform = `scale(${q})`; });
      $('.kick', tc).style.opacity = eo(prog(ti, 3.3, 3.8)); $('.kick', tc).style.letterSpacing = `${lerp(20, 8, eo(prog(ti, 3.3, 4)))}px`;
      const o = eio(prog(ti, 5.75, 6.35));
      tc.style.opacity = 1 - o; tc.style.transform = `scale(${1 - o * .12}) translateY(${-o * 60}px)`;
    }

    // Teléfono
    const pw = $('#phoneWrap'), fly = eo(prog(ti, 5.8, 7.0)), outk = eio(prog(to, SW2 - 1.2, SW2 + .3));
    pw.style.display = ti > 5.7 && to < SW2 + SWD ? 'block' : 'none';
    const ry = lerp(-46, -9 + Math.sin(t * .5) * 4, fly) + outk * 9, rz = (1 - fly) * 14;
    pw.style.transform = `scale(${PS}) translateY(${(1 - fly) * (VERT ? 1500 : 1150) + Math.sin(t * .9) * 8 * fly}px) rotateY(${ry}deg) rotateX(${Math.sin(t * .37) * 3}deg) rotateZ(${rz}deg) scale(${1 + outk * .04})`;

    // Pantallas de la app
    let actual = null;
    PANT.forEach((p, i) => {
      const el = p.el;
      const vis = (i === 0 ? t < p.t1 + .6 : t >= p.t0 && t < p.t1 + .6);
      el.style.display = vis ? 'block' : 'none';
      if (!vis) return;
      const kin = i === 0 ? 1 : eio(prog(t, p.t0, p.t0 + .55)), kout = eio(prog(t, p.t1, p.t1 + .55));
      el.style.transform = `translateX(${(1 - kin) * 100 - kout * 30}%)`;
      el.style.zIndex = i + 1;
      $('.dim', el).style.opacity = kout * .45;
      const lt = Math.max(0, t - p.t0) * SPD;
      if (t >= p.t0 && t < p.t1) actual = p;
      if (p.anim) p.anim(lt, el);
      escribir(p, lt, el);
    });
    toques(actual, t);

    // Panel
    const panel = $('#panel'), pin = eo(prog(ti, 6.4, 7.1)), pout = eio(prog(to, FIN + .1, FIN + .6));
    panel.style.display = ti > 6.3 && to < FIN + .7 ? 'block' : 'none';
    panel.style.opacity = pin * (1 - pout); panel.style.transform = `translateX(${(1 - pin) * 80 - pout * 60}px)`;
    const paso = clamp(Math.floor((t - S0) / DP), 0, N - 1), lt = (t - (S0 + paso * DP)) * SPD;
    $$('.pn').forEach((pn, i) => {
      pn.style.display = i === paso ? 'block' : 'none';
      if (i !== paso) return;
      const out = i < N - 1 ? eio(prog(lt, DPC - .38, DPC - .02)) : 0;
      const entra = (sel, a, dx = 0, dy = 40) => { const e = $(sel, pn), q = eo(prog(lt, a, a + .55));
        e.style.opacity = q * (1 - out); e.style.transform = `translate(${(1 - q) * dx}px, ${(1 - q) * dy - out * 24}px)`; };
      entra('.kick', .12, -30, 0); entra('.tt', .26); entra('.ds', .42);
      const nq = eb(prog(lt, .18, .75)), num = $('.num', pn);
      num.style.opacity = prog(lt, .18, .3) * (1 - out); num.style.transform = `translateY(${(1 - nq) * 120 - out * 24}px) scale(${lerp(.6, 1, nq)})`;
      const tip = $('.tip', pn), tq = eo(prog(lt, 1.3, 1.85));
      tip.style.opacity = prog(lt, 1.3, 1.5) * (1 - out);
      tip.style.transform = `translate(${(1 - tq) * 120}px, ${-out * 24}px) rotate(${(1 - tq) * 2}deg)`;
      $('.ico', tip).style.transform = `scale(${eb(prog(lt, 1.45, 1.9))}) rotate(${(1 - eo(prog(lt, 1.45, 2))) * -40}deg)`;
      $('.brillo', tip).style.left = `${lerp(-220, 900, eio(prog(lt, 1.8, 2.6)))}px`;
      $('.bar', tip).style.width = `${100 * prog(lt, 1.5, DPC - .2)}%`;
    });
    // Capítulos
    const cps = $$('#caps .cp'), ci = capDe(paso + 1), cprev = capDe(Math.max(1, paso)), ck = paso > 0 ? eio(prog(lt, 0, .5)) : 1;
    const sel = $('#capsel');
    sel.style.left = `${lerp(cps[cprev].offsetLeft, cps[ci].offsetLeft, ck)}px`;
    sel.style.width = `${lerp(cps[cprev].offsetWidth, cps[ci].offsetWidth, ck)}px`;
    cps.forEach((c, i) => c.classList.toggle('on', i === (ck > .5 ? ci : cprev)));
    $('#progLb').innerHTML = `Paso <b>${String(paso + 1).padStart(2, '0')}</b> de ${N}`;
    $$('#segs i').forEach((s, i) => { s.style.width = `${i < paso ? 100 : i === paso ? 100 * eio(prog(lt, 0, DPC)) : 0}%`; });

    // Confeti
    const tc0 = t - TCONF;
    $('#conf').style.display = tc0 > 0 && tc0 < 4 ? 'block' : 'none';
    if (tc0 > 0 && tc0 < 4) CONF.forEach((c) => {
      const u = Math.max(0, tc0 - c.d), drag = 1 - Math.exp(-u * 1.6);
      const x = c.x0 + c.vx * drag / 1.6 + Math.sin(u * c.sp) * 18, y = c.y0 + c.vy * drag / 1.6 + 260 * u * u;
      c.el.style.opacity = u > 0 ? 1 - prog(tc0, 3.2, 4) : 0;
      c.el.style.transform = `translate(${x}px, ${y}px) rotate(${c.r + c.vr * u}deg) scale(${c.s * Math.cos(u * c.sp)}, ${c.s})`;
    });

    // Cierre 1: ¡Así de fácil!
    const o1 = $('#out1'), o1v = to > FIN + .3 && to < SW2 + SWD;
    o1.style.display = o1v ? 'block' : 'none';
    if (o1v) {
      $$('#o1t span').forEach((s, i) => { const a = FIN + .45 + i * .14, q = eb(prog(to, a, a + .55));
        s.style.opacity = prog(to, a, a + .12); s.style.transform = `scale(${q}) rotate(${(1 - q) * -8}deg)`; });
      const q = eo(prog(to, FIN + 1.0, FIN + 1.5)); $('#o1s').style.opacity = q; $('#o1s').style.transform = `translateY(${(1 - q) * 24}px)`;
      $$('#o1l li').forEach((li, i) => { const a = FIN + 1.45 + i * .3, k = eo(prog(to, a, a + .45));
        li.style.opacity = k; li.style.transform = `translateX(${(1 - k) * 50}px)`;
        $('i', li).style.transform = `scale(${eb(prog(to, a + .05, a + .45))})`; });
    }

    // Cierre 2: logo en blanco
    const o2 = $('#out2'), o2v = to > SW2 + SWD / 2;
    o2.style.display = o2v ? 'flex' : 'none';
    if (o2v) {
      const a = SW2 + .6, m = $('.marca', o2), k = eo(prog(to, a, a + .85));
      m.style.clipPath = `circle(${150 * k}% at 0% 100%)`; m.style.transformOrigin = '0 100%';
      m.style.transform = `scale(${lerp(.55, 1, eb(prog(to, a, a + .8)))})`;
      const tx = $('.texto', o2), k2 = eo(prog(to, a + .45, a + 1.1));
      tx.style.clipPath = `inset(0 ${100 * (1 - k2)}% 0 0)`;
      [['#o2t', a + 1.2], ['#o2n', a + 1.5]].forEach(([s, b]) => { const q = eo(prog(to, b, b + .5));
        $(s).style.opacity = q; $(s).style.transform = `translateY(${(1 - q) * 26}px)`; });
      $('#o2b').style.width = `${420 * eio(prog(to, a + 1.6, a + 2.4))}px`;
      $('.lg2', o2).style.transform = `scale(${1 + (to - a) * .01})`;
    }
  }

  // Texto que se escribe, con cursor y la tecla que se ilumina
  function escribir(p, lt, el) {
    const teclas = $$('.kb .k, .kp .k', el); teclas.forEach((k) => k.classList.remove('on'));
    let tecla = null;
    (p.escribir || []).forEach((w) => {
      const inp = $(w.sel, el), v = $('.v', inp), L = w.texto.length, k = prog(lt, w.at, w.at + w.dur);
      const n = Math.floor(k * L + 1e-6);
      const foco = lt > w.at - .25 && lt < w.at + w.dur + .35;
      inp.classList.toggle('foco', foco);
      const cursor = foco && (k > 0 && k < 1 || Math.floor(lt * 2.5) % 2 === 0) ? '<span class="cur"></span>' : '';
      v.innerHTML = (n === 0 && w.ph && !foco ? `<span class="ph">${w.ph}</span>` : w.texto.slice(0, n).replace(/ /g, '&nbsp;')) + cursor;
      if (k > 0 && k < 1) tecla = sinTildes(w.texto[Math.min(n, L - 1)]);
    });
    if (p.otp) {
      const k = prog(lt, p.otp.at, p.otp.at + p.otp.dur), n = Math.floor(k * 6 + 1e-6);
      $$('.otp div', el).forEach((b, i) => { b.textContent = i < n ? G.datos.otp[i] : ''; b.classList.toggle('on', i === n && lt > p.otp.at - .3 && n < 6);
        b.style.transform = `scale(${i < n ? 1 + .15 * (1 - eo(prog(lt, p.otp.at + i * p.otp.dur / 6, p.otp.at + (i + .6) * p.otp.dur / 6))) : 1})`; });
      if (k > 0 && k < 1) tecla = G.datos.otp[Math.min(n, 5)];
    }
    if (tecla !== null) { const kk = teclas.find((x) => x.dataset.k === tecla); if (kk) kk.classList.add('on'); }
  }

  // Dedo, onda del toque y globo de ayuda
  function toques(p, t) {
    const f = $('#finger'), rp = $('#ripple'), hn = $('#hint');
    f.style.opacity = 0; rp.style.opacity = 0; hn.style.opacity = 0;
    if (!p || !p.taps) return;
    const lt = (t - p.t0) * SPD;
    p.taps.forEach((tp) => {
      const el = $(tp.sel, p.el); if (!el) return;
      const a = tp.at, press = ventana(lt, a - .1, a + .04, .08);
      el.style.transform = `scale(${1 - .07 * press})`;
      if (lt < a - 1.3 || lt > a + .6) return;
      const [x, y] = posIn(el, p.el);
      if (tp.hint) {
        const h = ventana(lt, a - 1.2, a - .1, .25);
        hn.textContent = tp.hint; hn.style.opacity = h;
        hn.style.left = `${clamp(x, 90, 300)}px`; hn.style.top = `${y - el.offsetHeight / 2 - 54}px`;
        hn.style.transform = `translateX(-50%) translateY(${(1 - h) * 10}px) scale(${lerp(.8, 1, h)})`;
      }
      if (lt < a - .75) return;
      const k1 = eio(prog(lt, a - .75, a - .1)), k2 = eio(prog(lt, a + .15, a + .55));
      const fx = x + lerp(120, 0, k1) + 60 * k2, fy = y + lerp(220, 0, k1) + 110 * k2;
      f.style.opacity = Math.min(prog(lt, a - .75, a - .5), 1 - prog(lt, a + .3, a + .55));
      f.style.transform = `translate(${fx - 26}px, ${fy - 4}px) rotate(-10deg) scale(${1 - .12 * press})`;
      if (lt >= a) { const r = prog(lt, a, a + .5); rp.style.opacity = (1 - r) * .95;
        rp.style.left = `${x}px`; rp.style.top = `${y}px`; rp.style.transform = `scale(${.2 + 1.3 * eo(r)})`; }
    });
  }

  // ---------- Vista en el navegador / render ----------
  window.__seek = seek;
  window.__ajustar = () => {
    const s = Math.min(innerWidth / W, innerHeight / H);
    const st = $('#stage'); st.style.transform = `scale(${s})`;
    st.style.left = `${(innerWidth - W * s) / 2}px`; st.style.top = `${(innerHeight - H * s) / 2}px`;
  };
  addEventListener('resize', window.__ajustar);
  window.__ajustar();
  if (Q.has('render')) { seek(0); return; }
  let t0 = performance.now() - (parseFloat((location.hash.match(/t=([\d.]+)/) || [])[1]) || 0) * 1000, pausa = false, tp = 0;
  addEventListener('keydown', (e) => { if (e.code === 'Space') { pausa = !pausa; if (!pausa) t0 = performance.now() - tp * 1000; } });
  const loop = () => { if (!pausa) { tp = ((performance.now() - t0) / 1000) % TOTAL; seek(tp); } requestAnimationFrame(loop); };
  document.fonts.ready.then(loop);
})();
