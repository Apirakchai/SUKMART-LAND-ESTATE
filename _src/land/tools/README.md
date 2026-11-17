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

Added 17 Nov 2026:

- **3D view** (`/assets/plot3d.js`, plain WebGL, loaded only when the 3D tab is in view): `make3d.py` keeps the clean
  band of each LandsMaps satellite capture as `images/<slug>/plot-3d.jpg` and stores `tex3d` (affine metres → texture
  px, outline px) in the JSON. `landplan.render_3d` passes the outline, front side and label anchors to the page.
- **Drone photo view** ("มุมสูง"): `make_aerial.py` maps the outline onto a top-down drone photo with a homography
  from hand-picked ground control points (plot corners / fence corners), turns the photo north-up and writes
  `images/<slug>/plot-aerial.jpg` + `aerial` in the JSON. Only Salaya has one: the other properties' drone photos
  already carry the owner's boundary lines, and Farm 1 has no top-down shot of the whole plot. `regphoto.py` is the
  automatic SIFT attempt (works for near-vertical shots only).
- **"ทำอะไรได้บ้าง" section** (`_src/landuse.py`): zoning picked from the DPT layer `PLLU_<province>` in LandsMaps
  (Salaya: ผังเมืองรวมชุมชนพุทธมณฑล 2566 zone ก.2-10; Phetchabun: provincial plan 2560 area 2.13; resort: Kanchanaburi
  provincial plan 2560 area 3.2; Farm 1: same plan, area 1.18 ชุมชน; Farm 3: no zone colour in the layer — left out).
  Rule lists are shown only where the plan text was read (Phetchabun, mr60-pb.pdf on asa.or.th).
- Translations for all of the above: `i18n_use.py`.
