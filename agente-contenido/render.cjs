// Captura el anuncio cuadro por cuadro (o unas vistas previas) con Chromium.
// Uso: node render.cjs <anuncio.html> <preview|full> <carpeta> <duracion> [tiempos de preview separados por coma]
const { chromium } = require('playwright');
const { mkdirSync } = require('fs');
const path = require('path');
(async () => {
  const [,, html, mode = 'preview', out = 'frames', dur = '15', previews = ''] = process.argv;
  const fps = 30, D = parseFloat(dur);
  mkdirSync(out, { recursive: true });
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
  await page.goto('file://' + path.resolve(html) + '?render');
  await page.evaluate(() => document.fonts.ready);
  await page.evaluate(() => window.__ajustar());
  await page.waitForTimeout(300);
  const times = mode === 'preview'
    ? previews.split(',').map(Number)
    : Array.from({ length: Math.round(fps * D) }, (_, i) => i / fps);
  let i = 0;
  for (const t of times) {
    await page.evaluate((t) => window.__seek(t), t);
    const name = mode === 'preview' ? `p_${String(i).padStart(2, '0')}_${t.toFixed(1)}.jpg` : `f_${String(i).padStart(4, '0')}.jpg`;
    await page.screenshot({ path: `${out}/${name}`, type: 'jpeg', quality: 92 });
    i++;
  }
  await browser.close();
})();
