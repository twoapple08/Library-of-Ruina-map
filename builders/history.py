"""역사의 층 (말쿠트) — 자유 형체 판 (2026-10-15).

reference/역사의 층 전경.png: 남쪽 높은 전망대(도착)에서 북쪽을 내려다본 구도 — 헤링본 나무 바닥 위로 동서로 긴 검은
난간 줄(8칸 간격)과 엇갈린 유리 진열장(5칸 간격), 바닥의 빛 띠, 멀리 안개 속 금빛 책장 기둥 사이로 거대 유물 셋
(불 켜진 창의 나무 장 · 톱니와 쇠사슬 감긴 돌기둥 · 이끼 덮인 돌덩이). 나무위키: 바닥이 엘리베이터 양면 거울처럼
여러 겹 아래로 반복 → 무대 가장자리 아래 바닥 겹 + 책장 절벽.
지정사서 방: builders/history_room.py.
"""
from __future__ import annotations

import math

import numpy as np

from builders import detail as D
from tools import artfit as A
from tools import form_textures as T
from tools import forms as F

Y0 = 64
ART = "reference/역사의 층 전경.png"
CAM = F.Camera((0.5, Y0 + 14.5, 100.0), 180.0, 43.5)     # 전망대 (원화: 난간 줄 간격·원근에 맞춤)
BALC = Y0 + 13                                            # 전망대 바닥
ARRIVE = (0.5, BALC, 100.0, 180.0, 43.5)
HX, HZ = 250, 124            # 무대 반폭·반깊이 (x -250..250, z -124..124)
RAIL_DZ, CASE_DX = 8, 5
LAYER_DY, LAYERS, LAYER_GROW = 24, 4, 16
RELIC_Z = -160               # 유물 깊이
UP = np.array([0, 1.0, 0])
SPACE = "history"


def mats():
    m = {}
    m["art"] = F.mat("hist_art", T.art("art/history", ART), emissive=True, flat=True, ao=False)
    m["floor"] = F.mat("hist_floor", T.herringbone("hist_floor", (64, 38, 22), (150, 98, 58)), emissive=True,
                       flat=True, ao=False)
    m["rail"] = F.mat("hist_rail", T.metal("hist_rail", (14, 12, 14), (52, 46, 46), seed=61), emissive=True, flat=True,
                      ao=False)
    m["rail_top"] = F.mat("hist_rail_top", T.metal("hist_rail_top", (120, 104, 84), (230, 210, 170), seed=62),
                          emissive=True, flat=True, ao=False)
    m["strip"] = F.mat("hist_strip", T.glow("hist_strip", (255, 214, 150)), emissive=True, flat=True, ao=False, glow=3)
    m["case_base"] = F.mat("hist_case_base", T.metal("hist_case_base", (10, 10, 12), (40, 36, 36), seed=63),
                           emissive=True, flat=True, ao=False)
    m["glass"] = F.mat("hist_glass", T.glow("hist_glass", (220, 230, 235)), layer="translucent", emissive=True,
                       flat=True, ao=False)
    m["book"] = F.mat("hist_book", T.flat("hist_book", (120, 60, 36)), emissive=True, flat=True, ao=False)
    warm = [(120, 70, 40), (96, 52, 32), (150, 110, 70), (80, 56, 38), (170, 130, 86)]
    m["shelf"] = [F.mat(f"hist_shelf{i}", T.shelf(f"hist_shelf{i}", warm, wood=(90, 58, 34), seed=60 + i,
                                                   dark_back=(30, 18, 10)), emissive=True, flat=True, ao=False)
                  for i in range(3)]
    m["wood"] = F.mat("hist_wood", T.wood("hist_wood", (50, 30, 18), (120, 80, 48), seed=64), emissive=True, flat=True,
                      ao=False)
    m["plank"] = [F.mat(f"hist_plank{i}", T.board(f"hist_plank{i}", c0, c1, w=16, h=32, seed=65 + i), emissive=True,
                        flat=True, ao=False)
                  for i, (c0, c1) in enumerate([((60, 40, 26), (130, 92, 58)), ((46, 32, 22), (104, 74, 48)),
                                                ((80, 58, 36), (156, 116, 72))])]
    m["fire"] = F.mat("hist_fire", T.glow("hist_fire", (255, 196, 110)), emissive=True, flat=True, ao=False, glow=3)
    m["sand"] = F.mat("hist_sand", T.stone_slab("hist_sand", (150, 104, 70), (210, 160, 112), seed=66), emissive=True,
                      flat=True, ao=False)
    m["copper"] = F.mat("hist_copper", T.metal("hist_copper", (110, 60, 30), (210, 140, 80), seed=67), emissive=True,
                        flat=True, ao=False)
    m["chain"] = F.mat("hist_chain", T.metal("hist_chain", (30, 26, 24), (90, 80, 70), seed=68), emissive=True,
                       flat=True, ao=False)
    m["moss"] = F.mat("hist_moss", T.bark("hist_moss", (40, 56, 26), (104, 120, 54), seed=69), emissive=True, flat=True,
                      ao=False)
    m["fog"] = F.mat("hist_fog", T.glow("hist_fog", (255, 226, 170)), layer="translucent", emissive=True, flat=True,
                     ao=False)
    return m


