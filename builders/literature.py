"""문학의 층 (호드) — 자유 형체 판 (2026-10-15).

reference/문학의 층 전경.png: 나무 판자 보도를 옆 조금 위(유리 전망 발판, 도착)에서 봄 — 아래 검은 들보와 팔각 아치가
이어진 고가(아치 안 줄 전구), 뒤로 사선으로 엇갈린 에스컬레이터형 책장 띠들, 줄에 매달린 물방울 전구(가까운 것은 살랑 흔들림),
판자를 덧댄 나무 탑(커튼 친 불 켜진 창, 안에 큰 전구), 상자 등불, 푸른 회색 안개.
지정사서 방: builders/literature_room.py.
"""
from __future__ import annotations

import math

import numpy as np

from tools import artfit as A
from tools import form_textures as T
from tools import forms as F

from . import kit

Y0 = 150
BX, HW = 200, 8.5
PLAT = Y0 + 5
CAM = F.Camera((0.5, PLAT + 1.62, HW + 11.0), 180.0, 12.0)
ARRIVE = (0.5, PLAT, HW + 11.0, 180.0, 12.0)
ART = "reference/문학의 층 전경.png"
SPACE = "literature"
UP = np.array([0, 1.0, 0])


def mats():
    m = {}
    m["art"] = F.mat("lit_art", T.art("art/literature", ART), emissive=True, flat=True, ao=False)
    m["deck"] = F.mat("lit_deck", T.planks("lit_deck", (44, 30, 24), (110, 80, 60), boards=4, seed=101), emissive=True,
                      flat=True, ao=False)
    m["beam"] = F.mat("lit_beam", T.wood("lit_beam", (16, 14, 16), (50, 44, 46), seed=102), emissive=True, flat=True,
                      ao=False)
    m["rim"] = F.mat("lit_rim", T.stone_slab("lit_rim", (120, 120, 126), (186, 184, 188), seed=103), emissive=True,
                     flat=True, ao=False)
    m["glass"] = F.mat("lit_glass", T.glow("lit_glass", (255, 236, 210)), layer="translucent", emissive=True,
                       flat=True, ao=False)
    m["bulb"] = F.mat("lit_bulb", T.glow("lit_bulb", (255, 190, 110)), emissive=True, flat=True, ao=False, glow=3)
    m["wire"] = F.mat("lit_wire", T.flat("lit_wire", (30, 26, 26)), emissive=True, flat=True, ao=False)
    blue = [(70, 76, 96), (56, 62, 84), (96, 100, 120), (80, 70, 80), (110, 90, 80)]
    m["shelf"] = [F.mat(f"lit_shelf{i}", T.shelf(f"lit_shelf{i}", blue, wood=(60, 56, 70), seed=104 + i,
                                                  dark_back=(20, 20, 28)), emissive=True, flat=True, ao=False)
                  for i in range(3)]
    m["board"] = [F.mat(f"lit_board{i}", T.board(f"lit_board{i}", c0, c1, w=16, h=32, seed=107 + i), emissive=True,
                        flat=True, ao=False)
                  for i, (c0, c1) in enumerate([((30, 24, 24), (76, 60, 54)), ((24, 22, 26), (64, 56, 58)),
                                                ((40, 30, 26), (96, 72, 58))])]
    m["curtain"] = F.mat("lit_curtain", T.glow("lit_curtain", (255, 232, 200)), emissive=True, flat=True, ao=False,
                         glow=3)
    return m


# ---------------------------------------------------------------- 보도·고가

