package ruina.library.test;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;

import net.fabricmc.loader.api.FabricLoader;
import net.fabricmc.loader.api.entrypoint.PreLaunchEntrypoint;

/**
 * 셰이더 확인 실행(-Pshaders)에서만: 맵 전용 BSL 을 shaderpacks 에 넣고 Iris 설정을 켬.
 * 게임 테스트는 시작할 때 실행 폴더를 비우므로 밖에서 미리 넣어 둘 수 없음 → Iris 가 설정을 읽기 전(preLaunch)에 여기서.
 * 경로는 build.gradle 이 -Druina.shaderpack 으로 넘김 (out/release/BSL_v10.1.6_Ruina.zip).
 */
public class ShaderSetup implements PreLaunchEntrypoint {
	@Override
	public void onPreLaunch() {
		String src = System.getProperty("ruina.shaderpack");
		if (src == null || !FabricLoader.getInstance().isModLoaded("iris")) {
			return;
		}
		Path game = FabricLoader.getInstance().getGameDir();
		Path pack = Path.of(src);
		try {
			Files.createDirectories(game.resolve("shaderpacks"));
			Files.copy(pack, game.resolve("shaderpacks").resolve(pack.getFileName()), StandardCopyOption.REPLACE_EXISTING);
			Files.createDirectories(game.resolve("config"));
			Files.writeString(game.resolve("config/iris.properties"),
					"enableShaders=true\nshaderPack=" + pack.getFileName() + "\ndisableUpdateMessage=true\n");
		} catch (IOException e) {
			throw new RuntimeException("셰이더 팩 준비 실패: " + src, e);
		}
	}
}
