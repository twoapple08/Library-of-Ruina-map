"""롤랑 방 (총류의 층 지정사서 방) — 자유 형체 판. reference/총류의 층 지정사서 방.png

높이 트인 잿빛 서고 (아래로도 깊음): 도착 턱 끝에서 내려다보면 깊은 구덩이, 양옆 빌딩만 한 책장 벽(안개 속으로 아득히 높음), 가운데 두 벽 사이 틈 너머 밝은 책장 벽과
뒤에서 비치는 빛, 그 앞 구덩이 바닥에서 촉수처럼 비틀려 솟은 거대한 책탑(위에서 오른쪽으로 꺾임) + 작은 촉수 둘,
흩날리는 먼지. 도착: 남쪽 턱 끝에서 북쪽 (정면, 원화처럼 세로선이 곧게).
원화 아래쪽까지 촉수 밑동이 이어지므로 바닥은 턱 아래 깊이 (PIT) 에 있음.
"""
from __future__ import annotations

import math

import numpy as np

from tools import artfit as A
from tools import form_textures as T
from tools import forms as F

from . import kit
from .general import tower

Y0 = 64
OX = 4000
ART = "reference/총류의 층 지정사서 방.png"
AW, AH = 850, 478
CAM = F.Camera((OX + 0.5, Y0 + 1.62, 29.5), 180.0, 0.0)
ARRIVE = (OX + 0.5, Y0, 29.5, 180.0, 0.0)
LEDGE = 28          # 도착 턱 앞 끝 (z)
PIT = Y0 - 70       # 구덩이 바닥
ZF = -20.0          # 양쪽 책장 빌딩 앞면
ZG = -70.0          # 틈 너머 밝은 책장 벽
H = 160.0
SPACE = "general"
TENTACLES = [  # 원화 (1000×562 기준) 가운데 선 [(x, y, 반폭)] 위 → 아래, 깊이 z
    ([(560, 128, 6), (540, 130, 12), (480, 135, 20), (440, 170, 28), (410, 250, 35), (380, 350, 40), (370, 450, 45),
      (380, 562, 55)], -38.0),
    ([(495, 270, 8), (505, 330, 18), (500, 450, 22), (510, 562, 25)], -46.0),
    ([(575, 420, 10), (545, 470, 20), (560, 562, 30)], -32.0),
]


def mats():
    m = {}
    m["art"] = F.mat("roland_room_art", T.art("art/general_room", ART), emissive=True, flat=True, ao=False)
    grey = [(96, 94, 92), (80, 78, 76), (120, 118, 114), (64, 62, 62), (140, 136, 130)]
    m["shelf"] = [F.mat(f"roland_room_shelf{i}", T.shelf(f"roland_room_shelf{i}", grey, wood=(84, 82, 80), seed=261 + i,
                                                    dark_back=(30, 30, 32)), emissive=True, flat=True, ao=False)
                  for i in range(2)]
    m["bright"] = F.mat("roland_room_bright", T.shelf("roland_room_bright", [(220, 214, 200), (200, 194, 182), (240, 232, 216)],
                                                wood=(230, 224, 210), seed=263, dark_back=(170, 164, 152)),
                        emissive=True, flat=True, ao=False, glow=3)
    # 공용 general.tower가 책층 윗표지에 사용하는 재질. 바닥과 별도로 둔다.
    m["slab"] = F.mat("roland_room_book_cover", T.flat("roland_room_book_cover", (84, 82, 80)),
                      emissive=True, flat=True, ao=False)
    m["books"] = [F.mat(f"gen_books{i}", T.book_stack(f"gen_books{i}", seed=252 + i), emissive=True, flat=True, ao=False)
                  for i in range(3)]
    m["floor"] = F.mat("roland_room_floor", T.stone_slab("roland_room_floor", (30, 30, 32), (70, 70, 74), seed=264), emissive=True,
                       flat=True, ao=False)
    m["light"] = F.mat("roland_room_light", T.glow("roland_room_light", (255, 226, 180)), layer="translucent", emissive=True,
                       flat=True, ao=False)
    m["haze"] = F.mat("roland_room_haze", T.glow("roland_room_haze", (120, 118, 116)), layer="translucent", emissive=True,
                      flat=True, ao=False)
    return m


def gap_x(view):
    """원화의 가운데 틈 (x 302~506 / 850) → 앞면 깊이 ZF 에서 월드 x."""
    p = view.at_z(np.array([302.0, 506.0]), np.array([239.0, 239.0]), ZF)
    return float(p[0][0]), float(p[1][0])


