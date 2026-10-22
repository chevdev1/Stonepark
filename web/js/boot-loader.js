// First-visit loader: a short pixel "descent" while the key art loads. Repeat visitors skip it.
(function(){
  var boot = document.getElementById('boot');
  if (!boot) return;
  var root = document.documentElement;
  if (!root.classList.contains('first')){ boot.remove(); return; }

  var lang = 'ru';
  try { var s = localStorage.getItem('sp_lang'); if (s === 'en' || s === 'ru') lang = s; else if (!/^ru/i.test(navigator.language || '')) lang = 'en'; } catch(e) {}
  var TIPS = {
    ru: ['Спускаемся в подземку…', 'Трясём балончик…', 'Греем стену…', 'Ищем CH…', 'Почти на месте…'],
    en: ['Heading underground…', 'Shaking the can…', 'Warming up the wall…', 'Looking for CH…', 'Almost there…']
  }[lang];
  var fill = document.getElementById('bootFill'), pct = document.getElementById('bootPct'), tip = document.getElementById('bootTip');
  var reduce = false; try { reduce = matchMedia('(prefers-reduced-motion: reduce)').matches || localStorage.getItem('sp_motion') === 'off'; } catch(e) {}
  root.classList.add('booting');

  // what we wait for: the art the player sees first
  var ASSETS = ['assets/img/scene_still.png', 'assets/img/ui/p_vex.png', 'assets/img/ui/p_vex_0.png', 'assets/img/ui/p_vex_1.png', 'assets/img/ui/rocket.png', 'assets/img/scene_sheet.png'];
  var total = ASSETS.length + 2, got = 0;
  function tick(){ got++; }
  ASSETS.forEach(function(u){ var i = new Image(); i.onload = i.onerror = tick; i.src = u; });
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(tick, tick); else tick();
  if (document.readyState === 'complete') tick(); else window.addEventListener('load', tick);

  var t0 = Date.now(), MIN = reduce ? 500 : 1700, MAX = 7000, shown = 0, done = false, tipI = 0;
  var tipTimer = setInterval(function(){ tipI = Math.min(TIPS.length - 1, tipI + 1); tip.textContent = TIPS[tipI]; }, 900);
  tip.textContent = TIPS[0];

  function finish(){
    if (done) return; done = true; clearInterval(tipTimer); clearInterval(loop);
    fill.style.width = '100%'; pct.textContent = '100%';
    boot.classList.add('out');
    setTimeout(function(){ boot.remove(); root.classList.remove('booting'); }, reduce ? 0 : 380);
  }
  var loop = setInterval(function(){
    var age = Date.now() - t0;
    // real progress, but never faster than the minimum show time and never stuck
    var target = Math.min(got / total, age / MIN);
    shown += (target - shown) * 0.25;
    var p = Math.min(99, Math.round(shown * 100));
    fill.style.width = p + '%'; pct.textContent = p + '%';
    if ((got >= total && age >= MIN) || age >= MAX) finish();
  }, 60);
})();
