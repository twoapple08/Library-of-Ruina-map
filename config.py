"""맵 전체 설정. 수치의 근거는 PLAN.md.

여기 값을 바꾸면 데이터팩·월드·미리보기가 모두 같이 바뀐다.
"""
from dataclasses import dataclass, field

NAMESPACE = "ruina"

# 외부 건물 스케일 (PLAN 5절: 단면도 사람 기준 환산값의 3배)
EXTERIOR_SCALE = 3

# 서버 jar에서 못 읽었을 때 쓰는 기본값 (2026-10 기준 26.3)
FALLBACK_DATA_VERSION = 5023
FALLBACK_PACK_FORMAT = (121, 0)

# 모든 차원 공통 높이 (HANDOFF 3-1). 공간별로 바꾸려면 Space(min_y=..., height=...)
DIM_MIN_Y = -64
DIM_HEIGHT = 640


def night_sky(sky="#2a1850", fog="#2a1a4f", *, moon_phase="waxing_crescent", moon_angle=35.0,
              stars=0.5, light_factor=0.24, light_color="#8f7aff", sky_light_level=0.27, clouds="#00000000",
              extra=None) -> dict:
    """시계 없이 고정된 밤하늘 (환경 속성).

    바닐라 timeline/day.json 의 한밤중(18000틱) 값을 기준으로 함:
    sun_angle 180 = 해가 지평선 아래 정반대, moon_angle 0 = 달이 머리 위, star_brightness 0.5.
    """
    a = {
        "minecraft:visual/sky_color": sky,
        "minecraft:visual/fog_color": fog,
        "minecraft:visual/sun_angle": 180.0,
        "minecraft:visual/moon_angle": moon_angle,
        "minecraft:visual/star_angle": 180.0,
        "minecraft:visual/star_brightness": stars,
        "minecraft:visual/moon_phase": moon_phase,
        "minecraft:visual/sky_light_factor": light_factor,
        "minecraft:visual/sky_light_color": light_color,
        "minecraft:visual/sunrise_sunset_color": "#00000000",
        "minecraft:visual/cloud_color": clouds,
        "minecraft:gameplay/sky_light_level": sky_light_level,
    }
    a.update(extra or {})
    return a


# 모든 공간이 오버월드 시계를 같이 쓰고, 이 시각에 멈춰 둔다 (tools/datapack.time_commands).
# 쉐이더(BSL)는 하늘을 이 시각으로 그린다. 138000 = 6번째 날 자정 → 달 위상 '초승달(차는 중)'
CLOCK_TIME = 138000


@dataclass
class Space:
    id: str            # 차원 경로 (ruina:<id>)
    name: str          # 한글 이름
    librarian: str     # 지정사서
    size: int          # 구역 한 변 (블록, 512 배수)
    content_height: int  # 구역 높이 (PLAN 6절)
    attributes: dict = field(default_factory=night_sky)  # 환경 속성 (차원 전체)
    min_y: int = DIM_MIN_Y
    height: int = DIM_HEIGHT
    has_skylight: bool = True
    # 공중에 떠다니는 파티클 [(파티클, 확률)] — 바이옴 visual/ambient_particles
    particles: list = field(default_factory=list)
    # 추가 바이옴 {id: {"attributes": {...}, "particles": [...]}} — 같은 차원 안에서 구역마다 하늘·안개를 다르게
    # (빌더에서 Dimension.set_biome 으로 청크에 지정). 바이옴 visual 속성은 차원 값을 덮어씀
    biomes: dict = field(default_factory=dict)

    @property
    def dim(self) -> str:
        return f"{NAMESPACE}:{self.id}"


# 외관: 보라색 밤하늘 + 초승달 (PLAN 5·7절). 층별 값은 각 층 착수 때 원화 보고 정해서 PLAN 7절에 기록
EXTERIOR_SKY = night_sky("#3b2370", "#2c1b52", moon_phase="waxing_crescent", moon_angle=35.0)

# 로비 (reference/로비.png, reference/로비 전경 (전환 후).jpg, reference/로비_3D/)
# sky_light_level 은 차원 단위만 됨 (바이옴에 넣으면 서버 오류) → 차원은 밝게, 방은 천장이 가려서 어두움
LOBBY_ROOM_SKY = night_sky("#120a05", "#1c1008", stars=0.0, sky_light_level=1.0, extra={
    "minecraft:visual/fog_start_distance": 4.0, "minecraft:visual/fog_end_distance": 48.0})
