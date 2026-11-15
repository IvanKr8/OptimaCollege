import io
import os
import tempfile
import unittest
from cli.parser import ArgParser
from main import build_application


class TestCLISystem(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.save_file = os.path.join(self.temp_dir.name, "test_save.json")
        self.stream = io.StringIO()
        self.cli, self.session = build_application(out_stream=self.stream, save_path=self.save_file)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_arg_parser(self):
        parser = ArgParser()
        args = parser.parse_args("heroes --detail 1")
        self.assertEqual(args.command, "heroes")
        self.assertEqual(args.options.get("detail"), "1")

    def test_character_selection_and_start(self):
        self.cli.exec_command("select 2")
        self.assertIsNotNone(self.session.player)
        self.assertEqual(self.session.player.name, "Еліна")

        self.cli.exec_command("start")
        self.assertTrue(self.session.is_active)
        self.assertEqual(self.session.turn, 1)

    def test_gameplay_loop_and_save_load(self):
        self.cli.exec_command("select 1")
        self.cli.exec_command("start")
        self.cli.exec_command("attack")
        self.assertGreater(self.session.score, 0)

        self.cli.exec_command("save")
        self.assertTrue(os.path.exists(self.save_file))

        saved_score = self.session.score
        self.session.score = 0
        self.cli.exec_command("load")
        self.assertEqual(self.session.score, saved_score)

    def test_unknown_command_and_exit(self):
        self.cli.exec_command("unknown_cmd")
        self.assertIn("Невідома команда", self.stream.getvalue())

        self.cli.exec_command("exit")
        self.assertFalse(self.cli.running)


if __name__ == "__main__":
    unittest.main()