def walkway(m):
    out = [F.plane((-BX, Y0, HW), (2 * BX, 0, 0), (0, 0, -2 * HW), m["deck"], tile=(4, 4))]
    for s in (-1, 1):
        z = s * HW
        out.append(F.box((-BX, Y0 - 0.6, min(z, z + s * 0.4)), (BX, Y0 + 0.15, max(z, z + s * 0.4)), m["rim"], tile=4.0))
    out.append(F.box((-BX, Y0 - 3.2, -HW), (BX, Y0 - 2.9, HW), m["beam"], tile=4.0))
    # 양 옆면: 팔각 아치가 이어진 검은 벽 (들보 + 기둥 + 깎은 모서리 + 밝은 테) + 아치 안 줄 전구
    period, ow, yb, ya = 9.0, 6.6, Y0 - 1.2, Y0 - 16      # 원화: 아치 9칸마다 (도착 시점 아치 자리와 맞춤)
    oa, ob, cut = Y0 - 14, Y0 - 2.6, 1.6
    x_first = -12.1 - period * 21
    for s in (-1, 1):
        z = s * HW
        f = 1 if s > 0 else -1

        def panel(x0, y0, x1, y1):
            return F.plane((x0 if f > 0 else x1, y0, z), ((x1 - x0) * f, 0, 0), (0, y1 - y0, 0), m["beam"], tile=(4, 4))
        out.append(panel(-BX, ob, BX, yb))                    # 위 들보
        out.append(panel(-BX, ya, BX, oa))                    # 아래
        for xc in np.arange(x_first, BX - period, period):
            out.append(panel(xc + ow / 2, oa, xc + period - ow / 2, ob))       # 기둥
            # 깎은 모서리 (삼각형 4개)
            for cx, cy, dx, dy in ((xc - ow / 2, oa, 1, 1), (xc + ow / 2, oa, -1, 1), (xc - ow / 2, ob, 1, -1),
                                   (xc + ow / 2, ob, -1, -1)):
                tri = np.array([[cx, cy, z], [cx + dx * cut, cy, z], [cx, cy + dy * cut, z], [cx, cy + dy * cut, z]])
                q = F.Quads(tri[None], np.array([[[0, 0], [1, 0], [0, 1], [0, 1]]]) * 0.9, M=m["beam"])
                if (F.face_normals(q.P) @ np.array([0, 0, s]))[0] < 0:
                    q = q.flipped()
                out.append(q)
            ring = [(xc - ow / 2 + cut, oa), (xc + ow / 2 - cut, oa), (xc + ow / 2, oa + cut), (xc + ow / 2, ob - cut),
                    (xc + ow / 2 - cut, ob), (xc - ow / 2 + cut, ob), (xc - ow / 2, ob - cut), (xc - ow / 2, oa + cut),
                    (xc - ow / 2 + cut, oa)]
            out.append(F.sweep(np.array([[x, y, z + s * 0.1] for x, y in ring]), 0.3, m["rim"], sides=4, step=1.0))
            # 줄 전구: 처진 줄 + 작은 전구 6개
            t = np.linspace(0, 1, 9)
            wire = np.stack([xc - ow / 2 + 0.5 + (ow - 1) * t, ob - 0.8 - 1.6 * np.sin(np.pi * t), np.full_like(t, z + s * 0.6)], 1)
            out.append(F.sweep(wire, 0.03, m["wire"], sides=4, step=1.0))
            for tt in np.linspace(0.15, 0.85, 4):
                p = np.array([xc - ow / 2 + 0.5 + (ow - 1) * tt, ob - 1.1 - 1.6 * math.sin(math.pi * tt), z + s * 0.6])
                out.append(F.ellipsoid(p, (0.12, 0.18, 0.12), m["bulb"], 6, 4))
    for x in np.arange(x_first - period / 2, BX, period * 3):           # 교각 (안개 속으로)
        for s in (-1, 1):
            out.append(F.box((x - 1.5, 0, s * HW - 1.5), (x + 1.5, ya, s * HW + 1.5), m["beam"], tile=4.0))
    return out


# ---------------------------------------------------------------- 배경

def escalators(m, rng, count, r_in, r_out, width, thick, far=False):
    """에스컬레이터형 책장: 45도로 오르는 책장 띠 (윗면·아랫면은 계단 무늬 판, 옆면 책)."""
    out = []
    for _ in range(count):
        for _try in range(30):
            x, z = rng.uniform(-r_out, r_out), rng.uniform(-r_out, r_out)
            if abs(z) > r_in or abs(x) > BX + 40:
                break
        n = rng.uniform(60, 170 if not far else 240)
        sx = 1 if rng.random() < 0.5 else -1
        y0 = rng.uniform(20, 300)
        L = n * math.sqrt(2)
        q = F.concat([F.box((-L / 2, -thick, 0), (L / 2, 0, width), m["shelf"][int(rng.integers(3))], tile=2.0,
                            faces="zZ"),
                      F.box((-L / 2, -thick, 0), (L / 2, 0, width), m["beam"], tile=2.0, faces="yY")])
        q = q.rotate("z", 45 * sx).translate((x, y0 + n / 2, z))
        out.append(q)
    return out


