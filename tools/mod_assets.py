"""모드 고정 리소스 생성 (저장소에 커밋): 아이템 아이콘(이름 글자)·아이템 모델·언어 파일.

python -m tools.mod_assets → mod/src/main/resources/assets/ruina/ + previews/mod_items.png (폰 확인용)
아이템 목록은 config.MOD_ITEMS. 아이콘은 사용자 결정대로 '아이템 이름 글자를 써 넣은 단순한 아이콘'.
"""
from __future__ import annotations

import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import config  # noqa: E402

ASSETS = os.path.join(ROOT, "mod", "src", "main", "resources", "assets", "ruina")
SIZE = 64          # 아이콘 해상도 (GUI 배율 2에서 칸 32px → 정확히 절반)
FONTS = ["/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
         "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
         "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf"]

# 카드 색 (배경 위, 배경 아래, 테두리, 글자)
PAPER = ((236, 214, 166), (196, 160, 98), (120, 84, 40), (60, 36, 16))
TEAL = ((70, 150, 150), (30, 80, 90), (170, 230, 220), (255, 255, 255))
# 세피라: 층(부서) 색
SEPHIRAH = {
    "malkuth": (227, 163, 58), "yesod": (122, 90, 181), "hod": (240, 138, 60), "netzach": (111, 191, 90),
    "tiphereth": (242, 209, 74), "gebura": (196, 58, 58), "chesed": (58, 123, 213), "binah": (140, 122, 90),
    "hokma": (160, 133, 91), "keter": (232, 232, 232),
}


def _font(px: int):
    for p in FONTS:
        if os.path.exists(p):
            return ImageFont.truetype(p, px)
    raise FileNotFoundError("한글 폰트 없음: " + ", ".join(FONTS))


def _colors(item_id: str, kind: str):
    if kind == "invitation":
        return PAPER
    if kind == "room":
        return TEAL
    if kind == "sephirah":
        c = SEPHIRAH[item_id]
        lum = 0.3 * c[0] + 0.59 * c[1] + 0.11 * c[2]
        top = tuple(min(255, v + 40) for v in c)
        bot = tuple(int(v * 0.6) for v in c)
        return top, bot, tuple(min(255, v + 90) for v in c), (30, 20, 10) if lum > 160 else (255, 255, 255)
    raise KeyError(f"아이콘 색 없음: {item_id} ({kind})")


def _lines(name: str) -> list[str]:
    """이름을 줄로 (띄어쓰기 기준, 4글자 넘는 낱말은 그대로)."""
    words = name.split()
    if len(words) > 1:
        return words
    if len(name) <= 3:
        return [name]
    h = (len(name) + 1) // 2
    return [name[:h], name[h:]]


def icon(item_id: str, name: str, kind: str, size: int = SIZE) -> Image.Image:
    top, bot, edge, ink = _colors(item_id, kind)
    s = 4   # 크게 그려서 줄임 (매끈한 글자)
    W = size * s
    img = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    grad = Image.new("RGBA", (W, W))
    gd = ImageDraw.Draw(grad)
    for y in range(W):
        t = y / (W - 1)
        gd.line([(0, y), (W, y)], fill=tuple(int(a + (b - a) * t) for a, b in zip(top, bot)) + (255,))
    mask = Image.new("L", (W, W), 0)
    md = ImageDraw.Draw(mask)
    pad, rad = 2 * s, 10 * s
    if kind == "sephirah":   # 세피라는 둥근 보석 모양
        md.ellipse([pad, pad, W - pad, W - pad], fill=255)
    else:
        md.rounded_rectangle([pad, pad, W - pad, W - pad], radius=rad, fill=255)
    img.paste(grad, (0, 0), mask)
    d = ImageDraw.Draw(img)
    if kind == "sephirah":
        d.ellipse([pad, pad, W - pad, W - pad], outline=edge + (255,), width=3 * s)
    else:
        d.rounded_rectangle([pad, pad, W - pad, W - pad], radius=rad, outline=edge + (255,), width=3 * s)
    if kind == "invitation":   # 봉투 접힌 선
        d.line([(pad + 6 * s, pad + 10 * s), (W // 2, W // 2 - 4 * s), (W - pad - 6 * s, pad + 10 * s)],
               fill=edge + (140,), width=2 * s)
    lines = _lines(name)
    inner = W - 2 * pad - 10 * s
    px = 24 * s   # 두 글자 이름도 너무 커지지 않게
    while px > 6 * s:
        f = _font(px)
        widths = [d.textbbox((0, 0), l, font=f)[2] for l in lines]
        lh = px * 1.08
        if max(widths) <= inner and lh * len(lines) <= inner:
            break
        px -= s
    f = _font(px)
    lh = px * 1.08
    y0 = (W - lh * len(lines)) / 2 + (6 * s if kind == "invitation" else 0)
    shadow = (0, 0, 0, 150) if ink == (255, 255, 255) else (255, 255, 255, 120)
    for i, l in enumerate(lines):
        bb = d.textbbox((0, 0), l, font=f)
        x = (W - (bb[2] - bb[0])) / 2 - bb[0]
        y = y0 + i * lh - bb[1] + (lh - (bb[3] - bb[1])) / 2
        d.text((x + s * 1.5, y + s * 1.5), l, font=f, fill=shadow)
        d.text((x, y), l, font=f, fill=ink + (255,))
    return img.resize((size, size), Image.LANCZOS)


def write_json(path: str, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(obj, fh, indent=2, ensure_ascii=False)
        fh.write("\n")


def main():
    lang = {"itemGroup.ruina.library": "도서관"}
    sheet = Image.new("RGBA", (6 * 136 + 8, 2 * 136 + 8), (40, 36, 44, 255))
    for i, (iid, name, kind, _) in enumerate(config.MOD_ITEMS):
        img = icon(iid, name, kind)
        p = os.path.join(ASSETS, "textures", "item", f"{iid}.png")
        os.makedirs(os.path.dirname(p), exist_ok=True)
        img.save(p)
        write_json(os.path.join(ASSETS, "models", "item", f"{iid}.json"),
                   {"parent": "minecraft:item/generated", "textures": {"layer0": f"ruina:item/{iid}"}})
        write_json(os.path.join(ASSETS, "items", f"{iid}.json"),
                   {"model": {"type": "minecraft:model", "model": f"ruina:item/{iid}"}})
        lang[f"item.ruina.{iid}"] = name
        sheet.paste(img.resize((128, 128), Image.NEAREST), (8 + (i % 6) * 136, 8 + (i // 6) * 136), img.resize((128, 128), Image.NEAREST))
    write_json(os.path.join(ASSETS, "lang", "ko_kr.json"), lang)
    write_json(os.path.join(ASSETS, "lang", "en_us.json"), lang)   # 영어 설정에서도 한국어 이름
    os.makedirs(os.path.join(ROOT, "previews"), exist_ok=True)
    sheet.save(os.path.join(ROOT, "previews", "mod_items.png"))
    print(f"아이콘 {len(config.MOD_ITEMS)}개 → {ASSETS}")


if __name__ == "__main__":
    main()
