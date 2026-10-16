from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))
from renamer import RenameItem, build_plan, bulk_labels, execute_plan  # noqa: E402


class RenamerTests(unittest.TestCase):
    def test_bulk_labels_add_serial_numbers(self):
        self.assertEqual(
            bulk_labels([Path("a"), Path("b"), Path("c")], "报告"),
            ["报告_001", "报告_002", "报告_003"],
        )

    def test_plan_renames_files_individually_and_preserves_extensions(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            first, second = folder / "old.txt", folder / "image.png"
            first.touch()
            second.touch()
            plan = build_plan([(first, "报告"), (second, "封面")])
            self.assertEqual([item.target.name for item in plan], ["报告.txt", "封面.png"])
            self.assertEqual([item.target.parent for item in plan], [folder, folder])
            self.assertEqual([item.error for item in plan], ["", ""])

    def test_plan_empty_label_reports_error(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            target = folder / "a.txt"
            target.touch()
            plan = build_plan([(target, "   ")])
            self.assertEqual(plan[0].error, "名称不能为空")

    def test_plan_flags_duplicate_targets(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            first, second = folder / "a.txt", folder / "b.txt"
            first.touch()
            second.touch()
            plan = build_plan([(first, "same"), (second, "same")])
            self.assertEqual(
                [item.error for item in plan],
                ["与本次计划中的其他项目重名"] * 2,
            )

    def test_execute_renames_directory_without_touching_contents(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            sub = folder / "old_dir"
            sub.mkdir()
            (sub / "keep.txt").write_text("K", encoding="utf-8")
            plan = build_plan([(sub, "new_dir")])
            self.assertEqual(plan[0].target, folder / "new_dir")
            self.assertFalse(plan[0].error)
            count = execute_plan(plan, folder / "log.csv")
            self.assertEqual(count, 1)
            self.assertFalse(sub.exists())
            self.assertEqual(
                (folder / "new_dir" / "keep.txt").read_text(encoding="utf-8"),
                "K",
            )

    def test_execute_handles_name_swap(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            first, second = folder / "a.txt", folder / "b.txt"
            first.write_text("A", encoding="utf-8")
            second.write_text("B", encoding="utf-8")
            count = execute_plan(
                [RenameItem(first, second), RenameItem(second, first)],
                folder / "log.csv",
            )
            self.assertEqual(count, 2)
            self.assertEqual(first.read_text(encoding="utf-8"), "B")
            self.assertEqual(second.read_text(encoding="utf-8"), "A")


if __name__ == "__main__":
    unittest.main()