def faces(m, rng, view):
    out = []
    gx0, gx1 = gap_x(view)
    out.extend([F.box((OX-60,Y0-.35,LEDGE-.6),(OX+61,Y0+.05,LEDGE),m['floor']), F.box((OX-60,Y0-.3,41),(OX-59.6,Y0+.3,LEDGE),m['floor'])])
    out.append(F.plane((OX - 60, Y0, 41), (121, 0, 0), (0, 0, LEDGE - 41), m["floor"], tile=(4, 4)))
    out.append(F.plane((OX - 60, Y0, LEDGE), (121, 0, 0), (0, PIT - Y0, 0), m["shelf"][0], tile=(2, 2)))     # 턱 앞면
    out.append(F.box((OX - 60, Y0 - 0.4, LEDGE - 0.4), (OX + 61, Y0 + 0.05, LEDGE), m["floor"], tile=2.0, faces="zyY"))
    out.append(F.plane((OX - 120, PIT, LEDGE), (240, 0, 0), (0, 0, ZG - LEDGE), m["floor"], tile=(4, 4)))
    # 양쪽 빌딩만 한 책장 (앞면 + 틈 쪽 옆면), 칸막이 세로 기둥·가로 판
    for (xa, xb), side in (((OX - 120, gx0), -1), ((gx1, OX + 120), 1)):
        out.append(F.plane((xa, PIT, ZF), (xb - xa, 0, 0), (0, Y0 + H - PIT, 0), m["shelf"][0 if side < 0 else 1], tile=(2, 2)))
        xe = gx0 if side < 0 else gx1
        z0, z1 = (ZF, ZG) if side < 0 else (ZG, ZF)
        out.append(F.plane((xe, PIT, z0), (0, 0, z1 - z0), (0, Y0 + H - PIT, 0), m["shelf"][1], tile=(2, 2)))
    # 양옆 벽 (방 둘레), 뒤(남) 벽
    for x, f in ((OX - 60, 1), (OX + 61, -1)):
        z0, z1 = (40, ZF) if f > 0 else (ZF, 40)
        out.append(F.plane((x, PIT, z0), (0, 0, z1 - z0), (0, Y0 + H - PIT, 0), m["shelf"][0], tile=(2, 2)))
    out.append(F.plane((OX + 61, Y0, 41), (-121, 0, 0), (0, H, 0), m["shelf"][1], tile=(2, 2)))
    # 틈 너머 밝은 책장 벽 + 빛
    out.append(F.plane((gx0, PIT, ZG), (gx1 - gx0, 0, 0), (0, Y0 + H - PIT, 0), m["bright"], tile=(2, 2)))
    for k in range(4):
        out.append(F.plane((gx0, PIT, ZG + 3 + k * 6), (gx1 - gx0, 0, 0), (0, Y0 + H - PIT, 0), m["light"], tile=(4, 4))
                   .tint((1, 1, 1), 0.1))
    out.append(F.plane((OX - 61, Y0 + H, 41), (122, 0, 0), (0, 0, ZG - 41), m["haze"], tile=(16, 16)).flipped())  # 위 안개 천장
    for y in (PIT + 20, Y0 + 50, Y0 + 90, Y0 + 130):          # 안개 겹 (아래 구덩이 + 위 높이 트임)
        out.append(F.plane((OX - 60, y, ZG), (121, 0, 0), (0, 0, 41 - ZG), m["haze"], tile=(16, 16)).tint((1, 1, 1), 0.15))
    for _ in range(60):                                        # 책 더미 (턱 위 양옆, 구덩이 바닥)
        if rng.random() < 0.4:
            x, z, y = OX + rng.uniform(-55, 55), rng.uniform(LEDGE + 1, 39), Y0
            if abs(x - OX) < 6:
                continue
        else:
            x, z, y = OX + rng.uniform(-55, 55), rng.uniform(ZF + 2, LEDGE - 2), PIT
        for _k in range(int(rng.integers(2, 7))):
            w, d, h = rng.uniform(0.5, 0.9), rng.uniform(0.35, 0.6), rng.uniform(0.1, 0.2)
            out.append(F.box((-w / 2, 0, -d / 2), (w / 2, h, d / 2), m["books"][int(rng.integers(3))], tile=1.0)
                       .rotate("y", rng.uniform(0, 180)).translate((x, y, z)))
            y += h
    return out


