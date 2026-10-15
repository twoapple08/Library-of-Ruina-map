"""자유 형체 기반 시험대 (임시 — 외부 작업을 시작하면 지움).

외부 차원 구석 공중 (700, 500, 700) 에 떠 있는 작은 무대. 게임 테스트가 두 자리에서 찍음:
- ART 자리: 원화(도서관 외견)를 투영한 디오라마 정면 → 화면이 원화와 거의 같아야 함 (원화 투영 확인)
- SIDE 자리: 옆에서 본 모습 → 같은 면이 입체로 보임 + 비틀린 가지(나무껍질), 도는 톱니, 흔들리는 추, 빛나는 고리(BSL 발광),
  날리는 종이, 카메라를 따라오는 먼 산 띠 (움직임·파티클·배경 확인)
"""
from __future__ import annotations

import math

import numpy as np

from tools import form_textures as T
from tools import forms as F

C = (700, 500, 700)                      # 무대 기준 (바닥 윗면 y = 500)
ART_CAM = F.Camera((700.5, 501.62, 721.5), 180.0, 0.0, 70.0)   # 북쪽을 봄
SIDE_CAM = F.Camera((733.5, 507.62, 706.5), 258.0, 0.0, 70.0)
ART_POS = (700.5, 500.0, 721.5, 180.0)    # 게임 테스트 tp (발 위치, yaw)
SIDE_POS = (733.5, 506.0, 706.5, 258.0)


def build(b):
    d = b.dim("exterior")
    lay = b.form("exterior")
    cx, y0, cz = C

    # ---------------------------------------------- 발판 (바닐라 블록: 서 있을 자리)
    d.fill(697, y0 - 1, 719, 703, y0 - 1, 724, "minecraft:polished_deepslate")
    d.fill(728, y0 + 5, 703, 738, y0 + 5, 710, "minecraft:polished_deepslate")

    # ---------------------------------------------- 텍스처·재질
    art_sp = T.art("art/exterior", "reference/도서관 외견.png")
    art = F.mat("showcase_art", art_sp, emissive=True, flat=True, ao=False)
    bark = F.mat("bark", T.bark(), ao=True)
    stone = F.mat("stone_slab", T.stone_slab())
    metal = F.mat("metal", T.metal())
    lamp = F.mat("lamp_gold", T.glow(), emissive=True, flat=True, ao=False, glow=3)
    hills = F.mat("far_hills", T.flat("far_hills", (255, 255, 255)), emissive=True, flat=True, ao=False)
    T.paper("paper_0")
    T.paper("paper_1", c=(250, 236, 200), lines=False, seed=9)

    # ---------------------------------------------- 원화 투영 디오라마 (북쪽)
    ex, ey, ez = ART_CAM.pos
    back = F.revolve([(46, -40), (46, 46)], stone, segs=72, center=(ex, ey, ez), arc=(205, 335),
                     tiles_around=24, tile_up=4).flipped()       # 카메라를 감싸는 벽 (안쪽이 앞)
    ground = F.heightfield(ex - 40, ez - 44, ex + 40, ez - 3, lambda X, Z: y0 - 0.6 + 1.5 * np.sin(X * 0.15) * np.cos(Z * 0.2)
                           * np.clip((ez - 3 - Z) / 10, 0, 1), stone, step=1.0)
    tower = F.revolve([(7, -2), (6.5, 10), (5, 24), (3.5, 36), (0.5, 42)], bark, segs=32, center=(ex, y0, ez - 30),
                      tiles_around=8, tile_up=3)
    rocks = F.concat([F.ellipsoid((ex + dx, y0 + 1, ez - dz), (r, r * 0.7, r), stone, 12, 6)
                      for dx, dz, r in ((-12, 14, 3), (14, 18, 4), (-20, 26, 5), (9, 9, 2))])
    for q in F.project_scene([F.subdivide(q, 1.0) for q in (back, ground, tower, rocks)], ART_CAM, art):
        lay.add(q)

    # ---------------------------------------------- 입체 견본 (동쪽, SIDE 자리에서 봄)
    # 비틀린 가지: 땅에서 솟아 휘다가 끝이 말림
    t = np.linspace(0, 1, 120)
    ang = t * 3.2 * math.pi
    rad = 9 * (1 - t) ** 1.4 + 0.6
    path = np.stack([744 + 4 * t + rad * np.cos(ang) * t, y0 + 2 + 26 * np.sin(t * 2.2) ** 0.8, 700 + rad * np.sin(ang) * t], 1)
    lay.add(F.sweep(path, lambda s: 2.2 * (1 - s) ** 0.8 + 0.25, bark, sides=10, step=0.4, tile_along=2.0,
                    profile=lambda th: 1 + 0.08 * np.cos(th * 5)))
    # 마디 고리
    for s in (0.15, 0.3, 0.45):
        i = int(s * (len(path) - 1))
        lay.add(F.sweep(path[max(0, i - 2):i + 3], 2.2 * (1 - s) ** 0.8 + 0.6, bark, sides=10, step=0.2, tile_along=0.8))
    # 빛나는 고리 (BSL 발광)
    ring = np.stack([744 + 5 * np.cos(np.linspace(0, 2 * math.pi, 80)), np.full(80, y0 + 12.0),
                     712 + 5 * np.sin(np.linspace(0, 2 * math.pi, 80))], 1)
    lay.add(F.sweep(ring, 0.35, lamp, sides=8, step=0.3, tile_along=1.0))
    d.set(744, y0 + 12, 712, "minecraft:light[level=15]")
    for x, y, z in ((736, y0 + 8, 700), (744, y0 + 4, 706), (748, y0 + 14, 696), (730, y0 + 8, 712)):
        d.set(x, y, z, "minecraft:light[level=13]")
    # 받침 기둥 (돌판)
    lay.add(F.box((742, y0 - 2, 711), (746, y0 + 6, 713), stone, tile=2.0))
    lay.solid_box(742, y0 - 2, 711, 745, y0 + 5, 712)

    # 도는 톱니 (z축 회전, 20초 한 바퀴)
    teeth = 16
    prof = []
    for k in range(teeth * 4 + 1):
        a = k / (teeth * 4) * 2 * math.pi
        r = 6.0 if (k % 4) in (1, 2) else 5.0
        prof.append((r * math.cos(a), r * math.sin(a)))
    gear = _extrude(np.array(prof), 1.0, metal)
    hub = F.box((-1.2, -1.2, -0.8), (1.2, 1.2, 0.8), metal, tile=1.0)
    gpos = (752, y0 + 10, 704)
    lay.mover(F.Mover(gpos, F.concat([gear, hub]).translate((752.5, y0 + 10.5, 704.5)), (752.5, y0 + 10.5, 704.5),
                      "spin", (0, 0, 1), 20.0))
    # 흔들리는 추 (x축 진자, 4초 왕복, ±25도)
    rod = F.box((-0.15, -8, -0.15), (0.15, 0, 0.15), metal, tile=1.0)
    bob = F.ellipsoid((0, -8.5, 0), (1.2, 1.2, 1.2), metal, 12, 6)
    ppos = (738, y0 + 16, 696)
    piv = (738.5, y0 + 18.5, 696.5)
    lay.mover(F.Mover(ppos, F.concat([rod, bob]).translate(piv), piv, "swing", (1, 0, 0), 4.0, 25.0))
    lay.add(F.box((735, y0 + 18.6, 696), (742, y0 + 19.4, 697), stone, tile=1.0))      # 추를 매단 들보

    # 카메라를 따라오는 먼 산 띠 (반지름 220, 눈높이 아래~위)
    hz = []
    for k in range(97):
        a = k / 96 * 2 * math.pi
        hz.append(18 + 10 * math.sin(a * 5) + 6 * math.sin(a * 13 + 1))
    hz = np.array(hz)
    a = np.linspace(0, 2 * math.pi, 97)
    G = np.stack([np.stack([220 * np.cos(a), np.full(97, -40.0), 220 * np.sin(a)], 1),
                  np.stack([220 * np.cos(a), hz - 30, 220 * np.sin(a)], 1)], 1)
    UV = np.zeros(G.shape[:2] + (2,))
    UV[..., 1] = [[0, 1]] * 97
    band = F.grid(G, UV * 0.999, hills, N=np.broadcast_to(-G[:, :1] / 220, G.shape)).flipped()
    band = F.gradient_y(band, -40, 0, (0.08, 0.05, 0.16), (0.32, 0.2, 0.5))
    lay.mover(F.Mover((730, y0 + 1, 720), band, (730.5, y0 + 1.5, 720.5), "follow"))

    # 날리는 종이
    lay.emitter(F.Emitter((725, y0 + 4, 690, 760, y0 + 30, 720), rate=6.0,
                          sprites=("ruina:block/form/paper_0", "ruina:block/form/paper_1"), wind=(-0.4, -0.5, 0.2)))


