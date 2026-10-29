// 모션그래픽 렌더: node tools/render.mjs stills 1,5,10 | video [--fps 30] [--audio x.wav] --out out.mp4
import { createRequire } from 'node:module';
import http from 'node:http'; import fs from 'node:fs'; import path from 'node:path'; import { spawn } from 'node:child_process';
const require = createRequire('/Users/shoun/Documents/zyxcad-ax-film/package.json');
const puppeteer = require('puppeteer-core');
const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
const FF = '/Users/shoun/Documents/zyxcad-ax-film/tools/ffmpeg';
const argv = process.argv.slice(2), mode = argv[0];
const opt = (k, d) => { const i = argv.indexOf('--' + k); return i >= 0 ? argv[i + 1] : d; };
const MIME = { '.html': 'text/html', '.otf': 'font/otf', '.js': 'text/javascript', '.png': 'image/png', '.jpg': 'image/jpeg' };
const srv = http.createServer((q, r) => { const f = path.join(ROOT, decodeURIComponent(q.url.split('?')[0])); if (!fs.existsSync(f)) { r.writeHead(404); return r.end(); } r.writeHead(200, { 'Content-Type': MIME[path.extname(f)] || 'application/octet-stream' }); fs.createReadStream(f).pipe(r); });
await new Promise(r => srv.listen(0, '127.0.0.1', r));
const page_ = opt('page', 'motion/index.html');
const br = await puppeteer.launch({ executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', headless: true, args: ['--headless=new', '--force-color-profile=srgb', '--hide-scrollbars'] });
const pg = await br.newPage(); await pg.setViewport({ width: 1920, height: 1080 });
await pg.goto(`http://127.0.0.1:${srv.address().port}/${page_}`); await pg.evaluate(() => window.__ready);
const shot = async t => { await pg.evaluate(t => window.__render(t), t); return pg.evaluate(() => document.getElementById('c').toDataURL('image/jpeg', .93).split(',')[1]); };
if (mode === 'stills') {
  const dir = opt('dir', 'motion/qa'); fs.mkdirSync(path.join(ROOT, dir), { recursive: true });
  for (const t of argv[1].split(',').map(Number)) fs.writeFileSync(path.join(ROOT, dir, `t${String(t).padStart(5, '0')}.jpg`), Buffer.from(await shot(t), 'base64'));
} else {
  const fps = +opt('fps', 30), dur = await pg.evaluate(() => window.__duration), n = Math.round(dur * fps);
  const args = ['-y', '-v', 'error', '-f', 'image2pipe', '-framerate', String(fps), '-c:v', 'mjpeg', '-i', '-'];
  if (opt('audio')) args.push('-i', opt('audio'), '-c:a', 'aac', '-b:a', '192k', '-shortest');
  args.push('-c:v', 'h264_videotoolbox', '-b:v', '10M', '-vf', 'scale=in_range=pc:out_range=tv,format=yuv420p', '-color_range', 'tv', '-movflags', '+faststart', opt('out'));
  const ff = spawn(FF, args, { stdio: ['pipe', 'inherit', 'inherit'] });
  for (let i = 0; i < n; i++) { const b = Buffer.from(await shot(i / fps), 'base64'); if (!ff.stdin.write(b)) await new Promise(r => ff.stdin.once('drain', r)); if (i % 300 === 0) console.log('frame', i, '/', n); }
  ff.stdin.end(); await new Promise(r => ff.on('close', r));
}
await br.close(); srv.close();
