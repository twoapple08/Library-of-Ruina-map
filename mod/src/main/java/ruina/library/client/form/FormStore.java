package ruina.library.client.form;

import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;

import net.minecraft.client.Minecraft;
import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.client.renderer.chunk.ChunkSectionLayer;
import net.minecraft.client.renderer.texture.TextureAtlasSprite;
import net.minecraft.core.BlockPos;
import net.minecraft.data.AtlasIds;
import net.minecraft.resources.Identifier;
import net.minecraft.server.packs.resources.Resource;

import ruina.library.RuinaMod;

/**
 * 형체 데이터 (모드 리소스 assets/ruina/forms/, tools/forms.py 가 만듦) 를 필요할 때 읽어 둠. 리소스 다시 읽기 때 비움.
 * 공간 = 지금 차원 id 의 경로 (ruina:exterior → exterior).
 */
public final class FormStore {
	private FormStore() {
	}

	/** 재질 (materials.json). sprite 는 아틀라스가 바뀌면 다시 찾음. */
	public static final class Mat {
		public final Identifier spriteId;
		public final ChunkSectionLayer layer;
		public final boolean emissive;
		public final boolean ao;
		public final boolean flat;
		volatile TextureAtlasSprite sprite;

		Mat(JsonObject o) {
			spriteId = Identifier.parse(o.get("sprite").getAsString());
			layer = switch (o.get("layer").getAsString()) {
				case "cutout" -> ChunkSectionLayer.CUTOUT;
				case "translucent" -> ChunkSectionLayer.TRANSLUCENT;
				default -> ChunkSectionLayer.SOLID;
			};
			emissive = o.get("emissive").getAsBoolean();
			ao = o.get("ao").getAsBoolean();
			flat = o.get("flat").getAsBoolean();
		}

		public TextureAtlasSprite sprite() {
			TextureAtlasSprite s = sprite;
			if (s == null) {
				s = Minecraft.getInstance().getAtlasManager().getAtlasOrThrow(AtlasIds.BLOCKS).getSprite(spriteId);
				sprite = s;
			}
			return s;
		}
	}

	/** 움직이는 형체 (movers.json 한 줄). */
	public record MoverSpec(String motion, float[] pivot, float[] axis, float period, float amp, float phase, float radius,
			FormData mesh) {
	}

	/** 종이 파티클 (emitters.json 한 줄). */
	public record EmitterSpec(double[] box, float rate, List<Identifier> sprites, float[] wind, float size, float life,
			float spin, float[] color, boolean glow) {
	}

	private static volatile List<Mat> materials;
	private static volatile Set<String> spaces;
	private static final Map<String, Optional<FormData>> REGIONS = new ConcurrentHashMap<>();
	private static final Map<String, Map<Long, MoverSpec>> MOVERS = new ConcurrentHashMap<>();
	private static final Map<String, List<EmitterSpec>> EMITTERS = new ConcurrentHashMap<>();
	private static final Map<String, Optional<FormData>> SKIES = new ConcurrentHashMap<>();

	public static void clear() {
		materials = null;
		spaces = null;
		REGIONS.clear();
		MOVERS.clear();
		EMITTERS.clear();
		SKIES.clear();
	}

	/** 지금 차원이 형체가 있는 도서관 공간이면 그 이름, 아니면 null. */
	public static String currentSpace() {
		ClientLevel level = Minecraft.getInstance().level;
		if (level == null) {
			return null;
		}
		Identifier id = level.dimension().identifier();
		if (!id.getNamespace().equals(RuinaMod.MOD_ID)) {
			return null;
		}
		return spaces().contains(id.getPath()) ? id.getPath() : null;
	}

	private static Set<String> spaces() {
		Set<String> s = spaces;
		if (s == null) {
			s = new HashSet<>();
			JsonElement e = json("forms/spaces.json");
			if (e != null) {
				for (JsonElement x : e.getAsJsonArray()) {
					s.add(x.getAsString());
				}
			}
			spaces = s;
		}
		return s;
	}

	public static Mat material(int i) {
		List<Mat> m = materials;
		if (m == null) {
			m = new ArrayList<>();
			JsonElement e = json("forms/materials.json");
			if (e != null) {
				for (JsonElement x : e.getAsJsonArray()) {
					m.add(new Mat(x.getAsJsonObject()));
				}
			}
			materials = m;
		}
		return i < m.size() ? m.get(i) : null;
	}

