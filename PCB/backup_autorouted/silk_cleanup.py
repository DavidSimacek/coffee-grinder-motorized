"""Silkscreen cleanup: block boxes as open polylines that dodge parts, refs auto-placed.
usage: python.exe silk.py in.kicad_pcb out.kicad_pcb
"""
import sys, math
import pcbnew

b = pcbnew.LoadBoard(sys.argv[1])
MM, TO = pcbnew.FromMM, pcbnew.ToMM
SILK = pcbnew.F_SilkS
ERR = MM(0.005)
LOC = pcbnew.ERROR_INSIDE

# ---------------- block boxes ----------------
DRAW = []
fps = list(b.GetFootprints())
for d in list(b.GetDrawings()):
    if d.GetLayer() == SILK and d.GetClass() == 'PCB_SHAPE' and d.GetShapeStr() in ('Polygon', 'Rect'):
        b.Delete(d)
    else:
        DRAW.append(d)


def poly(pts, w=0.15):
    for a, c in zip(pts, pts[1:]):
        s = pcbnew.PCB_SHAPE(b); s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetStart(pcbnew.VECTOR2I(MM(a[0]), MM(a[1]))); s.SetEnd(pcbnew.VECTOR2I(MM(c[0]), MM(c[1])))
        s.SetWidth(MM(w)); s.SetLayer(SILK); s.thisown = 0; b.Add(s); DRAW.append(s)


# 12V input / protection (J1's own outline closes it on the top/left)
poly([(50.2, 71.75), (50.2, 73.95), (61.3, 73.95), (61.3, 76.5), (64.6, 76.5), (64.6, 76.3),
      (74.0, 76.3), (74.0, 62.3), (65.3, 62.3)])
# 3.3V regulator
poly([(63.2, 76.5), (64.6, 76.5), (64.6, 76.3), (73.8, 76.3), (73.8, 87.15), (63.2, 87.15), (63.2, 76.5)])
# I-SENSE
poly([(66.2, 87.15), (75.45, 87.15), (75.45, 93.95), (78.5, 93.95), (78.5, 97.85), (66.2, 97.85), (66.2, 87.15)])
# MOTOR (left edge interrupted at C1 "+" mark and J2 pin-1 mark)
poly([(50.2, 80.35), (50.2, 73.95), (61.3, 73.95), (61.3, 76.5), (63.2, 76.5), (63.2, 87.15), (66.2, 87.15),
      (66.2, 97.85), (71.8, 97.85), (71.8, 101.85), (50.2, 101.85), (50.2, 94.15)])
poly([(50.2, 81.45), (50.2, 92.85)])
# PROG / UI
poly([(73.9, 84.4), (94.9, 84.4), (94.9, 83.25), (104.8, 83.25), (104.8, 101.85), (71.8, 101.85), (71.8, 97.85),
      (78.5, 97.85), (78.5, 93.95), (75.45, 93.95), (75.45, 87.15), (73.9, 87.15), (73.9, 84.4)])
# BLE MCU
poly([(74.0, 62.3), (104.7, 62.3), (104.7, 82.6), (74.0, 82.6), (74.0, 62.3)])

for d in DRAW:
    if d.GetClass() == 'PCB_TEXT' and d.GetText() == 'BLE MCU':
        d.SetTextSize(pcbnew.VECTOR2I(MM(1.0), MM(1.0))); d.SetTextThickness(MM(0.15))
        d.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_LEFT)
        d.SetPosition(pcbnew.VECTOR2I(MM(74.6), MM(83.55)))

# ---------------- obstacle map ----------------


def obstacles(skip_ref=None):
    s = pcbnew.SHAPE_POLY_SET()
    for d in DRAW:
        if d.GetLayer() == SILK:
            d.TransformShapeToPolygon(s, SILK, MM(0.1), ERR, LOC)
    for fp in fps:
        for g in fp.GraphicalItems():
            if g.GetLayer() == SILK:
                g.TransformShapeToPolygon(s, SILK, MM(0.1), ERR, LOC)
        for p in fp.Pads():
            if p.IsOnLayer(pcbnew.F_Mask):
                p.TransformShapeToPolygon(s, pcbnew.F_Mask, MM(0.12), ERR, LOC)
        if fp.GetReference() != skip_ref and fp.Reference().IsVisible() and placed.get(fp.GetReference()):
            fp.Reference().TransformTextToPolySet(s, MM(0.15), ERR, LOC)
    for v in b.GetTracks():
        if v.GetClass() == 'PCB_VIA':
            pass  # tented vias: silk over them is fine
    return s


inside = pcbnew.SHAPE_POLY_SET()
o = inside.NewOutline()
for x, y in ((50.35, 62.35), (104.65, 62.35), (104.65, 101.65), (50.35, 101.65)):
    inside.Append(MM(x), MM(y), o)


def rect_dist(px, py, bb):
    dx = max(TO(bb.GetLeft()) - px, 0, px - TO(bb.GetRight()))
    dy = max(TO(bb.GetTop()) - py, 0, py - TO(bb.GetBottom()))
    return math.hypot(dx, dy)


crt = {fp.GetReference(): (fp.GetCourtyard(pcbnew.F_CrtYd).BBox() if fp.GetCourtyard(pcbnew.F_CrtYd).OutlineCount()
                           else fp.GetBoundingBox(False)) for fp in fps}
placed = {}

H, TH = 0.8, 0.15


