// Banda sonora sutil y corporativa (sin voz) a partir de out/cues.json -> out/audio.wav
const fs = require('fs');
const path = require('path');
const SR = 48000;
const cues = JSON.parse(fs.readFileSync(path.join(__dirname, 'out', 'cues.json')));
const DUR = +(process.argv[2] || 67.5);
const N = Math.ceil(DUR * SR);
const L = new Float32Array(N), R = new Float32Array(N), send = new Float32Array(N);
const TAU = Math.PI * 2;
let seed = 7;
const rnd = () => ((seed = (seed * 1664525 + 1013904223) >>> 0) / 4294967296);
const noise = () => rnd() * 2 - 1;
function biquad(type) {
  let x1 = 0, x2 = 0, y1 = 0, y2 = 0;
  return (x, f, q = .7) => {
    const w = TAU * Math.min(f, SR * .45) / SR, c = Math.cos(w), al = Math.sin(w) / (2 * q);
    let b0, b1, b2;
    if (type === 'lp') { b0 = (1 - c) / 2; b1 = 1 - c; b2 = b0; }
    else if (type === 'hp') { b0 = (1 + c) / 2; b1 = -(1 + c); b2 = b0; }
    else { b0 = al; b1 = 0; b2 = -al; }
    const a0 = 1 + al, a1 = -2 * c, a2 = 1 - al;
    const y = (b0 * x + b1 * x1 + b2 * x2 - a1 * y1 - a2 * y2) / a0;
    x2 = x1; x1 = x; y2 = y1; y1 = y; return y;
  };
}
const env = (t, a, d) => t < a ? t / a : Math.exp(-(t - a) / d);
function add(t, len, fn, gain, pan = 0, rv = .6) {
  const s0 = Math.floor(t * SR), n = Math.floor(len * SR);
  const gl = gain * Math.cos((pan + 1) * Math.PI / 4) * 1.414, gr = gain * Math.sin((pan + 1) * Math.PI / 4) * 1.414;
  for (let i = 0; i < n; i++) { const k = s0 + i; if (k < 0 || k >= N) continue; const v = fn(i / SR);
    L[k] += v * gl; R[k] += v * gr; send[k] += v * gain * rv; }
}
// nota "felt piano / marimba suave"
function soft(t, f, g, pan = 0) {
  const lp = biquad('lp');
  add(t, 2.2, tt => lp(Math.sin(TAU * f * tt) + .25 * Math.sin(TAU * f * 2 * tt) * Math.exp(-tt * 5) + .08 * Math.sin(TAU * f * 3 * tt) * Math.exp(-tt * 9), 2600) * env(tt, .006, .55), g, pan, .9);
}
const PENT = [392, 440, 523.25, 587.33, 659.26, 783.99, 880];
const FX = {
  air(t) { const bp = biquad('bp'), len = 1.4;
    add(t - .7, len, tt => { const p = tt / len; return bp(noise(), 300 + 1500 * Math.sin(Math.PI * p), .9) * Math.pow(Math.sin(Math.PI * p), 2) * 2; }, .06, 0, .4); },
  soft(t, c) { soft(t, PENT[(c.n || 0) % PENT.length], .055, ((c.n || 0) % 4 - 1.5) / 4); },
  bell(t, c) { const base = [523.25, 587.33, 659.26, 698.46, 783.99][(c.n || 0) % 5];
    [1, 1.5, 2].forEach((m, j) => soft(t + j * .09, base * m, .045, (j - 1) * .3)); },
  tick(t) { const bp = biquad('bp'); add(t, .04, tt => bp(noise(), 3200, 2) * env(tt, .0005, .004) * 1.5 + Math.sin(TAU * 1900 * tt) * env(tt, .0005, .006) * .3, .035, (rnd() - .5) * .4, .2); },
  key(t) { const bp = biquad('bp'), f = 1800 + rnd() * 900; add(t, .03, tt => bp(noise(), f, 1.5) * env(tt, .0005, .004), .025, (rnd() - .5) * .3, .1); },
  click(t) { add(t, .08, tt => Math.sin(TAU * 900 * tt) * env(tt, .001, .015), .06, 0, .3); },
  msg(t) { soft(t, 659.26, .04, -.3); soft(t + .07, 880, .03, -.3); },
  msg2(t) { soft(t, 880, .035, .3); soft(t + .07, 659.26, .035, .3); },
  whisk(t) { const bp = biquad('bp'), len = .5;
    add(t, len, tt => { const p = tt / len; return bp(noise(), 800 + 2500 * p, 1.2) * Math.sin(Math.PI * p) * 1.6; }, .035, 0, .3); },
  final(t) { [261.63, 392, 523.25, 659.26, 783.99].forEach((f, j) => soft(t + j * .12, f, .045, (j - 2) / 4)); },
  pad_start() {}, pad_end() {},
};
cues.forEach(c => FX[c.type] && FX[c.type](c.t, c));

