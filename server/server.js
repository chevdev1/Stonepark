/*
 * STONEPARK backend: shared database, live sync, presence, uploads.
 *
 *   one WebSocket (/ws)  -> documents (wall strokes, chat, battles, gallery...) + cursors
 *   POST /api/upload     -> files for the gallery / tracks (owner only)
 *   GET  /api/asset/<id> -> uploaded file
 *   GET  /api/health     -> "ok"
 *
 * Storage: one SQLite file (data/stonepark.db). Needs Node 22.13+ and the `ws` package only.
 * Config via environment (see .env.example): PORT, HOST, DATA_DIR, ADMIN_TOKEN, ALLOWED_ORIGINS.
 */
'use strict';
const http = require('http');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { DatabaseSync } = require('node:sqlite');
const { WebSocketServer } = require('ws');

// ------------------------------------------------------------------ config
const PORT = +process.env.PORT || 3000;
const HOST = process.env.HOST || '127.0.0.1';
const DATA_DIR = path.resolve(process.env.DATA_DIR || path.join(__dirname, 'data'));
const WEB_DIR = path.resolve(process.env.WEB_DIR || path.join(__dirname, '..', 'web'));
const SERVE_STATIC = process.env.SERVE_STATIC === '1'; // for local testing; in production nginx serves /web
const ALLOWED_ORIGINS = (process.env.ALLOWED_ORIGINS || '').split(',').map((s) => s.trim()).filter(Boolean);
// the wall is 8640 x 4860; ~50 people can paint for hours. Everything stored is also sent on join, so keep the two equal.
const MAX_STROKES_PER_EPOCH = 60000;
const INIT_LIMIT = 60000;
const MAX_UPLOAD = 12 * 1024 * 1024;

fs.mkdirSync(DATA_DIR, { recursive: true });

function secretFile(name, make) {
  const f = path.join(DATA_DIR, name);
  if (!fs.existsSync(f)) fs.writeFileSync(f, make(), { mode: 0o600 });
  return fs.readFileSync(f, 'utf8').trim();
}
const SECRET = process.env.SECRET || secretFile('secret.key', () => crypto.randomBytes(32).toString('hex'));
let ADMIN_TOKEN = process.env.ADMIN_TOKEN || '';
if (!ADMIN_TOKEN) {
  ADMIN_TOKEN = secretFile('admin-token.txt', () => crypto.randomBytes(18).toString('base64url'));
  console.log('[stonepark] ADMIN_TOKEN not set, using ' + path.join(DATA_DIR, 'admin-token.txt'));
}

// ------------------------------------------------------------------ database
const db = new DatabaseSync(path.join(DATA_DIR, 'stonepark.db'));
db.exec(`
  PRAGMA journal_mode = WAL;
  PRAGMA synchronous = NORMAL;
  CREATE TABLE IF NOT EXISTS docs (
    col TEXT NOT NULL, id TEXT NOT NULL, data TEXT NOT NULL,
    PRIMARY KEY (col, id)
  );
  CREATE TABLE IF NOT EXISTS assets (
    id TEXT PRIMARY KEY, mime TEXT NOT NULL, data BLOB NOT NULL, created INTEGER NOT NULL
  );
`);
const q = {
  get: db.prepare('SELECT data FROM docs WHERE col = ? AND id = ?'),
  put: db.prepare('INSERT INTO docs (col, id, data) VALUES (?, ?, ?) ON CONFLICT(col, id) DO UPDATE SET data = excluded.data'),
  del: db.prepare('DELETE FROM docs WHERE col = ? AND id = ?'),
  list: db.prepare('SELECT id, data FROM docs WHERE col = ? ORDER BY rowid DESC LIMIT ?'),
  count: db.prepare('SELECT COUNT(*) AS n FROM docs WHERE col = ?'),
  putAsset: db.prepare('INSERT INTO assets (id, mime, data, created) VALUES (?, ?, ?, ?)'),
  getAsset: db.prepare('SELECT mime, data FROM assets WHERE id = ?'),
};

// first start: the tracks that used to be seeded in the browser
if (!q.count.get('tracks').n) {
  try {
    const seed = JSON.parse(fs.readFileSync(path.join(__dirname, 'seed-tracks.json'), 'utf8'));
    for (const [id, d] of Object.entries(seed)) q.put.run('tracks', id, JSON.stringify(d));
  } catch (e) { console.warn('[stonepark] no seed tracks:', e.message); }
}

