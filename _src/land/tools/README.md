# Plot data (รูปแปลง)

`_src/land/<slug>.json` feeds the "ขนาดและรูปแปลง" section on each property page (rendered by `_src/landplan.py` during `python3 _src/build.py`).

How the data was made (17 Nov 2026):

- **Chanote deeds** (Salaya 25984, Phetchabun 22368–22370, Farm 1 15117/15118/8666/13053/13054): searched on LandsMaps
  (landsmaps.dol.go.th) and read each parcel polygon from its WMS layer `LANDSMAPS:V_PARCEL47` (GetFeatureInfo).
  `raw-<slug>.json` holds the polygons (WGS84 lon/lat) and their pixel positions in the satellite capture.
- **N.S.3 documents** (resort N.S.3 Kor 11101–11103, Farm 3 N.S.3 Khor 148) have no digital parcel, so the outline
  is the owner's own map (`images/<slug>/dim-01.jpg`) matched onto a georeferenced satellite capture with
  `register.py` (SIFT + RANSAC). Those numbers are shown as approximate (≈).
- `process.py` merges the deeds of a property, measures every side (WGS84 geodesic), finds the frontage/depth,
  crops the satellite image to `images/<slug>/plot-sat.jpg` and writes `_src/land/<slug>.json`.
  It needs `pyproj`, `shapely`, `Pillow` (and the raw capture images, which are not kept in the repo).
