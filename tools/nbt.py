"""최소 NBT 읽기/쓰기 (외부 의존성: numpy).

타입 매핑
- Byte/Short/Int/Long/Float/Double: 아래 래퍼 클래스 (int/float 하위 클래스)
- 그냥 int → Int, 그냥 float → Double, bool → Byte 로 쓴다 (편의용)
- str → String, dict → Compound, list → List
- numpy 배열: int8 → ByteArray, int32 → IntArray, int64 → LongArray
- bytes/bytearray → ByteArray

읽으면 래퍼 타입과 numpy 배열로 돌려주므로 읽고 다시 써도 타입이 유지된다.
"""
from __future__ import annotations

import functools
import gzip
import io
import struct
import zlib

import numpy as np

TAG_END, TAG_BYTE, TAG_SHORT, TAG_INT, TAG_LONG = 0, 1, 2, 3, 4
TAG_FLOAT, TAG_DOUBLE, TAG_BYTE_ARRAY, TAG_STRING = 5, 6, 7, 8
TAG_LIST, TAG_COMPOUND, TAG_INT_ARRAY, TAG_LONG_ARRAY = 9, 10, 11, 12


class Byte(int):
    tag = TAG_BYTE


class Short(int):
    tag = TAG_SHORT


class Int(int):
    tag = TAG_INT


class Long(int):
    tag = TAG_LONG


class Float(float):
    tag = TAG_FLOAT


class Double(float):
    tag = TAG_DOUBLE


class RawCompound(bytes):
    """미리 직렬화한 Compound 내용(이름 없음, 끝 TAG_END 포함). 같은 내용을 많이 쓸 때 속도용."""
    tag = 10


class List(list):
    """원소 타입을 기억하는 리스트 (빈 리스트의 타입 보존용)."""

    def __init__(self, items=(), elem_tag: int | None = None):
        super().__init__(items)
        self.elem_tag = elem_tag


# ---------------------------------------------------------------- 문자열 (Modified UTF-8)

def _mutf8_encode(s: str) -> bytes:
    if s.isascii() and "\x00" not in s:
        return s.encode("ascii")
    if all(0 < ord(c) < 0x10000 for c in s):
        return s.encode("utf-8")
    # NUL·BMP 밖 문자가 있으면 UTF-16 코드 유닛 단위로 하나씩 인코딩
    out = bytearray()
    units = s.encode("utf-16-be", "surrogatepass")
    for i in range(0, len(units), 2):
        u = (units[i] << 8) | units[i + 1]
        if u == 0:
            out += b"\xc0\x80"
        elif u < 0x80:
            out.append(u)
        elif u < 0x800:
            out += bytes((0xC0 | (u >> 6), 0x80 | (u & 0x3F)))
        else:
            out += bytes((0xE0 | (u >> 12), 0x80 | ((u >> 6) & 0x3F), 0x80 | (u & 0x3F)))
    return bytes(out)


def _mutf8_decode(b: bytes) -> str:
    try:
        return b.decode("utf-8")
    except UnicodeDecodeError:
        b = b.replace(b"\xc0\x80", b"\x00")
        s = b.decode("utf-8", "surrogatepass")
        return s.encode("utf-16-be", "surrogatepass").decode("utf-16-be")


# ---------------------------------------------------------------- 쓰기

def tag_of(v) -> int:
    t = getattr(v, "tag", None)
    if t is not None and not isinstance(v, np.ndarray):
        return t
    if isinstance(v, bool):
        return TAG_BYTE
    if isinstance(v, int):
        return TAG_INT
    if isinstance(v, float):
        return TAG_DOUBLE
    if isinstance(v, str):
        return TAG_STRING
    if isinstance(v, dict):
        return TAG_COMPOUND
    if isinstance(v, list):
        return TAG_LIST
    if isinstance(v, (bytes, bytearray)):
        return TAG_BYTE_ARRAY
    if isinstance(v, np.ndarray):
        k = v.dtype
        if k == np.int8 or k == np.uint8:
            return TAG_BYTE_ARRAY
        if k == np.int32:
            return TAG_INT_ARRAY
        if k == np.int64 or k == np.uint64:
            return TAG_LONG_ARRAY
        raise TypeError(f"NBT로 쓸 수 없는 배열 dtype: {k}")
    raise TypeError(f"NBT로 쓸 수 없는 값: {type(v).__name__}")


