package ruina.library;

import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;

/**
 * 모드 전용 화면 이펙트 (서버 → 내 화면). kind: fade_in(가려짐) / fade_out(걷힘) / title(층 이름 카드) / flash(번쩍임).
 * 그리기는 클라이언트(client/FxOverlay)에서만 → 서버·엔티티 부담 없음.
 */
public record FxPayload(String kind, String text) implements CustomPacketPayload {
	public static final CustomPacketPayload.Type<FxPayload> TYPE = new Type<>(RuinaMod.id("fx"));
	public static final StreamCodec<RegistryFriendlyByteBuf, FxPayload> CODEC = CustomPacketPayload.codec(FxPayload::write, FxPayload::new);

	public FxPayload(RegistryFriendlyByteBuf buf) {
		this(buf.readUtf(), buf.readUtf());
	}

	public void write(RegistryFriendlyByteBuf buf) {
		buf.writeUtf(kind);
		buf.writeUtf(text);
	}

	@Override
	public Type<? extends CustomPacketPayload> type() {
		return TYPE;
	}
}
