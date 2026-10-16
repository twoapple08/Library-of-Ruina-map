"""로비 전환 전 '어두운 나무 방' — 자유 형체 판 (reference/로비.png, 로비_3D 01~07).

도착 자리(ROOM_CAM)에서 북쪽 벽을 올려다보면 원화 그대로: 책장 칸·홈 파인 기둥(조각된 주두)·종 모양 벽등·
가운데 좁은 계단 통로(아치)·빛나는 벽감·앞 낮은 단. 뒤(남쪽)는 3D 영상의 긴 방: 받침 기둥 등, 책상, 검은 출구.
빛은 등불마다 따뜻한 빛 웅덩이를 꼭짓점 색에 구움 (forms.bake_points) + 보이지 않는 빛 블록.
충돌: 벽·기둥 barrier, 바닥 barrier, 계단·단은 반 칸 (점프 없이).
"""
from __future__ import annotations

import math

import numpy as np

from builders import detail as D
from tools import form_textures as T
from tools import forms as F

Y0 = 64
ART = "reference/로비.png"
YF = Y0 + 2                   # 방 바닥 (북쪽 벽 앞은 네 단 내려간 Y0 — 원화 아래 계단)
CAM = F.Camera((0.5, YF + 1.62, -8.0), 180.0, 0.0)     # 원화는 세로선이 나란함 → 수평 시선
ARRIVE = (0.5, YF, -8.0, 180.0, 0.0)
X0, X1 = -11.0, 11.0          # 안쪽 벽 x
ZB, ZS = -16.0, 24.0          # 북쪽 벽 / 남쪽 벽 z
ZSTEP = (-14.0, -11.0)        # 내려가는 네 단 (북쪽 끝 z, 남쪽 끝 z)
H = 13.0                      # 천장 높이 (Y0 기준)
UP = np.array([0, 1.0, 0])

# 북쪽 벽 구간 (원화 픽셀 x → 벽면 x, tools: ArtView.on_plane_z)
BAYS = [(-11.0, -7.1), (-5.6, -1.4), (5.4, 8.0), (8.6, 11.0)]       # 책장 칸
PILLARS = [(-7.1, -5.6, 1.0, 68.4), (-1.4, -0.35, 0.5, None), (1.75, 3.9, 1.4, 68.9), (8.0, 8.6, 0.5, None)]
STAIR = (-0.3, 1.7)            # 계단 통로 x
NICHE = (3.9, 5.4)            # 빛나는 벽감
LAMPS = [(-0.9, Y0 + 5.55, ZB + 0.7), (2.85, Y0 + 3.3, ZB + 1.9)]      # 원화 벽등 두 개 (종 아래 끝 높이)


def mats():
    m = {}
    m["art"] = F.mat("lobby_art", T.art("art/lobby_room", ART), emissive=True, flat=True, ao=False)
    warm = [(104, 56, 34), (80, 40, 26), (128, 82, 48), (66, 42, 30), (146, 104, 66), (92, 62, 38), (58, 34, 26)]
    m["shelf"] = [F.mat(f"lobby_shelf{i}", T.shelf(f"lobby_shelf{i}", warm, seed=20 + i), emissive=True, flat=True,
                        ao=False) for i in range(3)]
    m["wood"] = F.mat("lobby_wood", T.wood("lobby_wood", (34, 18, 12), (88, 52, 32)), emissive=True, flat=True, ao=False)
    m["wood_l"] = F.mat("lobby_wood_l", T.wood("lobby_wood_l", (60, 34, 20), (128, 82, 50), seed=14), emissive=True,
                        flat=True, ao=False)
    m["floor"] = F.mat("lobby_floor", T.planks("lobby_floor", (40, 16, 12), (96, 44, 30), boards=4, seed=15),
                       emissive=True, flat=True, ao=False)
    m["lamp"] = F.mat("lobby_lamp", T.glow("lobby_lamp", (255, 222, 168)), emissive=True, flat=True, ao=False, glow=3)
    m["metal"] = F.mat("lobby_metal", T.metal("lobby_metal", (40, 30, 20), (120, 96, 60)), emissive=True, flat=True,
                       ao=False)
    m["dark"] = F.mat("lobby_dark", T.flat("lobby_dark", (10, 6, 5)), emissive=True, flat=True, ao=False)
    m["paper"] = F.mat("lobby_paper", T.paper("lobby_paper", c=(220, 200, 160), seed=16), emissive=True, flat=True,
                       ao=False)
    return m


# ---------------------------------------------------------------- 부품

