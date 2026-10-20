"""건축물(월드) 빌드 결과 재사용: 건축물 코드가 그대로면 4200만 블록 월드를 다시 만들지 않는다.

- 지문(fingerprint): 월드에 영향을 주는 파일(builders/, config.py, ref/, resourcepack/, tools/ 의 빌드 코드)의 해시
- save : mod/build/generated/ruina (모드 생성 리소스: 데이터팩·소리·items.json·world.zip) + 지문 → out/release/Ruina_generated.zip
         (CI 가 릴리스 world-latest 에 올림)
- fetch: 릴리스의 Ruina_generated.zip 을 받아 지문이 지금 코드와 같으면 mod/build/generated/ruina 에 풂 (종료 코드 0),
         다르거나 없으면 1 → 그때만 `python -m tools.ci world` 로 새로 만든다

사용: python -m tools.world_cache fetch || python -m tools.ci world
"""
from __future__ import annotations

import hashlib
import io
import os
import shutil
import sys
import urllib.request
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEN = os.path.join(ROOT, "mod", "build", "generated", "ruina")
OUT = os.path.join(ROOT, "out", "release", "Ruina_generated.zip")
URL = "https://github.com/twoapple08/Library-of-Ruina-map/releases/download/world-latest/Ruina_generated.zip"
STAMP = "ruina/source.sha"

INCLUDE_DIRS = ("builders", "ref", "resourcepack", "reference", "design/fit", "design/models")
# tools/ 중 월드 결과에 영향이 없는 것 (미리보기·검사·CI 정리·아이콘·셰이더·이 파일)
TOOLS_SKIP = {"ci.py", "mod_assets.py", "shaderpack.py", "render3d.py", "render_persp.py", "preview.py", "lint.py",
              "world_cache.py", "release_verify.py", "form_preview.py", "form_raster.py", "__init__.py"}


def fingerprint() -> str:
    files = [os.path.join(ROOT, "config.py")]
    for d in INCLUDE_DIRS:
        for base, dirs, names in os.walk(os.path.join(ROOT, d)):
            dirs[:] = sorted(x for x in dirs if x != "__pycache__")
            files += [os.path.join(base, n) for n in names if not n.endswith((".pyc", ".md"))]
    tools = os.path.join(ROOT, "tools")
    files += [os.path.join(tools, n) for n in os.listdir(tools) if n.endswith(".py") and n not in TOOLS_SKIP]
    h = hashlib.sha256()
    for p in sorted(files):
        h.update(os.path.relpath(p, ROOT).replace(os.sep, "/").encode() + b"\0")
        with open(p, "rb") as f:
            h.update(hashlib.sha256(f.read()).digest())
    return h.hexdigest()[:20]


def save() -> int:
    if not os.path.isfile(os.path.join(GEN, "ruina", "world.zip")):
        print("생성 리소스 없음 (먼저 python -m tools.ci world)")
        return 1
    fp = fingerprint()
    with open(os.path.join(GEN, STAMP), "w") as f:
        f.write(fp + "\n")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED, compresslevel=3) as z:
        for base, dirs, names in os.walk(GEN):
            for n in sorted(names):
                full = os.path.join(base, n)
                z.write(full, os.path.relpath(full, GEN), compress_type=zipfile.ZIP_STORED if n.endswith(".zip") else None)
    print(f"저장: {OUT} ({os.path.getsize(OUT) / 1e6:.1f} MB, 지문 {fp})")
    return 0


def fetch() -> int:
    fp = fingerprint()
    try:
        with urllib.request.urlopen(URL, timeout=120) as r:
            data = r.read()
    except Exception as e:  # noqa: BLE001 — 없거나 못 받으면 새로 빌드
        print(f"릴리스 건축물 못 받음 ({e}) → 새로 빌드")
        return 1
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        got = z.read(STAMP).decode().strip() if STAMP in z.namelist() else "?"
        if got != fp:
            print(f"건축물 코드가 바뀜 (릴리스 {got} ≠ 지금 {fp}) → 새로 빌드")
            return 1
        shutil.rmtree(GEN, ignore_errors=True)
        z.extractall(GEN)
    print(f"릴리스 건축물 재사용 (지문 {fp}, {len(data) / 1e6:.1f} MB)")
    return 0


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "fingerprint":
        print(fingerprint())
        sys.exit(0)
    sys.exit({"save": save, "fetch": fetch}.get(cmd, lambda: print(__doc__) or 2)())
