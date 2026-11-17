"""Render the "รูปแปลง" (plot & dimensions) section of a property page from _src/land/<slug>.json.

The JSON is produced by _src/land/tools/process.py from the Department of Lands' LandsMaps parcel polygons
(or, for N.S.3 documents that have no digital parcel, from an outline matched to satellite imagery).
Everything here is plain Python so the site build needs nothing extra.

Text rules for the translator (build.py → translate_page): a Thai phrase always sits alone in its own element,
numbers sit in their own element marked data-noi18n, and wrappers use <div> children so that no
Thai-plus-number mix ever becomes a translation key.
"""
import json
import math
import os

SRC = os.path.dirname(os.path.abspath(__file__))

DIR_TH = {"N": "ทิศเหนือ", "NE": "ทิศตะวันออกเฉียงเหนือ", "E": "ทิศตะวันออก", "SE": "ทิศตะวันออกเฉียงใต้",
          "S": "ทิศใต้", "SW": "ทิศตะวันตกเฉียงใต้", "W": "ทิศตะวันตก", "NW": "ทิศตะวันตกเฉียงเหนือ"}
SIDE_TH = {k: "ด้าน" + v for k, v in DIR_TH.items()}
OPP = {"N": "S", "S": "N", "E": "W", "W": "E", "NE": "SW", "SW": "NE", "NW": "SE", "SE": "NW"}
DOC_TH = {"โฉนดที่ดิน": "โฉนดที่ดิน (น.ส. 4 จ.)", "น.ส. 3 ก.": "หนังสือรับรองการทำประโยชน์ (น.ส. 3 ก.)",
          "น.ส. 3 ข.": "หนังสือรับรองการทำประโยชน์ (น.ส. 3 ข.)"}


def load(slug):
    p = os.path.join(SRC, "land", slug + ".json")
    if not os.path.exists(p):
        return None
    with open(p, encoding="utf8") as f:
        return json.load(f)


def num(v, approx=False, digits=1):
    s = f"{v:,.{digits}f}"
    return ("≈ " if approx else "") + s


def ni(v):
    return f'<div class="n" data-noi18n>{v}</div>'


def th(t, cls="t"):
    return f'<div class="{cls}">{t}</div>'


def pct(v, total):
    return f"{v / total * 100:.3f}%"


def upright(a):
    a = (a + 360) % 360
    if 90 < a < 270:
        a -= 180
    return a if a <= 180 else a - 360


# ───────────────────────────── geometry helpers (plan, metres, y north) ─────────────────────────────
def side_points(d, s):
    o = d["outline"]
    n = len(o)
    pts = [o[i] for i in s["edges"]]
    pts.append(o[(s["edges"][-1] + 1) % n])
    return pts


def polyline_mid(pts):
    segs = [math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]
    half = sum(segs) / 2
    for i, L in enumerate(segs):
        if half <= L:
            t = half / L if L else 0
            a, b = pts[i], pts[i + 1]
            return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t), (b[0] - a[0], b[1] - a[1])
        half -= L
    a, b = pts[-2], pts[-1]
    return b, (b[0] - a[0], b[1] - a[1])


def out_normal(bearing_deg):
    """outward normal from the side's 'out' bearing (0 = north, clockwise) as (x east, y north)."""
    r = math.radians(bearing_deg)
    return math.sin(r), math.cos(r)


def nice_scale(width_m):
    target = width_m * 0.2
    for L in (5, 10, 20, 25, 50, 100, 200, 250, 500):
        if L >= target * 0.7:
            return L
    return 1000


