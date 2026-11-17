"""Render the "ทำอะไรได้บ้าง" (zoning + land-use ideas) section of a property page.

Zoning comes from the Department of Public Works and Town & Country Planning (DPT) layer shown in LandsMaps
(PLLU_<province> WMS, picked at the plot), checked against the plan's own text where it could be read.
Each idea carries a rough site layout: bands measured from the frontage, clipped to the real plot outline.
Same text rules as landplan.py: a Thai phrase alone in its element, numbers in data-noi18n elements.
"""
import math

from shapely.geometry import Polygon, box
from shapely.affinity import rotate

import landplan

ZONE_COLORS = {"green": "#7fb069", "pink": "#e7a3b6", "yellow": "#ecd36a"}

USE = {
    "salaya": {
        # Zoning card left out on purpose (Safe, 17 Nov 2026): DPT layer shows ก.2-10 green
        # (ผังเมืองรวมชุมชนพุทธมณฑล, ประกาศกระทรวงมหาดไทย พ.ศ. 2566), yellow ย.2 across the front road.
        "lead": "แนวคิดการใช้ที่ดินพร้อมผังคร่าว ๆ จากขนาดและทำเลของแปลง",
        "ideas": [
            {"t": "บ้านพักครอบครัวในรั้วเดียว", "d": "ที่ดินผืนใหญ่กว่า 10 ไร่ ใกล้ศาลายาและพุทธมณฑล สร้างบ้านหลายหลังสำหรับครอบครัวใหญ่ พร้อมสวนส่วนตัว",
             "bands": [(0, .3, "บ้านหลัก · ที่จอดรถ", "gold"), (.3, .7, "สวน · สระว่ายน้ำ", "green"), (.7, 1, "บ้านพักญาติ", "navy")]},
            {"t": "ฟาร์มเกษตรใกล้กรุงเทพฯ", "d": "โรงเรือนปลูกผักหรือสวนเกษตรมูลค่าสูง เดินทางเข้ากรุงเทพฯ ฝั่งตะวันตกได้สะดวก",
             "bands": [(0, .16, "จุดขาย · ลานจอด", "gold"), (.16, 1, "โรงเรือน · แปลงปลูก", "green")]},
            {"t": "บ้านพักตากอากาศและสวน", "d": "บ้านหลังใหญ่หนึ่งหลังกลางสวนร่มรื่น ที่ดินลึกจากถนน 160–180 เมตร ได้ความเป็นส่วนตัว",
             "bands": [(0, .22, "ทางเข้า · สวนหน้าบ้าน", "green"), (.22, .55, "ตัวบ้าน", "gold"), (.55, 1, "สวนผลไม้", "green")]},
        ],
    },
    "phetchabun": {
        "zone": {
            "tone": "green", "name": "ชนบทและเกษตรกรรม", "color_th": "สีเขียว", "code": "2.13",
            "plan": "ผังเมืองรวมจังหวัดเพชรบูรณ์", "law": "กฎกระทรวง พ.ศ. 2560",
            "intent": "ที่ดินที่ผังเมืองกำหนดให้ใช้เพื่อเกษตรกรรม กิจการที่เกี่ยวกับเกษตรกรรม และการอยู่อาศัย",
            "ok": ["เกษตรกรรมและกิจการที่เกี่ยวกับเกษตรกรรม", "ที่อยู่อาศัย", "สถาบันการศึกษา ศาสนา และราชการ", "สาธารณูปโภคและสาธารณูปการ"],
            "no": ["โรงงานบางประเภทตามบัญชีท้ายกฎกระทรวง", "คลังน้ำมันและคลังก๊าซเพื่อจำหน่าย", "จัดสรรที่ดินเพื่ออุตสาหกรรม พาณิชยกรรม หรือที่อยู่อาศัย"],
            "src": "ราชกิจจานุเบกษา 18 มกราคม 2560",
        },
        "ideas": [
            {"t": "สวนผลไม้และเกษตรแปลงใหญ่", "d": "ต่อยอดสวนมะม่วงและแปลงยูคาลิปตัสเดิม ที่ดินผืนเดียว 110 ไร่ จัดการง่าย",
             "bands": [(0, .08, "ลานรับซื้อ · โรงเก็บ", "gold"), (.08, 1, "สวนผลไม้ · แปลงปลูก", "green")]},
            {"t": "ฟาร์มสเตย์ริมทางหลวง", "d": "หน้ากว้างกว่า 200 เมตรติดทางหลวง 2275 ทำที่พักและร้านอาหารด้านหน้า สวนเกษตรด้านหลังเป็นจุดขาย",
             "bands": [(0, .14, "ร้านอาหาร · ลานจอด", "gold"), (.14, .4, "บ้านพักกลางสวน", "navy"), (.4, 1, "สวนเกษตร", "green")]},
            {"t": "ศูนย์ธุรกิจเกษตร", "d": "จุดรวบรวมและคัดบรรจุผลผลิตติดถนนใหญ่ ส่วนที่เหลือเป็นแปลงเกษตรของตัวเอง",
             "bands": [(0, .2, "คัดบรรจุ · โกดังผลผลิต", "gold"), (.2, 1, "แปลงเกษตร", "green")]},
        ],
    },
    "kanchanaburi": {
        "zone": {
            "tone": "green", "name": "ชนบทและเกษตรกรรม", "color_th": "สีเขียว", "code": "3.2",
            "plan": "ผังเมืองรวมจังหวัดกาญจนบุรี", "law": "กฎกระทรวง พ.ศ. 2560",
            "intent": "ที่ดินที่ผังเมืองกำหนดให้ใช้เพื่อเกษตรกรรมและการอยู่อาศัยเป็นหลัก",
            # ข้อ 8 of the plan (read 17 Nov 2026); the 2567 amendment only touches area 4.1
            "ok": ["เกษตรกรรมและกิจการที่เกี่ยวกับเกษตรกรรม", "ที่อยู่อาศัยและพาณิชยกรรม", "สถาบันการศึกษา ศาสนา และราชการ", "สาธารณูปโภคและสาธารณูปการ"],
            "no": ["โรงงานบางประเภทตามบัญชีท้ายกฎกระทรวง", "จัดสรรที่ดินเพื่อประกอบอุตสาหกรรม"],
            "src": "ราชกิจจานุเบกษา 24 กุมภาพันธ์ 2560",
        },
        "ideas": [
            {"t": "ที่พักขนาดเล็ก", "d": "ปรับปรุงบ้านพัก 10 หลังเดิมและบ่อน้ำ เปิดเป็นที่พักหรือโฮมสเตย์ ใกล้ทางด่วนกาญจนบุรี–นครปฐม",
             "bands": [(0, .45, "บ้านพักเดิม · สวนกลางบ่อ", "gold"), (.45, 1, "ลานกิจกรรม · สวน", "green")]},
            {"t": "บ้านพักตากอากาศครอบครัว", "d": "บ้านพักส่วนตัวกลางสวน ที่ดินยาวกว่า 220 เมตร มีถนนคอนกรีตล้อมสามด้าน",
             "bands": [(0, .35, "บ้านพัก · ที่จอดรถ", "gold"), (.35, 1, "สวน · บ่อน้ำ", "green")]},
            {"t": "เกษตรผสมผสาน", "d": "สวนผลไม้ แปลงผัก และบ่อเลี้ยงปลา ทำได้ทั้งเป็นรายได้และบ้านสวนวันหยุด",
             "bands": [(0, .25, "บ้านสวน", "gold"), (.25, 1, "สวนผลไม้ · แปลงผัก", "green")]},
        ],
    },
    "farm1": {
        "zone": {
            "tone": "pink", "name": "ชุมชน", "color_th": "สีชมพู", "code": "1.18",
            "plan": "ผังเมืองรวมจังหวัดกาญจนบุรี", "law": "กฎกระทรวง พ.ศ. 2560",
            "intent": "ที่ดินในเขตชุมชนเมืองกาญจนบุรี ผังเมืองกำหนดให้เป็นศูนย์กลางที่อยู่อาศัย การค้า และบริการ",
            # ข้อ 6 of the plan (read 17 Nov 2026); its factory annex starts at ลำดับที่ 7 (no farm/animal types)
            "ok": ["ที่อยู่อาศัยและพาณิชยกรรม", "เกษตรกรรม", "สถาบันการศึกษา ศาสนา และราชการ", "สาธารณูปโภคและสาธารณูปการ"],
            "no": ["โรงงานบางประเภทตามบัญชีท้ายกฎกระทรวง", "คลังน้ำมันเพื่อจำหน่าย และคลังหรือที่บรรจุก๊าซหุงต้ม", "จัดสรรที่ดินเพื่อประกอบอุตสาหกรรม"],
            "src": "ราชกิจจานุเบกษา 24 กุมภาพันธ์ 2560",
        },
        "front": "S",
        "ideas": [
            {"t": "ดำเนินกิจการฟาร์มต่อ", "d": "ฟาร์มไก่ดำพร้อมโรงเรือนและใบอนุญาต ซื้อแล้วเดินระบบต่อได้ทันที",
             "bands": [(0, .25, "สำนักงาน · โรงฟัก", "gold"), (.25, 1, "โรงเรือนเลี้ยง", "navy")]},
            {"t": "ที่ดินในเขตชุมชน", "d": "อยู่ในเขตชุมชนเมืองกาญจนบุรี ต่อยอดเป็นที่อยู่อาศัยหรือการค้าในระยะยาว",
             "bands": [(0, .3, "อาคารด้านหน้า", "gold"), (.3, 1, "พื้นที่พัฒนา", "green")]},
        ],
    },
    "farm3": {
        "ideas": [
            {"t": "ดำเนินกิจการฟาร์มต่อ", "d": "ฟาร์มไก่ 31 ไร่พร้อมโรงเรือนและระบบ ซื้อแล้วเดินกิจการต่อได้ทันที",
             "bands": [(0, .14, "สำนักงาน · โกดังอาหาร", "gold"), (.14, 1, "โรงเรือนเลี้ยง", "navy")]},
            {"t": "ขยายเป็นฟาร์มครบวงจร", "d": "พื้นที่ว่างระหว่างโรงเรือนและรอบแปลงรองรับการขยายกำลังการผลิต",
             "bands": [(0, .14, "ส่วนบริการ", "gold"), (.14, .8, "โรงเรือนเลี้ยง", "navy"), (.8, 1, "พื้นที่ขยาย", "green")]},
        ],
    },
}

