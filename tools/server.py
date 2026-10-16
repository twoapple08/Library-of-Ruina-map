"""마인크래프트 전용 서버를 띄워 콘솔 명령을 보내고 로그를 읽는 도구 (GitHub Actions용).

서버 jar는 재배포 금지라 레포·아티팩트에 넣지 않는다. 실행할 때마다 Mojang에서 받는다.
"""
from __future__ import annotations

import hashlib
import json
import os
import queue
import re
import subprocess
import threading
import time
import urllib.request

MANIFEST = "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"


def _get_json(url):
    with urllib.request.urlopen(url, timeout=60) as r:
        return json.load(r)


def fetch_server(dest_dir: str, version: str | None = None) -> dict:
    """최신 정식(또는 지정) 버전 서버 jar 다운로드. 반환: {id, java, jar}"""
    os.makedirs(dest_dir, exist_ok=True)
    man = _get_json(MANIFEST)
    vid = version or man["latest"]["release"]
    entry = next(v for v in man["versions"] if v["id"] == vid)
    meta = _get_json(entry["url"])
    srv = meta["downloads"]["server"]
    jar = os.path.join(dest_dir, "server.jar")
    if not (os.path.exists(jar) and _sha1(jar) == srv["sha1"]):
        urllib.request.urlretrieve(srv["url"], jar)
        if _sha1(jar) != srv["sha1"]:
            raise RuntimeError("server.jar sha1 불일치")
    info = {"id": vid, "java": meta.get("javaVersion", {}).get("majorVersion"), "jar": jar,
            "release_time": meta.get("releaseTime")}
    with open(os.path.join(dest_dir, "info.json"), "w") as f:
        json.dump(info, f, indent=2)
    return info


def _sha1(path):
    h = hashlib.sha1()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


SERVER_PROPERTIES = {
    "level-name": "world",
    "level-type": "minecraft\\:flat",
    "generator-settings": '{"layers":[],"biome":"minecraft\\:the_void","features":false,"lakes":false,"structure_overrides":[]}',
    "generate-structures": "false",
    "online-mode": "false",
    "max-tick-time": "-1",          # 감시견 끔: 큰 월드 save-all 이 60초를 넘으면 서버가 스스로 죽음 (느린 작업 환경에서 확인)
    "spawn-protection": "0",
    "max-players": "1",
    "view-distance": "4",
    "simulation-distance": "4",
    "gamemode": "creative",
    "difficulty": "peaceful",
    "enable-command-block": "true",
    "sync-chunk-writes": "true",
    "region-file-compression": "deflate",
    "enable-rcon": "false",
    "motd": "ruina-build",
    "pause-when-empty-seconds": "-1",   # 플레이어가 없어도 멈추지 않음 (멈추면 forceload 청크가 안 불러와짐)
}


def prepare_dir(server_dir: str, jar: str):
    os.makedirs(server_dir, exist_ok=True)
    with open(os.path.join(server_dir, "eula.txt"), "w") as f:
        f.write("eula=true\n")
    with open(os.path.join(server_dir, "server.properties"), "w") as f:
        for k, v in SERVER_PROPERTIES.items():
            f.write(f"{k}={v}\n")
    link = os.path.join(server_dir, "server.jar")
    if not os.path.exists(link):
        os.symlink(os.path.abspath(jar), link)


LOG_LINE = re.compile(r"^\[[^\]]*\] \[([^\]]*)/(\w+)\]: ?(.*)$")


