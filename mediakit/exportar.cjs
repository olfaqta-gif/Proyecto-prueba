// PDF (A4) e imagen de cada página del media kit con Chromium.
// Uso: node exportar.cjs <media-kit.html>   → escribe .pdf y -1.png, -2.png al lado
const { chromium } = require('playwright');
const path = require('path');
(async () => {
  const html = path.resolve(process.argv[2]);
  const base = html.replace(/\.html$/, '');
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 794, height: 1123 }, deviceScaleFactor: 2 });
  await page.goto(require('url').pathToFileURL(path.resolve(html)).href + '?foto', { waitUntil: 'load', timeout: 20000 }).catch(() => {});
  await page.evaluate(() => document.fonts.ready);
  await page.waitForTimeout(200);
  const hojas = page.locator('.hoja');
  for (let i = 0; i < await hojas.count(); i++) {
    await hojas.nth(i).screenshot({ path: `${base}-${i + 1}.png` });
    console.log(`${base}-${i + 1}.png`);
  }
  await page.pdf({ path: base + '.pdf', format: 'A4', printBackground: true, margin: { top: 0, bottom: 0, left: 0, right: 0 } });
  console.log(base + '.pdf');
  await browser.close();
})().catch((e) => { console.error(e.message); process.exit(1); });
