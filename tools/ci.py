"""GitHub Actions에서 실행하는 단계들.

python -m tools.ci fetch            서버 jar 다운로드, Java 버전 출력
python -m tools.ci refs             jar에서 version.json·바닐라 JSON 추출 → ci_out/ref
python -m tools.ci reports          데이터 생성기 reports → 블록/레지스트리 목록 → ci_out/ref
python -m tools.ci colors           클라이언트 jar 텍스처로 블록 평균색 계산 → ci_out/ref/block_colors.json (미리보기용)
python -m tools.ci probe            포맷 프로브: 바닐라 월드 + 우리 데이터팩 월드를 만들어 NBT 덤프
python -m tools.ci world            실제 월드 빌드 (서버 2회 실행 + 검증 + zip)
"""
from __future__ import annotations

import glob
import json
import os
import re
import shutil
import subprocess
import sys
import zipfile

from . import nbt, region
from .server import Server, fetch_server, prepare_dir

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, ".server")
OUT = os.path.join(ROOT, "ci_out")


def _gh_output(**kv):
    p = os.environ.get("GITHUB_OUTPUT")
    if p:
        with open(p, "a") as f:
            for k, v in kv.items():
                f.write(f"{k}={v}\n")


def _info():
    with open(os.path.join(CACHE, "info.json")) as f:
        return json.load(f)


def cmd_fetch(version=None):
    info = fetch_server(CACHE, version)
    print(json.dumps(info, indent=2))
    _gh_output(mc_version=info["id"], java=info["java"] or 25)


# ------------------------------------------------------------------ jar 안 참고 파일

REF_PATTERNS = (
    "data/minecraft/dimension_type/",
    "data/minecraft/world_clock/",
    "data/minecraft/timeline/",
    "data/minecraft/worldgen/world_preset/",
    "data/minecraft/worldgen/flat_level_generator_preset/",
    "data/minecraft/worldgen/biome/the_void.json",
    "data/minecraft/worldgen/biome/plains.json",
    "data/minecraft/worldgen/biome/the_end.json",
    "data/minecraft/worldgen/biome/deep_dark.json",
    "data/minecraft/worldgen/biome/warm_ocean.json",
    "data/minecraft/tags/timeline/",
    "data/minecraft/tags/dimension_type/",
    "pack.mcmeta",
)


def _inner_jar(jar):
    z = zipfile.ZipFile(jar)
    inner = [n for n in z.namelist() if n.startswith("META-INF/versions/") and n.endswith(".jar")]
    if not inner:
        return z
    import io
    return zipfile.ZipFile(io.BytesIO(z.read(inner[0])))


def cmd_refs():
    info = _info()
    z = _inner_jar(info["jar"])
    ref = os.path.join(OUT, "ref")
    os.makedirs(ref, exist_ok=True)
    names = z.namelist()
    if "version.json" in names:
        with open(os.path.join(ref, "version.json"), "wb") as f:
            f.write(z.read("version.json"))
    n = 0
    for name in names:
        extra = (name.startswith("data/minecraft/worldgen/biome/") and name.endswith(".json")
                 and b"ambient_particles" in z.read(name))
        if (extra or any(name.startswith(p) for p in REF_PATTERNS)) and not name.endswith("/"):
            dst = os.path.join(ref, "vanilla", name.split("data/minecraft/", 1)[-1])
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            with open(dst, "wb") as f:
                f.write(z.read(name))
            n += 1
    # data/minecraft/ 아래 폴더 목록 (레지스트리 폴더 이름 확인용)
    dirs = sorted({"/".join(x.split("/")[:3]) for x in names if x.startswith("data/minecraft/") and x.count("/") >= 3})
    wg = sorted({"/".join(x.split("/")[:4]) for x in names if x.startswith("data/minecraft/worldgen/") and x.count("/") >= 4})
    with open(os.path.join(ref, "data_folders.txt"), "w") as f:
        f.write("\n".join(dirs + wg) + "\n")
    print(f"refs: {n} files")