_S_B, _S_H, _S_I, _S_Q = struct.Struct(">b"), struct.Struct(">h"), struct.Struct(">i"), struct.Struct(">q")
_S_F, _S_D, _S_US = struct.Struct(">f"), struct.Struct(">d"), struct.Struct(">H")


@functools.lru_cache(maxsize=1 << 16)
def _str_bytes(s: str) -> bytes:
    b = _mutf8_encode(s)
    return _S_US.pack(len(b)) + b


def _w_str(out: list, s: str):
    out.append(_str_bytes(s))


def _w_payload(out: list, t: int, v):
    if t == TAG_BYTE:
        out.append(_S_B.pack(int(v)))
    elif t == TAG_SHORT:
        out.append(_S_H.pack(v))
    elif t == TAG_INT:
        out.append(_S_I.pack(v))
    elif t == TAG_LONG:
        out.append(_S_Q.pack(v))
    elif t == TAG_FLOAT:
        out.append(_S_F.pack(v))
    elif t == TAG_DOUBLE:
        out.append(_S_D.pack(v))
    elif t == TAG_STRING:
        _w_str(out, v)
    elif t == TAG_COMPOUND:
        if isinstance(v, RawCompound):
            out.append(v)
            return
        for k, sub in v.items():
            st = tag_of(sub)
            out.append(bytes((st,)))
            _w_str(out, k)
            _w_payload(out, st, sub)
        out.append(b"\x00")
    elif t == TAG_LIST:
        et = getattr(v, "elem_tag", None)
        if len(v) == 0:
            et = et or TAG_END
        else:
            # 서버는 빈 리스트를 TAG_END로 저장할 수 있다. 읽은 뒤 블록 엔티티나
            # section을 추가하면 END는 원소 타입이 될 수 없으므로 실제 타입을 추론한다.
            et = tag_of(v[0]) if et in (None, TAG_END) else et
        out.append(bytes((et,)))
        out.append(_S_I.pack(len(v)))
        for item in v:
            _w_payload(out, et, item)
    elif t == TAG_BYTE_ARRAY:
        b = bytes(v) if not isinstance(v, np.ndarray) else v.astype(np.int8).tobytes()
        out.append(_S_I.pack(len(b)))
        out.append(b)
    elif t == TAG_INT_ARRAY:
        a = np.asarray(v, dtype=">i4")
        out.append(_S_I.pack(a.size))
        out.append(a.tobytes())
    elif t == TAG_LONG_ARRAY:
        a = np.asarray(v)
        if a.dtype == np.uint64:
            a = a.view(np.int64)
        a = a.astype(">i8")
        out.append(_S_I.pack(a.size))
        out.append(a.tobytes())
    else:
        raise ValueError(f"알 수 없는 태그 {t}")


def raw_compound(d: dict) -> RawCompound:
    out: list = []
    _w_payload(out, TAG_COMPOUND, d)
    return RawCompound(b"".join(out))


def dumps(root: dict, name: str = "") -> bytes:
    """루트 Compound를 압축하지 않은 NBT 바이트로."""
    out: list = [bytes((TAG_COMPOUND,))]
    _w_str(out, name)
    _w_payload(out, TAG_COMPOUND, root)
    return b"".join(out)


# ---------------------------------------------------------------- 읽기

