GitHub twoapple08/Library-of-Ruina-map 작업을 이어서 진행해 줘. 한국어로 짧게 대화해.
main과 ccr-365e34b9-yzsq81의 최신 커밋을 확인하고, HANDOFF.md → docs/mod/형체.md → docs/mod/기초구성.md 순서로 읽어.
현재는 외부 입체 부품 보강 중이며 외부 전체가 끝난 상태가 아니야.
외부의 남은 실루엣·근접 마감·종이 물결을 다듬고, 새 exterior_surroundings.py의 도시/테라스/고리/구름 전체 배치·시야·충돌·면 수를 검증한 뒤 로비부터 순서대로 진행해.
도착 시점 원화 투영만 맞는 평판/상자 더미를 완성으로 처리하지 말고, 옆·뒤·위·근접 형상도 확인해.
새 form_preview는 cc 기반 면 채움 렌더러와 mover 스냅샷을 사용해. 오프라인 비교를 게임 스크린샷이라고 부르지 마.
계획 확인이나 도구·스킬·외부 도구 사용 허가를 다시 묻지 말고 진행해. BSL은 건드리지 말고, 아이템 이미지/사운드는 임시 유지.
테스터 테스트는 전부 구축 후 한 번에. 공간 완료 시 실제 게임 스크린샷↔원화 비교, main과 지정 브랜치 푸시, HANDOFF 갱신.
현재 컨테이너에는 /opt/jdk25(Java25)와 Gradle9.7.1을 준비했어. local_test.sh에 프록시/시스템 CA 처리를 넣었고, Loom의 SocketException은 ci_out/local_compile.log와 HANDOFF를 확인해. 새 컨테이너에서 이전 캐시가 있다고 가정하지 마.
