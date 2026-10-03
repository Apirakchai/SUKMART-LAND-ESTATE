#!/usr/bin/env python3
"""Build sukmartland.com from _src/ into the repo root.

    python3 _src/build.py

Sources: _src/pages/*.html (one per page), _src/partials/*.html, _src/site.css + extra.css,
_src/site.js, _src/i18n/<lang>.json (Thai text -> translation).
Outputs: index.html, <page>/index.html, assets/, i18n/, sitemap.xml, robots.txt, 404.html, _headers
"""
import hashlib, json, os, re, shutil, sys
from html.parser import HTMLParser

SRC = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(SRC)
SITE = 'https://sukmartland.com'
LANGS = ['en', 'zh', 'ja', 'ko', 'my', 'ru']
PHONE = '081-713-2111'

def read(p):
    with open(os.path.join(SRC, p), encoding='utf8') as f:
        return f.read()

def write(p, s):
    p = os.path.join(ROOT, p)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w', encoding='utf8') as f:
        f.write(s)

# slug -> page meta.  kind: 'site' (home / brokers / faq) or 'detail' (a property)
PAGES = {
    'home': dict(path='', kind='site',
        title='SUKMART · ที่ดินทำเลศักยภาพ 5 แปลง · เจ้าของขายเอง · 081-713-2111',
        og_title='SUKMART · ที่ดินทำเลศักยภาพ 5 แปลง',
        desc='คอลเลกชันที่ดินทำเลศักยภาพ 5 แปลง รวม 170+ ไร่ จากตระกูล SUKMART · เพชรบูรณ์ ศาลายา กาญจนบุรี · เจ้าของขายเอง เปิดรับนายหน้า · 081-713-2111',
        og='og-image.jpg'),
    'phetchabun': dict(path='phetchabun/', kind='detail',
        title='ที่ดินเพชรบูรณ์ 110 ไร่ ติดถนน 2275 · SUKMART',
        desc='ที่ดิน 110-1-59 ไร่ ต.กันจุ อ.บึงสามพัน จ.เพชรบูรณ์ ติดถนนสาย 2275 หน้ากว้าง 250 เมตร โฉนด 3 แปลง · ไร่ละ 700,000 บาท · เจ้าของขายเอง 081-713-2111',
        card=('ที่ดิน 110 ไร่ ติดถนน 2275', 'เพชรบูรณ์ · บึงสามพัน', 'images/home/main-01.jpg')),
    'salaya': dict(path='salaya/', kind='detail',
        title='ที่ดินศาลายา 10 ไร่ ติดถนน 4006 · SUKMART',
        desc='ที่ดิน 10-2-16 ไร่ ต.มหาสวัสดิ์ อ.พุทธมณฑล จ.นครปฐม ติดถนนสาย 4006 ถมแล้ว มีรั้วรอบ ใกล้ Central ศาลายา · เจ้าของขายเอง 081-713-2111',
        card=('ที่ดิน 10 ไร่ ติดถนน 4006', 'นครปฐม · ศาลายา', 'images/home/main-02.jpg')),
    'kanchanaburi': dict(path='kanchanaburi/', kind='detail',
        title='ที่ดินกาญจนบุรี 9 ไร่ เดิมเป็นรีสอร์ท · SUKMART',
        desc='ที่ดิน 9 ไร่ 36 ตร.ว. ต.หนองขาว อ.ท่าม่วง จ.กาญจนบุรี เดิมเป็นรีสอร์ท บ้านพัก 10 หลัง ใกล้ทางขึ้นมอเตอร์เวย์ M81 · ไร่ละ 2,900,000 บาท · เจ้าของขายเอง 081-713-2111',
        card=('ที่ดิน 9 ไร่ เดิมเป็นรีสอร์ท', 'กาญจนบุรี · ท่าม่วง', 'images/home/main-03.jpg')),
    'farm1': dict(path='farm1/', kind='detail',
        title='ฟาร์มไก่ดำ 8 ไร่ กาญจนบุรี · SUKMART',
        desc='ฟาร์มไก่ดำ 8-2-21.2 ไร่ ต.ท่ามะขาม อ.เมือง จ.กาญจนบุรี โรงเรือน 14 โรง พ่อแม่พันธุ์ โรงฟักไข่ครบวงจร · 89 ล้านบาทเหมาทั้งกิจการ · เจ้าของขายเอง 081-713-2111',
        card=('ฟาร์มไก่ดำ ฟาร์ม 1', 'กาญจนบุรี · ท่ามะขาม', 'images/home/main-04.jpg')),
    'farm3': dict(path='farm3/', kind='detail',
        title='ฟาร์มไก่ไทย 31 ไร่ กาญจนบุรี · SUKMART',
        desc='ฟาร์มไก่ไทย 31-2-50 ไร่ ต.ปากแพรก อ.เมือง จ.กาญจนบุรี โรงเรือน 12 โรง รองรับ 66,000 ตัว · 89 ล้านบาทเหมาทั้งกิจการ · เจ้าของขายเอง 081-713-2111',
        card=('ฟาร์มไก่ไทย ฟาร์ม 3', 'กาญจนบุรี · ปากแพรก', 'images/home/main-05.jpg')),
    'brokers': dict(path='brokers/', kind='site',
        title='สำหรับนายหน้า · ค่านายหน้า 3% · SUKMART',
        desc='เปิดรับนายหน้าทุกราย ค่านายหน้า 3% ของราคาขาย พร้อมเครื่องมือสร้างลิงก์เฉพาะแปลงสำหรับส่งลูกค้า 7 ภาษา · SUKMART 081-713-2111',
        og='og-image.jpg'),
    'faq': dict(path='faq/', kind='site',
        title='คำถามที่พบบ่อย · SUKMART',
        desc='คำถามที่พบบ่อยเรื่องราคา เอกสารสิทธิ์ ค่านายหน้า การชำระเงิน และการนัดดูพื้นที่ · SUKMART 081-713-2111',
        og='og-image.jpg'),
}
PROPS = [k for k, v in PAGES.items() if v['kind'] == 'detail']

