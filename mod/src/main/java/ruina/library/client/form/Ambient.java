package ruina.library.client.form;

import java.util.List;

import net.minecraft.client.Minecraft;
import net.minecraft.client.renderer.texture.TextureAtlasSprite;
import net.minecraft.data.AtlasIds;
import net.minecraft.util.RandomSource;

/** 매 틱: 지금 공간의 emitters.json 중 플레이어 가까이(64블록) 있는 상자에서 종이를 날림. */
public final class Ambient {
	private Ambient() {
	}

	private static final double NEAR = 64;
	private static final RandomSource RNG = RandomSource.create();

	public static void tick(Minecraft mc) {
		if (mc.level == null || mc.player == null || mc.isPaused()) {
			return;
		}
		String space = FormStore.currentSpace();
		if (space == null) {
			return;
		}
		List<FormStore.EmitterSpec> list = FormStore.emitters(space);
		double px = mc.player.getX(), py = mc.player.getY(), pz = mc.player.getZ();
		for (FormStore.EmitterSpec e : list) {
			double[] b = e.box();
			// 상자와 플레이어 주변(±NEAR) 의 겹친 부분에서만
			double x0 = Math.max(b[0], px - NEAR), x1 = Math.min(b[3], px + NEAR);
			double y0 = Math.max(b[1], py - NEAR), y1 = Math.min(b[4], py + NEAR);
			double z0 = Math.max(b[2], pz - NEAR), z1 = Math.min(b[5], pz + NEAR);
			if (x0 >= x1 || y0 >= y1 || z0 >= z1) {
				continue;
			}
			double full = (b[3] - b[0]) * (b[5] - b[2]);
			double part = (x1 - x0) * (z1 - z0);
			double expect = e.rate() / 20.0 * (full > 0 ? part / full : 1);
			int n = (int) expect + (RNG.nextDouble() < expect - (int) expect ? 1 : 0);
			for (int i = 0; i < n; i++) {
				TextureAtlasSprite sp = mc.getAtlasManager().getAtlasOrThrow(AtlasIds.BLOCKS)
						.getSprite(e.sprites().get(RNG.nextInt(e.sprites().size())));
				mc.particleEngine.add(new PaperParticle(mc.level, x0 + RNG.nextDouble() * (x1 - x0),
						y0 + RNG.nextDouble() * (y1 - y0), z0 + RNG.nextDouble() * (z1 - z0), sp, e));
			}
		}
	}
}
