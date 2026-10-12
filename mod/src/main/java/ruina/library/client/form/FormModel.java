package ruina.library.client.form;

import java.util.List;
import java.util.function.Predicate;

import org.jspecify.annotations.Nullable;

import net.minecraft.client.renderer.block.BlockAndTintGetter;
import net.minecraft.client.renderer.block.dispatch.BlockStateModel;
import net.minecraft.client.renderer.block.dispatch.BlockStateModelPart;
import net.minecraft.client.renderer.texture.TextureAtlasSprite;
import net.minecraft.client.resources.model.sprite.Material;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.block.state.BlockState;

import net.fabricmc.fabric.api.client.renderer.v1.mesh.QuadAtlas;
import net.fabricmc.fabric.api.client.renderer.v1.mesh.QuadEmitter;
import net.fabricmc.fabric.api.util.TriState;

/**
 * 형체 블록 모델: 칸 위치로 형체 파일에서 자기 조각을 찾아 청크 메시에 구움 (매 프레임 비용 없음, Sodium·Iris 그대로).
 * 조명은 게임이 칸 기준으로 계산 (emissive 재질은 최대 밝기, flat 재질은 방향별 어둡게 하기 없음).
 */
public class FormModel implements BlockStateModel {
	private final BlockStateModel base;

	public FormModel(BlockStateModel base) {
		this.base = base;
	}

	@Override
	public void collectParts(RandomSource random, List<BlockStateModelPart> parts) {
		// 기본 모양 없음 (형체만)
	}

	@Override
	public Material.Baked particleMaterial() {
		return base.particleMaterial();
	}

	@Override
	public int materialFlags() {
		return base.materialFlags();
	}

	@Override
	public void emitQuads(QuadEmitter emitter, BlockAndTintGetter level, BlockPos pos, BlockState state, RandomSource random,
			Predicate<@Nullable Direction> cullTest) {
		String space = FormStore.currentSpace();
		if (space == null) {
			return;
		}
		FormData d = FormStore.region(space, pos.getX() >> 9, pos.getZ() >> 9);
		if (d == null) {
			return;
		}
		int cell = d.find(pos.asLong());
		if (cell < 0) {
			return;
		}
		int end = d.start(cell) + d.count(cell);
		for (int q = d.start(cell); q < end; q++) {
			FormStore.Mat m = FormStore.material(d.material(q));
			if (m == null) {
				continue;
			}
			TextureAtlasSprite sp = m.sprite();
			for (int v = 0; v < 4; v++) {
				emitter.pos(v, d.x(q, v), d.y(q, v), d.z(q, v));
				emitter.uv(v, sp.getU(d.u(q, v)), sp.getV(d.v(q, v)));
				emitter.color(v, d.argb(q, v));
				emitter.normal(v, d.nx(q, v), d.ny(q, v), d.nz(q, v));
			}
			emitter.atlas(QuadAtlas.BLOCK);
			emitter.chunkLayer(m.layer);
			emitter.emissive(m.emissive);
			emitter.ambientOcclusion(m.ao ? TriState.DEFAULT : TriState.FALSE);
			emitter.shadeDirectionOverride(m.flat ? Direction.UP : null);
			emitter.emit();
		}
	}
}
