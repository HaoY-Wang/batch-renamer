# Quick Rename

一个仅支持 Windows 的轻量悬浮窗批量重命名器。把文件或文件夹直接拖进窗口，可以点选某一项单独改名，也可以统一命名；文件始终保留在原本所在的文件夹中，文件夹只改名字、不动里面的内容。

## 使用方式

1. 从 [Releases](../../releases) 下载 `Quick-Rename-Windows.exe`。
2. 按 `Ctrl + Alt + R` 呼出悬浮窗。
3. 将一个或多个文件、文件夹拖到列表区域。
4. **单独修改**：在列表中双击某一行（或选中后点“单独修改”），为该文件或文件夹单独输入新名字。文件无需输入扩展名，扩展名会自动保留；文件夹只重命名它本身，不会改动里面的任何内容。
5. **统一命名**（可选）：在上方填写名称并点击“应用到全部”，会按顺序编号，例如 `新名称_001.jpg`、`新名称_002.pdf`。
6. 点击“确认修改”完成。

## 本地运行和打包

```powershell
python -m pip install -r requirements.txt pyinstaller
python src/main.py
pyinstaller --noconfirm --onefile --windowed --collect-all tkinterdnd2 --name Quick-Rename src/main.py
```

## 发布

推送形如 `v1.0.0` 的 Git 标签。GitHub Actions 会构建 Windows `.exe` 并创建对应的 Release。

## License

[MIT](LICENSE)
