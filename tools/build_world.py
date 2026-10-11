"""CI 월드 빌드: 실제 서버로 월드를 만들고, 우리가 만든 청크를 넣고, 서버가 제대로 읽는지 검증한다.

1차 실행: 데이터팩을 넣은 새 월드 생성 → 26.3이 직접 만든 level.dat·폴더 구조 확보
생성기: dimensions/ruina/<공간>/region/*.mca 작성
2차 실행: 블록·블록엔티티·TP 함수 검증, 상호작용 엔티티 소환, 게임룰·스폰 설정
후처리: 조명 계산 확인, level.dat 치트 허용, zip
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import time
import zipfile

from . import nbt, region, world as W
from .server import LOG_LINE, Server, prepare_dir

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, ".server")
OUT = os.path.join(ROOT, "ci_out", "world")
RELEASE = os.path.join(ROOT, "out", "release")
WORLD_NAME = "Library of Ruina"


class Report:
    def __init__(self):
        self.ok = True
        self.lines: list[str] = []
        self.data: dict = {}

    def add(self, ok: bool, msg: str):
        self.lines.append(("✅ " if ok else "❌ ") + msg)
        print(self.lines[-1], flush=True)
        if not ok:
            self.ok = False

    def info(self, msg: str):
        self.lines.append("ℹ️ " + msg)
        print(self.lines[-1], flush=True)


def _bad_lines(srv: Server) -> list[str]:
    """서버 로그 중 WARN/ERROR 줄 (오프라인 모드 안내 경고 제외). 압축 해제·JVM 경고는 로그 형식이 아니라 빠짐."""
    skip = ("OFFLINE/INSECURE", "authenticate usernames", "hackers to connect", '"online-mode"',
            "Can't keep up!")  # 빌드 중 청크를 한꺼번에 불러올 때 나는 성능 경고 (무해)
    out = []
    for l in srv.lines:
        m = LOG_LINE.match(l)
        if m and m.group(2) in ("WARN", "ERROR", "FATAL") and not any(k in l for k in skip):
            out.append(l)
    return out


def _forceload(srv: Server, dim: str, chunks: set, rep: Report) -> bool:
    for cx, cz in sorted(chunks):
        srv.run(f"execute in {dim} run forceload add {cx * 16} {cz * 16}")
    ok = True
    for cx, cz in sorted(chunks):
        if not srv.wait_loaded(dim, cx * 16, 64, cz * 16, timeout=90):
            rep.add(False, f"{dim} 청크 {cx},{cz} 로드 안 됨")
            ok = False
    return ok


def ci_world(argv) -> int:
    sys.path.insert(0, ROOT)
    from builders import build_all
    from tools import datapack
    import config

    shutil.rmtree(OUT, ignore_errors=True)
    os.makedirs(OUT, exist_ok=True)
    rep = Report()
    with open(os.path.join(CACHE, "info.json")) as f:
        info = json.load(f)
    rep.info(f"마인크래프트 {info['id']} / Java {info['java']}")

    # ---------------------------------------------- 빌더 실행
    t0 = time.time()
    b = build_all()
    dp = os.path.join(CACHE, "datapack")
    datapack.write(dp, b.links)
    from tools.lint import lint_build
    for line in lint_build(b):
        rep.info("검사: " + line.strip())
    rep.info(f"빌더 {time.time() - t0:.1f}초: " + ", ".join(f"{k} {len(d.chunk_keys())}청크" for k, d in b.dims.items()))

    # ---------------------------------------------- 1차 실행
    sdir = os.path.join(CACHE, "world_server")
    shutil.rmtree(sdir, ignore_errors=True)
    prepare_dir(sdir, info["jar"])
    wdir = os.path.join(sdir, "world")
    shutil.copytree(dp, os.path.join(wdir, "datapacks", "ruina"))
    srv = Server(sdir, log_path=os.path.join(OUT, "server1.log"))
    try:
        srv.start()
        packs = " ".join(srv.run("datapack list enabled"))
        rep.add("file/ruina" in packs, "데이터팩 켜짐")
        for s in b.dims.values():
            out = srv.run(f"execute in {s.dim} run say dim-ok")
            rep.add(not any("Unknown" in o or "Invalid" in o for o in out), f"차원 {s.dim} 존재")
    finally:
        srv.stop()
    bad = _bad_lines(srv)
    rep.add(not bad, f"1차 실행 로그 경고/오류 {len(bad)}줄")
    rep.data["server1_problems"] = bad

    level = nbt.read_file(os.path.join(wdir, "level.dat"))
    dv = int(level["Data"]["DataVersion"])
    rep.info(f"DataVersion {dv}")

    # ---------------------------------------------- 청크 쓰기
    t0 = time.time()
    total = 0
    for sid, d in b.dims.items():
        rdir = os.path.join(wdir, "dimensions", *d.dim.split(":"), "region")
        if os.path.isdir(rdir):
            shutil.rmtree(rdir)  # 1차 실행이 만든 빈 청크 제거
        total += d.write_regions(rdir, dv)
    rep.info(f"청크 {total}개 쓰기 {time.time() - t0:.1f}초")

    # ---------------------------------------------- 2차 실행: 검증
    checks = b.block_checks()
    lights = b.light_checks()
    srv = Server(sdir, log_path=os.path.join(OUT, "server2.log"))
    fails = []
    try:
        srv.start()
        by_dim: dict[str, set] = {}
        for c in checks + lights:
            by_dim.setdefault(c["dim"], set()).add((c["x"] >> 4, c["z"] >> 4))
        for p in b.links.portals:
            by_dim.setdefault(p.dim, set()).add((int(p.x) >> 4, int(p.z) >> 4))
        for a in b.links.anchors.values():
            by_dim.setdefault(a.dim, set()).add((int(a.x) >> 4, int(a.z) >> 4))
        for dim, chunks in by_dim.items():
            _forceload(srv, dim, chunks, rep)

        passed = 0
        for c in checks:
            ok = srv.test(f"execute in {c['dim']} if block {c['x']} {c['y']} {c['z']} {c['state']}")
            passed += ok
            if not ok:
                fails.append(c)
        rep.add(passed == len(checks), f"블록 검증 {passed}/{len(checks)} (팔레트 형식 {W.PALETTE_FORMAT})")

        for e in b.extra_checks:
            for c in e.get("setup", []):
                srv.run(c)
            got = srv.test(e["cmd"])
            rep.add(got == e["expect"], f"{e['what']}: {e['cmd']}")

        # 상호작용 엔티티 소환
        out = srv.run("function ruina:build/entities")
        rep.data["entities_cmd"] = out
        for p in b.links.portals:
            ok = srv.test(f"execute in {p.dim} positioned {p.x} {p.y} {p.z} if entity "
                          f"@e[type=minecraft:interaction,tag=ruina.to.{p.dest},distance=..0.5]")
            rep.add(ok, f"TP 엔티티 {p.dim} ({p.x}, {p.y}, {p.z}) → {p.dest}")

        # TP 함수: 마커 엔티티를 TP시켜 도착 확인
        for name, a in b.links.anchors.items():
            src = b.links.anchors[b.links.spawn] if b.links.spawn else a
            srv.run(f"execute in {src.dim} run summon minecraft:marker {src.x} {src.y} {src.z} {{Tags:[\"ruina.tptest\"]}}")
            srv.run(f"execute as @e[type=minecraft:marker,tag=ruina.tptest] run function ruina:tp/to/{name}")
            ok = srv.test(f"execute in {a.dim} positioned {a.x} {a.y} {a.z} if entity "
                          f"@e[type=minecraft:marker,tag=ruina.tptest,distance=..0.5]")
            rep.add(ok, f"TP 함수 ruina:tp/to/{name} → {a.dim} ({a.x}, {a.y}, {a.z})")
            srv.run("kill @e[type=minecraft:marker,tag=ruina.tptest]")

        # 걷기 TP: 마커를 구역 안에 두고 같은 선택자로 함수 실행 → 도착 확인
        for w in b.links.walks:
            x0, y0, z0, x1, y1, z1 = w.box
            cx, cy, cz = (x0 + x1 + 1) / 2, y0 + 0.1, (z0 + z1 + 1) / 2
            srv.run(f"execute in {w.dim} run summon minecraft:marker {cx} {cy} {cz} {{Tags:[\"ruina.walktest\"]}}")
            sel = w.selector("@e[type=minecraft:marker,tag=ruina.walktest]")
            srv.run(f"execute in {w.dim} as {sel} run function ruina:tp/to/{w.dest}")
            a = b.links.anchors[w.dest]
            ok = srv.test(f"execute in {a.dim} positioned {a.x} {a.y} {a.z} if entity "
                          f"@e[type=minecraft:marker,tag=ruina.walktest,distance=..0.5]")
            rep.add(ok, f"걷기 TP {w.dim} {w.box} → {w.dest}")
            srv.run("kill @e[type=minecraft:marker,tag=ruina.walktest]")

        # 암전 TP: 마커로 시작 → fade_tick 을 직접 여러 번 실행 (tick 은 플레이어만 처리) → 도착 + 암전 해제 확인
        for w in [w for w in b.links.walks if w.fade]:
            a = b.links.anchors[w.dest]
            x0, y0, z0, x1, y1, z1 = w.box
            # 플레이어가 없으니 도착지 둘레 청크를 직접 불러옴 (게임에서는 플레이어가 불러옴)
            r = datapack.LOAD_R
            srv.run(f"execute in {a.dim} run forceload add {int(a.x) - r} {int(a.z) - r} {int(a.x) + r} {int(a.z) + r}")
            time.sleep(3)
            srv.run(f"execute in {w.dim} run summon minecraft:marker {(x0 + x1 + 1) / 2} {y0 + 0.1} {(z0 + z1 + 1) / 2} "
                    f"{{Tags:[\"ruina.fadetest\"]}}")
            srv.run(f"execute as @e[type=minecraft:marker,tag=ruina.fadetest] run function ruina:tp/fade/{w.dest}")
            outs = []
            for _ in range(datapack.FADE_MIN + 2):
                outs.append(srv.run("execute as @e[type=minecraft:marker,tag=ruina.fadetest] at @s run function ruina:tp/fade_tick"))
            diag = {
                "ticks": outs[:1] + outs[9:12] + outs[-2:],
                "arrived": srv.test(f"execute in {a.dim} positioned {a.x} {a.y} {a.z} if entity "
                                    f"@e[type=minecraft:marker,tag=ruina.fadetest,distance=..0.5]"),
                "fading": srv.test("execute if entity @e[type=minecraft:marker,tag=ruina.fadetest,tag=ruina.fading]"),
                "score": srv.run("scoreboard players list @e[type=minecraft:marker,tag=ruina.fadetest,limit=1]"),
                "loaded": srv.test(f"execute in {a.dim} positioned {a.x} {a.y} {a.z} if loaded ~-{r} ~ ~-{r} "
                                   f"if loaded ~{r} ~ ~{r}"),
            }
            rep.data.setdefault("fade_diag", {})[w.dest] = diag
            ok = srv.test(f"execute in {a.dim} positioned {a.x} {a.y} {a.z} if entity "
                          f"@e[type=minecraft:marker,tag=ruina.fadetest,tag=!ruina.fading,distance=..0.5]")
            rep.add(ok, f"암전 TP {w.dim} {w.box} → {w.dest} (도착 + 로딩 확인 후 해제)")
            srv.run("kill @e[type=minecraft:marker,tag=ruina.fadetest]")

        # 시계: 문법 확인용 도움말 + 직접 실행해서 결과 기록
        rep.data["help_time"] = srv.run("help time")
        tout = {}
        for c in datapack.time_commands():
            tout[c] = srv.run(c)
        rep.data["time_cmds"] = tout
        bad_t = [c for c, o in tout.items() if any(k in " ".join(o) for k in ("Unknown", "Incorrect", "Can't", "Invalid", "<--[HERE]"))]
        rep.add(not bad_t, f"시계 고정 ({len(tout) - len(bad_t)}/{len(tout)} 명령 성공)")
        # 각 차원에서 본 시각 (쉐이더가 읽는 값): 모두 자정이어야 함
        tq = {}
        for dim in by_dim:
            tq[dim] = srv.run(f"execute in {dim} run time query time")
        tq["clock"] = srv.run(f"time of {datapack.CLOCK} query time")
        rep.data["time_query"] = tq

        def _ticks(lines):  # "Clock minecraft:overworld is at 138001 tick(s)" → 138001
            import re
            m = re.search(r"at (\d+) tick", " ".join(lines))
            return int(m.group(1)) if m else None
        # 멈추기 전에 한두 틱 흐를 수 있음 → ±20틱 허용 (하루 24000틱 중 자정 근처면 됨)
        bad_q = [k for k, o in tq.items() if _ticks(o) is None or abs(_ticks(o) - config.CLOCK_TIME) > 20]
        rep.add(not bad_q, f"차원별 시각 = 자정 {config.CLOCK_TIME} (어긋남: {bad_q})")
        out = srv.run("function ruina:setup")
        rep.data["setup_cmd"] = out
        for dim in by_dim:
            srv.run(f"execute in {dim} run forceload remove all")
        srv.run("save-all flush", timeout=300)
    finally:
        srv.stop()
    rep.data["block_fails"] = fails[:50]
    bad = _bad_lines(srv)
    rep.add(not bad, f"2차 실행 로그 경고/오류 {len(bad)}줄")
    rep.data["server2_problems"] = bad

    # ---------------------------------------------- 후처리 검증 (서버가 다시 저장한 청크 읽기)
    lit = 0
    for c in lights:
        d = c["dim"].split(":")
        mca = os.path.join(wdir, "dimensions", *d, "region", region.region_name(c["x"] >> 9, c["z"] >> 9))
        ch = region.read_region(mca).get((c["x"] >> 4, c["z"] >> 4))
        lvl = _block_light(ch, c["x"], c["y"], c["z"]) if ch else None
        c["light"] = lvl
        lit += bool(lvl)
    rep.add(lit == len(lights), f"조명 계산 {lit}/{len(lights)} (광원 옆 칸의 블록 빛 > 0)")
    rep.data["lights"] = lights
    # 저장된 청크 하나 덤프 (형식 비교용)
    for sid, d in b.dims.items():
        k = sorted(d.chunk_keys())[0]
        mca = os.path.join(wdir, "dimensions", *d.dim.split(":"), "region", region.region_name(k[0] >> 5, k[1] >> 5))
        ch = region.read_region(mca).get(k)
        with open(os.path.join(OUT, f"saved_chunk_{sid}_{k[0]}_{k[1]}.snbt"), "w") as f:
            f.write(nbt.to_snbt(ch, max_array=6) if ch else "없음")
        ents = os.path.join(wdir, "dimensions", *d.dim.split(":"), "entities")
        for p in sorted(os.listdir(ents)) if os.path.isdir(ents) else []:
            for key, ech in region.read_region(os.path.join(ents, p)).items():
                with open(os.path.join(OUT, f"saved_entities_{sid}_{key[0]}_{key[1]}.snbt"), "w") as f:
                    f.write(nbt.to_snbt(ech, max_array=6))

    # level.dat: 싱글플레이 치트 허용, 크리에이티브
    lp = os.path.join(wdir, "level.dat")
    level = nbt.read_file(lp)
    level["Data"]["allowCommands"] = nbt.Byte(1)
    level["Data"]["GameType"] = nbt.Int(1)
    level["Data"]["LevelName"] = WORLD_NAME
    nbt.write_file(lp, level)
    with open(os.path.join(OUT, "level.dat.snbt"), "w") as f:
        f.write(nbt.to_snbt(level))
    rep.info(f"스폰: {level['Data'].get('spawn')}")

    # ---------------------------------------------- zip
    os.makedirs(RELEASE, exist_ok=True)
    zpath = os.path.join(RELEASE, "Library-of-Ruina.zip")
    n = 0
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for base, dirs, files in os.walk(wdir):
            for fn in files:
                if fn in ("session.lock", "level.dat_old"):
                    continue
                full = os.path.join(base, fn)
                z.write(full, os.path.join(WORLD_NAME, os.path.relpath(full, wdir)))
                n += 1
    rep.info(f"zip {os.path.getsize(zpath) / 1e6:.1f} MB, 파일 {n}개")

    with open(os.path.join(OUT, "report.json"), "w") as f:
        json.dump({"ok": rep.ok, "lines": rep.lines, **rep.data}, f, indent=2, ensure_ascii=False, default=str)
    summary = "\n".join(["## 월드 빌드 결과", ""] + [f"- {l}" for l in rep.lines]) + "\n"
    with open(os.path.join(OUT, "SUMMARY.md"), "w") as f:
        f.write(summary)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as f:
            f.write(summary)
    return 0 if rep.ok else 1


def _block_light(chunk: dict, x: int, y: int, z: int):
    for sec in chunk.get("sections", []):
        if sec["Y"] == y >> 4:
            bl = sec.get("BlockLight")
            if bl is None:
                return 0
            i = ((y & 15) << 8) | ((z & 15) << 4) | (x & 15)
            v = int(bl[i >> 1]) & 0xFF
            return (v >> 4) if (i & 1) else (v & 15)
    return None
