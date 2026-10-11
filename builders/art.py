"""예술의 층 (네짜흐). 접대 공간(쓰러진 거대 나무줄기) ↔ 지정사서 방 (철발판 F).

참고: reference/예술의 층 전경.png, reference/예술의 층 지정사서 방.png, PLAN.md 8절 나무위키 요약
("모든 구조물이 거대한 나무줄기, 배경에 눈 셋 달린 거대 괴생물체").

원화(전경): 쓰러진 거대 나무줄기가 무대 (윗면 나무껍질 바닥, 뒤 가장자리 부러진 그루터기 줄),
아래는 위가 비치는 연두빛 수면, 뒤로 책장이 박힌 거대 나무줄기들, 줄기 사이로 새는 연두·노랑 빛, 반딧불이.
원화(방): 덩굴·뿌리 감긴 책장, 사다리, 책 더미, 책장 위 작은 빛나는 정령들, 오른쪽 빛나는 문 안 이젤 그림
(실크해트·눈 셋 괴생물체), 가운데 왼쪽 작은 빛나는 문.

크기 (1536×400, 사람 기준): ① 나무줄기 무대 (x -200..200, 반지름 14, 윗면 폭 15, 서 있는 Y 110), 수면 Y 70
② 400 안쪽 거대 나무 14그루 (반지름 15~40, 속 빈 곳에 책장) ③ 먼 나무 + 눈 셋 괴생물체 실루엣 (DH)
"""
from __future__ import annotations

import math

import numpy as np

from tools import shapes as S

Y0 = 110
BX, LR = 200, 14          # 줄기 반길이, 반지름
YC = Y0 - 1 - 11          # 줄기 중심 높이 (윗면을 Y0-1 에서 평평하게 자름)
WATER = 70
ARRIVE_X = -150
ROOM_X = 4000
RY = 64
BARK = ["minecraft:dark_oak_log[axis=%s]", "minecraft:spruce_log[axis=%s]", "minecraft:dark_oak_log[axis=%s]",
        "minecraft:mangrove_log[axis=%s]"]
GLOW = "minecraft:verdant_froglight"