DIR_DEG = {"N": 0, "NE": 45, "E": 90, "SE": 135, "S": 180, "SW": 225, "W": 270, "NW": 315}


def frontage(d, cfg):
    """(front side or None, outward bearing of the front in degrees)."""
    front = next((s for s in d["sides"] if s["front"]), None)
    if front:
        return front, front["out"]
    want = cfg.get("front")
    if want:
        cands = [s for s in d["sides"] if s["dir"] == want]
        if cands:
            s = max(cands, key=lambda q: q["len"])
            return s, s["out"]
    s = max(d["sides"], key=lambda q: q["len"])
    return s, s["out"]


def layout_svg(d, cfg, idea, has_road):
    """Plot outline turned so the frontage faces down, cut into bands by depth from the front."""
    side, out = frontage(d, cfg)
    poly = Polygon(d["outline"])
    cx, cy = poly.centroid.x, poly.centroid.y
    # rotate so that the outward normal of the front points to -y (down the page in plan, y north)
    rot = 180 - out  # bearing -> rotate the plot so this bearing becomes south (180)
    P = rotate(poly, -rot, origin=(cx, cy))  # shapely: positive = counter-clockwise; bearings are clockwise
    minx, miny, maxx, maxy = P.bounds
    depth = maxy - miny
    zones = []
    for f0, f1, label, tone in idea["bands"]:
        band = box(minx - 1, miny + f0 * depth, maxx + 1, miny + f1 * depth)
        z = P.intersection(band)
        if z.is_empty:
            continue
        zones.append((z, label, tone))
    pad = 0.08 * max(maxx - minx, depth)
    road = 0.05 * max(maxx - minx, depth) if has_road else 0
    VW = (maxx - minx) + 2 * pad
    VH = depth + pad + (pad * 0.3 + road + pad * 0.9 if has_road else pad)
    ox, oy = minx - pad, maxy + pad  # svg y down: Y = oy - y
    road_y = depth + pad + pad * 0.3

    def path(g):
        polys = [g] if g.geom_type == "Polygon" else [q for q in getattr(g, "geoms", []) if q.geom_type == "Polygon"]
        out_d = []
        for q in polys:
            pts = list(q.exterior.coords)
            out_d.append("M" + " L".join(f"{x - ox:.1f},{oy - y:.1f}" for x, y in pts) + "Z")
        return "".join(out_d)

    svg = [f'<svg class="idea-fig" viewBox="0 0 {VW:.1f} {VH:.1f}" preserveAspectRatio="xMidYMid meet" aria-hidden="true">']
    if has_road:
        svg.append(f'<rect class="lf-road" x="0" y="{road_y:.1f}" width="{VW:.1f}" height="{road:.1f}"/>')
    for z, label, tone in zones:
        svg.append(f'<path class="lf-zone {tone}" d="{path(z)}"/>')
    svg.append(f'<path class="lf-plot" d="{path(P)}"/>')
    # band separators
    for f0, f1, label, tone in idea["bands"][1:]:
        y = miny + f0 * depth
        seg = P.intersection(box(minx - 1, y - 0.01, maxx + 1, y + 0.01))
        if not seg.is_empty:
            x0, _, x1, _ = seg.bounds
            svg.append(f'<line class="lf-sep" x1="{x0 - ox:.1f}" y1="{oy - y:.1f}" x2="{x1 - ox:.1f}" y2="{oy - y:.1f}"/>')
    svg.append("</svg>")
    labels = []
    for z, label, tone in zones:
        c = z.representative_point()
        labels.append(f'<div class="lf-l" style="left:{(c.x - ox) / VW * 100:.2f}%;top:{(oy - c.y) / VH * 100:.2f}%"><div class="t">{label}</div></div>')
    if has_road:
        labels.append(f'<div class="lf-l road" style="left:50%;top:{(road_y + road / 2) / VH * 100:.2f}%"><div class="t">ถนน</div></div>')
    return f'<div class="idea-plan" style="--ar:{VW / VH:.3f}">{"".join(svg)}{"".join(labels)}</div>'