def warm_light(q, extra=()):
    """원화의 빛: 위쪽 멀리(북쪽 안개)에서 오는 금빛 + 바닥의 비스듬한 빛 띠."""
    lights = [((0, 160, -320), (1.0, 0.78, 0.5), 520.0)] + list(extra)
    return F.bake_points(q, lights, ambient=(0.38, 0.28, 0.2))


# ---------------------------------------------------------------- 무대

def floor_band(m, x0, z0, x1, z1, y):
    q = F.plane((x0, y, z1), (x1 - x0, 0, 0), (0, 0, z0 - z1), m["floor"], tile=(2.0, 2.0))
    # 원화의 비스듬한 빛 띠 (밝은 줄, 어두운 줄)
    def fn(P, N):
        t = np.sin((P[:, 0] * 0.55 + P[:, 2]) * 0.16) * 0.5 + 0.5
        return 0.72 + 0.45 * t[:, None] ** 2
    return q.color_by(fn)


def rail(m, x0, x1, z, y):
    """난간: 검은 몸통 + 둥근 금속 윗봉 + 앞(남쪽) 바닥 빛줄."""
    out = [F.box((x0, y, z - 0.3), (x1, y + 0.9, z + 0.3), m["rail"], tile=2.0)]
    bar = np.array([[x0, y + 1.05, z], [x1, y + 1.05, z]])
    out.append(F.sweep(bar, 0.2, m["rail_top"], sides=8, step=4.0, tile_along=4.0))
    out.append(F.plane((x0, y + 0.02, z + 0.9), (x1 - x0, 0, 0), (0, 0, -0.35), m["strip"], tile=(4, 1)).flipped())
    return F.concat(out)


def case(m, x, z, y, detailed=True):
    """실물 유리 진열장: 받침·상판·유리 4면·금속 테·펼친 책."""
    if not detailed:
        # 원거리 진열장: 외곽 실루엣만 유지해 불필요한 면과 투명 중첩을 절감.
        return F.concat([
            F.box((x-.48,y,z-.38),(x+.48,y+.7,z+.38),m["case_base"]),
            F.box((x-.43,y+.7,z-.34),(x+.43,y+1.72,z+.34),m["glass"],faces="zZ").tint((1,1,1),.22),
            F.box((x-.46,y+1.72,z-.36),(x+.46,y+1.78,z+.36),m["case_base"])
        ])
    out = [D.beveled_box((x-.48,y,z-.38),(x+.48,y+.7,z+.38),m["case_base"],.035)]
    out.append(D.beveled_box((x-.46,y+1.72,z-.36),(x+.46,y+1.78,z+.36),m["case_base"],.02))
    # 유리도 실제 두께를 가지며, 양면 렌더링으로 측면에서도 보인다.
    for lo,hi in (
        ((x-.43,y+.72,z-.35),(x+.43,y+1.72,z-.325)),
        ((x-.43,y+.72,z+.325),(x+.43,y+1.72,z+.35)),
        ((x-.43,y+.72,z-.325),(x-.405,y+1.72,z+.325)),
        ((x+.405,y+.72,z-.325),(x+.43,y+1.72,z+.325)),
    ):
        out.append(F.two_sided(F.box(lo,hi,m["glass"])).tint((1,1,1),.28))
    for xx in (x-.45,x+.42):
        for zz in (z-.37,z+.34):
            out.append(D.beveled_box((xx,y+.69,zz),(xx+.03,y+1.77,zz+.03),m["rail_top"],.005))
    # 펼쳐진 책의 두 장: 종이 속지와 표지에 별도 두께.
    for side in (-1,1):
        cx=x+side*.135
        leaf=D.flat_book(.25,.34,.055,m["book"],m["sand"])
        out.append(leaf.rotate("z",side*13).translate((cx,y+.83,z)))
    out.append(D.beveled_box((x-.025,y+.8,z-.2),(x+.025,y+.9,z+.2),m["book"],.008))
    return F.concat(out)


