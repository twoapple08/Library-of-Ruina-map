package ruina.library.test;

import net.minecraft.resources.Identifier;

import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.client.rendering.v1.hud.HudElement;
import net.fabricmc.fabric.api.client.rendering.v1.hud.HudElementRegistry;
import net.fabricmc.fabric.api.client.rendering.v1.hud.VanillaHudElements;

/** 게임 테스트 전용: clean 이면 바닐라 HUD(핫바·조준점·채팅 등)를 그리지 않음 → 원화 비교용 깨끗한 스크린샷. */
public class RuinaTestClient implements ClientModInitializer {
	public static volatile boolean clean = false;

	@Override
	public void onInitializeClient() {
		for (Identifier id : new Identifier[] {VanillaHudElements.HOTBAR, VanillaHudElements.CROSSHAIR,
				VanillaHudElements.INFO_BAR, VanillaHudElements.EXPERIENCE_LEVEL, VanillaHudElements.HELD_ITEM_TOOLTIP,
				VanillaHudElements.OVERLAY_MESSAGE, VanillaHudElements.CHAT, VanillaHudElements.ARMOR_BAR,
				VanillaHudElements.HEALTH_BAR, VanillaHudElements.FOOD_BAR}) {
			HudElementRegistry.replaceElement(id, original -> hideable(original));
		}
	}

	private static HudElement hideable(HudElement original) {
		return (graphics, deltaTracker) -> {
			if (!clean) {
				original.extractRenderState(graphics, deltaTracker);
			}
		};
	}
}
