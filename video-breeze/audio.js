// Sintetiza la banda sonora (sin voz) a partir de out/cues.json -> out/audio.wav
const fs = require('fs');
const path = require('path');
const SR = 48000;
const cues = JSON.parse(fs.readFileSync(path.join(__dirname, 'out', 'cues.json')));
const DUR = +(process.argv[2] || 58);
const N = Math.ceil(DUR * SR);
const L = new Float32Array(N), Rr = new Float32Array(N);   // mezcla final
const sfx = new Float32Array(N);                             // envío a reverb
const music = new Float32Array(N);

let seed = 12345;
const rnd = () => ((seed = (seed * 1664525 + 1013904223) >>> 0) / 4294967296);
const noise = () => rnd() * 2 - 1;
const TAU = Math.PI * 2;

// biquad sencillo con coeficientes recalculables
function biquad(type) {
  let x1 = 0, x2 = 0, y1 = 0, y2 = 0, b0, b1, b2, a1, a2;
  const f = (x, freq, q = 0.8) => {
    const w = TAU * Math.min(freq, SR * 0.45) / SR, c = Math.cos(w), al = Math.sin(w) / (2 * q);
    let a0;
    if (type === 'lp') { b0 = (1 - c) / 2; b1 = 1 - c; b2 = b0; }
    else if (type === 'hp') { b0 = (1 + c) / 2; b1 = -(1 + c); b2 = b0; }
    else { b0 = al; b1 = 0; b2 = -al; }
    a0 = 1 + al; a1 = -2 * c; a2 = 1 - al;
    const y = (b0 * x + b1 * x1 + b2 * x2 - a1 * y1 - a2 * y2) / a0;
    x2 = x1; x1 = x; y2 = y1; y1 = y; return y;
  };
  return f;
}
function add(t, len, fn, gain = 1, pan = 0) { // fn(i, tt) -> muestra
  const s0 = Math.floor(t * SR), n = Math.floor(len * SR);
  const gl = gain * Math.cos((pan + 1) * Math.PI / 4) * 1.414, gr = gain * Math.sin((pan + 1) * Math.PI / 4) * 1.414;
  for (let i = 0; i < n; i++) {
    const k = s0 + i; if (k < 0 || k >= N) continue;
    const v = fn(i, i / SR);
    L[k] += v * gl; Rr[k] += v * gr; sfx[k] += v * gain * 0.5;
  }
}
const env = (tt, a, d) => tt < a ? tt / a : Math.exp(-(tt - a) / d);

