"""GitHub Actions에서 실행하는 단계들.

python -m tools.ci fetch            서버 jar 다운로드, Java 버전 출력
python -m tools.ci refs             jar에서 version.json·바닐라 JSON 추출 → ci_out/ref
python -m tools.ci reports          데이터 생성기 reports → 블록/레지스트리 목록 → ci_out/ref
python -m tools.ci probe            포맷 프로브: 바닐라 월드 + 우리 데이터팩 월드를 만들어 NBT 덤프
python -m tools.ci world            실제 월드 빌드 (서버 2회 실행 + 검증 + zip)
"""
from __future__ import annotations

import glob
import json
import os
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
        if any(name.startswith(p) for p in REF_PATTERNS) and not name.endswith("/"):
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
    elif c == "probe":
        cmd_probe()
    elif c == "world":
        from .build_world import ci_world
        return ci_world(argv[1:])
    else:
        print(__doc__)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
