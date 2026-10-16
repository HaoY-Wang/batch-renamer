"""Safe filename planning and execution helpers."""

from __future__ import annotations

import csv
import re
import uuid
from dataclasses import dataclass
from pathlib import Path

INVALID_WINDOWS_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
RESERVED_NAMES = {
    "CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))
}


@dataclass(frozen=True)
class RenameItem:
    source: Path
    target: Path
    error: str = ""


def validate_name(name: str, *, is_dir: bool = False) -> str:
    """Return an error string for an invalid name, or "" when acceptable.

    ``name`` is the complete target name: for a file it includes the
    extension, for a directory it is the full directory name.
    """
    if not name:
        return "名称不能为空"
    if INVALID_WINDOWS_CHARS.search(name):
        return "包含 Windows 不允许的字符"
    if name.endswith((".", " ")):
        return "名称不能以句点或空格结尾"
    if is_dir and name in {".", ".."}:
        return "不能使用 \".\" 或 \"..\" 作为文件夹名"
    if Path(name).stem.upper() in RESERVED_NAMES:
        return "使用了 Windows 保留名称"
    if len(name) > 255:
        return "名称超过 255 个字符"
    return ""


def bulk_labels(sources: list[Path], base: str) -> list[str]:
    """Numbered labels for a bulk rename (stems for files, names for dirs)."""
    width = max(3, len(str(len(sources))))
    labels: list[str] = []
    for number, _source in enumerate(sources, start=1):
        serial = f"_{number:0{width}d}" if len(sources) > 1 else ""
        labels.append(f"{base}{serial}")
    return labels


def build_plan(entries: list[tuple[Path, str]]) -> list[RenameItem]:
    """Plan a rename for every ``(source, label)`` pair.

    ``label`` is the new name without extension for a file, and the full new
    name for a directory. Directories are renamed as a whole; their contents
    are never touched.
    """
    preliminary: list[RenameItem] = []
    for source, raw_label in entries:
        label = raw_label.strip()
        if not label:
            preliminary.append(RenameItem(source, source, "名称不能为空"))
            continue
        if source.is_dir():
            target = source.with_name(label)
            error = validate_name(label, is_dir=True)
        else:
            full = label + source.suffix
            target = source.with_name(full)
            error = validate_name(full, is_dir=False)
        preliminary.append(RenameItem(source, target, error))

    targets: dict[Path, int] = {}
    for item in preliminary:
        targets[item.target] = targets.get(item.target, 0) + 1

    planned_sources = {item.source for item in preliminary}
    result: list[RenameItem] = []
    for item in preliminary:
        error = item.error
        if not error and targets[item.target] > 1:
            error = "与本次计划中的其他项目重名"
        if not error and item.target.exists() and item.target not in planned_sources:
            error = "目标已存在"
        result.append(RenameItem(item.source, item.target, error))
    return result


def execute_plan(plan: list[RenameItem], log_path: Path) -> int:
    actionable = [item for item in plan if not item.error and item.source != item.target]
    if not actionable:
        return 0
    if any(item.error for item in plan):
        raise ValueError("计划中存在错误，请先修正后再执行。")

    temporary: list[tuple[Path, Path, Path]] = []
    completed: list[tuple[Path, Path, Path]] = []
    try:
        for item in actionable:
            temp = item.source.with_name(f".__batch_rename_{uuid.uuid4().hex}__")
            item.source.rename(temp)
            temporary.append((item.source, temp, item.target))
        for source, temp, target in temporary:
            temp.rename(target)
            completed.append((source, temp, target))
    except OSError:
        # Best-effort recovery: restore completed targets and untouched temporary names.
        for source, _temp, target in reversed(completed):
            if target.exists() and not source.exists():
                target.rename(source)
        for source, temp, _target in reversed(temporary):
            if temp.exists() and not source.exists():
                temp.rename(source)
        raise

    new_file = not log_path.exists()
    with log_path.open("a", newline="", encoding="utf-8-sig") as output:
        writer = csv.writer(output)
        if new_file:
            writer.writerow(["原文件", "新文件"])
        writer.writerows([str(item.source), str(item.target)] for item in actionable)
    return len(actionable)
