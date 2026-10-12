package ruina.library;

import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;

import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.item.CreativeModeTab;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;

import net.fabricmc.api.ModInitializer;
import net.fabricmc.fabric.api.creativetab.v1.FabricCreativeModeTab;
import net.fabricmc.fabric.api.entity.event.v1.ServerPlayerEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;

import ruina.library.form.Forms;

/**
 * 도서관 모드: 아이템(초대장·방전환·세피라 10종), 도서관 차원·건축물 설치, 이동.
 * 아이템 목록·도착 자리는 빌드 코드가 만든 /ruina/items.json (tools/mod_pack.py, 원본 config.MOD_ITEMS).
 * 차원·바이옴·이동 함수는 모드 데이터팩(data/ruina, 항상 켜짐), 건축물은 /ruina/world.zip (WorldInstaller).
 */
public class RuinaMod implements ModInitializer {
	public static final String MOD_ID = "ruina";
	public static final Logger LOGGER = LoggerFactory.getLogger(MOD_ID);

	/** 초대장 도착 자리 (데이터팩 ruina:tp/fade/&lt;spawn&gt;). */
	public static String spawnAnchor = "exterior_spawn";
	public static final List<Item> ITEMS = new ArrayList<>();

	public static Identifier id(String path) {
		return Identifier.fromNamespaceAndPath(MOD_ID, path);
	}

	@Override
	public void onInitialize() {
		JsonObject cfg = readConfig();
		spawnAnchor = cfg.get("spawn").getAsString();
		for (JsonElement e : cfg.getAsJsonArray("items")) {
			JsonObject o = e.getAsJsonObject();
			String id = o.get("id").getAsString();
			RuinaItem.Kind kind = RuinaItem.Kind.valueOf(o.get("kind").getAsString().toUpperCase());
			String anchor = o.has("anchor") ? o.get("anchor").getAsString() : null;
			ResourceKey<Item> key = ResourceKey.create(Registries.ITEM, id(id));
			Item item = new RuinaItem(new Item.Properties().setId(key).stacksTo(1), kind, anchor);
			Registry.register(BuiltInRegistries.ITEM, key, item);
			ITEMS.add(item);
		}

		// 크리에이티브 모드 탭에서만 (제작법·자동 지급 없음)
		ResourceKey<CreativeModeTab> tab = ResourceKey.create(Registries.CREATIVE_MODE_TAB, id("library"));
		Registry.register(BuiltInRegistries.CREATIVE_MODE_TAB, tab, FabricCreativeModeTab.builder()
				.title(Component.translatable("itemGroup.ruina.library"))
				.icon(() -> new ItemStack(ITEMS.getFirst()))
				.displayItems((context, entries) -> ITEMS.forEach(entries::accept))
				.build());

		Fx.init();
		Forms.init();
		ServerLifecycleEvents.SERVER_STARTING.register(WorldInstaller::install);
		ServerTickEvents.END_SERVER_TICK.register(Library::tick);
		ServerPlayerEvents.AFTER_RESPAWN.register(Library::afterRespawn);
		LOGGER.info("도서관 모드: 아이템 {}개", ITEMS.size());
	}

	private static JsonObject readConfig() {
		try (InputStream in = RuinaMod.class.getResourceAsStream("/ruina/items.json")) {
			if (in == null) {
				throw new IllegalStateException("/ruina/items.json 없음 (tools/mod_pack.py 로 만든 리소스가 빠짐)");
			}
			return JsonParser.parseReader(new InputStreamReader(in, StandardCharsets.UTF_8)).getAsJsonObject();
		} catch (IOException e) {
			throw new IllegalStateException("/ruina/items.json 읽기 실패", e);
		}
	}
}