class Server:
    def __init__(self, server_dir: str, xmx: str = "4G", log_path: str | None = None):
        self.dir = server_dir
        self.xmx = xmx
        self.lines: list[str] = []
        self.q: queue.Queue = queue.Queue()
        self.proc = None
        self.log = open(log_path, "a", encoding="utf-8") if log_path else None
        self._mark = 0

    # -------------------------------------------------- 실행/종료
    def start(self, timeout: float = 600) -> float:
        t0 = time.time()
        self.proc = subprocess.Popen(
            ["java", f"-Xmx{self.xmx}", "-jar", "server.jar", "nogui"],
            cwd=self.dir, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, encoding="utf-8", errors="replace", bufsize=1)
        threading.Thread(target=self._pump, daemon=True).start()
        self.wait_for(r'Done \(|Failed to start|Exception in server tick loop|Stopping server', timeout)
        if not any("Done (" in l for l in self.lines):
            raise RuntimeError("서버 시작 실패 (로그 확인)")
        return time.time() - t0

    def _pump(self):
        for line in self.proc.stdout:
            line = line.rstrip("\n")
            self.lines.append(line)
            self.q.put(line)
            print("  | " + line, flush=True)
            if self.log:
                self.log.write(line + "\n")
        self.q.put(None)

    def stop(self, timeout: float = 300):
        if self.proc and self.proc.poll() is None:
            self.send("stop")
            try:
                self.proc.wait(timeout)
            except subprocess.TimeoutExpired:
                self.proc.kill()
        if self.log:
            self.log.flush()

    # -------------------------------------------------- 명령
    def send(self, command: str):
        print(f"  > {command}", flush=True)
        if self.log:
            self.log.write(f"> {command}\n")
        self.proc.stdin.write(command + "\n")
        self.proc.stdin.flush()

    def wait_for(self, pattern: str, timeout: float = 60) -> str:
        rx = re.compile(pattern)
        end = time.time() + timeout
        while True:
            left = end - time.time()
            if left <= 0:
                raise TimeoutError(f"로그에서 '{pattern}'을(를) 못 찾음")
            try:
                line = self.q.get(timeout=left)
            except queue.Empty:
                continue
            if line is None:
                raise RuntimeError(f"서버가 종료됨 ('{pattern}' 기다리는 중)")
            if rx.search(line):
                return line

    def run(self, command: str, timeout: float = 60) -> list[str]:
        """명령 실행 후 그 명령이 출력한 메시지 줄들 (시간·스레드 접두어 제거)."""
        return self.run_many([command], timeout)[0]

    def run_many(self, commands: list[str], timeout: float = 60) -> list[list[str]]:
        """명령마다 고유 완료 마커를 유지하며 한 묶음을 보낸다. 결과 누락/순서 오류는 실패."""
        if not commands:
            return []
        start = len(self.lines)
        marks = []
        for command in commands:
            self._mark += 1
            mark = f"__ruina_mark_{self._mark}__"
            marks.append(mark)
            self.send(command)
            self.send(f"say {mark}")
        self.wait_for(re.escape(marks[-1]), timeout)
        out = [[] for _ in commands]
        current = 0
        for l in self.lines[start:]:
            marker = re.search(r"__ruina_mark_\d+__", l)
            if marker:
                if current >= len(marks) or marker.group() != marks[current]:
                    raise RuntimeError("서버 명령 완료 마커 순서 불일치")
                current += 1
                if current == len(marks):
                    break
                continue
            m = LOG_LINE.match(l)
            out[current].append(m.group(3) if m else l)
        if current != len(marks):
            raise RuntimeError("서버 명령 완료 마커 누락")
        return out

    def test(self, command: str) -> bool:
        """execute if ... 형태 명령의 결과 (Test passed/failed)."""
        return self._test_result(self.run(command))

    @staticmethod
    def _test_result(out: list[str]) -> bool:
        txt = " ".join(out)
        if "Test passed" in txt:
            return True
        if "Test failed" in txt:
            return False
        print(f"  ! 예상 못 한 결과 (실패로 처리): {out}", flush=True)
        return False

    def test_many(self, commands: list[str], batch_size: int = 128) -> list[bool]:
        """검사 개수는 유지하며 콘솔 왕복/틱 대기만 묶는다. 각 검사 결과는 별도로 판정."""
        results = []
        for i in range(0, len(commands), batch_size):
            results.extend(self._test_result(out) for out in self.run_many(commands[i:i + batch_size], timeout=180))
        return results

    def wait_loaded(self, dim: str, x: int, y: int, z: int, timeout: float = 60) -> bool:
        end = time.time() + timeout
        while time.time() < end:
            if self.test(f"execute in {dim} if loaded {x} {y} {z}"):
                return True
            time.sleep(0.5)
        return False

    def problems(self) -> list[str]:
        """WARN/ERROR 줄과 데이터팩·청크 관련 의심 줄."""
        bad = []
        keys = ("Couldn't", "Failed", "Exception", "Unknown", "error", "Error", "Invalid", "invalid",
                "Recoverable", "corrupt", "Missing")
        for l in self.lines:
            m = LOG_LINE.match(l)
            level = m.group(2) if m else ""
            if level in ("WARN", "ERROR", "FATAL") or (not m and l.strip()) or any(k in l for k in keys):
                bad.append(l)
        return bad
