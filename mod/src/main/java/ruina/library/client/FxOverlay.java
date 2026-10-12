package ruina.library.client;

import net.minecraft.client.DeltaTracker;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.Font;
import net.minecraft.client.gui.GuiGraphicsExtractor;

import ruina.library.FxPayload;

/**
 * 모드 전용 화면 이펙트 (포션 효과 대신, 화면 위에 사각형·글자만 그림 → 가벼움).
 * <ul>
 * <li>이동 암전: 잉크빛 어둠이 가장자리부터 덮었다가(0.5초) 도착 후 걷힘(1초)</li>
 * <li>층 이름 카드: 금빛 글자 + 위아래 가는 선, 나타났다 사라짐 (원작 층 이름 표시 느낌)</li>
 * <li>번쩍임: 따뜻한 흰빛이 0.35초 동안 사라짐 (방전환·티페리트)</li>
 * </ul>
 */
public final class FxOverlay {
	private FxOverlay() {
	}

	private static final int INK = 0x0d0a08;
	private static final int GOLD = 0xecd6a6;
	private static final int FLASH = 0xfff4dc;
	private static final float FADE_IN_S = 0.5f;
	private static final float FADE_OUT_S = 1.0f;
	private static final float TITLE_S = 3.2f;
	private static final float FLASH_S = 0.35f;

	private static boolean covering;
	private static float cover;        // 0 = 맑음, 1 = 완전히 가려짐
	private static String title = "";
	private static float titleAge = -1f;
	private static float flashAge = -1f;
	private static long last = System.nanoTime();

	static void receive(FxPayload p) {
		switch (p.kind()) {
			case "fade_in" -> covering = true;
			case "fade_out" -> covering = false;
			case "title" -> {
				title = p.text();
				titleAge = 0f;
			}
			case "flash" -> flashAge = 0f;
			default -> {
			}
		}
	}

	static void render(GuiGraphicsExtractor g, DeltaTracker deltaTracker) {
		long now = System.nanoTime();
		float dt = Math.min(0.1f, (now - last) / 1e9f);
		last = now;
		cover = covering ? Math.min(1f, cover + dt / FADE_IN_S) : Math.max(0f, cover - dt / FADE_OUT_S);
		int w = g.guiWidth();
		int h = g.guiHeight();

		if (cover > 0f) {
			float e = cover * cover * (3f - 2f * cover);   // 부드럽게
			// 가장자리부터: 바깥 띠가 먼저 짙어지고 가운데가 나중에 (8겹)
			for (int i = 0; i < 8; i++) {
				float t = i / 8f;
				float a = Math.clamp((e * 1.6f) - t * 0.6f, 0f, 1f);
				int ix = (int) (w * t * 0.5f);
				int iy = (int) (h * t * 0.5f);
				int col = argb(a * (i == 0 ? 1f : 0.35f), INK);
				g.fill(ix, iy, w - ix, h - iy, col);
			}
			g.fill(0, 0, w, h, argb(e, INK));
		}

		if (titleAge >= 0f) {
			titleAge += dt;
			float a = titleAge < 0.5f ? titleAge / 0.5f : titleAge > TITLE_S - 0.9f ? (TITLE_S - titleAge) / 0.9f : 1f;
			if (titleAge >= TITLE_S || title.isEmpty()) {
				titleAge = -1f;
			} else if (a > 0.02f) {
				Font font = Minecraft.getInstance().font;
				int cx = w / 2;
				int cy = (int) (h * 0.30f);
				float s = 2.2f;
				int tw = (int) (font.width(title) * s);
				int line = argb(a * 0.8f, GOLD);
				g.fill(cx - tw / 2 - 24, cy - 6, cx + tw / 2 + 24, cy - 5, line);
				g.fill(cx - tw / 2 - 24, cy + (int) (9 * s) + 5, cx + tw / 2 + 24, cy + (int) (9 * s) + 6, line);
				g.pose().pushMatrix();
				g.pose().translate(cx, cy);
				g.pose().scale(s);
				g.centeredText(font, title, 0, 0, argb(a, GOLD));
				g.pose().popMatrix();
			}
		}

		if (flashAge >= 0f) {
			flashAge += dt;
			float a = 1f - flashAge / FLASH_S;
			if (a <= 0f) {
				flashAge = -1f;
			} else {
				g.fill(0, 0, w, h, argb(a * a * 0.6f, FLASH));
			}
		}
	}

	private static int argb(float alpha, int rgb) {
		return ((int) (Math.clamp(alpha, 0f, 1f) * 255f) << 24) | rgb;
	}
}
