package ruina.library.client.form;

import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.client.particle.SingleQuadParticle;
import net.minecraft.client.renderer.texture.TextureAtlasSprite;

/** 날리는 종이: 바람 + 좌우로 팔랑거림 + 돌기, 끝에 흐려짐. 스프라이트는 블록 아틀라스 (forms 텍스처). */
public class PaperParticle extends SingleQuadParticle {
	private final float spin;
	private final float wx, wy, wz;
	private final float seed;
	private final boolean glow;

	public PaperParticle(ClientLevel level, double x, double y, double z, TextureAtlasSprite sprite,
			FormStore.EmitterSpec e) {
		super(level, x, y, z, sprite);
		this.wx = e.wind()[0] / 20f;
		this.wy = e.wind()[1] / 20f;
		this.wz = e.wind()[2] / 20f;
		this.spin = e.spin();
		this.glow = e.glow();
		this.seed = random.nextFloat() * 100f;
		this.quadSize = e.size() * (0.7f + random.nextFloat() * 0.6f);
		this.lifetime = (int) (e.life() * 20 * (0.7f + random.nextFloat() * 0.6f));
		this.gravity = 0;
		this.friction = 1;
		this.hasPhysics = true;
		this.roll = random.nextFloat() * 6.28f;
		this.oRoll = roll;
		float[] c = e.color();
		setColor(c[0], c[1], c[2]);
		this.xd = wx;
		this.yd = wy;
		this.zd = wz;
	}

	@Override
	public void tick() {
		super.tick();
		float t = (age + seed) * 0.15f;
		xd = wx + Math.sin(t) * 0.04 * spin;
		zd = wz + Math.cos(t * 0.8f) * 0.04 * spin;
		yd = wy * (0.6 + 0.4 * Math.abs(Math.sin(t * 0.5)));
		oRoll = roll;
		roll += (float) Math.sin(t * 0.7f) * 0.12f * spin;
		int fade = Math.min(20, lifetime / 4);
		setAlpha(Math.min(1f, Math.min(age / 10f, (lifetime - age) / (float) Math.max(1, fade))));
		if (onGround) {
			lifetime = Math.min(lifetime, age + 40);
		}
	}

	@Override
	protected Layer getLayer() {
		return Layer.TRANSLUCENT_TERRAIN;
	}

	@Override
	protected int getLightCoords(float partialTick) {
		return glow ? 0xF000F0 : super.getLightCoords(partialTick);
	}
}
