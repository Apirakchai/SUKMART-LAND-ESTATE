"""Register a drone photo to the plot's satellite texture and map the plot outline onto the photo.

usage:
  python3 regphoto.py SLUG PHOTO OUT_PREFIX [--init x,y:u,v;x,y:u,v;...]   (photo px : texture px pairs)

Without --init the photo is matched straight to images/<slug>/plot-3d.jpg with SIFT + RANSAC (works for
near-vertical shots). With --init (>= 4 rough ground pairs, for oblique shots) the photo is first warped into the
texture frame with that rough homography, matched there, and the refinement is composed back.
Writes OUT_PREFIX-check.jpg (outline + matched points drawn on the photo) and OUT_PREFIX.json.
"""
import json
import os
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))


def sift_h(a, b, mask_a=None, mask_b=None, ratio=0.78, thr=5.0):
    sift = cv2.SIFT_create(9000, contrastThreshold=0.02)
    ga = cv2.cvtColor(a, cv2.COLOR_BGR2GRAY)
    gb = cv2.cvtColor(b, cv2.COLOR_BGR2GRAY)
    ga = cv2.createCLAHE(2.0, (8, 8)).apply(ga)
    gb = cv2.createCLAHE(2.0, (8, 8)).apply(gb)
    ka, da = sift.detectAndCompute(ga, mask_a)
    kb, db = sift.detectAndCompute(gb, mask_b)
    if da is None or db is None:
        return None, 0, []
    raw = cv2.BFMatcher(cv2.NORM_L2).knnMatch(da, db, k=2)
    good = [m for m, n in (p for p in raw if len(p) == 2) if m.distance < ratio * n.distance]
    if len(good) < 8:
        return None, len(good), []
    src = np.float32([ka[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
    dst = np.float32([kb[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)
    H, inl = cv2.findHomography(src, dst, cv2.RANSAC, thr, maxIters=20000, confidence=0.999)
    if H is None:
        return None, 0, []
    pts = [(src[i, 0], dst[i, 0]) for i in range(len(good)) if inl[i]]
    return H, int(inl.sum()), pts


def main():
    slug, photo_p, out = sys.argv[1:4]
    init = next((a.split("=", 1)[1] if "=" in a else sys.argv[sys.argv.index(a) + 1] for a in sys.argv if a.startswith("--init")), None)
    d = json.load(open(os.path.join(SITE, "_src", "land", f"{slug}.json")))
    tex = cv2.imread(os.path.join(SITE, d["tex3d"]["img"]))
    photo = cv2.imread(photo_p)
    outline = np.float32(d["tex3d"]["outline_px"]).reshape(-1, 1, 2)

    if init:
        pairs = [p.split(":") for p in init.split(";") if p.strip()]
        P = np.float32([[float(v) for v in a.split(",")] for a, _ in pairs])
        T = np.float32([[float(v) for v in b.split(",")] for _, b in pairs])
        H0, _ = cv2.findHomography(P, T, 0)
        warped = cv2.warpPerspective(photo, H0, (tex.shape[1], tex.shape[0]))
        wmask = cv2.warpPerspective(np.full(photo.shape[:2], 255, np.uint8), H0, (tex.shape[1], tex.shape[0]))
        wmask = cv2.erode(wmask, np.ones((9, 9), np.uint8))
        H1, n, pts = sift_h(warped, tex, wmask, None, ratio=0.8, thr=6.0)
        print("init-warp matches inliers:", n)
        if H1 is None or n < 12:
            H = H0
            pts = []
        else:
            H = H1 @ H0
            Hinv0 = np.linalg.inv(H0)
            pts = [(cv2.perspectiveTransform(np.float32([[a]]), Hinv0)[0, 0], b) for a, b in pts]
    else:
        H, n, pts = sift_h(photo, tex)
        print("direct matches inliers:", n)
        if H is None:
            sys.exit("no homography")

    Hinv = np.linalg.inv(H)
    mapped = cv2.perspectiveTransform(outline, Hinv).reshape(-1, 2)
    vis = photo.copy()
    for a, b in pts[:400]:
        cv2.circle(vis, (int(a[0]), int(a[1])), 3, (0, 255, 0), -1)
    cv2.polylines(vis, [mapped.astype(np.int32)], True, (40, 40, 40), 6)
    cv2.polylines(vis, [mapped.astype(np.int32)], True, (90, 210, 245), 3)
    for i, (x, y) in enumerate(mapped):
        cv2.putText(vis, str(i), (int(x) + 5, int(y) - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    cv2.imwrite(out + "-check.jpg", vis, [cv2.IMWRITE_JPEG_QUALITY, 85])
    json.dump({"photo": os.path.relpath(photo_p, SITE), "H_photo_to_tex": H.tolist(), "inliers": n,
               "outline_photo_px": [[round(float(x), 1), round(float(y), 1)] for x, y in mapped]},
              open(out + ".json", "w"), indent=1)
    print("ok", out)


if __name__ == "__main__":
    main()
