package ruina.library.test;

import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.Identifier;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockBehaviour;

import net.fabricmc.api.ModInitializer;

/**
 * ② 준비 시험: 블록 격자와 상관없는 자유 형체(칸 밖으로 뻗는 비틀린 띠)를 청크 메시에 구워 그릴 수 있는지.
 * 바닐라(Indigo)와 Sodium+Iris(+BSL) 양쪽 스크린샷으로 확인. 모양은 client/MeshProbeModel.
 */
public class MeshProbe implements ModInitializer {
	public static final ResourceKey<Block> KEY = ResourceKey.create(Registries.BLOCK,
			Identifier.fromNamespaceAndPath("ruina-test", "mesh_probe"));
	public static Block BLOCK;

	@Override
	public void onInitialize() {
		BLOCK = Registry.register(BuiltInRegistries.BLOCK, KEY,
				new Block(BlockBehaviour.Properties.of().setId(KEY).noOcclusion()));
	}
}
