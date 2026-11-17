"""Build the ground texture + georeference for the 3D plot view.

For each plot we take the full LandsMaps satellite capture (1200x796 screen, header 58 px, credit line at
the bottom), keep the clean band y 58..780 as images/<slug>/plot-3d.jpg, and store in _src/land/<slug>.json:

  tex3d = {img, w, h,
           A:  affine metres(x east, y north) -> texture px (u right, v down) as [a, b, c, d, e, f]
               u = a*x + b*y + c ; v = d*x + e*y + f
           outline_px: plot outline in texture px}

The affine is fitted (least squares) on the outline: metres from the JSON vs the satellite-crop pixels,
shifted by the crop offset. Usage:  python3 make3d.py /path/to/raw/captures
"""
import json
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
LAND = os.path.dirname(HERE)
SITE = os.path.dirname(os.path.dirname(LAND))

CAPS = {  # slug: (raw capture file, crop offset used for plot-sat.jpg)
    "salaya": ("salaya-sat-raw.jpg", (190, 100)),
    "phetchabun": ("phetchabun-sat-raw.jpg", (150, 110)),
    "farm1": ("farm1-sat-raw.jpg", (250, 120)),
    "kanchanaburi": ("resort-sat-raw.jpg", (340, 150)),
    "farm3": ("farm3-sat-raw.jpg", (400, 170)),
}
Y0, Y1 = 58, 780  # below the LandsMaps header, above the map credit line


def fit_affine(src, dst):
    src = np.asarray(src, float)
    dst = np.asarray(dst, float)
    X = np.c_[src, np.ones(len(src))]
    cu, *_ = np.linalg.lstsq(X, dst[:, 0], rcond=None)
    cv, *_ = np.linalg.lstsq(X, dst[:, 1], rcond=None)
    pred = X @ np.c_[cu, cv]
    err = np.hypot(*(pred - dst).T)
    return [*cu, *cv], float(err.max())


def main(raw_dir):
    for slug, (fn, (x0, y0)) in CAPS.items():
        path = os.path.join(LAND, f"{slug}.json")
        d = json.load(open(path))
        im = Image.open(os.path.join(raw_dir, fn)).convert("RGB")
        tex = im.crop((0, Y0, im.width, Y1))
        rel = f"images/{slug}/plot-3d.jpg"
        tex.save(os.path.join(SITE, rel), quality=84, optimize=True, progressive=True, subsampling=0)
        px = [[x + x0, y + y0 - Y0] for x, y in d["sat"]["outline"]]
        A, err = fit_affine(d["outline"], px)
        d["tex3d"] = {"img": rel, "w": tex.width, "h": tex.height, "A": [round(v, 6) for v in A],
                      "outline_px": [[round(x, 1), round(y, 1)] for x, y in px]}
        extra = []
        for e in d["sat"].get("extra", []):
            extra.append([[round(x + x0, 1), round(y + y0 - Y0, 1)] for x, y in e["px"]])
        d["tex3d"]["extra_px"] = extra
        json.dump(d, open(path, "w"), ensure_ascii=False, indent=1)
        kb = os.path.getsize(os.path.join(SITE, rel)) // 1024
        print(f"{slug:13s} tex {tex.width}x{tex.height} {kb} KB  affine max err {err:.2f} px")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ".")
