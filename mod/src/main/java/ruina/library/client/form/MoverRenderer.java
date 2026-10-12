package ruina.library.client.form;

import org.joml.Quaternionf;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;

import net.minecraft.client.renderer.SubmitNodeCollector;
import net.minecraft.client.renderer.blockentity.BlockEntityRenderer;
import net.minecraft.client.renderer.blockentity.state.BlockEntityRenderState;
import net.minecraft.client.renderer.chunk.ChunkSectionLayer;
import net.minecraft.client.renderer.feature.ModelFeatureRenderer;
import net.minecraft.client.renderer.rendertype.RenderType;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.client.renderer.state.level.CameraRenderState;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.client.renderer.texture.TextureAtlasSprite;
import net.minecraft.world.phys.Vec3;

import ruina.library.form.MoverBlockEntity;

/**
 * 움직이는 형체: spin(축 회전)·swing(진자)·bob(위아래)·still, follow(카메라를 따라오는 먼 배경 — 하늘 그림·먼 산).
 * 모양은 forms/&lt;공간&gt;/mesh_N.bin (pivot 기준). 화면 밖이어도 그림 (큰 톱니·배경).
 */
public class MoverRenderer implements BlockEntityRenderer<MoverBlockEntity, MoverRenderer.State> {
	private static final int FULL_BRIGHT = 0xF000F0;

	public static class State extends BlockEntityRenderState {
		FormStore.MoverSpec spec;
		float seconds;
		double camX, camY, camZ;
	}

	@Override
	public State createRenderState() {
		return new State();
	}

	@Override
	public void extractRenderState(MoverBlockEntity be, State state, float partialTick, Vec3 cameraPosition,
			ModelFeatureRenderer.CrumblingOverlay breakProgress) {
		BlockEntityRenderer.super.extractRenderState(be, state, partialTick, cameraPosition, breakProgress);
		String space = FormStore.currentSpace();
		state.spec = space == null ? null : FormStore.mover(space, be.getBlockPos().asLong());
		state.seconds = be.getLevel() == null ? 0 : (be.getLevel().getGameTime() % 24000000L + partialTick) / 20f;
		state.camX = cameraPosition.x;
		state.camY = cameraPosition.y;
		state.camZ = cameraPosition.z;
	}

	@Override
	public void submit(State state, PoseStack pose, SubmitNodeCollector collector, CameraRenderState camera) {
		FormStore.MoverSpec s = state.spec;
		if (s == null) {
			return;
		}
		pose.pushPose();
		float t = s.period() > 0 ? state.seconds / s.period() + s.phase() : 0;
		float[] a = s.axis();
		switch (s.motion()) {
			case "follow" -> pose.translate(state.camX - state.blockPos.getX(), state.camY - state.blockPos.getY(),
					state.camZ - state.blockPos.getZ());
			case "spin" -> {
				pose.translate(s.pivot()[0], s.pivot()[1], s.pivot()[2]);
				pose.rotate(new Quaternionf().fromAxisAngleRad(a[0], a[1], a[2], (float) (t * Math.PI * 2)));
			}
			case "swing" -> {
				pose.translate(s.pivot()[0], s.pivot()[1], s.pivot()[2]);
				pose.rotate(new Quaternionf().fromAxisAngleRad(a[0], a[1], a[2],
						(float) Math.toRadians(s.amp() * Math.sin(t * Math.PI * 2))));
			}
			case "bob" -> {
				float o = (float) (s.amp() * Math.sin(t * Math.PI * 2));
				pose.translate(s.pivot()[0] + a[0] * o, s.pivot()[1] + a[1] * o, s.pivot()[2] + a[2] * o);
			}
			default -> pose.translate(s.pivot()[0], s.pivot()[1], s.pivot()[2]);
		}
		int light = s.motion().equals("follow") ? FULL_BRIGHT : state.lightCoords;
		for (ChunkSectionLayer layer : ChunkSectionLayer.values()) {
			RenderType type = switch (layer) {
				case CUTOUT -> RenderTypes.cutoutMovingBlock();
				case TRANSLUCENT -> RenderTypes.translucentMovingBlock();
				default -> RenderTypes.solidMovingBlock();
			};
			FormData d = s.mesh();
			collector.submitCustomGeometry(pose, type, (p, vc) -> emit(d, layer, light, p, vc));
		}
		pose.popPose();
	}

	private static void emit(FormData d, ChunkSectionLayer layer, int light, PoseStack.Pose p, VertexConsumer vc) {
		int n = d.count(0);
		for (int q = 0; q < n; q++) {
			FormStore.Mat m = FormStore.material(d.material(q));
			if (m == null || m.layer != layer) {
				continue;
			}
			TextureAtlasSprite sp = m.sprite();
			int l = m.emissive ? FULL_BRIGHT : light;
			for (int v = 0; v < 4; v++) {
				vc.addVertex(p, d.x(q, v), d.y(q, v), d.z(q, v)).setColor(d.argb(q, v))
						.setUv(sp.getU(d.u(q, v)), sp.getV(d.v(q, v))).setOverlay(OverlayTexture.NO_OVERLAY).setLight(l)
						.setNormal(p, d.nx(q, v), d.ny(q, v), d.nz(q, v));
			}
		}
	}

	@Override
	public boolean shouldRenderOffScreen() {
		return true;
	}

	@Override
	public int getViewDistance() {
		return 512;
	}

	@Override
	public boolean shouldRender(MoverBlockEntity be, Vec3 cameraPosition) {
		return true;
	}
}
