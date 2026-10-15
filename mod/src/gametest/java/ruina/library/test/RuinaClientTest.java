package ruina.library.test;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.function.Function;

import net.minecraft.client.KeyMapping;
import net.minecraft.client.Options;
import net.minecraft.client.gui.screens.worldselection.WorldCreationUiState;
import net.minecraft.core.BlockPos;

import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.fabricmc.fabric.api.client.gametest.v1.screenshot.TestScreenshotOptions;
import net.fabricmc.loader.api.FabricLoader;

import ruina.library.form.Forms;

/**
 * 실제 게임으로 확인: 새 야생 월드 → 아이템 우클릭(진짜 입력)으로 도서관 이동 → 도착 화면 스크린샷.
 * 결과: run/clientGameTest/screenshots/*.png, run/clientGameTest/ruina_test.txt (CI 가 ci-output 브랜치에 올림).
 */
public class RuinaClientTest implements FabricClientGameTest {
	private static final String[][] FLOORS = {
			// 세피라, 차원, 층 이름
			{"malkuth", "ruina:history", "역사"}, {"yesod", "ruina:technology", "기술과학"},
			{"hod", "ruina:literature", "문학"}, {"netzach", "ruina:art", "예술"},
			{"tiphereth", "ruina:natural_science", "자연과학"}, {"gebura", "ruina:language", "언어"},
			{"chesed", "ruina:social_science", "사회과학"}, {"binah", "ruina:philosophy", "철학"},
			{"hokma", "ruina:religion", "종교"}, {"keter", "ruina:general", "총류"},
	};

	/** Iris(+Sodium, 맵 전용 BSL) 가 함께 실행됐으면 셰이더 확인용 짧은 순회만 (스크린샷 이름 앞에 bsl_). */
	private static final boolean SHADERS = FabricLoader.getInstance().isModLoaded("iris");
	private static final String PREFIX = SHADERS ? "bsl_" : "";

