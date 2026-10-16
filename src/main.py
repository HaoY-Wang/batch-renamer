from __future__ import annotations

import sys
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from renamer import RenameItem, build_plan, execute_plan, find_files


class BatchRenamerApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Batch Renamer - 批量文件重命名器")
        self.geometry("980x650")
        self.minsize(760, 520)
        self.plan: list[RenameItem] = []
        self.folder = tk.StringVar()
        self.extensions = tk.StringVar()
        self.find_text = tk.StringVar()
        self.replace_text = tk.StringVar()
        self.prefix = tk.StringVar()
        self.suffix = tk.StringVar()
        self.recursive = tk.BooleanVar()
        self.numbering = tk.BooleanVar()
        self._build_ui()

    def _build_ui(self) -> None:
        form = ttk.Frame(self, padding=14)
        form.pack(fill="x")
        ttk.Label(form, text="文件夹").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Entry(form, textvariable=self.folder).grid(row=0, column=1, sticky="ew", pady=4)
        ttk.Button(form, text="选择…", command=self.choose_folder).grid(row=0, column=2, padx=(8, 0), pady=4)
        ttk.Label(form, text="扩展名筛选").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Entry(form, textvariable=self.extensions).grid(row=1, column=1, sticky="ew", pady=4)
        ttk.Label(form, text="例如 jpg,png；留空处理所有文件").grid(row=1, column=2, sticky="w", padx=(8, 0))
        ttk.Label(form, text="查找 / 替换").grid(row=2, column=0, sticky="w", padx=(0, 8), pady=4)
        pair = ttk.Frame(form)
        pair.grid(row=2, column=1, columnspan=2, sticky="ew", pady=4)
        ttk.Entry(pair, textvariable=self.find_text).pack(side="left", fill="x", expand=True)
        ttk.Label(pair, text="  →  ").pack(side="left")
        ttk.Entry(pair, textvariable=self.replace_text).pack(side="left", fill="x", expand=True)
        ttk.Label(form, text="前缀 / 后缀").grid(row=3, column=0, sticky="w", padx=(0, 8), pady=4)
        pair2 = ttk.Frame(form)
        pair2.grid(row=3, column=1, columnspan=2, sticky="ew", pady=4)
        ttk.Entry(pair2, textvariable=self.prefix).pack(side="left", fill="x", expand=True)
        ttk.Label(pair2, text="  /  ").pack(side="left")
        ttk.Entry(pair2, textvariable=self.suffix).pack(side="left", fill="x", expand=True)
        options = ttk.Frame(form)
        options.grid(row=4, column=1, columnspan=2, sticky="w", pady=(5, 0))
        ttk.Checkbutton(options, text="包含子文件夹", variable=self.recursive).pack(side="left", padx=(0, 16))
        ttk.Checkbutton(options, text="在文件名末尾添加序号", variable=self.numbering).pack(side="left")
        form.columnconfigure(1, weight=1)

        actions = ttk.Frame(self, padding=(14, 0, 14, 8))
        actions.pack(fill="x")
        ttk.Button(actions, text="生成预览", command=self.preview).pack(side="left")
        ttk.Button(actions, text="执行重命名", command=self.apply).pack(side="left", padx=8)
        self.status = ttk.Label(actions, text="请选择文件夹并生成预览。")
        self.status.pack(side="left", padx=8)

        frame = ttk.Frame(self, padding=(14, 0, 14, 14))
        frame.pack(fill="both", expand=True)
        self.table = ttk.Treeview(frame, columns=("old", "new", "status"), show="headings")
        for column, title, width in (("old", "原文件名", 330), ("new", "新文件名", 330), ("status", "状态", 180)):
            self.table.heading(column, text=title)
            self.table.column(column, width=width, anchor="w")
        scroll = ttk.Scrollbar(frame, orient="vertical", command=self.table.yview)
        self.table.configure(yscrollcommand=scroll.set)
        self.table.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

    def choose_folder(self) -> None:
        selected = filedialog.askdirectory(title="选择要处理的文件夹")
        if selected:
            self.folder.set(selected)

    def preview(self) -> None:
        folder = Path(self.folder.get())
        if not folder.is_dir():
            messagebox.showerror("无法预览", "请选择有效的文件夹。")
            return
        files = find_files(folder, self.extensions.get(), self.recursive.get())
        self.plan = build_plan(files, self.find_text.get(), self.replace_text.get(), self.prefix.get(), self.suffix.get(), self.numbering.get())
        self.table.delete(*self.table.get_children())
        errors = 0
        for item in self.plan:
            status = item.error or ("未变化" if item.source == item.target else "可重命名")
            errors += bool(item.error)
            self.table.insert("", "end", values=(item.source.name, item.target.name, status))
        self.status.config(text=f"找到 {len(files)} 个文件；{errors} 项存在问题。")

    def apply(self) -> None:
        if not self.plan:
            self.preview()
            if not self.plan:
                return
        errors = [item for item in self.plan if item.error]
        if errors:
            messagebox.showerror("无法执行", "预览中存在错误，请调整规则后重新生成预览。")
            return
        count = sum(item.source != item.target for item in self.plan)
        if not count:
            messagebox.showinfo("无需操作", "没有需要变更的文件名。")
            return
        if not messagebox.askyesno("确认重命名", f"将重命名 {count} 个文件。此操作会保存记录，确定继续吗？"):
            return
        try:
            log_path = Path(self.folder.get()) / "rename_log.csv"
            changed = execute_plan(self.plan, log_path)
        except (OSError, ValueError) as error:
            messagebox.showerror("执行失败", str(error))
            return
        self.status.config(text=f"已完成：重命名 {changed} 个文件。记录已保存到 rename_log.csv。")
        messagebox.showinfo("完成", f"已重命名 {changed} 个文件。\n记录：{log_path}")
        self.preview()


if __name__ == "__main__":
    app = BatchRenamerApp()
    app.mainloop()
