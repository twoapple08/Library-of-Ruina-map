"""말쿠트 방 (역사의 층 지정사서 방) — 자유 형체 판. reference/역사의 층 지정사서 방.png

천장까지 닿는 책장 칸(사이 기둥에 가는 금빛 빛줄), 아래 칸엔 책 더미, 앞쪽 큰 책상 + 높은 등받이 의자 둘·펼친 책,
오른쪽 책장 틈으로 쏟아지는 금빛(그 안 헤링본 바닥과 책장, 책 더미), 오른쪽 앞 짙은 기둥.
도착(CAM): 남쪽 한 칸 높은 단에서 북쪽 책장을 봄 (원화는 세로선이 나란함 → 수평 시선).
"""
from __future__ import annotations

import math

import numpy as np

from tools import form_textures as T
from tools import forms as F

Y0 = 64
OX = 4000
ART = "reference/역사의 층 지정사서 방.png"
CAM = F.Camera((OX + 0.5, Y0 + 1 + 1.62, 8.0), 180.0, 0.0)
ARRIVE = (OX + 0.5, Y0 + 1, 8.0, 180.0, 0.0)
X0, X1, ZB, ZS, H = OX - 12.0, OX + 13.0, 0.0, 14.0, 12.0
SEAMS = [OX - 7.4, OX - 3.2, OX + 1.2, OX + 4.7]            # 기둥 (금빛 줄) x
GAP = (OX + 1.4, OX + 4.5)                                  # 금빛 틈 (북쪽 벽 뚫림)
UP = np.array([0, 1.0, 0])


def mats():
    m = {}
    m["art"] = F.mat("hroom_art", T.art("art/history_room", ART), emissive=True, flat=True, ao=False)
    dark = [(70, 46, 32), (52, 36, 28), (96, 70, 46), (60, 50, 44), (110, 80, 56), (44, 40, 40)]
    m["shelf"] = [F.mat(f"hroom_shelf{i}", T.shelf(f"hroom_shelf{i}", dark, wood=(56, 36, 24), seed=80 + i,
                                                    dark_back=(16, 10, 8)), emissive=True, flat=True, ao=False)
                  for i in range(3)]
    m["wood"] = F.mat("hroom_wood", T.wood("hroom_wood", (30, 20, 14), (78, 52, 34), seed=81), emissive=True, flat=True,
                      ao=False)
    m["floor"] = F.mat("hroom_floor", T.herringbone("hroom_floor", (54, 34, 22), (120, 80, 50), seed=82),
                       emissive=True, flat=True, ao=False)
    m["seam"] = F.mat("hroom_seam", T.glow("hroom_seam", (255, 210, 130)), emissive=True, flat=True, ao=False, glow=3)
    m["gold"] = F.mat("hroom_gold", T.glow("hroom_gold", (255, 196, 96)), emissive=True, flat=True, ao=False, glow=3)
    m["haze"] = F.mat("hroom_haze", T.glow("hroom_haze", (255, 200, 110)), layer="translucent", emissive=True,
                      flat=True, ao=False)
    m["leather"] = F.mat("hroom_leather", T.wood("hroom_leather", (24, 18, 16), (60, 46, 38), seed=83, grain=False),
                         emissive=True, flat=True, ao=False)
    m["paper"] = F.mat("hroom_paper", T.paper("hroom_paper", c=(226, 214, 186), seed=84), emissive=True, flat=True,
                       ao=False)
    m["book"] = [F.mat(f"hroom_book{i}", T.flat(f"hroom_book{i}", c), emissive=True, flat=True, ao=False)
                 for i, c in enumerate([(90, 60, 40), (70, 50, 40), (130, 100, 70), (60, 44, 36)])]
    return m


def shelf_face(m, x0, x1, y0, y1, z, k, facing=1):
    return F.plane((x0 if facing > 0 else x1, y0, z), ((x1 - x0) * facing, 0, 0), (0, y1 - y0, 0), m["shelf"][k % 3],
                   tile=(1.2, 1.2))


def book_stack(m, rng, x, y, z, n):
    out = []
    for i in range(n):
        w, d, h = rng.uniform(0.5, 0.8), rng.uniform(0.35, 0.55), rng.uniform(0.08, 0.15)
        out.append(F.box((-w / 2, 0, -d / 2), (w / 2, h, d / 2), m["book"][int(rng.integers(4))]).rotate(
            "y", rng.uniform(-20, 20)).translate((x, y, z)))
        y += h
    return F.concat(out), y


