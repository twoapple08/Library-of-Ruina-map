"""공간 빌더 공용 형체 부품 (자유 형체 판).

- project_add: 형체 묶음들을 굽고(빛) 원화 투영해서 공간에 넣기 (가까이 촘촘, 멀리 굵게)
- art_sky: 원화 위쪽 + 고도별 색으로 그린 하늘
- glass_platform: 원화 시점에 서기 위한 거의 투명한 유리 발판 (+ barrier)
- gear / chain / building: 톱니(납작 원판), 처진 쇠사슬, 네온 빌딩 상자
"""
from __future__ import annotations

import math

import numpy as np

from tools import artfit as A
from tools import form_textures as T
from tools import forms as F

UP = np.array([0, 1.0, 0])


def keep_glow(baked: F.Quads, orig: F.Quads, glow_mats) -> F.Quads:
    sel = np.isin(orig.M, list(glow_mats))
    baked.C[sel] = orig.C[sel]
    return baked


def project_add(lay, cam, art_mat, near=(), far=(), lights=(), ambient=(0.4, 0.32, 0.26), glow_mats=(), masks=None,
                min_facing=0.15, zres=(1000, 562), min_seen=3, near_edge=1.0, far_edge=4.0, bake=True,
                far_min_facing=None):
    """near: 가까운 형체 (1블록 면), far: 먼 형체 (far_edge 면). lights 를 굽고 (bake_points), glow_mats 는 제 색.
    원화 투영 후 lay 에 넣음."""
    parts, edges = [], []
    for group, e in ((near, near_edge), (far, far_edge)):
        for q in group:
            if not len(q):
                continue
            bq = keep_glow(F.bake_points(q, lights, ambient=ambient), q, glow_mats) if bake else q
            parts.append(F.subdivide(bq, e))
            edges.append(e)
    if far_min_facing is None:
        proj = F.project_scene(parts, cam, art_mat, min_facing=min_facing, zres=zres, min_seen=min_seen, masks=masks)
    else:   # 먼 형체는 카메라를 정면으로 보는 면만 원화 (옆면에 원화가 번져 보이지 않게)
        zb = F.zbuffer(parts, cam, *zres)
        proj = [F.project_art(q, cam, art_mat, zres=zres, zb=zb, min_seen=min_seen,
                              min_facing=min_facing if e <= 1 else far_min_facing)[0] for q, e in zip(parts, edges)]
    for q, e in zip(proj, edges):
        lay.add(q, max_edge=max(e, 2.0) if e > 1 else 1.0)
    return proj


def art_sky(lay, name, cam, art_path, gradient, e_lo=-60.0, e_hi=90.0, city=None, cloud_e=(54.0, 62.0),
            below=(20, 14, 24), zenith=(30, 20, 40), clean=None, size=(2048, 1024), feather=0.2):
    from PIL import Image
    img = clean if clean is not None else Image.open(A.ROOT + "/" + art_path).convert("RGB")
    pano = A.sky_panorama(cam, img, size[0], size[1], e_lo=e_lo, e_hi=e_hi, gradient=gradient, feather=feather,
                          cloud_e=cloud_e, below=below, zenith=zenith, city=city)
    names = T.panorama(f"sky_{name}", pano, 512)
    mats = [[F.mat(f"sky_{name}_{r}_{c}", nm, emissive=True, flat=True, ao=False) for c, nm in enumerate(row)]
            for r, row in enumerate(names)]
    bm = F.mat(f"sky_{name}_below", T.flat(f"sky_{name}_below", below), emissive=True, flat=True, ao=False)
    lay.sky(A.sky_dome(mats, e_lo=e_lo, e_hi=e_hi, yaw=cam.yaw, below_mat=bm))


