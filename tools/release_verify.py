"""JAR의 소스/건축 지문을 검사하고 배포 파일의 SHA-256 증명서를 만든다.

python -m tools.release_verify prepare
python -m tools.release_verify verify path/to/Ruina.jar [--manifest out.json]
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import zipfile

from tools.world_cache import fingerprint

ROOT = Path(__file__).resolve().parents[1]
GEN = ROOT / "mod/build/generated/ruina"


def source_commit():
    return os.environ.get("GITHUB_SHA") or subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def prepare():
    expected = fingerprint()
    actual = (GEN / "ruina/source.sha").read_text().strip()
    if actual != expected:
        raise ValueError(f"건축 데이터 지문 불일치: {actual} != {expected}")
    props = dict(line.split("=", 1) for line in (ROOT / "mod/gradle.properties").read_text().splitlines()
                 if "=" in line and not line.startswith("#"))
    meta = {"source_commit": source_commit(), "built_at_utc": datetime.now(timezone.utc).isoformat(),
            "world_id": (GEN / "ruina/world.id").read_text().strip(), "world_fingerprint": expected,
            "minecraft": props["minecraft_version"], "fabric_loader": props["loader_version"],
            "fabric_api": props["fabric_api_version"], "mod_version": props["mod_version"],
            "run_id": os.environ.get("GITHUB_RUN_ID")}
    (GEN / "ruina/build.json").write_text(json.dumps(meta, indent=2) + "\n")
    return meta


def verify(path, expected_commit=None, expected_fingerprint=None):
    with zipfile.ZipFile(path) as jar:
        if jar.testzip() is not None:
            raise ValueError("JAR CRC 검사 실패")
        meta = json.loads(jar.read("ruina/build.json"))
        if expected_commit and meta["source_commit"] != expected_commit:
            raise ValueError("JAR 소스 커밋 불일치")
        actual = jar.read("ruina/source.sha").decode().strip()
        if actual != meta["world_fingerprint"] or (expected_fingerprint and actual != expected_fingerprint):
            raise ValueError("JAR 건축 지문 불일치")
        if jar.read("ruina/world.id").decode().strip() != meta["world_id"]:
            raise ValueError("JAR 건축 버전 불일치")
        if jar.getinfo("ruina/world.zip").file_size == 0:
            raise ValueError("빈 월드 데이터")
        mod = json.loads(jar.read("fabric.mod.json"))
        if mod["id"] != "ruina" or mod["version"] != meta["mod_version"]:
            raise ValueError("모드 ID/버전 불일치")
        if mod["depends"]["minecraft"] != "~" + meta["minecraft"]:
            raise ValueError("마인크래프트 버전 불일치")
    with open(path, "rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    return {**meta, "file": Path(path).name, "size": Path(path).stat().st_size, "sha256": digest}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("command", choices=["prepare", "verify"])
    p.add_argument("jar", nargs="?")
    p.add_argument("--manifest")
    a = p.parse_args()
    meta = prepare() if a.command == "prepare" else verify(a.jar, source_commit(), fingerprint())
    data = json.dumps(meta, indent=2) + "\n"
    if a.manifest:
        Path(a.manifest).write_text(data)
    print(data)


if __name__ == "__main__":
    main()
