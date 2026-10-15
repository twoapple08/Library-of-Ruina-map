"""게임 외 검증용 면 채움 렌더링. C 컴파일러만 필요하며 빌드 결과는 /tmp에 캐시한다.

기존 점 샘플 미리보기의 확대 시 빈 픽셀을 없앤다. 삼각형 분할·깊이·UV 원근 보정·
뒷면 제거를 사용한다. 반투명은 기존 미리보기와 같이 제외한다.
"""
from __future__ import annotations

import ctypes
import hashlib
from pathlib import Path
import subprocess
import tempfile

import numpy as np

from tools import forms as F

_KERNEL = None


def _kernel():
    global _KERNEL
    if _KERNEL is None:
        source = Path(__file__).with_suffix('.c')
        digest = hashlib.sha256(source.read_bytes()).hexdigest()[:16]
        cache = Path(tempfile.gettempdir()) / f'ruina-raster-{digest}.so'
        if not cache.exists():
            with tempfile.TemporaryDirectory(prefix='ruina-raster-') as tmp:
                output = Path(tmp) / 'raster.so'
                subprocess.run(['cc', '-O3', '-shared', '-fPIC', str(source), '-o', str(output), '-lm'], check=True)
                output.replace(cache)  # 동시 미리보기가 덜 만들어진 공유 라이브러리를 읽지 않게 한다.
        lib = ctypes.CDLL(str(cache))
        fn = lib.raster
        ptr = ctypes.c_void_p
        fn.argtypes = [ptr, ptr, ctypes.c_int64, ctypes.c_int, ctypes.c_int, ptr, ptr, ptr, ptr, ptr, ptr, ptr]
        fn.restype = None
        _KERNEL = fn
    return _KERNEL


def fragments(q, cam, width, height):
    """면 번호/깊이/원본 사각형 꼭짓점별 원근 보정 가중치 (안 그린 픽셀은 id=-1)."""
    sx, sy, z = cam.project(q.P)
    points = np.ascontiguousarray(np.stack([sx*width, sy*height, z], -1), dtype=np.float64)
    facing = np.sum(F.face_normals(q.P)*(np.asarray(cam.pos)-q.P.mean(1)), axis=1) > 0
    active = np.ascontiguousarray(facing & np.isfinite(points).all((1, 2)) & (z > .05).all(1), dtype=np.uint8)
    depth = np.full((height, width), np.inf)
    ids = np.full((height, width), -1, dtype=np.int64)
    weights = np.zeros((height, width, 4), dtype=np.float64)
    uv = np.ascontiguousarray(q.UV-np.floor(q.UV.min(1, keepdims=True)+1e-6))
    materials = np.ascontiguousarray(q.M, dtype=np.int32)
    meta = np.full((len(F.MATERIALS), 3), -1, dtype=np.int64)
    alpha_parts, offset = [], 0
    for i, mat in enumerate(F.MATERIALS):
        texture = F.TEXTURES.get(mat.sprite.removeprefix('ruina:block/form/'))
        if mat.layer == 'cutout' and texture is not None:
            a = np.asarray(texture.convert('RGBA'))[..., 3].copy().ravel()
            if (a < 128).any():
                meta[i] = offset, texture.width, texture.height
                alpha_parts.append(a)
                offset += len(a)
    alpha = np.concatenate(alpha_parts) if alpha_parts else np.zeros(1, dtype=np.uint8)
    _kernel()(points.ctypes.data, active.ctypes.data, len(q), width, height,
              depth.ctypes.data, ids.ctypes.data, weights.ctypes.data,
              uv.ctypes.data, materials.ctypes.data, meta.ctypes.data, alpha.ctypes.data)
    return ids, depth, weights


def mover_mesh(mover, cam, seconds=0):
    """Java MoverRenderer와 같은 축·위상. 기본 스냅샷은 t=0초."""
    t = seconds/mover.period+mover.phase if mover.period > 0 else 0
    if mover.motion == 'follow':
        return mover.mesh.translate(np.asarray(cam.pos)-np.asarray(mover.pivot))
    if mover.motion in ('spin', 'swing'):
        angle = t*360 if mover.motion == 'spin' else mover.amp*np.sin(t*2*np.pi)
        return mover.mesh.rotate(mover.axis, angle, origin=mover.pivot)
    if mover.motion == 'bob':
        return mover.mesh.translate(F._unit(np.asarray(mover.axis))*mover.amp*np.sin(t*2*np.pi))
    return mover.mesh


def render(qs, cam, width=960, height=540, bg=(30, 20, 50), light=(-.4, .8, .45)):
    from PIL import Image
    q = F.concat([p.take(p.C[..., 3].mean(1) >= .5) for p in qs])
    ids, depth, weights = fragments(q, cam, width, height)
    visible = ids >= 0
    qi = ids[visible]
    wt = weights[visible, :, None]
    img = np.empty((height, width, 3), dtype=float)
    img[:] = bg
    if not len(qi):
        return Image.fromarray(img.astype('uint8')), depth
    uv = ((q.UV[qi]-np.floor(q.UV[qi].min(1, keepdims=True)+1e-6))*wt).sum(1)
    col = (q.C[qi]*wt).sum(1)
    normals = F._unit((q.N[qi]*wt).sum(1))
    colors = np.zeros((len(qi), 3))
    for index in np.unique(q.M[qi]):
        mat = F.MATERIALS[index]
        sel = q.M[qi] == index
        name = mat.sprite.removeprefix('ruina:block/form/')
        texture = F.TEXTURES.get(name)
        if texture is None:
            rgb = np.full((sel.sum(), 3), 128.)
        else:
            tx = np.asarray(texture.convert('RGB'), float)
            th, tw = tx.shape[:2]
            rgb = tx[np.clip((uv[sel, 1]*th).astype(int), 0, th-1),
                     np.clip((uv[sel, 0]*tw).astype(int), 0, tw-1)]
        rgb *= col[sel, :3]
        if not (mat.emissive or mat.flat):
            rgb *= (.45+.55*np.clip(normals[sel] @ F._unit(np.asarray(light)), 0, 1))[:, None]
        colors[sel] = rgb
    img[visible] = colors
    return Image.fromarray(np.clip(img, 0, 255).astype('uint8')), depth
