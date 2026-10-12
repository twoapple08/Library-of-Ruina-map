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
import ruina.library.form.MoverBlockEntity;

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

			// 초대장: 야생 → 외부
			useItem(ctx, sp, "invitation");
			check(ctx, "초대장 → 외부", "ruina:exterior");
			screenshot(ctx, sp, "exterior_title_card");   // 모드 이펙트: 도착 직후 층 이름 카드 '도서관'
			render(sp);
			screenshot(ctx, sp, "exterior");

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

			formShowcase(ctx, sp);

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
	 * 자유 형체 기반 시험대 (builders/form_showcase.py, 외부 구석 공중): 원화 투영 정면(원화와 같아야 함)과
	 * 옆 모습(입체 + 도는 톱니·흔들리는 추·빛나는 고리·날리는 종이·먼 산 띠).
	 */
	private void formShowcase(ClientGameTestContext ctx, TestSingleplayerContext sp) {
		sp.getServer().runCommand("execute in ruina:exterior run tp @a 700.5 500 721.5 180 0");
		ctx.waitTicks(20);
		render(sp);
		ctx.waitTicks(40);
		expect("형체 블록 있음 (시험대 바닥 앞)", ctx.computeOnClient(c -> {
			for (BlockPos p : BlockPos.betweenClosed(690, 499, 690, 710, 503, 718)) {
				if (c.level.getBlockState(p).is(Forms.FORM)) {
					return true;
				}
			}
			return false;
		}));
		screenshot(ctx, sp, "forms_art");
		sp.getServer().runCommand("execute in ruina:exterior run tp @a 733.5 506 706.5 120 8");
		ctx.waitTicks(20);
		render(sp);
		ctx.waitTicks(60);   // 톱니·추가 움직이고 종이가 날리게
		expect("움직이는 형체 블록 엔티티 있음", ctx.computeOnClient(c -> {
			for (BlockPos p : BlockPos.betweenClosed(730, 500, 690, 760, 525, 715)) {
				if (c.level.getBlockEntity(p) instanceof MoverBlockEntity) {
					return true;
				}
			}
			return false;
		}));
		screenshot(ctx, sp, "forms_3d");
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
		formShowcase(ctx, sp);
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
			sp.getConnection().waitForChunksRender(true, 20 * 30);
		} catch (Throwable t) {
			log.add("ℹ️ 청크 그리기 대기 시간 초과 (그대로 촬영)");
		}
	}

	private void screenshot(ClientGameTestContext ctx, TestSingleplayerContext sp, String name) {
		sp.getServer().runCommand("item replace entity @a weapon.mainhand with minecraft:air");   // 손에 아이템이 안 보이게
		// 도착 자리의 보는 방향 그대로 (원화 구도 비교용). 하늘을 본 채면 수평으로
		ctx.getInput().lookAt(ctx.computeOnClient(c -> c.player.getYRot()), 0f);
		ctx.waitTicks(5);
		shot++;
		Path p = ctx.takeScreenshot(TestScreenshotOptions.of(String.format("%s%02d_%s", PREFIX, shot, name)).withSize(1280, 720)
				.disableCounterPrefix());
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
