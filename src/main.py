"""Always-on-top Windows drag-and-drop batch renamer."""

from __future__ import annotations

import ctypes
import ctypes.wintypes
import os
import threading
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, ttk

from tkinterdnd2 import DND_FILES, TkinterDnD

from renamer import RenameItem, build_drop_plan, execute_plan

WM_HOTKEY, MOD_ALT, MOD_CONTROL, VK_R, HOTKEY_ID = 0x0312, 0x0001, 0x0002, 0x52, 1


class FloatingRenamer(TkinterDnD.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Quick Rename")
        self.geometry("440x300")
        self.minsize(400, 280)
        self.attributes("-topmost", True)
        self.files: list[Path] = []
        self.new_name = tk.StringVar()
        self.status = tk.StringVar(value="把一个或多个文件拖到下方区域")
        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self.withdraw)
        threading.Thread(target=self._listen_for_hotkey, daemon=True).start()

    def _build_ui(self) -> None:
        container = ttk.Frame(self, padding=16)
        container.pack(fill="both", expand=True)
        ttk.Label(container, text="新的文件名", font=("Microsoft YaHei UI", 10, "bold")).pack(anchor="w")
        entry = ttk.Entry(container, textvariable=self.new_name, font=("Microsoft YaHei UI", 12))
        entry.pack(fill="x", pady=(6, 10))
        entry.focus_set()
        ttk.Label(container, text="扩展名会自动保留；多个文件将自动添加编号。", foreground="#666666").pack(anchor="w")
        self.drop_zone = tk.Label(container, text="将文件拖放到这里\n支持任意文件类型", relief="groove", bd=2, bg="#f3f7ff", fg="#2456a6", font=("Microsoft YaHei UI", 12), padx=20, pady=28)
        self.drop_zone.pack(fill="both", expand=True, pady=12)
        self.drop_zone.drop_target_register(DND_FILES)
        self.drop_zone.dnd_bind("<<Drop>>", self.on_drop)
        footer = ttk.Frame(container)
        footer.pack(fill="x")
        ttk.Label(footer, textvariable=self.status).pack(side="left", fill="x", expand=True)
        ttk.Button(footer, text="清空", command=self.clear).pack(side="right", padx=(6, 0))
        ttk.Button(footer, text="确认修改", command=self.rename).pack(side="right")
        self.bind("<Return>", lambda _event: self.rename())
        self.bind("<Escape>", lambda _event: self.withdraw())

    def on_drop(self, event: tk.Event) -> None:
        paths = [Path(item) for item in self.tk.splitlist(event.data)]
        self.files = [path for path in paths if path.is_file()]
        count = len(self.files)
        self.drop_zone.config(text=f"已接收 {count} 个文件\n点击“确认修改”即可处理")
        self.status.set("文件会留在各自原本的文件夹中。")

    def clear(self) -> None:
        self.files = []
        self.drop_zone.config(text="将文件拖放到这里\n支持任意文件类型")
        self.status.set("已清空。")

    def rename(self) -> None:
        stem = self.new_name.get().strip()
        if not self.files:
            messagebox.showwarning("还没有文件", "请先把要修改的文件拖到窗口中。", parent=self)
            return
        if not stem:
            messagebox.showwarning("请输入名称", "请输入新的文件名（不需要输入扩展名）。", parent=self)
            return
        plan = build_drop_plan(self.files, stem)
        errors = [item for item in plan if item.error]
        if errors:
            messagebox.showerror("无法修改", "\n".join(f"{item.source.name}：{item.error}" for item in errors[:4]), parent=self)
            return
        preview = "\n".join(f"{item.source.name}  →  {item.target.name}" for item in plan[:5])
        more = "\n…" if len(plan) > 5 else ""
        if not messagebox.askyesno("确认修改", f"以下 {len(plan)} 个文件将被重命名：\n\n{preview}{more}", parent=self):
            return
        try:
            app_data = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "QuickRename"
            app_data.mkdir(parents=True, exist_ok=True)
            changed = execute_plan(plan, app_data / "rename_log.csv")
        except (OSError, ValueError) as error:
            messagebox.showerror("修改失败", str(error), parent=self)
            return
        self.clear()
        self.status.set(f"已完成：{changed} 个文件已在原路径重命名。")

    def show_window(self) -> None:
        self.deiconify()
        self.lift()
        self.focus_force()
        self.new_name.set("")

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
