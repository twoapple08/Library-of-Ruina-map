"""원근 미리보기: 사람 눈높이 카메라에서 본 모습 (원화와 같은 구도로 비교용).

블록을 화면에 정사각형 점(크기 = 거리에 반비례)으로 찍고 Z버퍼로 가린다.
가까운 섹션은 1칸, 먼 섹션은 2·4칸 묶음 (속도). 밤하늘·별·초승달·안개·발광 번짐 포함.
"""
from __future__ import annotations

import math

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from .preview import Palette, _frame
from .render3d import _flags, _glow_lut
from .world import Dimension


def _gather(dim: Dimension, cam, near=170.0, mid=450.0, max_dist=1400.0):
    """lod별 (좌표 lod단위 (N,3), 팔레트 번호) 목록."""
    groups = {1: ([], []), 2: ([], []), 4: ([], [])}
    for (sx, sy, sz), a in dim.sections.items():
        c = np.array([sx * 16 + 8, sy * 16 + 8, sz * 16 + 8])
        dist = float(np.linalg.norm(c - cam))
        if dist > max_dist:
            continue
        k = 1 if dist < near else (2 if dist < mid else 4)
        n = 16 // k
        if k == 1:
            yzx = np.argwhere(a != 0)
            if not len(yzx):
                continue
            ids = a[a != 0]
        else:
            b = a.reshape(n, k, n, k, n, k).transpose(0, 2, 4, 1, 3, 5).reshape(n, n, n, k ** 3)
            order = np.argsort(-np.repeat(np.arange(k), k * k))
            bb = b[..., order]
            nz = bb != 0
            has = nz.any(-1)
            if not has.any():
                continue
            first = nz.argmax(-1)
            rep = np.take_along_axis(bb, first[..., None], -1)[..., 0]
            yzx = np.argwhere(has)
            ids = rep[has]
        g = yzx + np.array([sy * n, sz * n, sx * n])
        groups[k][0].append(np.stack([g[:, 2], g[:, 0], g[:, 1]], 1))
        groups[k][1].append(ids)
    out = {}
    for k, (xs, ids) in groups.items():
        if xs:
            out[k] = (np.concatenate(xs).astype(np.int64), np.concatenate(ids).astype(np.int64))
    return out


def _key(X):
    return (X[:, 0] + (1 << 20)) * (1 << 42) + (X[:, 1] + (1 << 20)) * (1 << 21) + (X[:, 2] + (1 << 20))


