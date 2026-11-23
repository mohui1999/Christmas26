import http from 'node:http';
import { createReadStream } from 'node:fs';
import { stat } from 'node:fs/promises';
import { extname, join, normalize, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = resolve(fileURLToPath(new URL('.', import.meta.url)));
const BASE_PORT = Number(process.env.PORT || 8787);
const HOST = '127.0.0.1';

const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.mjs': 'text/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.glb': 'model/gltf-binary',
  '.gltf': 'model/gltf+json',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.webp': 'image/webp',
  '.svg': 'image/svg+xml',
  '.wasm': 'application/wasm',
  '.ico': 'image/x-icon',
};

function safePath(urlPath) {
  let p = decodeURIComponent(urlPath.split('?')[0]);
  if (p === '/' || p === '') p = '/index.html';
  p = normalize(p).replace(/^(\.\.[/\\])+/, '');
  const abs = resolve(join(ROOT, p));
  if (!abs.startsWith(ROOT + '/') && abs !== ROOT) return null;
  return abs;
}

const server = http.createServer(async (req, res) => {
  try {
    if (req.url === '/health') {
      res.writeHead(200, { 'content-type': 'application/json' });
      res.end(JSON.stringify({ ok: true, service: 'christmas-town', root: ROOT }));
      return;
    }
    const file = safePath(req.url || '/');
    if (!file) {
      res.writeHead(403); res.end('Forbidden'); return;
    }
    const info = await stat(file).catch(() => null);
    if (!info || !info.isFile()) {
      res.writeHead(404, { 'content-type': 'text/plain; charset=utf-8' });
      res.end('Not found');
      return;
    }
    const ext = extname(file).toLowerCase();
    const type = MIME[ext] || 'application/octet-stream';
    const headers = {
      'content-type': type,
      'content-length': info.size,
      'cache-control': 'no-cache',
      'accept-ranges': 'bytes',
      'x-content-type-options': 'nosniff',
    };
    if (req.method === 'HEAD') {
      res.writeHead(200, headers); res.end(); return;
    }
    // minimal single-range support
    const range = req.headers.range;
    if (range && /^bytes=\d*-\d*$/.test(range)) {
      const [startRaw, endRaw] = range.replace('bytes=', '').split('-');
      let start = startRaw ? Number(startRaw) : 0;
      let end = endRaw ? Number(endRaw) : info.size - 1;
      start = Math.max(0, Math.min(start, info.size - 1));
      end = Math.max(start, Math.min(end, info.size - 1));
      res.writeHead(206, {
        ...headers,
        'content-range': `bytes ${start}-${end}/${info.size}`,
        'content-length': end - start + 1,
      });
      createReadStream(file, { start, end }).pipe(res);
      return;
    }
    res.writeHead(200, headers);
    createReadStream(file).pipe(res);
  } catch (err) {
    res.writeHead(500, { 'content-type': 'text/plain; charset=utf-8' });
    res.end('Server error');
    console.error(err);
  }
});

function listen(port, attempt = 0) {
  server.once('error', (err) => {
    if (err.code === 'EADDRINUSE' && attempt < 8) {
      listen(port + 1, attempt + 1);
    } else {
      console.error(err);
      process.exit(1);
    }
  });
  server.listen(port, HOST, () => {
    const url = `http://${HOST}:${port}/`;
    console.log('CHRISTMAS_TOWN_URL ' + url);
    console.log('Serving ' + ROOT);
  });
}
listen(BASE_PORT);