// ------------------------------------------------------------------ identity
const sign = (uid) => crypto.createHmac('sha256', SECRET).update(uid).digest('hex').slice(0, 32);
const safeEq = (a, b) => { const x = Buffer.from(String(a)), y = Buffer.from(String(b)); return x.length === y.length && crypto.timingSafeEqual(x, y); };
const isOwnerToken = (t) => typeof t === 'string' && t.length > 0 && safeEq(t, ADMIN_TOKEN);

// ------------------------------------------------------------------ write policy
class Denied extends Error { constructor(code) { super(code); this.code = code; } }
const ID_RE = /^[A-Za-z0-9_.-]{1,80}$/;
const COL_RE = /^[A-Za-z0-9_-]{1,60}(\/[A-Za-z0-9_-]{1,60}){0,3}$/;
const isStr = (v, max) => typeof v === 'string' && v.length <= max;
const root = (col) => col.split('/')[0];

/** Returns the sanitized document to store, or throws Denied. `old` is the stored doc (or null). */
function checkWrite(conn, col, id, data, old, isDelete) {
  const r = root(col);
  const owner = conn.owner;
  const author = old && old.by === conn.uid;
  switch (r) {
    case 'megawall':
    case 'bstrokes': {
      if (col.split('/').length !== (r === 'megawall' ? 3 : 3)) throw new Denied('invalid_argument');
      if (isDelete) { if (!old) return null; if (!owner && !author) throw new Denied('permission_denied'); return null; }
      if (old && !owner && !author) throw new Denied('permission_denied');
      if (!data || !Array.isArray(data.p) || !Array.isArray(data.d)) throw new Denied('invalid_argument');
      if (!old && q.count.get(col).n >= MAX_STROKES_PER_EPOCH) throw new Denied('quota_exceeded');
      return Object.assign({}, data, { by: old ? old.by : conn.uid });
    }
    case 'chat':
    case 'shouts': {
      if (isDelete) { if (!old) return null; if (!owner && !author) throw new Denied('permission_denied'); return null; }
      if (old && !owner && !author) throw new Denied('permission_denied');
      if (!isStr(data.text, 400) || (r === 'chat' && !isStr(data.nick, 40))) throw new Denied('invalid_argument');
      if (!old && !conn.chatBucket.take()) throw new Denied('resource_exhausted');
      return Object.assign({}, data, { by: old ? old.by : conn.uid });
    }
    case 'props':
    case 'bvotes': {
      if (id !== conn.uid && !owner) throw new Denied('permission_denied');
      return isDelete ? null : data;
    }
    case 'battles': {
      if (isDelete) { if (!old) return null; if (!owner && !(old.a && old.a.uid === conn.uid) && !(old.b && old.b.uid === conn.uid)) throw new Denied('permission_denied'); return null; }
      if (!data || !data.a || typeof data.a.uid !== 'string') throw new Denied('invalid_argument');
      if (!old) { if (data.a.uid !== conn.uid && !owner) throw new Denied('permission_denied'); return data; }
      const mine = old.a && old.a.uid === conn.uid || old.b && old.b.uid === conn.uid;
      const joining = !old.b && data.b && data.b.uid === conn.uid;
      if (!owner && !mine && !joining) throw new Denied('permission_denied');
      if (!owner && data.a.uid !== old.a.uid) throw new Denied('permission_denied');
      return data;
    }
    case 'wall':
    case 'tracks':
    case 'music':
    case 'gallery':
      if (!owner) throw new Denied('permission_denied');
      return isDelete ? null : data;
    default:
      throw new Denied('permission_denied');
  }
}

// ------------------------------------------------------------------ rate limiting
class Bucket {
  constructor(perSec, cap) { this.perSec = perSec; this.cap = cap; this.n = cap; this.at = Date.now(); }
  take() {
    const now = Date.now(); this.n = Math.min(this.cap, this.n + (now - this.at) / 1000 * this.perSec); this.at = now;
    if (this.n < 1) return false; this.n -= 1; return true;
  }
}

// ------------------------------------------------------------------ http
const MIME = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript', '.css': 'text/css', '.json': 'application/json', '.png': 'image/png', '.jpg': 'image/jpeg', '.webp': 'image/webp', '.gif': 'image/gif', '.mp3': 'audio/mpeg', '.mp4': 'video/mp4', '.svg': 'image/svg+xml' };
const UPLOAD_MIME = new Set(['image/png', 'image/jpeg', 'image/webp', 'image/gif', 'audio/mpeg', 'audio/mp4', 'audio/ogg', 'audio/wav', 'audio/x-wav']);
const clientIp = (req) => String(req.headers['x-forwarded-for'] || req.socket.remoteAddress || '').split(',')[0].trim();
const originOk = (req) => !ALLOWED_ORIGINS.length || !req.headers.origin || ALLOWED_ORIGINS.includes(req.headers.origin);

