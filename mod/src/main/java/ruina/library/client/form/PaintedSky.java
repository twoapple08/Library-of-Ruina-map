package ruina.library.client.form;

import java.lang.reflect.Field;
import java.lang.reflect.Method;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import com.mojang.renderpearl.api.pipeline.ColorTargetState;
import com.mojang.renderpearl.api.pipeline.CompareOp;
import com.mojang.renderpearl.api.pipeline.DepthStencilState;
import com.mojang.renderpearl.api.pipeline.RenderPipeline;

import net.minecraft.client.renderer.RenderPipelines;
import net.minecraft.client.renderer.rendertype.RenderSetup;
import net.minecraft.client.renderer.rendertype.RenderType;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.client.renderer.texture.TextureAtlas;
import net.minecraft.client.renderer.texture.TextureAtlasSprite;

import net.fabricmc.fabric.api.client.rendering.v1.level.LevelRenderContext;
import net.fabricmc.fabric.api.client.rendering.v1.level.LevelRenderEvents;

import ruina.library.RuinaMod;

/**
 * 그린 하늘: 공간마다 forms/&lt;공간&gt;/sky.bin (카메라 둘레 구, tools/forms.py FormLayer.sky) 을 매 프레임 카메라 자리에 그림.
 * 셰이더(ruina:core/painted_sky)가 깊이를 가장 먼 값으로 두므로 지형·형체 뒤 빈 곳에만 보이고, 안개를 받지 않음
 * (렌더 거리와 상관없이 원화 하늘·먼 배경 그대로). 바닐라 하늘 위에 덮어 그림.
 */
public final class PaintedSky {
	private static final int FULL_BRIGHT = 0xF000F0;
	private static RenderType type;
	private static boolean failed;

	private PaintedSky() {
	}

	public static void init() {
		LevelRenderEvents.COLLECT_SUBMITS.register(PaintedSky::submit);
	}

	private static RenderType type() {
		if (type == null && !failed) {
			try {
				Field f = RenderPipelines.class.getDeclaredField("BLOCK_SNIPPET");
				f.setAccessible(true);
				RenderPipeline.Snippet block = (RenderPipeline.Snippet) f.get(null);
				RenderPipeline pipeline = RenderPipeline.builder(block)
						.withLocation(RuinaMod.id("pipeline/painted_sky"))
						.withVertexShader(RuinaMod.id("core/painted_sky"))
						.withFragmentShader(RuinaMod.id("core/painted_sky"))
						.withDepthStencilState(new DepthStencilState(CompareOp.GREATER_THAN_OR_EQUAL, false))
						.withCull(false)
						.withColorTargetState(ColorTargetState.DEFAULT)
						.build();
				RenderSetup setup = RenderSetup.builder(pipeline).withTexture("Sampler0", TextureAtlas.LOCATION_BLOCKS)
						.useLightmap().createRenderSetup();
				Method create = RenderType.class.getDeclaredMethod("create", String.class, RenderSetup.class);
				create.setAccessible(true);
				type = (RenderType) create.invoke(null, "ruina_painted_sky", setup);
			} catch (ReflectiveOperationException | RuntimeException e) {
				failed = true;
				RuinaMod.LOGGER.error("그린 하늘 준비 실패", e);
			}
		}
		return type;
	}

	private static void submit(LevelRenderContext ctx) {
		String space = FormStore.currentSpace();
		if (space == null) {
			return;
		}
		FormData sky = FormStore.sky(space);
		if (sky == null) {
			return;
		}
		RenderType t = type();
		if (t == null) {
			return;
		}
		PoseStack pose = ctx.poseStack();
		ctx.submitNodeCollector().submitCustomGeometry(pose, t, (p, vc) -> emit(sky, p, vc));
	}

	private static void emit(FormData d, PoseStack.Pose p, VertexConsumer vc) {
		int n = d.count(0);
		for (int q = 0; q < n; q++) {
			FormStore.Mat m = FormStore.material(d.material(q));
			if (m == null) {
				continue;
			}
			TextureAtlasSprite sp = m.sprite();
			for (int v = 0; v < 4; v++) {
				vc.addVertex(p, d.x(q, v), d.y(q, v), d.z(q, v)).setColor(d.argb(q, v))
						.setUv(sp.getU(d.u(q, v)), sp.getV(d.v(q, v))).setOverlay(OverlayTexture.NO_OVERLAY).setLight(FULL_BRIGHT)
						.setNormal(p, 0, 1, 0);
			}
		}
	}
}