// ---------------- efectos ----------------
const FX = {
  key(t, c) {
    const bp = biquad('bp'), f0 = 2600 + rnd() * 2200, g = 0.16 + rnd() * 0.08, pan = (rnd() - .5) * .3;
    add(t, 0.05, (i, tt) => bp(noise(), f0, 1.2) * env(tt, 0.0008, 0.008) * 2.2 + Math.sin(TAU * 190 * tt) * env(tt, 0.001, 0.012) * 0.5, g, pan);
  },
  space(t) { const bp = biquad('bp'); add(t, 0.06, (i, tt) => bp(noise(), 1400, 1) * env(tt, .001, .012) * 2 + Math.sin(TAU * 140 * tt) * env(tt, .001, .02) * .6, 0.18); },
  focus(t) { add(t, 0.12, (i, tt) => Math.sin(TAU * (1800 - tt * 4000) * tt) * env(tt, .002, .03), 0.08); },
  send(t) {
    add(t, 0.25, (i, tt) => { const f = 500 + 900 * Math.min(1, tt / 0.09); return Math.sin(TAU * f * tt) * env(tt, .003, .07); }, 0.32);
    FX.tap(t, {});
  },
  tap(t) { add(t, 0.08, (i, tt) => (Math.sin(TAU * 1500 * tt) * 0.6 + Math.sin(TAU * 3100 * tt) * 0.2) * env(tt, .001, .018), 0.12, (rnd() - .5) * .4); },
  tick(t) { add(t, 0.05, (i, tt) => Math.sin(TAU * 2300 * tt) * env(tt, .001, .01), 0.08); },
  check(t) { [1318.5, 1760].forEach((f, j) => add(t + j * 0.06, 0.4, (i, tt) => Math.sin(TAU * f * tt) * env(tt, .002, .09), 0.1, j ? .2 : -.2)); },
  blip(t, c) { const f = 520 * Math.pow(2, (c.n || 0) * 2 / 12); add(t, 0.15, (i, tt) => Math.sin(TAU * f * tt) * env(tt, .002, .035), 0.09, ((c.n || 0) - 4) / 8); },
  pop(t) { add(t, 0.18, (i, tt) => { const f = 950 * Math.exp(-tt * 18) + 280; return Math.sin(TAU * f * tt) * env(tt, .002, .05); }, 0.3); },
  pop_s(t, c) { const f0 = 1300 + ((c.n || 0) % 4) * 140; add(t, 0.12, (i, tt) => Math.sin(TAU * (f0 * Math.exp(-tt * 14) + 400) * tt) * env(tt, .002, .035), 0.16, (rnd() - .5) * .5); },
  note(t, c) { // pluck pentatónico
    const sc = [523.25, 587.33, 659.26, 783.99, 880, 1046.5, 1174.66, 1318.51];
    const f = sc[(c.n || 0) % 8];
    add(t, 0.9, (i, tt) => (Math.sin(TAU * f * tt) + 0.35 * Math.sin(TAU * f * 2 * tt) * Math.exp(-tt * 8)) * env(tt, .003, .22), 0.11, ((c.n || 0) - 3.5) / 7);
  },
  chime(t) {
    [1046.5, 1318.5, 1568, 2093].forEach((f, j) => add(t + j * 0.07, 1.8, (i, tt) =>
      (Math.sin(TAU * f * tt) + 0.25 * Math.sin(TAU * f * 2.76 * tt) * Math.exp(-tt * 6)) * env(tt, .002, .5), 0.09, (j - 1.5) / 3));
  },
  success(t) {
    [523.25, 659.26, 783.99, 1046.5, 1318.5].forEach((f, j) => add(t + j * 0.06, 2.2, (i, tt) =>
      (Math.sin(TAU * f * tt) + 0.3 * Math.sin(TAU * f * 2 * tt) * Math.exp(-tt * 4)) * env(tt, .003, .6), 0.1, (j - 2) / 4));
    FX.shimmer(t + 0.1, {});
  },
  shimmer(t) {
    for (let k = 0; k < 14; k++) {
      const f = 3500 + rnd() * 4500, dt = rnd() * 0.8;
      add(t + dt, 0.5, (i, tt) => Math.sin(TAU * f * tt) * env(tt, .002, .08), 0.035, (rnd() - .5) * 1.4);
    }
    const hp = biquad('hp');
    add(t, 1.0, (i, tt) => hp(noise(), 6000, .7) * Math.sin(Math.PI * Math.min(1, tt / 1.0)) , 0.05);
  },
  whoosh(t, c, len = 0.7, rev = false, g = 0.33) {
    const bp = biquad('bp');
    add(t - len * 0.55, len, (i, tt) => {
      let p = tt / len; if (rev) p = 1 - p;
      const f = 250 * Math.pow(16, Math.sin(Math.PI * p * 0.5));
      const a = Math.pow(Math.sin(Math.PI * (tt / len)), 2);
      return bp(noise(), f, 1.4) * a * 3;
    }, g, 0);
  },
  whoosh_s(t, c) { FX.whoosh(t, c, 0.38, false, 0.2); },
  whoosh_r(t, c) { FX.whoosh(t + 0.3, c, 0.6, true, 0.28); },
  impact(t) {
    const lp = biquad('lp');
    add(t, 1.6, (i, tt) => {
      const f = 35 + 55 * Math.exp(-tt * 9);
      return Math.sin(TAU * f * tt + 0.3) * env(tt, .002, .45) * 1.1 + lp(noise(), 900, .7) * env(tt, .001, .09) * 1.2;
    }, 0.55);
  },
  impact_s(t) {
    const lp = biquad('lp');
    add(t, 0.7, (i, tt) => Math.sin(TAU * (45 + 70 * Math.exp(-tt * 14)) * tt) * env(tt, .002, .16) + lp(noise(), 1500, .7) * env(tt, .001, .04) * .6, 0.38);
  },
  hit(t) {
    const hp = biquad('hp');
    add(t, 1.0, (i, tt) => Math.sin(TAU * (45 + 120 * Math.exp(-tt * 30)) * tt) * env(tt, .001, .22) * 1.2 + hp(noise(), 2500, .7) * env(tt, .001, .05) * .9, 0.5);
    FX.whoosh(t, {}, 0.3, false, 0.15);
  },
  riser(t, c) {
    const d = c.d || 1, bp = biquad('bp'), g = c.soft ? 0.07 : 0.22;
    add(t, d, (i, tt) => {
      const p = tt / d;
      return bp(noise(), 400 * Math.pow(18, p), 2) * Math.pow(p, 2) * 2.5 + Math.sin(TAU * (200 + 600 * p * p) * tt) * Math.pow(p, 3) * 0.3;
    }, g);
  },
  count(t, c) {
    const d = c.d || 1, step = c.fast ? 0.028 : 0.042;
    for (let x = 0; x < d; x += step) {
      const p = x / d, f = 1700 + 900 * p;
      add(t + x, 0.03, (i, tt) => Math.sin(TAU * f * tt) * env(tt, .0008, .006), 0.06 * (1 - p * 0.5), (rnd() - .5) * .3);
    }
  },
  pad_start() {}, pad_end() {},
};
cues.forEach(c => { if (FX[c.type]) FX[c.type](c.t, c); });