def wood_tower(m, rng, cx, cz, w, h, y0=0.0):
    """판자를 덧댄 나무 탑 + 남쪽 면 커튼 친 불 켜진 창 + 위 울퉁불퉁 상자."""
    out = []
    x0, x1, z0, z1 = cx - w / 2, cx + w / 2, cz - w / 2, cz + w / 2
    for (ax, az), (bx, bz) in (((x0, z1), (x1, z1)), ((x1, z1), (x1, z0)), ((x1, z0), (x0, z0)), ((x0, z0), (x0, z1))):
        n = max(1, int(math.hypot(bx - ax, bz - az) / 3))
        for i in range(n):
            for yb in np.arange(y0, y0 + h, 9.0):
                t0, t1 = i / n, (i + 1) / n
                p = np.array([ax + (bx - ax) * t0, yb, az + (bz - az) * t0])
                du = np.array([(bx - ax) * (t1 - t0), 0, (bz - az) * (t1 - t0)])
                nrm = np.cross(du, UP)
                nrm /= np.linalg.norm(nrm)
                out.append(F.plane(p + nrm * rng.uniform(0, 0.5), du, UP * min(9.2, y0 + h - yb),
                                   m["board"][int(rng.integers(3))], tile=(3, 9)))
    out.append(F.plane((x0, y0 + h, z1), (w, 0, 0), (0, 0, -w), m["beam"], tile=(4, 4)))
    for _ in range(int(rng.integers(1, 4))):
        bw = rng.uniform(4, max(5, w / 2))
        bx, bz = cx + rng.uniform(-w / 3, w / 3), cz + rng.uniform(-w / 3, w / 3)
        out.append(F.box((bx - bw / 2, y0 + h, bz - bw / 2), (bx + bw / 2, y0 + h + rng.uniform(5, 16), bz + bw / 2),
                         m["board"][int(rng.integers(3))], tile=3.0))
    wy = y0 + h * rng.uniform(0.45, 0.7)
    ww, wh = max(5, w / 3), max(8, w / 2)
    out.append(F.box((cx - ww / 2 - 1, wy - 1, z1), (cx + ww / 2 + 1, wy + wh + 1, z1 + 0.6), m["beam"], faces="xXyYZ"))
    out.append(F.plane((cx - ww / 2, wy, z1 + 0.62), (ww, 0, 0), (0, wh, 0), m["curtain"], tile=(2, 2)))
    return out


def bulb_mesh(m, p, size, wire):
    """물방울 전구 (유리 + 빛나는 속 + 꼭지 + 줄). p = 전구 아래 끝."""
    x, y, z = p
    prof = [(0.02, y), (size * 0.8, y + size * 0.6), (size, y + size * 1.2), (size * 0.6, y + size * 2.0),
            (size * 0.25, y + size * 2.6), (size * 0.2, y + size * 2.8)]
    glass = F.revolve(prof, m["glass"], segs=10, center=(x, 0, z), tiles_around=2, tile_up=4.0).tint((1, 1, 1), 0.35)
    core = F.ellipsoid((x, y + size * 1.1, z), (size * 0.45, size * 0.7, size * 0.45), m["bulb"], 8, 4)
    cap = F.box((x - size * 0.22, y + size * 2.8, z - size * 0.22), (x + size * 0.22, y + size * 3.2, z + size * 0.22),
                m["wire"])
    line = F.sweep(np.array([[x, y + size * 3.2, z], [x, y + size * 3.2 + wire, z]]), 0.04, m["wire"], sides=4,
                   step=max(1.0, wire))
    return F.concat([glass, core, cap, line])


def bulbs(lay, m, rng, n_static=280, n_swing=72, r=380):
    """줄에 매달린 전구: 보도 가까이는 살랑 흔들리는 움직이는 형체, 멀리는 정적."""
    static = []
    placed = 0
    while placed < n_static + n_swing:
        x, z = rng.uniform(-r, r), rng.uniform(-r, r)
        if abs(z) <= HW + 3 and abs(x) <= BX + 3:
            continue
        near = math.hypot(x - CAM.pos[0], z - CAM.pos[2]) < 120 and placed < n_swing
        y = rng.uniform(Y0 - 40, Y0 + 180)
        size = rng.uniform(0.35, 1.6) if rng.random() < 0.85 else rng.uniform(2.0, 3.5)
        wire = rng.uniform(6, 40)
        mesh = bulb_mesh(m, (x, y, z), size, wire)
        if near:
            piv = (x, y + size * 3.2 + wire, z)
            lay.mover(F.Mover((int(x), int(y), int(z)), mesh, piv, "swing", (rng.uniform(-1, 1), 0, rng.uniform(-1, 1)),
                              period=rng.uniform(5, 9), amp=rng.uniform(2, 5), phase=rng.random()))
        else:
            static.append(mesh)
        placed += 1
    return static


