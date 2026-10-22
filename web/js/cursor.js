// 8-bit spray-can cursor: the nozzle puffs paint toward the pointer tip, it revs up over clickable things,
// bursts on click and leaves a short trail of pixel paint. Mouse/trackpad only; touch screens keep their finger.
(function(){
  if (!window.matchMedia || !matchMedia('(hover: hover) and (pointer: fine)').matches) return;
  var root = document.documentElement;
  var S = 3, N = 64, OX = 14, OY = 10, HX = 7, HY = 7;      // art pixel = 3px; canvas 64px; hotspot (pointer tip) at 7,7
  var NOZ = [OX + 5 * S, OY + 1 * S];                         // nozzle, in canvas px (the sprite is mirrored: nozzle on the left)
  var COLORS = ['#FF3EA5', '#FF9A3C', '#FFD23A', '#7CFF6B', '#2EE6E6', '#3D7BFF', '#9B5CFF'];

  var can = new Image();
  can.onload = start;
  can.src = 'assets/img/ui/can16.png';

  function motionOff(){
    var m = null; try { m = localStorage.getItem('sp_motion'); } catch(e) {}
    if (m) return m === 'off';
    return !!(window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches);
  }

  function start(){
    var el = document.createElement('div'); el.id = 'pcur'; el.setAttribute('aria-hidden', 'true');
    var cv = document.createElement('canvas'); cv.width = cv.height = N; el.appendChild(cv);
    var g = cv.getContext('2d'); g.imageSmoothingEnabled = false;
    var tr = document.createElement('canvas'); tr.id = 'ptrail'; tr.setAttribute('aria-hidden', 'true');
    var tg = tr.getContext('2d');
    document.body.appendChild(tr); document.body.appendChild(el);
    root.classList.add('pcur');

    var mx = -100, my = -100, shown = false, down = false, hot = false, native = false;
    var frame = 0, parts = [], raf = 0, lastEmit = [0, 0], ci = 0;

    function sizeTrail(){ tr.width = innerWidth; tr.height = innerHeight; }
    sizeTrail(); addEventListener('resize', sizeTrail);

    // ---------- the sprite
    function draw(){
      g.clearRect(0, 0, N, N);
      var still = motionOff();
      var dy = down ? S : 0;                                              // pressed: the can sinks one pixel
      var jx = 0, jy = 0;                                                 // hovering something clickable: the can shakes; otherwise a tiny hop now and then
      if (!still){ if (hot) jx = [0, -S, 0, S][frame % 4]; else if (frame % 6 === 3) jy = -1; }
      g.save();
      g.translate(OX + 16 * S + jx, OY + dy + jy);
      g.scale(-1, 1);                                                      // nozzle toward the pointer tip
      g.drawImage(can, 0, 0, 16 * S, 16 * S);
      g.restore();
      // puffs from the nozzle flying to the tip
      if (!still){
        var n = hot || down ? 9 : 5;
        for (var i = 0; i < n; i++){
          var ph = (frame * (hot ? 2 : 1) + i * 2) % 12, t = ph / 12;
          var x = NOZ[0] - (NOZ[0] - HX) * t + Math.sin(frame + i * 2) * 1.5;
          var y = NOZ[1] + dy - (NOZ[1] - HY) * t - Math.sin(t * 3.14) * 4;
          g.globalAlpha = 1 - t * 0.85; g.fillStyle = COLORS[(i + (frame >> 2)) % COLORS.length];
          g.fillRect(Math.round(x), Math.round(y), S, S);
        }
        g.globalAlpha = 1;
      }
      // the exact tip, so aiming stays honest
      g.fillStyle = '#05090D'; g.fillRect(HX - 4, HY - 4, 8, 8);
      g.fillStyle = '#FFFFFF'; g.fillRect(HX - 2, HY - 2, 4, 4);
    }
    setInterval(function(){ if (!shown || native) return; frame++; draw(); }, 110);
    draw();

    // ---------- trail + click burst (own canvas, runs only while there are particles)
    function emit(x, y, n, speed, life){
      for (var i = 0; i < n; i++){
        var a = Math.random() * Math.PI * 2, v = Math.random() * speed;
        parts.push({ x: x, y: y, vx: Math.cos(a) * v, vy: Math.sin(a) * v - 0.4, t: 0, life: life * (0.6 + Math.random() * 0.6), c: COLORS[(ci++) % COLORS.length], s: Math.random() < 0.3 ? 4 : 3 });
      }
      if (!raf) raf = requestAnimationFrame(loop);
    }
    function loop(){
      raf = 0;
      tg.clearRect(0, 0, tr.width, tr.height);
      var alive = [];
      for (var i = 0; i < parts.length; i++){
        var p = parts[i]; p.t += 16; if (p.t >= p.life) continue;
        p.x += p.vx; p.y += p.vy; p.vy += 0.07; p.vx *= 0.97;
        tg.globalAlpha = 1 - p.t / p.life; tg.fillStyle = p.c;
        tg.fillRect(Math.round(p.x), Math.round(p.y), p.s, p.s);
        alive.push(p);
      }
      tg.globalAlpha = 1; parts = alive;
      if (parts.length) raf = requestAnimationFrame(loop);
    }

    // ---------- pointer
    var NATIVE = 'dialog, input, textarea, select, [contenteditable="true"], #wallView, #miniWrap';
    var CLICKABLE = 'a[href], button, summary, label, [role="button"], [tabindex="0"], .hot, select, input[type="range"], input[type="checkbox"], input[type="radio"]';
    function setNative(v){
      if (v === native) return; native = v;
      root.classList.toggle('pcur-native', v); el.style.visibility = v || !shown ? 'hidden' : 'visible';
    }
    function place(){ el.style.transform = 'translate3d(' + (mx - HX) + 'px,' + (my - HY) + 'px,0)'; }
    addEventListener('pointermove', function(e){
      if (e.pointerType && e.pointerType !== 'mouse' && e.pointerType !== 'pen') return;
      mx = e.clientX; my = e.clientY;
      if (!shown){ shown = true; el.style.visibility = native ? 'hidden' : 'visible'; }
      place();
      if (!motionOff() && !native){
        var d = Math.abs(mx - lastEmit[0]) + Math.abs(my - lastEmit[1]);
        if (d > 18){ lastEmit = [mx, my]; emit(mx + 2, my + 2, 1, 0.8, 520); }
      }
    }, { passive: true });
    addEventListener('pointerover', function(e){
      var t = e.target && e.target.closest ? e.target : null; if (!t) return;
      setNative(!!t.closest(NATIVE));
      var h = !!t.closest(CLICKABLE) && !native;
      if (h !== hot){ hot = h; if (h && !motionOff()) emit(mx + 2, my + 2, 5, 1.6, 420); draw(); }
    }, { passive: true });
    addEventListener('pointerdown', function(e){
      if (e.pointerType && e.pointerType !== 'mouse' && e.pointerType !== 'pen') return;
      down = true; draw();
      if (!motionOff() && !native) emit(mx + 2, my + 2, 16, 3.4, 640);
    }, { passive: true });
    addEventListener('pointerup', function(){ down = false; draw(); }, { passive: true });
    root.addEventListener('mouseleave', function(){ shown = false; el.style.visibility = 'hidden'; });
    root.addEventListener('mouseenter', function(){ if (mx > -50){ shown = true; el.style.visibility = native ? 'hidden' : 'visible'; } });

    // the wall editor goes real fullscreen: only that subtree is drawn, so the cursor moves in with it
    document.addEventListener('fullscreenchange', function(){
      var host = document.fullscreenElement || document.body;
      host.appendChild(tr); host.appendChild(el);
    });
  }
})();
