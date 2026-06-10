# EnPop

> **English + Popup** — Windows 全局英文翻译朗读工具

在任何应用中选中英文文本，按快捷键即可弹出翻译浮窗，并支持即时朗读。

## 功能

- **全局热键**：在任何应用中选中文本，按 `Ctrl+Alt+E` 触发翻译
- **有道翻译**：调用有道云翻译 API 英译中
- **GUI 配置**：内置配置窗口，首次启动自动弹出，无需手动编辑配置文件
- **气泡浮窗**：贴近鼠标位置显示原文和译文，5秒自动消失
- **语音朗读**：支持 Edge TTS（在线）和 SAPI5（离线）两种引擎
- **系统托盘**：常驻托盘，右键菜单可配置 API Key、快捷键和切换引擎

## 安装

### 依赖

```bash
pip install -r requirements.txt
```

### 获取 API Key

1. 访问 [有道智云 AI 开放平台](https://ai.youdao.com) 注册账号
2. 在控制台创建应用，选择「文本翻译」服务
3. 获取 appKey 和 appSecret

### 运行

```bash
python src/main.py
```

首次运行会自动弹出 API Key 配置窗口，填入上一步获取的 appKey 和 appSecret 即可。

也随时可以通过系统托盘右键菜单 →「配置 API Key...」修改配置。

### 打包

```bash
pyinstaller --onefile --windowed `
  --icon assets\icon.ico `
  --name EnPop `
  --add-data "assets;assets" `
  src\main.py
```

打包产物：`dist/EnPop.exe`

## 用法

1. 运行 EnPop，系统托盘会出现蓝色 "En" 图标
2. 首次运行需配置有道翻译 API Key（会自动弹出配置窗口）
3. 在任意应用中选中英文文本
4. 按 `Ctrl+Alt+E`（默认快捷键）
5. 查看翻译浮窗，点击「朗读原文」收听发音
6. 浮窗 5 秒自动关闭，或按 Esc 立即关闭

## 项目结构

```
enpop/
├── src/
│   ├── main.py              # 程序入口
│   ├── hotkey.py             # 全局热键
│   ├── capturer.py           # 文本捕获
│   ├── translator.py         # 有道翻译 API
│   ├── tts.py                # 语音朗读
│   ├── popup.py              # 气泡浮窗
│   ├── tray.py               # 系统托盘
│   ├── config_dialog.py      # 配置对话框
│   ├── config_manager.py     # 配置管理
│   └── constants.py          # 常量定义
├── assets/                   # 图标资源
├── requirements.txt
├── build.spec
├── docs/
│   └── 开发文档.md
└── README.md
```

## 许可证

MIT
