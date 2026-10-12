package ruina.library;

import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.level.Level;

/** 도서관 아이템 (초대장·방전환·세피라). 우클릭으로 사용. */
public class RuinaItem extends Item {
	public enum Kind {
		INVITATION, ROOM, SEPHIRAH
	}

	private final Kind kind;
	private final String anchor;   // 세피라: 그 층 전경 도착 자리

	public RuinaItem(Properties properties, Kind kind, String anchor) {
		super(properties);
		this.kind = kind;
		this.anchor = anchor;
	}

	@Override
	public InteractionResult use(Level level, Player player, InteractionHand hand) {
		if (player instanceof ServerPlayer sp) {
			Library.use(sp, kind, anchor);
		}
		return InteractionResult.SUCCESS;
	}
}
