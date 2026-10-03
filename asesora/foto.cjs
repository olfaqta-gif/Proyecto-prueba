// Saca la imagen 1080×1920 de una tarjeta de rutina con Chromium.
// Uso: node foto.cjs <rutina.html> <rutina.png>
const { chromium } = require('playwright');
const path = require('path');
(async () => {
  const [,, html, png] = process.argv;
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
  await page.goto('file://' + path.resolve(html) + '?foto', { waitUntil: 'load', timeout: 20000 }).catch(() => {});
  await page.evaluate(() => document.fonts.ready);
  await page.waitForTimeout(200);
  await page.locator('#tarjeta').screenshot({ path: png });
  await browser.close();
})().catch((e) => { console.error(e.message); process.exit(1); });
