"""로비 전환 후 '밝은 책장 홀' — 자유 형체 판 (reference/로비 전경 (전환 후).jpg, 로비_3D 08~19).

도착 자리(CAM, 남쪽 높은 층계참)에서 북쪽을 보면 원화: 가운데 앤젤라의 책상(톱니 장치 앞면), 뒤로 빛 속으로 오르는
흰 대계단, 둘레의 높낮이 다른 책장 탑들, 쌓인 책 더미와 촛불. 3D 영상의 둥근 책장 벽(붉은 아래 장·사다리)과
바닥에 흩어진 책·작은 탁자. 빛은 계단 꼭대기의 큰 빛 + 촛불 웅덩이를 꼭짓점 색에 구움.
"""
from __future__ import annotations

import math

import numpy as np

from builders import detail as D
from tools import form_textures as T
from tools import forms as F

Y0 = 64
OX = 512.0                       # 홀 중심 x (방 + 512)
ART = "reference/로비 전경 (전환 후).jpg"
LAND = 4.0                       # 도착 층계참 높이
CAM = F.Camera((OX + 0.5, Y0 + LAND + 1.62, 14.0), 180.0, 0.0)
ARRIVE = (OX + 0.5, Y0 + LAND, 14.0, 180.0, 0.0)
HR, HW = 22.0, 12.0              # 둥근 책장 벽 반지름·높이
DESK = (OX + 0.5, 0.0)           # 책상 가운데 (x, z) — 단 위
STAIR_Z0, STAIR_W, STAIR_N, RISE, RUN = -6.0, 5.0, 26, 1.0, 1.25
UP = np.array([0, 1.0, 0])
SPACE = "lobby"


def mats():
    m = {}
    m["art"] = F.mat("hall_art", T.art("art/lobby_hall", ART), emissive=True, flat=True, ao=False)
    warm = [(150, 62, 40), (120, 46, 32), (176, 120, 70), (96, 60, 40), (196, 150, 96), (140, 92, 56), (88, 44, 32)]
    m["shelf"] = [F.mat(f"hall_shelf{i}", T.shelf(f"hall_shelf{i}", warm, wood=(110, 64, 38), seed=40 + i,
                                                   dark_back=(40, 22, 14)), emissive=True, flat=True, ao=False)
                  for i in range(3)]
    m["wood"] = F.mat("hall_wood", T.wood("hall_wood", (80, 44, 26), (170, 110, 66), seed=41), emissive=True, flat=True,
                      ao=False)
    m["cab"] = F.mat("hall_cab", T.wood("hall_cab", (90, 24, 18), (150, 52, 36), seed=42), emissive=True, flat=True,
                     ao=False)
    m["floor"] = F.mat("hall_floor", T.planks("hall_floor", (70, 46, 30), (150, 106, 70), boards=4, seed=43),
                       emissive=True, flat=True, ao=False)
    m["white"] = F.mat("hall_white", T.stone_slab("hall_white", (214, 206, 190), (250, 246, 236), seed=44),
                       emissive=True, flat=True, ao=False)
    m["stone"] = F.mat("hall_stone", T.stone_slab("hall_stone", (70, 66, 64), (128, 122, 116), seed=45), emissive=True,
                       flat=True, ao=False)
    m["gear"] = F.mat("hall_gear", T.metal("hall_gear", (60, 46, 30), (170, 140, 90), seed=46), emissive=True, flat=True,
                      ao=False)
    m["light"] = F.mat("hall_light", T.glow("hall_light", (255, 246, 222)), emissive=True, flat=True, ao=False, glow=3)
    m["candle"] = F.mat("hall_candle", T.glow("hall_candle", (255, 200, 120)), emissive=True, flat=True, ao=False, glow=3)
    m["book"] = [F.mat(f"hall_book{i}", T.flat(f"hall_book{i}", c), emissive=True, flat=True, ao=False)
                 for i, c in enumerate([(150, 52, 38), (110, 40, 30), (190, 160, 120), (120, 84, 56), (220, 210, 190)])]
    m["paper"] = F.mat("hall_paper", T.paper("hall_paper", c=(240, 230, 210), seed=47), layer="cutout", emissive=True,
                       flat=True, ao=False)
    return m