LOBBY_HALL_SKY = {
    "minecraft:visual/sky_color": "#f4e2bd",
    "minecraft:visual/fog_color": "#e9cf9c",
    "minecraft:visual/fog_start_distance": 12.0,
    "minecraft:visual/fog_end_distance": 110.0,
    "minecraft:visual/sky_light_factor": 1.0,
    "minecraft:visual/sky_light_color": "#fff0d0",
    "minecraft:visual/star_brightness": 0.0,
}

# 역사의 층 (reference/역사의 층 전경.png, 지정사서 방.png)
HISTORY_SKY = night_sky("#f1d9a6", "#e2bf86", stars=0.0, sky_light_level=1.0, light_factor=1.0,
                        light_color="#fff0d0", extra={
                            "minecraft:visual/fog_start_distance": 40.0, "minecraft:visual/fog_end_distance": 340.0,
                            "minecraft:visual/sky_fog_end_distance": 360.0})
HISTORY_ROOM_SKY = {
    "minecraft:visual/sky_color": "#2a1a0c",
    "minecraft:visual/fog_color": "#3a2412",
    "minecraft:visual/fog_start_distance": 6.0,
    "minecraft:visual/fog_end_distance": 60.0,
}

# 기술과학의 층 (reference/기술과학의 층 전경.png, 지정사서 방.png)
TECH_SKY = night_sky("#6a4596", "#4b2f70", moon_phase="waxing_crescent", moon_angle=8.0, stars=0.3,
                     sky_light_level=0.35, light_color="#b48cff", clouds="#b78fd8e0", extra={
                         "minecraft:visual/cloud_height": 380.0,
                         "minecraft:visual/fog_start_distance": 80.0, "minecraft:visual/fog_end_distance": 420.0})
TECH_ROOM_SKY = {
    "minecraft:visual/sky_color": "#140a20",
    "minecraft:visual/fog_color": "#24133a",
    "minecraft:visual/fog_start_distance": 6.0,
    "minecraft:visual/fog_end_distance": 50.0,
}

# 문학의 층 (reference/문학의 층 전경.png, 지정사서 방.png)
LIT_SKY = night_sky("#7a8ea4", "#6d8096", stars=0.0, sky_light_level=0.45, light_color="#c8d4e0", extra={
    "minecraft:visual/fog_start_distance": 30.0, "minecraft:visual/fog_end_distance": 300.0,
    "minecraft:visual/block_light_tint": "#ff9a4a"})
LIT_ROOM_SKY = {
    "minecraft:visual/sky_color": "#3a2a1c",
    "minecraft:visual/fog_color": "#6a5640",
    "minecraft:visual/fog_start_distance": 8.0,
    "minecraft:visual/fog_end_distance": 70.0,
}

# 예술의 층 (reference/예술의 층 전경.png, 지정사서 방.png)
ART_SKY = night_sky("#b4cc52", "#a2b648", stars=0.0, sky_light_level=0.6, light_factor=0.8, light_color="#e8ff9a",
                    extra={"minecraft:visual/fog_start_distance": 25.0, "minecraft:visual/fog_end_distance": 300.0,
                           "minecraft:visual/water_fog_color": "#6f8f1e", "minecraft:visual/water_fog_end_distance": 24.0})
ART_ROOM_SKY = {
    "minecraft:visual/sky_color": "#1e2608",
    "minecraft:visual/fog_color": "#3a4a10",
    "minecraft:visual/fog_start_distance": 8.0,
    "minecraft:visual/fog_end_distance": 60.0,
}

# 자연과학의 층 (reference/자연과학의 층 전경.png, 전경 (색 바뀐 판).jpg, 지정사서 방.png)
NS_SKY = night_sky("#5a4520", "#a07a36", stars=0.0, sky_light_level=0.8, light_color="#ffe0a0", extra={
    "minecraft:visual/fog_start_distance": 60.0, "minecraft:visual/fog_end_distance": 260.0})
NS_TEAL_SKY = {
    "minecraft:visual/sky_color": "#1a262a",
    "minecraft:visual/fog_color": "#2e4044",
    "minecraft:visual/fog_start_distance": 60.0,
    "minecraft:visual/fog_end_distance": 260.0,
}
NS_ROOM_SKY = {
    "minecraft:visual/sky_color": "#6a4a1c",
    "minecraft:visual/fog_color": "#a07a3a",
    "minecraft:visual/fog_start_distance": 10.0,
    "minecraft:visual/fog_end_distance": 80.0,
}

# 언어의 층 (reference/언어의 층 전경.png, 지정사서 방.png)
LANG_SKY = night_sky("#2a0c06", "#5a1a0a", stars=0.0, sky_light_level=0.2, light_color="#ff7a3a", extra={
    "minecraft:visual/fog_start_distance": 40.0, "minecraft:visual/fog_end_distance": 300.0,
    "minecraft:visual/block_light_tint": "#ff8a3a"})
