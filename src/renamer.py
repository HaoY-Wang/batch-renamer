"""Safe filename planning and execution helpers."""

from __future__ import annotations

import csv
import os
import re
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

INVALID_WINDOWS_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
RESERVED_NAMES = {
    "CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))
}


@dataclass(frozen=True)
class RenameItem:
    source: Path
    target: Path
    error: str = ""


def find_files(folder: Path, extensions: str, include_subfolders: bool) -> list[Path]:
    wanted = {item.strip().lower().lstrip(".") for item in extensions.split(",") if item.strip()}
    candidates: Iterable[Path] = folder.rglob("*") if include_subfolders else folder.glob("*")
    return sorted(
        (path for path in candidates if path.is_file() and (not wanted or path.suffix.lower().lstrip(".") in wanted)),
        key=lambda path: str(path).lower(),
    )


def validate_filename(name: str) -> str:
    stem = Path(name).stem.rstrip(". ")
    if not stem:
        return "文件名不能为空"
    if INVALID_WINDOWS_CHARS.search(name):
        return "包含 Windows 不允许的字符"
    if name.endswith((".", " ")):
        return "文件名不能以句点或空格结尾"
    if stem.upper() in RESERVED_NAMES:
        return "使用了 Windows 保留名称"
    if len(name) > 255:
        return "文件名超过 255 个字符"
    return ""


def build_plan(
    files: list[Path], find_text: str, replace_text: str, prefix: str, suffix: str, numbering: bool
) -> list[RenameItem]:
    preliminary: list[RenameItem] = []
    width = max(3, len(str(len(files))))
    for number, source in enumerate(files, start=1):
        stem = source.stem.replace(find_text, replace_text) if find_text else source.stem
        if numbering:
            stem = f"{stem}_{number:0{width}d}"
        new_name = f"{prefix}{stem}{suffix}{source.suffix}"
        preliminary.append(RenameItem(source, source.with_name(new_name), validate_filename(new_name)))

    targets: dict[Path, int] = {}
    for item in preliminary:
        targets[item.target] = targets.get(item.target, 0) + 1

    planned_sources = {item.source for item in preliminary}
    result: list[RenameItem] = []
    for item in preliminary:
        error = item.error
        if not error and targets[item.target] > 1:
            error = "与本次计划中的其他文件重名"
        if not error and item.target.exists() and item.target not in planned_sources:
            error = "目标文件已存在"
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
