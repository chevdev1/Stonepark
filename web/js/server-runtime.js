/*
 * STONEPARK: server runtime.
 *
 * Same interface as local-runtime.js (window.claude.use('db' | 'room' | 'user' | 'assets' | 'downloads')),
 * but everything goes through the STONEPARK backend (server/server.js) over one WebSocket,
 * so every visitor sees the same wall, chat, gallery and cursors.
 *
 * Owner mode (delete strokes/messages, reset the wall, upload tracks and gallery works):
 * open the site once as  https://your-domain/?admin=YOUR_ADMIN_TOKEN  (token: server/data/admin-token.txt).
 * It is remembered in this browser.
 *
 * If the server is unreachable the site falls back to the guest mode of app.js (paint stays in the browser).
 */
(function () {
  if (window.claude && typeof window.claude.use === 'function') return;

  const NS = 'sp_srv:';
  const lsGet = (k) => { try { return localStorage.getItem(k); } catch (e) { return null; } };
  const lsSet = (k, v) => { try { localStorage.setItem(k, v); } catch (e) {} };

  // owner token from ?admin=...
  let admin = lsGet(NS + 'admin') || '';
  try {
    const u = new URL(location.href);
    const a = u.searchParams.get('admin');
    if (a) { admin = a; lsSet(NS + 'admin', a); u.searchParams.delete('admin'); history.replaceState(null, '', u.pathname + u.search + u.hash); }
    if (u.searchParams.get('logout') !== null) { admin = ''; lsSet(NS + 'admin', ''); }
  } catch (e) {}

  const WS_URL = window.STONEPARK_WS || ((location.protocol === 'https:' ? 'wss://' : 'ws://') + location.host + '/ws');
  let uid = lsGet(NS + 'uid') || '', sig = lsGet(NS + 'sig') || '';
  let owner = false, ws = null, open = false, retry = 0, myCid = '';

  const mem = {};                 // col -> { id: data }
  const listeners = new Set();    // { col, run }
  const wantCols = new Map();     // col -> refcount (server subscriptions)
  const pending = new Map();      // rid -> { res, rej, timer }
  let rid = 1;
  const clone = (v) => JSON.parse(JSON.stringify(v));
  const split = (path) => { const i = path.lastIndexOf('/'); return [path.slice(0, i), path.slice(i + 1)]; };
  const col$ = (c) => mem[c] || (mem[c] = {});
  const notify = (col) => listeners.forEach((l) => l.col === col && l.run());

  let readyRes; const ready = new Promise((r) => { readyRes = r; });
  setTimeout(() => readyRes(), 6000); // do not hang the page if the server is down

  const sendRaw = (o) => { if (open && ws.readyState === 1) { ws.send(JSON.stringify(o)); return true; } return false; };

  // ---------------------------------------------------------------- connection
  function connect() {
    ws = new WebSocket(WS_URL);
    ws.onopen = () => { open = true; retry = 0; ws.send(JSON.stringify({ t: 'hello', uid, sig, admin })); };
    ws.onmessage = (e) => {
      let m; try { m = JSON.parse(e.data); } catch (x) { return; }
      switch (m.t) {
        case 'hello':
          uid = m.uid; sig = m.sig; owner = !!m.owner; myCid = m.cid;
          lsSet(NS + 'uid', uid); lsSet(NS + 'sig', sig);
          if (admin && !owner) lsSet(NS + 'admin', ''); // wrong/old token
          (m.peers || []).forEach(([cid, p]) => peers.set(cid, { presence: p, at: Date.now() }));
          wantCols.forEach((_, col) => sendRaw({ t: 'sub', col }));
          readyRes(); emitPeers();
          break;
        case 'init': {
          const c = {}; (m.docs || []).forEach(([id, d]) => { c[id] = d; });
          mem[m.col] = c; notify(m.col); break;
        }
        case 'set': col$(m.col)[m.id] = m.data; notify(m.col); break;
        case 'del': delete col$(m.col)[m.id]; notify(m.col); break;
        case 'ack': {
          const p = pending.get(m.rid); if (!p) break;
          pending.delete(m.rid); clearTimeout(p.timer);
          if (m.ok) p.res({}); else { const err = new Error(m.code || 'error'); err.code = m.code; p.rej(err); }
          break;
        }
        case 'pres': peers.set(m.cid, { presence: m.p, at: Date.now() }); emitPeers(); break;
        case 'leave': peers.delete(m.cid); emitPeers(); break;
      }
    };
    ws.onclose = () => {
      open = false; peers.clear(); emitPeers();
      pending.forEach((p) => { clearTimeout(p.timer); const e = new Error('unavailable'); e.code = 'unavailable'; p.rej(e); }); pending.clear();
      setTimeout(connect, Math.min(15000, 500 * Math.pow(1.7, retry++)));
    };
    ws.onerror = () => {};
  }
  connect();

  function subscribe(col) {
    wantCols.set(col, (wantCols.get(col) || 0) + 1);
    if (wantCols.get(col) === 1) sendRaw({ t: 'sub', col });
  }
  function unsubscribe(col) {
    const n = (wantCols.get(col) || 1) - 1;
    if (n <= 0) { wantCols.delete(col); sendRaw({ t: 'unsub', col }); } else wantCols.set(col, n);
  }

  function write(t, col, id, data) {
    return new Promise((res, rej) => {
      const r = rid++;
      const timer = setTimeout(() => { pending.delete(r); const e = new Error('unavailable'); e.code = 'unavailable'; rej(e); }, 10000);
      pending.set(r, { res, rej, timer });
      if (!sendRaw({ t, rid: r, col, id, data })) { pending.delete(r); clearTimeout(timer); const e = new Error('unavailable'); e.code = 'unavailable'; rej(e); }
    });
  }

  // ---------------------------------------------------------------- db
  function docRef(col, id) {
    return {
      id,
      async set(data) { const d = clone(data); await write('set', col, id, d); col$(col)[id] = d; notify(col); return { id }; },
      async update(data) { const d = clone(data); await write('update', col, id, d); col$(col)[id] = Object.assign({}, col$(col)[id] || {}, d); notify(col); return { id }; },
      async delete() { await write('del', col, id); delete col$(col)[id]; notify(col); },
      async get() { const d = col$(col)[id]; return { id, exists: !!d, data: () => (d ? clone(d) : null) }; },
      onSnapshot(cb) {
        const l = { col, run: () => { if (!(col in mem)) return; const d = col$(col)[id]; cb({ id, exists: !!d, data: () => (d ? clone(d) : null) }); } };
        listeners.add(l); subscribe(col); setTimeout(l.run, 0);
        return () => { listeners.delete(l); unsubscribe(col); };
      },
    };
  }
  function query(col, opts) {
    return {
      orderBy(field, dir) { return query(col, Object.assign({}, opts, { field, dir: dir || 'asc' })); },
      limit(n) { return query(col, Object.assign({}, opts, { n })); },
      doc(id) { return docRef(col, id); },
      onSnapshot(cb) {
        let prev = {}; let first = true;
        const l = {
          col, run: () => {
            if (first && !(col in mem)) return; // wait for the server's first answer
            first = false;
            const all = Object.entries(col$(col)).map(([id, d]) => ({ id, d }));
            if (opts.field) all.sort((a, b) => { const x = a.d[opts.field], y = b.d[opts.field]; return (x > y ? 1 : x < y ? -1 : 0) * (opts.dir === 'desc' ? -1 : 1); });
            const list = opts.n ? all.slice(0, opts.n) : all;
            const next = {}; const changes = [];
            list.forEach(({ id, d }) => {
              const s = JSON.stringify(d); next[id] = s;
              const doc = { id, data: () => clone(d) };
              if (!(id in prev)) changes.push({ type: 'added', doc }); else if (prev[id] !== s) changes.push({ type: 'modified', doc });
            });
            Object.keys(prev).forEach((id) => { if (!(id in next)) changes.push({ type: 'removed', doc: { id, data: () => null } }); });
            prev = next;
            const docs = list.map(({ id, d }) => ({ id, data: () => clone(d) }));
            cb({ docChanges: () => changes, docs, size: docs.length, empty: !docs.length, metadata: { fromCache: false, hasPendingWrites: false } });
          },
        };
        listeners.add(l); subscribe(col); setTimeout(l.run, 0);
        return () => { listeners.delete(l); unsubscribe(col); };
      },
    };
  }
  const db = { collection: (path) => query(path, {}), doc: (path) => { const [c, id] = split(path); return docRef(c, id); } };

  // ---------------------------------------------------------------- room (cursors, "N at the wall")
  const peers = new Map(); let mine = {}; const peerCbs = new Set();
  function emitPeers() {
    const now = Date.now(); peers.forEach((p, k) => { if (now - p.at > 8000) peers.delete(k); });
    const list = [{ sameTab: true, presence: mine }].concat([...peers.values()].map((p) => ({ sameTab: false, presence: p.presence })));
    peerCbs.forEach((cb) => cb({ peers: list }));
  }
  const room = {
    async presence(p) { mine = p || {}; sendRaw({ t: 'pres', p: mine }); emitPeers(); },
    onPeers(cb) { peerCbs.add(cb); setTimeout(emitPeers, 0); return () => peerCbs.delete(cb); },
  };
  setInterval(() => { if (Object.keys(mine).length) sendRaw({ t: 'pres', p: mine }); emitPeers(); }, 3000);

  // ---------------------------------------------------------------- user, assets, downloads
  const user = {
    async id() { await ready; return uid || 'guest'; },
    async canEdit() { await ready; return owner; },
    async can() { await ready; return open; }, // false -> app.js switches to guest mode
    async profiles(ids) { const o = {}; (ids || []).forEach((i) => { o[i] = { name: i === uid ? 'Ты' : 'Гость' }; }); return o; },
  };
  const assets = {
    async upload(file) {
      const r = await fetch('/api/upload', { method: 'POST', headers: { 'Content-Type': file.type || 'application/octet-stream', 'X-Admin': admin }, body: file });
      if (!r.ok) { const err = new Error('upload failed'); err.code = r.status === 413 ? 'quota_exceeded' : 'permission_denied'; throw err; }
      const j = await r.json();
      return { id: j.id, url: '/api/asset/' + j.id };
    },
  };
  const downloads = {
    async save({ filename, data }) {
      const blob = data instanceof Blob ? data : new Blob([data]);
      const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = filename || 'download';
      document.body.appendChild(a); a.click(); setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 1000);
      return { ok: true };
    },
  };

  // files that ship with the site (the demo crate and the docs screenshots); anything else is an upload
  const STATIC = { '0000000000000000000000000000a001': 'assets/music/starboy_preview.mp3', '0000000000000000000000000000a002': 'assets/music/starboy_cover.jpg', '0000000000000000000000000000a003': 'assets/music/ch_rightnow.mp3', '0000000000000000000000000000a004': 'assets/music/cover_rightnow.jpg', '0000000000000000000000000000a005': 'assets/music/ch_neverblame.mp3', '0000000000000000000000000000a006': 'assets/music/cover_neverblame.jpg', '0000000000000000000000000000a007': 'assets/music/ch_darkside.mp3', '0000000000000000000000000000a008': 'assets/music/cover_darkside.jpg', '0000000000000000000000000000a009': 'assets/music/ch_darkparadise.mp3', '0000000000000000000000000000a00a': 'assets/music/cover_darkparadise.jpg', '0000000000000000000000000000a00b': 'assets/music/chever_eskizy.mp3', '0000000000000000000000000000a00c': 'assets/music/cover_eskizy.jpg', '0000000000000000000000000000a00d': 'assets/music/tcf_preview.mp3', '0000000000000000000000000000a00e': 'assets/music/tcf_cover.jpg', '0000000000000000000000000000a00f': 'assets/music/napolkah_preview.mp3', '0000000000000000000000000000a010': 'assets/music/napolkah_cover.jpg', '2c331e1611b07323ec224fb3d03b2810': 'assets/docs/d1_scene.jpg', '05f148975b74163d1e9637fe02ceee19': 'assets/docs/d2_room_fx.jpg', 'e88f9df47ce03280c216d690b6f2a3c9': 'assets/docs/d3_wall.jpg', 'f161ab8bd393bfbef4c26b60d673524f': 'assets/docs/d4_ranked.jpg', '19bc8e85e60672f2a635538acd7ba53d': 'assets/docs/d6_player.jpg', '46b2979bb94716bfcb3e6d173f29338b': 'assets/docs/d7_mobile.jpg', '695e63843468211854e9c23d89d05275': 'assets/docs/d8_smoke.jpg' };

  const caps = { db, room, user, assets, downloads, sample: null };
  window.claude = {
    server: true,
    use: async (name) => caps[name] || null,
    assetUrl: (id) => STATIC[id] || (/^[0-9a-f]{32}$/.test(id || '') ? '/api/asset/' + id : ''),
  };
})();