def render_persp(dim: Dimension, pal: Palette, cam, look, fov: float = 70.0, W: int = 1600, H: int = 900,
                 sky=((22, 12, 46), (58, 34, 104)), fog=(44, 30, 80), fog_dist: float = 900.0,
                 moon_dir=(-0.57, 0.82, 0.0), stars: int = 500, glow: float = 1.0, night: bool = True,
                 max_dist: float = 1400.0, beams=()) -> Image.Image:
    cam = np.asarray(cam, float)
    f = np.asarray(look, float) - cam
    f /= np.linalg.norm(f)
    right = np.cross(f, [0, 1, 0])
    right /= np.linalg.norm(right)
    up = np.cross(right, f)
    focal = (W / 2) / math.tan(math.radians(fov) / 2)

    # 하늘
    t = np.linspace(0, 1, H)[:, None]
    img = np.repeat((np.array(sky[0]) * (1 - t) + np.array(sky[1]) * t)[:, None, :], W, 1).astype(np.float32)
    rng = np.random.default_rng(3)
    sx_, sy_ = rng.integers(0, W, stars), rng.integers(0, int(H * 0.75), stars)
    img[sy_, sx_] = np.maximum(img[sy_, sx_], rng.uniform(140, 255, (stars, 1)))
    md = np.asarray(moon_dir, float)
    md /= np.linalg.norm(md)
    if md @ f > 0.05:
        mu = W / 2 + focal * (md @ right) / (md @ f)
        mv = H / 2 - focal * (md @ up) / (md @ f)
        r = W * 0.025
        moon = Image.new("L", (W, H), 0)
        dm = ImageDraw.Draw(moon)
        dm.ellipse((mu - r, mv - r, mu + r, mv + r), fill=255)
        dm.ellipse((mu - r + r * 0.55, mv - r - r * 0.25, mu + r + r * 0.55, mv + r - r * 0.25), fill=0)
        m = np.asarray(moon.filter(ImageFilter.GaussianBlur(1.2)), np.float32)[..., None] / 255
        img = img * (1 - m) + np.array([235, 215, 255], np.float32) * m
        halo = np.asarray(moon.filter(ImageFilter.GaussianBlur(r * 1.5)), np.float32)[..., None] / 255
        img = img + halo * np.array([120, 80, 200], np.float32) * 0.6

    zbuf = np.full(W * H, np.inf)
    cbuf = np.zeros((W * H, 3), np.float32)
    ebuf = np.zeros(W * H, np.float32)
    emis_p, full_p = _flags(dim)
    top_c = _glow_lut(dim, pal.lut(dim, 0))
    side_c = _glow_lut(dim, pal.lut(dim, 1))
    for k, (X, I) in _gather(dim, cam, max_dist=max_dist).items():
        opaque = full_p[I]
        keys = np.sort(_key(X[opaque]))

        def exposed(dx, dy, dz):
            q = _key(X + np.array([dx, dy, dz]))
            i = np.clip(np.searchsorted(keys, q), 0, len(keys) - 1)
            return ~(keys[i] == q) | ~opaque
        P = (X + 0.5) * k  # 중심 (월드)
        V = cam - P
        # 보이는 면 고르기: 카메라 쪽을 향하고 이웃이 비어 있는 면 중 가장 정면인 것
        cand = [(V[:, 1], 0, exposed(0, 1, 0), 1.0), (-V[:, 1], 0, exposed(0, -1, 0), 0.45),
                (V[:, 0], 1, exposed(1, 0, 0), 0.62), (-V[:, 0], 1, exposed(-1, 0, 0), 0.7),
                (V[:, 2], 1, exposed(0, 0, 1), 0.82), (-V[:, 2], 1, exposed(0, 0, -1), 0.76)]
        best = np.full(len(P), -np.inf)
        face = np.zeros(len(P), int)
        shade = np.zeros(len(P))
        for comp, fc, ex, sh in cand:
            score = np.where(ex & (comp > 0), comp, -np.inf)
            m = score > best
            best[m], face[m], shade[m] = score[m], fc, sh
        vis = np.isfinite(best)
        P, I, face, shade = P[vis], I[vis], face[vis], shade[vis]
        rel = P - cam
        zc = rel @ f
        ok = zc > 1.0
        P, I, face, shade, rel, zc = P[ok], I[ok], face[ok], shade[ok], rel[ok], zc[ok]
        u = W / 2 + focal * (rel @ right) / zc
        v = H / 2 - focal * (rel @ up) / zc
        s = np.clip(np.ceil(focal * k / zc * 1.1), 1, 64).astype(int)
        inview = (u > -s) & (u < W + s) & (v > -s) & (v < H + s)
        u, v, s, zc, I, face, shade = u[inview], v[inview], s[inview], zc[inview], I[inview], face[inview], shade[inview]
        emis = emis_p[I]
        col = np.where(face[:, None] == 0, top_c[I], side_c[I]) * np.where(emis, 1.0, shade)[:, None]
        if night:
            col = np.where(emis[:, None], col * 1.1, col * 0.62)
        fk = (1 - np.exp(-zc / fog_dist))[:, None]
        col = col * (1 - fk * 0.85) + np.array(fog, np.float32) * fk * 0.85
        for size in np.unique(s):
            sel = np.nonzero(s == size)[0]
            off = np.arange(size) - size // 2
            du, dv = np.meshgrid(off, off, indexing="ij")
            du, dv = du.ravel(), dv.ravel()
            for c0 in range(0, len(sel), max(1, 4_000_000 // len(du))):
                j = sel[c0:c0 + max(1, 4_000_000 // len(du))]
                pu = (np.round(u[j])[:, None] + du[None]).astype(np.int64).ravel()
                pv = (np.round(v[j])[:, None] + dv[None]).astype(np.int64).ravel()
                inb = (pu >= 0) & (pu < W) & (pv >= 0) & (pv < H)
                pix = (pv * W + pu)[inb]
                zz = np.repeat(zc[j], len(du))[inb]
                cc = np.repeat(col[j], len(du), axis=0)[inb]
                ee = np.repeat(emis[j].astype(np.float32), len(du))[inb]
                order = np.argsort(zz, kind="stable")
                pix, zz, cc, ee = pix[order], zz[order], cc[order], ee[order]
                _, first = np.unique(pix, return_index=True)
                p, zp = pix[first], zz[first]
                better = zp < zbuf[p]
                p = p[better]
                zbuf[p] = zp[better]
                cbuf[p] = cc[first][better]
                ebuf[p] = ee[first][better]
    # 신호기 빛기둥: 세로선 (가려지면 안 그림)
    for bx, by, bz in beams:
        ys = np.arange(by, by + 1200, 2.0)
        Pb = np.stack([np.full_like(ys, bx + 0.5), ys, np.full_like(ys, bz + 0.5)], 1)
        rel = Pb - cam
        zc = rel @ f
        ok = zc > 1
        u = (W / 2 + focal * (rel[ok] @ right) / zc[ok]).astype(int)
        v = (H / 2 - focal * (rel[ok] @ up) / zc[ok]).astype(int)
        w = np.clip((focal * 1.2 / zc[ok]).astype(int), 1, 12)
        for uu, vv, ww, z0 in zip(u, v, w, zc[ok]):
            if 0 <= vv < H:
                for du in range(-ww, ww + 1):
                    if 0 <= uu + du < W and zbuf[vv * W + uu + du] > z0:
                        zbuf[vv * W + uu + du] = z0
                        cbuf[vv * W + uu + du] = (255, 236, 170)
                        ebuf[vv * W + uu + du] = 1.0
    flat = img.reshape(-1, 3)
    hit = np.isfinite(zbuf)
    flat[hit] = cbuf[hit]
    img = flat.reshape(H, W, 3)
    if glow > 0 and ebuf.any():
        e = (ebuf.reshape(H, W, 1) * img).clip(0, 255).astype(np.uint8)
        gl = Image.fromarray(e, "RGB")
        g1 = np.asarray(gl.filter(ImageFilter.GaussianBlur(3)), np.float32)
        g2 = np.asarray(gl.filter(ImageFilter.GaussianBlur(14)), np.float32)
        img = img + glow * (0.9 * g1 + 0.8 * g2)
    return Image.fromarray(img.clip(0, 255).astype(np.uint8), "RGB")


def persp_panel(dim, pal, title, notes=(), **kw):
    img = render_persp(dim, pal, **kw)
    return _frame(img, title, list(notes))
