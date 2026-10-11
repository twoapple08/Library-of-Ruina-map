"""리전 파일(.mca) 읽기/쓰기.

구조: [위치 테이블 4KiB][타임스탬프 4KiB][청크 데이터 ... 4KiB 섹터 단위]
청크 데이터: [길이 4바이트(압축타입 1바이트 포함)][압축타입: 1=gzip 2=zlib 3=무압축 4=lz4][데이터]
섹터 수가 255를 넘으면 c.<x>.<z>.mcc 외부 파일에 데이터를 쓰고 압축타입에 128을 더한다.
"""
from __future__ import annotations

import gzip
import os
import struct
import zlib

from . import nbt

SECTOR = 4096
COMP_GZIP, COMP_ZLIB, COMP_NONE = 1, 2, 3
EXTERNAL = 128


def region_name(rx: int, rz: int) -> str:
    return f"r.{rx}.{rz}.mca"


def write_region(path: str, chunks: dict, timestamp: int = 0, level: int = 6):
    """chunks: {(cx, cz) 절대 청크좌표: 루트 Compound 또는 압축 안 한 NBT 바이트}.

    모든 청크는 같은 리전(cx>>5, cz>>5)에 속해야 한다.
    """
    folder = os.path.dirname(path)
    locations = bytearray(SECTOR)
    stamps = bytearray(SECTOR)
    body = bytearray()
    next_sector = 2
    rxz = None
    for (cx, cz), data in sorted(chunks.items(), key=lambda kv: (kv[0][1], kv[0][0])):
        key = (cx >> 5, cz >> 5)
        if rxz is None:
            rxz = key
        elif key != rxz:
            raise ValueError(f"청크 {cx},{cz}가 다른 리전에 속함 ({key} != {rxz})")
        if isinstance(data, dict):
            data = nbt.dumps(data)
        comp = zlib.compress(data, level)
        payload = struct.pack(">IB", len(comp) + 1, COMP_ZLIB) + comp
        sectors = -(-len(payload) // SECTOR)
        if sectors > 255:
            with open(os.path.join(folder, f"c.{cx}.{cz}.mcc"), "wb") as f:
                f.write(comp)
            payload = struct.pack(">IB", 1, COMP_ZLIB | EXTERNAL)
            sectors = 1
        payload += b"\x00" * (sectors * SECTOR - len(payload))
        idx = (cx & 31) + (cz & 31) * 32
        struct.pack_into(">I", locations, idx * 4, (next_sector << 8) | sectors)
        struct.pack_into(">i", stamps, idx * 4, timestamp)
        body += payload
        next_sector += sectors
    with open(path, "wb") as f:
        f.write(locations)
        f.write(stamps)
        f.write(body)


def _decompress(kind: int, data: bytes) -> bytes:
    if kind == COMP_ZLIB:
        return zlib.decompress(data)
    if kind == COMP_GZIP:
        return gzip.decompress(data)
    if kind == COMP_NONE:
        return data
    raise ValueError(f"지원하지 않는 압축 타입 {kind} (4=lz4면 서버 설정 region-file-compression 확인)")


def read_region_raw(path: str) -> dict:
    """{(cx, cz): 압축 푼 NBT 바이트}. 좌표는 파일명 기준 절대 청크좌표."""
    base = os.path.basename(path).split(".")
    rx, rz = int(base[1]), int(base[2])
    folder = os.path.dirname(path)
    with open(path, "rb") as f:
        raw = f.read()
    out = {}
    if len(raw) < 2 * SECTOR:
        return out
    for idx in range(1024):
        loc = struct.unpack_from(">I", raw, idx * 4)[0]
        if loc == 0:
            continue
        off, count = loc >> 8, loc & 0xFF
        start = off * SECTOR
        length, kind = struct.unpack_from(">IB", raw, start)
        cx, cz = rx * 32 + (idx & 31), rz * 32 + (idx >> 5)
        if kind & EXTERNAL:
            with open(os.path.join(folder, f"c.{cx}.{cz}.mcc"), "rb") as f:
                data = f.read()
            kind &= ~EXTERNAL
        else:
            data = raw[start + 5:start + 4 + length]
        out[(cx, cz)] = _decompress(kind, data)
    return out


def read_region(path: str) -> dict:
    """{(cx, cz): 루트 Compound}."""
    return {k: nbt.loads(v) for k, v in read_region_raw(path).items()}
