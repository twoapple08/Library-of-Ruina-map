package ruina.library.client.form;

import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.util.Arrays;

import net.minecraft.core.BlockPos;

/**
 * 형체 파일 한 개 (tools/forms.py `_write_cells` 형식): 칸 목록 + 면 레코드.
 * 면 = u16 재질, u16 0, 꼭짓점 4 × (i16 x,y,z / u16 u,v / u32 ARGB / i8 nx,ny,nz, u8) = 76바이트.
 */
public final class FormData {
	public static final int QUAD = 76;
	public static final int VERT = 18;

	public final float scale;
	private final long[] keys;
	private final int[] start;
	private final int[] count;
	public final ByteBuffer quads;

	private FormData(float scale, long[] keys, int[] start, int[] count, ByteBuffer quads) {
		this.scale = scale;
		this.keys = keys;
		this.start = start;
		this.count = count;
		this.quads = quads;
	}

	public static FormData read(byte[] raw) {
		ByteBuffer b = ByteBuffer.wrap(raw).order(ByteOrder.LITTLE_ENDIAN);
		if (b.get() != 'R' || b.get() != 'F' || b.get() != 'M' || b.get() != '1') {
			throw new IllegalArgumentException("형체 파일 형식이 아님");
		}
		float scale = b.getFloat();
		int n = b.getInt();
		long[] k = new long[n];
		int[] s = new int[n];
		int[] c = new int[n];
		Integer[] order = new Integer[n];
		for (int i = 0; i < n; i++) {
			int x = b.getInt(), y = b.getInt(), z = b.getInt();
			k[i] = BlockPos.asLong(x, y, z);
			s[i] = b.getInt();
			c[i] = b.getInt();
			order[i] = i;
		}
		Arrays.sort(order, (p, q) -> Long.compare(k[p], k[q]));
		long[] ks = new long[n];
		int[] ss = new int[n];
		int[] cs = new int[n];
		for (int i = 0; i < n; i++) {
			ks[i] = k[order[i]];
			ss[i] = s[order[i]];
			cs[i] = c[order[i]];
		}
		ByteBuffer q = b.slice().order(ByteOrder.LITTLE_ENDIAN);
		return new FormData(scale, ks, ss, cs, q);
	}

	/** 칸의 번호 (없으면 -1). */
	public int find(long posKey) {
		int i = Arrays.binarySearch(keys, posKey);
		return i < 0 ? -1 : i;
	}

	public int start(int cell) {
		return start[cell];
	}

	public int count(int cell) {
		return count[cell];
	}

	public int cells() {
		return keys.length;
	}

	// ---------------------------------------------- 면 읽기 (q = 면 번호, v = 꼭짓점 0~3)
	public int material(int q) {
		return quads.getShort(q * QUAD) & 0xFFFF;
	}

	private int vbase(int q, int v) {
		return q * QUAD + 4 + v * VERT;
	}

	public float x(int q, int v) {
		return quads.getShort(vbase(q, v)) / scale;
	}

	public float y(int q, int v) {
		return quads.getShort(vbase(q, v) + 2) / scale;
	}

	public float z(int q, int v) {
		return quads.getShort(vbase(q, v) + 4) / scale;
	}

	public float u(int q, int v) {
		return (quads.getShort(vbase(q, v) + 6) & 0xFFFF) / 65535f;
	}

	public float v(int q, int v) {
		return (quads.getShort(vbase(q, v) + 8) & 0xFFFF) / 65535f;
	}

	public int argb(int q, int v) {
		return quads.getInt(vbase(q, v) + 10);
	}

	public float nx(int q, int v) {
		return quads.get(vbase(q, v) + 14) / 127f;
	}

	public float ny(int q, int v) {
		return quads.get(vbase(q, v) + 15) / 127f;
	}

	public float nz(int q, int v) {
		return quads.get(vbase(q, v) + 16) / 127f;
	}
}
