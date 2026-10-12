package ruina.library;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.UUID;

import com.mojang.serialization.Codec;

import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerPlayer;

import net.fabricmc.fabric.api.attachment.v1.AttachmentRegistry;
import net.fabricmc.fabric.api.attachment.v1.AttachmentType;

/**
 * 아이템 동작. 도서관 안의 이동은 모드 데이터팩 함수(검증된 암전 TP·방전환)를 플레이어로 실행한다.
 * <ul>
 * <li>초대장: 야생 → 외부 (쓰기 전 자리 기록) / 도서관 안 어디서든 → 기록한 자리 (없으면 월드 스폰)</li>
 * <li>방전환: 로비 방↔홀, 각 층 지정사서 방↔전경 (번쩍임, 바로) — ruina:mod/room</li>
 * <li>세피라: 그 층 전경으로 (암흑 1초 → 이동 → 1초 뒤 풀림) — ruina:tp/fade/&lt;층&gt;_entrance. 야생에서 쓰면 자리 기록</li>
 * </ul>
 */
public final class Library {
	private Library() {
	}

	/** 도서관에 들어오기 전 자리 "차원 x y z yaw pitch" (월드에 저장, 죽어도 유지). */
	public static final AttachmentType<String> RETURN_POINT = AttachmentRegistry.create(RuinaMod.id("return_point"),
			builder -> builder.persistent(Codec.STRING).copyOnDeath());

	private static final int FADE_IN = 20;     // 암흑 1초 → 이동
	private static final int FADE_OUT = 40;    // 도착지에서 1초 뒤 풀림
	private static final Map<UUID, Integer> lastUse = new HashMap<>();
	private static final List<Fade> fades = new ArrayList<>();

	private record Fade(UUID player, String tp, int start) {
	}

	public static boolean inLibrary(ServerPlayer player) {
		return player.level().dimension().identifier().getNamespace().equals(RuinaMod.MOD_ID);
	}

	static void use(ServerPlayer player, RuinaItem.Kind kind, String anchor) {
		MinecraftServer server = player.level().getServer();
		int now = server.getTickCount();
		Integer last = lastUse.get(player.getUUID());
		if (last != null && now - last < 10) {
			return;   // 한 번 누름에 한 번만
		}
		lastUse.put(player.getUUID(), now);
		if (isFading(player)) {
			return;
		}
		switch (kind) {
			case INVITATION -> {
				if (inLibrary(player)) {
					goBack(server, player);
				} else {
					remember(player);
					runAs(server, player, "execute unless entity @s[tag=ruina.fading] run function ruina:tp/fade/" + RuinaMod.spawnAnchor);
				}
			}
			case ROOM -> {
				if (inLibrary(player)) {
					runAs(server, player, "execute unless entity @s[tag=ruina.fading] run function ruina:mod/room");
				} else {
					actionbar(server, player, "도서관 안에서만 쓸 수 있어요 (초대장으로 들어가세요)");
				}
			}
			case SEPHIRAH -> {
				if (!inLibrary(player)) {
					remember(player);
				}
				runAs(server, player, "execute unless entity @s[tag=ruina.fading] run function ruina:tp/fade/" + anchor);
			}
			default -> {
			}
		}
	}

	private static void remember(ServerPlayer player) {
		String point = String.format(Locale.ROOT, "%s %.3f %.3f %.3f %.2f %.2f",
				player.level().dimension().identifier(), player.getX(), player.getY(), player.getZ(),
				player.getYRot(), player.getXRot());
		player.setAttached(RETURN_POINT, point);
	}

	/** 기록한 자리로 (없으면 월드 스폰). 암흑 1초 → 이동 → 1초 뒤 풀림. */
	private static void goBack(MinecraftServer server, ServerPlayer player) {
		String point = player.getAttached(RETURN_POINT);
		String tp;
		if (point != null) {
			String[] p = point.split(" ");
			tp = "execute in " + p[0] + " run tp @s " + p[1] + " " + p[2] + " " + p[3] + " " + p[4] + " " + p[5];
			player.removeAttached(RETURN_POINT);
		} else {
			var spawn = server.overworld().getRespawnData();
			tp = "execute in " + spawn.dimension().identifier() + " run tp @s " + (spawn.pos().getX() + 0.5) + " "
					+ spawn.pos().getY() + " " + (spawn.pos().getZ() + 0.5);
		}
		runAs(server, player, "tag @s add ruina.fading");
		runAs(server, player, "effect give @s minecraft:darkness 3 0 true");
		fades.add(new Fade(player.getUUID(), tp, server.getTickCount()));
	}

	static void tick(MinecraftServer server) {
		int now = server.getTickCount();
		for (Iterator<Fade> it = fades.iterator(); it.hasNext(); ) {
			Fade f = it.next();
			ServerPlayer player = server.getPlayerList().getPlayer(f.player());
			if (player == null) {
				it.remove();
				continue;
			}
			int t = now - f.start();
			if (t == FADE_IN) {
				runAs(server, player, f.tp());
				runAs(server, player, "playsound minecraft:item.book.page_turn master @s ~ ~ ~ 1 0.8");
			} else if (t >= FADE_OUT) {
				runAs(server, player, "effect clear @s minecraft:darkness");
				runAs(server, player, "tag @s remove ruina.fading");
				it.remove();
			}
		}
	}

	/** 도서관 안에서 죽으면 다시 살아난 뒤 도서관 스폰 자리로 (보는 방향 포함). */
	static void afterRespawn(ServerPlayer oldPlayer, ServerPlayer newPlayer, boolean alive) {
		if (alive || !inLibrary(oldPlayer)) {
			return;
		}
		MinecraftServer server = newPlayer.level().getServer();
		runAs(server, newPlayer, "tag @s remove ruina.fading");
		runAs(server, newPlayer, "effect clear @s minecraft:darkness");
		runAs(server, newPlayer, "function ruina:tp/to/" + RuinaMod.spawnAnchor);
	}

	private static boolean isFading(ServerPlayer player) {
		for (Fade f : fades) {
			if (f.player().equals(player.getUUID())) {
				return true;
			}
		}
		return false;
	}

	private static void actionbar(MinecraftServer server, ServerPlayer player, String text) {
		runAs(server, player, "title @s actionbar {\"text\":\"" + text + "\",\"color\":\"#ecd6a6\"}");
	}

	/** 명령을 그 플레이어로(as, at) 실행 (서버 권한, 출력 숨김). */
	static void runAs(MinecraftServer server, ServerPlayer player, String command) {
		server.getCommands().performPrefixedCommand(server.createCommandSourceStack().withSuppressedOutput(),
				"execute as " + player.getUUID() + " at @s run " + command);
	}
}