def shelf_block(m, x0, z0, x1, z1, y0, y1, rng, cap=True):
    """네 면의 개별 책과 선반·뒤판·모서리 기둥으로 구성된 책장 탑."""
    out = []
    # 높이와 무관하게 각 층의 선반을 실제 두께로 만들고,
    # 근접에서 읽히는 책은 종이 속지와 표지·책등을 각각 가진다.
    for side, (ax, az), (bx, bz) in (
        (0, (x0, z1), (x1, z1)),
        (1, (x1, z1), (x1, z0)),
        (2, (x1, z0), (x0, z0)),
        (3, (x0, z0), (x0, z1)),
    ):
        direction = np.array([bx-ax, 0, bz-az], float)
        length = float(np.linalg.norm(direction))
        tangent = direction / length
        inward = np.array([tangent[2], 0, -tangent[0]])
        # 네 면의 깊은 뒤판, 실재하는 책 선반
        for row in range(max(1, int((y1-y0-0.6)/1.15))):
            yy = y0 + row*1.15
            p = np.array([ax, yy, az]) + inward*.15
            q = np.array([bx, yy, bz]) + inward*.15
            if side % 2 == 0:
                out.append(F.box((min(p[0],q[0]),yy,min(p[2],q[2])-.28),
                                 (max(p[0],q[0]),yy+.10,max(p[2],q[2])+.28),m["wood"]))
            else:
                out.append(F.box((min(p[0],q[0])-.28,yy,min(p[2],q[2])),
                                 (max(p[0],q[0])+.28,yy+.10,max(p[2],q[2])),m["wood"]))
            # 거리별 밀도: 원거리 탑도 개별 책으로 구성하되 간격을 키운다.
            step = .23 if abs((x0+x1)/2-OX)<30 and abs((z0+z1)/2)<30 else .43
            count = max(1,int((length-.55)/step))
            for j in range(count):
                pos = .3+(j+.5)*(length-.6)/count
                height = float(rng.uniform(.68,.98))
                width = min(step*.82,.27)
                book = D.upright_book(width,height,.34,
                                      m["book"][int(rng.integers(len(m["book"])))],m["paper"])
                # 로컬 +Z 책등을 외부 방향으로 배치.
                angle = math.degrees(math.atan2(tangent[2],tangent[0]))
                book = book.rotate("y",-angle)
                loc = np.array([ax, yy+.10, az])+tangent*pos-inward*.05
                out.append(book.translate(loc))
        # 실제 뒤판: 외곽 모서리 사이의 얇은 벽
        if side % 2 == 0:
            out.append(F.box((min(ax,bx),y0,az-.12),(max(ax,bx),y1,az+.12),m["cab"]))
        else:
            out.append(F.box((ax-.12,y0,min(az,bz)),(ax+.12,y1,max(az,bz)),m["cab"]))
    for x,z in ((x0,z0),(x1,z0),(x0,z1),(x1,z1)):
        out.append(F.box((x-.2,y0,z-.2),(x+.2,y1+.2,z+.2),m["wood"]))
    if cap:
        out.append(F.box((x0-.3,y1,z0-.3),(x1+.3,y1+.4,z1+.3),m["wood"]))
    return F.concat(out)


def ring_wall(m, rng):
    """둥근 책장 벽 (붉은 아래 장 2 + 책장 + 위 판, 이음 기둥, 사다리). 계단 자리는 뚫음."""
    out = []
    n = 40
    for i in range(n):
        a0, a1 = 2 * math.pi * i / n, 2 * math.pi * (i + 1) / n
        p0 = np.array([OX + HR * math.cos(a0), 0, HR * math.sin(a0)])
        p1 = np.array([OX + HR * math.cos(a1), 0, HR * math.sin(a1)])
        mid = (p0 + p1) / 2
        if mid[2] < 2.0:                  # 북쪽 반은 트임 (원화: 책장 탑들이 바로 보임)
            continue
        st, du = p1, p0 - p1
        if np.cross(du, UP) @ (np.array([OX, 0, 0]) - mid) < 0:     # 안쪽을 보게
            st, du = p0, p1 - p0
        out.append(F.plane(st + UP * Y0, du, UP * 2.0, m["cab"], tile=(1, 1)))
        out.append(F.plane(st + UP * (Y0 + 2), du, UP * (HW - 2.5), m["shelf"][i % 3], tile=(1.0, 1.0)))
        out.append(F.plane(st + UP * (Y0 + HW - 0.5), du, UP * 0.5, m["wood"], tile=(1, 1)))
        if i % 2 == 0:
            out.append(F.box(p0 + np.array([-0.25, Y0, -0.25]), p0 + np.array([0.25, Y0 + HW, 0.25]), m["wood"]))
        if i % 5 == 2:                    # 사다리
            c = mid * 0.97 + np.array([OX, 0, 0]) * 0.03
            t = (p1 - p0) / np.linalg.norm(p1 - p0)
            for s in (-0.35, 0.35):
                q = c + t * s
                out.append(F.box(q + np.array([-0.06, Y0, -0.06]), q + np.array([0.06, Y0 + HW - 1, 0.06]), m["wood"]))
            for y in np.arange(Y0 + 0.5, Y0 + HW - 1, 0.5):
                a, b = c - t * 0.35, c + t * 0.35
                out.append(F.sweep(np.array([a + UP * y, b + UP * y]), 0.04, m["wood"], sides=4, step=0.4))
    return F.concat(out)


