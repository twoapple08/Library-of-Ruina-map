package ruina.library.form;

import net.minecraft.core.BlockPos;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;

/** 데이터 없음 (렌더러가 위치로 movers.json 을 찾음). */
public class MoverBlockEntity extends BlockEntity {
	public MoverBlockEntity(BlockPos pos, BlockState state) {
		super(Forms.MOVER_ENTITY, pos, state);
	}
}