const server = http.createServer((req, res) => {
  const url = new URL(req.url, 'http://x');
  const send = (code, body, type) => { res.writeHead(code, { 'Content-Type': type || 'text/plain; charset=utf-8', 'X-Content-Type-Options': 'nosniff' }); res.end(body); };

  if (url.pathname === '/api/health') return send(200, 'ok');

  if (url.pathname === '/api/upload' && req.method === 'POST') {
    if (!originOk(req)) return send(403, 'origin');
    if (!isOwnerToken(req.headers['x-admin'])) return send(403, 'owner only');
    const mime = String(req.headers['content-type'] || '').split(';')[0].trim().toLowerCase();
    if (!UPLOAD_MIME.has(mime)) return send(415, 'unsupported type');
    const chunks = []; let size = 0, dead = false;
    req.on('data', (c) => { size += c.length; if (size > MAX_UPLOAD) { dead = true; send(413, 'too big'); req.destroy(); } else chunks.push(c); });
    req.on('end', () => {
      if (dead) return;
      const id = crypto.randomBytes(16).toString('hex');
      q.putAsset.run(id, mime, Buffer.concat(chunks), Date.now());
      send(200, JSON.stringify({ id }), 'application/json');
    });
    return;
  }

  const m = url.pathname.match(/^\/api\/asset\/([0-9a-f]{32})$/);
  if (m) {
    const a = q.getAsset.get(m[1]);
    if (!a) return send(404, 'not found');
    res.writeHead(200, { 'Content-Type': a.mime, 'Cache-Control': 'public, max-age=31536000, immutable', 'X-Content-Type-Options': 'nosniff' });
    return res.end(Buffer.from(a.data));
  }

  if (SERVE_STATIC) {
    let p = path.normalize(decodeURIComponent(url.pathname)).replace(/^([/\\])+/, '');
    let f = path.join(WEB_DIR, p || 'index.html');
    if (!f.startsWith(WEB_DIR)) return send(403, 'forbidden');
    if (fs.existsSync(f) && fs.statSync(f).isDirectory()) f = path.join(f, 'index.html');
    if (fs.existsSync(f)) return send(200, fs.readFileSync(f), MIME[path.extname(f).toLowerCase()] || 'application/octet-stream');
  }
  send(404, 'not found');
});

// ------------------------------------------------------------------ websocket
const wss = new WebSocketServer({ noServer: true, maxPayload: 256 * 1024, perMessageDeflate: { threshold: 1024 } });
const subs = new Map();            // col -> Set<conn>
const conns = new Set();
const perIp = new Map();
let nextCid = 1;

server.on('upgrade', (req, socket, head) => {
  const url = new URL(req.url, 'http://x');
  const ip = clientIp(req);
  if (url.pathname !== '/ws' || !originOk(req) || (perIp.get(ip) || 0) >= 30) { socket.destroy(); return; }
  wss.handleUpgrade(req, socket, head, (ws) => onConnect(ws, ip));
});

function onConnect(ws, ip) {
  const conn = {
    ws, ip, cid: 'c' + (nextCid++), uid: null, owner: false, ready: false,
    cols: new Set(), pres: null, presAt: 0,
    writeBucket: new Bucket(60, 120), chatBucket: new Bucket(0.7, 3), msgBucket: new Bucket(120, 240),
  };
  conns.add(conn); perIp.set(ip, (perIp.get(ip) || 0) + 1);
  const out = (o) => { if (ws.readyState === 1) ws.send(JSON.stringify(o)); };
  conn.out = out;

  ws.on('message', (raw) => {
    if (!conn.msgBucket.take()) return;
    let m; try { m = JSON.parse(raw.toString()); } catch (e) { return; }
    if (!m || typeof m.t !== 'string') return;
    try { handle(conn, m); } catch (e) { console.error('[stonepark] handler error:', e); }
  });
  ws.on('close', () => {
    conns.delete(conn); perIp.set(ip, Math.max(0, (perIp.get(ip) || 1) - 1));
    conn.cols.forEach((c) => { const s = subs.get(c); if (s) { s.delete(conn); if (!s.size) subs.delete(c); } });
    broadcastAll({ t: 'leave', cid: conn.cid }, conn);
  });
  ws.on('pong', () => { conn.dead = false; });
  ws.on('error', () => {});
}

function broadcast(col, msg, except) {
  const s = subs.get(col); if (!s) return;
  const str = JSON.stringify(msg);
  s.forEach((c) => { if (c !== except && c.ws.readyState === 1) c.ws.send(str); });
}
function broadcastAll(msg, except) {
  const str = JSON.stringify(msg);
  conns.forEach((c) => { if (c !== except && c.ready && c.ws.readyState === 1) c.ws.send(str); });
}

