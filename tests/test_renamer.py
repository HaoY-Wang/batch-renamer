from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))
from renamer import build_plan, execute_plan, find_files  # noqa: E402


class RenamerTests(unittest.TestCase):
    def test_plan_detects_existing_target(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            source = folder / "old.txt"
            source.touch()
            (folder / "new.txt").touch()
            plan = build_plan([source], "old", "new", "", "", False)
            self.assertEqual(plan[0].error, "目标文件已存在")

    def test_execute_handles_name_swap(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            first, second = folder / "a.txt", folder / "b.txt"
            first.write_text("A", encoding="utf-8")
            second.write_text("B", encoding="utf-8")
            from renamer import RenameItem
            count = execute_plan([RenameItem(first, second), RenameItem(second, first)], folder / "log.csv")
            self.assertEqual(count, 2)
            self.assertEqual(first.read_text(encoding="utf-8"), "B")
            self.assertEqual(second.read_text(encoding="utf-8"), "A")


if __name__ == "__main__":
    unittest.main()