// ---------------- música de fondo ----------------
const cueT = ty => (cues.find(c => c.type === ty) || {}).t;
const M0 = cueT('pad_start') || 0.15;
const impacts = cues.filter(c => c.type === 'impact').map(c => c.t);
const BEAT_IN = impacts[0];                       // entra el beat al revelar la UI
const OW = impacts[1];                            // barrido al outro
const LOGO = impacts[2];
const BPM = 100, B = 60 / BPM, BAR = 4 * B;
const CH = [ // acordes Fmaj7 - Am7 - Cmaj7 - G6
  { r: 87.31, n: [174.61, 220, 261.63, 329.63] },
  { r: 110, n: [220, 261.63, 329.63, 392] },
  { r: 65.41, n: [196, 246.94, 261.63, 329.63] },
  { r: 98, n: [196, 246.94, 293.66, 329.63] },
];
const lpPad = biquad('lp'), lpBass = biquad('lp'), hpHat = biquad('hp');
const kicks = [], hats = [];
for (let t = BEAT_IN; t < OW - 0.9; t += B) kicks.push(t);
for (let t = BEAT_IN + 6 * BAR / 4; t < OW - 0.9; t += B) hats.push(t + B / 2);
const final = { r: 65.41, n: [130.81, 196, 261.63, 329.63, 392, 493.88] };
const fadeOut = DUR - 0.9;
for (let k = Math.floor(M0 * SR); k < N; k++) {
  const t = k / SR;
  const rel = t - BEAT_IN;
  let chord = t < BEAT_IN ? CH[0] : CH[Math.floor(rel / BAR) % 4];
  if (t >= LOGO) chord = final;
  // ducking estilo sidechain
  let duck = 1;
  if (t >= BEAT_IN && t < OW - 0.9) { const ph = (rel % B) / B; duck = 0.55 + 0.45 * Math.min(1, ph * 3.5); }
  const swell = Math.min(1, (t - M0) / 2.5);
  let pad = 0;
  chord.n.forEach((f, j) => {
    pad += Math.sin(TAU * f * t + j) + 0.5 * Math.sin(TAU * f * 1.003 * t) + 0.3 * Math.sin(TAU * f * 2.001 * t) * 0.5;
  });
  pad = lpPad(pad, 1400 + 600 * Math.sin(t * 0.4), 0.7) * 0.05 * (0.85 + 0.15 * Math.sin(t * 1.3));
  let bass = 0;
  if (t >= BEAT_IN && t < OW - 0.9) {
    const ph = (rel % (B / 2)) / (B / 2);
    bass = lpBass(Math.sin(TAU * chord.r * t) + 0.4 * Math.sin(TAU * chord.r * 2 * t), 400, .7) * Math.exp(-ph * 2.5) * 0.12;
  }
  let outroGain = 1;
  if (t > OW - 0.9 && t < OW) outroGain = 1 - (t - (OW - 0.9)) / 0.9 * 0.7;   // hueco antes del impacto
  else if (t >= OW && t < LOGO) outroGain = 0.5;
  else if (t >= LOGO) outroGain = 1.3;
  let v = (pad * duck + bass) * swell * outroGain;
  if (t > fadeOut) v *= Math.max(0, 1 - (t - fadeOut) / 0.9);
  music[k] = v;
}
// batería
kicks.forEach((t, i) => add(t, 0.4, (j, tt) => Math.sin(TAU * (48 + 110 * Math.exp(-tt * 35)) * tt) * env(tt, .001, .12), i % 4 === 0 ? 0.36 : 0.3));
hats.forEach(t => { const hp = biquad('hp'); add(t, 0.06, (j, tt) => hp(noise(), 8000, .7) * env(tt, .001, .015), 0.05, 0.25); });

