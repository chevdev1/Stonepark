/*
 * STONEPARK — local runtime.
 *
 * On claude.ai the page gets `window.claude.use(name)` with real capabilities
 * (shared database, live presence, viewer identity, file uploads, downloads, Claude).
 * Outside claude.ai this file provides stand-ins with the same shape, so the whole
 * site works on your machine:
 *
 *   db        documents in localStorage, live updates across tabs (BroadcastChannel)
 *   room      presence (cursors, "N people on the wall") across tabs
 *   user      a local id, you are always the owner (canEdit = true)
 *   assets    uploads stored as data URLs in localStorage
 *   downloads saves files with a normal <a download>
 *   sample    not available locally -> CH's pager answers from his canned lines
 *
 * Testing tricks: open two tabs with ?as=anna and ?as=boris to be two different visitors,
 * add &rkfast to make ranked rounds 15 s painting + 20 s voting.
 *
 * For a real public launch replace these with your backend (Supabase / Firebase /
 * your own API) by keeping the same method names — app.js does not need to change.
 * See README.md, section "Свой бэкенд".
 */
(function () {
  if (window.claude && typeof window.claude.use === 'function') return; // running on claude.ai

  const NS = 'sp_local:';
  const chan = 'BroadcastChannel' in window ? new BroadcastChannel('stonepark-local') : null;
  let uid = localStorage.getItem(NS + 'uid');
  if (!uid) { uid = 'local-' + Math.random().toString(36).slice(2, 10); localStorage.setItem(NS + 'uid', uid); }
  // ?as=name pretends to be another visitor in this tab (handy for testing battles and chat)
  const asName = new URLSearchParams(location.search).get('as');
  if (asName && /^[A-Za-z0-9_-]{1,20}$/.test(asName)) uid = 'local-as-' + asName;

  // ---------------------------------------------------------------- db
  const mem = {}; // collection path -> { id: data }
  const load = (col) => { if (!mem[col]) { try { mem[col] = JSON.parse(localStorage.getItem(NS + 'col:' + col) || '{}'); } catch (e) { mem[col] = {}; } } return mem[col]; };
  const save = (col) => {
    try { localStorage.setItem(NS + 'col:' + col, JSON.stringify(mem[col] || {})); }
    catch (e) { const err = new Error('local storage is full'); err.code = 'quota_exceeded'; throw err; }
  };
  const listeners = new Set();
  const notify = (col, remote) => { listeners.forEach((l) => l.col === col && l.run()); if (!remote && chan) chan.postMessage({ t: 'db', col }); };
  const split = (path) => { const i = path.lastIndexOf('/'); return [path.slice(0, i), path.slice(i + 1)]; };
  const clone = (v) => JSON.parse(JSON.stringify(v));

  function docRef(col, id) {
    return {
      id,
      async set(data) { load(col)[id] = clone(data); save(col); notify(col); return { id }; },
      async update(data) { const c = load(col); c[id] = Object.assign({}, c[id] || {}, clone(data)); save(col); notify(col); return { id }; },
      async delete() { delete load(col)[id]; save(col); notify(col); },
      async get() { const d = load(col)[id]; return { id, exists: !!d, data: () => (d ? clone(d) : null) }; },
      onSnapshot(cb) {
        const l = { col, run: () => { const d = load(col)[id]; cb({ id, exists: !!d, data: () => (d ? clone(d) : null) }); } };
        listeners.add(l); setTimeout(l.run, 0); return () => listeners.delete(l);
      },
    };
  }
  function query(col, opts) {
    const q = {
      orderBy(field, dir) { return query(col, Object.assign({}, opts, { field, dir: dir || 'asc' })); },
      limit(n) { return query(col, Object.assign({}, opts, { n })); },
      doc(id) { return docRef(col, id); },
      onSnapshot(cb) {
        let prev = {};
        const l = {
          col, run: () => {
            const all = Object.entries(load(col)).map(([id, d]) => ({ id, d }));
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
        listeners.add(l); setTimeout(l.run, 0); return () => listeners.delete(l);
      },
    };
    return q;
  }
  const db = { collection: (path) => query(path, {}), doc: (path) => { const [c, id] = split(path); return docRef(c, id); } };
  // seedTracks: the tracks published on claude.ai, so the local crate is not empty
  (function seedTracks(){
    const t = load('tracks');
    if (!t.t5){
      t.t5 = { artist: 'CH feat. flame', audio: '0000000000000000000000000000a003', cover: '0000000000000000000000000000a004', demo: true, duration: 196, label: '#FF4FA3', order: 1.5, previewStart: 0, sc: [], title: 'rightnow', url: '' };
      t.t6 = { artist: 'CH', audio: '0000000000000000000000000000a005', cover: '0000000000000000000000000000a006', demo: true, duration: 174, label: '#2EE6E6', order: 2.5, previewStart: 0, sc: [], title: 'NeverBlameLife', url: '' };
      save('tracks');
    }
    if (!t.t10){
      t.t10 = { artist: 'sadtr1p', audio: '0000000000000000000000000000a00d', comments: 19, cover: '0000000000000000000000000000a00e', duration: 77, label: '#E7C55A', order: 0.6, plays: 859, previewStart: 0, sc: [], title: 'Time Creates Feelings', updated: '17.10.2026', url: 'https://soundcloud.com/sadtr1p/fxckingupthetime' };
      t.t11 = { artist: 'fuck12 damn i’m rollin', audio: '0000000000000000000000000000a00f', cover: '0000000000000000000000000000a010', duration: 67, label: '#D7263D', likes: 3, order: 0.7, plays: 433, previewStart: 0, sc: [], title: 'на полках', updated: '17.10.2026', url: 'https://soundcloud.com/jankie_04/dfdfdfd' };
      save('tracks');
    }
    if (!t.t7){
      t.t7 = { artist: 'CH feat. ICE', audio: '0000000000000000000000000000a007', cover: '0000000000000000000000000000a008', demo: true, duration: 179, label: '#9B5CFF', order: 3.5, previewStart: 0, sc: [], title: 'The dark side of the moon', url: '' };
      t.t8 = { artist: 'CH', audio: '0000000000000000000000000000a009', cover: '0000000000000000000000000000a00a', demo: true, duration: 118, label: '#D7263D', order: 4.5, previewStart: 0, sc: [], title: 'DarkParadise', url: '' };
      t.t9 = { artist: 'Chever', audio: '0000000000000000000000000000a00b', cover: '0000000000000000000000000000a00c', demo: true, duration: 133, label: '#FFD23A', order: 5.5, previewStart: 0, sc: [], title: 'Прячу эскизы', url: '' };
      save('tracks');
    }
    if (!t.t4){
      t.t4 = { artist: 'sadtr1p feat. chever', audio: '0000000000000000000000000000a001', cover: '0000000000000000000000000000a002', duration: 105, label: '#9B5CFF', likes: 79, order: 0.5, plays: 6640, previewStart: 0, reposts: 18, sc: [], title: 'starboy', updated: '16.10.2026', url: 'https://soundcloud.com/sadtr1p/starboy' };
      save('tracks');
    }
  })();

  // ---------------------------------------------------------------- room (presence across tabs)
  const peers = new Map(); let mine = {}; const peerCbs = new Set();
  const emitPeers = () => {
    const now = Date.now(); peers.forEach((p, k) => { if (now - p.at > 8000) peers.delete(k); });
    const list = [{ sameTab: true, presence: mine }].concat([...peers.values()].map((p) => ({ sameTab: false, presence: p.presence })));
    peerCbs.forEach((cb) => cb({ peers: list }));
  };
  const room = {
    async presence(p) { mine = p || {}; if (chan) chan.postMessage({ t: 'pres', uid, p: mine }); emitPeers(); },
    onPeers(cb) { peerCbs.add(cb); setTimeout(emitPeers, 0); return () => peerCbs.delete(cb); },
  };
  setInterval(() => { if (chan) chan.postMessage({ t: 'pres', uid, p: mine }); emitPeers(); }, 3000);
  if (chan) chan.onmessage = (e) => {
    const m = e.data || {};
    if (m.t === 'db') { delete mem[m.col]; notify(m.col, true); }
    if (m.t === 'pres' && m.uid !== uid) { peers.set(m.uid, { presence: m.p, at: Date.now() }); emitPeers(); }
  };

  // ---------------------------------------------------------------- user, assets, downloads
  const user = {
    async id() { return uid; },
    async canEdit() { return true; },
    async can() { return true; },
    async profiles(ids) { const o = {}; (ids || []).forEach((i) => { o[i] = { name: i === uid ? 'Ты' : 'Гость' }; }); return o; },
  };
  const assets = {
    upload(file) {
      return new Promise((res, rej) => {
        const r = new FileReader();
        r.onload = () => {
          const id = Array.from(crypto.getRandomValues(new Uint8Array(16))).map((b) => b.toString(16).padStart(2, '0')).join('');
          try { localStorage.setItem(NS + 'asset:' + id, r.result); res({ id, url: r.result }); }
          catch (e) { const err = new Error('file too big for local storage'); err.code = 'quota_exceeded'; rej(err); }
        };
        r.onerror = () => rej(r.error);
        r.readAsDataURL(file);
      });
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

  const caps = { db, room, user, assets, downloads, sample: null };
  window.claude = {
    local: true,
    use: async (name) => caps[name] || null,
    assetUrl: (id) => ({ '0000000000000000000000000000a001': 'assets/music/starboy_preview.mp3', '0000000000000000000000000000a002': 'assets/music/starboy_cover.jpg', '0000000000000000000000000000a003': 'assets/music/ch_rightnow.mp3', '0000000000000000000000000000a004': 'assets/music/cover_rightnow.jpg', '0000000000000000000000000000a005': 'assets/music/ch_neverblame.mp3', '0000000000000000000000000000a006': 'assets/music/cover_neverblame.jpg', '0000000000000000000000000000a007': 'assets/music/ch_darkside.mp3', '0000000000000000000000000000a008': 'assets/music/cover_darkside.jpg', '0000000000000000000000000000a009': 'assets/music/ch_darkparadise.mp3', '0000000000000000000000000000a00a': 'assets/music/cover_darkparadise.jpg', '0000000000000000000000000000a00b': 'assets/music/chever_eskizy.mp3', '0000000000000000000000000000a00c': 'assets/music/cover_eskizy.jpg', '0000000000000000000000000000a00d': 'assets/music/tcf_preview.mp3', '0000000000000000000000000000a00e': 'assets/music/tcf_cover.jpg', '0000000000000000000000000000a00f': 'assets/music/napolkah_preview.mp3', '0000000000000000000000000000a010': 'assets/music/napolkah_cover.jpg', '2c331e1611b07323ec224fb3d03b2810': 'assets/docs/d1_scene.jpg', '05f148975b74163d1e9637fe02ceee19': 'assets/docs/d2_room_fx.jpg', 'e88f9df47ce03280c216d690b6f2a3c9': 'assets/docs/d3_wall.jpg', 'f161ab8bd393bfbef4c26b60d673524f': 'assets/docs/d4_ranked.jpg', '19bc8e85e60672f2a635538acd7ba53d': 'assets/docs/d6_player.jpg', '46b2979bb94716bfcb3e6d173f29338b': 'assets/docs/d7_mobile.jpg', '695e63843468211854e9c23d89d05275': 'assets/docs/d8_smoke.jpg' })[id] || localStorage.getItem(NS + 'asset:' + id) || '',
  };
})();