	private final List<String> log = new ArrayList<>();
	private int fails = 0;
	private int shot = 0;

	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext sp = ctx.worldBuilder()
				.adjustSettings(c -> c.setGameMode(WorldCreationUiState.SelectedGameMode.CREATIVE)).create()) {
			ctx.runOnClient(c -> c.options.renderDistance().set(10));
			RuinaTestClient.clean = true;   // 핫바·조준점 등 숨김 (원화 비교용)
			render(sp);
			screenshot(ctx, sp, "overworld");
			String overworld = dim(ctx);
			if (SHADERS) {
				shaderTour(ctx, sp, overworld);
				if (fails > 0) {
					throw new AssertionError("셰이더 순회 실패 " + fails + "건 (ruina_test_bsl.txt)");
				}
				return;
			}

			String only = System.getProperty("ruina.only");
			if (only != null) {
				quick(ctx, sp, only);
				return;
			}

			// 초대장: 야생 → 외부
			useItem(ctx, sp, "invitation");
			check(ctx, "초대장 → 외부", "ruina:exterior");
			screenshot(ctx, sp, "exterior_title_card");   // 모드 이펙트: 도착 직후 층 이름 카드 '도서관'
			render(sp);
			screenshot(ctx, sp, "exterior");
			exteriorViews(ctx, sp);
			useItem(ctx, sp, "invitation");   // 외부 다른 자리 → 초대장 쓰면 야생으로 → 다시 외부 (도착 자리)
			useItem(ctx, sp, "invitation");

			// 방전환: 외부에는 방이 없음 → 그대로
			useItem(ctx, sp, "room_switch");
			check(ctx, "외부에서 방전환 → 그대로", "ruina:exterior");

			// 로비 (정문 걷기 TP 대신 같은 함수로)
			sp.getServer().runCommand("execute as @a run function ruina:tp/to/lobby_entrance");
			ctx.waitTicks(20);
			check(ctx, "로비", "ruina:lobby");
			render(sp);
			screenshot(ctx, sp, "lobby");
			double x0 = x(ctx);
			useItem(ctx, sp, "room_switch");
			expect("로비 방전환 → 홀 (x " + (int) x0 + " → " + (int) x(ctx) + ")", x(ctx) - x0 > 100);
			render(sp);
			screenshot(ctx, sp, "lobby_hall");

			// 세피라 10종: 그 층 전경 → 방전환 → 지정사서 방
			for (String[] f : FLOORS) {
				useItem(ctx, sp, f[0]);
				check(ctx, f[0] + " → " + f[2] + "의 층 전경", f[1]);
				render(sp);
				screenshot(ctx, sp, f[1].substring(6));
				double sx = x(ctx);
				useItem(ctx, sp, "room_switch");
				expect(f[2] + " 방전환 → 지정사서 방 (x " + (int) sx + " → " + (int) x(ctx) + ")", Math.abs(x(ctx) - sx) > 100);
				render(sp);
				screenshot(ctx, sp, f[1].substring(6) + "_room");
			}

			// 초대장: 도서관 안 → 기록한 자리 (야생)
			useItem(ctx, sp, "invitation");
			check(ctx, "초대장 → 처음 자리로", overworld);
		} catch (Throwable t) {
			fails++;
			log.add("❌ 예외: " + t);
			throw t;
		} finally {
			writeReport();
		}
		if (fails > 0) {
			throw new AssertionError("도서관 테스트 실패 " + fails + "건 (ruina_test.txt)");
		}
	}

	/**
	 * 외부 형체 (탑·가지·종이 물결·그린 하늘): 도착 시점 말고 다른 자리에서도 — 정문 앞 계단, 옆 광장, 뒤.
	 * 형체 블록·움직이는/그린 하늘 확인.
	 */
	private void exteriorViews(ClientGameTestContext ctx, TestSingleplayerContext sp) {
		expect("형체 블록 있음 (탑 기단)", ctx.computeOnClient(c -> {
			for (BlockPos p : BlockPos.betweenClosed(-6, 0, 40, 6, 20, 64)) {
				if (c.level.getBlockState(p).is(Forms.FORM)) {
					return true;
				}
			}
			return false;
		}));
		String[][] views = {
				{"14 0 82 160 -40", "exterior_gate"}, {"120 4.5 30 105 -25", "exterior_side"},
				{"-80 0 -95 -40 -40", "exterior_back"},
		};
		for (String[] v : views) {
			sp.getServer().runCommand("execute in ruina:exterior run tp @a " + v[0]);
			ctx.waitTicks(20);
			render(sp);
			ctx.waitTicks(30);
			screenshot(ctx, sp, v[1]);
		}
	}

	/** 작업 중 확인: 한 공간만 (외부는 초대장 도착 + 다른 시점, 로비·층은 전경과 방). */
	private void quick(ClientGameTestContext ctx, TestSingleplayerContext sp, String only) {
		useItem(ctx, sp, "invitation");
		check(ctx, "초대장 → 외부", "ruina:exterior");
		if (only.equals("exterior")) {
			render(sp);
			ctx.waitTicks(40);
			screenshot(ctx, sp, "exterior");
			exteriorViews(ctx, sp);
			return;
		}
		if (only.equals("lobby")) {
			sp.getServer().runCommand("execute as @a run function ruina:tp/to/lobby_entrance");
			ctx.waitTicks(20);
			render(sp);
			ctx.waitTicks(40);
			screenshot(ctx, sp, "lobby");
			useItem(ctx, sp, "room_switch");
			render(sp);
			ctx.waitTicks(40);
			screenshot(ctx, sp, "lobby_hall");
			return;
		}
		for (String[] f : FLOORS) {
			if (f[1].substring(6).equals(only)) {
				useItem(ctx, sp, f[0]);
				check(ctx, f[0] + " → " + f[2] + "의 층 전경", f[1]);
				render(sp);
				ctx.waitTicks(40);
				screenshot(ctx, sp, only);
				useItem(ctx, sp, "room_switch");
				render(sp);
				ctx.waitTicks(40);
				screenshot(ctx, sp, only + "_room");
			}
		}
	}

	/** 셰이더(BSL) 켠 상태로 몇 곳만: 외부·로비 홀·역사·총류 전경과 방·철학 (소프트웨어 GL 이라 느림). */
	private void shaderTour(ClientGameTestContext ctx, TestSingleplayerContext sp, String overworld) {
		useItem(ctx, sp, "invitation");
		check(ctx, "초대장 → 외부", "ruina:exterior");
		render(sp);
		screenshot(ctx, sp, "exterior");
		sp.getServer().runCommand("execute as @a run function ruina:tp/to/lobby_entrance");
		ctx.waitTicks(20);
		useItem(ctx, sp, "room_switch");
		render(sp);
		screenshot(ctx, sp, "lobby_hall");
		for (String[] f : new String[][] {FLOORS[0], FLOORS[7], FLOORS[9]}) {
			useItem(ctx, sp, f[0]);
			check(ctx, f[0] + " → " + f[2] + "의 층 전경", f[1]);
			render(sp);
			screenshot(ctx, sp, f[1].substring(6));
		}
		useItem(ctx, sp, "room_switch");
		render(sp);
		screenshot(ctx, sp, "general_room");
		useItem(ctx, sp, "invitation");
		check(ctx, "초대장 → 처음 자리로", overworld);
	}

	/** 아이템을 오른손에 들고 하늘을 보며 우클릭 (블록을 보면 블록 사용이 먼저라). 암전 이동이 끝날 때까지 기다림. */
	private void useItem(ClientGameTestContext ctx, TestSingleplayerContext sp, String id) {
		sp.getServer().runCommand("item replace entity @a weapon.mainhand with ruina:" + id);
		ctx.waitTicks(5);
		ctx.getInput().lookAt(ctx.computeOnClient(c -> c.player.getYRot()), -90f);
		ctx.waitTicks(2);
		press(ctx, o -> o.keyUse);
		ctx.waitTicks(70);
	}

	private void press(ClientGameTestContext ctx, Function<Options, KeyMapping> key) {
		ctx.getInput().pressKey(key);
	}

	private void render(TestSingleplayerContext sp) {
		try {
			// 형체가 많은 공간은 소프트웨어 GL 에서 청크 굽기가 느림 → 넉넉히 (작업 중 확인 모드는 2분)
			sp.getConnection().waitForChunksRender(true, System.getProperty("ruina.only") != null ? 20 * 120 : 20 * 45);
		} catch (Throwable t) {
			log.add("ℹ️ 청크 그리기 대기 시간 초과 (그대로 촬영)");
		}
	}

	private void screenshot(ClientGameTestContext ctx, TestSingleplayerContext sp, String name) {
		sp.getServer().runCommand("item replace entity @a weapon.mainhand with minecraft:air");   // 손에 아이템이 안 보이게
		// 도착 자리의 보는 방향 그대로 (원화 구도 비교용). 아이템을 쓰려고 하늘을 본 채면 수평으로
		if (ctx.computeOnClient(c -> c.player.getXRot()) < -80f) {
			ctx.getInput().lookAt(ctx.computeOnClient(c -> c.player.getYRot()), 0f);
		}
		ctx.waitTicks(5);
		shot++;
		ctx.runOnClient(c -> {    // 손·HUD 숨김 (F1)
			if (!c.gui.hud.isHidden()) {
				c.gui.hud.toggle();
			}
		});
		ctx.waitTicks(2);
		Path p = ctx.takeScreenshot(TestScreenshotOptions.of(String.format("%s%02d_%s", PREFIX, shot, name))
				.disableCounterPrefix());
		ctx.runOnClient(c -> {
			if (c.gui.hud.isHidden()) {
				c.gui.hud.toggle();
			}
		});
		log.add("📷 " + p.getFileName());
	}

	private static String dim(ClientGameTestContext ctx) {
		return ctx.computeOnClient(c -> c.level.dimension().identifier().toString());
	}

	private static double x(ClientGameTestContext ctx) {
		return ctx.computeOnClient(c -> c.player.getX());
	}

	private void check(ClientGameTestContext ctx, String what, String expectDim) {
		String got = dim(ctx);
		expect(what + " (" + got + ")", got.equals(expectDim));
	}

	private void expect(String what, boolean ok) {
		log.add((ok ? "✅ " : "❌ ") + what);
		if (!ok) {
			fails++;
		}
	}

	private void writeReport() {
		try {
			Files.write(FabricLoader.getInstance().getGameDir().resolve(SHADERS ? "ruina_test_bsl.txt" : "ruina_test.txt"), log);
		} catch (IOException ignored) {
			// 보고서는 참고용
		}
	}
}
