# Quick Rename

一个仅支持 Windows 的轻量悬浮窗批量重命名器。把任何类型的文件直接拖进窗口，输入新名称，点击确认即可完成。文件始终保留在原本所在的文件夹中。

## 使用方式

1. 从 [Releases](../../releases) 下载 `Quick-Rename-Windows.exe`。
2. 按 `Ctrl + Alt + R` 呼出悬浮窗。
3. 在上方输入新的文件名；无需输入扩展名。
4. 将一个或多个文件拖放到区域，点击“确认修改”。

单个文件会改为 `新名称.原扩展名`。批量拖入文件时，程序会自动编号，例如 `新名称_001.jpg`、`新名称_002.pdf`。

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
