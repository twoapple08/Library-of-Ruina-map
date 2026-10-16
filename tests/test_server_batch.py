"""검사를 묶어도 명령별 성공/실패와 완료 순서를 잃지 않는다."""
import unittest

from tools.server import Server


class ServerBatchTest(unittest.TestCase):
    def make_server(self, missing=None):
        server = Server("/tmp/unused-ruina-server-test")
        sent = []

        def send(command):
            sent.append(command)
            if command.startswith("say "):
                marker = command[4:]
                if marker != missing:
                    server.lines.append(f"[12:00:00] [Server thread/INFO]: [Server] {marker}")
            else:
                result = "Test failed" if "bad" in command else "Test passed"
                server.lines.append(f"[12:00:00] [Server thread/INFO]: {result}")

        def wait(pattern, timeout):
            # 완료 대기는 모든 명령을 보낸 뒤 한 번만 한다.
            self.assertEqual(len(sent), server._mark * 2)
            return server.lines[-1]

        server.send = send
        server.wait_for = wait
        return server, sent

    def test_results_are_separate(self):
        server, sent = self.make_server()
        self.assertEqual(server.test_many(["good1", "bad", "good2"], batch_size=2), [True, False, True])
        self.assertEqual(len(sent), 6)

    def test_single_command_keeps_existing_interface(self):
        server, _ = self.make_server()
        self.assertTrue(server.test("good"))
        self.assertFalse(server.test("bad"))

    def test_missing_intermediate_marker_is_error(self):
        server, _ = self.make_server(missing="__ruina_mark_1__")
        with self.assertRaisesRegex(RuntimeError, "마커 순서"):
            server.run_many(["good", "bad"])


if __name__ == "__main__":
    unittest.main()
