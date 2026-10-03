/* SUKMART Land Estate — site script (built by _src/build.py) */
(function () {
  'use strict';

  var BODY = document.body;
  var PAGE = BODY.dataset.page || 'home';
  var VER = BODY.dataset.ver || '1';
  var PROPS = ['phetchabun', 'salaya', 'kanchanaburi', 'farm1', 'farm3'];
  var params = new URLSearchParams(location.search);

  function store(k, v) { try { if (v === undefined) return localStorage.getItem(k); localStorage.setItem(k, v); } catch (e) { return null; } }

  /* ───── Old #hash links (sukmartland.com/#phetchabun) → real pages ───── */
  if (PAGE === 'home') {
    var h = location.hash.replace('#', '');
    if (PROPS.indexOf(h) > -1) { location.replace('/' + h + '/' + location.search); return; }
  }

  /* ───── Solo mode: link shows only this property ───── */
  var SOLO = params.has('solo') && PROPS.indexOf(PAGE) > -1;
  if (SOLO) BODY.classList.add('solo');

  function withParams(path) {
    // keep nothing by default: language lives in localStorage
    return path;
  }
  window.goDetail = function (id) { location.href = withParams('/' + id + '/'); };
  window.goHome = function () { location.href = withParams('/'); };
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
    if (currentLang !== 'th') u.searchParams.set('lang', currentLang);
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
  var dicts = { th: {} };
  var currentLang = 'th';
  var THAI_TITLE = document.title;

  function t(th) { var d = dicts[currentLang]; return (d && d[th]) || th; }

  function pickInitialLang() {
    var q = params.get('lang');
    if (q && LANGS[q]) { store('sukmart-lang', q); return q; }
    var saved = store('sukmart-lang');
    if (saved && LANGS[saved]) return saved;
    var nav = (navigator.languages && navigator.languages[0]) || navigator.language || '';
    var code = nav.slice(0, 2).toLowerCase();
    // Only auto-switch for languages we translate fully and that are clearly not Thai/English setups
    if (['zh', 'ja', 'ko', 'my', 'ru'].indexOf(code) > -1) return code;
    return 'th';
  }

  function loadDict(lang) {
    if (dicts[lang]) return Promise.resolve(dicts[lang]);
    return fetch('/i18n/' + lang + '.json?v=' + VER).then(function (r) {
      if (!r.ok) throw new Error('i18n ' + r.status);
      return r.json();
    }).then(function (d) { dicts[lang] = d; return d; });
  }

  var ATTRS = ['alt', 'aria-label', 'placeholder', 'title'];

  /* Blocks: an element whose Thai text is split by inline tags (<em>, <br>, <span>) is translated
     as ONE unit, so each language can use its own word order. Key = text with tags as <1>…</1>. */
  var THAI = /[\u0E00-\u0E7F]/;
  var INLINE = { EM: 1, B: 1, STRONG: 1, BR: 1, SPAN: 1, SUP: 1, SMALL: 1, I: 1 };
  var blocks = null;
  function serialize(el, tags) {
    var out = '';
    el.childNodes.forEach(function (n) {
      if (n.nodeType === 3) out += n.nodeValue;
      else if (n.nodeType === 1) {
        if (n.tagName === 'BR') { out += '<br>'; return; }
        tags.push(n.cloneNode(false).outerHTML.replace(/<\/[^>]+>$/, ''));
        var i = tags.length;
        out += '<' + i + '>' + serialize(n, tags) + '</' + i + '>';
      }
    });
    return out;
  }
  function findBlocks() {
    var list = [];
    document.querySelectorAll('h1,h2,h3,h4,p,li,blockquote,div,span,a,button').forEach(function (el) {
      if (el.closest('[data-noi18n], .lang-dd, [data-i18n-b], script, style')) return;
      if (!el.children.length) return;
      var ok = true, letters = 0;
      el.querySelectorAll('*').forEach(function (d) {
        if (!INLINE[d.tagName] || d.hasAttribute('data-noi18n') || d.hasAttribute('data-thb') || d.hasAttribute('onclick')) ok = false;
      });
      if (!ok) return;
      var w = document.createTreeWalker(el, NodeFilter.SHOW_TEXT), n;
      while ((n = w.nextNode())) if (THAI.test(n.nodeValue)) letters++;
      if (letters < 2) return;
      var tags = [];
      var key = serialize(el, tags).replace(/\s+/g, ' ').trim();
      el.setAttribute('data-i18n-b', '');
      list.push({ el: el, key: key, tags: tags, html: el.innerHTML });
    });
    return list;
  }
  function applyBlocks(dict) {
    if (!blocks) blocks = findBlocks();
    blocks.forEach(function (b) {
      var tr = currentLang === 'th' ? null : dict[b.key];
      if (!tr) { if (b.cur) { b.el.innerHTML = b.html; b.cur = null; } return; }
      if (b.cur === currentLang) return;
      b.el.innerHTML = tr.replace(/<(\/?)(\d+)>/g, function (m, close, i) {
        var t = b.tags[i - 1];
        if (!t) return '';
        return close ? '</' + t.match(/^<(\w+)/)[1] + '>' : t;
      });
      b.cur = currentLang;
    });
  }
  window.__i18nKeys = function () {
    if (!blocks) blocks = findBlocks();
    var keys = blocks.map(function (b) { return b.key; });
    var w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT), n;
    while ((n = w.nextNode())) {
      var p = n.parentElement;
      if (!p || p.closest('script,style,noscript,[data-noi18n],.lang-dd,[data-i18n-b]')) continue;
      var k = (n._orig !== undefined ? n._orig : n.nodeValue).trim().replace(/\s+/g, ' ');
      if (k && THAI.test(k)) keys.push(k);
    }
    keys.push(THAI_TITLE);
    return keys;
  };

  function applyTranslations() {
    var dict = dicts[currentLang] || {};
    applyBlocks(dict);
    var walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, {
      acceptNode: function (node) {
        var p = node.parentElement;
        if (!p) return NodeFilter.FILTER_REJECT;
        var tag = p.tagName;
        if (tag === 'SCRIPT' || tag === 'STYLE' || tag === 'NOSCRIPT') return NodeFilter.FILTER_REJECT;
        if (p.closest('[data-noi18n], .lang-dd, [data-i18n-b]')) return NodeFilter.FILTER_REJECT;
        if (!node.nodeValue.trim() && !node._orig) return NodeFilter.FILTER_REJECT;
        return NodeFilter.FILTER_ACCEPT;
      }
    });
    var nodes = [], n;
    while ((n = walker.nextNode())) nodes.push(n);
    nodes.forEach(function (node) {
      if (node._orig === undefined) node._orig = node.nodeValue;
      var orig = node._orig, key = orig.trim().replace(/\s+/g, ' ');
      if (currentLang === 'th' || !dict[key]) { node.nodeValue = orig; return; }
      node.nodeValue = orig.match(/^\s*/)[0] + dict[key] + orig.match(/\s*$/)[0];
    });
    document.querySelectorAll('[alt],[aria-label],[placeholder]').forEach(function (el) {
      if (el.closest('[data-noi18n], .lang-dd')) return;
      ATTRS.forEach(function (a) {
        if (!el.hasAttribute(a)) return;
        var k = '_o_' + a;
        if (el[k] === undefined) el[k] = el.getAttribute(a);
        el.setAttribute(a, currentLang === 'th' ? el[k] : (dict[el[k]] || el[k]));
      });
    });
    document.title = currentLang === 'th' ? THAI_TITLE : (dict[THAI_TITLE] || THAI_TITLE);
  }

  function setLang(lang, fromUser) {
    if (!LANGS[lang]) lang = 'th';
    return loadDict(lang).catch(function () { lang = 'th'; }).then(function () {
      currentLang = lang;
      if (fromUser) {
        store('sukmart-lang', lang);
        store('sukmart-cur', '');           // language choice resets the currency to its default
        if (params.has('lang')) {            // keep the address bar honest
          var u = new URL(location.href); u.searchParams.set('lang', lang);
          history.replaceState(null, '', u.toString());
        }
      }
      document.documentElement.lang = LANGS[lang].html;
      BODY.dataset.lang = lang;
      if (lang === 'my' && !document.getElementById('font-my')) {
        var l = document.createElement('link'); l.id = 'font-my'; l.rel = 'stylesheet';
        l.href = 'https://fonts.googleapis.com/css2?family=Noto+Sans+Myanmar:wght@300;400;500;600;700&family=Noto+Serif+Myanmar:wght@400;500;600&display=swap';
        document.head.appendChild(l);
      }
      var cur = document.getElementById('langDdCur');
      if (cur) cur.textContent = LANGS[lang].name;
      document.querySelectorAll('[data-lang-btn]').forEach(function (b) {
        b.classList.toggle('active', b.dataset.langBtn === lang);
      });
      applyTranslations();
      renderPrices();
      document.documentElement.classList.remove('i18n-wait');
    });
  }
  window.setLang = function (l) { return setLang(l, true); };

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
      var u = new URL('https://sukmartland.com/' + (prop.value ? prop.value + '/' : ''));
      if (lang.value !== 'th') u.searchParams.set('lang', lang.value);
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
  var initial = pickInitialLang();
  renderPrices();
  setLang(initial, false).then(loadRates);
})();
