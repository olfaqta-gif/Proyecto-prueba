// Una imagen por cada elemento (diapositiva) de una página, con Chromium.
// Uso: node fotos.cjs <pagina.html> <selector> <ancho> <alto>  → <pagina>-1.png, -2.png…
const { chromium } = require('playwright');
const path = require('path');
(async () => {
  const [,, html, selector, w, h] = process.argv;
  const base = path.resolve(html).replace(/\.html$/, '');
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: +w, height: +h } });
  await page.goto('file://' + path.resolve(html) + '?foto', { waitUntil: 'load', timeout: 20000 }).catch(() => {});
  await page.evaluate(() => document.fonts.ready);
  await page.waitForTimeout(200);
  const items = page.locator(selector);
  for (let i = 0; i < await items.count(); i++) {
    await items.nth(i).screenshot({ path: `${base}-${i + 1}.png` });
    console.log(`${base}-${i + 1}.png`);
  }
  await browser.close();
})().catch((e) => { console.error(e.message); process.exit(1); });
