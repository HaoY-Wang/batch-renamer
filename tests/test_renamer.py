from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))
from renamer import RenameItem, build_drop_plan, execute_plan  # noqa: E402


class RenamerTests(unittest.TestCase):
    def test_plan_preserves_extensions_and_adds_numbers(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            first, second = folder / "old.txt", folder / "image.png"
            first.touch()
            second.touch()
            plan = build_drop_plan([first, second], "报告")
            self.assertEqual([item.target.name for item in plan], ["报告_001.txt", "报告_002.png"])
            self.assertEqual([item.target.parent for item in plan], [folder, folder])

    def test_execute_handles_name_swap(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            first, second = folder / "a.txt", folder / "b.txt"
            first.write_text("A", encoding="utf-8")
            second.write_text("B", encoding="utf-8")
            count = execute_plan([RenameItem(first, second), RenameItem(second, first)], folder / "log.csv")
            self.assertEqual(count, 2)
            self.assertEqual(first.read_text(encoding="utf-8"), "B")
            self.assertEqual(second.read_text(encoding="utf-8"), "A")
