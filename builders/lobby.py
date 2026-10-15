"""로비 (앤젤라). 두 모습: 전환 전 '어두운 나무 방' ↔ 전환 후 '밝은 책장 홀' — 자유 형체 판 (2026-10-15).

- 방: builders/lobby_room.py (reference/로비.png, 3D 영상 01~07)
- 홀: builders/lobby_hall.py (reference/로비 전경 (전환 후).jpg, 3D 영상 08~19)
두 공간은 같은 차원(ruina:lobby)에서 HALL_DX만큼 떨어져 있고, 방전환 우클릭으로 서로의 도착 자리로
순간이동한다 (두 도착 자리가 다른 높이·구도라 같은 상대 위치 대신 고정 자리). 방 남쪽 검은 문으로 걸어 나가면 외부 정문 앞으로.
"""
from __future__ import annotations

Y0 = 64            # 서 있는 높이 (홀 바닥, 방 북쪽 벽 앞)
HALL_DX = 512      # 홀 = 방 + (512, 0, 0)


def build(b):
    from . import fragment as F
    from . import lobby_hall, lobby_room
    d = b.dim("lobby")
    arrive = lobby_room.build(b, d)
    hall = lobby_hall.build(b, d)
    L = b.links
    F.stage(b, d, "silver", "로비", arrive, hall,
            room_box=f"x={HALL_DX // 2},y=-64,z=-1024,dx=4096,dy=1024,dz=2048",
            scene_name="lobby_entrance", room_name="lobby_hall")
    zs = int(lobby_room.ZS)
    yf = lobby_room.YF
    L.portal(d.dim, 0.5, yf, zs + 0.5, "exterior_gate", width=3, height=4)
    L.walk(d.dim, (-1, yf, zs, 1, yf + 2, zs), "exterior_gate", fade=True)
    b.extra_checks += [
        {"what": "홀 바이옴 ruina:lobby_hall", "cmd": f"execute in {d.dim} if biome {HALL_DX} {Y0} 0 ruina:lobby_hall",
         "expect": True},
        {"what": "방 바이옴 ruina:lobby", "cmd": f"execute in {d.dim} if biome 0 {Y0} 0 ruina:lobby", "expect": True},
    ]