function handle(conn, m) {
  if (m.t === 'hello') {
    if (conn.ready) return;
    let uid = typeof m.uid === 'string' && /^[A-Za-z0-9_-]{6,40}$/.test(m.uid) && typeof m.sig === 'string' && safeEq(m.sig, sign(m.uid)) ? m.uid : null;
    if (!uid) uid = 'u' + crypto.randomBytes(8).toString('hex');
    conn.uid = uid; conn.owner = isOwnerToken(m.admin); conn.ready = true;
    const peers = [];
    conns.forEach((c) => { if (c !== conn && c.pres && Date.now() - c.presAt < 8000) peers.push([c.cid, c.pres]); });
    conn.out({ t: 'hello', uid, sig: sign(uid), owner: conn.owner, cid: conn.cid, peers });
    return;
  }
  if (!conn.ready) return;

  if (m.t === 'sub' || m.t === 'unsub') {
    if (typeof m.col !== 'string' || !COL_RE.test(m.col)) return;
    if (m.t === 'unsub') { conn.cols.delete(m.col); const s = subs.get(m.col); if (s) s.delete(conn); return; }
    if (conn.cols.size >= 40) return;
    conn.cols.add(m.col);
    if (!subs.has(m.col)) subs.set(m.col, new Set());
    subs.get(m.col).add(conn);
    // newest INIT_LIMIT docs, oldest first; the stored JSON is spliced in as text (no parse/stringify of tens of thousands of strokes)
    const rows = q.list.all(m.col, INIT_LIMIT);
    let msg = '{"t":"init","col":' + JSON.stringify(m.col) + ',"docs":[';
    for (let i = rows.length - 1; i >= 0; i--) msg += '[' + JSON.stringify(rows[i].id) + ',' + rows[i].data + ']' + (i ? ',' : '');
    if (conn.ws.readyState === 1) conn.ws.send(msg + ']}');
    return;
  }

  if (m.t === 'pres') {
    const now = Date.now(); if (now - conn.presAt < 40) return;
    const p = m.p || {};
    const clean = {
      x: p.x == null ? null : Math.max(0, Math.min(1, +p.x || 0)), y: p.y == null ? null : Math.max(0, Math.min(1, +p.y || 0)),   // null = pointer left the wall
      c: typeof p.c === 'string' ? p.c.slice(0, 9) : '', down: !!p.down, n: typeof p.n === 'string' ? p.n.slice(0, 16) : '',
    };
    conn.pres = clean; conn.presAt = now;
    broadcastAll({ t: 'pres', cid: conn.cid, p: clean }, conn);
    return;
  }

  if (m.t === 'set' || m.t === 'update' || m.t === 'del') {
    const ack = (code) => conn.out({ t: 'ack', rid: m.rid, ok: !code, code: code || undefined });
    try {
      if (!isStr(m.col, 200) || !COL_RE.test(m.col) || !isStr(m.id, 80) || !ID_RE.test(m.id)) throw new Denied('invalid_argument');
      const isDel = m.t === 'del';
      if (!isDel && (!m.data || typeof m.data !== 'object' || Array.isArray(m.data) || JSON.stringify(m.data).length > 120000)) throw new Denied('invalid_argument');
      if (!conn.writeBucket.take()) throw new Denied('resource_exhausted');
      const row = q.get.get(m.col, m.id);
      const old = row ? JSON.parse(row.data) : null;
      let next = isDel ? null : (m.t === 'update' ? Object.assign({}, old || {}, m.data) : m.data);
      next = checkWrite(conn, m.col, m.id, next, old, isDel);
      if (isDel) { q.del.run(m.col, m.id); broadcast(m.col, { t: 'del', col: m.col, id: m.id }, conn); }
      else { q.put.run(m.col, m.id, JSON.stringify(next)); broadcast(m.col, { t: 'set', col: m.col, id: m.id, data: next }, conn); }
      ack();
    } catch (e) {
      if (e instanceof Denied) ack(e.code); else { console.error(e); ack('internal'); }
    }
  }
}

// drop dead sockets
setInterval(() => { conns.forEach((c) => { if (c.dead) { c.ws.terminate(); return; } c.dead = true; try { c.ws.ping(); } catch (e) {} }); }, 30000);

server.listen(PORT, HOST, () => console.log(`[stonepark] listening on http://${HOST}:${PORT}  data: ${DATA_DIR}${SERVE_STATIC ? '  (serving ' + WEB_DIR + ')' : ''}`));
process.on('SIGTERM', () => { try { db.close(); } catch (e) {} process.exit(0); });
