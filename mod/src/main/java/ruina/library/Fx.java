package ruina.library;

import static net.minecraft.commands.Commands.argument;
import static net.minecraft.commands.Commands.literal;

import com.mojang.brigadier.arguments.StringArgumentType;
import com.mojang.brigadier.builder.LiteralArgumentBuilder;
import com.mojang.brigadier.context.CommandContext;

import net.minecraft.commands.CommandSourceStack;
import net.minecraft.server.level.ServerPlayer;

import net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback;
import net.fabricmc.fabric.api.networking.v1.PayloadTypeRegistry;
import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;

/** 화면 이펙트 보내기 + 데이터팩에서 쓰는 명령 `ruina fx <fade_in|fade_out|flash|title 글자>` (실행한 플레이어에게). */
public final class Fx {
	private Fx() {
	}

	static void init() {
		PayloadTypeRegistry.clientboundPlay().register(FxPayload.TYPE, FxPayload.CODEC);
		CommandRegistrationCallback.EVENT.register((dispatcher, buildContext, selection) -> {
			LiteralArgumentBuilder<CommandSourceStack> fx = literal("fx");
			for (String kind : new String[] {"fade_in", "fade_out", "flash"}) {
				fx.then(literal(kind).executes(ctx -> run(ctx, kind, "")));
			}
			fx.then(literal("title").then(argument("text", StringArgumentType.greedyString())
					.executes(ctx -> run(ctx, "title", StringArgumentType.getString(ctx, "text")))));
			dispatcher.register(literal(RuinaMod.MOD_ID).then(fx));
		});
	}

	private static int run(CommandContext<CommandSourceStack> ctx, String kind, String text) {
		ServerPlayer player = ctx.getSource().getPlayer();
		if (player == null) {
			return 0;   // 플레이어가 아니면 (검사용 마커 등) 무시
		}
		send(player, kind, text);
		return 1;
	}

	public static void send(ServerPlayer player, String kind, String text) {
		if (ServerPlayNetworking.canSend(player, FxPayload.TYPE)) {
			ServerPlayNetworking.send(player, new FxPayload(kind, text));
		}
	}
}