def _extrude(poly2d: np.ndarray, depth: float, mat_id: int) -> F.Quads:
    """닫힌 다각형 (k,2) (x,y) 을 z 방향으로 두께 depth (가운데 0). 옆면 + 앞뒤 면(부채꼴)."""
    p = poly2d[:-1] if np.allclose(poly2d[0], poly2d[-1]) else poly2d
    k = len(p)
    z0, z1 = -depth / 2, depth / 2
    P3 = lambda xy, z: np.c_[xy, np.full(len(xy), z)]
    a, b = p, np.roll(p, -1, 0)
    side = np.stack([P3(a, z0), P3(b, z0), P3(b, z1), P3(a, z1)], 1)
    c = p.mean(0)
    cen = np.repeat(c[None], k, 0)
    front = np.stack([P3(cen, z1), P3(a, z1), P3(b, z1), P3(b, z1)], 1)
    back = np.stack([P3(cen, z0), P3(b, z0), P3(a, z0), P3(a, z0)], 1)
    q = F.Quads(np.concatenate([side, front, back]), M=mat_id)
    # 바깥 향하게: 옆면은 중심에서 멀어지는 쪽, 앞뒤는 ±z
    out = np.r_[np.c_[(a + b) / 2 - c, np.zeros(k)], np.tile([0, 0, 1.0], (k, 1)), np.tile([0, 0, -1.0], (k, 1))]
    fn = F.face_normals(q.P)
    flip = (fn * out).sum(-1) < 0
    q = F.concat([q.take(~flip), q.take(flip).flipped()])
    span = np.ptp(p, 0).max()
    q.UV = (q.P[..., :2] - p.min(0)) / span * 0.999
    q.N = F.face_normals(q.P)[:, None].repeat(4, 1)
    return q
