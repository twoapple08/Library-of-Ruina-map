"""로컬 빌드 도구.

python build.py previews     빌더 실행 → previews/*.png (폰 확인용)
python build.py proto        외부 시제품 미리보기 (약 30초)
python build.py datapack     out/datapack 생성
python build.py check        빌더 실행 + 블록 품질 검사 (숨은 블록, 흐르는 물, 떠 있는 랜턴 등)
실제 월드(.zip)는 GitHub Actions(build.yml)가 서버로 만든다.
"""
import os
import sys
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)


def main(argv):
    from builders import build_all
    from tools import datapack
    cmd = argv[0] if argv else "check"
    t0 = time.time()
    b = build_all()
    print(f"빌더 {time.time() - t0:.1f}초: " + ", ".join(f"{k} {len(d.chunk_keys())}청크" for k, d in b.dims.items()))
    if cmd == "check":
        from tools.lint import lint_build
        print("\n".join(lint_build(b)))
    elif cmd == "datapack":
        datapack.write(os.path.join(ROOT, "out", "datapack"), b.links)
    elif cmd == "proto":
        from builders.previews import render_proto
        for p in render_proto(os.path.join(ROOT, "previews")):
            print("  ", os.path.relpath(p, ROOT))
    elif cmd == "previews":
        from builders.previews import render_all
        for p in render_all(b, os.path.join(ROOT, "previews")):
            print("  ", os.path.relpath(p, ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
