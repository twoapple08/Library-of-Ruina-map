#!/usr/bin/env bash
# 작업 환경(클라우드 세션)에서 CI 와 같은 확인을 직접: 건축물(재사용 또는 빌드) → 모드 빌드 → 게임 테스트.
#   bash tools/local_test.sh            바닐라 게임 테스트 (약 17분)
#   bash tools/local_test.sh bsl        + Iris+Sodium+맵 전용 BSL (장소당 5~6분, 소프트웨어 GL)
#   bash tools/local_test.sh build      건축물·모드 빌드만
#   bash tools/local_test.sh only <공간>  건축물은 있는 그대로(world.zip) 두고 그 공간만 게임 테스트 (작업 중 확인, 몇 분)
# 결과: python -m tools.ci modtest → ci_out/mod/ (sheet.jpg, sheet_bsl.jpg, SUMMARY.md)
# 주의: 이 환경의 Xvfb 에서는 GLX 창을 못 만듦 ("Couldn't find matching GLX visual") → SDL 을 EGL 로 (SDL_VIDEO_FORCE_EGL=1)
set -e
cd "$(dirname "$0")/.."
# 환경 기본 JAVA_HOME 이 21 일 수 있음 (Loom 은 25 필요) → 있으면 항상 /opt/jdk25
[ -d /opt/jdk25 ] && JAVA_HOME=/opt/jdk25
export JAVA_HOME=${JAVA_HOME:-/opt/jdk25} PATH=/opt/jdk25/bin:$PATH SDL_VIDEO_FORCE_EGL=1 XDG_RUNTIME_DIR=/tmp/xdg
mkdir -p /tmp/xdg && chmod 700 /tmp/xdg
# 새 컨테이너에는 libEGL 이 없을 수 있음 → 게임이 "Could not load EGL library" 로 멈춤
if [ "$1" != build ] && ! ls /usr/lib/x86_64-linux-gnu/libEGL.so.1 > /dev/null 2>&1; then
  apt-get install -y -q libegl1 libegl-mesa0 libgbm1 > /dev/null 2>&1 \
    || { apt-get update -q > /dev/null 2>&1 && apt-get install -y -q libegl1 libegl-mesa0 libgbm1 > /dev/null 2>&1; }
fi
if [ ! -f mod/build/generated/ruina/ruina/world.zip ]; then
  python -m tools.world_cache fetch || { python -m tools.ci fetch && python -m tools.ci refs && python -m tools.ci reports \
    && python -m tools.ci world && python -m tools.world_cache save; }
fi
(cd mod && ./gradlew build -q)
[ "$1" = build ] && exit 0
python -m tools.shaderpack > /dev/null
cd mod
R=build/run/clientGameTest
rm -rf build/vanilla
set +e
ONLY=""
[ "$1" = only ] && ONLY="-Ponly=$2"
xvfb-run -a -s "-screen 0 1920x1080x24" ./gradlew runClientGameTest $ONLY > build/gametest_gradle.log 2>&1
export GAMETEST_OUTCOME=$([ $? = 0 ] && echo success || echo failure)
if [ "$1" = bsl ]; then
  mkdir -p build/vanilla && cp -r $R/screenshots $R/ruina_test.txt $R/logs/latest.log build/vanilla/
  xvfb-run -a -s "-screen 0 1920x1080x24" ./gradlew runClientGameTest -Pshaders > build/gametest_bsl_gradle.log 2>&1
  export GAMETEST_BSL_OUTCOME=$([ $? = 0 ] && echo success || echo failure)
fi
cd .. && python -m tools.ci modtest | grep -v "ℹ️"
