"""BSL 쉐이더팩 맵 전용 개조 → out/release/BSL_v10.1.6_Ruina.zip

원본: shaderpack/BSL_v10.1.6.zip (사용자 제공). 원본은 그대로 두고 이 스크립트로만 고친다 (다시 만들 수 있게).
사용: python -m tools.shaderpack

고치는 것 (테스트 2차: BSL에서 층·방이 너무 어두움, GTX1050ti 26~50fps):
1. dimension.properties: 외부(ruina:exterior)는 그대로 world0, 나머지 ruina 공간은 새 폴더 `ruina`
   (world0 복사 + `#define RUINA`)
2. RUINA 에서는 밤빛(lightNight·ambientNight)을 공간의 안개색(fogColor = 차원·바이옴 환경 속성)에서 만든다
   → 모든 공간이 자정에 멈춰 있어도(BSL은 오버월드 시계를 읽음) 층마다 원화 색의 빛·안개, 너무 어둡지 않게.
   최소 밝기(minLightCol)도 올려 지붕 아래 방이 새까맣지 않게
3. RUINA 에서는 하늘색을 바닐라 값(SKY_VANILLA 경로 = 우리 환경 속성 하늘색)으로
4. 기본 설정을 가볍게: 그림자 1536/192, 구름 끔 (맵에 블록 구름이 있음)
5. 모드 호환 (2026-10-12, 모드화 ①): 모드는 아무 월드(야생)에나 들어가므로 오버월드 시계가 정상으로 흐른다.
   → world0(원본)은 오버월드·다른 차원 전용으로 그대로 두고, 외부는 새 폴더 `ruina_ext`(world0 복사 + 밤 고정),
   로비·층은 `ruina`(+ 밤 고정). 밤 고정(RUINA_NIGHT_LOCK) = BSL 의 시간 값(timeAngle·timeBrightness·shadowFade·worldTime)을
   자정 상수로 → 어느 시계를 읽든(오버월드가 낮이어도) 도서관은 늘 원화의 밤빛
"""
from __future__ import annotations

import io
import os
import re
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "shaderpack", "BSL_v10.1.6.zip")
OUT = os.path.join(ROOT, "out", "release", "BSL_v10.1.6_Ruina.zip")
NS = "ruina"
OUTSIDE = ["ruina:exterior"]          # world0 그대로 (BSL 밤하늘이 원화와 잘 맞음 — 테스트 2차 ①)

EXT = "ruina_ext"   # 외부 폴더 (원본 BSL 그대로 + 밤 고정)

DIMENSION_PROPERTIES = """#BSL Shaders Dimension Mapping (Library of Ruina 맵 개조)

dimension.world0 = minecraft:overworld *
dimension.world-1 = minecraft:the_nether
dimension.world1 = minecraft:the_end
dimension.{ext} = {outside}
dimension.ruina = {inside}
"""

# 밤 고정: BSL 시간 uniform(shaders.properties 의 사용자 정의 uniform 포함)을 자정 값 상수로.
# sunAngle 0.75(자정) 를 shaders.properties 식에 넣은 값: timeAngle 0.75, timeBrightness 0, shadowFade 1
NIGHT_LOCK = {"timeAngle": "0.75", "timeBrightness": "0.0", "shadowFade": "1.0", "worldTime": "18000"}
NIGHT_LOCK_DEFINE = "#define RUINA_NIGHT_LOCK\n"

# lightColor.glsl 의 밤빛 두 줄(달 위상 있음/없음 모두)을 바꿈
RUINA_NIGHT = """#ifdef RUINA
// Library of Ruina: 공간 안개색(차원·바이옴 환경 속성)으로 빛 색을 정함. 모든 공간이 자정이라 밤빛 = 그 공간의 빛
#ifndef RUINA_FOG_DECLARED
#define RUINA_FOG_DECLARED
uniform vec3 fogColor;
#endif
float ruinaMax = max(fogColor.r, max(fogColor.g, fogColor.b));
vec3 ruinaTint = mix(vec3(1.0), fogColor / max(ruinaMax, 0.02), RUINA_TINT);
float ruinaBright = mix(RUINA_MIN_BRIGHT, 1.0, sqrt(clamp(dot(fogColor, vec3(0.299, 0.587, 0.114)), 0.0, 1.0)));
vec3 lightNight      = ruinaTint * RUINA_LIGHT * ruinaBright;
vec3 ambientNight    = ruinaTint * RUINA_AMBIENT * ruinaBright;
#else
"""