SITE_MENU = [('home', '/', 'ที่ดินทั้งหมด'), ('brokers', '/brokers/', 'สำหรับนายหน้า'), ('faq', '/faq/', 'คำถามที่พบบ่อย')]
DETAIL_MENU = [('sec-overview', 'ภาพรวม'), ('sec-specs', 'รายละเอียด'), ('sec-dim', 'รูปแปลง'), ('sec-gallery', 'ภาพ'),
               ('sec-loc', 'ทำเล'), ('sec-docs', 'เอกสารสิทธิ์'), ('contact', 'ติดต่อ')]

def menus(slug):
    if PAGES[slug]['kind'] == 'detail':
        nav = '\n'.join(f'      <li><a data-section="{s}">{t}</a></li>' for s, t in DETAIL_MENU)
        drawer = nav.replace('      <li>', '    <li>') + '\n    <li class="drawer-sep"><a href="/" data-home>ที่ดินทั้งหมด</a></li>'
        return nav, drawer
    def item(k, href, t, ind):
        cls = ' class="here"' if k == slug else ''
        return f'{ind}<li><a href="{href}"{cls}>{t}</a></li>'
    nav = '\n'.join(item(k, h, t, '      ') for k, h, t in SITE_MENU)
    nav += '\n      <li><a href="tel:0817132111">โทร ' + PHONE + '</a></li>'
    drawer = '\n'.join(item(k, h, t, '    ') for k, h, t in SITE_MENU)
    drawer += '\n    <li><a href="https://line.me/R/ti/p/0817132111" target="_blank" rel="noopener">แชท Line</a></li>'
    drawer += '\n    <li><a href="tel:0817132111">โทร ' + PHONE + '</a></li>'
    return nav, drawer

def more_props(slug):
    cards = []
    for k in PROPS:
        if k == slug:
            continue
        t, loc, img = PAGES[k]['card']
        cards.append(f'''        <a class="more-card" href="/{k}/">
          <img src="/{img}" alt="{t}" loading="lazy" width="600" height="375" decoding="async">
          <div><b>{t}</b><span>{loc}</span></div>
        </a>''')
    return f'''
  <section class="more-props">
    <div class="container">
      <div class="section-head reveal">
        <div><div class="section-num">แปลงอื่น</div></div>
        <div><h2 class="section-title">ที่ดิน <em>แปลงอื่น</em></h2></div>
      </div>
      <div class="more-grid reveal">
{chr(10).join(cards)}
      </div>
    </div>
  </section>
'''

