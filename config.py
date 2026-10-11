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
    Space("technology", "기술과학의 층", "예소드", 2048, 512),
    Space("literature", "문학의 층", "호드", 1536, 400),
    Space("art", "예술의 층", "네짜흐", 1536, 400),
    Space("natural_science", "자연과학의 층", "티페리트", 1024, 400),
    Space("language", "언어의 층", "게부라", 1536, 400),
    Space("social_science", "사회과학의 층", "헤세드", 2048, 400),
    Space("philosophy", "철학의 층", "비나", 2048, 400),
    Space("religion", "종교의 층", "호크마", 3072, 512),
    Space("general", "총류의 층", "롤랑", 2048, 512),
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