RUINA_DEFINES = """#define RUINA
#define RUINA_TINT 0.65
#define RUINA_MIN_BRIGHT 0.45
#define RUINA_LIGHT 0.75
#define RUINA_AMBIENT 0.50
#define RUINA_MINLIGHT 5.0
"""


def _night_lock(s: str) -> str:
    """시간 uniform 선언을 밤 고정일 때 상수 #define 으로 (선언이 여러 번 나와도 안전하게)."""
    def sub(m):
        decl = m.group(0)
        names = [n.strip() for n in m.group(2).split(",")]
        if not any(n in NIGHT_LOCK for n in names):
            return decl
        keep = [n for n in names if n not in NIGHT_LOCK]
        out = ["#ifndef RUINA_NIGHT_LOCK", decl, "#else"]
        if keep:
            out.append(f"uniform {m.group(1)} {', '.join(keep)};")
        for n in names:
            if n in NIGHT_LOCK:
                out += [f"#ifndef {n}", f"#define {n} {NIGHT_LOCK[n]}", "#endif"]
        out.append("#endif")
        return "\n".join(out)
    return re.sub(r"uniform (float|int) ([A-Za-z_][\w, ]*);", sub, s)


def _patch_light_color(s: str) -> str:
    start = s.index("#ifdef NIGHT_MOON_PHASE")
    end = s.index("#endif", s.index("#else", start)) + len("#endif")
    return s[:start] + RUINA_NIGHT + s[start:end] + "\n#endif" + s[end:]


def _patch_dimension_color(s: str) -> str:
    a = "vec3 minLightCol\t = minLightColSqrt * minLightColSqrt * 0.04;"
    if a not in s:
        a = re.search(r"vec3 minLightCol\s*=\s*minLightColSqrt \* minLightColSqrt \* 0\.04;", s).group(0)
    b = ("#ifdef RUINA\nvec3 minLightCol = minLightColSqrt * minLightColSqrt * 0.04 * RUINA_MINLIGHT;\n#else\n"
         + a + "\n#endif")
    return s.replace(a, b)


def _guard_fog(s: str) -> str:
    """fogColor 를 RUINA 블록에서 먼저 선언했으면 다시 선언하지 않게."""
    return s.replace("uniform vec3 fogColor;", "#ifndef RUINA_FOG_DECLARED\n#define RUINA_FOG_DECLARED\n"
                                               "uniform vec3 fogColor;\n#endif")


def _patch_settings(s: str) -> str:
    rep = [
        (r"const int shadowMapResolution = 2048;", "const int shadowMapResolution = 1536;"),
        (r"const float shadowDistance = 256.0;", "const float shadowDistance = 192.0;"),
        (r"#define CLOUDS 2 //", "#define CLOUDS 0 //"),
    ]
    for a, b in rep:
        assert a in s, a
        s = s.replace(a, b)
    return s


def _patch_properties(s: str) -> str:
    """program.world0/<프로그램>.enabled=... 줄을 ruina 폴더에도 (없으면 그 프로그램이 항상 켜져서
    다색 블록빛 끈 상태의 shadowcomp 가 컴파일 실패 — 테스트 3차 ⑭)."""
    lines = s.split("\n")
    out = []
    for line in lines:
        out.append(line)
        if line.startswith("program.world0/"):
            for folder in (NS, EXT):
                out.append(line.replace("program.world0/", f"program.{folder}/", 1))
    assert any(l.startswith(f"program.{NS}/shadowcomp") for l in out)
    assert any(l.startswith(f"program.{EXT}/shadowcomp") for l in out)
    return "\n".join(out)