LANG_ROOM_SKY = {
    "minecraft:visual/sky_color": "#200804",
    "minecraft:visual/fog_color": "#4a1406",
    "minecraft:visual/fog_start_distance": 6.0,
    "minecraft:visual/fog_end_distance": 50.0,
}

# 사회과학의 층 (reference/사회과학의 층 전경.png, 지정사서 방.png)
SOC_SKY = night_sky("#0a2a5a", "#124a8a", stars=0.0, sky_light_level=0.35, light_color="#7ab8ff", extra={
    "minecraft:visual/fog_start_distance": 15.0, "minecraft:visual/fog_end_distance": 220.0,
    "minecraft:visual/block_light_tint": "#8ad0ff"})
SOC_ROOM_SKY = {
    "minecraft:visual/sky_color": "#06101e",
    "minecraft:visual/fog_color": "#0c2036",
    "minecraft:visual/fog_start_distance": 6.0,
    "minecraft:visual/fog_end_distance": 50.0,
}

# 철학의 층 (reference/철학의 층 전경.png, 지정사서 방.png)
PHIL_SKY = night_sky("#0c0a14", "#2a2018", moon_phase="waxing_crescent", moon_angle=10.0, stars=1.0, sky_light_level=0.2,
                     light_color="#a08060", extra={"minecraft:visual/fog_start_distance": 120.0,
                                                   "minecraft:visual/fog_end_distance": 520.0})
PHIL_ROOM_SKY = {
    "minecraft:visual/sky_color": "#120a04",
    "minecraft:visual/fog_color": "#3a2408",
    "minecraft:visual/fog_start_distance": 6.0,
    "minecraft:visual/fog_end_distance": 60.0,
}

# 종교의 층 (reference/종교의 층 전경.png, 지정사서 방.png) — 흑백
REL_SKY = night_sky("#c8c8c8", "#b4b4b4", stars=0.0, sky_light_level=0.8, light_factor=0.9, light_color="#e8e8e8",
                    extra={"minecraft:visual/fog_start_distance": 40.0, "minecraft:visual/fog_end_distance": 420.0,
                           "minecraft:visual/block_light_tint": "#e8e8e8"})
REL_ROOM_SKY = {
    "minecraft:visual/sky_color": "#d8d8d8",
    "minecraft:visual/fog_color": "#d0d0d0",
    "minecraft:visual/fog_start_distance": 10.0,
    "minecraft:visual/fog_end_distance": 70.0,
}

# 총류의 층 (reference/총류의 층 전경.png, 전경 (배경만).png, 지정사서 방.png)
GEN_SKY = night_sky("#a8a49a", "#9a968c", stars=0.0, sky_light_level=0.7, light_factor=0.9, light_color="#f0e8d8",
                    extra={"minecraft:visual/fog_start_distance": 40.0, "minecraft:visual/fog_end_distance": 380.0,
                           "minecraft:visual/water_fog_color": "#101828"})
GEN_ROOM_SKY = {
    "minecraft:visual/sky_color": "#6a6862",
    "minecraft:visual/fog_color": "#7a776e",
    "minecraft:visual/fog_start_distance": 10.0,
    "minecraft:visual/fog_end_distance": 140.0,
}