def faces(m, rng):
    out = []
    yt = Y0 + H
    # 바닥·천장·단
    out.append(F.plane((X0, Y0, ZS), (X1 - X0, 0, 0), (0, 0, ZB - ZS), m["floor"], tile=(2, 2)))
    out.append(F.plane((X0, yt, ZB), (X1 - X0, 0, 0), (0, 0, ZS - ZB), m["wood"], tile=(2, 2)))
    out.append(F.box((OX - 3, Y0, 7.0), (OX + 4, Y0 + 1, ZS), m["wood"], faces="yYxXz"))
    # 북쪽 벽: 책장 칸 (금빛 틈 제외) + 기둥 + 금빛 줄
    xs = [X0] + SEAMS + [X1]
    for i, (a, b) in enumerate(zip(xs[:-1], xs[1:])):
        a2, b2 = a + 0.35, b - 0.35
        if a2 >= GAP[0] - 0.5 and b2 <= GAP[1] + 0.5:
            continue
        out.append(shelf_face(m, a2, b2, Y0 + 1.2, yt, ZB - 0.5, i))
        for y in np.arange(Y0 + 1.2, yt, 1.2):                     # 선반 판 앞 모서리
            out.append(F.box((a2, y - 0.08, ZB - 0.5), (b2, y + 0.08, ZB), m["wood"], faces="yYZ"))
        out.append(F.box((a2, Y0, ZB - 0.5), (b2, Y0 + 1.2, ZB), m["wood"], faces="Y"))
        # 아래 칸 책 더미
        for x in np.arange(a2 + 0.5, b2 - 0.4, 0.9):
            q, _ = book_stack(m, rng, x, Y0, ZB - 0.25, int(rng.integers(2, 6)))
            out.append(q)
    for x in SEAMS:
        out.append(F.box((x - 0.35, Y0, ZB - 0.6), (x + 0.35, yt, ZB + 0.25), m["wood"], faces="xXZ"))
        out.append(F.plane((x - 0.05, Y0 + 0.5, ZB + 0.27), (0.1, 0, 0), (0, H - 1, 0), m["seam"], tile=(1, 4)))
    # 금빛 틈 너머: 깊은 통로 (헤링본 바닥, 양옆 책장, 끝 빛 벽, 빛 안개, 책 더미)
    ga, gb = GAP
    out.append(F.plane((ga, Y0, ZB), (gb - ga, 0, 0), (0, 0, -14), m["floor"], tile=(2, 2)).tint((1.6, 1.3, 0.9)))
    for x, f in ((ga, 1), (gb, -1)):
        q = F.plane((x, Y0, ZB - 14 if f > 0 else ZB), (0, 0, 14 * f), (0, H, 0), m["shelf"][1], tile=(1.2, 1.2))
        out.append(q.tint((1.5, 1.2, 0.8)))
    out.append(F.plane((ga, Y0, ZB - 14), (gb - ga, 0, 0), (0, H, 0), m["gold"], tile=(3, 3)))
    for k in range(4):
        out.append(F.plane((ga, Y0, ZB - 2 - k * 3), (gb - ga, 0, 0), (0, H, 0), m["haze"], tile=(3, 3))
                   .tint((1, 1, 1), 0.16))
    for z in (-2.0, -5.0, -9.0):
        q, _ = book_stack(m, rng, ga + 0.9, Y0, z, int(rng.integers(4, 9)))
        out.append(q.tint((1.5, 1.2, 0.8)))
    # 동·서·남 벽 (책장)
    for x, f in ((X0, 1), (X1, -1)):
        out.append(F.plane((x, Y0, ZS if f > 0 else ZB), (0, 0, (ZB - ZS) * f), (0, H, 0), m["shelf"][2], tile=(1.2, 1.2)))
    out.append(F.plane((X1, Y0, ZS), (X0 - X1, 0, 0), (0, H, 0), m["shelf"][0], tile=(1.2, 1.2)))
    # 오른쪽 앞 짙은 기둥
    out.append(F.box((OX + 8.6, Y0, 3.0), (OX + 10.6, yt, 5.0), m["wood"]).tint((0.45, 0.4, 0.38)))
    # 책상 + 의자 둘 + 펼친 책·책 더미
    dx0, dx1, dz0, dz1 = OX - 4.6, OX + 1.9, 2.6, 4.6
    out.append(F.box((dx0, Y0 + 0.9, dz0), (dx1, Y0 + 1.05, dz1), m["wood"]))
    out.append(F.box((dx0 + 0.2, Y0, dz0 + 0.2), (dx1 - 0.2, Y0 + 0.9, dz1 - 0.2), m["wood"], faces="xXzZ")
               .tint((0.6, 0.6, 0.6)))
    for cx in (OX - 2.4, OX + 1.0):
        out.append(F.box((cx - 0.6, Y0 + 0.5, 1.2), (cx + 0.6, Y0 + 0.62, 2.4), m["leather"]))
        out.append(F.box((cx - 0.65, Y0 + 0.62, 1.05), (cx + 0.65, Y0 + 2.1, 1.3), m["leather"]))
        for lx in (-0.5, 0.5):
            out.append(F.box((cx + lx - 0.06, Y0, 1.3), (cx + lx + 0.06, Y0 + 0.5, 1.42), m["wood"]))
    out.append(F.plane((OX - 3.8, Y0 + 1.06, 3.9), (1.6, 0, 0), (0, 0, -0.9), m["paper"]).rotate(
        "z", 4, origin=(OX - 3.0, Y0 + 1.06, 3.5)))
    for x in (OX - 1.0, OX - 0.3, OX + 0.6):
        q, _ = book_stack(m, rng, x, Y0 + 1.05, 3.4, int(rng.integers(2, 5)))
        out.append(q)
    # 오른쪽 바닥 책 더미 (원화 오른쪽 아래)
    for _ in range(14):
        x, z = rng.uniform(OX + 4.5, OX + 8.4), rng.uniform(1.0, 6.5)
        q, _ = book_stack(m, rng, x, Y0, z, int(rng.integers(3, 12)))
        out.append(q)
    return out


