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


@dataclass
class Sky:
    """차원(층)별 하늘. 키는 환경 속성 이름에서 'minecraft:visual/'를 뺀 것."""
    visual: dict = field(default_factory=dict)


@dataclass
class Space:
    id: str            # 차원 경로 (ruina:<id>)
    name: str          # 한글 이름
    librarian: str     # 지정사서
    size: int          # 구역 한 변 (블록, 512 배수)
    content_height: int  # 구역 높이 (PLAN 6절)
    sky: Sky = field(default_factory=Sky)
    min_y: int = DIM_MIN_Y
    height: int = DIM_HEIGHT
    has_skylight: bool = True

    @property
    def dim(self) -> str:
        return f"{NAMESPACE}:{self.id}"


NIGHT_PURPLE = Sky(visual={
    "sky_color": "#2a1850",
    "fog_color": "#3a2468",
})

SPACES = [
    Space("exterior", "외부", "", 1536, 400, NIGHT_PURPLE),
    Space("lobby", "로비", "앤젤라", 512, 400),
    Space("history", "역사의 층", "말쿠트", 1536, 400),
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
}