def glass_platform(d, glass_mat, trim_mat, x0, x1, z0, z1, y, alpha=0.12):
    """원화 시점에 서는 거의 투명한 유리 발판 (바닥 y, 테두리 금속선). 충돌 = barrier 한 겹 (y-1)."""
    out = [F.two_sided(F.plane((x0, y, z1), (x1 - x0, 0, 0), (0, 0, z0 - z1), glass_mat, tile=(1, 1)))
           .tint((1, 1, 1), alpha)]
    for a, b in (((x0, z0), (x1, z0)), ((x1, z0), (x1, z1)), ((x1, z1), (x0, z1)), ((x0, z1), (x0, z0))):
        out.append(F.sweep(np.array([[a[0], y, a[1]], [b[0], y, b[1]]]), 0.05, trim_mat, sides=4, step=2.0))
    d.fill(int(math.floor(x0)), int(y) - 1, int(math.floor(z0)), int(math.ceil(x1)) - 1, int(y) - 1,
           int(math.ceil(z1)) - 1, "minecraft:barrier")
    return F.concat(out)


def gear(center, normal, R, mat, teeth=16, thick=1.0, hole=0.35, spokes=6, tooth=0.14):
    """톱니 (납작한 원판 + 이빨 + 바퀴살 구멍). normal = 축 방향."""
    c = np.asarray(center, float)
    n = np.asarray(normal, float)
    n = n / np.linalg.norm(n)
    u = np.cross(n, [0, 1, 0] if abs(n[1]) < 0.9 else [1, 0, 0])
    u /= np.linalg.norm(u)
    v = np.cross(n, u)
    k = teeth * 4
    a = np.linspace(0, 2 * math.pi, k + 1)
    r_out = np.where((np.arange(k + 1) % 4 == 1) | (np.arange(k + 1) % 4 == 2), R * (1 + tooth), R)
    r_in = R * hole
    out = []
    for side in (-1, 1):
        o = c + n * side * thick / 2
        G = np.stack([np.stack([o + (r_in * np.cos(t)) * u + (r_in * np.sin(t)) * v for t in a]),
                      np.stack([o + (ro * np.cos(t)) * u + (ro * np.sin(t)) * v for t, ro in zip(a, r_out)])], 1)
        UV = np.stack([np.stack([np.cos(a) * 0.45 * r_in / R + 0.5, np.sin(a) * 0.45 * r_in / R + 0.5], -1),
                       np.stack([np.cos(a) * 0.48 + 0.5, np.sin(a) * 0.48 + 0.5], -1)], 1)
        out.append(F.grid(G, UV * 0.998 + 0.001, mat, N=np.broadcast_to(n * side, G.shape)))
    # 바깥 테두리 (이빨 옆면)
    rim = np.stack([np.stack([c - n * thick / 2 + (ro * np.cos(t)) * u + (ro * np.sin(t)) * v for t, ro in zip(a, r_out)]),
                    np.stack([c + n * thick / 2 + (ro * np.cos(t)) * u + (ro * np.sin(t)) * v for t, ro in zip(a, r_out)])],
                   1)
    nrm = np.stack([np.cos(a)[:, None] * u + np.sin(a)[:, None] * v] * 2, 1)
    UVr = np.stack([np.stack([np.arange(k + 1) / k * teeth % 1.0001, np.zeros(k + 1)], -1),
                    np.stack([np.arange(k + 1) / k * teeth % 1.0001, np.full(k + 1, 0.25)], -1)], 1)
    out.append(F.fit_tiles(F.grid(rim, np.clip(UVr, 0, 0.999), mat, N=nrm)))
    # 안쪽 축 구멍 테
    hub = np.stack([np.stack([c - n * thick * 0.7 + (r_in * np.cos(t)) * u + (r_in * np.sin(t)) * v for t in a]),
                    np.stack([c + n * thick * 0.7 + (r_in * np.cos(t)) * u + (r_in * np.sin(t)) * v for t in a])], 1)
    out.append(F.grid(hub, np.clip(UVr, 0, 0.999), mat, N=-np.stack([np.cos(a)[:, None] * u + np.sin(a)[:, None] * v] * 2, 1)))
    for s in range(spokes):
        t = s * 2 * math.pi / spokes
        p0 = c + r_in * (math.cos(t) * u + math.sin(t) * v)
        out.append(F.sweep(np.array([c, c + R * 0.95 * (math.cos(t) * u + math.sin(t) * v)]), R * 0.06, mat, sides=6,
                           step=max(0.5, R / 6)))
    return F.concat(out)


