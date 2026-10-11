"""연결 검토: 모든 도착 자리(설 자리·발밑·TP 구역 안 아님)와 걷기 구역(가운데 빈칸·바닥·목적지)을 확인하고 층 사슬을 출력.

사용: python build.py check 처럼 빌드 후 pickle 로 저장한 Build 를 넣어 실행 — python tools/review_links.py <build.pkl>
"""
import sys, pickle
sys.path.insert(0, '.')
b = pickle.load(open(sys.argv[1], 'rb'))
L = b.links
dims = {d.dim: d for d in b.dims.values()}
PASS = ("minecraft:air", "minecraft:light", "carpet", "pressure_plate", "minecraft:cave_vines", "snow[layers=1]")
def passable(s): return s == "minecraft:air" or any(p in s for p in PASS[1:])
issues = []
for n, a in L.anchors.items():
    d = dims[a.dim]; x, y, z = int(a.x // 1), int(a.y), int(a.z // 1)
    feet, head, below = d.get(x, y, z), d.get(x, y + 1, z), d.get(x, y - 1, z)
    if not passable(feet) or not passable(head):
        issues.append(f"자리 {n}: 발/머리 막힘 {feet} / {head}")
    if below == "minecraft:air":
        issues.append(f"자리 {n}: 발밑이 빔")
    for w in L.walks:
        if w.dim != a.dim: continue
        x0, y0, z0, x1, y1, z1 = w.box
        if x0 <= x <= x1 and y0 - 1 <= y <= y1 and z0 <= z <= z1:
            issues.append(f"자리 {n}: TP 구역 안 ({w.dest}) → 도착하자마자 다시 이동")
for w in L.walks:
    d = dims[w.dim]; x0, y0, z0, x1, y1, z1 = w.box
    cx, cz = (x0 + x1) // 2, (z0 + z1) // 2
    ys = [y for y in range(y0, y1 + 1) if passable(d.get(cx, y, cz))]
    floor = any(d.get(cx, y - 1, cz) != "minecraft:air" for y in range(y0, y1 + 1) if passable(d.get(cx, y, cz)))
    if not ys: issues.append(f"구역 → {w.dest} {w.box}: 가운데가 꽉 막힘")
    if not floor: issues.append(f"구역 → {w.dest} {w.box}: 디딜 바닥 없음")
    if w.dest not in L.anchors: issues.append(f"구역 → {w.dest}: 도착 자리 없음")
print("자리", len(L.anchors), "구역", len(L.walks))
print("\n".join(issues) or "문제 없음")
# 층 사슬
order = ["exterior","lobby","history","technology","literature","art","natural_science","language","social_science","philosophy","religion","general"]
for w in L.walks:
    src = w.dim.split(":")[1]; dst = L.anchors[w.dest].dim.split(":")[1]
    print(f"  {src:16s} {str(w.box):40s} → {w.dest:26s} ({dst})")