SPACES = [
    # 날리는 종이: 하얀 창백한참나무 잎 + 금빛 포플러 잎 파티클 (떨어지며 흔들림)
    Space("exterior", "외부", "", 1536, 400, EXTERIOR_SKY,
          particles=[("minecraft:pale_oak_leaves", 0.004), ("minecraft:yellow_poplar_leaves", 0.002)]),
    # 로비: 전환 전 = 어두운 나무 방 (어두운 갈색 안개, 먼지), 전환 후 = 밝은 홀 (바이옴 lobby_hall: 크림색 안개·하늘, 빛 입자)
    Space("lobby", "로비", "앤젤라", 512, 400, LOBBY_ROOM_SKY, particles=[("minecraft:white_ash", 0.003)],
          biomes={"lobby_hall": {"attributes": LOBBY_HALL_SKY, "particles": [("minecraft:firefly", 0.004),
                                                                             ("minecraft:end_rod", 0.0004)]}}),
    # 역사의 층: 금빛·크림색 안개 (원화 배경의 밝은 빛), 먼 배경은 안개 속으로. 말쿠트 방은 따뜻하고 어두운 실내
    Space("history", "역사의 층", "말쿠트", 1536, 400, HISTORY_SKY, particles=[("minecraft:firefly", 0.002),
                                                                          ("minecraft:white_ash", 0.002)],
          biomes={"history_room": {"attributes": HISTORY_ROOM_SKY, "particles": [("minecraft:white_ash", 0.002)]}}),
    # 기술과학의 층: 보라 밤하늘 + 보라 구름(바닐라 구름 색·높이) + 초승달, 보라 안개. 예소드 방은 어두운 보라
    Space("technology", "기술과학의 층", "예소드", 2048, 512, TECH_SKY, particles=[("minecraft:white_ash", 0.001)],
          biomes={"technology_room": {"attributes": TECH_ROOM_SKY, "particles": []}}),
    # 문학의 층: 푸른 회색 안개 속 주홍빛 전구 (원화). 호드 방은 따뜻한 갈색
    Space("literature", "문학의 층", "호드", 1536, 400, LIT_SKY, particles=[("minecraft:white_ash", 0.002),
                                                                     ("minecraft:firefly", 0.001)],
          biomes={"literature_room": {"attributes": LIT_ROOM_SKY, "particles": [("minecraft:white_ash", 0.002)]}}),
    # 예술의 층: 연두·노랑 빛 안개(나무 사이로 새는 빛), 반딧불이, 연두빛 물. 네짜흐 방은 어두운 숲빛
    Space("art", "예술의 층", "네짜흐", 1536, 400, ART_SKY, particles=[("minecraft:firefly", 0.006)],
          biomes={"art_room": {"attributes": ART_ROOM_SKY, "particles": [("minecraft:firefly", 0.004)]}}),
    # 자연과학의 층: 금빛 실내 (돔). 색 바뀐 판은 같은 차원 다른 자리 (바이옴 natural_science_teal)
    Space("natural_science", "자연과학의 층", "티페리트", 1024, 400, NS_SKY, particles=[("minecraft:white_ash", 0.001)],
          biomes={"natural_science_room": {"attributes": NS_ROOM_SKY, "particles": [("minecraft:white_ash", 0.002)]},
                  "natural_science_teal": {"attributes": NS_TEAL_SKY, "particles": [("minecraft:white_ash", 0.001)]}}),
    # 언어의 층: 검붉은 용광로 안개, 블록 빛 주황. 게부라 방은 붉은 빛 어두운 서재
    Space("language", "언어의 층", "게부라", 1536, 400, LANG_SKY, particles=[("minecraft:ash", 0.006), ("minecraft:lava", 0.0004)],
          biomes={"language_room": {"attributes": LANG_ROOM_SKY, "particles": [("minecraft:ash", 0.002)]}}),
    # 사회과학의 층: 깊은 바닷속 (짙은 푸른 안개, 떠다니는 입자). 헤세드 방은 푸른 어둠
    Space("social_science", "사회과학의 층", "헤세드", 2048, 400, SOC_SKY,
          particles=[("minecraft:white_ash", 0.006), ("minecraft:underwater", 0.01)],
          biomes={"social_science_room": {"attributes": SOC_ROOM_SKY, "particles": [("minecraft:white_ash", 0.002)]}}),
    # 철학의 층: 맑은 밤하늘 (별 밝게, 초승달), 아래 도시 안개. 비나 방은 금빛 어둠
    Space("philosophy", "철학의 층", "비나", 2048, 400, PHIL_SKY, particles=[("minecraft:white_ash", 0.001)],
          biomes={"philosophy_room": {"attributes": PHIL_ROOM_SKY, "particles": []}}),
    # 종교의 층: 흑백 잿빛 안개 (원화가 흑백). 호크마 방은 흰빛 안개
    Space("religion", "종교의 층", "호크마", 3072, 512, REL_SKY, particles=[("minecraft:white_ash", 0.004)],
          biomes={"religion_room": {"attributes": REL_ROOM_SKY, "particles": [("minecraft:white_ash", 0.003)]}}),
    # 총류의 층: 옅은 잿빛 안개 (책장 빌딩 사이 빛), 떨어지는 종이. 롤랑 방도 잿빛
    Space("general", "총류의 층", "롤랑", 2048, 512, GEN_SKY, particles=[("minecraft:white_ash", 0.006)],
          biomes={"general_room": {"attributes": GEN_ROOM_SKY, "particles": [("minecraft:white_ash", 0.004)]}}),
]

SPACE_BY_ID = {s.id: s for s in SPACES}

# 관상용 게임룰 (HANDOFF 2절). 빌드 때 한 번 적용하고, /function ruina:setup 으로 다시 적용 가능
GAMERULES = {
    "advance_time": "false",
    "advance_weather": "false",
    "spawn_mobs": "false",
    "spawn_patrols": "false",
    "spawn_wandering_traders": "false",
    "random_tick_speed": "0",
    "fire_spread_radius_around_player": "0",
    "mob_griefing": "false",
    "respawn_radius": "0",
    "spawn_monsters": "false",
    "spawn_phantoms": "false",
}
