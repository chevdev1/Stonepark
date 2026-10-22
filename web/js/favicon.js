// Animated tab icon: the spray can twitches and puffs paint, with a laggy glitch now and then.
(function(){
  var link = document.getElementById('favicon');
  if (!link) return;
  var reduce = false; try { reduce = localStorage.getItem('sp_motion') === 'off'; } catch(e) {}
  if (reduce) return;
  var can = new Image();
  can.onload = start;
  can.src = 'assets/img/ui/can16.png';

  var S = 2, N = 16 * S;                      // 32x32 canvas, 2x the 16px art
  var cv = document.createElement('canvas'); cv.width = cv.height = N;
  var g = cv.getContext('2d'); g.imageSmoothingEnabled = false;
  var COLORS = ['#FF8A1F', '#FFE14A', '#E8432D', '#C02AA8', '#4F6FF0'];
  var frame = 0, hold = 0, seed = 7;
  function rnd(){ seed = (seed * 16807) % 2147483647; return seed / 2147483647; }

  function draw(){
    g.clearRect(0, 0, N, N);
    var lag = hold > 0, dx = 0, dy = 0;
    // the can shakes: one pixel left/right, a hop, sometimes frozen (lag)
    var k = frame % 8;
    if (!lag){ dx = [0, -1, 0, 1, 0, 0, 1, -1][k]; dy = [0, 0, -1, 0, 0, -1, 0, 0][k]; }
    g.drawImage(can, dx * S, dy * S, N, N);
    // glitch: a band of the can slides sideways and gets an RGB ghost
    if (lag || k === 5){
      var band = 8 + ((frame * 3) % 5), off = (lag ? 3 : -2) * S;
      try {
        var d = g.getImageData(0, band * S, N, 3 * S); g.clearRect(0, band * S, N, 3 * S); g.putImageData(d, off, band * S);
        g.globalCompositeOperation = 'source-atop'; g.fillStyle = 'rgba(255,62,165,.35)'; g.fillRect(0, band * S, N, 3 * S); g.globalCompositeOperation = 'source-over';
      } catch(e) {}
    }
    // paint puffs from the nozzle (top right), rising and fading
    for (var i = 0; i < 5; i++){
      var ph = (frame + i * 3) % 12, x = 9 + i * 1.3 + Math.sin((frame + i) * 1.7) * 1.2, y = 3 - ph * 0.28;
      if (y < 0 || ph > 9) continue;
      g.globalAlpha = 1 - ph / 10; g.fillStyle = COLORS[(i + (frame >> 2)) % COLORS.length];
      g.fillRect(Math.round(x) * S, Math.round(y + 1) * S, S, S);
    }
    g.globalAlpha = 1;
    link.type = 'image/png'; link.href = cv.toDataURL('image/png');
  }
  function start(){
    draw();
    setInterval(function(){
      frame++;
      if (hold > 0) hold--; else if (rnd() < 0.09) hold = 2 + Math.floor(rnd() * 3);   // random "lag" freeze
      draw();
    }, 140);
  }
})();