def shelf_wall(m, x0, x1, y0, y1, z, facing=1, seed=0, depth=0.6):
    """책장 칸 (벽면 z, facing=+1 이면 +z 를 봄): 한 블록마다 책 줄, 양옆 기둥 판, 위 장식 띠, 아래 걸레받이."""
    rng = np.random.default_rng(seed)
    out = []
    zf = z + facing * 0.02
    # 선반마다 독립적인 낱권 책: 종이 속지·앞뒤 표지·책등에 실제 두께.
    # 양쪽 벽면도 같은 로컬 +Z 부품을 뒤집어 책등이 실내를 향하게 한다.
    zi = z - facing * depth
    inner_width = max(0.1, x1 - x0 - 0.65)
    rows = int(y1 - y0 - 1.2)
    for i in range(rows):
        base = y0 + 0.68 + i
        cursor = x0 + 0.36
        while cursor < x1 - 0.42:
            width = float(rng.uniform(0.13, 0.23))
            if cursor + width > x1 - 0.34:
                break
            height = float(rng.uniform(0.62, 0.87))
            book_depth = float(rng.uniform(0.28, 0.45))
            cover = m["wood_l"] if rng.random() < 0.18 else m["shelf"][int(rng.integers(3))]
            q = D.upright_book(width, height, book_depth, cover, m["paper"])
            q = q.translate((cursor + width / 2, base, zi + facing * (book_depth / 2 + 0.05)))
            if facing < 0:
                q = q.rotate("y", 180, origin=(cursor + width / 2, 0, zi))
            out.append(q)
            cursor += width + float(rng.uniform(0.015, 0.045))
    # 칸 안 옆·위·아래 면 (깊이)
    out.append(F.box((x0, y0, zi - 0.05 if facing > 0 else z), (x0 + 0.25, y1, z if facing > 0 else zi + 0.05),
                     m["wood"], faces="xXzZ"))
    out.append(F.box((x1 - 0.25, y0, zi - 0.05 if facing > 0 else z), (x1, y1, z if facing > 0 else zi + 0.05),
                     m["wood"], faces="xXzZ"))
    # 앞 테: 기둥 판·걸레받이·위 띠
    zz = (z, z + facing * 0.15)
    zlo, zhi = min(zz), max(zz)
    out.append(F.box((x0, y0, zlo), (x0 + 0.3, y1, zhi), m["wood_l"]))
    out.append(F.box((x1 - 0.3, y0, zlo), (x1, y1, zhi), m["wood_l"]))
    out.append(F.box((x0, y0, zlo), (x1, y0 + 0.6, zhi + facing * 0.1 if facing > 0 else zhi), m["wood"]))
    out.append(F.box((x0, y1 - 0.5, zlo), (x1, y1, zhi + 0.1 * facing if facing > 0 else zhi), m["wood_l"]))
    # 선반 앞 모서리 (가로 판)
    for i in range(int(y1 - y0 - 1.2)):
        y = y0 + 0.6 + i
        out.append(F.box((x0 + 0.3, y - 0.06, min(z, zi)), (x1 - 0.3, y + 0.06, max(z, zi)), m["wood_l"], faces="yYzZ"))
    return F.concat(out)


def fluted_pillar(m, x, z, r, y0, y1, capital=None, flutes=12):
    """홈 파인 둥근 기둥 (받침 2단 + 몸통 + 조각 주두)."""
    out = []
    out.append(F.box((x - r - 0.25, y0, z - r - 0.25), (x + r + 0.25, y0 + 1.0, z + r + 0.25), m["wood"]))
    out.append(F.box((x - r - 0.12, y0 + 1.0, z - r - 0.12), (x + r + 0.12, y0 + 1.4, z + r + 0.12), m["wood_l"]))
    prof = [(r, y0 + 1.4), (r, y1)]
    q = F.revolve(prof, m["wood"], segs=flutes * 4, center=(x, 0, z), tiles_around=flutes, tile_up=2.0)
    # 홈: 반지름을 각도에 따라 살짝 오목하게
    ang = np.arctan2(q.P[..., 2] - z, q.P[..., 0] - x)
    k = 1 - 0.08 * (0.5 + 0.5 * np.cos(ang * flutes))
    q.P[..., 0] = x + (q.P[..., 0] - x) * k
    q.P[..., 2] = z + (q.P[..., 2] - z) * k
    out.append(q)
    if capital:
        cy = capital
        out.append(F.box((x - r - 0.35, cy, z - r - 0.35), (x + r + 0.35, cy + 1.6, z + r + 0.35), m["wood_l"]))
        out.append(F.box((x - r - 0.5, cy + 1.6, z - r - 0.5), (x + r + 0.5, cy + 2.0, z + r + 0.5), m["wood"]))
    return F.concat(out)