def stage(m, rng, x0=-HX, x1=HX, z0=-HZ, z1=HZ, y=Y0, near=None):
    out = [floor_band(m, x0, z0, x1, z1, y)]
    for zr in range(z0 + RAIL_DZ // 2, z1, RAIL_DZ):
        out.append(rail(m, x0, x1, zr, y))
        off = rng.uniform(0, CASE_DX)
        xs = np.arange(x0 + off, x1, CASE_DX)
        for i, x in enumerate(xs):
            if near is not None and not near(x, zr):
                continue
            out.append(case(m, x, zr + (1.2 if i % 2 == 0 else -1.2), y, detailed=(abs(x) < 36 and zr > 30)))
    return out


def lower_layers(m, rng):
    """아래로 반복되는 바닥 겹 (위 겹보다 LAYER_GROW 넓은 테두리) + 그 사이 책장 절벽. 먼 곳이라 면을 굵게."""
    out = []
    for k in range(1, LAYERS + 1):
        y = Y0 - LAYER_DY * k
        hx, hz = HX + LAYER_GROW * k, HZ + LAYER_GROW * k
        ix, iz = HX + LAYER_GROW * (k - 1), HZ + LAYER_GROW * (k - 1)
        for (a0, b0, a1, b1) in ((-hx, -hz, hx, -iz), (-hx, iz, hx, hz), (-hx, -iz, -ix, iz), (ix, -iz, hx, iz)):
            out.append(floor_band(m, a0, b0, a1, b1, y))
            for zr in range(int(b0) + 4, int(b1), RAIL_DZ):
                out.append(rail(m, a0, a1, zr, y))
        # 위 겹 가장자리 아래 책장 절벽
        yt = Y0 - LAYER_DY * (k - 1)
        for (p, q) in (((-ix, -iz), (ix, -iz)), ((ix, iz), (-ix, iz)), ((-ix, iz), (-ix, -iz)), ((ix, -iz), (ix, iz))):
            p, q = np.array([p[0], 0, p[1]], float), np.array([q[0], 0, q[1]], float)
            out.append(F.plane(p + UP * y, q - p, UP * (yt - y), m["shelf"][k % 3], tile=(2.0, 2.0)))
    return out


# ---------------------------------------------------------------- 배경: 금빛 책장 기둥·유물

def tower(m, x0, z0, x1, z1, y0, y1, k=0):
    out = []
    for (ax, az), (bx, bz) in (((x0, z1), (x1, z1)), ((x1, z1), (x1, z0)), ((x1, z0), (x0, z0)), ((x0, z0), (x0, z1))):
        out.append(F.plane((ax, y0, az), (bx - ax, 0, bz - az), (0, y1 - y0, 0), m["shelf"][k % 3], tile=(3.0, 3.0)))
    out.append(F.plane((x0, y1, z1), (x1 - x0, 0, 0), (0, 0, z0 - z1), m["wood"], tile=(4, 4)))
    return F.concat(out)


def towers(m, rng):
    out = []
    x = -470
    while x < 470:
        w = rng.uniform(26, 46)
        dz = rng.uniform(18, 30)
        z1 = rng.uniform(-330, -290)
        out.append(tower(m, x, z1 - dz, x + w, z1, Y0 - 140, Y0 + rng.uniform(150, 250), int(x)))
        x += w + rng.uniform(8, 20)
    for side in (-1, 1):
        for z in range(-260, 200, 90):
            w, dz = rng.uniform(20, 34), rng.uniform(20, 34)
            x0 = side * rng.uniform(330, 370)
            out.append(tower(m, min(x0, x0 + side * w), z, max(x0, x0 + side * w), z + dz, Y0 - 140,
                             Y0 + rng.uniform(120, 220), int(z)))
    # 기둥 밑동의 빛 안개 (원화: 기둥 사이·아래가 금빛으로 번짐)
    for y in (Y0 - 30, Y0 - 10, Y0 + 15):
        out.append(F.plane((-520, y, -360), (1040, 0, 0), (0, 0, 120), m["fog"], tile=(40, 40)).tint((1, 1, 1), 0.18)
                   .flipped())
    return out


def _relic_box(view, x0p, x1p, row, z):
    """원화 상자 (픽셀 x0..x1, 가운데 줄 row) → 깊이 z 의 월드 x 범위."""
    a, b = view.at_z(np.array([x0p, x1p]), np.array([row, row]), z)
    return a[0], b[0]


def cabinet(m, view, rng):
    """왼쪽 유물: 판자를 덧댄 거대한 나무 장 + 불 켜진 창 + 작은 불꽃 셋."""
    xa, xb = _relic_box(view, 95, 255, 60, RELIC_Z)
    zc, d = RELIC_Z - 18, 36
    y0, y1 = Y0 - 120, Y0 + 120
    out = []
    pw = 6.0
    for (ax, az), (bx, bz) in (((xa, zc + d / 2), (xb, zc + d / 2)), ((xb, zc + d / 2), (xb, zc - d / 2)),
                               ((xb, zc - d / 2), (xa, zc - d / 2)), ((xa, zc - d / 2), (xa, zc + d / 2))):
        L = math.hypot(bx - ax, bz - az)
        n = max(1, int(L / pw))
        for i in range(n):
            t0, t1 = i / n, (i + 1) / n
            for yb in np.arange(y0, y1, 10.0):
                off = rng.uniform(0, 0.8)
                p = np.array([ax + (bx - ax) * t0, yb, az + (bz - az) * t0])
                du = np.array([(bx - ax) * (t1 - t0), 0, (bz - az) * (t1 - t0)])
                nrm = np.cross(du, UP)
                nrm = nrm / np.linalg.norm(nrm)
                # 판자에 실제 두께를 주고 벽에서 약간씩 돌출시킨다.
                # 접선 축을 따라 사각 기둥을 만든 뒤 벽면 방향으로 회전.
                length = float(np.linalg.norm(du))
                angle = math.degrees(math.atan2(du[2], du[0]))
                plank = D.beveled_box((0, 0, -0.18), (length, 10.2, 0.18),
                                     m["plank"][int(rng.integers(3))], .045)
                out.append(plank.rotate("y", -angle).translate(p + nrm * off))
    out.append(F.plane((xa, y1, zc + d / 2), (xb - xa, 0, 0), (0, 0, -d), m["wood"], tile=(8, 8)))
    # 불 켜진 창 (남쪽 면, 원화 x 165~235, 줄 25~115)
    wa, wb = _relic_box(view, 165, 235, 70, zc + d / 2)
    ya = view.at_z(np.array([200.0]), np.array([115.0]), zc + d / 2)[0][1]
    yb = view.at_z(np.array([200.0]), np.array([25.0]), zc + d / 2)[0][1]
    zf = zc + d / 2 + 1.2
    out.append(F.box((wa - 1.5, ya - 1.5, zf - 1.0), (wb + 1.5, yb + 1.5, zf), m["wood"], faces="xXyYZ"))
    out.append(F.plane((wa, ya, zf + 0.05), (wb - wa, 0, 0), (0, yb - ya, 0), m["fire"], tile=(4, 4)))
    return F.concat(out), (0.5 * (wa + wb), 0.5 * (ya + yb), zf + 6)


def stone_pillar(m, view, rng):
    """가운데 유물: 꼭대기가 기울어진 돌기둥 + 옆 큰 톱니 + 비스듬히 감긴 쇠사슬."""
    xa, xb = _relic_box(view, 440, 570, 60, RELIC_Z)
    cx, r = (xa + xb) / 2, (xb - xa) / 2
    cz = RELIC_Z - r
    y0, y1 = Y0 - 120, Y0 + 150
    out = [F.box((cx - r, y0, cz - r), (cx + r, y1, cz + r), m["sand"], tile=4.0, faces="xXzZ")]
    top = F.plane((cx - r, y1, cz + r), (2 * r, 0, 0), (0, 0, -2 * r), m["sand"], tile=(4, 4))
    out.append(top.rotate("z", -18, origin=(cx, y1, cz)))
    # 톱니 (남쪽 면 서쪽 위)
    gx, gy, gz, R = cx - r * 0.6, y1 - 30, cz + r + 1.5, r * 0.75
    teeth = 16
    prof = []
    for k in range(teeth * 4 + 1):
        a = k / (teeth * 4) * 2 * math.pi
        rr = R * (1.12 if (k % 4) in (1, 2) else 1.0)
        prof.append((gx + rr * math.cos(a), gy + rr * math.sin(a)))
    p = np.array(prof)
    ring = np.c_[p[:, 0], p[:, 1], np.full(len(p), gz)]
    out.append(F.sweep(ring, 1.4, m["copper"], sides=6, step=1.5, tile_along=4))
    for k in range(6):
        a = k * math.pi / 3
        spoke = np.array([[gx, gy, gz], [gx + R * math.cos(a), gy + R * math.sin(a), gz]])
        out.append(F.sweep(spoke, 0.8, m["copper"], sides=6, step=2.0))
    # 쇠사슬 두 줄: 기둥을 비스듬히 감는 고리
    for ystart, turn in ((y1 - 25, -1), (y1 - 70, 1)):
        n = 46
        for i in range(n):
            t = i / n
            a = turn * (0.4 + 2.2 * t * math.pi)
            c = np.array([cx + (r + 2.5) * math.cos(a), ystart - 70 * t, cz + (r + 2.5) * math.sin(a)])
            tang = np.array([-math.sin(a) * turn, -0.35, math.cos(a) * turn])
            tang /= np.linalg.norm(tang)
            side = np.cross(tang, UP) if i % 2 == 0 else UP
            side = side / np.linalg.norm(side)
            tt = np.linspace(0, 2 * math.pi, 13)
            link = c + 2.6 * np.cos(tt)[:, None] * tang + 1.4 * np.sin(tt)[:, None] * side
            out.append(F.sweep(link, 0.45, m["chain"], sides=5, step=0.8))
    return F.concat(out)


def moss_monolith(m, view, rng):
    """오른쪽 유물: 이끼 덮인 둥근 초록 돌덩이 + 표면의 작은 불빛."""
    xa, xb = _relic_box(view, 770, 965, 60, RELIC_Z)
    cx, rx = (xa + xb) / 2, (xb - xa) / 2
    cz = RELIC_Z - rx * 0.7
    y0, y1 = Y0 - 120, Y0 + 140
    prof = [(rx * 0.92, y0), (rx * 1.0, y0 + 80), (rx * 0.98, y1 - 60), (rx * 0.8, y1 - 15), (rx * 0.4, y1), (0.1, y1 + 3)]
    q = F.revolve(prof, m["moss"], segs=48, center=(cx, 0, cz), tiles_around=16, tile_up=12.0)
    q.P[..., 2] = cz + (q.P[..., 2] - cz) * 0.7
    # 울퉁불퉁
    n = np.sin(q.P[..., 1] * 0.13) * np.cos(np.arctan2(q.P[..., 2] - cz, q.P[..., 0] - cx) * 5)
    d = q.P - np.array([cx, 0, cz])
    d[..., 1] = 0
    q.P += d / np.maximum(np.linalg.norm(d, axis=-1, keepdims=True), 1e-6) * n[..., None] * 1.5
    out = [q]
    for _ in range(40):
        a = rng.uniform(math.pi * 0.15, math.pi * 0.85)
        y = rng.uniform(Y0 - 40, y1 - 20)
        p = np.array([cx + rx * 1.02 * math.cos(a), y, cz + rx * 0.72 * math.sin(a)])
        out.append(F.plane(p, (0.9, 0, 0), (0, 1.2, 0), m["fire"]))
    return F.concat(out)


# ---------------------------------------------------------------- 전망대 (도착)

def balcony(m):
    """도착 자리: 무대 위 공중의 유리 발판 (원화를 가리지 않게 거의 투명, 테만 금빛) + 동쪽으로 내려가는 유리 계단.
    나무위키 '엘리베이터 양면 거울' → 유리 승강대 느낌."""
    out = []
    x0, x1, z0, z1 = -2.0, 3.0, 98.0, 103.0
    glass = F.two_sided(F.plane((x0, BALC, z1), (x1 - x0, 0, 0), (0, 0, z0 - z1), m["glass"], tile=(1, 1)))
    out.append(glass.tint((1, 1, 1), 0.12))
    for (a, b) in (((x0, z0), (x1, z0)), ((x1, z0), (x1, z1)), ((x1, z1), (x0, z1)), ((x0, z1), (x0, z0))):
        seg = np.array([[a[0], BALC, a[1]], [b[0], BALC, b[1]]])
        out.append(F.sweep(seg, 0.06, m["rail_top"], sides=4, step=2.0))
    n = int((BALC - Y0) * 2)
    for k in range(n):
        za = z1 - 0.7 * k
        y = BALC - 0.5 * (k + 1)
        step = F.two_sided(F.plane((x1 + 0.2, y, za), (2.5, 0, 0), (0, 0, -0.7), m["glass"], tile=(1, 1)))
        out.append(step.tint((1, 1, 1), 0.15))
        out.append(F.sweep(np.array([[x1 + 0.2, y, za], [x1 + 2.7, y, za]]), 0.04, m["rail_top"], sides=4, step=2.0))
    return F.concat(out)


def build(b):
    from . import fragment as Fr
    from . import history_room
    d = b.dim("history")
    lay = b.form("history")
    rng = np.random.default_rng(701)
    m = mats()
    view = A.ArtView(CAM, 1000, 562)
    near_art = lambda x, z: True  # 모든 열의 실루엣은 유지하고 case()에서 LOD 적용
    st = stage(m, rng, near=near_art)
    low = lower_layers(m, rng)
    tw = towers(m, rng)
    cab, fire = cabinet(m, view, rng)
    relics = [cab, stone_pillar(m, view, rng), moss_monolith(m, view, rng)]
    bal = balcony(m)
    lay.add(bal)                              # 유리 발판은 원화 투영 안 함
    extra = [(fire, (1.4, 0.8, 0.35), 90.0)]
    near = [warm_light(q, extra) for q in st]
    far = [warm_light(q, extra) for q in low + tw + relics]
    for q in near + far:                       # 빛나는 재질은 굽지 않은 제 색
        sel = np.isin(q.M, [m["strip"], m["fire"], m["glass"], m["fog"]])
        q.C[sel, :, :3] = 1.0
    near_s = [F.subdivide(q, 1.0) for q in near]
    far_s = [F.subdivide(q, 4.0) for q in far]
    proj = F.project_scene(near_s + far_s, CAM, m["art"], min_facing=0.15, zres=(1000, 562), min_seen=3)
    for i, q in enumerate(proj):
        lay.add(q, max_edge=2.0 if i < len(near_s) else 6.0)
    sky(lay)
    collision(d)
    lay.emitter(F.Emitter((-40, Y0 + 1, 40, 40, Y0 + 12, 100), rate=3.0, sprites=("ruina:block/form/paper_gold",),
                          wind=(0.1, 0.2, -0.1), size=0.1, life=10.0, spin=0.1, color=(1.0, 0.8, 0.45), glow=True))
    room = history_room.build(b, d)
    Fr.stage(b, d, "gold", "역사의 층", ARRIVE, room,
             room_box=f"x={history_room.OX - 200},y=-64,z=-1024,dx=400,dy=1024,dz=2048")
    b.extra_checks += [
        {"what": "말쿠트 방 바이옴", "cmd": f"execute in {d.dim} if biome {history_room.OX} {Y0} 0 ruina:history_room",
         "expect": True},
    ]


def sky(lay):
    """하늘: 원화 위쪽(안개 속 금빛)을 이어 붙인 그린 하늘."""
    from PIL import Image
    clean = Image.open(A.ROOT + "/" + ART).convert("RGB")
    grad = [(-90, (40, 26, 16)), (-30, (120, 84, 50)), (-8, (220, 176, 110)), (0, (250, 220, 160)),
            (20, (200, 150, 90)), (60, (90, 60, 36)), (90, (40, 26, 18))]
    pano = A.sky_panorama(CAM, clean, 2048, 1024, e_lo=-60, e_hi=90, gradient=grad, feather=0.2,
                          cloud_e=(-6.0, 6.0), below=(60, 40, 24), zenith=(40, 26, 18))
    names = T.panorama("sky_hist", pano, 512)
    mats_ = [[F.mat(f"sky_hist_{r}_{c}", nm, emissive=True, flat=True, ao=False) for c, nm in enumerate(row)]
             for r, row in enumerate(names)]
    below = F.mat("sky_hist_below", T.flat("sky_hist_below", (60, 40, 24)), emissive=True, flat=True, ao=False)
    lay.sky(A.sky_dome(mats_, e_lo=-60, e_hi=90, yaw=CAM.yaw, below_mat=below))


def collision(d):
    """걷는 곳: 무대 바닥(barrier 한 겹), 난간(barrier 높이 1), 진열장은 지나갈 수 있게 비움, 전망대·계단."""
    d.fill(-HX, Y0 - 1, -HZ, HX, Y0 - 1, HZ, "minecraft:barrier")
    for zr in range(-HZ + RAIL_DZ // 2, HZ, RAIL_DZ):
        d.fill(-HX, Y0, zr, HX, Y0, zr, "minecraft:barrier")
    # 아래 겹 바닥 테두리
    for k in range(1, LAYERS + 1):
        y = Y0 - LAYER_DY * k - 1
        hx, hz = HX + LAYER_GROW * k, HZ + LAYER_GROW * k
        ix, iz = HX + LAYER_GROW * (k - 1), HZ + LAYER_GROW * (k - 1)
        for (a0, b0, a1, b1) in ((-hx, -hz, hx, -iz), (-hx, iz, hx, hz), (-hx, -iz, -ix, iz), (ix, -iz, hx, iz)):
            d.fill(a0, y, b0, a1, y, b1, "minecraft:barrier")
    # 유리 발판 (도착) + 동쪽 유리 계단 (반 칸씩)
    d.fill(-2, BALC - 1, 98, 2, BALC - 1, 102, "minecraft:barrier")
    n = int((BALC - Y0) * 2)
    for k in range(n):
        z = int(math.floor(103 - 0.7 * (k + 0.5)))
        h = BALC - 0.5 * (k + 1)
        full = int(math.floor(h - Y0))
        y = Y0 + full - 1 if h - Y0 - full < 0.25 else Y0 + full
        st = "minecraft:barrier" if h - Y0 - full < 0.25 else F.HALF_SOLID
        if y >= Y0:
            d.fill(3, y, z, 5, y, z, st)


PREVIEW_CAMS = [("무대 위 (난간 사이에서 북쪽)", F.Camera((10.5, Y0 + 1.62, 70.0), 170.0, -8.0)),
                ("무대 가장자리 (아래 겹)", F.Camera((240.0, Y0 + 1.62, 60.0), 120.0, 25.0)),
                ("유물 쪽으로", F.Camera((-40.0, Y0 + 1.62, -100.0), 180.0, -25.0))]


def preview(b):
    build(b)