def tentacles(m, rng, view):
    out = []
    for pts, z in TENTACLES:
        path = []
        for px, py, pr in pts:
            sx, sy = px * AW / 1000, py * AH / 562
            c = view.at_z(np.array([sx]), np.array([sy]), z)[0]
            path.append((c[0], c[1], c[2], max(0.4, pr * AW / 1000 * float(view.px_size(c)))))
        xb, yb, zb, rb = path[-1]
        path.append((xb, PIT - 1, zb, rb * 1.3))                # 구덩이 바닥까지
        out += tower(m, rng, path, layer=0.6)
    return out


def build(b, d):
    lay = b.form("general")
    rng = np.random.default_rng(2511)
    m = mats()
    view = A.ArtView(CAM, AW, AH)
    fs = faces(m, rng, view) + tentacles(m, rng, view)
    # 전망 턱의 연속적인 전면 모서리 마감.
    fs.append(F.box((OX-60,Y0-.4,LEDGE-.45),(OX+61,Y0+.06,LEDGE-.28),m['floor']))
    # 깊은 서고 전망턱의 두꺼운 가장자리.
    fs.append(F.box((OX-12,Y0-.35,LEDGE-.65),(OX+12,Y0+.08,LEDGE),m['floor']))
    for x in (OX-45,OX-30,OX+30,OX+45):
        fs.append(F.box((x,Y0-.2,LEDGE-.7),(x+3,Y0+.12,LEDGE),m['floor']))
    for j in range(6):
        fs.append(F.box((OX-6+j*2, Y0+.05, ZG+2), (OX-5.3+j*2, Y0+.35, ZG+2.5), m['floor']))
    lights = [((OX + 2, Y0 + 40, ZG + 4), (1.1, 0.95, 0.75), 70.0)]
    # 도착 턱은 정밀하게, 32블록 밖 서고·책탑은 기존 면을 불필요하게 1칸으로 더 쪼개지 않는다.
    # 실제 부품은 유지하며, 정적 분류이므로 접근 시 동적으로 세분화되는 LOD는 아니다.
    near, far = [], []
    eye = np.asarray(CAM.pos)
    for mesh in fs:
        lo, hi = mesh.bounds()
        distance = np.linalg.norm(eye - np.clip(eye, lo, hi))
        (far if distance > 32 else near).append(mesh)
    kit.project_add(lay, CAM, m["art"], near=near, far=far, far_edge=4.0, lights=lights, ambient=(0.45, 0.45, 0.47),
                    glow_mats=[m["bright"], m["light"], m["haze"]], min_facing=0.1)
    lay.emitter(F.Emitter((OX - 20, Y0 + 1, ZG, OX + 20, Y0 + 50, 30), rate=4.0, sprites=("ruina:block/form/paper_1",),
                          wind=(0.05, -0.05, 0.0), size=0.06, life=12.0, spin=0.2, color=(1.0, 0.92, 0.8), glow=True))
    yt = int(Y0 + H)
    x0, x1, z0, z1 = OX - 61, OX + 62, LEDGE - 1, 41           # 턱 위만 걸음 (구덩이 쪽은 보이지 않는 난간)
    d.fill(x0, Y0 - 1, LEDGE, x1, Y0 - 1, z1, "minecraft:barrier")
    d.fill(x0, Y0 + 30, z0, x1, Y0 + 30, z1, "minecraft:barrier")
    for x in (x0, x1):
        d.fill(x, Y0, z0, x, Y0 + 30, z1, "minecraft:barrier")
    for z in (z0, z1):
        d.fill(x0, Y0, z, x1, Y0 + 30, z, "minecraft:barrier")
    for x in range(OX - 50, OX + 51, 10):
        for z in range(LEDGE + 3, 40, 6):
            if d.get(x, Y0 + 6, z) == "minecraft:air":
                d.set(x, Y0 + 6, z, "minecraft:light[level=12]")
    d.set_biome(OX - 80, -100, OX + 80, 60, "ruina:general_room")
    return ARRIVE


PREVIEW_CAMS = [("턱에서 구덩이 내려다봄", F.Camera((OX + 10.0, Y0 + 1.62, 29.5), 165.0, 45.0)),
                ("턱 옆에서 올려다봄", F.Camera((OX - 30.0, Y0 + 1.62, 35.0), 160.0, -40.0))]


def preview(b):
    build(b, b.dim("general"))
