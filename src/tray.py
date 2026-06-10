"""EnPop 系统托盘图标与菜单"""

import sys
import threading
from PIL import Image, ImageDraw, ImageFont

from src.constants import APP_NAME


def _create_default_icon(size: int = 64) -> Image.Image:
    """绘制默认托盘图标"""
    from pathlib import Path
    icon_path = Path(__file__).resolve().parent.parent / "assets" / "icon.png"
    if icon_path.exists():
        try:
            return Image.open(icon_path).resize((size, size), Image.LANCZOS)
        except Exception:
            pass

    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    radius = size // 5
    draw.rounded_rectangle(
        [(2, 2), (size - 2, size - 2)],
        radius=radius,
        fill=(79, 195, 247, 255),
    )

    try:
        font_size = size // 3
        try:
            font = ImageFont.truetype("segoeui.ttf", font_size)
        except Exception:
            try:
                font = ImageFont.truetype("arial.ttf", font_size)
            except Exception:
                font = ImageFont.load_default()
        bbox = draw.textbbox((0, 0), "En", font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        tx = (size - tw) // 2 - bbox[0]
        ty = (size - th) // 2 - bbox[1]
        draw.text((tx, ty), "En", fill="white", font=font)
    except Exception:
        draw.text((size // 4, size // 4), "En", fill="white")

    return img


class TrayApp:
    """系统托盘管理"""

    def __init__(self, config_manager, on_translate, on_quit):
        self._config = config_manager
        self._on_translate = on_translate
        self._on_quit = on_quit
        self._icon = None
        self._on_settings = None  # 由 main.py 注入，避免循环导入
        self._on_api_config = None  # 由 main.py 注入

    def run(self):
        """启动托盘图标（阻塞当前线程）"""
        import pystray
        from pystray import MenuItem as Item

        icon_image = _create_default_icon()

        self._icon = pystray.Icon(
            APP_NAME,
            icon_image,
            APP_NAME,
            menu=pystray.Menu(
                Item("翻译/朗读", self._on_translate, default=True),
                Item("设置快捷键...", self._on_settings_call),
                Item("配置 API Key...", self._on_api_config_call),
                Item("切换朗读引擎", self._create_engine_submenu()),
                pystray.Menu.SEPARATOR,
                Item("开机自启", self._on_toggle_autostart,
                     checked=lambda item: self._config.get("start_on_boot") or False),
                pystray.Menu.SEPARATOR,
                Item("退出", self._on_quit_action),
            ),
        )
        self._icon.run()

    def _on_settings_call(self):
        """调用外部注入的设置回调"""
        if self._on_settings:
            self._on_settings()
 
    def _on_api_config_call(self):
        """调用外部注入的 API 配置回调"""
        if self._on_api_config:
            self._on_api_config()

    def _create_engine_submenu(self):
        """创建引擎切换子菜单"""
        from pystray import Menu, MenuItem as Item

        def _set_edge():
            self._config.set("tts_engine", "edge")

        def _set_sapi5():
            self._config.set("tts_engine", "sapi5")

        return Menu(
            Item("Edge TTS (在线)", _set_edge,
                 checked=lambda item: self._config.get("tts_engine") == "edge"),
            Item("SAPI5 (离线)", _set_sapi5,
                 checked=lambda item: self._config.get("tts_engine") == "sapi5"),
        )

    def _on_toggle_autostart(self):
        """切换开机自启"""
        current = self._config.get("start_on_boot") or False
        self._config.set("start_on_boot", not current)
        self._set_autostart(not current)

    def _set_autostart(self, enable: bool):
        """通过 Windows 注册表设置开机自启"""
        import winreg
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0,
                                winreg.KEY_SET_VALUE | winreg.KEY_READ) as key:
                if enable:
                    if getattr(sys, "frozen", False):
                        exe = sys.executable
                    else:
                        exe = f'"{sys.executable}" -m src.main'
                    winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, exe)
                else:
                    try:
                        winreg.DeleteValue(key, APP_NAME)
                    except FileNotFoundError:
                        pass
        except Exception as e:
            print(f"设置开机自启失败: {e}")

    def _on_quit_action(self):
        if self._icon:
            self._icon.stop()
        if self._on_quit:
            self._on_quit()

    def stop(self):
        if self._icon:
            self._icon.stop()