def towers(m, rng):
    """벽 너머 책장 탑들 (원화 뒤쪽 '책장 도시'): 바깥으로 갈수록 높게. 계단 양옆에 바짝."""
    out = []
    placed = []
    for _ in range(600):
        if len(placed) >= 80:
            break
        a = rng.uniform(0, 2 * math.pi)
        r = rng.uniform(HR + 3, 64)
        cx, cz = OX + r * math.cos(a), r * math.sin(a)
        if abs(cx - OX) < STAIR_W + 3 and cz < -HR + 6 and cz > -60:
            continue
        w, l = rng.uniform(5, 11), rng.uniform(3, 6)
        if abs(math.cos(a)) > abs(math.sin(a)):
            w, l = l, w
        if any(abs(cx - px) < (w + pw) / 2 + 0.5 and abs(cz - pz) < (l + pl) / 2 + 0.5 for px, pz, pw, pl, *_ in placed):
            continue
        h = (14 + (r - HR) * 1.15) * rng.uniform(0.7, 1.4)
        y0 = Y0 + rng.uniform(-2, 3)
        out.append(shelf_block(m, cx - w / 2, cz - l / 2, cx + w / 2, cz + l / 2, y0, y0 + h, rng))
        placed.append((cx, cz, w, l, y0 + h))
    return F.concat(out), placed


def white_stairs(m):
    """흰 대계단: 책상 뒤에서 북쪽으로 오르다 꼭대기에서 빛나는 아치. 양옆 흰 벽 + 난간."""
    out = []
    x0, x1 = OX + 0.5 - STAIR_W, OX + 0.5 + STAIR_W
    for k in range(STAIR_N):
        za, zb = STAIR_Z0 - RUN * k, STAIR_Z0 - RUN * (k + 1)
        yt = Y0 + RISE * (k + 1)
        out.append(F.plane((x0, yt, za), (x1 - x0, 0, 0), (0, 0, zb - za), m["white"], tile=(2, 1)).flipped())
        out.append(F.plane((x0, yt - RISE, za), (x1 - x0, 0, 0), (0, RISE, 0), m["white"], tile=(2, 1)))
    zt = STAIR_Z0 - RUN * STAIR_N
    yt = Y0 + RISE * STAIR_N
    for x, s in ((x0, -1), (x1, 1)):
        # 옆벽 (바닥 ~ 단 위 1.2): 비스듬한 위 테
        n = STAIR_N
        G = np.zeros((n + 1, 2, 3))
        for k in range(n + 1):
            z = STAIR_Z0 - RUN * k
            G[k, 0] = (x, Y0, z)
            G[k, 1] = (x, Y0 + RISE * k + 1.4, z)
        UV = np.stack([np.stack([np.arange(n + 1) * RUN / 2, np.zeros(n + 1)], -1),
                       np.stack([np.arange(n + 1) * RUN / 2, np.ones(n + 1)], -1)], 1)
        out.append(F.fit_tiles(F.grid(G + np.array([s * 0.4, 0, 0]), UV, m["white"],
                                      N=np.broadcast_to([s, 0, 0], G.shape))))
        out.append(F.fit_tiles(F.grid(G, UV, m["white"], N=np.broadcast_to([-s, 0, 0], G.shape))))
        top = np.stack([G[:, 1], G[:, 1] + np.array([s * 0.4, 0, 0])], 1)
        out.append(F.fit_tiles(F.grid(top, UV, m["white"], N=np.broadcast_to(UP, top.shape))))
    # 꼭대기 층계참 + 빛 아치 (원화 위쪽 창의 빛)
    out.append(F.plane((x0, yt, zt), (x1 - x0, 0, 0), (0, 0, -6), m["white"], tile=(2, 2)).flipped())
    out.append(F.plane((x0 - 2, yt, zt - 6), (x1 - x0 + 4, 0, 0), (0, 22, 0), m["light"], tile=(4, 4)))
    for x in (x0 - 2.5, x0 + 3.0, x1 - 3.0, x1 + 2.5):
        out.append(F.box((x - 0.6, yt, zt - 6.5), (x + 0.6, yt + 20, zt - 5.5), m["white"]))
    return F.concat(out)