def try_place(fp):
    ref = fp.Reference()
    obs = obstacles(fp.GetReference())
    cb = crt[fp.GetReference()]
    L, T, R, B = TO(cb.GetLeft()), TO(cb.GetTop()), TO(cb.GetRight()), TO(cb.GetBottom())
    cx, cy = (L + R) / 2, (T + B) / 2
    n = len(fp.GetReference())
    tw = n * H * 0.85 + TH
    cands = []
    for gap in (0.25, 0.5, 0.8, 1.1, 1.5):
        for k in [0, -0.5, 0.5, -1, 1, -1.5, 1.5, -2, 2, -3, 3]:
            # above / below (horizontal)
            cands.append((cx + k, T - gap - H / 2, 0))
            cands.append((cx + k, B + gap + H / 2, 0))
            # left / right (vertical text, reads bottom-to-top)
            cands.append((L - gap - H / 2, cy + k, 90))
            cands.append((R + gap + H / 2, cy + k, 90))
            # left / right horizontal
            cands.append((L - gap - tw / 2, cy + k, 0))
            cands.append((R + gap + tw / 2, cy + k, 0))
    best = None
    for x, y, ang in cands:
        ref.SetTextSize(pcbnew.VECTOR2I(MM(H), MM(H))); ref.SetTextThickness(MM(TH))
        ref.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER); ref.SetVertJustify(pcbnew.GR_TEXT_V_ALIGN_CENTER)
        ref.SetTextAngle(pcbnew.EDA_ANGLE(ang, pcbnew.DEGREES_T))
        ref.SetPosition(pcbnew.VECTOR2I(MM(x), MM(y)))
        tp = pcbnew.SHAPE_POLY_SET(); ref.TransformTextToPolySet(tp, 0, ERR, LOC)
        # inside board
        t2 = pcbnew.SHAPE_POLY_SET(tp); t2.BooleanSubtract(inside)
        if not t2.IsEmpty():
            continue
        t3 = pcbnew.SHAPE_POLY_SET(tp); t3.BooleanIntersection(obs)
        if not t3.IsEmpty():
            continue
        own = rect_dist(x, y, cb)
        other = min(rect_dist(x, y, crt[f.GetReference()]) for f in fps if f is not fp and not f.GetReference().startswith('H'))
        score = own + (0 if own <= other + 0.05 else 3 + (own - other) * 2) + (0.15 if ang else 0)
        if best is None or score < best[0]:
            best = (score, x, y, ang)
    if best is None:
        return False
    _, x, y, ang = best
    ref.SetTextAngle(pcbnew.EDA_ANGLE(ang, pcbnew.DEGREES_T))
    ref.SetPosition(pcbnew.VECTOR2I(MM(x), MM(y)))
    placed[fp.GetReference()] = (round(x, 2), round(y, 2), ang, round(best[0], 2))
    return True


order = sorted(fps, key=lambda f: (crt[f.GetReference()].GetArea()))
failed = []
for fp in order:
    if not try_place(fp):
        failed.append(fp.GetReference())
for k, v in sorted(placed.items()):
    print(k, v)
print('FAILED', failed)
b.Save(sys.argv[2])

# ---------------- manual overrides for the densest spots ----------------
b2 = pcbnew.LoadBoard(sys.argv[2])
MAN = {  # ref: (x, y, angle)
    'C11': (70.0, 63.75, 90), 'C12': (70.0, 66.3, 90),
    'R8': (71.3, 67.65, 0), 'R9': (73.05, 67.65, 0),
    'TP4': (77.0, 97.25, 0), 'TP1': (80.0, 97.25, 0), 'TP2': (82.5, 97.25, 0), 'TP3': (85.0, 97.25, 0),
    'J1': (52.0, 72.75, 0), 'J3': (92.3, 88.3, 0),
    'D4': (97.45, 85.0, 90), 'R12': (97.45, 89.0, 90),
}
for fp in b2.GetFootprints():
    r = fp.Reference(); ref = fp.GetReference()
    r.SetTextSize(pcbnew.VECTOR2I(MM(H), MM(H))); r.SetTextThickness(MM(TH))
    if ref in ('H1', 'H2'):
        r.SetVisible(False)
    if ref in MAN:
        x, y, a = MAN[ref]
        r.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER); r.SetVertJustify(pcbnew.GR_TEXT_V_ALIGN_CENTER)
        r.SetTextAngle(pcbnew.EDA_ANGLE(a, pcbnew.DEGREES_T)); r.SetPosition(pcbnew.VECTOR2I(MM(x), MM(y)))
texts = [d for d in b2.GetDrawings() if d.GetClass() == 'PCB_TEXT']
ref_txt = [t for t in texts if t.GetText() == 'I-SENSE'][0]
for t in texts:
    if t.GetText() == '3.3V':
        t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_LEFT); t.SetPosition(pcbnew.VECTOR2I(MM(63.7), MM(86.2)))
if not any(t.GetText() == '12V IN' for t in texts):
    t = pcbnew.PCB_TEXT(b2); t.SetText('12V IN'); t.SetLayer(SILK)
    t.SetTextSize(ref_txt.GetTextSize()); t.SetTextThickness(ref_txt.GetTextThickness())
    t.SetPosition(pcbnew.VECTOR2I(MM(56.4), MM(72.75))); t.thisown = 0; b2.Add(t)
for t in texts:
    if t.GetText() in ('MOTOR', '3.3V', 'PROG / UI', 'BLE MCU'):
        t.SetTextSize(ref_txt.GetTextSize()); t.SetTextThickness(ref_txt.GetTextThickness())
    if t.GetText() == 'BLE MCU':
        t.SetVertJustify(pcbnew.GR_TEXT_V_ALIGN_CENTER); t.SetPosition(pcbnew.VECTOR2I(MM(74.6), MM(83.5)))
ref_txt.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER); ref_txt.SetVertJustify(pcbnew.GR_TEXT_V_ALIGN_CENTER)
ref_txt.SetPosition(pcbnew.VECTOR2I(MM(69.6), MM(88.0)))
b2.Save(sys.argv[2])
print('overrides applied')
