"""Turn the raw LandsMaps / satellite data into the per-property JSON used by the website (_src/land/<slug>.json).

Needs pyproj + shapely + Pillow (not needed by the site build itself).
    python3 process.py            # writes ../sukmart-land-estate/_src/land/*.json and images/<slug>/plot-sat.jpg
"""
import json
import math
import os

from PIL import Image
from pyproj import Geod, Transformer
from shapely.geometry import Polygon
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(os.path.dirname(HERE), "sukmart-land-estate")
OUT = os.path.join(SITE, "_src", "land")
os.makedirs(OUT, exist_ok=True)

geod = Geod(ellps="WGS84")
to_utm = Transformer.from_crs("EPSG:4326", "EPSG:32647", always_xy=True)
CHECKED = "2026-11-17"

DIRS = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]


def wind(bearing):
    return DIRS[int(((bearing % 360) + 22.5) // 45) % 8]


def rai_to_m2(s):
    r, n, w = s.split("-")
    return int(r) * 1600 + int(n) * 400 + float(w) * 4


def geo_len(a, b):
    return geod.inv(a[0], a[1], b[0], b[1])[2]


def ring_area(lonlat):
    lons = [p[0] for p in lonlat] + [lonlat[0][0]]
    lats = [p[1] for p in lonlat] + [lonlat[0][1]]
    return abs(geod.polygon_area_perimeter(lons, lats)[0])


def clean_ring(coords):
    pts = [tuple(p) for p in coords]
    if pts[0] == pts[-1]:
        pts = pts[:-1]
    out = []
    for p in pts:  # drop duplicates
        if not out or (abs(out[-1][0] - p[0]) > 1e-9 or abs(out[-1][1] - p[1]) > 1e-9):
            out.append(p)
    # drop collinear points (straight-through vertices), tolerance in metres
    changed = True
    while changed and len(out) > 3:
        changed = False
        for i in range(len(out)):
            a, b, c = out[i - 1], out[i], out[(i + 1) % len(out)]
            (ax, ay), (bx, by), (cx, cy) = (to_utm.transform(*a), to_utm.transform(*b), to_utm.transform(*c))
            L = math.hypot(cx - ax, cy - ay)
            if L == 0:
                continue
            d = abs((cx - ax) * (by - ay) - (cy - ay) * (bx - ax)) / L
            if d < 0.25:
                out.pop(i)
                changed = True
                break
    return out


def bearing(a, b):
    return geod.inv(a[0], a[1], b[0], b[1])[0] % 360


def build(cfg):
    slug = cfg["slug"]
    deeds = cfg["deeds"]
    polys = {k: Polygon(d["ring"]) for k, d in deeds.items()}
    if len(polys) > 1:
        # snap tiny gaps between neighbouring deeds before the union
        u = unary_union([p.buffer(1e-7, join_style=2) for p in polys.values()]).buffer(-1e-7, join_style=2)
    else:
        u = list(polys.values())[0]
    if u.geom_type != "Polygon":
        u = max(u.geoms, key=lambda g: g.area)
    outer = clean_ring(list(u.exterior.coords))
    # orient clockwise on the map (x east, y north) so that "outward" is to the left of travel
    xy = [to_utm.transform(*p) for p in outer]
    s2 = sum(xy[i][0] * xy[(i + 1) % len(xy)][1] - xy[(i + 1) % len(xy)][0] * xy[i][1] for i in range(len(xy)))
    if s2 > 0:  # counter-clockwise -> reverse
        outer = outer[::-1]
        xy = xy[::-1]
    n = len(outer)
    minx = min(p[0] for p in xy)
    miny = min(p[1] for p in xy)
    loc = [(round(x - minx, 2), round(y - miny, 2)) for x, y in xy]

    edges = []
    for i in range(n):
        a, b = outer[i], outer[(i + 1) % n]
        edges.append({"i": i, "len": round(geo_len(a, b), 2), "brg": round(bearing(a, b), 1)})
    # outward normal bearing for clockwise ring = travel bearing - 90
    for e in edges:
        e["out"] = (e["brg"] - 90) % 360

    # group consecutive edges into sides when the direction barely changes
    def ang(a, b):
        d = abs(a - b) % 360
        return min(d, 360 - d)

    sides = []
    for e in edges:
        if sides and ang(sides[-1]["brg"], e["brg"]) < cfg.get("merge_deg", 12):
            s = sides[-1]
            s["edges"].append(e["i"])
        else:
            sides.append({"edges": [e["i"]], "brg": e["brg"]})
    if len(sides) > 1 and ang(sides[-1]["brg"], sides[0]["brg"]) < cfg.get("merge_deg", 12):
        sides[0]["edges"] = sides[-1]["edges"] + sides[0]["edges"]
        sides.pop()
    for s in sides:
        s["len"] = round(sum(edges[i]["len"] for i in s["edges"]), 2)
        s["parts"] = [edges[i]["len"] for i in s["edges"]]
        # direction of the side's outward normal, weighted by length
        vx = sum(math.sin(math.radians(edges[i]["out"])) * edges[i]["len"] for i in s["edges"])
        vy = sum(math.cos(math.radians(edges[i]["out"])) * edges[i]["len"] for i in s["edges"])
        s["out"] = round(math.degrees(math.atan2(vx, vy)) % 360, 1)
        s["dir"] = wind(s["out"])
        del s["brg"]
    # roads / frontage from config
    for s in sides:
        s["road"] = None
        s["front"] = False
    for r in cfg.get("roads", []):
        cand = [s for s in sides if s["dir"] in r["dirs"]]
        if not cand:
            raise SystemExit(f"{slug}: no side facing {r['dirs']}")
        s = max(cand, key=lambda q: q["len"])
        s["road"] = r["name"]
        s["front"] = bool(r.get("front"))
    for k, s in enumerate(sides):
        s["k"] = k
        for i in s["edges"]:
            edges[i]["side"] = k

    stats = {"perimeter": round(sum(e["len"] for e in edges), 1), "area_poly_m2": round(ring_area(outer), 0)}
    fronts = [s for s in sides if s["front"]]
    if fronts:
        f = fronts[0]
        stats["frontage"] = f["len"]
        stats["frontage_side"] = f["k"]
        a = xy[f["edges"][0]]
        b = xy[(f["edges"][-1] + 1) % n]
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
        depths = [abs((p[0] - a[0]) * uy - (p[1] - a[1]) * ux) for p in xy]
        stats["depth_far"] = round(max(depths), 1)
        # the sides that leave the frontage at each end
        k = f["k"]
        nb = [sides[(k - 1) % len(sides)], sides[(k + 1) % len(sides)]]
        stats["depth_sides"] = sorted(round(s["len"], 1) for s in nb)
    else:
        mrr = Polygon(xy).minimum_rotated_rectangle
        c = list(mrr.exterior.coords)[:4]
        l1 = math.hypot(c[1][0] - c[0][0], c[1][1] - c[0][1])
        l2 = math.hypot(c[2][0] - c[1][0], c[2][1] - c[1][1])
        stats["length"] = round(max(l1, l2), 1)
        stats["width"] = round(min(l1, l2), 1)

    deed_out = []
    for no, d in deeds.items():
        r = clean_ring(d["ring"])
        rxy = [to_utm.transform(*p) for p in r]
        cx, cy = Polygon(rxy).representative_point().coords[0]
        deed_out.append({"no": no, "type": d.get("type", ""), "area": d.get("area", ""),
                         "ring": [(round(x - minx, 2), round(y - miny, 2)) for x, y in rxy],
                         "c": (round(cx - minx, 2), round(cy - miny, 2)),
                         "area_m2_poly": round(ring_area(r), 0)})

    # ---- satellite image: crop + pixel coordinates -------------------------------------
    cap = cfg["capture"]
    im = Image.open(os.path.join(HERE, cap["file"]))
    x0, y0, x1, y1 = cap["crop"]
    crop = im.crop((x0, y0, x1, y1))
    scale = cfg.get("img_w", 1200) / crop.size[0]
    if scale < 1:
        crop = crop.resize((round(crop.size[0] * scale), round(crop.size[1] * scale)), Image.LANCZOS)
    else:
        scale = 1.0
    img_rel = f"images/{slug}/plot-sat.jpg"
    crop.save(os.path.join(SITE, img_rel), quality=86, optimize=True, progressive=True, subsampling=0)

    def px(lonlat_pt):
        return cap["to_px"](lonlat_pt)

    sat_outline = []
    for p in outer:
        X, Y = px(p)
        sat_outline.append((round((X - x0) * scale, 1), round((Y - y0) * scale, 1)))
    sat_deeds = []
    if len(deeds) > 1:
        for no, d in deeds.items():
            pts = []
            for p in clean_ring(d["ring"]):
                X, Y = px(p)
                pts.append((round((X - x0) * scale, 1), round((Y - y0) * scale, 1)))
            sat_deeds.append({"no": no, "px": pts})
    extra = []
    for e in cfg.get("sat_extra", []):
        pts = []
        for p in e["pts"]:
            X, Y = px(p)
            pts.append((round((X - x0) * scale, 1), round((Y - y0) * scale, 1)))
        extra.append({**{k: v for k, v in e.items() if k != "pts"}, "px": pts})

    data = {
        "slug": slug, "source": cfg["source"], "checked": CHECKED,
        "area_deed": cfg["area_deed"], "area_deed_m2": rai_to_m2(cfg["area_deed"]),
        "outline": loc, "outline_lonlat": [(round(p[0], 8), round(p[1], 8)) for p in outer],
        "edges": edges, "sides": sides, "stats": stats, "deeds": deed_out,
        "landoffice": cfg.get("landoffice"), "utm": cfg.get("utm"), "doc_sides": cfg.get("doc_sides"),
        "context": cfg.get("context", []),
        "sat": {"img": img_rel, "w": crop.size[0], "h": crop.size[1], "outline": sat_outline, "deeds": sat_deeds, "extra": extra},
    }
    json.dump(data, open(os.path.join(OUT, f"{slug}.json"), "w"), ensure_ascii=False, indent=1)
    return data


def screen_mapper(view_tl, view_br, y_top=58, w=1200, h=796):
    """Linear lon/lat -> screen px for a Cesium 2D (geographic) view given the corner coordinates."""
    (lon0, lat0), (lon1, lat1) = view_tl, view_br

    def f(p):
        return ((p[0] - lon0) / (lon1 - lon0) * w, y_top + (lat0 - p[1]) / (lat0 - lat1) * (h - y_top))
    return f


def fit_mapper(pairs):
    """Least-squares affine lon/lat -> px from (lonlat, px) pairs (for captures where only vertex px are known)."""
    import numpy as np
    A, bx, by = [], [], []
    for (lon, lat), (X, Y) in pairs:
        A.append([lon, lat, 1.0])
        bx.append(X)
        by.append(Y)
    A = np.array(A)
    cx = np.linalg.lstsq(A, np.array(bx), rcond=None)[0]
    cy = np.linalg.lstsq(A, np.array(by), rcond=None)[0]
    err = max(abs(A @ cx - np.array(bx)).max(), abs(A @ cy - np.array(by)).max())

    def f(p):
        return (cx[0] * p[0] + cx[1] * p[1] + cx[2], cy[0] * p[0] + cy[1] * p[1] + cy[2])
    return f, err


def from_capture_json(path):
    raw = json.load(open(os.path.join(HERE, path)))
    pairs = []
    for k, d in raw["deeds"].items():
        scr = raw["capture"]["screen"][k]
        ring = d["ring"]
        assert len(scr) == len(ring), (k, len(scr), len(ring))
        pairs += list(zip(ring, scr))
    f, err = fit_mapper(pairs)
    print(f"  {raw['slug']}: lon/lat->px fit max error {err:.2f}px from {len(pairs)} points")
    return raw, f


def px_to_lonlat(view_tl, view_br, y_top=58, w=1200, h=796):
    (lon0, lat0), (lon1, lat1) = view_tl, view_br

    def f(X, Y):
        return (lon0 + X / w * (lon1 - lon0), lat0 - (Y - y_top) / (h - y_top) * (lat0 - lat1))
    return f


if __name__ == "__main__":
    results = {}

    # ---------- Salaya (LandsMaps, 1 deed) ----------
    raw, f = from_capture_json("salaya.json")
    results["salaya"] = build({
        "slug": "salaya", "source": "landsmaps", "area_deed": "10-2-16", "deeds": raw["deeds"],
        "landoffice": raw["landoffice"], "utm": "5036 I 3626-00",
        "roads": [{"name": "ถนนทางหลวงชนบท", "dirs": ["E", "SE", "NE"], "front": True}],
        "capture": {"file": raw["capture"]["file"], "crop": (190, 100, 1010, 660), "to_px": f},
        "sat_extra": [{"kind": "dist", "label": "ทางหลวง 4006", "value": 79,
                        "pts": [[100.27318463, 13.80407464], [100.27334597, 13.80477359]]}],
        "context": [{"kind": "road_far", "label": "ทางหลวง 4006", "value": 79, "from_side": "front_end"}],
    })

    # ---------- Phetchabun (LandsMaps, 3 deeds) ----------
    raw, f = from_capture_json("phetchabun.json")
    results["phetchabun"] = build({
        "slug": "phetchabun", "source": "landsmaps", "area_deed": "110-1-59", "deeds": raw["deeds"],
        "landoffice": raw["landoffice"], "utm": "5240 IV 2654-00",
        "roads": [{"name": "ทางหลวงหมายเลข 2275", "dirs": ["W", "SW", "NW"], "front": True},
                  {"name": "ถนนคอนกรีต", "dirs": ["N", "NE", "NW"]}],
        "capture": {"file": raw["capture"]["file"], "crop": (150, 110, 1060, 700), "to_px": f},
    })

    # ---------- Farm 1 (LandsMaps, 5 deeds) ----------
    raw, f = from_capture_json("farm1.json")
    results["farm1"] = build({
        "slug": "farm1", "source": "landsmaps", "area_deed": "8-2-21.2", "deeds": raw["deeds"],
        "landoffice": raw["landoffice"], "utm": "4937 III 5452-12",
        "roads": [],
        "capture": {"file": raw["capture"]["file"], "crop": (250, 120, 1000, 720), "to_px": f},
    })

    # ---------- Resort, Tha Muang (N.S.3 Kor: outline from the owner's map, registered to satellite) ----------
    tl, br = (99.58456606, 14.05048256), (99.59103394, 14.04650482)
    p2ll = px_to_lonlat(tl, br)
    resort_px = [[663.8, 243.0], [592.7, 606.1], [684.8, 613.9], [760.3, 360.4], [772.6, 256.0]]
    ring = [p2ll(*p) for p in resort_px]
    results["kanchanaburi"] = build({
        "slug": "kanchanaburi", "source": "approx", "area_deed": "9-0-36",
        "deeds": {"11101-11103": {"type": "น.ส. 3 ก.", "area": "9-0-36", "ring": ring}},
        "roads": [{"name": "ถนนคอนกรีต", "dirs": ["E", "SE", "NE"], "front": True},
                  {"name": "ถนนคอนกรีต", "dirs": ["N", "NW", "NE"]},
                  {"name": "ถนนคอนกรีต", "dirs": ["S", "SW", "SE"]}],
        "merge_deg": 20,
        "capture": {"file": "resort-sat-raw.jpg", "crop": (340, 150, 1060, 700), "to_px": screen_mapper(tl, br)},
    })

    # ---------- Farm 3 (N.S.3 Khor: outline registered from the owner's map; document sides as text) ----------
    tl, br = (99.5564364, 14.05248437), (99.5632636, 14.04828565)
    p2ll = px_to_lonlat(tl, br)
    farm3_px = [[590.2, 260.9], [531.8, 586.9], [911.6, 612.0], [949.3, 281.2]]
    ring = [p2ll(*p) for p in farm3_px]
    results["farm3"] = build({
        "slug": "farm3", "source": "approx", "area_deed": "31-2-50",
        "deeds": {"148": {"type": "น.ส. 3 ข.", "area": "31-2-50", "ring": ring}},
        "roads": [{"name": "ถนนหน้าฟาร์ม", "dirs": ["W", "SW", "NW"], "front": True}],
        "doc_sides": [["N", "5 เส้น", 200], ["S", "5 เส้น", 200], ["E", "6 เส้น 13 วา", 266], ["W", "6 เส้น", 240]],
        "capture": {"file": "farm3-sat-raw.jpg", "crop": (400, 170, 1100, 700), "to_px": screen_mapper(tl, br)},
    })

    for slug, d in results.items():
        s = d["stats"]
        print(f"\n== {slug} ({d['source']}) deed {d['area_deed']} = {d['area_deed_m2']:,.0f} m2 · polygon {s['area_poly_m2']:,.0f} m2 "
              f"({(s['area_poly_m2'] / d['area_deed_m2'] - 1) * 100:+.1f}%) · perimeter {s['perimeter']}")
        for sd in d["sides"]:
            print(f"   side {sd['k']} {sd['dir']:>2} len {sd['len']:8.1f} parts {sd['parts']} road {sd['road']} front {sd['front']}")
        print("   stats", {k: v for k, v in s.items() if k not in ('perimeter', 'area_poly_m2')})
        for dd in d["deeds"]:
            print(f"   deed {dd['no']} {dd['area']} poly {dd['area_m2_poly']:,.0f} m2")
        print("   sat", d["sat"]["img"], d["sat"]["w"], "x", d["sat"]["h"])