def build(b, d):
    lay = b.form("history")
    rng = np.random.default_rng(551)
    m = mats()
    fs = faces(m, rng)
    for j in range(7):
        fs.append(F.box((OX-7+j*2, Y0+.1, ZB+1), (OX-6.7+j*2, Y0+.8, ZB+1.6), m['leather']))
    lights = [((OX + 3.0, Y0 + 5, ZB - 6), (1.5, 1.1, 0.6), 18.0)]
    lights += [((x, Y0 + 6, ZB + 0.5), (0.5, 0.36, 0.2), 4.0) for x in SEAMS]
    glow = [m["seam"], m["gold"], m["haze"]]
    baked = []
    for q in fs:
        bq = F.bake_points(q, lights, ambient=(0.45, 0.36, 0.28))
        sel = np.isin(q.M, glow)
        bq.C[sel] = q.C[sel]
        baked.append(F.subdivide(bq, 1.0))
    proj = F.project_scene(baked, CAM, m["art"], min_facing=0.1, zres=(1000, 562), min_seen=3)
    for q in proj:
        lay.add(q)
    yt = int(Y0 + H)
    d.fill(int(X0) - 1, Y0 - 1, int(ZB) - 15, int(X1), Y0 - 1, int(ZS), "minecraft:barrier")
    d.fill(int(X0) - 1, yt, int(ZB) - 15, int(X1), yt, int(ZS), "minecraft:barrier")
    for x in (int(X0) - 1, int(X1)):
        d.fill(x, Y0, int(ZB) - 1, x, yt, int(ZS), "minecraft:barrier")
    d.fill(int(X0) - 1, Y0, int(ZS), int(X1), yt, int(ZS), "minecraft:barrier")
    d.fill(int(X0) - 1, Y0, int(ZB) - 1, int(X1), yt, int(ZB) - 1, "minecraft:barrier")
    ga, gb = int(GAP[0]), int(GAP[1])
    d.fill(ga + 1, Y0, int(ZB) - 1, gb - 1, yt - 1, int(ZB) - 1, "minecraft:air")      # 틈으로 들어갈 수 있게
    d.fill(ga, Y0, int(ZB) - 15, ga, yt, int(ZB) - 1, "minecraft:barrier")
    d.fill(gb, Y0, int(ZB) - 15, gb, yt, int(ZB) - 1, "minecraft:barrier")
    d.fill(ga, Y0, int(ZB) - 15, gb, yt, int(ZB) - 15, "minecraft:barrier")
    d.fill(OX - 3, Y0, 7, OX + 3, Y0, int(ZS) - 1, "minecraft:barrier")              # 도착 단
    d.fill(int(OX - 4.6), Y0, 2, int(OX + 1.9), Y0, 4, "minecraft:barrier")          # 책상
    d.fill(OX + 8, Y0, 3, OX + 10, yt, 4, "minecraft:barrier")                       # 기둥
    for x in range(int(X0) + 2, int(X1) - 1, 6):
        for z in (3, 10):
            if d.get(x, Y0 + 8, z) == "minecraft:air":
                d.set(x, Y0 + 8, z, "minecraft:light[level=11]")
    d.set_biome(OX - 40, -40, OX + 40, 40, "ruina:history_room")
    return ARRIVE


SPACE = "history"
PREVIEW_CAMS = [("방 옆에서", F.Camera((OX - 9.0, Y0 + 1.62, 11.0), 215.0, 5.0)),
                ("금빛 틈 앞", F.Camera((OX + 3.0, Y0 + 1.62, 2.0), 180.0, -5.0))]


def preview(b):
    build(b, b.dim("history"))
