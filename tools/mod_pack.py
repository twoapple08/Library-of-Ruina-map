"""모드 jar 에 들어갈 생성 리소스 (CI 월드 빌드 끝에서): mod/build/generated/ruina/

- data/        모드용 데이터팩 (차원·바이옴·함수, 모드 전용 함수 포함, 월드 전용 함수 제외) — 모드 데이터는 항상 켜짐
- assets/ruina/sounds*  리소스팩 원본(resourcepack/)의 소리
- ruina/items.json      아이템 목록·도착 자리 (모드 Java 가 읽음)
- ruina/world.zip       건축물: 서버가 검증·조명 계산까지 한 차원별 region·entities (어느 월드든 처음 열 때 복사)
- ruina/world.id        빌드 번호 (모드 업데이트로 바뀌면 월드의 도서관 차원을 새 것으로 교체 — 사용자 결정)
"""
from __future__ import annotations

import json
import os
import shutil
import zipfile

import config
from tools import datapack

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "mod", "build", "generated", "ruina")


def items_json(links: datapack.Links) -> dict:
    items = []
    for iid, name, kind, floor in config.MOD_ITEMS:
        it = {"id": iid, "name": name, "kind": kind}
        if kind == "sephirah":
            anchor = f"{floor}_entrance"
            if anchor not in links.anchors:
                raise KeyError(f"세피라 {iid}: 도착 자리 {anchor} 없음")
            it["anchor"] = anchor
        items.append(it)
    if not links.spawn:
        raise KeyError("초대장 도착 자리(links.spawn) 없음")
    return {"spawn": links.spawn, "namespace": config.NAMESPACE, "items": items}


def pack(links: datapack.Links, wdir: str | None, build_id: str, out: str = OUT) -> dict:
    """생성 리소스 쓰기. wdir: 서버가 저장을 마친 월드 폴더 (None 이면 건축물 없이)."""
    shutil.rmtree(out, ignore_errors=True)
    tmp = out + "_dp"
    datapack.write(tmp, links, mod=True)
    shutil.copytree(os.path.join(tmp, "data"), os.path.join(out, "data"))
    shutil.rmtree(tmp)
    snd = os.path.join(ROOT, "resourcepack", "assets", "ruina")
    shutil.copytree(os.path.join(snd, "sounds"), os.path.join(out, "assets", "ruina", "sounds"))
    shutil.copy(os.path.join(snd, "sounds.json"), os.path.join(out, "assets", "ruina", "sounds.json"))
    meta = os.path.join(out, "ruina")
    os.makedirs(meta, exist_ok=True)
    with open(os.path.join(meta, "items.json"), "w", encoding="utf-8") as f:
        json.dump(items_json(links), f, indent=2, ensure_ascii=False)
    with open(os.path.join(meta, "world.id"), "w") as f:
        f.write(build_id + "\n")
    stats = {"files": 0, "bytes": 0}
    if wdir:
        base = os.path.join(wdir, "dimensions", config.NAMESPACE)
        # 이미 압축된 청크(.mca)라 다시 압축하지 않음 (STORED) → 풀 때 빠름
        with zipfile.ZipFile(os.path.join(meta, "world.zip"), "w", zipfile.ZIP_STORED) as z:
            for sid in sorted(os.listdir(base)):
                for sub in ("region", "entities"):
                    d = os.path.join(base, sid, sub)
                    for fn in sorted(os.listdir(d)) if os.path.isdir(d) else []:
                        if fn.endswith((".mca", ".mcc")):
                            z.write(os.path.join(d, fn), f"{sid}/{sub}/{fn}")
                            stats["files"] += 1
        stats["bytes"] = os.path.getsize(os.path.join(meta, "world.zip"))
    return stats