def desk(m):
    """앤젤라의 책상: 돌 단(높이 1, 앞 두 계단) 위 폭 6 책상, 앞면 = 톱니 장치, 윗면 = 회색 돌판."""
    cx, cz = DESK
    out = [F.box((cx - 7, Y0, cz - 4), (cx + 7, Y0 + 0.5, cz + 3), m["stone"]),
           F.box((cx - 6, Y0 + 0.5, cz - 3.5), (cx + 6, Y0 + 1.0, cz + 2.2), m["stone"])]
    out.append(F.box((cx - 3.2, Y0 + 1.0, cz - 1.2), (cx + 3.2, Y0 + 2.2, cz + 1.0), m["gear"], faces="xXzy"))
    out.append(F.box((cx - 3.5, Y0 + 2.2, cz - 1.5), (cx + 3.5, Y0 + 2.45, cz + 1.3), m["stone"]))
    # 의자·등·책
    out.append(F.box((cx - 0.6, Y0 + 1.0, cz - 3.0), (cx + 0.6, Y0 + 1.6, cz - 2.0), m["wood"]))
    out.append(F.box((cx - 0.6, Y0 + 1.6, cz - 3.1), (cx + 0.6, Y0 + 3.2, cz - 2.9), m["wood"]))
    out.append(F.box((cx - 2.6, Y0 + 2.45, cz - 0.8), (cx - 2.2, Y0 + 3.2, cz - 0.4), m["candle"]))
    for i in range(4):
        out.append(F.box((cx + 1.2 + i * 0.45, Y0 + 2.45, cz - 0.8), (cx + 1.6 + i * 0.45, Y0 + 2.45 + 0.3 + 0.1 * i,
                                                                       cz - 0.2), m["book"][i % 5]))
    return F.concat(out)


def clutter(m, rng, placed_towers):
    """바닥: 쌓인 책 탑, 흩어진 책·종이, 작은 탁자, 촛불 (3D 영상 08~12, 원화 아래 양옆)."""
    out, candles = [], []
    for _ in range(140):
        a = rng.uniform(0, 2 * math.pi)
        r = rng.uniform(4, HR - 1.5) ** 1.0
        x, z = OX + r * math.cos(a), r * math.sin(a)
        if abs(x - DESK[0]) < 8 and -5 < z < 4:
            continue
        if abs(x - OX - 0.5) < STAIR_W + 1.5 and z < STAIR_Z0 + 1:
            continue
        if abs(x - OX - 0.5) < 3 and z > 4:          # 도착 층계참 앞 통로
            continue
        kind = rng.random()
        if kind < 0.35:                               # 책 탑
            y = Y0
            for k in range(int(rng.integers(3, 14))):
                w, d, h = rng.uniform(0.5, 0.9), rng.uniform(0.35, 0.6), rng.uniform(0.08, 0.16)
                ang = rng.uniform(-0.3, 0.3)
                b = F.box((-w / 2, 0, -d / 2), (w / 2, h, d / 2), m["book"][int(rng.integers(5))]).rotate("y", math.degrees(ang))
                out.append(b.translate((x, y, z)))
                y += h
            if rng.random() < 0.4:
                candles.append((x, y, z))
                out.append(F.box((x - 0.05, y, z - 0.05), (x + 0.05, y + 0.25, z + 0.05), m["candle"]))
        elif kind < 0.85:                             # 흩어진 책·종이
            for k in range(int(rng.integers(3, 9))):
                xx, zz = x + rng.uniform(-1.5, 1.5), z + rng.uniform(-1.5, 1.5)
                ang = rng.uniform(0, 180)
                if rng.random() < 0.5:
                    b = F.box((-0.3, 0, -0.2), (0.3, 0.1, 0.2), m["book"][int(rng.integers(5))])
                else:
                    b = F.plane((-0.25, 0.01, -0.18), (0.5, 0, 0), (0, 0, 0.36), m["paper"]).flipped()
                out.append(b.rotate("y", ang).translate((xx, Y0, zz)))
        else:                                         # 작은 탁자 + 촛불
            out.append(F.box((x - 1.0, Y0 + 0.9, z - 0.6), (x + 1.0, Y0 + 1.0, z + 0.6), m["wood"]))
            for dx in (-0.85, 0.85):
                for dz in (-0.45, 0.45):
                    out.append(F.box((x + dx - 0.06, Y0, z + dz - 0.06), (x + dx + 0.06, Y0 + 0.9, z + dz + 0.06),
                                     m["wood"]))
            out.append(F.box((x - 0.05, Y0 + 1.0, z - 0.05), (x + 0.05, Y0 + 1.3, z + 0.05), m["candle"]))
            candles.append((x, Y0 + 1.3, z))
    return F.concat(out), candles