# ───────────────────────────── section ─────────────────────────────
def render(slug):
    d = load(slug)
    if not d:
        return None
    approx = d["source"] != "landsmaps"
    st = d["stats"]
    sides = d["sides"]
    roads = [s for s in sides if s["road"]]
    front = next((s for s in sides if s["front"]), None)

    # list order starts at the frontage and goes round; repeated directions get a running number in that order
    order = sides[:]
    if front:
        order = sides[front["k"]:] + sides[:front["k"]]
    count = {}
    for s in sides:
        count[s["dir"]] = count.get(s["dir"], 0) + 1
    run = {}
    for s in order:
        if count[s["dir"]] > 1:
            run[s["dir"]] = run.get(s["dir"], 0) + 1
            s["idx"] = run[s["dir"]]
        else:
            s["idx"] = None

    dig = 0 if approx else 1
    R = lambda v: num(v, False, dig)  # noqa: E731

    # ── stats ──
    stats = []
    if front:
        stats.append(dict(cls="key", k="หน้ากว้างติดถนน", v=R(front["len"]), u="เมตร", ap=approx,
                          sub=[th(front["road"]), th(DIR_TH[front["dir"]])]))
        a, b = st["depth_sides"]
        if abs(b - a) / max(a, b) > 0.01:
            stats.append(dict(k="ความลึกจากถนน", v=f"{a:,.0f}–{b:,.0f}", u="เมตร", ap=approx,
                              sub=[th("สั้นสุด–ยาวสุด")]))
        else:
            stats.append(dict(k="ความลึกจากถนน", v=R((a + b) / 2), u="เมตร", ap=approx, sub=[th("วัดตั้งฉากกับถนน")]))
        if len(roads) >= 2:
            names, done = [], set()
            others = [s for s in roads if s is not front]
            for s in others:  # "road · direction", naming a road only once when several sides share it
                if s["road"] not in done:
                    names.append(th(s["road"]))
                    done.add(s["road"])
                names.append(th(DIR_TH[s["dir"]]))
            stats.append(dict(k="ติดถนน", v=str(len(roads)), u="ด้าน", ap=False, sub=names))
        elif st["depth_far"] > max(a, b) * 1.05:
            stats.append(dict(k="จุดที่ลึกที่สุด", v=f"{st['depth_far']:,.0f}", u="เมตร", ap=approx, sub=[th("วัดตั้งฉากกับถนน")]))
        else:
            back = [s for s in sides if s["dir"] == OPP[front["dir"]]]
            if back:
                bs = max(back, key=lambda s: s["len"])
                stats.append(dict(k="ด้านหลัง", v=R(bs["len"]), u="เมตร", ap=approx, sub=[th(DIR_TH[bs["dir"]])]))
    else:
        stats.append(dict(cls="key", k="ความยาวแปลง", v=R(st["length"]), u="เมตร", ap=approx, sub=[th("ตามแนวยาวของแปลง")]))
        stats.append(dict(k="ความกว้างแปลง", v=R(st["width"]), u="เมตร", ap=approx, sub=[th("ตั้งฉากกับแนวยาว")]))
        stats.append(dict(k="เอกสารสิทธิ์", v=str(len(d["deeds"])), u="ฉบับ", ap=False, sub=[th("รวมเป็นผืนเดียวกัน")]))
    stats.append(dict(k="เนื้อที่ตามเอกสารสิทธิ์", v=d["area_deed"], u="ไร่", ap=False,
                      sub=[ni(f"{d['area_deed_m2']:,.0f}"), th("ตร.ม.")]))

    stat_html = "\n".join(
        f'''        <div class="plot-stat {s.get('cls', '')}">
          <div class="plot-stat-k">{s['k']}</div>
          <div class="plot-stat-v">{'<div class="ap" data-noi18n>≈</div>' if s['ap'] else ''}<div class="n" data-noi18n>{s['v']}</div><div class="u">{s['u']}</div></div>
          <div class="plot-stat-s">{''.join(s['sub'])}</div>
        </div>''' for s in stats)

    # ── side list ──
    rows = []
    for s in order:
        parts = ""
        if len(s["parts"]) > 1:
            parts = '<div class="ps-parts" data-noi18n>' + " + ".join(R(p) for p in s["parts"]) + "</div>"
        road = ""
        if s["road"]:
            road = f'<div class="ps-road"><div class="t">ติดถนน</div><div class="t">{s["road"]}</div></div>'
        idx = f'<div class="ps-idx" data-noi18n>{s["idx"]}</div>' if s["idx"] else ""
        rows.append(f'''          <li class="ps{' front' if s['front'] else ''}" data-side="{s['k']}">
            <div class="ps-dot"></div>
            <div class="ps-name"><div class="t">{SIDE_TH[s['dir']]}</div>{idx}{road}</div>
            <div class="ps-len">{'<div class="ap" data-noi18n>≈</div>' if approx else ''}<div class="n" data-noi18n>{R(s['len'])}</div><div class="u">ม.</div>{parts}</div>
          </li>''')
    rows.append(f'''          <li class="ps total">
            <div class="ps-dot"></div>
            <div class="ps-name"><div class="t">รวมเส้นรอบแปลง</div></div>
            <div class="ps-len">{'<div class="ap" data-noi18n>≈</div>' if approx else ''}<div class="n" data-noi18n>{R(st['perimeter'])}</div><div class="u">ม.</div></div>
          </li>''')

    # ── facts ──
    facts = []
    dtype = d["deeds"][0]["type"]
    facts.append(("เอกสารสิทธิ์", th(DOC_TH.get(dtype, dtype))))
    if len(d["deeds"]) > 1:
        for dd in d["deeds"]:
            facts.append((None, f'<div class="fd"><div class="t">เลขที่</div>{ni(dd["no"])}<div class="sep" data-noi18n>·</div>{ni(dd["area"])}<div class="t">ไร่</div></div>'))
    else:
        dd = d["deeds"][0]
        no = dd["no"] if "-" not in dd["no"] else dd["no"].replace("-", "–")
        facts.append(("เลขที่", ni(no)))
    if d.get("doc_sides"):
        bits = "".join(f'<div class="fd"><div class="t">{DIR_TH[k]}</div><div class="t">{txt}</div><div class="ap" data-noi18n>≈ {m}</div><div class="t">ม.</div></div>'
                       for k, txt, m in d["doc_sides"])
        facts.append(("ขนาดตามเอกสาร", bits))
    if d.get("utm"):
        facts.append(("ระวาง", ni(d["utm"])))
    if d.get("landoffice"):
        facts.append(("สำนักงานที่ดิน", th(d["landoffice"])))
    facts.append(("ข้อมูลรูปแปลง", th("กรมที่ดิน · LandsMaps" if not approx else "ประมาณจากภาพถ่ายดาวเทียม")))
    fact_html = "\n".join(
        f'          <div class="pf-row{"" if k else " sub"}">' + (f'<div class="pf-k">{k}</div>' if k else '<div class="pf-k"></div>') + f'<div class="pf-v">{v}</div></div>'
        for k, v in facts)

    lead = ("รูปแปลงจากระบบของกรมที่ดิน วัดระยะทุกด้าน หน้ากว้าง และความลึก เพื่อให้เห็นขนาดจริงของที่ดินก่อนนัดดูพื้นที่"
            if not approx else
            "แนวเขตและขนาดโดยประมาณจากภาพถ่ายดาวเทียม ประกอบกับเอกสารสิทธิ์ เพื่อให้เห็นรูปแปลงและขนาดของที่ดินก่อนนัดดูพื้นที่")
    note = ("ระยะทั้งหมดคำนวณจากรูปแปลงดิจิทัลของกรมที่ดิน อาจคลาดเคลื่อนได้ราว 1–2 เมตร ระยะที่ใช้อ้างอิงทางกฎหมายต้องรังวัดโดยเจ้าพนักงานที่ดิน"
            if not approx else
            "เอกสารสิทธิ์ประเภท น.ส. 3 ยังไม่มีรูปแปลงดิจิทัลในระบบของกรมที่ดิน ระยะในส่วนนี้จึงเป็นค่าประมาณจากภาพถ่ายดาวเทียม ระยะที่ใช้อ้างอิงทางกฎหมายต้องรังวัดโดยเจ้าพนักงานที่ดิน")

    sat = render_sat(d, approx)
    plan = render_plan(d, approx)
    v3d = render_3d(d, approx)
    aerial = render_aerial(d, approx)
    tabs = []
    if v3d:
        tabs.append(("3d", "3 มิติ", False))
    if aerial:
        tabs.append(("aerial", "มุมสูง", False))
    tabs += [("sat", "ภาพดาวเทียม", True), ("plan", "ผังแปลง", False)]
    tab_html = "\n".join(
        f'          <button class="plot-tab{" on" if on else ""}" type="button" role="tab" aria-selected="{"true" if on else "false"}" data-view="{k}">{label}</button>'
        for k, label, on in tabs)

    return f'''  <section class="dim plot" id="sec-dim">
    <div class="container">
      <div class="section-head reveal">
        <div><div class="section-num">รูปแปลง</div></div>
        <div>
          <h2 class="section-title">ขนาด <em>และรูปแปลง</em></h2>
          <p class="section-lead">{lead}</p>
        </div>
      </div>

      <div class="plot-stats reveal">
{stat_html}
      </div>

      <div class="plot-stage reveal">
        <div class="plot-tabs" role="tablist">
{tab_html}
        </div>
{v3d}
{aerial}
{sat}
{plan}
      </div>

      <div class="plot-grid reveal">
        <div class="plot-sides">
          <h3 class="plot-h">ระยะแต่ละด้าน</h3>
          <ol class="ps-list">
{chr(10).join(rows)}
          </ol>
        </div>
        <div class="plot-facts">
          <h3 class="plot-h">ข้อมูลแปลง</h3>
{fact_html}
        </div>
      </div>
      <p class="plot-note">{note}</p>
    </div>
  </section>'''