HEAD = '''<!DOCTYPE html>
<html lang="th">
<head>
<meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
  <title>{title}</title>
  <meta name="description" content="{desc}">
  <meta name="author" content="SUKMART">
  <link rel="canonical" href="{url}">
{robots}
  <meta property="og:type" content="website">
  <meta property="og:url" content="{url}">
  <meta property="og:title" content="{og_title}">
  <meta property="og:description" content="{desc}">
  <meta property="og:image" content="{og}">
  <meta property="og:image:secure_url" content="{og}">
  <meta property="og:image:type" content="image/jpeg">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta property="og:locale" content="th_TH">
  <meta property="og:site_name" content="SUKMART">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{og_title}">
  <meta name="twitter:description" content="{desc}">
  <meta name="twitter:image" content="{og}">
  <script>(function(){{try{{var q=new URLSearchParams(location.search).get('lang'),s=localStorage.getItem('sukmart-lang'),n=(navigator.language||'').slice(0,2).toLowerCase(),l=q||s||(['zh','ja','ko','my','ru'].indexOf(n)>-1?n:'th');if(l!=='th'){{document.documentElement.classList.add('i18n-wait');setTimeout(function(){{document.documentElement.classList.remove('i18n-wait')}},1500)}}}}catch(e){{}}}})();</script>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Noto+Serif+Thai:wght@300;400;500;600;700&family=Sarabun:ital,wght@0,300;0,400;0,500;0,600;0,700;1,300;1,400&family=Cormorant+Garamond:ital,wght@0,300;0,400;0,500;0,600;1,300;1,400&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="/assets/site.css?v={ver}">
  <script async src="https://www.googletagmanager.com/gtag/js?id=G-RS5FRK6VMZ"></script>
  <script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','G-RS5FRK6VMZ');</script>
  <link rel="icon" type="image/x-icon" href="/favicon.ico">
  <link rel="icon" type="image/svg+xml" href="/favicon.svg">
  <link rel="icon" type="image/png" sizes="16x16" href="/favicon-16x16.png">
  <link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png">
  <link rel="icon" type="image/png" sizes="96x96" href="/favicon-96x96.png">
  <link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png">
  <link rel="manifest" href="/site.webmanifest">
  <meta name="theme-color" content="#0a1f44">
</head>
<body class="{body_cls}" data-page="{slug}" data-ver="{ver}">
'''

TAIL = '''
<!-- ───── LIGHTBOX ───── -->
<div class="lb" id="lb" role="dialog" aria-label="ขยายภาพ">
  <button class="lb-close" id="lbClose" aria-label="ปิด">×</button>
  <button class="lb-prev" aria-label="ก่อนหน้า">‹</button>
  <img id="lbImg" src="data:image/gif;base64,R0lGODlhAQABAAAAACH5BAEKAAEALAAAAAABAAEAAAICTAEAOw==" alt="">
  <button class="lb-next" aria-label="ถัดไป">›</button>
</div>

<div class="float-toolbar">
  <button class="float-btn" onclick="shareLink()" aria-label="แชร์">
    <svg viewBox="0 0 24 24"><path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8"/><polyline points="16 6 12 2 8 6"/><line x1="12" y1="2" x2="12" y2="15"/></svg>
    <span class="float-btn-tooltip">แชร์ลิงก์</span>
  </button>
{print_btn}</div>
<div id="floatToast" class="float-toast" data-noi18n></div>
{extra_js}<script src="/assets/site.js?v={ver}"></script>
</body>
</html>
'''
PRINT_BTN = '''  <button class="float-btn" onclick="downloadBrochure()" aria-label="พิมพ์ / บันทึกเป็น PDF">
    <svg viewBox="0 0 24 24"><polyline points="6 9 6 2 18 2 18 9"/><path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/><rect x="6" y="14" width="12" height="8"/></svg>
    <span class="float-btn-tooltip">พิมพ์ / PDF</span>
  </button>
'''
OLD_CTA = re.compile(r'<a href="#" onclick="event\.preventDefault\(\); const c = document\.querySelector[^"]*"')

def page_html(slug, ver):
    m = PAGES[slug]
    body = read(f'pages/{slug}.html')
    contact = read('partials/contact.html').rstrip()
    body = body.replace('<!--HOME_EXTRA-->', read('partials/home-extra.html'))
    body = body.replace('{{FAQ}}', read('partials/faq-section.html').rstrip())
    body = body.replace('{{CONTACT}}', contact)
    if m['kind'] == 'detail':
        i = body.rindex('  <footer>')
        body = body[:i] + more_props(slug).lstrip('\n') + '\n' + body[i:]
    body = re.sub(r'<div id="page-(\w+)" class="page[^"]*">', r'<div id="page-\1" class="page active">', body, count=1)
    body = OLD_CTA.sub('<a href="#contact" onclick="scrollToContact(event)"', body)
    nav_menu, drawer_menu = menus(slug)
    nav = read('partials/nav.html').replace('{{NAV_MENU}}', nav_menu).replace('{{DRAWER_MENU}}', drawer_menu)
    url = f'{SITE}/{m["path"]}'
    og = f'{SITE}/' + (m.get('og') or f'og/{slug}.jpg')
    head = HEAD.format(title=m['title'], og_title=m.get('og_title', m['title']), desc=m['desc'], url=url, og=og, ver=ver, slug=slug,
                       body_cls=m['kind'], robots='')
    tail = TAIL.format(ver=ver, print_btn=PRINT_BTN if m['kind'] == 'detail' else '',
                       extra_js=f'<script src="/assets/qrcode.js?v={ver}"></script>\n' if slug == 'brokers' else '')
    html = head + nav + '\n' + body + tail
    # root-absolute asset paths so pages work from any folder
    html = re.sub(r'(src|href)="images/', r'\1="/images/', html)
    return html

