// Renderiza breeze.html a MP4 cuadro por cuadro.
//   node render.js                 -> video completo (frames.mp4 + cues.json)
//   node render.js stills 5 12 17  -> capturas PNG en esos segundos
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

const FPS = 30;
const OUT = path.join(__dirname, 'out');

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
  await page.goto('file://' + path.join(__dirname, 'breeze.html'));
  await page.evaluate(() => document.fonts.ready);
  const duration = await page.evaluate(() => window.DURATION);
  fs.writeFileSync(path.join(OUT, 'cues.json'), JSON.stringify(await page.evaluate(() => window.CUES)));

  const mode = process.argv[2];
  if (mode === 'stills') {
    for (const s of process.argv.slice(3)) {
      await page.evaluate(t => window.seek(t), +s);
      await page.screenshot({ path: path.join(OUT, `still_${s}.png`) });
    }
    await browser.close();
    return;
  }

  const frames = Math.round(duration * FPS);
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-',
    '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', path.join(OUT, 'frames.mp4')], { stdio: ['pipe', 'inherit', 'inherit'] });
  for (let f = 0; f < frames; f++) {
    await page.evaluate(t => window.seek(t), f / FPS);
    const buf = await page.screenshot({ type: 'jpeg', quality: 95 });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if (f % 150 === 0) console.log(`frame ${f}/${frames}`);
  }
  ff.stdin.end();
  await new Promise(r => ff.on('close', r));
  await browser.close();
  console.log('listo', frames, 'frames');
})();