def cmd_reports():
    info = _info()
    work = os.path.join(CACHE, "gen")
    shutil.rmtree(work, ignore_errors=True)
    subprocess.run(["java", "-DbundlerMainClass=net.minecraft.data.Main", "-jar", os.path.abspath(info["jar"]),
                    "--reports", "--output", work], cwd=CACHE, check=True)
    ref = os.path.join(OUT, "ref")
    os.makedirs(ref, exist_ok=True)
    with open(os.path.join(work, "reports", "blocks.json")) as f:
        blocks = json.load(f)
    compact = {}
    for name, b in blocks.items():
        props = b.get("properties", {})
        default = next((s.get("properties", {}) for s in b.get("states", []) if s.get("default")), {})
        compact[name] = {"p": props, "d": default} if props else {}
    with open(os.path.join(ref, "blocks.json"), "w") as f:
        json.dump(compact, f, separators=(",", ":"), sort_keys=True)
    with open(os.path.join(work, "reports", "registries.json")) as f:
        regs = json.load(f)
    small = {k: sorted(v.get("entries", {}).keys()) for k, v in regs.items()}
    with open(os.path.join(ref, "registries.json"), "w") as f:
        json.dump(small, f, separators=(",", ":"), sort_keys=True)
    others = sorted(os.path.relpath(p, work) for p in glob.glob(os.path.join(work, "reports", "**"), recursive=True))
    with open(os.path.join(ref, "reports_files.txt"), "w") as f:
        f.write("\n".join(others) + "\n")
    print(f"reports: {len(compact)} blocks, {len(small)} registries")


# ------------------------------------------------------------------ 블록 색 (미리보기용)

TINTS = {  # 바이옴 색이 곱해지는 블록 (대략값)
    "grass": (0x79, 0xC0, 0x5A), "leaves": (0x59, 0xAE, 0x30), "vine": (0x59, 0xAE, 0x30),
    "fern": (0x79, 0xC0, 0x5A), "lily_pad": (0x20, 0x80, 0x30), "water": (0x3F, 0x76, 0xE4),
    "sugar_cane": (0x79, 0xC0, 0x5A),
}