def bell_lamp(m, x, y, z, arm=None):
    """종 모양 벽등: 위 금속 갓 + 빛나는 종 (원화). arm = 벽 쪽 팔 끝 z (없으면 매달기만)."""
    out = []
    bell = F.revolve([(0.04, y + 0.7), (0.24, y + 0.62), (0.3, y + 0.22), (0.36, y)], m["lamp"], segs=16,
                     center=(x, 0, z), tiles_around=4, tile_up=1.0)
    out.append(bell)
    out.append(F.revolve([(0.0, y + 0.88), (0.22, y + 0.74), (0.28, y + 0.66)], m["metal"], segs=12, center=(x, 0, z),
                         tiles_around=4, tile_up=1.0))
    out.append(F.box((x - 0.03, y + 0.85, z - 0.03), (x + 0.03, y + 1.4, z + 0.03), m["metal"]))
    if arm is not None:
        out.append(F.box((x - 0.04, y + 1.35, min(z, arm)), (x + 0.04, y + 1.43, max(z, arm)), m["metal"]))
    return F.concat(out)


def stairs_up(m, x0, x1, z0, y0, n=10, rise=0.5, run=0.8):
    """북쪽(-z)으로 오르는 계단 (발판·챌판). 반환: 면, [(z_lo, z_hi, 단 높이)]."""
    out, steps = [], []
    for k in range(n):
        za, zb = z0 - run * k, z0 - run * (k + 1)
        yt = y0 + rise * (k + 1)
        out.append(F.plane((x0, yt, za), (x1 - x0, 0, 0), (0, 0, zb - za), m["wood"], tile=(1, 1)).flipped())
        out.append(F.plane((x0, yt - rise, za), (x1 - x0, 0, 0), (0, rise, 0), m["wood_l"], tile=(1, 1)))
        steps.append((zb, za, yt))
    return F.concat(out), steps


# ---------------------------------------------------------------- 방 전체