def landing(m):
    """도착 층계참 (남쪽, 높이 LAND): 앞으로 내려가는 계단 + 난간."""
    out = []
    x0, x1, z0, z1 = OX - 4.5, OX + 5.5, 11.5, 18.0
    out.append(F.box((x0, Y0, z0), (x1, Y0 + LAND, z1), m["wood"]))
    for k in range(int(LAND * 2)):
        za = z0 - 0.6 * (k + 1)
        y = Y0 + LAND - 0.5 * (k + 1)
        out.append(F.box((x0 + 1, Y0, za), (x1 - 1, y, za + 0.6), m["wood"]))
    for x in (x0, x1):
        out.append(F.box((x - 0.1, Y0 + LAND, z0), (x + 0.1, Y0 + LAND + 1.1, z1), m["wood"]))
    return F.concat(out)


def build(b, d):
    lay = b.form("lobby")
    rng = np.random.default_rng(401)
    m = mats()
    floor = F.plane((OX - 66, Y0, 66), (132, 0, 0), (0, 0, -132), m["floor"], tile=(3, 3))
    tw, placed = towers(m, rng)
    cl, candles = clutter(m, rng, placed)
    parts = [floor, ring_wall(m, rng), tw, white_stairs(m), desk(m), cl, landing(m)]
    zt = STAIR_Z0 - RUN * STAIR_N
    lights = [((OX + 0.5, Y0 + STAIR_N * RISE + 8, zt - 4), (1.6, 1.4, 1.1), 70.0),
              ((OX + 0.5, Y0 + 30, 0), (0.55, 0.42, 0.3), 60.0)]
    lights += [(p, (0.9, 0.55, 0.25), 5.0) for p in candles[:60]]
    glow = {m["light"], m["candle"]}
    baked = []
    for q in parts:
        bq = F.bake_points(q, lights, ambient=(0.42, 0.32, 0.24), ao_floor=Y0)
        sel = np.isin(q.M, list(glow))
        bq.C[sel] = q.C[sel]
        baked.append(bq)
    sub = [F.subdivide(q, 1.0) for q in baked]
    proj = F.project_scene(sub, CAM, m["art"], min_facing=0.25, zres=(700, 394), min_seen=3)
    for i, q in enumerate(proj):
        lay.add(q, max_edge=2.0 if i in (0, 2) else 1.0)
    collision(d, placed)
    for x, y, z in candles[:40]:
        p = (int(math.floor(x)), int(y), int(math.floor(z)))
        if d.get(*p) == "minecraft:air":
            d.set(*p, "minecraft:light[level=10]")
    for gx in range(-16, 17, 8):
        for gz in range(-16, 17, 8):
            p = (int(OX) + gx, Y0 + 9, gz)
            if d.get(*p) == "minecraft:air":
                d.set(*p, "minecraft:light[level=15]")
    lay.emitter(F.Emitter((OX - 18, Y0 + 1, -18, OX + 18, Y0 + 14, 14), rate=4.0,
                          sprites=("ruina:block/form/paper_gold",), wind=(0.0, 0.25, 0.0), size=0.12, life=8.0,
                          spin=0.2, color=(1.0, 0.85, 0.5), glow=True))
    d.set_biome(int(OX) - 80, -96, int(OX) + 80, 80, "ruina:lobby_hall")
    return ARRIVE