def log_bridge(d, rng):
    """쓰러진 나무줄기: 단면마다 원 껍질 (나무껍질, 길이 방향 결), 윗면은 Y0-1 에서 평평한 껍질 벗긴 나무, 양 끝은 부러짐."""
    bark = [d.id(b % "x") for b in BARK]
    top = [d.id(s) for s in ("minecraft:stripped_dark_oak_log[axis=x]", "minecraft:stripped_spruce_log[axis=x]",
                             "minecraft:stripped_oak_log[axis=x]")]
    zs = np.arange(-LR - 2, LR + 3)
    ys = np.arange(YC - LR - 2, Y0)
    Zg, Yg = np.meshgrid(zs, ys, indexing="ij")
    for x in range(-BX - 12, BX + 13):
        end = max(0, abs(x) - BX)                         # 끝은 들쭉날쭉하게 부러짐
        if end and S.hash01(np.array(x), seed=1201) < end / 12:
            continue
        wob = 1.2 * math.sin(x / 23) + 0.8 * math.sin(x / 7.3)     # 울퉁불퉁한 껍질
        r = np.hypot(Zg, Yg - YC)
        R = LR + wob * 0.4 + 0.6 * S.hash01(np.full_like(Zg, x // 3), (np.arctan2(Yg - YC, Zg) * 5).astype(int), seed=1202)
        shell = (r <= R) & (r > R - 1.6)
        flat = (Yg == Y0 - 1) & (r <= R)
        ids = np.full(Zg.shape, -1, np.int32)
        h = (S.hash01(np.full_like(Zg, x // 5), Zg, Yg // 2, seed=1203) * len(bark)).astype(int).clip(0, len(bark) - 1)
        ids[shell & (Yg < Y0 - 1)] = np.array(bark)[h][shell & (Yg < Y0 - 1)]
        ht = (S.hash01(np.full_like(Zg, (x + 50) // 6), Zg, seed=1204) * len(top)).astype(int).clip(0, len(top) - 1)
        ids[flat] = np.array(top)[ht][flat]
        ids[(Yg > Y0 - 1)] = -1
        d.place(x, int(ys[0]), int(zs[0]), ids.T[None, :, :])
    # 뒤(북쪽) 가장자리 부러진 그루터기 줄 (원화), 앞은 낮은 혹
    for x in range(-BX, BX + 1, 3):
        h = int(rng.integers(1, 8))
        z = -7 - int(rng.integers(0, 2))
        d.fill(x, Y0, z, x + int(rng.integers(0, 2)), Y0 + h, z, BARK[int(rng.integers(len(BARK)))] % "y")
        if rng.random() < 0.3:
            d.set(x, Y0 + h + 1, z, "minecraft:dark_oak_fence")
    # 아래로 늘어진 뿌리·잔가지 몇 개 (수면에 닿음)
    for x in range(-BX + 20, BX, 45):
        for dz in (-1, 1):
            p0 = np.array([x, YC - 6, dz * 9.0])
            p3 = np.array([x + rng.uniform(-20, 20), WATER - 2, dz * rng.uniform(16, 30)])
            pts = S.bezier(p0, p0 + [0, -8, dz * 6], p3 + [0, 10, 0], p3, 40)
            for p in pts:
                d.fill(int(p[0]), int(p[1]), int(p[2]), int(p[0]) + 1, int(p[1]) + 1, int(p[2]) + 1, BARK[0] % "y")


def water(d, R=380):
    """연두빛 수면 (실제 물, 아래 진흙) — 쉐이더에서 위가 비침."""
    d.fill(-R, WATER - 1, -R, R, WATER - 1, R, "minecraft:mud")
    d.fill(-R, WATER, -R, R, WATER, R, "minecraft:water")


def tree(d, rng, cx, cz, r0, h, lean=(0.0, 0.0), niches=True, seed=0):
    """책장이 박힌 거대 나무줄기: 위로 가며 가늘어지는 둥근 껍질 + 껍질 곳곳 움푹한 칸(안에 책장) + 위 가지 + 아래 뿌리."""
    bark = np.array([d.id(b % "y") for b in BARK])
    shelf = d.id("minecraft:bookshelf")
    y0, y1 = WATER - 10, WATER + h
    R = int(r0 + 6)
    xs, zs = np.arange(-R, R + 1), np.arange(-R, R + 1)
    X, Z = np.meshgrid(xs, zs, indexing="ij")
    A = np.arctan2(Z, X)
    for y in range(y0, y1):
        t = (y - y0) / (y1 - y0)
        r = r0 * (1.15 - 0.45 * t) * (1 + 0.25 * max(0.0, 0.08 - t) / 0.08)   # 밑동은 넓게
        ox, oz = lean[0] * (y - y0), lean[1] * (y - y0)
        bump = 0.9 * np.sin(5 * A + y / 15 + seed) + 0.6 * np.sin(11 * A - y / 9 + 2 * seed)   # 울퉁불퉁 (싸게)
        rr = np.hypot(X - ox, Z - oz)
        shell = (rr <= r + bump) & (rr > r + bump - 1.25)
        ids = bark[(S.hash01((A * 9).astype(int), np.full_like(X, y // 4), seed=1211 + seed) * len(bark)).astype(int)
                   .clip(0, len(bark) - 1)]
        if niches:   # 껍질의 움푹한 칸 (책장): 각도·높이 격자에서 일부
            cell = S.hash01((A * 6 / math.pi).astype(int), np.full_like(X, y // 9), seed=1212 + seed) < 0.32
            inner = (rr <= r + bump - 2) & (rr > r + bump - 3.8)
            d.place(cx - R, y, cz - R, np.where(cell & inner, shelf, -1)[:, None, :].astype(np.int32))
            shell = shell & ~(cell & ((y % 9) not in (0, 8)))
        d.place(cx - R, y, cz - R, np.where(shell, ids, -1)[:, None, :].astype(np.int32))
    # 위 가지 (굵게 몇 갈래, 끝은 안개 속으로) — 관(Tube)으로 모아서 나중에 한 번에 껍질만 깎음
    top = np.array([cx + lean[0] * (y1 - y0), y1 - 5, cz + lean[1] * (y1 - y0)])
    tubes = []
    for k in range(int(rng.integers(3, 6))):
        a = rng.uniform(0, 2 * math.pi)
        d_ = np.array([math.cos(a), rng.uniform(0.3, 0.9), math.sin(a)])
        pts = S.resample(S.bezier(top - [0, h * 0.25, 0], top + d_ * r0 * 1.5, top + d_ * r0 * 3,
                                  top + d_ * r0 * 4.5 + [0, r0, 0], 40), 1.0)
        pts = pts[pts[:, 1] < d.min_y + d.height - 20]      # 차원 꼭대기 넘지 않게
        if len(pts) > 3:
            tubes.append(S.Tube(pts, np.linspace(r0 * 0.3, 1.5, len(pts))).with_(
                paint=BARK[0] % "y", name=f"branch{seed}_{k}"))
    # 줄기 사이로 새는 빛 (원화의 연두 빛 윤곽): 밑동 둘레 물가 빛
    for a in np.linspace(0, 2 * math.pi, 12, endpoint=False):
        x, z = int(cx + (r0 * 1.2 + 2) * math.cos(a)), int(cz + (r0 * 1.2 + 2) * math.sin(a))
        d.set(x, WATER, z, GLOW)
    return tubes


_BALLS = {}


def _ball_shell(r):
    """반지름 r 공의 껍질(두께 약 1.5) [x, y, z] bool."""
    if r not in _BALLS:
        g = np.arange(-r, r + 1)
        X, Y, Z = np.meshgrid(g, g, g, indexing="ij")
        dd = np.sqrt(X ** 2 + Y ** 2 + Z ** 2)
        _BALLS[r] = (dd <= r + 0.3) & (dd > r - 1.5)
    return _BALLS[r]


def creature(d, cx=0, cz=-560):
    """배경 안개 속 눈 셋 괴생물체 (방 이젤 그림): 실크해트, 세로로 선 눈 셋, 가늘고 긴 다리."""
    body_y0, body_y1, rw = WATER + 120, WATER + 330, 28
    d.fill(cx - rw, body_y0, cz - 10, cx + rw, body_y1, cz + 10, "minecraft:blackstone")
    d.fill(cx - rw + 1, body_y0 + 1, cz - 9, cx + rw - 1, body_y1 - 1, cz + 9, "minecraft:air")
    d.fill(cx - rw - 14, body_y1, cz - 22, cx + rw + 14, body_y1 + 4, cz + 22, "minecraft:black_concrete")   # 모자 챙
    d.fill(cx - rw + 6, body_y1 + 5, cz - 14, cx + rw - 6, body_y1 + 70, cz + 14, "minecraft:black_concrete")  # 모자
    d.fill(cx - rw + 7, body_y1 + 5, cz - 13, cx + rw - 7, body_y1 + 69, cz + 13, "minecraft:air")
    d.fill(cx - rw - 13, body_y1 + 1, cz - 21, cx + rw + 13, body_y1 + 3, cz + 21, "minecraft:air")
    for k, ey in enumerate((body_y1 - 40, body_y1 - 95, body_y1 - 150)):      # 눈 셋
        for x in range(-12, 13):
            for y in range(-9, 10):
                if (x / 12) ** 2 + (y / 9) ** 2 <= 1:
                    st = "minecraft:black_concrete" if (x / 5) ** 2 + (y / 5) ** 2 <= 1 else GOLD_EYE
                    d.set(cx + x, ey + y, cz + 11, st)
    for i, lx in enumerate((-22, -10, 2, 14, 24)):                            # 다리
        foot = (cx + lx * 2.2, WATER - 5, cz + (i % 2) * 12)
        pts = S.bezier(np.array([cx + lx, body_y0, cz]), np.array([cx + lx * 1.5, body_y0 - 40, cz + 8]),
                       np.array([foot[0], WATER + 30, foot[2]]), np.array(foot), 80)
        for p in pts:
            d.fill(int(p[0]), int(p[1]), int(p[2]), int(p[0]) + 1, int(p[1]), int(p[2]) + 1, "minecraft:blackstone")


GOLD_EYE = "minecraft:ochre_froglight"


# ---------------------------------------------------------------- 네짜흐 방
RW, RD, RH = 14, 11, 18


def netzach_room(d, ox=ROOM_X):
    """덩굴·뿌리 감긴 책장(사다리), 책 더미, 빛나는 큰 문(이젤 그림 — 다음 층 입구), 작은 빛나는 문, 빛나는 덩굴 열매."""
    y0, yt = RY, RY + RH
    xs, zs = np.arange(ox - RW, ox + RW + 1), np.arange(-RD, RD + 1)
    X, Z = np.meshgrid(xs, zs, indexing="ij")
    fl = np.where(S.hash01(X // 4, Z, seed=1301) < 0.5, d.id("minecraft:dark_oak_planks"), d.id("minecraft:spruce_planks"))
    fl = np.where(S.hash01(X, Z, seed=1302) < 0.12, d.id("minecraft:moss_block"), fl)
    d.place(ox - RW, y0 - 1, -RD, fl[:, None, :])
    x0, x1, z0, z1 = ox - RW - 1, ox + RW + 1, -RD - 1, RD + 1
    for (a0, b0, a1, b1) in ((x0, z0, x1, z0), (x0, z1, x1, z1), (x0, z0, x0, z1), (x1, z0, x1, z1)):
        d.fill(a0, y0, b0, a1, yt, b1, "minecraft:bookshelf")
        for y in range(y0 + 4, yt, 4):
            d.fill(a0, y, b0, a1, y, b1, "minecraft:dark_oak_planks")
    d.fill(x0, yt, z0, x1, yt, z1, "minecraft:dark_oak_planks")
    # 뿌리 (벽을 타고 내려옴)
    rng = np.random.default_rng(1311)
    for _ in range(14):
        x = ox + int(rng.integers(-RW, RW))
        z = z0 + 1 if rng.random() < 0.6 else z1 - 1
        y = yt - 1
        while y > y0:
            d.set(x, y, z, "minecraft:mangrove_roots")
            y -= 1
            if rng.random() < 0.25:
                x += int(rng.integers(-1, 2))
    # 사다리 (북쪽 책장 벽에 기댐)
    for x in (ox - 9, ox - 2):
        d.fill(x, y0, z0 + 1, x, yt - 3, z0 + 1, "minecraft:ladder[facing=south]")
    # 빛나는 큰 문 (북쪽 벽 동쪽): 빛 + 이젤 위 그림 (눈 셋 괴생물체, 블록 그림)
    dx0, dx1 = ox + 5, ox + 11
    d.fill(dx0, y0, z0, dx1, y0 + 10, z0, "minecraft:ochre_froglight")
    d.fill(dx0 + 1, y0 + 11, z0, dx1 - 1, y0 + 11, z0, "minecraft:ochre_froglight")
    d.fill(dx0 - 1, y0, z0 + 1, dx0 - 1, y0 + 11, z0 + 1, "minecraft:mangrove_roots")
    d.fill(dx1 + 1, y0, z0 + 1, dx1 + 1, y0 + 11, z0 + 1, "minecraft:mangrove_roots")
    ex = ox + 8
    d.fill(ex - 2, y0 + 3, z0 + 2, ex + 2, y0 + 8, z0 + 2, "minecraft:white_wool")          # 화폭
    for y, st in ((y0 + 8, "minecraft:black_wool"), (y0 + 7, "minecraft:gray_wool"), (y0 + 6, "minecraft:gray_wool"),
                  (y0 + 5, "minecraft:gray_wool"), (y0 + 4, "minecraft:gray_wool")):
        d.set(ex, y, z0 + 2, st)
    for y in (y0 + 7, y0 + 6, y0 + 5):
        d.set(ex - 1, y, z0 + 2, "minecraft:black_wool" if y != y0 + 6 else "minecraft:gray_wool")
    d.set(ex - 1, y0 + 3, z0 + 2, "minecraft:gray_wool")
    d.set(ex + 1, y0 + 3, z0 + 2, "minecraft:gray_wool")
    d.fill(ex - 2, y0, z0 + 3, ex - 2, y0 + 3, z0 + 3, "minecraft:spruce_fence")             # 이젤 다리
    d.fill(ex + 2, y0, z0 + 3, ex + 2, y0 + 3, z0 + 3, "minecraft:spruce_fence")
    # 작은 빛나는 문 (가운데 왼쪽)
    d.fill(ox - 6, y0, z0, ox - 5, y0 + 6, z0, "minecraft:ochre_froglight")
    # 책 더미
    for _ in range(30):
        x, z = ox + int(rng.integers(-RW + 1, RW)), int(rng.integers(-RD + 1, RD))
        if d.get(x, y0, z) != "minecraft:air" or (dx0 - 1 <= x <= dx1 + 1 and z < z0 + 6):
            continue
        for y in range(int(rng.integers(1, 3))):
            d.set(x, y0 + y, z, ["minecraft:brown_terracotta", "minecraft:green_terracotta",
                                 "minecraft:terracotta"][int(rng.integers(3))])
    # 빛나는 덩굴 열매 (천장에서)
    for _ in range(26):
        x, z = ox + int(rng.integers(-RW + 1, RW)), int(rng.integers(-RD + 1, RD))
        L = int(rng.integers(2, 7))
        if d.get(x, yt - 1, z) != "minecraft:air":
            continue
        for k in range(L):
            d.set(x, yt - 1 - k, z, "minecraft:cave_vines_plant[berries=true]" if k < L - 1 else
                  "minecraft:cave_vines[berries=true]")
    d.set_biome(ox - 40, -40, ox + 40, 40, "ruina:art_room")


def spirits(b, d, ox=ROOM_X, n=20, seed=1321):
    """작은 빛나는 정령: 블록 디스플레이 2개 (둥근 머리 + 몸통). 책장 칸·책 더미 위·바닥에."""
    rng = np.random.default_rng(seed)
    cmds = []
    spots = []
    for _ in range(n):
        side = rng.integers(3)
        if side == 0:   # 북쪽 책장 선반 앞
            x, y, z = ox + int(rng.integers(-RW + 1, RW)), RY + int(rng.integers(0, 4)) * 4, -RD
        elif side == 1:
            x, y, z = ox + int(rng.integers(-RW + 1, RW)), RY, int(rng.integers(-RD + 2, RD - 1))
        else:
            x, y, z = ox - RW, RY + int(rng.integers(0, 4)) * 4, int(rng.integers(-RD + 2, RD - 1))
        while d.get(x, y, z) != "minecraft:air" and y < RY + RH - 2:
            y += 1
        spots.append((x + 0.5, y, z + 0.5))
    for x, y, z in spots:
        for (oy, sx, sy, sz) in ((0.0, 0.22, 0.3, 0.22), (0.3, 0.32, 0.3, 0.32)):
            cmds.append(f"execute in {d.dim} run summon minecraft:block_display {x - sx / 2:.2f} {y + oy:.2f} {z - sz / 2:.2f} "
                        '{block_state:"minecraft:verdant_froglight",Tags:["ruina.spirit"],'
                        "brightness:{sky:15,block:15},transformation:{left_rotation:[0f,0f,0f,1f],"
                        f"right_rotation:[0f,0f,0f,1f],translation:[0f,0f,0f],scale:[{sx}f,{sy}f,{sz}f]}}}}")
        b.forceload.append((d.dim, x, z))
    b.links.entity_cmds += cmds


# ---------------------------------------------------------------- 조립

def build(b):
    from . import fragment as F
    d = b.dim("art")
    rng = np.random.default_rng(1401)
    water(d)
    log_bridge(d, rng)
    trees = [(-120, -70, 26, 330), (40, -95, 34, 340), (190, -60, 22, 300), (-260, -150, 38, 360), (300, -170, 30, 350),
             (-40, -220, 40, 370), (130, -260, 32, 360), (-150, 90, 24, 300), (120, 110, 28, 320), (-320, 60, 26, 310),
             (320, 40, 30, 330), (0, 180, 36, 340), (-230, 260, 30, 340), (240, 270, 34, 350)]
    tubes = []
    for i, (cx, cz, r, h) in enumerate(trees):
        tubes += tree(d, rng, cx, cz, r, h, lean=(rng.uniform(-0.04, 0.04), rng.uniform(-0.04, 0.04)), seed=i)
    for i in range(9):     # ③ 먼 나무 (책장 칸 없이)
        a = 2 * math.pi * i / 9 + 0.2
        tree(d, rng, int(560 * math.cos(a)), int(560 * math.sin(a)), int(rng.integers(36, 50)), int(rng.integers(340, 420)),
             niches=False, seed=20 + i)
    S.carve(d, S.Union(*tubes), shell=1, smooth=False, only_air=True)   # 가지 (가까운 나무만, 껍질만)
    creature(d)
    netzach_room(d)
    spirits(b, d)

    F.floor(b, d, "iplate", (F.IPLATE_P, F.IPLATE), "예술의 층", (ARRIVE_X + 0.5, Y0, 0.5, -90),
            (ROOM_X + 0.5, RY, RD - 2.5, 180), (-BX + 4, Y0, -6, -BX + 7, Y0 + 3, 6), "literature_door")
    # 네짜흐 방 빛나는 큰 문(이젤 그림) → 자연과학의 층. 돌아오면 문 앞에서 방 쪽(남쪽)을 봄
    F.door(b, d, "iplate", (ROOM_X + 5, RY, -RD, ROOM_X + 11, RY + 3, -RD), "natural_science_entrance",
           (ROOM_X + 3.5, RY, -RD + 6.5, 0), "예술의 층")
    b.extra_checks += [
        {"what": "네짜흐 방 바이옴", "cmd": f"execute in {d.dim} if biome {ROOM_X} {RY} 0 ruina:art_room", "expect": True},
        {"what": "정령 (block_display)", "cmd": f"execute in {d.dim} if entity @e[type=minecraft:block_display,tag=ruina.spirit]",
         "expect": True, "after_entities": True},
    ]


_GREEN = dict(sky=((150, 170, 60), (196, 214, 92)), fog=(160, 180, 70), stars=0, night=False)
PREVIEW = [
    {"file": "art_compare_stage.png", "ref": "예술의 층 전경.png", "cam": (0.5, Y0 + 4, 34), "look": (0.5, Y0 + 30, -120),
     "kw": dict(fov=80, max_dist=900, fog_dist=280, **_GREEN),
     "title": "예술의 층 — 원화(위) / 맵(아래): 나무줄기 옆에서 북쪽",
     "notes": ["쓰러진 거대 나무줄기 무대(뒤 그루터기 줄), 아래 연두빛 수면, 책장이 박힌 거대 나무들",
               "안개 속 멀리 눈 셋 괴생물체 (방 이젤 그림의 그것)"]},
    {"file": "art_compare_room.png", "ref": "예술의 층 지정사서 방.png", "cam": (ROOM_X - 3.5, RY + 2.5, RD - 1),
     "look": (ROOM_X + 3, RY + 5, -RD), "kw": dict(fov=80, max_dist=120, sky=((30, 40, 10), (60, 70, 20)),
                                                    fog=(60, 70, 20), fog_dist=60, stars=0),
     "title": "네짜흐 방 — 원화(위) / 맵(아래)",
     "notes": ["뿌리 감긴 책장·사다리, 빛나는 큰 문과 이젤 그림, 작은 빛나는 문, 빛나는 덩굴 열매",
               "작은 정령(디스플레이 엔티티)은 미리보기에 안 나옴"]},
]