# ───────────────────────────── satellite view ─────────────────────────────
def render_sat(d, approx):
    cap = ("ภาพถ่ายดาวเทียม © Google · เส้นสีทองคือรูปแปลงจากกรมที่ดิน" if not approx else
           "ภาพถ่ายดาวเทียม © Google · เส้นสีทองคือแนวเขตโดยประมาณ")
    return render_overlay(d, approx, d["sat"], "sat", cap, "ภาพถ่ายดาวเทียมพร้อมเส้นรูปแปลง", on=True)


def render_overlay(d, approx, s, view, cap, alt, on=False):
    W, H = s["w"], s["h"]
    o = s["outline"]
    n = len(o)
    pts = " ".join(f"{x},{y}" for x, y in o)
    svg = [f'<svg class="plot-ov" viewBox="0 0 {W} {H}" preserveAspectRatio="none" aria-hidden="true">']
    for dd in s.get("deeds", []):
        q = " ".join(f"{x},{y}" for x, y in dd["px"])
        svg.append(f'<polygon class="ov-deed" points="{q}"/>')
    for e in s.get("extra", []):
        a, b = e["px"]
        svg.append(f'<line class="ov-extra" x1="{a[0]}" y1="{a[1]}" x2="{b[0]}" y2="{b[1]}"/>')
    svg.append(f'<polygon class="ov-fill" points="{pts}"/>')
    svg.append(f'<polygon class="ov-halo" points="{pts}"/>')
    svg.append(f'<polygon class="ov-line" points="{pts}"/>')
    for side in d["sides"]:
        seg = [o[i] for i in side["edges"]] + [o[(side["edges"][-1] + 1) % n]]
        q = " ".join(f"{x},{y}" for x, y in seg)
        svg.append(f'<polyline class="ov-side{" front" if side["front"] else ""}" data-side="{side["k"]}" points="{q}"/>')
    svg.append("</svg>")

    # outward direction on screen: y grows downward, so flip north
    def screen_normal(side):
        nx, ny = out_normal(side["out"])
        return nx, -ny

    longest = max(sd["len"] for sd in d["sides"])
    ranked = [sd["k"] for sd in sorted(d["sides"], key=lambda q: -q["len"]) if not sd["front"]]
    keep_small = set(ranked[:2])  # on phones only the frontage and the two longest sides keep a label
    labels = []
    for side in d["sides"]:
        if not (side["front"] or side["len"] >= 0.22 * longest or side["road"]):
            continue
        seg = [o[i] for i in side["edges"]] + [o[(side["edges"][-1] + 1) % n]]
        (mx, my), (dx, dy) = polyline_mid(seg)
        nx, ny = screen_normal(side)
        off = 30 if side["front"] else 24
        x, y = mx + nx * off, my + ny * off
        x = min(max(x, 60), W - 60)
        y = min(max(y, 18), H - 18)
        ang = upright(math.degrees(math.atan2(dy, dx)))
        val = num(side["len"], False, 0 if approx else 1)
        ap = '<div class="ap" data-noi18n>≈</div>' if approx else ""
        if side["front"]:
            inner = f'<div class="t">หน้ากว้าง</div>{ap}<div class="n" data-noi18n>{val}</div><div class="u">ม.</div>'
            cls = "pl pill front"
        else:
            inner = f'{ap}<div class="n" data-noi18n>{val}</div><div class="u">ม.</div>'
            cls = "pl pill" + ("" if side["k"] in keep_small else " minor")
        labels.append(f'<div class="{cls}" data-side="{side["k"]}" style="left:{pct(x, W)};top:{pct(y, H)};--a:{ang:.1f}deg">{inner}</div>')
    for e in s.get("extra", []):
        (ax, ay), (bx, by) = e["px"]
        mx, my = (ax + bx) / 2, (ay + by) / 2
        ang = upright(math.degrees(math.atan2(by - ay, bx - ax)))
        # put the label beside the line, away from the parcel's centre
        cx = sum(p[0] for p in o) / n
        cy = sum(p[1] for p in o) / n
        L = math.hypot(bx - ax, by - ay)
        nx, ny = -(by - ay) / L, (bx - ax) / L
        if (mx + nx - cx) ** 2 + (my + ny - cy) ** 2 < (mx - cx) ** 2 + (my - cy) ** 2:
            nx, ny = -nx, -ny
        x, y = mx + nx * 26, my + ny * 26
        labels.append(f'<div class="pl pill soft" style="left:{pct(x, W)};top:{pct(y, H)};--a:{ang:.1f}deg">'
                      f'<div class="t">{e["label"]}</div><div class="ap" data-noi18n>≈</div><div class="n" data-noi18n>{e["value"]}</div><div class="u">ม.</div></div>')
    north = '<div class="pl-north" aria-hidden="true"><svg viewBox="0 0 20 30"><path d="M10 1 17 26 10 21 3 26Z"/></svg><div class="n" data-noi18n>N</div></div>'
    return f'''        <figure class="plot-view plot-{view}{' on' if on else ''}" data-view="{view}">
          <div class="plot-canvas" style="aspect-ratio:{W}/{H}">
            <img src="/{s['img']}" alt="{alt}" width="{W}" height="{H}" loading="lazy" decoding="async">
            {"".join(svg)}
            {"".join(labels)}
            {north}
          </div>
          <figcaption class="plot-cap">{cap}</figcaption>
        </figure>'''