def collision(d, placed):
    ox = int(OX)
    d.fill(ox - 66, Y0 - 1, -66, ox + 66, Y0 - 1, 66, "minecraft:barrier")
    # 둥근 벽
    for i in range(720):
        a = 2 * math.pi * i / 720
        x, z = int(math.floor(OX + HR * math.cos(a))), int(math.floor(HR * math.sin(a)))
        if z < 2:
            continue
        d.fill(x, Y0, z, x, Y0 + int(HW), z, "minecraft:barrier")
    # 책장 탑 + 바깥 경계
    for cx, cz, w, l, top in placed:
        d.fill(int(math.floor(cx - w / 2)), Y0, int(math.floor(cz - l / 2)), int(math.floor(cx + w / 2)),
               min(int(top), Y0 + 40), int(math.floor(cz + l / 2)), "minecraft:barrier")
    for i in range(1440):
        a = 2 * math.pi * i / 1440
        x, z = int(math.floor(OX + 65 * math.cos(a))), int(math.floor(65 * math.sin(a)))
        d.fill(x, Y0, z, x, Y0 + 6, z, "minecraft:barrier")
    # 책상 단·책상
    cx, cz = int(DESK[0]), int(DESK[1])
    d.fill(cx - 7, Y0, cz - 4, cx + 6, Y0, cz + 2, F.HALF_SOLID)
    d.fill(cx - 3, Y0 + 1, cz - 2, cx + 3, Y0 + 2, cz, "minecraft:barrier")
    # 흰 대계단 (1 단 = 1 높이 → 계단마다 반 칸 두 개 대신 온 칸: 점프. 반 칸 사이 단을 둬 걷게)
    x0, x1 = int(math.floor(OX + 0.5 - STAIR_W)), int(math.floor(OX + 0.5 + STAIR_W - 1e-6))
    zt = STAIR_Z0 - RUN * STAIR_N
    for z in range(int(math.floor(STAIR_Z0)) - 1, int(math.floor(zt)) - 7, -1):
        k = (STAIR_Z0 - (z + 0.5)) / RUN
        top = Y0 + RISE * min(STAIR_N, math.ceil(k)) if k > 0 else Y0
        hf = top - Y0 - (k % 1 < 0.5) * 0.5 if k > 0 else 0       # 단 안 앞 절반은 반 칸 낮게 → 반 칸씩 오름
        full = int(math.floor(hf))
        if full > 0:
            d.fill(x0, Y0, z, x1, Y0 + full - 1, z, "minecraft:barrier")
        if hf - full > 0.25:
            d.fill(x0, Y0 + full, z, x1, Y0 + full, z, F.HALF_SOLID)
        d.fill(x0 - 1, Y0, z, x0 - 1, int(top) + 1, z, "minecraft:barrier")
        d.fill(x1 + 1, Y0, z, x1 + 1, int(top) + 1, z, "minecraft:barrier")
    # 도착 층계참 + 내려가는 계단 (반 칸씩)
    d.fill(ox - 5, Y0, 12, ox + 5, Y0 + int(LAND) - 1, 17, "minecraft:barrier")
    for z in range(6, 12):
        k = math.ceil((11.5 - (z + 0.5)) / 0.6)
        h = LAND - 0.5 * k
        if h <= 0:
            continue
        full = int(math.floor(h))
        if full > 0:
            d.fill(ox - 3, Y0, z, ox + 4, Y0 + full - 1, z, "minecraft:barrier")
        if h - full > 0.25:
            d.fill(ox - 3, Y0 + full, z, ox + 4, Y0 + full, z, F.HALF_SOLID)


PREVIEW_CAMS = [("홀 가운데에서 남쪽", F.Camera((OX + 0.5, Y0 + 1.62, -2.0), 0.0, -5.0)),
                ("책상 옆에서 계단 위", F.Camera((OX + 9.0, Y0 + 1.62, 6.0), 160.0, -25.0)),
                ("계단 꼭대기에서 내려다봄", F.Camera((OX + 0.5, Y0 + 27.6, -36.0), 0.0, 30.0))]


def preview(b):
    build(b, b.dim("lobby"))
