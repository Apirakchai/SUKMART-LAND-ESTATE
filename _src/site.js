/* SUKMART Land Estate — site script (built by _src/build.py) */
(function () {
  'use strict';

  var BODY = document.body;
  var PAGE = BODY.dataset.page || 'home';
  var VER = BODY.dataset.ver || '1';
  var PROPS = ['phetchabun', 'salaya', 'kanchanaburi', 'farm1', 'farm3'];
  var params = new URLSearchParams(location.search);
  var PAGE_LANG = BODY.dataset.lang || 'th';
  var PREFIX = PAGE_LANG === 'th' ? '' : '/' + PAGE_LANG;

  function store(k, v) { try { if (v === undefined) return localStorage.getItem(k); localStorage.setItem(k, v); } catch (e) { return null; } }

  /* ───── Old #hash links (sukmartland.com/#phetchabun) → real pages ───── */
  if (PAGE === 'home') {
    var h = location.hash.replace('#', '');
    if (PROPS.indexOf(h) > -1) { location.replace(PREFIX + '/' + h + '/' + location.search); return; }
  }

  /* ───── Solo mode: link shows only this property ───── */
  var SOLO = params.has('solo') && PROPS.indexOf(PAGE) > -1;
  if (SOLO) BODY.classList.add('solo');

  function withParams(path) {
    // keep nothing by default: language lives in localStorage
    return path;
  }
  window.goDetail = function (id) { location.href = withParams(PREFIX + '/' + id + '/'); };
  window.goHome = function () { location.href = withParams(PREFIX + '/'); };
  if (SOLO) {
    document.querySelectorAll('[data-home]').forEach(function (a) {
      a.removeAttribute('href'); a.style.cursor = 'default';
    });
  }

  /* ───── Filter pills (home) ───── */
  (function () {
    var pills = document.querySelectorAll('.filter-pill');
    pills.forEach(function (pill) {
      pill.addEventListener('click', function () {
        var filter = pill.dataset.filter, visible = 0;
        pills.forEach(function (p) { p.classList.remove('active'); });
        pill.classList.add('active');
        document.querySelectorAll('.card[data-category]').forEach(function (card) {
          var cats = (card.dataset.category || '').split(/\s+/);
          var show = filter === 'all' || cats.indexOf(filter) > -1;
          card.classList.toggle('filter-hidden', !show);
          if (show) visible++;
        });
        var empty = document.querySelector('.filter-empty');
        if (empty) empty.classList.toggle('show', visible === 0);
      });
    });
  })();

  /* ───── FAQ ───── */
  window.toggleFAQ = function (btn) {
    var item = btn.parentElement, open = item.classList.contains('open');
    document.querySelectorAll('.faq-item.open').forEach(function (el) { el.classList.remove('open'); });
    if (!open) item.classList.add('open');
  };

  /* ───── Reveal animations ───── */
  var io;
  function setupReveal() {
    if (!('IntersectionObserver' in window)) {
      document.querySelectorAll('.reveal').forEach(function (el) { el.classList.add('in'); });
      return;
    }
    if (io) io.disconnect();
    var rootMargin = window.innerWidth <= 768 ? '0px 0px 300px 0px' : '0px 0px 100px 0px';
    io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); }
      });
    }, { threshold: 0, rootMargin: rootMargin });
    document.querySelectorAll('.reveal:not(.in)').forEach(function (el) { io.observe(el); });
    requestAnimationFrame(function () {
      var vh = window.innerHeight;
      document.querySelectorAll('.reveal:not(.in)').forEach(function (el) {
        if (el.getBoundingClientRect().top < vh + 300) el.classList.add('in');
      });
    });
  }
  setupReveal();

  /* ───── Lightbox (with prev / next inside the same group) ───── */
  var lb = document.getElementById('lb'), lbImg = document.getElementById('lbImg');
  var lbList = [], lbIdx = 0;
  var ZOOM_SEL = '[data-zoom] img, .g-item img, .hero-img img, .overview-img img';
  function lbShow(i) {
    lbIdx = (i + lbList.length) % lbList.length;
    lbImg.src = lbList[lbIdx].currentSrc || lbList[lbIdx].src;
    lbImg.alt = lbList[lbIdx].alt;
    lb.classList.toggle('multi', lbList.length > 1);
  }
  function closeLb() { lb.classList.remove('open'); BODY.style.overflow = ''; }
  if (lb) {
    document.addEventListener('click', function (e) {
      if (e.target.closest('.lb')) return;
      var img = e.target.closest(ZOOM_SEL);
      if (!img) return;
      var group = img.closest('.deed-grid, .photo-grid, .gallery-grid');
      lbList = group ? Array.prototype.slice.call(group.querySelectorAll('img')) : [img];
      lbShow(lbList.indexOf(img));
      lb.classList.add('open');
      BODY.style.overflow = 'hidden';
    });
    document.querySelectorAll(ZOOM_SEL).forEach(function (i) { i.style.cursor = 'zoom-in'; });
    lb.addEventListener('click', function (e) {
      if (e.target.closest('.lb-prev')) { lbShow(lbIdx - 1); return; }
      if (e.target.closest('.lb-next')) { lbShow(lbIdx + 1); return; }
      closeLb();
    });
    document.addEventListener('keydown', function (e) {
      if (!lb.classList.contains('open')) return;
      if (e.key === 'Escape') closeLb();
      if (e.key === 'ArrowLeft') lbShow(lbIdx - 1);
      if (e.key === 'ArrowRight') lbShow(lbIdx + 1);
    });
  }

  /* ───── Nav: section scroll, drawer, active section ───── */
  function navH() { var n = document.querySelector('.nav'); return n ? n.offsetHeight : 0; }
  function scrollToSection(id) {
    var el = document.getElementById(id);
    if (!el) return;
    window.scrollTo({ top: el.getBoundingClientRect().top + window.scrollY - navH() - 20, behavior: 'smooth' });
  }
  window.scrollToContact = function (e) { if (e) e.preventDefault(); scrollToSection('contact'); };

  var drawer = document.getElementById('mobileDrawer');
  var drawerOverlay = document.getElementById('drawerOverlay');
  function openDrawer() { drawer.classList.add('open'); drawerOverlay.classList.add('open'); BODY.style.overflow = 'hidden'; }
  function closeDrawer() { if (!drawer) return; drawer.classList.remove('open'); drawerOverlay.classList.remove('open'); BODY.style.overflow = ''; }
  var mt = document.getElementById('menuToggle'), dc = document.getElementById('drawerClose');
  if (mt) mt.addEventListener('click', openDrawer);
  if (dc) dc.addEventListener('click', closeDrawer);
  if (drawerOverlay) drawerOverlay.addEventListener('click', closeDrawer);

  document.querySelectorAll('[data-section]').forEach(function (link) {
    link.addEventListener('click', function (e) {
      e.preventDefault(); closeDrawer(); scrollToSection(link.getAttribute('data-section'));
    });
  });

  var sectionIds = ['sec-overview', 'sec-specs', 'sec-operation', 'sec-dim', 'sec-gallery', 'sec-loc', 'sec-docs', 'contact'];
  function updateActiveSection() {
    var pos = window.scrollY + navH() + 100, active = null;
    sectionIds.forEach(function (id) {
      var el = document.getElementById(id);
      if (el && el.offsetTop <= pos) active = id;
    });
    document.querySelectorAll('.nav-menu a[data-section]').forEach(function (a) {
      a.classList.toggle('active', a.getAttribute('data-section') === active);
    });
  }
  if (BODY.classList.contains('detail')) window.addEventListener('scroll', updateActiveSection, { passive: true });

  /* ───── Toast, share, brochure ───── */
  function showToast(msg) {
    var t = document.getElementById('floatToast');
    if (!t) return;
    t.textContent = msg; t.classList.add('show');
    setTimeout(function () { t.classList.remove('show'); }, 2200);
  }
  function copyText(text) {
    if (navigator.clipboard && navigator.clipboard.writeText) return navigator.clipboard.writeText(text);
    return new Promise(function (res, rej) {
      var ta = document.createElement('textarea'); ta.value = text; ta.style.position = 'fixed'; ta.style.opacity = '0';
      document.body.appendChild(ta); ta.select();
      try { document.execCommand('copy') ? res() : rej(); } catch (e) { rej(e); }
      ta.remove();
    });
  }
  function shareUrl() {
    var u = new URL(location.origin + location.pathname);
    if (SOLO) u.searchParams.set('solo', '1');
    return u.toString();
  }
  window.shareLink = function () {
    var url = shareUrl();
    if (navigator.share) {
      navigator.share({ title: document.title, url: url }).catch(function () {});
      return;
    }
    copyText(url).then(function () { showToast(t('คัดลอกลิงก์เรียบร้อย')); }, function () { showToast(url); });
  };
  window.downloadBrochure = function () {
    var imgs = Array.prototype.slice.call(document.querySelectorAll('.page img'));
    imgs.forEach(function (img) { img.loading = 'eager'; });
    Promise.all(imgs.map(function (img) {
      if (img.complete && img.naturalHeight > 0) return null;
      return new Promise(function (resolve) {
        var timer = setTimeout(resolve, 10000);
        var done = function () { clearTimeout(timer); resolve(); };
        img.addEventListener('load', done, { once: true });
        img.addEventListener('error', done, { once: true });
      });
    })).then(function () { setTimeout(function () { window.print(); }, 300); });
  };

  /* ───── Language ───── */
  var LANGS = {
    th: { name: 'ไทย', html: 'th', locale: 'th-TH', cur: 'THB' },
    en: { name: 'English', html: 'en', locale: 'en-US', cur: 'USD' },
    zh: { name: '中文', html: 'zh-CN', locale: 'zh-CN', cur: 'CNY' },
    ja: { name: '日本語', html: 'ja', locale: 'ja-JP', cur: 'JPY' },
    ko: { name: '한국어', html: 'ko', locale: 'ko-KR', cur: 'KRW' },
    my: { name: 'မြန်မာ', html: 'my', locale: 'en-US', cur: 'USD' },
    ru: { name: 'Русский', html: 'ru', locale: 'ru-RU', cur: 'USD' }
  };
  var currentLang = LANGS[PAGE_LANG] ? PAGE_LANG : 'th';
  var STR = window.__T || {};
  function t(th) { return STR[th] || th; }

  // Every language has its own static pages: /phetchabun/ (Thai), /en/phetchabun/, /zh/phetchabun/ …
  function urlFor(lang) {
    var path = location.pathname.replace(/^\/(en|zh|ja|ko|my|ru)(?=\/)/, '');
    var q = new URLSearchParams(location.search); q.delete('lang');
    var qs = q.toString();
    return (lang === 'th' ? '' : '/' + lang) + path + (qs ? '?' + qs : '');
  }
  function wantedLang() {
    var q = params.get('lang');
    if (q && LANGS[q]) return q;                       // old-style ?lang=xx links
    if (PAGE_LANG !== 'th') return PAGE_LANG;          // an explicit language URL always wins
    var saved = store('sukmart-lang');
    if (saved && LANGS[saved]) return saved;
    var code = ((navigator.languages && navigator.languages[0]) || navigator.language || '').slice(0, 2).toLowerCase();
    return ['zh', 'ja', 'ko', 'my', 'ru'].indexOf(code) > -1 ? code : 'th';
  }
  function setLang(lang) {
    if (!LANGS[lang]) lang = 'th';
    store('sukmart-lang', lang);
    store('sukmart-cur', '');                           // language choice resets the currency to its default
    if (lang !== currentLang) location.href = urlFor(lang);
  }
  window.setLang = setLang;

  // dropdown
  (function () {
    var dd = document.getElementById('langDd'), btn = document.getElementById('langDdBtn');
    if (!dd) return;
    function close() { dd.classList.remove('open'); btn.setAttribute('aria-expanded', 'false'); }
    btn.addEventListener('click', function (e) {
      e.stopPropagation();
      var open = dd.classList.toggle('open');
      btn.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
    document.addEventListener('click', function (e) { if (!e.target.closest('#langDd')) close(); });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape') close(); });
    document.querySelectorAll('[data-lang-btn]').forEach(function (b) {
      b.addEventListener('click', function () { close(); closeDrawer(); setLang(b.dataset.langBtn, true); });
    });
  })();

  /* ───── Currency ───── */
  // Fallback rates (1 THB → x), refreshed from the network once a day.
  var RATES = { THB: 1, USD: 0.0297, CNY: 0.1999, JPY: 4.689, KRW: 40.44 };
  var RATE_DATE = null;
  var CURS = {
    THB: { sym: '฿' }, USD: { sym: '$' }, CNY: { sym: '¥' }, JPY: { sym: '¥' }, KRW: { sym: '₩' }
  };
  function currentCur() {
    var q = params.get('cur'); if (q && CURS[q.toUpperCase()]) return q.toUpperCase();
    var s = store('sukmart-cur'); if (s && CURS[s]) return s;
    return LANGS[currentLang].cur;
  }
  function roundSig(v, sig) {
    if (!v) return 0;
    var p = Math.pow(10, sig - 1 - Math.floor(Math.log10(Math.abs(v))));
    return Math.round(v * p) / p;
  }
  function locale() { return LANGS[currentLang].locale; }
  function fmtFull(thb, cur) {
    var v = cur === 'THB' ? thb : roundSig(thb * RATES[cur], 3);
    return CURS[cur].sym + new Intl.NumberFormat('en-US', { maximumFractionDigits: 0 }).format(v);
  }
  function fmtShort(thb, cur) {
    var v = cur === 'THB' ? thb : thb * RATES[cur];
    var s;
    try {
      var th = currentLang === 'th';
      s = new Intl.NumberFormat(th ? 'th-TH' : locale(),
        { notation: 'compact', compactDisplay: th ? 'long' : 'short', maximumSignificantDigits: 3 }).format(v);
    } catch (e) { s = String(Math.round(v)); }
    return CURS[cur].sym + s;
  }
  function renderPrices() {
    var cur = currentCur(), foreign = cur !== 'THB';
    document.querySelectorAll('.price-box').forEach(function (box) {
      var amt = box.querySelector('[data-thb]');
      var fx = box.querySelector('.price-fx'), note = box.querySelector('.price-fx-note'), chips = box.querySelector('.cur-chips');
      if (!amt) return;
      var thb = +amt.dataset.thb;
      var unit = box.querySelector('.price-box-unit');
      if (fx) {
        fx.hidden = !foreign;
        if (foreign) fx.textContent = '≈ ' + fmtFull(thb, cur) + ' ' + cur + (unit && /^\s*\//.test(unit.textContent) ? ' ' + unit.textContent.trim() : '');
      }
      box.querySelectorAll('[data-thb-short]').forEach(function (el) {
        var v = +el.dataset.thbShort;
        el.textContent = fmtShort(v, 'THB') + (foreign ? ' (≈ ' + fmtShort(v, cur) + ' ' + cur + ')' : (currentLang === 'th' ? 'บาท' : ''));
      });
      if (note) {
        note.hidden = !foreign;
        var d = note.querySelector('.fx-date');
        if (d) d.textContent = foreign ? '· 1 ' + cur + ' ≈ ' + (1 / RATES[cur]).toFixed(cur === 'USD' || cur === 'CNY' ? 2 : 4) + ' THB' + (RATE_DATE ? ' (' + RATE_DATE + ')' : '') : '';
      }
      if (chips) {
        chips.hidden = currentLang === 'th' && !foreign;
        if (!chips.dataset.ready) {
          chips.dataset.ready = '1';
          Object.keys(CURS).forEach(function (c) {
            var b = document.createElement('button');
            b.type = 'button'; b.className = 'cur-chip'; b.dataset.cur = c; b.textContent = c;
            b.addEventListener('click', function () { store('sukmart-cur', c); renderPrices(); });
            chips.appendChild(b);
          });
        }
        chips.querySelectorAll('.cur-chip').forEach(function (b) { b.classList.toggle('active', b.dataset.cur === cur); });
      }
    });
    document.querySelectorAll('[data-thb-card]').forEach(function (el) {
      var v = +el.dataset.thbCard;
      if (el._th === undefined) el._th = el.textContent;
      el.textContent = foreign ? '≈' + fmtShort(v, cur) : el._th;
    });
  }
  function loadRates() {
    var cached = null;
    try { cached = JSON.parse(store('sukmart-fx') || 'null'); } catch (e) {}
    function use(o) {
      Object.keys(RATES).forEach(function (c) { if (o.rates[c] > 0) RATES[c] = o.rates[c]; });
      RATES.THB = 1; RATE_DATE = o.date; renderPrices();
    }
    if (cached && cached.rates) use(cached);
    if (cached && Date.now() - cached.at < 12 * 3600 * 1000) return;
    fetch('https://open.er-api.com/v6/latest/THB').then(function (r) { return r.json(); }).then(function (j) {
      if (j.result !== 'success' || !j.rates) return;
      var o = { at: Date.now(), date: new Date(j.time_last_update_unix * 1000).toISOString().slice(0, 10), rates: {} };
      Object.keys(RATES).forEach(function (c) { o.rates[c] = j.rates[c]; });
      store('sukmart-fx', JSON.stringify(o)); use(o);
    }).catch(function () {});
  }

  /* ───── Brokers page: link builder ───── */
  (function () {
    var prop = document.getElementById('ltProp');
    if (!prop) return;
    var lang = document.getElementById('ltLang'), mode = document.getElementById('ltMode');
    var out = document.getElementById('ltUrl'), open = document.getElementById('ltOpen'), qr = document.getElementById('ltQr');
    function build() {
      var u = new URL('https://sukmartland.com/' + (lang.value !== 'th' ? lang.value + '/' : '') + (prop.value ? prop.value + '/' : ''));
      if (prop.value && mode.value === 'solo') u.searchParams.set('solo', '1');
      mode.disabled = !prop.value;
      out.value = u.toString();
      open.href = u.pathname + u.search;
      if (window.qrcode && qr) {
        var q = window.qrcode(0, 'M'); q.addData(out.value); q.make();
        qr.innerHTML = q.createImgTag(6, 12);
      }
    }
    [prop, lang, mode].forEach(function (el) { el.addEventListener('change', build); });
    document.getElementById('ltCopy').addEventListener('click', function () {
      copyText(out.value).then(function () { showToast(t('คัดลอกลิงก์เรียบร้อย')); }, function () { out.select(); });
    });
    out.addEventListener('focus', function () { out.select(); });
    build();
    window.addEventListener('load', build);
  })();

  /* ───── Analytics events ───── */
  document.addEventListener('click', function (e) {
    if (typeof window.gtag !== 'function') return;
    var a = e.target.closest('a');
    if (!a) return;
    var href = a.getAttribute('href') || '';
    var name = href.indexOf('line.me') > -1 ? 'click_line_button' : href.indexOf('tel:') === 0 ? 'click_phone_button' : href.indexOf('maps.app.goo.gl') > -1 ? 'click_map_button' : null;
    if (name) window.gtag('event', name, { event_category: 'engagement', event_label: PAGE });
  });

  /* ───── Init ───── */
  var want = wantedLang();
  if (want !== currentLang) { location.replace(urlFor(want) + location.hash); return; }
  if (params.has('lang')) { store('sukmart-lang', want); history.replaceState(null, '', urlFor(want) + location.hash); }
  var curLabel = document.getElementById('langDdCur');
  if (curLabel) curLabel.textContent = LANGS[currentLang].name;
  document.querySelectorAll('[data-lang-btn]').forEach(function (b) {
    b.classList.toggle('active', b.dataset.langBtn === currentLang);
  });
  renderPrices();
  loadRates();
})();