def room_faces(m):
    out = []
    yt = Y0 + H
    # 바닥·천장
    za, zb = ZSTEP
    out.append(F.plane((X0, YF, ZS), (X1 - X0, 0, 0), (0, 0, zb - ZS), m["floor"], tile=(2, 2)))
    out.append(F.plane((X0, Y0, za), (X1 - X0, 0, 0), (0, 0, ZB - za), m["floor"], tile=(2, 2)))
    for k in range(4):                              # 네 단 (반 칸씩, 북쪽으로 내려감)
        z1 = zb - (zb - za) * k / 4
        z0 = zb - (zb - za) * (k + 1) / 4
        y = YF - 0.5 * (k + 1)
        out.append(F.plane((X0, y, z1), (X1 - X0, 0, 0), (0, 0, z0 - z1), m["wood"], tile=(2, 1)))
        out.append(F.plane((X1, y, z1), (X0 - X1, 0, 0), (0, 0.5, 0), m["wood_l"], tile=(2, 1)))
    out.append(F.plane((X0, yt, ZB), (X1 - X0, 0, 0), (0, 0, ZS - ZB), m["wood"], tile=(2, 2)))
    for z in np.arange(ZB + 2, ZS, 4.0):          # 천장 들보
        out.append(F.box((X0, yt - 0.7, z - 0.35), (X1, yt, z + 0.35), m["wood"], faces="yzZ"))
    # 북쪽 벽: 원화 구간
    for i, (a, b) in enumerate(BAYS):
        out.append(shelf_wall(m, a, b, Y0 + 1.0, yt - 1.0, ZB, 1, seed=i))
    for i, (a, b, prot, cap) in enumerate(PILLARS):
        x = (a + b) / 2
        r = (b - a) / 2
        out.append(F.box((a, Y0, ZB - 0.2), (b, yt, ZB + 0.05), m["wood"], faces="xXZ"))     # 기둥 뒤 판
        out.append(fluted_pillar(m, x, ZB + prot * 0.5, r * 0.9, Y0 + 0.5, yt - 1.2, capital=cap))
    # 계단 통로 (아치): 양옆 책장 벽, 위 아치 테두리, 계단
    sx0, sx1 = STAIR
    st, steps = stairs_up(m, sx0, sx1, ZB, Y0, n=8)
    out.append(st)
    zt = ZB - 0.8 * 8
    out.append(F.plane((sx0, Y0 + 4, zt), (sx1 - sx0, 0, 0), (0, 0, -4), m["wood"], tile=(1, 1)).flipped())  # 층계참
    out.append(_side_shelf(m, sx0, zt - 4, ZB, Y0, Y0 + H - 0.5, +1))
    out.append(_side_shelf(m, sx1, zt - 4, ZB, Y0, Y0 + H - 0.5, -1))
    out.append(F.plane((sx0, Y0 + H - 0.5, zt - 4), (sx1 - sx0, 0, 0), (0, 0, 4 + ZB - zt), m["wood"]).flipped())
    out.append(F.plane((sx0, Y0 + 4, zt - 4), (sx1 - sx0, 0, 0), (0, H - 4.5, 0), m["shelf"][0], tile=(1, 1)))
    # 아치 테 (반원)
    t = np.linspace(0, math.pi, 24)
    cx, rr = (sx0 + sx1) / 2, (sx1 - sx0) / 2 + 0.3
    arch = np.stack([cx + rr * np.cos(t), Y0 + 10.6 + rr * 0.8 * np.sin(t), np.full_like(t, ZB + 0.15)], 1)
    out.append(F.sweep(arch, 0.22, m["wood_l"], sides=6, step=0.3, tile_along=1.0))
    # 빛나는 벽감 (깊이 2, 문틀)
    nx0, nx1 = NICHE
    out.append(F.plane((nx0, Y0 + 1, ZB - 2), (nx1 - nx0, 0, 0), (0, 9, 0), m["lamp"], tile=(2, 9)).tint((0.75, 0.6, 0.45)))
    out.append(_side_shelf(m, nx0, ZB - 2, ZB, Y0 + 1, Y0 + 10, +1, books=False))
    out.append(_side_shelf(m, nx1, ZB - 2, ZB, Y0 + 1, Y0 + 10, -1, books=False))
    out.append(F.plane((nx0, Y0 + 10, ZB - 2), (nx1 - nx0, 0, 0), (0, 0, 2), m["wood"]).flipped())
    out.append(F.plane((nx0, Y0 + 10, ZB), (nx1 - nx0, 0, 0), (0, yt - Y0 - 10, 0), m["shelf"][1], tile=(1, 1)))
    out.append(F.box((nx0 - 0.2, Y0 + 0.5, ZB), (nx0, Y0 + 10.3, ZB + 0.2), m["wood_l"]))
    out.append(F.box((nx1, Y0 + 0.5, ZB), (nx1 + 0.2, Y0 + 10.3, ZB + 0.2), m["wood_l"]))
    out.append(F.box((nx0 - 0.2, Y0 + 10, ZB), (nx1 + 0.2, Y0 + 10.5, ZB + 0.25), m["wood_l"]))
    # 동·서 벽: 책장 칸 + 5칸마다 기둥 + 벽등
    lamps = []
    for x, y, z in LAMPS:
        out.append(bell_lamp(m, x, y, z, arm=ZB))
        lamps.append((x, y + 0.4, z))
    for side, x in ((1, X0), (-1, X1)):
        zs = np.arange(ZB + 1, ZS, 5.0)
        for z0, z1 in zip(zs[:-1], zs[1:]):
            fy = Y0 if z1 <= ZSTEP[0] + 0.5 else YF
            out.append(_side_shelf(m, x, z0 + 0.6, z1 - 0.6, fy, yt - 1, side, front=True))
        for z in zs:
            fy = Y0 if z <= ZSTEP[0] else YF
            out.append(fluted_pillar(m, x + side * 0.55, z, 0.5, fy, yt - 1.5, capital=Y0 + 9.5, flutes=10))
            if ZB + 3 < z < ZS - 3:
                lx = x + side * 1.4
                out.append(bell_lamp(m, lx, YF + 4.6, z, None))
                out.append(F.box((min(x, lx), YF + 6.4, z - 0.05), (max(x, lx), YF + 6.5, z + 0.05), m["metal"]))
                lamps.append((lx, YF + 5.0, z))
    # 남쪽 벽: 책장 + 검은 출구 문
    out.append(_back_shelf(m, X0, -1.6, ZS, YF, yt - 1))
    out.append(_back_shelf(m, 2.6, X1, ZS, YF, yt - 1))
    out.append(F.plane((2.6, YF, ZS), (-4.2, 0, 0), (0, 4.5, 0), m["dark"]))
    out.append(F.plane((2.6, YF + 4.5, ZS), (-4.2, 0, 0), (0, yt - YF - 4.5, 0), m["shelf"][2], tile=(1, 1)))
    out.append(F.box((-1.9, YF, ZS - 0.3), (2.9, YF + 4.9, ZS), m["wood_l"], faces="yzxX"))
    # 방 가운데: 받침 위 등 기둥 2줄 (3D 영상 02~05) + 책상
    for x in (-5.5, 6.5):
        for z in (4.0, 14.0):
            out.append(F.box((x - 0.7, YF, z - 0.7), (x + 0.7, YF + 1.6, z + 0.7), m["wood"]))
            out.append(F.box((x - 0.8, YF + 1.6, z - 0.8), (x + 0.8, YF + 1.8, z + 0.8), m["wood_l"]))
            out.append(fluted_pillar(m, x, z, 0.35, YF + 1.8, YF + 5.2, flutes=8))
            out.append(bell_lamp(m, x, YF + 5.3, z))
            lamps.append((x, YF + 5.6, z))
    out.append(desk(m, 0.5, 9.0))
    lamps.append((-0.4, YF + 2.2, 9.0))
    return out, lamps


