// Captura el showcase con Chromium.
//   node render.cjs eventos <salida.json>            línea de tiempo de sonidos + duración
//   node render.cjs previa <carpeta> 1,7.5,12          cuadros sueltos (segundos)
//   node render.cjs video <carpeta> [hilos]           todos los cuadros a 30 fps
// (con FORMATO=9x16 y/o VERSION=corta delante para las otras opciones)
const { chromium } = require('playwright');
const { mkdirSync, writeFileSync } = require('fs');
const path = require('path');
// Formato y versión: FORMATO=16x9|9x16  VERSION=completa|corta
const FORMATO = process.env.FORMATO || '16x9', VERSION = process.env.VERSION || 'completa';
const [W, H] = FORMATO === '9x16' ? [1080, 1920] : [1920, 1080];
const HTML = 'file://' + path.resolve(__dirname, 'showcase.html') + `?render&formato=${FORMATO}&version=${VERSION}`;
const FPS = 30;

async function abrir(browser) {
  const page = await browser.newPage({ viewport: { width: W, height: H } });
  await page.goto(HTML);
  await page.evaluate(() => document.fonts.ready);
  await page.waitForTimeout(300);
  return page;
}
async function cuadro(page, t, archivo) {
  await page.evaluate((t) => window.__seek(t), t);
  await page.evaluate(() => new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r))));
  await page.screenshot({ path: archivo, type: 'jpeg', quality: 93 });
}

(async () => {
  const [,, modo, out, extra] = process.argv;
  const browser = await chromium.launch({ args: ['--disable-gpu-vsync'] });
  const page = await abrir(browser);
  const info = await page.evaluate(() => ({ eventos: window.__eventos, duracion: window.__duracion, marcas: window.__marcas }));
  if (modo === 'eventos') {
    writeFileSync(out, JSON.stringify(info, null, 1));
  } else if (modo === 'previa') {
    mkdirSync(out, { recursive: true });
    for (const t of extra.split(',').map(Number)) await cuadro(page, t, `${out}/p_${t.toFixed(2).padStart(6, '0')}.jpg`);
  } else {
    mkdirSync(out, { recursive: true });
    const total = Math.round(info.duracion * FPS), hilos = parseInt(extra || '4', 10);
    const pages = [page];
    for (let i = 1; i < hilos; i++) pages.push(await abrir(browser));
    let hechos = 0;
    await Promise.all(pages.map(async (pg, h) => {
      for (let i = h; i < total; i += hilos) {
        await cuadro(pg, i / FPS, `${out}/f_${String(i).padStart(5, '0')}.jpg`);
        if (++hechos % 300 === 0) console.log(`${hechos}/${total}`);
      }
    }));
  }
  await browser.close();
})();
