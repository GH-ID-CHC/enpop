"""EnPop 常量与默认配置"""

import sys
import os
from pathlib import Path

# ----- 应用信息 -----
APP_NAME = "EnPop"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "EnPop - 全局英文翻译朗读工具"

# ----- 路径 -----
# 优先使用可执行文件同级目录（便携模式）
if getattr(sys, "frozen", False):
    APP_DIR = Path(sys.executable).parent
else:
    APP_DIR = Path(__file__).resolve().parent.parent

CONFIG_DIR = APP_DIR
APPDATA_CONFIG_DIR = Path(os.environ.get("APPDATA", "")) / APP_NAME

# ----- 默认配置 -----
DEFAULT_CONFIG = {
    "hotkey": "<ctrl>+<alt>+e",
    "tts_engine": "edge",          # "edge" | "sapi5"
    "auto_close_seconds": 5,
    "youdao_app_key": "",
    "youdao_app_secret": "",
    "start_on_boot": False,
}

# ----- 有道翻译 API -----
YOUDAO_API_URL = "https://openapi.youdao.com/api"
YOUDAO_SIGN_TYPE = "v3"

# ----- 热键 -----
VALID_MODIFIERS = {"<ctrl>", "<alt>", "<shift>", "<cmd>"}

# ----- 浮窗 -----
POPUP_WIDTH = 420
POPUP_MAX_HEIGHT = 300
POPUP_BG_COLOR = "#2D2D2D"
POPUP_FG_COLOR = "#FFFFFF"
POPUP_ACCENT_COLOR = "#4FC3F7"
AUTO_CLOSE_MS = 5000  # 5秒自动关闭

