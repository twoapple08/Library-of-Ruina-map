package ruina.library.client;

import net.minecraft.client.renderer.blockentity.BlockEntityRenderers;

import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.fabricmc.fabric.api.client.model.loading.v1.ModelLoadingPlugin;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;
import net.fabricmc.fabric.api.client.rendering.v1.hud.HudElementRegistry;

import ruina.library.FxPayload;
import ruina.library.RuinaMod;
import ruina.library.client.form.Ambient;
import ruina.library.client.form.FormModel;
import ruina.library.client.form.FormStore;
import ruina.library.client.form.MoverRenderer;
import ruina.library.client.form.PaintedSky;
import ruina.library.form.Forms;

/** 내 화면 쪽: 이펙트 받기 + 화면 위에 그리기, 자유 형체(형체 블록 모델·움직이는 형체·종이 파티클·그린 하늘). */
public class RuinaClient implements ClientModInitializer {
	@Override
	public void onInitializeClient() {
		ClientPlayNetworking.registerGlobalReceiver(FxPayload.TYPE, (payload, context) -> FxOverlay.receive(payload));
		HudElementRegistry.addLast(RuinaMod.id("fx"), FxOverlay::render);
		// 리소스를 다시 읽을 때(모델 굽기 시작) 형체 데이터도 비움 → 새 리소스에서 다시 읽음
		ModelLoadingPlugin.register(ctx -> {
			FormStore.clear();
			ctx.modifyBlockModelAfterBake().register((model, c) -> c.state().is(Forms.FORM) ? new FormModel(model) : model);
		});
		BlockEntityRenderers.register(Forms.MOVER_ENTITY, c -> new MoverRenderer());
		ClientTickEvents.END_CLIENT_TICK.register(Ambient::tick);
		PaintedSky.init();
	}
}
