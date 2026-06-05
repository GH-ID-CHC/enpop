"""EnPop 翻译结果气泡浮窗"""

import tkinter as tk
from typing import Optional

from src.constants import (
    POPUP_WIDTH,
    POPUP_MAX_HEIGHT,
    POPUP_BG_COLOR,
    POPUP_FG_COLOR,
    POPUP_ACCENT_COLOR,
    AUTO_CLOSE_MS,
)


class TranslationPopup:
    """翻译结果气泡浮窗，基于指定的 tkinter root 创建 Toplevel"""

    _root: Optional[tk.Tk] = None  # 共享的 tkinter 根窗口

    def __init__(self, tts_callback=None):
        self._window: Optional[tk.Toplevel] = None
        self._tts_callback = tts_callback
        self._close_timer_id: Optional[str] = None

    @classmethod
    def set_root(cls, root: tk.Tk):
        cls._root = root

    def show(self, original: str, translation: str, x: int = None, y: int = None):
        """在鼠标附近显示翻译浮窗（必须在 tkinter 主线程调用）"""
        self.close()

        if self._root is None:
            print("错误：未设置 tkinter root")
            return

        if x is None or y is None:
            try:
                x = self._root.winfo_pointerx()
                y = self._root.winfo_pointery()
            except Exception:
                x, y = 0, 0

        self._window = tk.Toplevel(self._root)
        self._window.title("EnPop 翻译")
        self._window.overrideredirect(True)
        self._window.attributes("-topmost", True)
        self._window.configure(bg=POPUP_BG_COLOR)

        # 主框架
        frame = tk.Frame(
            self._window,
            bg=POPUP_BG_COLOR,
            highlightbackground=POPUP_ACCENT_COLOR,
            highlightthickness=1,
            padx=12,
            pady=10,
        )
        frame.pack(fill=tk.BOTH, expand=True)

        # 标题行
        title_frame = tk.Frame(frame, bg=POPUP_BG_COLOR)
        title_frame.pack(fill=tk.X, pady=(0, 6))

        tk.Label(
            title_frame,
            text="EnPop 翻译",
            bg=POPUP_BG_COLOR,
            fg=POPUP_ACCENT_COLOR,
            font=("Microsoft YaHei UI", 10, "bold"),
        ).pack(side=tk.LEFT)

        close_btn = tk.Label(
            title_frame,
            text="✕",
            bg=POPUP_BG_COLOR,
            fg="#AAAAAA",
            font=("Segoe UI", 10),
            cursor="hand2",
        )
        close_btn.pack(side=tk.RIGHT, padx=(5, 0))
        close_btn.bind("<Button-1>", lambda e: self.close())

        # 分隔线
        sep = tk.Frame(frame, bg="#444444", height=1)
        sep.pack(fill=tk.X, pady=(0, 8))

        # 原文
        tk.Label(
            frame,
            text="原文:",
            bg=POPUP_BG_COLOR,
            fg="#888888",
            font=("Microsoft YaHei UI", 9),
            anchor="w",
        ).pack(fill=tk.X)

        original_text = tk.Text(
            frame,
            wrap=tk.WORD,
            height=2,
            bg="#3A3A3A",
            fg=POPUP_FG_COLOR,
            font=("Segoe UI", 11),
            relief=tk.FLAT,
            padx=6,
            pady=4,
            borderwidth=0,
            highlightthickness=0,
        )
        original_text.insert("1.0", original)
        original_text.config(state=tk.DISABLED)
        original_text.pack(fill=tk.X, pady=(2, 8))

        # 译文
        tk.Label(
            frame,
            text="译文:",
            bg=POPUP_BG_COLOR,
            fg="#888888",
            font=("Microsoft YaHei UI", 9),
            anchor="w",
        ).pack(fill=tk.X)

        translation_text = tk.Text(
            frame,
            wrap=tk.WORD,
            height=3,
            bg="#3A3A3A",
            fg=POPUP_ACCENT_COLOR,
            font=("Microsoft YaHei UI", 11),
            relief=tk.FLAT,
            padx=6,
            pady=4,
            borderwidth=0,
            highlightthickness=0,
        )
        translation_text.insert("1.0", translation)
        translation_text.config(state=tk.DISABLED)
        translation_text.pack(fill=tk.X, pady=(2, 10))

        # 按钮行
        btn_frame = tk.Frame(frame, bg=POPUP_BG_COLOR)
        btn_frame.pack(fill=tk.X)

        speak_btn = tk.Button(
            btn_frame,
            text="朗读原文",
            bg="#555555",
            fg=POPUP_FG_COLOR,
            activebackground="#666666",
            activeforeground=POPUP_FG_COLOR,
            relief=tk.FLAT,
            padx=10,
            pady=2,
            cursor="hand2",
            font=("Microsoft YaHei UI", 9),
            borderwidth=0,
        )
        speak_btn.pack(side=tk.LEFT, padx=(0, 6))
        speak_btn.bind(
            "<Button-1>",
            lambda e: self._on_speak(original) if self._tts_callback else None,
        )

        dismiss_btn = tk.Button(
            btn_frame,
            text="关闭 (Esc)",
            bg="#444444",
            fg="#AAAAAA",
            activebackground="#555555",
            activeforeground=POPUP_FG_COLOR,
            relief=tk.FLAT,
            padx=10,
            pady=2,
            cursor="hand2",
            font=("Microsoft YaHei UI", 9),
            borderwidth=0,
        )
        dismiss_btn.pack(side=tk.RIGHT)
        dismiss_btn.bind("<Button-1>", lambda e: self.close())

        self._window.update_idletasks()

        # 位置：鼠标光标右下方
        offset_x, offset_y = 20, 20
        win_w = self._window.winfo_reqwidth()
        win_h = self._window.winfo_reqheight()
        screen_w = self._window.winfo_screenwidth()
        screen_h = self._window.winfo_screenheight()

        pos_x = min(x + offset_x, screen_w - win_w - 10)
        pos_y = min(y + offset_y, screen_h - win_h - 10)
        pos_x = max(10, pos_x)
        pos_y = max(10, pos_y)

        self._window.geometry(f"+{pos_x}+{pos_y}")

        self._window.bind("<Escape>", lambda e: self.close())
        self._start_close_timer()

    def _start_close_timer(self):
        self._cancel_close_timer()
        self._close_timer_id = self._window.after(AUTO_CLOSE_MS, self.close)

    def _cancel_close_timer(self):
        if self._close_timer_id and self._window:
            try:
                self._window.after_cancel(self._close_timer_id)
            except Exception:
                pass
            self._close_timer_id = None

    def _on_speak(self, text: str):
        if self._tts_callback:
            self._tts_callback(text)
        self._start_close_timer()

    def close(self):
        self._cancel_close_timer()
        if self._window:
            try:
                self._window.destroy()
            except Exception:
                pass
            self._window = None