// ---------- música: pad cálido, sin batería ----------
const ct = ty => (cues.find(c => c.type === ty) || {}).t;
const M0 = ct('pad_start') || .2, MEND = ct('pad_end') || DUR - 2.5;
const CH = [ // Dmaj9 – Bm7 – Gmaj7 – A6 (voicings abiertos)
  { r: 73.42, n: [146.83, 220, 277.18, 329.63, 369.99] },
  { r: 61.74, n: [123.47, 185, 220, 293.66, 329.63] },
  { r: 49, n: [98, 146.83, 196, 246.94, 293.66] },
  { r: 55, n: [110, 164.81, 220, 277.18, 329.63] },
];
const CHL = 4.8; // segundos por acorde
const lp1 = biquad('lp'), lp2 = biquad('lp');
const music = new Float32Array(N);
for (let k = Math.floor(M0 * SR); k < N; k++) {
  const t = k / SR, ci = Math.floor((t - M0) / CHL), ph = ((t - M0) % CHL) / CHL;
  const cur = CH[ci % 4], prev = CH[(ci + 3) % 4];
  const x = Math.min(1, ph / .18); // fundido entre acordes
  const voice = ch => ch.n.reduce((s, f, j) => s + Math.sin(TAU * f * t + j) + .4 * Math.sin(TAU * f * 1.004 * t + j * 2), 0);
  let pad = voice(cur) * x + voice(prev) * (1 - x);
  pad = lp1(pad, 900 + 300 * Math.sin(t * .25), .6) * .035;
  const sub = lp2(Math.sin(TAU * cur.r * t), 200) * .05 * (.8 + .2 * Math.sin(t * .8));
  let g = Math.min(1, (t - M0) / 3);
  if (t > MEND) g *= Math.max(0, 1 - (t - MEND) / 2.5);
  music[k] = (pad + sub) * g;
}
// arpegio muy suave en cada cambio de acorde
for (let t = M0 + CHL * 2, i = 0; t < MEND - 2; t += CHL / 2, i++) {
  const ch = CH[Math.floor((t - M0) / CHL) % 4];
  soft(t, ch.n[(i % 3) + 2] * 2, .022, i % 2 ? .35 : -.35);
}

// ---------- reverb amplia ----------
function reverb(inp) {
  const out = new Float32Array(N);
  const cb = [1687, 1601, 2053, 2251].map(d => ({ b: new Float32Array(d), i: 0, s: 0 }));
  const ap = [347, 113].map(d => ({ b: new Float32Array(d), i: 0 }));
  for (let k = 0; k < N; k++) {
    let s = 0;
    for (const c of cb) { const y = c.b[c.i]; c.s = y * .7 + c.s * .3; c.b[c.i] = inp[k] + c.s * .84; c.i = (c.i + 1) % c.b.length; s += y; }
    s *= .25;
    for (const a of ap) { const y = a.b[a.i]; const v = s + y * .5; a.b[a.i] = v; s = y - v * .5; a.i = (a.i + 1) % a.b.length; }
    out[k] = s;
  }
  return out;
}
const rv = reverb(send);
let peak = 0;
for (let k = 0; k < N; k++) {
  L[k] += music[k] + rv[k] * .5; R[k] += music[Math.max(0, k - 11)] + rv[Math.max(0, k - 480)] * .5;
  peak = Math.max(peak, Math.abs(L[k]), Math.abs(R[k]));
}
const g = .7 / peak;
const buf = Buffer.alloc(44 + N * 4);
buf.write('RIFF', 0); buf.writeUInt32LE(36 + N * 4, 4); buf.write('WAVE', 8); buf.write('fmt ', 12);
buf.writeUInt32LE(16, 16); buf.writeUInt16LE(1, 20); buf.writeUInt16LE(2, 22); buf.writeUInt32LE(SR, 24);
buf.writeUInt32LE(SR * 4, 28); buf.writeUInt16LE(4, 32); buf.writeUInt16LE(16, 34); buf.write('data', 36); buf.writeUInt32LE(N * 4, 40);
for (let k = 0; k < N; k++) { buf.writeInt16LE(Math.round(cl(L[k] * g) * 32000), 44 + k * 4); buf.writeInt16LE(Math.round(cl(R[k] * g) * 32000), 46 + k * 4); }
function cl(x) { return Math.max(-1, Math.min(1, x)); }
fs.writeFileSync(path.join(__dirname, 'out', 'audio.wav'), buf);
console.log('audio.wav', DUR.toFixed(2), 's');