// ---------------- reverb (Schroeder) sobre efectos ----------------
function reverb(inp) {
  const out = new Float32Array(N);
  const combs = [1557, 1617, 1491, 1422].map(d => ({ b: new Float32Array(Math.round(d * SR / 44100)), i: 0, fb: 0.8 }));
  const aps = [225, 556].map(d => ({ b: new Float32Array(Math.round(d * SR / 44100)), i: 0 }));
  for (let k = 0; k < N; k++) {
    let s = 0;
    for (const c of combs) { const y = c.b[c.i]; c.b[c.i] = inp[k] + y * c.fb; c.i = (c.i + 1) % c.b.length; s += y; }
    s *= 0.25;
    for (const a of aps) { const y = a.b[a.i]; const x = s + y * -0.5; a.b[a.i] = x; s = y - x * 0.5 + x * 0; a.i = (a.i + 1) % a.b.length; }
    out[k] = s;
  }
  return out;
}
const rv = reverb(sfx);
let peak = 0;
for (let k = 0; k < N; k++) {
  const d = Math.floor(SR * 0.011);
  L[k] += music[k] + rv[k] * 0.22;
  Rr[k] += music[Math.max(0, k - 7)] + (k >= d ? rv[k - d] : 0) * 0.22;
  peak = Math.max(peak, Math.abs(L[k]), Math.abs(Rr[k]));
}
const g = 0.89 / peak;
const buf = Buffer.alloc(44 + N * 4);
buf.write('RIFF', 0); buf.writeUInt32LE(36 + N * 4, 4); buf.write('WAVE', 8); buf.write('fmt ', 12);
buf.writeUInt32LE(16, 16); buf.writeUInt16LE(1, 20); buf.writeUInt16LE(2, 22); buf.writeUInt32LE(SR, 24);
buf.writeUInt32LE(SR * 4, 28); buf.writeUInt16LE(4, 32); buf.writeUInt16LE(16, 34); buf.write('data', 36); buf.writeUInt32LE(N * 4, 40);
const sat = x => Math.tanh(x * 1.2) / Math.tanh(1.2);
for (let k = 0; k < N; k++) {
  buf.writeInt16LE(Math.round(sat(L[k] * g) * 32000), 44 + k * 4);
  buf.writeInt16LE(Math.round(sat(Rr[k] * g) * 32000), 46 + k * 4);
}
fs.writeFileSync(path.join(__dirname, 'out', 'audio.wav'), buf);
console.log('audio.wav', DUR.toFixed(2), 's, pico', peak.toFixed(2));