def desk(m, x, z):
    """3D 영상: 등과 책이 놓인 넓은 책상 + 의자."""
    out = [F.box((x - 2.2, YF + 1.0, z - 0.9), (x + 2.2, YF + 1.15, z + 0.9), m["wood_l"])]
    for dx in (-2.0, 2.0):
        for dz in (-0.7, 0.7):
            out.append(F.box((x + dx - 0.1, YF, z + dz - 0.1), (x + dx + 0.1, YF + 1.0, z + dz + 0.1), m["wood"]))
    out.append(bell_lamp(m, x - 0.9, YF + 1.15, z - 0.2).scale(0.5, origin=(x - 0.9, YF + 1.15, z - 0.2)))
    for i, (bx, h) in enumerate(((0.3, 0.3), (0.8, 0.45), (1.3, 0.2))):
        out.append(F.box((x + bx - 0.2, YF + 1.15, z - 0.4), (x + bx + 0.2, YF + 1.15 + h, z + 0.1), m["shelf"][i]))
    out.append(F.plane((x - 0.3, YF + 1.16, z + 0.2), (0.6, 0, 0), (0, 0, 0.45), m["paper"]).flipped())
    # 의자 (북쪽, 남쪽을 봄)
    out.append(F.box((x - 0.4, YF + 0.55, z - 1.8), (x + 0.4, YF + 0.65, z - 1.0), m["wood"]))
    out.append(F.box((x - 0.4, YF + 0.65, z - 1.85), (x + 0.4, YF + 1.7, z - 1.75), m["wood"]))
    return F.concat(out)


def _side_shelf(m, x, za, zb, y0, y1, facing, books=True, front=False):
    """x 자리 벽면의 책장 (facing +1 = +x 를 봄, z za..zb). x-y 평면(+z 를 봄)에서 만들어 y 축으로 돌림."""
    a, b = (-zb, -za) if facing > 0 else (za, zb)
    seed = int(abs(za * 7 + x * 3)) % 97
    q = shelf_wall(m, a, b, y0, y1, 0.0, 1, seed=seed) if books else \
        F.plane((a, y0, 0.0), (b - a, 0, 0), (0, y1 - y0, 0), m["wood"], tile=(1, 1))
    return q.rotate("y", 90 if facing > 0 else -90).translate((x, 0, 0))


def _back_shelf(m, xa, xb, z, y0, y1):
    """남쪽 벽 (북쪽을 봄)."""
    return shelf_wall(m, xa, xb, y0, y1, z, -1, seed=int(abs(xa * 5)) % 97)


def build(b, d):
    """방 형체 + 충돌 + 빛. 반환: 도착 자리."""
    lay = b.form("lobby")
    m = mats()
    faces, lamps = room_faces(m)
    lights = [(p, (1.25, 0.82, 0.48), 9.0) for p in lamps]
    lights.append(((NICHE[0] + 1, Y0 + 4, ZB - 1), (0.9, 0.62, 0.36), 7.0))
    baked = [F.bake_points(q, lights, ambient=(0.32, 0.22, 0.16), ao_floor=Y0) for q in faces]
    # 등 자체는 굽지 않음 (빛나는 재질은 제 색)
    lampm = {m["lamp"]}
    for i, q in enumerate(baked):
        sel = np.isin(faces[i].M, list(lampm))
        q.C[sel] = faces[i].C[sel]
    parts = [F.subdivide(q, 1.0) for q in baked]
    from tools import artfit as A
    proj = F.project_scene(parts, CAM, m["art"], min_facing=0.03, zres=(850, 478), min_seen=3)
    for q in proj:
        lay.add(q)
    collision(d)
    for x, y, z in lamps:
        p = (int(math.floor(x)), int(y), int(math.floor(z)))
        if d.get(*p) == "minecraft:air":
            d.set(*p, "minecraft:light[level=12]")
    return ARRIVE