	/** 리전(512×512) 형체 파일. 없으면 null. */
	public static FormData region(String space, int rx, int rz) {
		return REGIONS.computeIfAbsent(space + "/r." + rx + "." + rz, k -> Optional.ofNullable(load("forms/" + k + ".bin")))
				.orElse(null);
	}

	/** 그린 하늘 (sky.bin, 카메라 기준 좌표). 없으면 null. */
	public static FormData sky(String space) {
		return SKIES.computeIfAbsent(space, k -> Optional.ofNullable(load("forms/" + k + "/sky.bin"))).orElse(null);
	}

	public static MoverSpec mover(String space, long posKey) {
		return MOVERS.computeIfAbsent(space, FormStore::loadMovers).get(posKey);
	}

	public static List<EmitterSpec> emitters(String space) {
		return EMITTERS.computeIfAbsent(space, FormStore::loadEmitters);
	}

	private static Map<Long, MoverSpec> loadMovers(String space) {
		Map<Long, MoverSpec> out = new HashMap<>();
		JsonElement e = json("forms/" + space + "/movers.json");
		if (e == null) {
			return out;
		}
		for (JsonElement x : e.getAsJsonArray()) {
			JsonObject o = x.getAsJsonObject();
			JsonArray p = o.getAsJsonArray("pos");
			FormData mesh = load("forms/" + space + "/" + o.get("mesh").getAsString() + ".bin");
			if (mesh == null) {
				continue;
			}
			out.put(BlockPos.asLong(p.get(0).getAsInt(), p.get(1).getAsInt(), p.get(2).getAsInt()),
					new MoverSpec(o.get("motion").getAsString(), floats(o.getAsJsonArray("pivot")), floats(o.getAsJsonArray("axis")),
							o.get("period").getAsFloat(), o.get("amp").getAsFloat(), o.get("phase").getAsFloat(),
							o.get("radius").getAsFloat(), mesh));
		}
		return out;
	}

	private static List<EmitterSpec> loadEmitters(String space) {
		List<EmitterSpec> out = new ArrayList<>();
		JsonElement e = json("forms/" + space + "/emitters.json");
		if (e == null) {
			return out;
		}
		for (JsonElement x : e.getAsJsonArray()) {
			JsonObject o = x.getAsJsonObject();
			JsonArray b = o.getAsJsonArray("box");
			double[] box = new double[6];
			for (int i = 0; i < 6; i++) {
				box[i] = b.get(i).getAsDouble();
			}
			List<Identifier> sprites = new ArrayList<>();
			for (JsonElement s : o.getAsJsonArray("sprites")) {
				sprites.add(Identifier.parse(s.getAsString()));
			}
			out.add(new EmitterSpec(box, o.get("rate").getAsFloat(), sprites, floats(o.getAsJsonArray("wind")),
					o.get("size").getAsFloat(), o.get("life").getAsFloat(), o.get("spin").getAsFloat(),
					floats(o.getAsJsonArray("color")), o.get("glow").getAsBoolean()));
		}
		return out;
	}

	private static float[] floats(JsonArray a) {
		float[] f = new float[a.size()];
		for (int i = 0; i < f.length; i++) {
			f[i] = a.get(i).getAsFloat();
		}
		return f;
	}

	private static FormData load(String path) {
		Optional<Resource> r = Minecraft.getInstance().getResourceManager().getResource(RuinaMod.id(path));
		if (r.isEmpty()) {
			return null;
		}
		try (InputStream in = r.get().open()) {
			return FormData.read(in.readAllBytes());
		} catch (IOException | RuntimeException ex) {
			RuinaMod.LOGGER.error("형체 파일 {} 읽기 실패", path, ex);
			return null;
		}
	}

	private static JsonElement json(String path) {
		Optional<Resource> r = Minecraft.getInstance().getResourceManager().getResource(RuinaMod.id(path));
		if (r.isEmpty()) {
			return null;
		}
		try (InputStream in = r.get().open()) {
			return JsonParser.parseReader(new InputStreamReader(in, StandardCharsets.UTF_8));
		} catch (IOException | RuntimeException ex) {
			RuinaMod.LOGGER.error("형체 설정 {} 읽기 실패", path, ex);
			return null;
		}
	}
}