class Keys(HTMLParser):
    """Collect translatable text nodes exactly like site.js does."""
    VOID = {'meta', 'link', 'img', 'br', 'input', 'hr', 'source', 'path', 'circle', 'rect', 'line', 'polyline', 'stop'}
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack, self.keys, self.in_body = [], [], False
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'body':
            self.in_body = True
        skip = tag in ('script', 'style', 'noscript') or 'data-noi18n' in a or 'lang-dd' in (a.get('class') or '').split()
        if tag not in self.VOID:
            self.stack.append((tag, skip))
    def handle_startendtag(self, tag, attrs):
        pass
    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                del self.stack[i:]
                return
    def handle_data(self, data):
        if not self.in_body or any(s for _, s in self.stack):
            return
        k = ' '.join(data.split())
        if k:
            self.keys.append(k)

def check_balance(slug, html):
    opens = len(re.findall(r'<div\b', html)); closes = html.count('</div>')
    if opens != closes:
        sys.exit(f'{slug}: <div> {opens} vs </div> {closes}')

def main():
    css = read('site.css') + '\n' + read('extra.css')
    js = read('site.js')
    i18n = {}
    for l in LANGS:
        p = os.path.join(SRC, 'i18n', l + '.json')
        i18n[l] = json.load(open(p, encoding='utf8')) if os.path.exists(p) else {}
    ver = hashlib.sha1((css + js + json.dumps(i18n, sort_keys=True)).encode()).hexdigest()[:8]

    keys, seen = [], set()
    def add(k):
        if k not in seen and re.search('[\u0e00-\u0e7f]', k):
            seen.add(k); keys.append(k)
    for slug, m in PAGES.items():
        html = page_html(slug, ver)
        check_balance(slug, html)
        write(m['path'] + 'index.html', html)
        add(m['title'])
        p = Keys(); p.feed(html)
        for k in p.keys:
            add(k)
    add('คัดลอกลิงก์เรียบร้อย')
    json.dump(keys, open(os.path.join(SRC, 'i18n', '_keys.json'), 'w', encoding='utf8'), ensure_ascii=False, indent=0)

    write('assets/site.css', css)
    write('assets/site.js', js)
    shutil.copy(os.path.join(SRC, 'vendor', 'qrcode.js'), os.path.join(ROOT, 'assets', 'qrcode.js'))
    for l in LANGS:
        used = i18n[l]
        write(f'i18n/{l}.json', json.dumps(used, ensure_ascii=False, separators=(',', ':')))
        missing = [k for k in keys if k not in i18n[l]]
        print(f'{l}: {len(used)}/{len(keys)} translated, {len(missing)} missing')

    urls = ''.join(f'  <url><loc>{SITE}/{m["path"]}</loc></url>\n' for m in PAGES.values())
    write('sitemap.xml', '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + urls + '</urlset>\n')
    write('robots.txt', f'User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n')
    write('_headers', '/assets/*\n  Cache-Control: public, max-age=31536000, immutable\n/images/*\n  Cache-Control: public, max-age=604800\n/i18n/*\n  Cache-Control: public, max-age=31536000, immutable\n')
    write('404.html', '<!DOCTYPE html><html lang="th"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="robots" content="noindex"><title>ไม่พบหน้านี้ · SUKMART</title><style>body{margin:0;min-height:100vh;display:grid;place-items:center;background:#fbfaf6;color:#0a1f44;font-family:Sarabun,-apple-system,sans-serif;text-align:center;padding:24px}a{color:#0a1f44;border-bottom:1px solid #c9a961;text-decoration:none}</style></head><body><div><h1 style="font-weight:300">ไม่พบหน้านี้</h1><p><a href="/">กลับไปหน้าที่ดินทั้งหมด · Back to all properties</a></p></div></body></html>\n')
    print('built', len(PAGES), 'pages · ver', ver, '·', len(keys), 'text keys')

if __name__ == '__main__':
    main()
