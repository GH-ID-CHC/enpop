"""EnPop - 全局英文翻译朗读工具主入口

架构：
- 主线程：tkinter root（隐藏）+ mainloop
- 后台线程：pystray 系统托盘
- 后台线程：pynput 全局热键监听

热键触发时，通过 root.after(0, ...) 在主线程安全显示浮窗。
"""

import os
import sys
import threading
import tkinter as tk

from src.config_manager import ConfigManager
from src.hotkey import HotkeyManager
from src.capturer import capture_selected_text
from src.translator import YoudaoTranslator
from src.tts import TTSPlayer
from src.popup import TranslationPopup
from src.tray import TrayApp
from src.constants import APP_NAME, APP_VERSION

# ---- 全局引用（供 tray 模块回调） ----
_hotkey_manager: HotkeyManager = None


def update_hotkey(new_hotkey: str):
    """更新全局热键（供 tray 设置菜单调用）"""
    global _hotkey_manager
    if _hotkey_manager:
        _hotkey_manager.update_hotkey(new_hotkey)


def _get_translator(config: ConfigManager) -> YoudaoTranslator:
    """创建翻译器，环境变量优先级高于配置文件"""
    app_key = os.environ.get("ENPOP_YOUDAO_APP_KEY") or config.get("youdao_app_key") or ""
    app_secret = os.environ.get("ENPOP_YOUDAO_APP_SECRET") or config.get("youdao_app_secret") or ""
    if not app_key or not app_secret:
        print("=" * 50)
        print("警告：未配置有道翻译 API Key")
        print("请在 config.json 中配置 youdao_app_key 和 youdao_app_secret")
        print("或设置环境变量 ENPOP_YOUDAO_APP_KEY / ENPOP_YOUDAO_APP_SECRET")
        print("=" * 50)
        return None
    return YoudaoTranslator(app_key, app_secret)


def main():
    global _hotkey_manager

    print(f"{APP_NAME} v{APP_VERSION} 启动中...")

    # 1. 加载配置
    config = ConfigManager()

    # 2. 初始化各模块
    tts_player = TTSPlayer(engine=config.get("tts_engine") or "edge")
    translator = _get_translator(config)
    popup = TranslationPopup(tts_callback=lambda text: tts_player.speak(text))

    # 3. 创建 tkinter root（隐藏）
    root = tk.Tk()
    root.withdraw()
    root.title(f"{APP_NAME} v{APP_VERSION}")
    TranslationPopup.set_root(root)

    # 热键触发标记（防重入）
    _translate_running = False

    def _schedule_popup(original: str, translation: str):
        """在主线程调度显示浮窗"""
        print("[EnPop] root.after 调度弹窗")
        root.after(0, lambda: popup.show(original, translation))

    def _do_translate():
        """热键触发：捕获 -> 翻译 -> 显示浮窗（在后台线程运行）"""
        nonlocal _translate_running
        if _translate_running:
            return
        _translate_running = True

        try:
            text = capture_selected_text()
            if not text:
                return

            en_chars = sum(1 for c in text if c.isascii() and c.isalpha())
            if en_chars / max(len(text), 1) < 0.5:
                return

            print(f"[EnPop] 原文: {text[:60]}{chr(46)*3 if len(text) > 60 else chr(46)*0}")

            if translator:
                try:
                    result = translator.translate(text)
                    if result.get("success"):
                        translation = result.get("translation", "")
                        print(f"[EnPop] 译文: {translation[:60]}{chr(46)*3 if len(translation) > 60 else chr(46)*0}")
                        _schedule_popup(text, translation)
                        return
                    else:
                        err = result.get("error_msg", "翻译失败")
                        print(f"[EnPop] {err}")
                        _schedule_popup(text, f"[翻译失败] {err}")
                        return
                except Exception as e:
                    print(f"[EnPop] 翻译异常: {e}")

            _schedule_popup(text, "（请配置有道 API Key 以启用翻译）")

        finally:
            _translate_running = False
    def _on_quit():
        """退出清理"""
        print("正在退出 EnPop...")
        _hotkey_manager.stop()
        popup.close()
        root.quit()
        os._exit(0)

    def _on_settings():
        """托盘菜单 -> 设置快捷键（在主线程调度对话框）"""
        import tkinter.simpledialog as simpledialog
        from threading import Event

        result = {}
        done_event = Event()

        def _show():
            key = simpledialog.askstring(
                "设置快捷键",
                "请输入新的快捷键组合\n例如: <ctrl>+<alt>+e\n"
                "支持修饰键: <ctrl>, <alt>, <shift>, <cmd>",
                parent=root,
                initialvalue=config.get("hotkey"),
            )
            result["key"] = key
            done_event.set()

        root.after(0, _show)
        done_event.wait()

        key = result.get("key")
        if key and key.strip():
            config.set("hotkey", key.strip())
            update_hotkey(key.strip())

    # 4. 启动热键监听（后台线程）
    _hotkey_manager = HotkeyManager(callback=_do_translate)
    _hotkey_manager.start(config.get("hotkey"))

    # 5. 启动系统托盘（后台线程）
    tray = TrayApp(config, _do_translate, _on_quit)
    tray._on_settings = _on_settings
    tray_thread = threading.Thread(target=tray.run, daemon=True)
    tray_thread.start()

    print(f"{APP_NAME} 已就绪 — 选中英文后按 {config.get('hotkey')} 翻译")

    # 6. 进入 tkinter 主循环（主线程）
    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("\n用户中断")
        _on_quit()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"程序异常: {e}")
        import traceback
        traceback.print_exc()
        input("按 Enter 退出...")
        sys.exit(1)

