"""형체 미리보기 (게임 없이, 수십 초): 공간 빌더 하나만 돌려 형체를 원근으로 그림 → 원화와 비교.

    python -m tools.form_preview exterior [출력.png]

빌더 모듈의 CAM(도착 시점), ART(원화), PREVIEW_CAMS(추가 시점 목록)를 씀. 하늘(sky)은 가장 뒤에 그림.
"""
from __future__ import annotations

import importlib
import os
import sys
import time

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def caption_font(size=19):
    for path in (os.environ.get("RUINA_PREVIEW_FONT", ""),
                 "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
                 "/tmp/ruina-fonts/NanumGothic-Regular.ttf"):
        if path and os.path.isfile(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default(size=size)


def render(space: str, out: str, W: int = 960, H: int = 540, kw=None):
    sys.path.insert(0, ROOT)
    from builders import Build
    from tools import forms as F
    from tools import form_raster as R
    mod = importlib.import_module(f"builders.{space}")
    b = Build()
    t0 = time.time()
    if hasattr(mod, "preview"):
        mod.preview(b)
    else:
        mod.build(b, **(kw or {}))
    lay = b.forms.layers[getattr(mod, "SPACE", space)]
    parts = [p for p, _ in lay.parts]
    print(f"빌드 {time.time() - t0:.0f}초, 면 {sum(len(p) for p in parts)}")
    cams = [("도착 (원화 투영)", mod.CAM)] + list(getattr(mod, "PREVIEW_CAMS", []))
    tiles = []
    if getattr(mod, "ART", None):
        ref = Image.open(os.path.join(ROOT, mod.ART)).convert("RGB").resize((W, H))
        tiles.append(("원화", ref))
    for name, cam in cams:
        t1 = time.time()
        moving = [R.mover_mesh(m, cam) for m in lay.movers]
        img, depth = R.render(parts + moving, cam, W, H, bg=(0, 0, 0))
        if lay.sky_mesh is not None:
            sky, _ = R.render([lay.sky_mesh.translate(cam.pos)], cam, W, H, bg=(0, 0, 0))
            a = np.asarray(img)
            empty = ~np.isfinite(depth)[..., None]
            img = Image.fromarray(np.where(empty, np.asarray(sky), a))
        tiles.append((name, img))
        print(f"  {name} {time.time() - t1:.0f}초")
    bar = 38
    sheet = Image.new("RGB", (W, (H + bar) * len(tiles)), (20, 16, 28))
    dr = ImageDraw.Draw(sheet)
    font = caption_font()
    for i, (name, img) in enumerate(tiles):
        sheet.paste(img, (0, i * (H + bar) + bar))
        label = name if name == "원화" else "오프라인 미리보기 · " + name
        dr.text((10, i * (H + bar) + 8), label, font=font, fill=(255, 255, 255))
    sheet.save(out)
    print(out)


if __name__ == "__main__":
    render(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else f"/tmp/form_preview_{sys.argv[1]}.png",
           kw={"city": False, "clouds": False} if sys.argv[1] == "exterior" else None)
