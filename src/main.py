"""Always-on-top Windows drag-and-drop batch renamer."""

from __future__ import annotations

import ctypes
import ctypes.wintypes
import os
import threading
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

from tkinterdnd2 import DND_FILES, TkinterDnD

from renamer import build_plan, bulk_labels, execute_plan

WM_HOTKEY, MOD_ALT, MOD_CONTROL, VK_R, HOTKEY_ID = 0x0312, 0x0001, 0x0002, 0x52, 1


class FloatingRenamer(TkinterDnD.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Quick Rename")
        self.geometry("560x440")
        self.minsize(480, 360)
        self.attributes("-topmost", True)
        self.entries: list[dict] = []  # 每一项：{"source": Path, "label": str}
        self.base_name = tk.StringVar()
        self.status = tk.StringVar(value="把文件或文件夹拖到下方列表")
        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self.withdraw)
        threading.Thread(target=self._listen_for_hotkey, daemon=True).start()

    def _build_ui(self) -> None:
        container = ttk.Frame(self, padding=16)
        container.pack(fill="both", expand=True)

        ttk.Label(container, text="统一命名（可选）", font=("Microsoft YaHei UI", 10, "bold")).pack(anchor="w")
        top = ttk.Frame(container)
        top.pack(fill="x", pady=(6, 2))
        entry = ttk.Entry(top, textvariable=self.base_name, font=("Microsoft YaHei UI", 12))
        entry.pack(side="left", fill="x", expand=True)
        entry.bind("<Return>", self._on_entry_return)
        ttk.Button(top, text="应用到全部", command=self.apply_bulk).pack(side="left", padx=(6, 0))

        ttk.Label(
            container,
            text="把文件或文件夹拖到下方列表；双击某一行即可单独修改它的名称。",
            foreground="#666666",
        ).pack(anchor="w")

        columns = ("type", "source", "new")
        self.list = ttk.Treeview(container, columns=columns, show="headings", selectmode="browse")
        self.list.heading("type", text="类型")
        self.list.heading("source", text="原名称")
        self.list.heading("new", text="新名称")
        self.list.column("type", width=60, anchor="center", stretch=False)
        self.list.column("source", width=210)
        self.list.column("new", width=210)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=self.list.yview)
        self.list.configure(yscrollcommand=scrollbar.set)
        self.list.pack(side="left", fill="both", expand=True, pady=(8, 4))
        scrollbar.pack(side="right", fill="y", pady=(8, 4))
        self.list.drop_target_register(DND_FILES)
        self.list.dnd_bind("<<Drop>>", self.on_drop)
        self.list.bind("<Double-1>", lambda _event: self.edit_selected())

        footer = ttk.Frame(container)
        footer.pack(fill="x", pady=(4, 0))
        ttk.Label(footer, textvariable=self.status).pack(side="left", fill="x", expand=True)
        ttk.Button(footer, text="单独修改", command=self.edit_selected).pack(side="right", padx=(6, 0))
        ttk.Button(footer, text="清空", command=self.clear).pack(side="right")
        ttk.Button(footer, text="确认修改", command=self.rename).pack(side="right")

        self.bind("<Return>", lambda _event: self.rename())
        self.bind("<Escape>", lambda _event: self.withdraw())

    def _on_entry_return(self, _event: tk.Event) -> str:
        self.apply_bulk()
        return "break"

    def on_drop(self, event: tk.Event) -> None:
        paths = [Path(item) for item in self.tk.splitlist(event.data)]
        dropped = [path for path in paths if path.is_file() or path.is_dir()]
        if not dropped:
            self.status.set("没有接收到有效的文件或文件夹。")
            return
        base = self.base_name.get().strip()
        if base:
            labels = bulk_labels(dropped, base)
        else:
            labels = [self._default_label(path) for path in dropped]
        self.entries = [{"source": path, "label": label} for path, label in zip(dropped, labels)]
        self.refresh_list()
        self.status.set(f"已接收 {len(dropped)} 项；双击某行可单独修改名称。")

    @staticmethod
    def _default_label(path: Path) -> str:
        return path.name if path.is_dir() else path.stem

    def refresh_list(self) -> None:
        for item in self.list.get_children():
            self.list.delete(item)
        for entry in self.entries:
            source = entry["source"]
            is_dir = source.is_dir()
            kind = "文件夹" if is_dir else "文件"
            new_full = entry["label"] if is_dir else entry["label"] + source.suffix
            self.list.insert("", "end", values=(kind, source.name, new_full))

    def edit_selected(self) -> None:
        selection = self.list.selection()
        if not selection:
            messagebox.showinfo("未选择", "请先在列表中点击要单独修改的那一项。", parent=self)
            return
        index = self.list.index(selection[0])
        entry = self.entries[index]
        source = entry["source"]
        is_dir = source.is_dir()
        title = "修改文件夹名" if is_dir else "修改文件名"
        prompt = (
            "新的文件夹名（只改文件夹名字，不影响里面的内容）："
            if is_dir
            else "新的文件名（无需输入扩展名）："
        )
        value = simpledialog.askstring(title, prompt, initialvalue=entry["label"], parent=self)
        if value is None:
            return
        value = value.strip()
        if value:
            entry["label"] = value
            self.refresh_list()

    def apply_bulk(self) -> None:
        if not self.entries:
            messagebox.showwarning("还没有内容", "请先把文件或文件夹拖到窗口中。", parent=self)
            return
        base = self.base_name.get().strip()
        if not base:
            messagebox.showwarning("请输入名称", "请先在“统一命名”输入框里填写名称。", parent=self)
            return
        labels = bulk_labels([entry["source"] for entry in self.entries], base)
        for entry, label in zip(self.entries, labels):
            entry["label"] = label
        self.refresh_list()
        self.status.set(f"已按“{base}”批量编号 {len(self.entries)} 项；仍可双击单独调整。")

    def clear(self) -> None:
        self.entries = []
        self.base_name.set("")
        self.refresh_list()
        self.status.set("已清空。")

    def rename(self) -> None:
        if not self.entries:
            messagebox.showwarning("还没有内容", "请先把要修改的文件或文件夹拖到窗口中。", parent=self)
            return
        plan = build_plan([(entry["source"], entry["label"]) for entry in self.entries])
        errors = [item for item in plan if item.error]
        if errors:
            messagebox.showerror(
                "无法修改",
                "\n".join(f"{item.source.name}：{item.error}" for item in errors[:6]),
                parent=self,
            )
            return
        preview = "\n".join(f"{item.source.name}  →  {item.target.name}" for item in plan[:8])
        more = "\n…" if len(plan) > 8 else ""
        if not messagebox.askyesno("确认修改", f"以下 {len(plan)} 项将被重命名：\n\n{preview}{more}", parent=self):
            return
        try:
            app_data = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "QuickRename"
            app_data.mkdir(parents=True, exist_ok=True)
            changed = execute_plan(plan, app_data / "rename_log.csv")
        except (OSError, ValueError) as error:
            messagebox.showerror("修改失败", str(error), parent=self)
            return
        self.clear()
        self.status.set(f"已完成：{changed} 项已重命名。")

    def show_window(self) -> None:
        self.deiconify()
        self.lift()
        self.focus_force()
        self.base_name.set("")

    def _listen_for_hotkey(self) -> None:
        user32 = ctypes.windll.user32
        if not user32.RegisterHotKey(None, HOTKEY_ID, MOD_CONTROL | MOD_ALT, VK_R):
            self.after(0, lambda: self.status.set("全局快捷键注册失败；请从任务栏打开窗口。"))
            return
        message = ctypes.wintypes.MSG()
        while user32.GetMessageW(ctypes.byref(message), None, 0, 0) != 0:
            if message.message == WM_HOTKEY and message.wParam == HOTKEY_ID:
                self.after(0, self.show_window)


if __name__ == "__main__":
    FloatingRenamer().mainloop()
