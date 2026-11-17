"""Put the plot outline on a top-down drone photo (the "มุมสูง" view).

The photo is matched to the satellite texture (images/<slug>/plot-3d.jpg) with ground control points picked by
hand at clear features (fence corners, plot corners): a homography texture px -> photo px. The photo is turned so
north is up and saved as images/<slug>/plot-aerial.jpg; the outline in that frame goes into <slug>.json["aerial"].

Run from anywhere:  python3 make_aerial.py
"""
import json
import os

import cv2
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
LAND = os.path.dirname(HERE)
SITE = os.path.dirname(os.path.dirname(LAND))

JOBS = {
    # slug: photo, rotation to bring north up (PIL degrees, counter-clockwise), {outline vertex: photo px}
    "salaya": ("images/salaya/loc-01.jpg", -90, {6: (8, 44), 7: (330, 58), 4: (14, 695), 8: (348, 640)}),
}


def main():
    for slug, (photo, rot, gcp) in JOBS.items():
        path = os.path.join(LAND, f"{slug}.json")
        d = json.load(open(path))
        tex = np.float32(d["tex3d"]["outline_px"])
        H, _ = cv2.findHomography(np.float32([tex[k] for k in gcp]), np.float32([gcp[k] for k in gcp]), 0)
        pts = cv2.perspectiveTransform(tex.reshape(-1, 1, 2), H).reshape(-1, 2)
        im = Image.open(os.path.join(SITE, photo)).convert("RGB")
        W0, H0 = im.size
        out = im.rotate(rot, expand=True, resample=Image.BICUBIC)
        if rot == -90:      # clockwise: (x, y) -> (H0 - y, x)
            pts = [(H0 - y, x) for x, y in pts]
        elif rot == 90:     # counter-clockwise: (x, y) -> (y, W0 - x)
            pts = [(y, W0 - x) for x, y in pts]
        elif rot == 180:
            pts = [(W0 - x, H0 - y) for x, y in pts]
        rel = f"images/{slug}/plot-aerial.jpg"
        out.save(os.path.join(SITE, rel), quality=86, optimize=True, progressive=True, subsampling=0)
        d["aerial"] = {"img": rel, "w": out.width, "h": out.height, "src": photo,
                       "outline": [[round(float(x), 1), round(float(y), 1)] for x, y in pts]}
        json.dump(d, open(path, "w"), ensure_ascii=False, indent=1)
        print(slug, out.size, "outline", d["aerial"]["outline"][:3], "...")


if __name__ == "__main__":
    main()