def cmd_colors():
    import io
    import urllib.request
    from PIL import Image
    info = _info()
    from .server import _get_json, MANIFEST
    man = _get_json(MANIFEST)
    entry = next(v for v in man["versions"] if v["id"] == info["id"])
    meta = _get_json(entry["url"])
    cpath = os.path.join(CACHE, "client.jar")
    if not os.path.exists(cpath):
        urllib.request.urlretrieve(meta["downloads"]["client"]["url"], cpath)
    z = zipfile.ZipFile(cpath)
    names = set(z.namelist())

    def js(path):
        return json.loads(z.read(path)) if path in names else None

    model_cache = {}

    def model_textures(ref):
        ref = ref.split(":")[-1]
        if ref in model_cache:
            return model_cache[ref]
        m = js(f"assets/minecraft/models/{ref}.json") or {}
        tex = {}
        if "parent" in m:
            tex.update(model_textures(m["parent"]))
        tex.update(m.get("textures", {}))
        model_cache[ref] = tex
        return tex

    def resolve(tex, key, depth=0):
        v = tex.get(key)
        while depth < 10:
            if isinstance(v, dict):  # 새 형식: {"sprite": "...", ...}
                v = v.get("sprite")
            if isinstance(v, str) and v.startswith("#"):
                v = tex.get(v[1:])
                depth += 1
                continue
            break
        return v if isinstance(v, str) else None

    def avg(texref):
        if not texref:
            return None
        p = f"assets/minecraft/textures/{texref.split(':')[-1]}.png"
        if p not in names:
            return None
        im = Image.open(io.BytesIO(z.read(p))).convert("RGBA")
        w, h = im.size
        im = im.crop((0, 0, w, min(w, h)))  # 애니메이션 텍스처는 첫 프레임
        import numpy as np
        a = np.asarray(im, dtype=np.float64).reshape(-1, 4)
        alpha = a[:, 3] / 255.0
        cover = float(alpha.mean())
        if alpha.sum() == 0:
            return None
        rgb = (a[:, :3] * alpha[:, None]).sum(0) / alpha.sum()
        return [int(round(c)) for c in rgb] + [int(round(cover * 255))]

    with open(os.path.join(OUT, "ref", "blocks.json")) as f:
        blocks = json.load(f)
    out = {}
    for full in blocks:
        name = full.split(":")[1]
        bs = js(f"assets/minecraft/blockstates/{name}.json")
        if not bs:
            continue
        model = None
        if "variants" in bs:
            v = next(iter(bs["variants"].values()))
            model = (v[0] if isinstance(v, list) else v).get("model")
        elif "multipart" in bs:
            ap = bs["multipart"][0]["apply"]
            model = (ap[0] if isinstance(ap, list) else ap).get("model")
        if not model:
            continue
        tex = model_textures(model)
        top = next((resolve(tex, k) for k in ("top", "end", "all", "up", "texture", "cross", "plant", "particle")
                    if resolve(tex, k)), None)
        side = next((resolve(tex, k) for k in ("side", "all", "front", "north", "texture", "cross", "particle")
                     if resolve(tex, k)), None)
        ct, cs = avg(top), avg(side)
        if ct is None and cs is None:
            continue
        ct, cs = ct or cs, cs or ct
        for key, t in TINTS.items():
            if key in name and "dead" not in name:
                ct = [c * m // 255 for c, m in zip(ct[:3], t)] + ct[3:]
                cs = [c * m // 255 for c, m in zip(cs[:3], t)] + cs[3:]
        out[full] = ["#%02x%02x%02x%02x" % tuple(ct), "#%02x%02x%02x%02x" % tuple(cs)]
    with open(os.path.join(OUT, "ref", "block_colors.json"), "w") as f:
        json.dump(out, f, separators=(",", ":"), sort_keys=True)
    print(f"colors: {len(out)} / {len(blocks)} blocks")


# ------------------------------------------------------------------ 덤프 도우미

def dump_tree(world: str, out_txt: str):
    rows = []
    for p in sorted(glob.glob(os.path.join(world, "**"), recursive=True)):
        if os.path.isfile(p):
            rows.append(f"{os.path.getsize(p):>10}  {os.path.relpath(p, world)}")
    with open(out_txt, "w") as f:
        f.write("\n".join(rows) + "\n")


def dump_nbt_files(world: str, out_dir: str):
    for p in glob.glob(os.path.join(world, "**", "*.dat"), recursive=True):
        rel = os.path.relpath(p, world).replace(os.sep, "__")
        try:
            txt = nbt.to_snbt(nbt.read_file(p), max_array=8)
        except Exception as e:  # noqa
            txt = f"읽기 실패: {e!r}"
        with open(os.path.join(out_dir, rel + ".snbt"), "w") as f:
            f.write(txt + "\n")


def dump_chunk(mca: str, cx: int, cz: int, out_path: str):
    chunks = region.read_region(mca)
    c = chunks.get((cx, cz))
    if c is None:
        txt = f"청크 {cx},{cz} 없음. 있는 청크: {sorted(chunks)[:20]}"
    else:
        txt = nbt.to_snbt(c, max_array=8)
    with open(out_path, "w") as f:
        f.write(txt + "\n")


def _write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(text)


# ------------------------------------------------------------------ 포맷 프로브

def _probe_world(tag: str, datapack: str | None, extra_cmds: list, chunk_dumps: list):
    out = os.path.join(OUT, "probe", tag)
    os.makedirs(out, exist_ok=True)
    sdir = os.path.join(CACHE, f"probe_{tag}")
    shutil.rmtree(sdir, ignore_errors=True)
    prepare_dir(sdir, _info()["jar"])
    if datapack:
        shutil.copytree(datapack, os.path.join(sdir, "world", "datapacks", "ruina"))
    srv = Server(sdir, log_path=os.path.join(out, "server.log"))
    report = {"started": False, "cmds": {}}
    try:
        report["start_seconds"] = srv.start()
        report["started"] = True
        for c in extra_cmds:
            if c.startswith("#wait "):
                dim, x, y, z = c.split()[1:]
                report["cmds"][c] = srv.wait_loaded(dim, int(x), int(y), int(z))
            else:
                report["cmds"][c] = srv.run(c)
        report["cmds"]["save-all flush"] = srv.run("save-all flush", timeout=120)
    except Exception as e:  # noqa
        report["error"] = repr(e)
    finally:
        srv.stop()
    report["problems"] = srv.problems()
    world = os.path.join(sdir, "world")
    if os.path.isdir(world):
        dump_tree(world, os.path.join(out, "tree.txt"))
        dump_nbt_files(world, out)
        for rel, cx, cz in chunk_dumps:
            mca = os.path.join(world, rel)
            if os.path.exists(mca):
                dump_chunk(mca, cx, cz, os.path.join(out, f"chunk_{rel.replace('/', '__')}_{cx}_{cz}.snbt"))
    with open(os.path.join(out, "report.json"), "w") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    return report


def cmd_probe():
    sys.path.insert(0, ROOT)
    from tools import datapack
    # 1) 바닐라 (데이터팩 없음)
    _probe_world("vanilla", None, [
        "forceload add 0 0",
        "#wait minecraft:overworld 0 0 0",
        "gamerule advance_time",
        "gamerule random_tick_speed",
        "time query daytime",
        "execute if block 0 0 0 minecraft:air",
    ], [("dimensions/minecraft/overworld/region/r.0.0.mca", 0, 0)])
    # 2) 우리 데이터팩
    dp = os.path.join(CACHE, "datapack")
    datapack.write(dp, datapack.Links())
    shutil.copytree(dp, os.path.join(OUT, "probe", "datapack_used"), dirs_exist_ok=True)
    _probe_world("ruina", dp, [
        "datapack list",
        "execute in ruina:lobby run forceload add 0 0",
        "#wait ruina:lobby 0 0 0",
        "execute in ruina:lobby if block 0 0 0 minecraft:air",
        "execute in ruina:lobby run setblock 1 0 1 minecraft:oak_stairs[facing=east,half=top]",
        "execute in ruina:lobby run setblock 2 0 1 minecraft:chest[facing=west]{Items:[{Slot:0b,id:\"minecraft:book\",count:3}]}",
        "execute in ruina:exterior run forceload add 0 0",
        "#wait ruina:exterior 0 0 0",
        "execute in ruina:exterior run setworldspawn 0 100 0",
        "execute in ruina:exterior run time query daytime",
        "time query daytime",
        "function ruina:setup",
    ], [("dimensions/ruina/lobby/region/r.0.0.mca", 0, 0),
        ("dimensions/ruina/exterior/region/r.0.0.mca", 0, 0)])


def _sheet(items, path):
    """스크린샷 썸네일 한 장 모음 (4열)."""
    from PIL import Image, ImageDraw
    cols = 4
    sheet = Image.new("RGB", (cols * 324, ((len(items) + cols - 1) // cols) * 200), (24, 22, 28))
    d = ImageDraw.Draw(sheet)
    for i, (name, t) in enumerate(items):
        x, y = (i % cols) * 324 + 2, (i // cols) * 200 + 2
        sheet.paste(t, (x, y))
        d.text((x + 4, y + 182), name, fill=(236, 214, 166))
    sheet.save(path, quality=85)


def _read_lines(path):
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.readlines()


def _gradle_errors(lines):
    err = []
    for i, l in enumerate(lines):   # 컴파일 오류는 아래 3줄까지 (기호 이름·위치)
        if re.search(r"\.java:\d+: error:", l) or "FAILED" in l:
            err += [x.rstrip() for x in lines[i:i + (4 if "error:" in l else 1)]]
    return err


def cmd_modtest():
    """모드 게임 테스트 결과 → ci_out/mod/: 스크린샷 jpg·한 장 모음(sheet.jpg, 셰이더 판 sheet_bsl.jpg)·보고서·로그 끝부분.
    두 번 실행: 바닐라 렌더(전체 순회) → Iris+Sodium+맵 전용 BSL(몇 곳, 스크린샷 이름 bsl_)."""
    from PIL import Image
    mod = os.path.join(ROOT, "mod", "build")
    run = os.path.join(mod, "run", "clientGameTest")
    out = os.path.join(ROOT, "ci_out", "mod")
    shutil.rmtree(out, ignore_errors=True)
    os.makedirs(out, exist_ok=True)
    van = os.path.join(mod, "vanilla")   # 셰이더 판 실행 전에 옮겨 둔 바닐라 판 결과 (실행 폴더는 테스트 시작 때 비워짐)
    shots = sorted(glob.glob(os.path.join(run, "screenshots", "*.png")) + glob.glob(os.path.join(van, "screenshots", "*.png")))
    thumbs = {"": [], "bsl_": []}
    for p in shots:
        name = os.path.basename(p)[:-4]
        im = Image.open(p).convert("RGB")
        im.save(os.path.join(out, name + ".jpg"), quality=85)
        thumbs["bsl_" if name.startswith("bsl_") else ""].append((name, im.resize((320, 180))))
    for pre, items in thumbs.items():
        if items:
            _sheet(items, os.path.join(out, f"sheet{'_bsl' if pre else ''}.jpg"))

    vanilla_log = os.path.join(van, "latest.log")
    bsl_ran = os.path.isdir(van)
    logs = {"": vanilla_log if bsl_ran else os.path.join(run, "logs", "latest.log")}
    if bsl_ran:
        logs["_bsl"] = os.path.join(run, "logs", "latest.log")
    for suf, lp in logs.items():
        log_lines = _read_lines(lp)
        if not log_lines:
            continue
        with open(os.path.join(out, f"latest{suf}_tail.log"), "w", encoding="utf-8") as f:
            f.writelines(log_lines[-3000:])
        keys = ("ruina", "function", "iris", "shader", "sodium") if suf else ("ruina", "function")
        bad = [l for l in log_lines if ("/ERROR]" in l or "/WARN]" in l) and any(k in l.lower() for k in keys)]
        with open(os.path.join(out, f"problems{suf}.log"), "w", encoding="utf-8") as f:
            f.writelines(bad[:500])

    lines = ["## 모드 게임 테스트 (실제 클라이언트)", ""]
    for suf, report, title, env in (("", "ruina_test.txt", "바닐라 렌더", "GAMETEST_OUTCOME"),
                                    ("_bsl", "ruina_test_bsl.txt", "Iris+Sodium+맵 전용 BSL", "GAMETEST_BSL_OUTCOME")):
        outcome = os.environ.get(env, "" if suf else "?")
        if outcome in ("skipped", ""):
            lines.append(f"- ℹ️ {title}: 미실행 (건축 완료 후 최종 검사 때 실행)")
            continue
        n = len(thumbs["bsl_" if suf else ""])
        lines.append(f"- {'✅' if outcome == 'success' else '❌'} {title}: {outcome}, 스크린샷 {n}장 (ci-output 브랜치 mod/sheet{suf}.jpg)")
        rp = os.path.join(van if bsl_ran and not suf else run, report)
        lines += [f"  - {l.rstrip()}" for l in _read_lines(rp) if l.strip() and not l.startswith("📷")]
        gl = os.path.join(mod, f"gametest{suf}_gradle.log")
        if os.path.exists(gl):
            shutil.copy(gl, os.path.join(out, f"gradle{suf}.log"))
            err = _gradle_errors(_read_lines(gl))
            if err:
                lines += ["", "```"] + err[:60] + ["```"]
        if suf and os.path.exists(os.path.join(out, "problems_bsl.log")):
            probs = _read_lines(os.path.join(out, "problems_bsl.log"))
            lines.append(f"  - 셰이더 관련 경고·오류 {len(probs)}줄 (problems_bsl.log)")
    with open(os.path.join(out, "SUMMARY.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))


def main(argv):
    if not argv:
        print(__doc__)
        return 1
    c = argv[0]
    if c == "fetch":
        cmd_fetch(argv[1] if len(argv) > 1 else None)
    elif c == "refs":
        cmd_refs()
    elif c == "reports":
        cmd_reports()
    elif c == "colors":
        cmd_colors()
    elif c == "probe":
        cmd_probe()
    elif c == "modtest":
        cmd_modtest()
    elif c == "world":
        from .build_world import ci_world
        return ci_world(argv[1:])
    else:
        print(__doc__)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