def build(b):
    from . import fragment as Fr
    from . import literature_room
    d = b.dim("literature")
    lay = b.form("literature")
    rng = np.random.default_rng(1001)
    m = mats()
    near = walkway(m)
    # 공중 보도의 하부 보강재: 원근에 관계없이 이어지는 입체 지지대.
    near += [F.box((-BX, Y0 - 1.7, z - .3), (BX, Y0 - 1.25, z + .3), m["rim"]) for z in (-HW + 1.5, HW - 1.5)]
    far = escalators(m, rng, 90, 40, 400, 7, 5) + escalators(m, rng, 40, 400, 700, 9, 7, far=True)
    # 나무 탑: 원화의 셋은 원화 자리 (도착 시점에서 픽셀 상자 → 깊이), 나머지는 둘레
    for cx, cz, w, h in ((0.6, -60, 30, 200), (-91, -80, 24, 205), (116, -90, 27, 210),
                         (-230, -110, 30, 250), (220, -120, 26, 240), (-90, 70, 24, 180), (110, 80, 28, 200),
                         (-300, -20, 28, 230), (300, -10, 26, 220)):
        far += wood_tower(m, rng, cx, cz, w, h)
    static_bulbs = bulbs(lay, m, rng)
    lights = [((0, 300, -200), (0.5, 0.55, 0.7), 700.0), ((0, Y0 - 6, 0), (0.9, 0.6, 0.3), 30.0)]
    kit.project_add(lay, CAM, m["art"], near=near, far=far, lights=lights, ambient=(0.5, 0.52, 0.62),
                    glow_mats=[m["bulb"], m["curtain"], m["glass"]], min_facing=0.12, far_edge=6.0, far_min_facing=0.5)
    for q in static_bulbs:
        lay.add(q)
    lay.add(kit.glass_platform(d, m["glass"], m["wire"], -2.0, 3.0, HW + 9.0, HW + 13.0, PLAT))
    lay.add(kit.glass_stairs(m["glass"], m["wire"], 4, 5, int(HW) + 12, int(HW) + 1, PLAT, Y0))
    kit.art_sky(lay, "lit", CAM, ART, [(-90, (40, 40, 52)), (-10, (90, 96, 110)), (0, (130, 136, 150)),
                                       (20, (110, 118, 136)), (50, (70, 78, 96)), (90, (40, 46, 60))],
                cloud_e=(-5.0, 8.0), below=(60, 60, 72), zenith=(40, 46, 60))
    collision(d)
    lay.emitter(F.Emitter((-60, Y0 - 20, -60, 60, Y0 + 40, 60), rate=4.0, sprites=("ruina:block/form/paper_gold",),
                          wind=(0.0, 0.15, 0.0), size=0.1, life=8.0, spin=0.1, color=(1.0, 0.75, 0.45), glow=True))
    room = literature_room.build(b, d)
    Fr.stage(b, d, "goldbar", "문학의 층", ARRIVE, room,
             room_box=f"x={literature_room.OX - 200},y=-64,z=-1024,dx=400,dy=1024,dz=2048")
    b.extra_checks += [
        {"what": "호드 방 바이옴", "cmd": f"execute in {d.dim} if biome {literature_room.OX} {literature_room.Y0} 0 "
                                     f"ruina:literature_room", "expect": True},
    ]


def collision(d):
    d.fill(-BX, Y0 - 1, -int(HW), BX, Y0 - 1, int(HW), "minecraft:barrier")
    for z in (-int(HW) - 1, int(HW) + 1):
        d.fill(-BX, Y0, z, BX, Y0, z, "minecraft:barrier")
    kit.stair_collision(d, 4, 5, int(HW) + 12, int(HW) + 1, PLAT, Y0)
    d.fill(4, Y0, int(HW) + 1, 5, Y0, int(HW) + 1, "minecraft:air")


PREVIEW_CAMS = [("보도 위", F.Camera((0.5, Y0 + 1.62, 0.0), 90.0, -5.0)),
                ("보도에서 책장 띠 올려다봄", F.Camera((0.5, Y0 + 1.62, -6.0), 180.0, -30.0))]


def preview(b):
    build(b)