class _Reader:
    __slots__ = ("b", "p")

    def __init__(self, b: bytes):
        self.b = b
        self.p = 0

    def take(self, n: int) -> bytes:
        p = self.p
        self.p = p + n
        if self.p > len(self.b):
            raise ValueError("NBT 데이터가 중간에 끝남")
        return self.b[p:p + n]

    def unpack(self, s: struct.Struct):
        v = s.unpack_from(self.b, self.p)[0]
        self.p += s.size
        return v

    def str(self) -> str:
        n = self.unpack(_S_US)
        return _mutf8_decode(self.take(n))

    def payload(self, t: int):
        if t == TAG_BYTE:
            return Byte(self.unpack(_S_B))
        if t == TAG_SHORT:
            return Short(self.unpack(_S_H))
        if t == TAG_INT:
            return Int(self.unpack(_S_I))
        if t == TAG_LONG:
            return Long(self.unpack(_S_Q))
        if t == TAG_FLOAT:
            return Float(self.unpack(_S_F))
        if t == TAG_DOUBLE:
            return Double(self.unpack(_S_D))
        if t == TAG_STRING:
            return self.str()
        if t == TAG_COMPOUND:
            d = {}
            while True:
                st = self.take(1)[0]
                if st == TAG_END:
                    return d
                k = self.str()
                d[k] = self.payload(st)
        if t == TAG_LIST:
            et = self.take(1)[0]
            n = self.unpack(_S_I)
            return List((self.payload(et) for _ in range(n)), elem_tag=et)
        if t == TAG_BYTE_ARRAY:
            n = self.unpack(_S_I)
            return np.frombuffer(self.take(n), dtype=np.int8).copy()
        if t == TAG_INT_ARRAY:
            n = self.unpack(_S_I)
            return np.frombuffer(self.take(4 * n), dtype=">i4").astype(np.int32)
        if t == TAG_LONG_ARRAY:
            n = self.unpack(_S_I)
            return np.frombuffer(self.take(8 * n), dtype=">i8").astype(np.int64)
        raise ValueError(f"알 수 없는 태그 {t} (위치 {self.p})")


def loads(b: bytes) -> dict:
    """압축하지 않은 NBT 바이트 → 루트 Compound. (이름은 버림)"""
    r = _Reader(b)
    t = r.take(1)[0]
    if t != TAG_COMPOUND:
        raise ValueError(f"루트가 Compound가 아님: {t}")
    r.str()
    return r.payload(TAG_COMPOUND)


# ---------------------------------------------------------------- 파일

def read_file(path) -> dict:
    """gzip/zlib/무압축 자동 판별."""
    with open(path, "rb") as f:
        raw = f.read()
    if raw[:2] == b"\x1f\x8b":
        raw = gzip.decompress(raw)
    elif raw[:1] == b"\x78":
        raw = zlib.decompress(raw)
    return loads(raw)


def write_file(path, root: dict, compress: str = "gzip"):
    data = dumps(root)
    if compress == "gzip":
        buf = io.BytesIO()
        with gzip.GzipFile(fileobj=buf, mode="wb", mtime=0) as g:
            g.write(data)
        data = buf.getvalue()
    elif compress == "zlib":
        data = zlib.compress(data)
    with open(path, "wb") as f:
        f.write(data)


# ---------------------------------------------------------------- 사람이 읽는 출력 (SNBT 비슷하게)

def to_snbt(v, indent: int = 0, max_array: int = 16) -> str:
    sp = "  " * indent
    t = tag_of(v)
    if t == TAG_BYTE:
        return f"{int(v)}b"
    if t == TAG_SHORT:
        return f"{int(v)}s"
    if t == TAG_INT:
        return f"{int(v)}"
    if t == TAG_LONG:
        return f"{int(v)}L"
    if t == TAG_FLOAT:
        return f"{float(v)!r}f"
    if t == TAG_DOUBLE:
        return f"{float(v)!r}d"
    if t == TAG_STRING:
        return '"' + v.replace("\\", "\\\\").replace('"', '\\"') + '"'
    if t in (TAG_BYTE_ARRAY, TAG_INT_ARRAY, TAG_LONG_ARRAY):
        a = np.frombuffer(bytes(v), np.int8) if isinstance(v, (bytes, bytearray)) else np.asarray(v)
        pre = {TAG_BYTE_ARRAY: "B", TAG_INT_ARRAY: "I", TAG_LONG_ARRAY: "L"}[t]
        items = ", ".join(str(int(x)) for x in a[:max_array])
        more = f", ... ({a.size} total)" if a.size > max_array else ""
        return f"[{pre}; {items}{more}]"
    if t == TAG_LIST:
        if not v:
            return "[]"
        if all(tag_of(x) not in (TAG_COMPOUND, TAG_LIST) for x in v):
            return "[" + ", ".join(to_snbt(x, 0, max_array) for x in v) + "]"
        inner = ",\n".join(sp + "  " + to_snbt(x, indent + 1, max_array) for x in v)
        return "[\n" + inner + "\n" + sp + "]"
    if t == TAG_COMPOUND:
        if not v:
            return "{}"
        inner = ",\n".join(f"{sp}  {k}: {to_snbt(x, indent + 1, max_array)}" for k, x in v.items())
        return "{\n" + inner + "\n" + sp + "}"
    raise TypeError(t)