# ───────────────────────────── aerial photo with the outline ─────────────────────────────
def render_aerial(d, approx):
    a = d.get("aerial")
    if not a:
        return ""
    cap = ("ภาพถ่ายโดรน · เส้นสีทองคือรูปแปลงจากกรมที่ดิน" if not approx else
           "ภาพถ่ายโดรน · เส้นสีทองคือแนวเขตโดยประมาณ")
    return render_overlay(d, approx, a, "aerial", cap, "ภาพถ่ายโดรนพร้อมเส้นรูปแปลง")


# ───────────────────────────── 3D view (WebGL, see /js/plot3d.js) ─────────────────────────────
def poly_centroid(o):
    a = cx = cy = 0.0
    n = len(o)
    for i in range(n):
        (x0, y0), (x1, y1) = o[i], o[(i + 1) % n]
        c = x0 * y1 - x1 * y0
        a += c
        cx += (x0 + x1) * c
        cy += (y0 + y1) * c
    a *= 0.5
    return cx / (6 * a), cy / (6 * a)


def render_3d(d, approx):
    t = d.get("tex3d")
    if not t:
        return ""
    o = d["outline"]
    n = len(o)
    cx, cy = poly_centroid(o)
    a, b, c, dd, e, f = t["A"]
    det = a * e - b * dd

    def px2m(u, v):
        u, v = u - c, v - f
        return ((e * u - b * v) / det, (-dd * u + a * v) / det)

    W, H = t["w"], t["h"]
    corners = [px2m(0, 0), px2m(W, 0), px2m(W, H), px2m(0, H)]
    r = max(math.dist((cx, cy), p) for p in o)
    # fade ellipse in texture px, centred on the plot and kept inside the texture
    cu = a * cx + b * cy + c
    cv = dd * cx + e * cy + f
    sc = math.sqrt(abs(det))                  # texture px per metre
    cap = 1.6 * r * sc                        # keep the island in proportion to the plot
    rx, ry = min(cu, W - cu, cap), min(cv, H - cv, cap)
    island = max(rx, ry) / sc                 # metres, for framing the camera

    e2s = [0] * n
    for s in d["sides"]:
        for i in s["edges"]:
            e2s[i] = s["k"]
    front = next((s for s in d["sides"] if s["front"]), None)
    longest = max(sd["len"] for sd in d["sides"])
    ranked = [sd["k"] for sd in sorted(d["sides"], key=lambda q: -q["len"]) if not sd["front"]]
    keep = set(ranked[:2])

    R2 = lambda p: [round(p[0] - cx, 2), round(p[1] - cy, 2)]  # noqa: E731
    labels = []
    for s in d["sides"]:
        if not (s["front"] or s["k"] in keep or (s["road"] and s["len"] >= 0.22 * longest)):
            continue
        (mx, my), _ = polyline_mid(side_points(d, s))
        nx, ny = out_normal(s["out"])
        off = r * (0.075 if s["front"] else 0.06)
        x, y = mx + nx * off - cx, my + ny * off - cy
        val = num(s["len"], False, 0 if approx else 1)
        ap = '<div class="ap" data-noi18n>≈</div>' if approx else ""
        if s["front"]:
            inner = f'<div class="t">หน้ากว้าง</div>{ap}<div class="n" data-noi18n>{val}</div><div class="u">ม.</div>'
            cls = "pl pill front"
        else:
            inner = f'{ap}<div class="n" data-noi18n>{val}</div><div class="u">ม.</div>'
            cls = "pl pill" + ("" if s["k"] in keep else " minor")
        labels.append(f'<div class="{cls}" data-side="{s["k"]}" data-at="{x:.1f},{y:.1f}">{inner}</div>')

    extra = []
    for ex_px, ex in zip(t.get("extra_px", []), d["sat"].get("extra", [])):
        p0, p1 = (px2m(*q) for q in ex_px)
        extra.append([R2(p0), R2(p1)])
        mx, my = (p0[0] + p1[0]) / 2 - cx, (p0[1] + p1[1]) / 2 - cy
        labels.append(f'<div class="pl pill soft" data-at="{mx:.1f},{my:.1f}">'
                      f'<div class="t">{ex["label"]}</div><div class="ap" data-noi18n>≈</div><div class="n" data-noi18n>{ex["value"]}</div><div class="u">ม.</div></div>')

    cfg = {
        "tex": "/" + t["img"], "W": W, "H": H,
        "g": [R2(p) for p in corners],            # texture corners (TL, TR, BR, BL) in metres from the centroid
        "o": [R2(p) for p in o],                  # outline, metres from the centroid (x east, y north)
        "px": t["outline_px"],                    # outline in texture px (mask)
        "s": e2s,                                 # side index of every edge
        "f": front["k"] if front else -1,
        "fb": front["out"] if front else (d["sides"][0]["out"]),
        "r": round(r, 1),
        "ir": round(island, 1),
        "fade": [round(cu, 1), round(cv, 1), round(rx, 1), round(ry, 1)],
        "x": extra,
    }
    data = json.dumps(cfg, separators=(",", ":"), ensure_ascii=False)
    north = '<div class="pl-north p3d-north" aria-hidden="true"><svg viewBox="0 0 20 30"><path d="M10 1 17 26 10 21 3 26Z"/></svg><div class="n" data-noi18n>N</div></div>'
    cap = ("ภาพถ่ายดาวเทียม © Google · เส้นสีทองคือรูปแปลงจากกรมที่ดิน" if not approx else
           "ภาพถ่ายดาวเทียม © Google · เส้นสีทองคือแนวเขตโดยประมาณ")
    return f'''        <figure class="plot-view plot-3d" data-view="3d">
          <div class="plot-canvas p3d" data-p3d='{data}'>
            <canvas class="p3d-gl" aria-hidden="true"></canvas>
            {"".join(labels)}
            {north}
            <div class="p3d-hint"><div class="t">ลากเพื่อหมุนดูรอบแปลง</div></div>
          </div>
          <figcaption class="plot-cap">{cap}</figcaption>
        </figure>'''


