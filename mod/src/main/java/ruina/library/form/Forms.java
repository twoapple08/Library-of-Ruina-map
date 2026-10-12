package ruina.library.form;

import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.material.PushReaction;

import net.fabricmc.fabric.api.object.builder.v1.block.entity.FabricBlockEntityTypeBuilder;

import ruina.library.RuinaMod;

/** 자유 형체 공용 등록: 형체 블록, 움직이는 형체 블록·블록 엔티티. 아이템 없음 (월드에만). 종이 파티클은 클라이언트만 (client/form/Ambient). */
public final class Forms {
	private Forms() {
	}

	public static Block FORM;
	public static Block MOVER;
	public static BlockEntityType<MoverBlockEntity> MOVER_ENTITY;

	public static void init() {
		ResourceKey<Block> fk = ResourceKey.create(Registries.BLOCK, RuinaMod.id("form"));
		FORM = Registry.register(BuiltInRegistries.BLOCK, fk, new FormBlock(base(fk)
				.lightLevel(s -> s.getValue(FormBlock.LIGHT))));
		ResourceKey<Block> mk = ResourceKey.create(Registries.BLOCK, RuinaMod.id("mover"));
		MOVER = Registry.register(BuiltInRegistries.BLOCK, mk, new MoverBlock(base(mk)));
		MOVER_ENTITY = Registry.register(BuiltInRegistries.BLOCK_ENTITY_TYPE, RuinaMod.id("mover"),
				FabricBlockEntityTypeBuilder.create(MoverBlockEntity::new, MOVER).build());
	}

	private static BlockBehaviour.Properties base(ResourceKey<Block> key) {
		return BlockBehaviour.Properties.of().setId(key).noOcclusion().strength(-1.0f, 3600000.0f).noLootTable()
				.noTerrainParticles().pushReaction(PushReaction.IMMOVEABLE)
				.isValidSpawn((s, l, p, e) -> false).isSuffocating((s, l, p) -> false).isViewBlocking((s, l, p, a) -> false);
	}
}
