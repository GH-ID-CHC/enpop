"""EnPop 全局热键管理"""

import threading
from pynput import keyboard


class HotkeyManager:
    """全局热键管理，在独立线程中运行 pynput 监听"""

    def __init__(self, callback):
        """
        Args:
            callback: 热键触发时回调函数
        """
        self._callback = callback
        self._current_hotkey = "<ctrl>+<alt>+e"  # 默认
        self._listener = None
        self._thread = None
        self._running = False

    def start(self, hotkey: str = None):
        """启动热键监听（在新的守护线程中运行）

        Args:
            hotkey: 热键字符串，如 "<ctrl>+<alt>+e"
        """
        if self._running:
            return

        if hotkey:
            self._current_hotkey = hotkey

        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        """热键监听循环（阻塞）"""
        try:
            hotkey_map = {self._current_hotkey: self._safe_callback}
            with keyboard.GlobalHotKeys(hotkey_map) as listener:
                self._listener = listener
                listener.join()
        except Exception as e:
            print(f"热键监听错误: {e}")
        finally:
            self._running = False

    def _safe_callback(self):
        """安全回调包装，捕获异常"""
        try:
            self._callback()
        except Exception as e:
            print(f"热键回调错误: {e}")

    def update_hotkey(self, new_hotkey: str):
        """运行时更新热键组合（需要重启监听）

        Args:
            new_hotkey: 新的热键字符串
        """
        self.stop()
        self.start(new_hotkey)

    def stop(self):
        """停止热键监听"""
        self._running = False
        if self._listener is not None:
            self._listener.stop()
            self._listener = None
        if self._thread is not None:
            self._thread = None

    @property
    def current_hotkey(self) -> str:
        return self._current_hotkey
