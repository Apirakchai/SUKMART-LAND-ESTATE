/* SUKMART · 3D plot view — dependency-free WebGL, loaded on demand by site.js.
   Ground: the satellite texture on a plane in metres (x east, y north → world x, -z), dimmed outside the plot
   and faded out in a soft ellipse. Boundary: a gold ribbon on the ground plus a translucent gold "fence".
   Labels are the HTML pills already in the page; they are projected every frame. */
(function () {
  'use strict';

  var GOLD = [0.937, 0.804, 0.522], GOLD_HI = [1, 0.93, 0.74], WHITE = [1, 1, 1];  // --plot-gold #efcd85
  var FOV = 30 * Math.PI / 180;
  var reduce = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;

  // ── tiny column-major mat4 helpers ──
  function perspective(o, fovy, asp, n, f) {
    var t = 1 / Math.tan(fovy / 2);
    for (var i = 0; i < 16; i++) o[i] = 0;
    o[0] = t / asp; o[5] = t; o[10] = (f + n) / (n - f); o[11] = -1; o[14] = 2 * f * n / (n - f);
    return o;
  }
  function lookAt(o, e, c) {
    var zx = e[0] - c[0], zy = e[1] - c[1], zz = e[2] - c[2], l = Math.hypot(zx, zy, zz);
    zx /= l; zy /= l; zz /= l;
    var xx = zz, xy = 0, xz = -zx;                       // up = (0,1,0) × z
    l = Math.hypot(xx, xy, xz); xx /= l; xz /= l;
    var yx = zy * xz - zz * xy, yy = zz * xx - zx * xz, yz = zx * xy - zy * xx;
    o[0] = xx; o[1] = yx; o[2] = zx; o[3] = 0;
    o[4] = xy; o[5] = yy; o[6] = zy; o[7] = 0;
    o[8] = xz; o[9] = yz; o[10] = zz; o[11] = 0;
    o[12] = -(xx * e[0] + xy * e[1] + xz * e[2]);
    o[13] = -(yx * e[0] + yy * e[1] + yz * e[2]);
    o[14] = -(zx * e[0] + zy * e[1] + zz * e[2]);
    o[15] = 1;
    return o;
  }
  function mul(o, a, b) {
    for (var i = 0; i < 4; i++) for (var j = 0; j < 4; j++) {
      var s = 0;
      for (var k = 0; k < 4; k++) s += a[k * 4 + j] * b[i * 4 + k];
      o[i * 4 + j] = s;
    }
    return o;
  }

  var VS_G = 'attribute vec3 aP;attribute vec2 aUV;uniform mat4 uM;varying vec2 vUV;' +
    'void main(){vUV=aUV;gl_Position=uM*vec4(aP,1.0);}';
  var FS_G = 'precision mediump float;uniform sampler2D uTex;uniform sampler2D uMask;uniform vec2 uSize;uniform vec4 uFade;uniform float uIn;varying vec2 vUV;' +
    'void main(){vec4 c=texture2D(uTex,vUV);float m=texture2D(uMask,vUV).r;float l=dot(c.rgb,vec3(.299,.587,.114));' +
    'vec3 o=mix(c.rgb,vec3(l),.55)*.7;vec3 col=mix(o,c.rgb*1.04,m);' +
    'vec2 q=abs(vUV*uSize-uFade.xy)/uFade.zw;q*=q;float d=sqrt(sqrt(dot(q,q)));float a=(1.0-smoothstep(.74,.985,d))*uIn;' +
    'gl_FragColor=vec4(col*a,a);}';
  var VS_L = 'attribute vec3 aP;attribute vec3 aA;uniform mat4 uM;varying vec3 vA;' +
    'void main(){vA=aA;gl_Position=uM*vec4(aP,1.0);}';
  // aA = (t: 0 bottom → 1 top, side index, front flag)
  var FS_L = 'precision mediump float;uniform vec3 uC;uniform vec3 uC2;uniform float uHL;uniform float uBase;uniform float uIn;varying vec3 vA;' +
    'void main(){float hl=1.0-step(.5,abs(vA.y-uHL));float k=max(vA.z,hl);' +
    'float a=clamp(pow(1.0-vA.x,1.5)*uBase*mix(1.0,1.9,k),0.0,1.0)*uIn;' +
    'gl_FragColor=vec4(mix(uC,uC2,k)*a,a);}';

  function shader(gl, type, src) {
    var s = gl.createShader(type);
    gl.shaderSource(s, src); gl.compileShader(s);
    if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(s));
    return s;
  }
  function program(gl, vs, fs) {
    var p = gl.createProgram();
    gl.attachShader(p, shader(gl, gl.VERTEX_SHADER, vs));
    gl.attachShader(p, shader(gl, gl.FRAGMENT_SHADER, fs));
    gl.linkProgram(p);
    if (!gl.getProgramParameter(p, gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(p));
    var u = {}, n = gl.getProgramParameter(p, gl.ACTIVE_UNIFORMS);
    for (var i = 0; i < n; i++) { var info = gl.getActiveUniform(p, i); u[info.name] = gl.getUniformLocation(p, info.name); }
    return { p: p, u: u, aP: gl.getAttribLocation(p, 'aP'), aUV: gl.getAttribLocation(p, 'aUV'), aA: gl.getAttribLocation(p, 'aA') };
  }
  function buffer(gl, arr) {
    var b = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, b);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(arr), gl.STATIC_DRAW);
    return b;
  }

  function mount(root) {
    if (root.__p3d) return root.__p3d;
    var cfg = JSON.parse(root.getAttribute('data-p3d'));
    var canvas = root.querySelector('canvas');
    var opts = { antialias: true, alpha: true, premultipliedAlpha: true, preserveDrawingBuffer: false };
    var gl = canvas.getContext('webgl2', opts) || canvas.getContext('webgl', opts);
    if (!gl) { root.classList.add('p3d-fail'); return null; }
    var gl2 = typeof WebGL2RenderingContext !== 'undefined' && gl instanceof WebGL2RenderingContext;

    var sec = root.closest('.plot');
    var o = cfg.o, n = o.length, r = cfg.r;
    var H3 = Math.min(Math.max(r * 0.075, 5), 30);       // fence height, metres
    var W3 = Math.max(0.7, r * 0.0075);                   // ribbon width, metres
    function P(p, y) { return [p[0], y || 0, -p[1]]; }

    // ── geometry ──
    var g = cfg.g, gp = [], tl = P(g[0]), tr = P(g[1]), br = P(g[2]), bl = P(g[3]);
    gp.push.apply(gp, tl.concat([0, 0], tr, [1, 0], br, [1, 1], tl, [0, 0], br, [1, 1], bl, [0, 1]));
    var walls = [], mids = [];
    var ribbon = [];
    for (var i = 0; i < n; i++) {
      var a = o[i], b = o[(i + 1) % n], s = cfg.s[i], f = s === cfg.f ? 1 : 0;
      var A0 = P(a), B0 = P(b), A1 = P(a, H3), B1 = P(b, H3);
      walls.push.apply(walls, A0.concat([0, s, f], B0, [0, s, f], B1, [1, s, f], A0, [0, s, f], B1, [1, s, f], A1, [1, s, f]));
      mids.push([(a[0] + b[0]) / 2, 0, -(a[1] + b[1]) / 2]);
      var dx = b[0] - a[0], dy = b[1] - a[1], L = Math.hypot(dx, dy) || 1, w = W3 * (f ? 1.7 : 1) / 2;
      var ux = dx / L, uy = dy / L, nx = -uy * w, ny = ux * w, ex = ux * w, ey = uy * w;
      var q = [[a[0] - ex + nx, a[1] - ey + ny], [b[0] + ex + nx, b[1] + ey + ny], [b[0] + ex - nx, b[1] + ey - ny], [a[0] - ex - nx, a[1] - ey - ny]];
      [0, 1, 2, 0, 2, 3].forEach(function (k) { ribbon.push.apply(ribbon, P(q[k], 0.05).concat([0, s, f])); });
    }
    var dash = [];
    (cfg.x || []).forEach(function (seg) {
      var a = seg[0], b = seg[1], dx = b[0] - a[0], dy = b[1] - a[1], L = Math.hypot(dx, dy), ux = dx / L, uy = dy / L;
      var dl = Math.max(2, r * 0.03), w = W3 * 0.45, nx = -uy * w, ny = ux * w;
      for (var t = 0; t < L; t += dl * 2) {
        var t1 = Math.min(L, t + dl), p0 = [a[0] + ux * t, a[1] + uy * t], p1 = [a[0] + ux * t1, a[1] + uy * t1];
        var q = [[p0[0] + nx, p0[1] + ny], [p1[0] + nx, p1[1] + ny], [p1[0] - nx, p1[1] - ny], [p0[0] - nx, p0[1] - ny]];
        [0, 1, 2, 0, 2, 3].forEach(function (k) { dash.push.apply(dash, P(q[k], 0.06).concat([0, -9, 0])); });
      }
    });

    var pg, pl;
    try { pg = program(gl, VS_G, FS_G); pl = program(gl, VS_L, FS_L); }
    catch (e) { root.classList.add('p3d-fail'); return null; }
    var bG = buffer(gl, gp), bW = buffer(gl, walls), bR = buffer(gl, ribbon), bD = dash.length ? buffer(gl, dash) : null;

    // ── textures ──
    function tex(src, mip) {
      var t = gl.createTexture();
      gl.bindTexture(gl.TEXTURE_2D, t);
      gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, false);
      gl.pixelStorei(gl.UNPACK_PREMULTIPLY_ALPHA_WEBGL, false);
      gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, src);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
      if (mip && gl2) {
        gl.generateMipmap(gl.TEXTURE_2D);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR_MIPMAP_LINEAR);
        var an = gl.getExtension('EXT_texture_filter_anisotropic') || gl.getExtension('WEBKIT_EXT_texture_filter_anisotropic');
        if (an) gl.texParameterf(gl.TEXTURE_2D, an.TEXTURE_MAX_ANISOTROPY_EXT, Math.min(8, gl.getParameter(an.MAX_TEXTURE_MAX_ANISOTROPY_EXT)));
      } else {
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
      }
      return t;
    }
    var mc = document.createElement('canvas');
    mc.width = cfg.W; mc.height = cfg.H;
    var mx = mc.getContext('2d');
    mx.fillStyle = '#000'; mx.fillRect(0, 0, cfg.W, cfg.H);
    mx.filter = 'blur(1.5px)';
    mx.fillStyle = '#fff'; mx.beginPath();
    cfg.px.forEach(function (p, k) { k ? mx.lineTo(p[0], p[1]) : mx.moveTo(p[0], p[1]); });
    mx.closePath(); mx.fill();
    var tMask = tex(mc, false), tImg = null;
    var img = new Image();
    img.decoding = 'async';
    img.onload = function () { tImg = tex(img, true); root.classList.add('p3d-ready'); t0 = 0; kick(); };
    img.onerror = function () { root.classList.add('p3d-fail'); };
    img.src = cfg.tex;

    // ── camera ──
    var phi = 56 * Math.PI / 180, theta = Math.PI - cfg.fb * Math.PI / 180 + 0.42, D = 1, asp = 1;
    var proj = new Float32Array(16), view = new Float32Array(16), mvp = new Float32Array(16);
    var cw = 1, ch = 1, eye = [0, 0, 0];
    function fit() {
      var t = Math.tan(FOV / 2), re = Math.max(r * 1.25, (cfg.ir || r * 1.5) * 1.02);
      var dh = re / (t * asp), dv = (re * Math.cos(phi) + H3 * Math.sin(phi)) / t;
      return Math.max(dh, dv) * 1.08;
    }
    function resize() {
      var dpr = Math.min(window.devicePixelRatio || 1, 2);
      cw = root.clientWidth; ch = root.clientHeight;
      if (!cw || !ch) return;
      canvas.width = Math.round(cw * dpr); canvas.height = Math.round(ch * dpr);
      asp = cw / ch; D = fit();
      kick();
    }

    // ── labels ──
    var pills = [].map.call(root.querySelectorAll('.pl[data-at]'), function (el) {
      var p = el.getAttribute('data-at').split(',').map(Number);
      return { el: el, w: [p[0], 0, -p[1]] };
    });
    var north = root.querySelector('.p3d-north svg');
    function project(w) {
      var x = w[0], y = w[1], z = w[2], m = mvp;
      var cx = m[0] * x + m[4] * y + m[8] * z + m[12], cy = m[1] * x + m[5] * y + m[9] * z + m[13], cwv = m[3] * x + m[7] * y + m[11] * z + m[15];
      if (cwv <= 0) return null;
      return [(cx / cwv + 1) / 2 * cw, (1 - cy / cwv) / 2 * ch];
    }

    // ── state, input ──
    var hl = -1, intro = reduce ? 1 : 0, t0 = 0, last = 0, idleUntil = 0, spin = 0, drag = null, raf = 0, visible = false;
    var hint = root.querySelector('.p3d-hint');
    canvas.addEventListener('pointerdown', function (e) {
      drag = { x: e.clientX, y: e.clientY, id: e.pointerId, mouse: e.pointerType === 'mouse' };
      try { canvas.setPointerCapture(e.pointerId); } catch (err) { /* ignore */ }
      if (hint) hint.classList.add('gone');
      root.classList.add('grab');
    });
    canvas.addEventListener('pointermove', function (e) {
      if (!drag || e.pointerId !== drag.id) return;
      var dx = e.clientX - drag.x, dy = e.clientY - drag.y;
      drag.x = e.clientX; drag.y = e.clientY;
      theta -= dx * 0.0065;
      if (drag.mouse) phi = Math.min(68 * Math.PI / 180, Math.max(32 * Math.PI / 180, phi - dy * 0.004));
      D = fit(); spin = 0; idleUntil = performance.now() + 3500;
      kick();
    });
    function end() { drag = null; root.classList.remove('grab'); idleUntil = performance.now() + 3500; }
    canvas.addEventListener('pointerup', end);
    canvas.addEventListener('pointercancel', end);
    if (sec) sec.addEventListener('plot:hl', function (e) { hl = e.detail.on ? e.detail.k : -1; kick(); });

    function frame(now) {
      raf = 0;
      if (!visible || !tImg || root.offsetParent === null) return;
      var dt = last ? Math.min(0.05, (now - last) / 1000) : 0;
      last = now;
      if (!t0) t0 = now;
      if (!reduce) intro = Math.min(1, (now - t0) / 1600);
      var ease = 1 - Math.pow(1 - intro, 3);
      if (!reduce && !drag && now > idleUntil) { spin = Math.min(1, spin + dt * 0.6); theta += dt * spin * (2 * Math.PI / 75); }
      var th = theta - (1 - ease) * 0.55, dd = D * (1 + (1 - ease) * 0.28);
      eye[0] = dd * Math.sin(phi) * Math.sin(th); eye[1] = dd * Math.cos(phi); eye[2] = dd * Math.sin(phi) * Math.cos(th);
      perspective(proj, FOV, asp, dd * 0.05, dd * 6);
      proj[9] = -0.1;                                   // lens shift: lift the island a little, the near side looks bigger
      lookAt(view, eye, [0, 0, 0]);
      mul(mvp, proj, view);

      gl.viewport(0, 0, canvas.width, canvas.height);
      gl.clearColor(0, 0, 0, 0); gl.clear(gl.COLOR_BUFFER_BIT);
      gl.disable(gl.DEPTH_TEST); gl.enable(gl.BLEND); gl.blendFunc(gl.ONE, gl.ONE_MINUS_SRC_ALPHA);
      var fadeIn = Math.min(1, intro * 1.6);

      // ground
      gl.useProgram(pg.p);
      gl.uniformMatrix4fv(pg.u.uM, false, mvp);
      gl.uniform2f(pg.u.uSize, cfg.W, cfg.H);
      gl.uniform4f(pg.u.uFade, cfg.fade[0], cfg.fade[1], cfg.fade[2], cfg.fade[3]);
      gl.uniform1f(pg.u.uIn, fadeIn);
      gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, tImg); gl.uniform1i(pg.u.uTex, 0);
      gl.activeTexture(gl.TEXTURE1); gl.bindTexture(gl.TEXTURE_2D, tMask); gl.uniform1i(pg.u.uMask, 1);
      gl.bindBuffer(gl.ARRAY_BUFFER, bG);
      gl.enableVertexAttribArray(pg.aP); gl.vertexAttribPointer(pg.aP, 3, gl.FLOAT, false, 20, 0);
      gl.enableVertexAttribArray(pg.aUV); gl.vertexAttribPointer(pg.aUV, 2, gl.FLOAT, false, 20, 12);
      gl.drawArrays(gl.TRIANGLES, 0, 6);
      gl.disableVertexAttribArray(pg.aUV);

      // lines and fence
      gl.useProgram(pl.p);
      gl.uniformMatrix4fv(pl.u.uM, false, mvp);
      gl.uniform1f(pl.u.uIn, fadeIn);
      gl.uniform1f(pl.u.uHL, hl);
      function draw(buf, count, c1, c2, base, order) {
        gl.uniform3fv(pl.u.uC, c1); gl.uniform3fv(pl.u.uC2, c2); gl.uniform1f(pl.u.uBase, base);
        gl.bindBuffer(gl.ARRAY_BUFFER, buf);
        gl.enableVertexAttribArray(pl.aP); gl.vertexAttribPointer(pl.aP, 3, gl.FLOAT, false, 24, 0);
        gl.enableVertexAttribArray(pl.aA); gl.vertexAttribPointer(pl.aA, 3, gl.FLOAT, false, 24, 12);
        if (order) order.forEach(function (i) { gl.drawArrays(gl.TRIANGLES, i * 6, 6); });
        else gl.drawArrays(gl.TRIANGLES, 0, count);
      }
      draw(bR, ribbon.length / 6, GOLD, GOLD_HI, 1.0);
      if (bD) draw(bD, dash.length / 6, WHITE, WHITE, 0.9);
      var order = mids.map(function (m, i) { return [i, (m[0] - eye[0]) * (m[0] - eye[0]) + (m[2] - eye[2]) * (m[2] - eye[2])]; })
        .sort(function (a, b) { return b[1] - a[1]; }).map(function (x) { return x[0]; });
      draw(bW, walls.length / 6, GOLD, GOLD_HI, 0.34, order);

      // labels + compass
      pills.forEach(function (p) {
        var s = project(p.w);
        if (!s || s[0] < -20 || s[0] > cw + 20 || s[1] < -20 || s[1] > ch + 20) { p.el.style.opacity = 0; return; }
        p.el.style.opacity = fadeIn;
        p.el.style.setProperty('--x', s[0].toFixed(1) + 'px');
        p.el.style.setProperty('--y', s[1].toFixed(1) + 'px');
      });
      if (north) {
        var c0 = project([0, 0, 0]), c1 = project([0, 0, -r * 0.3]);
        if (c0 && c1) north.style.transform = 'rotate(' + (Math.atan2(c1[0] - c0[0], c0[1] - c1[1]) * 180 / Math.PI).toFixed(1) + 'deg)';
      }
      if (intro < 1 || spin > 0 || drag) kick();
      else if (!reduce && now <= idleUntil) setTimeout(kick, Math.max(16, idleUntil - now));
    }
    function kick() { if (!raf && visible) raf = requestAnimationFrame(frame); }

    if ('ResizeObserver' in window) new ResizeObserver(resize).observe(root);
    else window.addEventListener('resize', resize);
    if ('IntersectionObserver' in window) {
      new IntersectionObserver(function (es) { visible = es[0].isIntersecting; last = 0; kick(); }, { rootMargin: '80px' }).observe(root);
    } else visible = true;
    document.addEventListener('visibilitychange', function () { last = 0; kick(); });
    if (sec) sec.addEventListener('plot:view', function () { last = 0; resize(); kick(); });
    canvas.addEventListener('webglcontextlost', function (e) { e.preventDefault(); root.classList.add('p3d-fail'); });
    resize();
    root.__p3d = { kick: kick };
    return root.__p3d;
  }

  window.SukmartPlot3D = { mount: mount };
  document.querySelectorAll('.p3d[data-p3d]').forEach(function (el) { if (el.offsetParent !== null) mount(el); });
})();
