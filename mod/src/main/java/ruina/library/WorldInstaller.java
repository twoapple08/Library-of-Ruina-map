package ruina.library;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Comparator;
import java.util.HashSet;
import java.util.Set;
import java.util.stream.Stream;
import java.util.zip.ZipEntry;
import java.util.zip.ZipInputStream;

import net.minecraft.server.MinecraftServer;
import net.minecraft.world.level.storage.LevelResource;

/**
 * 건축물 설치: 월드를 열 때(차원을 불러오기 전) 모드 안의 /ruina/world.zip 을 월드 폴더 dimensions/ruina/ 로 복사.
 * 모드 빌드 번호(/ruina/world.id)가 바뀌면 도서관 차원(region·entities·poi)을 새 것으로 교체 (사용자 결정 2026-10-12).
 * 도서관 밖(오버월드 등)은 건드리지 않는다.
 */
public final class WorldInstaller {
	private WorldInstaller() {
	}

	private static final String MARKER = "ruina_build.txt";

	public static void install(MinecraftServer server) {
		String build = resourceText("/ruina/world.id");
		if (build == null) {
			RuinaMod.LOGGER.warn("도서관 건축물 없음 (/ruina/world.id) — 차원만 생김");
			return;
		}
		Path base = server.getWorldPath(LevelResource.ROOT).resolve("dimensions").resolve(RuinaMod.MOD_ID).normalize();
		Path marker = base.resolve(MARKER);
		try {
			if (Files.exists(marker) && Files.readString(marker).strip().equals(build)) {
				return;
			}
			long t0 = System.currentTimeMillis();
			int files = 0;
			Set<String> cleaned = new HashSet<>();
			try (InputStream raw = RuinaMod.class.getResourceAsStream("/ruina/world.zip")) {
				if (raw == null) {
					RuinaMod.LOGGER.warn("도서관 건축물 없음 (/ruina/world.zip)");
					return;
				}
				ZipInputStream zip = new ZipInputStream(raw);
				for (ZipEntry e; (e = zip.getNextEntry()) != null; ) {
					if (e.isDirectory()) {
						continue;
					}
					String name = e.getName();
					String dim = name.substring(0, name.indexOf('/'));
					if (cleaned.add(dim)) {
						for (String sub : new String[] {"region", "entities", "poi"}) {
							deleteTree(base.resolve(dim).resolve(sub));
						}
					}
					Path out = base.resolve(name).normalize();
					if (!out.startsWith(base)) {
						throw new IOException("잘못된 경로: " + name);
					}
					Files.createDirectories(out.getParent());
					Files.copy(zip, out);
					files++;
				}
			}
			Files.createDirectories(base);
			Files.writeString(marker, build + "\n");
			RuinaMod.LOGGER.info("도서관 건축물 설치: {}개 차원, 파일 {}개, {}ms (빌드 {})", cleaned.size(), files,
					System.currentTimeMillis() - t0, build);
		} catch (IOException e) {
			RuinaMod.LOGGER.error("도서관 건축물 설치 실패", e);
		}
	}

	private static void deleteTree(Path dir) throws IOException {
		if (!Files.exists(dir)) {
			return;
		}
		try (Stream<Path> walk = Files.walk(dir)) {
			for (Path p : walk.sorted(Comparator.reverseOrder()).toList()) {
				Files.delete(p);
			}
		}
	}

	private static String resourceText(String path) {
		try (InputStream in = RuinaMod.class.getResourceAsStream(path)) {
			if (in == null) {
				return null;
			}
			return new BufferedReader(new InputStreamReader(in, StandardCharsets.UTF_8)).readLine().strip();
		} catch (IOException e) {
			return null;
		}
	}
}
