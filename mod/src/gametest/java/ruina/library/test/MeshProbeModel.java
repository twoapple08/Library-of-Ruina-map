package ruina.library.test;

import java.util.List;
import java.util.function.Predicate;

import org.jspecify.annotations.Nullable;

import net.minecraft.client.renderer.block.dispatch.BlockStateModel;
import net.minecraft.client.renderer.block.dispatch.BlockStateModelPart;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.util.RandomSource;
import net.minecraft.client.renderer.block.BlockAndTintGetter;
import net.minecraft.world.level.block.state.BlockState;

import net.fabricmc.fabric.api.client.renderer.v1.mesh.MutableQuadView;
import net.fabricmc.fabric.api.client.renderer.v1.mesh.QuadEmitter;

/** 시험 형체: 반지름 1.5칸, 높이 5칸을 한 바퀴 반 도는 비틀린 띠 (칸 밖으로 뻗음, 양면). 텍스처는 원래 모델(돌)의 것. */
public class MeshProbeModel implements BlockStateModel {
	private static final int SEG = 36;
	private final BlockStateModel base;

	public MeshProbeModel(BlockStateModel base) {
		this.base = base;
	}

	@Override
	public void collectParts(RandomSource random, List<BlockStateModelPart> parts) {
		base.collectParts(random, parts);
	}

	@Override
	public net.minecraft.client.resources.model.sprite.Material.Baked particleMaterial() {
		return base.particleMaterial();
	}

	@Override
	public int materialFlags() {
		return base.materialFlags();
	}

	@Override
	public void emitQuads(QuadEmitter emitter, BlockAndTintGetter level, BlockPos pos, BlockState state, RandomSource random,
			Predicate<@Nullable Direction> cullTest) {
		for (int i = 0; i < SEG; i++) {
			float[] a = rib(i), b = rib(i + 1);
			for (int side = 0; side < 2; side++) {   // 양면
				int[] order = side == 0 ? new int[] {0, 1, 2, 3} : new int[] {3, 2, 1, 0};
				float[][] v = {{a[0], a[1], a[2]}, {a[3], a[4], a[5]}, {b[3], b[4], b[5]}, {b[0], b[1], b[2]}};
				float[][] uv = {{0, (float) i / SEG}, {1, (float) i / SEG}, {1, (float) (i + 1) / SEG}, {0, (float) (i + 1) / SEG}};
				for (int k = 0; k < 4; k++) {
					int o = order[k];
					emitter.pos(k, v[o][0], v[o][1], v[o][2]).uv(k, uv[o][0], uv[o][1] * 4 % 1.0001f);
				}
				emitter.materialBake(base.particleMaterial(), MutableQuadView.BAKE_NORMALIZED);
				emitter.color(-1, -1, -1, -1);
				emitter.emit();
			}
		}
	}

	/** 띠 단면 (안쪽 점, 바깥 점): 블록 중심 기준 나선. */
	private static float[] rib(int i) {
		double t = (double) i / SEG, ang = t * Math.PI * 3, tw = t * Math.PI * 2;
		double cx = 0.5 + 1.5 * Math.cos(ang), cz = 0.5 + 1.5 * Math.sin(ang), y = 5 * t;
		double dx = 0.5 * Math.cos(ang) * Math.cos(tw), dz = 0.5 * Math.sin(ang) * Math.cos(tw), dy = 0.5 * Math.sin(tw);
		return new float[] {(float) (cx - dx), (float) (y - dy), (float) (cz - dz), (float) (cx + dx), (float) (y + dy), (float) (cz + dz)};
	}
}