# ───────────────────────────── plan view ─────────────────────────────
def render_plan(d, approx):
    o = d["outline"]
    n = len(o)
    xs = [p[0] for p in o]
    ys = [p[1] for p in o]
    w, h = max(xs) - min(xs), max(ys) - min(ys)
    span = max(w, h)
    road_w = max(span * 0.035, 8)
    pad = span * 0.13 + road_w
    minx, maxx = min(xs) - pad, max(xs) + pad
    miny, maxy = min(ys) - pad, max(ys) + pad
    if d.get("context"):
        maxy += span * 0.10
    if (maxx - minx) / (maxy - miny) < 1.3:  # tall parcels: widen the sheet so the drawing stays a sensible size
        grow = ((maxy - miny) * 1.3 - (maxx - minx)) / 2
        minx -= grow
        maxx += grow
    VW = 1000.0
    s = VW / (maxx - minx)
    VH = (maxy - miny) * s
    if VH < 420:  # keep very wide parcels from looking like a thin strip
        extra = (420 - VH) / s
        miny -= extra / 2
        maxy += extra / 2
        VH = 420.0

    def P(p):
        return ((p[0] - minx) * s, (maxy - p[1]) * s)

    O = [P(p) for p in o]
    svg = [f'<svg class="plan-svg" viewBox="0 0 {VW:.0f} {VH:.0f}" preserveAspectRatio="none" aria-hidden="true">',
           '<defs><pattern id="plgrid-' + d["slug"] + '" width="40" height="40" patternUnits="userSpaceOnUse">'
           '<path d="M40 0H0V40" fill="none" stroke="currentColor" stroke-width=".6" opacity=".07"/></pattern></defs>',
           f'<rect width="{VW:.0f}" height="{VH:.0f}" fill="url(#plgrid-{d["slug"]})"/>']
    labels = []

    # road bands
    for side in d["sides"]:
        if not side["road"]:
            continue
        seg = side_points(d, side)
        nx, ny = out_normal(side["out"])
        ext = span * 0.08
        a, b = seg[0], seg[-1]
        L = math.dist(a, b)
        ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
        inner = [(seg[0][0] - ux * ext, seg[0][1] - uy * ext)] + seg[1:-1] + [(seg[-1][0] + ux * ext, seg[-1][1] + uy * ext)]
        gap = road_w * 0.12
        near = [(x + nx * gap, y + ny * gap) for x, y in inner]
        far = [(x + nx * (gap + road_w), y + ny * (gap + road_w)) for x, y in inner][::-1]
        q = " ".join(f"{X:.1f},{Y:.1f}" for X, Y in (P(p) for p in near + far))
        svg.append(f'<polygon class="pl-road" points="{q}"/>')
        (mx, my), (dx, dy) = polyline_mid(seg)
        lx, ly = P((mx + nx * (gap + road_w / 2), my + ny * (gap + road_w / 2)))
        ang = upright(math.degrees(math.atan2(-dy, dx)))
        labels.append(f'<div class="pl road" style="left:{pct(lx, VW)};top:{pct(ly, VH)};--a:{ang:.1f}deg"><div class="t">{side["road"]}</div></div>')

    # deeds (internal boundaries)
    if len(d["deeds"]) > 1:
        for dd in d["deeds"]:
            q = " ".join(f"{X:.1f},{Y:.1f}" for X, Y in (P(p) for p in dd["ring"]))
            svg.append(f'<polygon class="pl-deed" points="{q}"/>')
            cx, cy = P(dd["c"])
            labels.append(f'<div class="pl deed" style="left:{pct(cx, VW)};top:{pct(cy, VH)}"><div class="t">โฉนด</div>{ni(dd["no"])}</div>')

    pts = " ".join(f"{X:.1f},{Y:.1f}" for X, Y in O)
    svg.append(f'<polygon class="pl-parcel" points="{pts}"/>')
    for side in d["sides"]:
        seg = [O[i] for i in side["edges"]] + [O[(side["edges"][-1] + 1) % n]]
        q = " ".join(f"{X:.1f},{Y:.1f}" for X, Y in seg)
        svg.append(f'<polyline class="pl-side{" front" if side["front"] else ""}" data-side="{side["k"]}" points="{q}"/>')
    for X, Y in O:
        svg.append(f'<circle class="pl-pt" cx="{X:.1f}" cy="{Y:.1f}" r="3.2"/>')

    # edge lengths
    longest = max(e["len"] for e in d["edges"])
    side_of = {e["i"]: e["side"] for e in d["edges"]}
    sides_by_k = {sd["k"]: sd for sd in d["sides"]}
    for e in d["edges"]:
        i = e["i"]
        sd = sides_by_k[side_of[i]]
        a, b = o[i], o[(i + 1) % n]
        mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
        nx, ny = out_normal(e["out"])
        off_m = (road_w * 1.12 + 22 / s) if sd["road"] else 20 / s
        if sd["front"] and len(sd["edges"]) == 1:
            continue
        X, Y = P((mx + nx * off_m, my + ny * off_m))
        ang = upright(math.degrees(math.atan2(-(b[1] - a[1]), b[0] - a[0])))
        minor = e["len"] < max(0.09 * longest, 12)
        val = num(e["len"], False, 0 if approx else 1)
        ap = '<div class="ap" data-noi18n>≈</div>' if approx else ""
        labels.append(f'<div class="pl len{" minor" if minor else ""}" data-side="{sd["k"]}" style="left:{pct(X, VW)};top:{pct(Y, VH)};--a:{ang:.1f}deg">{ap}<div class="n" data-noi18n>{val}</div></div>')
    # frontage label (total of the frontage side), inside the parcel along the road
    for sd in d["sides"]:
        if not sd["front"]:
            continue
        seg = side_points(d, sd)
        (mx, my), (dx, dy) = polyline_mid(seg)
        nx, ny = out_normal(sd["out"])
        X, Y = P((mx - nx * 26 / s, my - ny * 26 / s))
        ang = upright(math.degrees(math.atan2(-dy, dx)))
        val = num(sd["len"], False, 0 if approx else 1)
        ap = '<div class="ap" data-noi18n>≈</div>' if approx else ""
        labels.append(f'<div class="pl pill front" data-side="{sd["k"]}" style="left:{pct(X, VW)};top:{pct(Y, VH)};--a:{ang:.1f}deg"><div class="t">หน้ากว้าง</div>{ap}<div class="n" data-noi18n>{val}</div><div class="u">ม.</div></div>')

    # context: distance from the frontage's north end to a road further away (Salaya → Hwy 4006)
    for c in d.get("context", []):
        fr = next((sd for sd in d["sides"] if sd["front"]), None)
        if not fr:
            continue
        seg = side_points(d, fr)
        a, b = seg[0], seg[-1]
        end, other = (a, b) if a[1] > b[1] else (b, a)
        L = math.dist(a, b)
        ux, uy = (end[0] - other[0]) / L, (end[1] - other[1]) / L
        nx, ny = out_normal(fr["out"])
        base = (end[0] + nx * road_w * 0.62, end[1] + ny * road_w * 0.62)
        tip = (base[0] + ux * span * 0.22, base[1] + uy * span * 0.22)
        (X1, Y1), (X2, Y2) = P(base), P(tip)
        svg.append(f'<line class="pl-ctx" x1="{X1:.1f}" y1="{Y1:.1f}" x2="{X2:.1f}" y2="{Y2:.1f}" marker-end="url(#plarr-{d["slug"]})"/>')
        svg[1] = svg[1].replace("</defs>", f'<marker id="plarr-{d["slug"]}" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="currentColor"/></marker></defs>')
        lx, ly = P((tip[0] + ux * span * 0.03, tip[1] + uy * span * 0.03))
        edge = " r" if lx > VW * 0.78 else (" l" if lx < VW * 0.22 else "")
        labels.append(f'<div class="pl ctx{edge}" style="left:{pct(lx, VW)};top:{pct(ly, VH)}"><div class="t">{c["label"]}</div><div class="ap" data-noi18n>≈</div><div class="n" data-noi18n>{c["value"]}</div><div class="u">ม.</div></div>')

    # scale bar
    Lm = nice_scale(w)
    sx, sy = 34, VH - 34
    bar = Lm * s
    svg.append(f'<rect class="pl-bar a" x="{sx}" y="{sy:.1f}" width="{bar / 2:.1f}" height="5"/>'
               f'<rect class="pl-bar b" x="{sx + bar / 2:.1f}" y="{sy:.1f}" width="{bar / 2:.1f}" height="5"/>')
    labels.append(f'<div class="pl scale" style="left:{pct(sx, VW)};top:{pct(sy - 14, VH)}"><div class="n" data-noi18n>0</div></div>')
    labels.append(f'<div class="pl scale" style="left:{pct(sx + bar, VW)};top:{pct(sy - 14, VH)}"><div class="n" data-noi18n>{Lm}</div><div class="u">ม.</div></div>')
    svg.append("</svg>")
    north = '<div class="pl-north dark" aria-hidden="true"><svg viewBox="0 0 20 30"><path d="M10 1 17 26 10 21 3 26Z"/></svg><div class="n" data-noi18n>N</div></div>'
    cap = "ผังตามมาตราส่วน · ตัวเลขคือความยาวแต่ละช่วงเป็นเมตร · ทิศเหนืออยู่ด้านบน"
    return f'''        <figure class="plot-view plot-plan" data-view="plan">
          <div class="plot-canvas paper" style="aspect-ratio:{VW:.0f}/{VH:.0f}">
            {"".join(svg)}
            {"".join(labels)}
            {north}
          </div>
          <figcaption class="plot-cap">{cap}</figcaption>
        </figure>'''
