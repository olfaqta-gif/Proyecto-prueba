const { chromium } = require('playwright');
const { mkdirSync } = require('fs');
(async () => {
const [,, mode = 'preview', out = 'frames'] = process.argv;
const fps = 30, D = 26;
mkdirSync(out, { recursive: true });
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
await page.goto('file://' + process.cwd() + '/anuncio.html?render');
await page.evaluate(() => document.fonts.ready);
await page.waitForTimeout(500);
const times = mode === 'preview'
  ? [1.9, 4.6, 5.6, 7.6, 8.9, 11.9, 13.0, 15.5, 19.3, 21.0, 23.5]
  : Array.from({ length: fps * D }, (_, i) => i / fps);
let i = 0;
for (const t of times) {
  await page.evaluate((t) => window.__seek(t), t);
  const name = mode === 'preview' ? `p_${t.toFixed(1)}.jpg` : `f_${String(i).padStart(4, '0')}.jpg`;
  await page.screenshot({ path: `${out}/${name}`, type: 'jpeg', quality: 92 });
  i++;
}
await browser.close();
})();