def _patch_sky_color(s: str) -> str:
    """RUINA 공간은 바닐라 하늘색 (= 우리 환경 속성 하늘·안개색). 옵션 SKY_VANILLA 는 건드리지 않음 (설정 메뉴용)."""
    s = _guard_fog(s)
    a = "#ifdef SKY_VANILLA"
    assert s.startswith(a), s[:40]
    return "#if defined SKY_VANILLA || defined RUINA" + s[len(a):]


def build(spaces: list[str]) -> str:
    inside = [d for d in spaces if d not in OUTSIDE]
    src = zipfile.ZipFile(SRC)
    files = {n: src.read(n) for n in src.namelist() if not n.endswith("/")}
    out = {}
    locked = 0
    for n, data in files.items():
        if n.startswith("shaders/world0/"):
            text = data.decode("utf-8")
            for folder, defines in ((NS, NIGHT_LOCK_DEFINE + RUINA_DEFINES), (EXT, NIGHT_LOCK_DEFINE)):
                t = text
                if "#define OVERWORLD" in t:      # 셰이더 파일 (.fsh/.vsh/.glsl)
                    t = t.replace("#define OVERWORLD", "#define OVERWORLD\n" + defines, 1)
                else:
                    assert not n.endswith((".fsh", ".vsh", ".gsh", ".csh")), n
                out[n.replace("shaders/world0/", f"shaders/{folder}/")] = t.encode()
        if n.endswith((".glsl", ".fsh", ".vsh", ".gsh", ".csh")) and n.startswith(("shaders/program/", "shaders/lib/")):
            t = data.decode("utf-8")
            t2 = t
            if n == "shaders/lib/lighting/shadows.glsl":   # 같은 이름의 지역 변수 (밤 고정 #define 과 겹침)
                t2 = re.sub(r"\bshadowFade\b", "shadowFadeLocal", t2)
            t2 = _night_lock(t2)
            if t2 != t:
                locked += 1
                data = t2.encode()
        if n == "shaders/dimension.properties":
            data = DIMENSION_PROPERTIES.format(ext=EXT, outside=" ".join(OUTSIDE), inside=" ".join(inside)).encode()
        elif n == "shaders/lib/color/lightColor.glsl":
            data = _patch_light_color(data.decode()).encode()
        elif n == "shaders/lib/color/dimensionColor.glsl":
            data = _patch_dimension_color(data.decode()).encode()
        elif n == "shaders/lib/color/skyColor.glsl":
            data = _patch_sky_color(data.decode()).encode()
        elif n in ("shaders/lib/atmospherics/waterFog.glsl", "shaders/lib/color/netherColor.glsl"):
            data = _guard_fog(data.decode()).encode()
        elif n == "shaders/shaders.properties":
            data = _patch_properties(data.decode()).encode()
        elif n == "shaders/lib/settings.glsl":
            data = _patch_settings(data.decode()).encode()
        out[n] = data
    out["shaders/RUINA_README.txt"] = (
        "Library of Ruina 맵 전용으로 고친 BSL v10.1.6 (원작: Capt Tatsu, https://capttatsu.com)\n"
        "바꾼 것: tools/shaderpack.py 설명 참고. 오버월드는 원본 그대로, 도서관 외부는 원본 + 밤 고정,\n"
        "로비·층은 공간 안개색으로 빛을 정함 + 밤 고정 (도서관 모드와 함께 아무 월드에서).\n").encode()
    assert locked >= 10, f"밤 고정 대상 파일이 너무 적음: {locked}"
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for n in sorted(out):
            z.writestr(n, out[n])
    with open(OUT, "wb") as f:
        f.write(buf.getvalue())
    return OUT


def main():
    import sys
    sys.path.insert(0, ROOT)
    import config
    p = build([s.dim for s in config.SPACES])
    print(p, os.path.getsize(p))


if __name__ == "__main__":
    main()
