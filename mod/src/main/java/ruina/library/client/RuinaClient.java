package ruina.library.client;

import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;
import net.fabricmc.fabric.api.client.rendering.v1.hud.HudElementRegistry;

import ruina.library.FxPayload;
import ruina.library.RuinaMod;

/** 내 화면 쪽: 이펙트 받기 + 화면 위에 그리기. */
public class RuinaClient implements ClientModInitializer {
	@Override
	public void onInitializeClient() {
		ClientPlayNetworking.registerGlobalReceiver(FxPayload.TYPE, (payload, context) -> FxOverlay.receive(payload));
		HudElementRegistry.addLast(RuinaMod.id("fx"), FxOverlay::render);
	}
}
