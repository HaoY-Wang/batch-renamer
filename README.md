# Batch Renamer

一个仅支持 Windows 的桌面批量文件重命名器。下载发布页中的 `.exe` 后即可使用，不需要安装 Python。

## 功能

- 选择文件夹，可选是否包含子文件夹
- 按扩展名筛选文件，例如 `jpg,png,pdf`
- 查找替换、添加前缀和后缀、追加编号
- 执行前预览全部变更
- 检查重复文件名、非法 Windows 文件名和已有文件冲突
- 每次操作会在选定文件夹保存 `rename_log.csv`

## 使用

1. 在 [Releases](../../releases) 下载 `Batch-Renamer-Windows.exe`。
2. 打开程序并选择文件夹。
3. 设置规则，点击“生成预览”。
4. 检查状态列没有错误后，点击“执行重命名”。

> 请先在一份副本上试用。程序不会处理文件内容，但重命名仍可能影响其他软件中的文件引用。

## 本地运行和打包

需要 Windows 和 Python 3.11 或更新版本。

```powershell
python src/main.py
python -m pip install pyinstaller
pyinstaller --noconfirm --onefile --windowed --name Batch-Renamer src/main.py
```

生成的文件位于 `dist/Batch-Renamer.exe`。

## 发布新版本

推送形如 `v1.0.0` 的 Git 标签。GitHub Actions 会构建 Windows `.exe` 并创建对应的 Release。

```powershell
git tag v1.0.0
git push origin v1.0.0
```

## License

[MIT](LICENSE)