def chain(p0, p1, sag, mat, link=1.2, radius=0.12):
    """처진 쇠사슬 (고리가 번갈아 90도). sag = 가운데 처짐 (블록)."""
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
    L = np.linalg.norm(p1 - p0)
    n = max(2, int(L / link))
    t = np.linspace(0, 1, n + 1)
    pts = p0 + (p1 - p0) * t[:, None] - UP * (4 * sag * t * (1 - t))[:, None]
    out = []
    for i in range(n):
        a, b = pts[i], pts[i + 1]
        tan = b - a
        ln = np.linalg.norm(tan)
        if ln < 1e-6:
            continue
        tan /= ln
        side = np.cross(tan, UP)
        if np.linalg.norm(side) < 1e-6:
            side = np.array([1.0, 0, 0])
        side /= np.linalg.norm(side)
        if i % 2:
            side = np.cross(tan, side)
        c = (a + b) / 2
        tt = np.linspace(0, 2 * math.pi, 11)
        ring = c + (ln * 0.62) * np.cos(tt)[:, None] * tan + (ln * 0.32) * np.sin(tt)[:, None] * side
        out.append(F.sweep(ring, radius, mat, sides=4, step=max(0.2, ln / 5)))
    return F.concat(out)


def building(x0, z0, x1, z1, y0, y1, mat, top_mat=None, tile=(4.0, 4.0), faces="xXzZ"):
    q = F.box((x0, y0, z0), (x1, y1, z1), mat, tile=tile[0], faces=faces)
    if top_mat is not None:
        q = F.concat([q, F.plane((x0, y1, z1), (x1 - x0, 0, 0), (0, 0, z0 - z1), top_mat, tile=tile)])
    return q


def stair_collision(d, x0, x1, z_from, z_to, y_from, y_to):
    """z_from → z_to (칸 단위, 양 끝 포함) 로 가며 높이가 y_from → y_to 로 바뀌는 계단 충돌 (반 칸씩, 점프 없이).
    칸마다 꼭대기 높이를 0.5 단위로 반올림해 아래는 barrier, 반 칸이면 아래 반 칸 블록."""
    zs = list(range(z_from, z_to + (1 if z_to >= z_from else -1), 1 if z_to >= z_from else -1))
    n = len(zs)
    for i, z in enumerate(zs):
        top = y_from + (y_to - y_from) * (i + 1) / n
        top = round(top * 2) / 2
        base = int(math.floor(min(y_from, y_to))) - 1
        full = int(math.floor(top))
        if full > base + 1:
            d.fill(x0, base + 1, z, x1, full - 1, z, "minecraft:barrier")
        if top - full >= 0.5:
            d.fill(x0, full, z, x1, full, z, F.HALF_SOLID)


def glass_stairs(glass_mat, trim_mat, x0, x1, z_from, z_to, y_from, y_to, alpha=0.15):
    """보이는 유리 계단 (stair_collision 과 같은 칸)."""
    zs = list(range(z_from, z_to + (1 if z_to >= z_from else -1), 1 if z_to >= z_from else -1))
    n = len(zs)
    out = []
    for i, z in enumerate(zs):
        top = round((y_from + (y_to - y_from) * (i + 1) / n) * 2) / 2
        out.append(F.two_sided(F.plane((x0, top, z + 1), (x1 + 1 - x0, 0, 0), (0, 0, -1), glass_mat)).tint((1, 1, 1), alpha))
        out.append(F.sweep(np.array([[x0, top, z + (0 if z_to >= z_from else 1)], [x1 + 1, top, z + (0 if z_to >= z_from else 1)]]),
                           0.04, trim_mat, sides=4, step=2.0))
    return F.concat(out)