SPACE = "lobby"
PREVIEW_CAMS = [("남쪽에서 본 방 (책상·등 기둥)", F.Camera((0.5, YF + 1.62, 20.0), 180.0, -5.0)),
                ("북쪽에서 남쪽 (출구)", F.Camera((0.5, YF + 1.62, -10.0), 0.0, 0.0)),
                ("계단 통로 앞", F.Camera((1.0, Y0 + 1.62, -14.5), 160.0, -25.0))]


def preview(b):
    build(b, b.dim("lobby"))


def _column(d, x0, x1, z, top):
    """z 줄의 바닥을 높이 top 까지 (온 칸 barrier + 반 칸)."""
    full = int(math.floor(top - Y0 + 1e-6))
    if full > 0:
        d.fill(x0, Y0, z, x1, Y0 + full - 1, z, "minecraft:barrier")
    if top - Y0 - full > 0.25:
        d.fill(x0, Y0 + full, z, x1, Y0 + full, z, F.HALF_SOLID)


def collision(d):
    """걷는 곳·벽 (barrier) + 계단·단 반 칸."""
    yt = int(Y0 + H)
    x0, x1, zb, zs = int(X0) - 1, int(X1), int(ZB) - 1, int(ZS)
    d.fill(x0, Y0 - 1, zb - 12, x1, Y0 - 1, zs, "minecraft:barrier")          # 바닥 (계단 통로 아래까지)
    d.fill(x0, yt, zb - 12, x1, yt, zs, "minecraft:barrier")                   # 천장
    for x in (x0, x1):
        d.fill(x, Y0, zb, x, yt, zs, "minecraft:barrier")
    d.fill(x0, Y0, zs, x1, yt, zs, "minecraft:barrier")
    sx0, sx1 = int(math.floor(STAIR[0])), int(math.floor(STAIR[1] - 1e-6))
    nx0, nx1 = int(math.floor(NICHE[0])), int(math.floor(NICHE[1] - 1e-6))
    d.fill(x0, Y0, zb, x1, yt, zb, "minecraft:barrier")
    d.fill(sx0, Y0, zb, sx1, yt - 1, zb, "minecraft:air")                       # 계단 통로 입구
    # 계단 통로 (북쪽으로 0.5씩 오름, 8단) + 층계참 + 양옆 벽
    zt = ZB - 0.8 * 8
    for z in range(int(ZB) - 1, int(zt) - 5, -1):
        top = min(Y0 + 4.0, Y0 + 0.5 * math.ceil((ZB - (z + 0.5)) / 0.8))
        _column(d, sx0, sx1, z, top)
    d.fill(sx0 - 1, Y0, int(zt) - 5, sx0 - 1, yt, zb, "minecraft:barrier")
    d.fill(sx1 + 1, Y0, int(zt) - 5, sx1 + 1, yt, zb, "minecraft:barrier")
    d.fill(sx0, Y0, int(zt) - 5, sx1, yt, int(zt) - 5, "minecraft:barrier")
    # 내려가는 네 단 + 방 바닥 (YF = Y0 + 2)
    za, zb2 = ZSTEP
    for z in range(int(za), zs):
        zc = z + 0.5
        top = YF if zc >= zb2 else Y0 + 0.5 * math.ceil((zc - za) / ((zb2 - za) / 4))
        _column(d, x0 + 1, x1 - 1, z, min(top, YF))
    # 받침 기둥·책상
    for x in (-5.5, 6.5):
        for z in (4.0, 14.0):
            d.fill(int(math.floor(x - 0.7)), YF, int(math.floor(z - 0.7)), int(math.floor(x + 0.6)), YF + 5,
                   int(math.floor(z + 0.6)), "minecraft:barrier")
    d.fill(-2, YF, 8, 2, YF, 9, "minecraft:barrier")
    # 출구 문 (남쪽, x -1..1)
    d.fill(-1, YF, zs, 1, YF + 3, zs, "minecraft:air")
