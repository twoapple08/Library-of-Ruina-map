package ruina.library.form;

import net.minecraft.core.BlockPos;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.RenderShape;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.BooleanProperty;
import net.minecraft.world.level.block.state.properties.IntegerProperty;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.Shapes;
import net.minecraft.world.phys.shapes.VoxelShape;

/**
 * 자유 형체 블록 (ruina:form): 보이는 모습은 칸마다의 형체 조각 (클라이언트 FormModel 이 위치로 찾아 청크 메시에 구움).
 * 자체로는 빛을 막지 않고 고를 수도 없음. 빌드 코드(tools/forms.py)가 서버 검증 뒤 자리 표시에서 바꿔 넣음:
 * 공기 → solid=false, barrier → solid=true (충돌만), light[level=N] → light=N. glow = BSL 발광 색 번호 (0 = 없음, 26~50 약한 빛).
 */
public class FormBlock extends Block {
	public static final BooleanProperty SOLID = BooleanProperty.create("solid");
	public static final IntegerProperty LIGHT = IntegerProperty.create("light", 0, 15);
	public static final IntegerProperty GLOW = IntegerProperty.create("glow", 0, 50);

	public FormBlock(Properties properties) {
		super(properties);
		registerDefaultState(stateDefinition.any().setValue(SOLID, false).setValue(LIGHT, 0).setValue(GLOW, 0));
	}

	@Override
	protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
		builder.add(SOLID, LIGHT, GLOW);
	}

	@Override
	protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
		return Shapes.empty();
	}

	@Override
	protected VoxelShape getCollisionShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
		return state.getValue(SOLID) ? Shapes.block() : Shapes.empty();
	}

	@Override
	protected VoxelShape getOcclusionShape(BlockState state) {
		return Shapes.empty();
	}

	@Override
	protected boolean propagatesSkylightDown(BlockState state) {
		return true;
	}

	@Override
	protected int getLightDampening(BlockState state) {
		return 0;
	}

	@Override
	protected float getShadeBrightness(BlockState state, BlockGetter level, BlockPos pos) {
		return 1.0f;
	}

	@Override
	protected RenderShape getRenderShape(BlockState state) {
		return RenderShape.MODEL;
	}
}
