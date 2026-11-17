"""Map the owner's hand-drawn red outline (on a Google satellite screenshot) onto a georeferenced capture.

usage: python3 register.py OWNER_IMG CAPTURE_IMG OUT_PREFIX
Writes OUT_PREFIX-match.jpg (visual check) and prints the outline vertices in capture pixel coordinates.
"""
import json
import sys

import cv2
import numpy as np

owner_p, cap_p, out = sys.argv[1:4]
own = cv2.imread(owner_p)
cap = cv2.imread(cap_p)

# --- red outline in the owner's image -------------------------------------------
hsv = cv2.cvtColor(own, cv2.COLOR_BGR2HSV)
m1 = cv2.inRange(hsv, (0, 150, 120), (8, 255, 255))
m2 = cv2.inRange(hsv, (170, 150, 120), (180, 255, 255))
red = cv2.morphologyEx(m1 | m2, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
cnts, _ = cv2.findContours(red, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
cnt = max(cnts, key=cv2.contourArea)
# the outline is a thick line: take the polygon traced by the line's centre
mask = np.zeros(red.shape, np.uint8)
cv2.drawContours(mask, [cnt], -1, 255, -1)
filled = mask.copy()
inner, _ = cv2.findContours(cv2.subtract(filled, red), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
inner = max(inner, key=cv2.contourArea)
outer = cnt
# centre line ≈ average of inner and outer boundary polygons (approximate each, then match vertices)
peri = cv2.arcLength(inner, True)
poly_in = cv2.approxPolyDP(inner, 0.012 * peri, True).reshape(-1, 2).astype(float)
peri_o = cv2.arcLength(outer, True)
poly_out = cv2.approxPolyDP(outer, 0.012 * peri_o, True).reshape(-1, 2).astype(float)
poly = []
for p in poly_in:
    d = np.linalg.norm(poly_out - p, axis=1)
    q = poly_out[d.argmin()]
    poly.append(((p + q) / 2).tolist())
poly = np.array(poly)

# --- feature matching owner -> capture (mask out the red line and text) -------------
own_mask = cv2.bitwise_not(cv2.dilate(red, np.ones((15, 15), np.uint8)))
sift = cv2.SIFT_create(6000)
g1 = cv2.cvtColor(own, cv2.COLOR_BGR2GRAY)
g2 = cv2.cvtColor(cap, cv2.COLOR_BGR2GRAY)
cap_mask = np.full(g2.shape, 255, np.uint8)
cap_mask[:60, :] = 0  # LandsMaps header bar
k1, d1 = sift.detectAndCompute(g1, own_mask)
k2, d2 = sift.detectAndCompute(g2, cap_mask)
bf = cv2.BFMatcher(cv2.NORM_L2)
raw = bf.knnMatch(d1, d2, k=2)
good = [m for m, n in raw if m.distance < 0.78 * n.distance]
src = np.float32([k1[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
dst = np.float32([k2[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)
H, inl = cv2.findHomography(src, dst, cv2.RANSAC, 4.0)
print("matches", len(good), "inliers", int(inl.sum()))
mapped = cv2.perspectiveTransform(poly.reshape(-1, 1, 2), H).reshape(-1, 2)

vis = cap.copy()
cv2.polylines(vis, [mapped.astype(np.int32)], True, (0, 220, 255), 2)
for i, (x, y) in enumerate(mapped):
    cv2.circle(vis, (int(x), int(y)), 4, (255, 255, 255), -1)
    cv2.putText(vis, str(i + 1), (int(x) + 6, int(y) - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
cv2.imwrite(out + "-match.jpg", vis)
json.dump({"owner_poly": poly.tolist(), "capture_poly": mapped.tolist(), "inliers": int(inl.sum())}, open(out + "-reg.json", "w"), indent=1)
print(json.dumps([[round(x, 1), round(y, 1)] for x, y in mapped]))