def render(slug):
    cfg = USE.get(slug)
    d = landplan.load(slug)
    if not cfg or not d:
        return ""
    has_road = any(s["road"] for s in d["sides"]) or bool(cfg.get("front"))
    z = cfg.get("zone")
    if z:
        rows = []
        if z.get("ok"):
            rows.append('<div class="zone-col"><h3 class="zone-h">ใช้ประโยชน์ได้</h3><ul class="zone-list ok">'
                        + "".join(f'<li><div class="t">{x}</div></li>' for x in z["ok"]) + "</ul></div>")
        if z.get("no"):
            rows.append('<div class="zone-col"><h3 class="zone-h">ข้อห้ามหลัก</h3><ul class="zone-list no">'
                        + "".join(f'<li><div class="t">{x}</div></li>' for x in z["no"]) + "</ul></div>")
        near = "".join(
            f'<div class="zone-near"><div class="zone-dot" style="--zc:{ZONE_COLORS[t]}"></div><div class="t">{where}</div>'
            f'<div class="t">{name}</div><div class="n" data-noi18n>{code}</div></div>' for t, where, name, code in z.get("near", []))
        src = f'<div class="t">{z["src"]}</div>' if z.get("src") else ""
        zone_html = f'''      <div class="zone-card reveal">
        <div class="zone-main">
          <div class="zone-swatch" style="--zc:{ZONE_COLORS[z['tone']]}"></div>
          <div>
            <div class="zone-k">ประเภทที่ดินตามผังเมือง</div>
            <div class="zone-name"><div class="t">{z['name']}</div></div>
            <div class="zone-meta"><div class="t">{z['color_th']}</div><div class="n" data-noi18n>{z['code']}</div></div>
          </div>
        </div>
        <div class="zone-body">
          <p class="zone-intent">{z['intent']}</p>
          <div class="zone-plan"><div class="t">{z['plan']}</div><div class="t">{z['law']}</div>{src}</div>
          {near}
          {''.join(rows) and f'<div class="zone-cols">{"".join(rows)}</div>'}
        </div>
      </div>'''
    else:
        zone_html = ""
    cards = []
    for i, idea in enumerate(cfg["ideas"]):
        cards.append(f'''        <article class="idea">
          {layout_svg(d, cfg, idea, has_road)}
          <div class="idea-n" data-noi18n>{i + 1:02d}</div>
          <h3 class="idea-t">{idea['t']}</h3>
          <p class="idea-d">{idea['d']}</p>
        </article>''')
    note = ("ข้อมูลผังเมืองจากชั้นข้อมูลของกรมโยธาธิการและผังเมืองในระบบ LandsMaps ตรวจสอบเมื่อพฤศจิกายน 2569 "
            "ผังด้านบนเป็นแนวคิดเบื้องต้นเพื่อให้เห็นภาพ ก่อนลงทุนควรตรวจสอบข้อกำหนดกับสำนักงานโยธาธิการและผังเมืองจังหวัด" if z else
            "ผังด้านบนเป็นแนวคิดเบื้องต้นเพื่อให้เห็นภาพ ก่อนลงทุนควรตรวจสอบข้อกำหนดผังเมืองกับสำนักงานโยธาธิการและผังเมืองจังหวัด")
    lead = cfg.get("lead") or ("ประเภทที่ดินตามผังเมืองรวม ณ ที่ตั้งแปลง และแนวคิดการใช้ที่ดินพร้อมผังคร่าว ๆ" if z else
                               "แนวคิดการใช้ที่ดินพร้อมผังคร่าว ๆ จากสภาพและกิจการที่มีอยู่ในปัจจุบัน")
    return f'''  <section class="use" id="sec-use">
    <div class="container">
      <div class="section-head reveal">
        <div><div class="section-num">ศักยภาพ</div></div>
        <div>
          <h2 class="section-title">ที่ดินนี้ <em>ทำอะไรได้บ้าง</em></h2>
          <p class="section-lead">{lead}</p>
        </div>
      </div>
{zone_html}
      <div class="ideas reveal{' two' if len(cards) == 2 else ''}">
{chr(10).join(cards)}
      </div>
      <p class="plot-note use-note">{note}</p>
    </div>
  </section>'''
