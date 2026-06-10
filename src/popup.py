"""EnPop 翻译结果气泡浮窗"""

import tkinter as tk
from typing import Optional

from src.constants import (
    POPUP_WIDTH,
    POPUP_BG_COLOR,
    POPUP_FG_COLOR,
    POPUP_ACCENT_COLOR,
    AUTO_CLOSE_MS,
)


_MIN_TEXT_HEIGHT = 2        # 最小显示行数
_MAX_TEXT_HEIGHT = 8        # 最大显示行数


class TranslationPopup:
    """翻译结果气泡浮窗，基于指定的 tkinter root 创建 Toplevel"""

    _root: Optional[tk.Tk] = None  # 共享的 tkinter 根窗口

    def __init__(self, tts_callback=None, tts_player=None):
        self._window: Optional[tk.Toplevel] = None
        self._tts_callback = tts_callback
        self._tts_player = tts_player
        self._speak_btn: Optional[tk.Button] = None
        self._close_timer_id: Optional[str] = None
        self._drag_start = None

    @classmethod
    def set_root(cls, root: tk.Tk):
        cls._root = root

    @staticmethod
    def _calc_text_height(text: str) -> int:
        """根据文本长度估算 Text widget 所需行数"""
        if not text:
            return _MIN_TEXT_HEIGHT
        # 估算每行可显示的字符数
        # POPUP_WIDTH 420px - frame padx 12*2 - text padx 6*2 = 384px
        # Segoe UI 11pt 英文字符约 7px，中文字符约 14px
        usable_width = POPUP_WIDTH - 36
        avg_char_width = 7.0
        chars_per_line = max(int(usable_width / avg_char_width), 15)
        raw_lines = text.split("\n")
        total_visual_lines = 0
        for line in raw_lines:
            if not line:
                total_visual_lines += 1
                continue
            line_len = len(line)
            needed = line_len // chars_per_line + (1 if line_len % chars_per_line > 0 else 0)
            total_visual_lines += max(1, needed)
        return max(_MIN_TEXT_HEIGHT, min(total_visual_lines, _MAX_TEXT_HEIGHT))

    def _create_text_widget(self, parent, text, fg_color, height):
        """创建只读文本区域"""
        widget = tk.Text(
            parent,
            wrap=tk.WORD,
            height=height,
            bg="#3A3A3A",
            fg=fg_color,
            font=("Segoe UI", 11),
            relief=tk.FLAT,
            padx=6,
            pady=4,
            borderwidth=0,
            highlightthickness=0,
        )
        widget.insert("1.0", text)
        widget.config(state=tk.DISABLED)
        return widget

    def show(self, original, translation, x=None, y=None):
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
            text="\u2716",
            bg=POPUP_BG_COLOR,
            fg="#AAAAAA",
            font=("Segoe UI", 10),
            cursor="hand2",
        )
        close_btn.pack(side=tk.RIGHT, padx=(5, 0))
        close_btn.bind("<Button-1>", lambda e: self.close())
        title_frame.bind("<Button-1>", self._start_drag)
        title_frame.bind("<B1-Motion>", self._do_drag)
        sep = tk.Frame(frame, bg="#444444", height=1)
        sep.pack(fill=tk.X, pady=(0, 8))
        # 计算动态高度
        orig_height = self._calc_text_height(original)
        trans_height = self._calc_text_height(translation)

        # 原文
        tk.Label(
            frame,
            text="原文:",
            bg=POPUP_BG_COLOR,
            fg="#888888",
            font=("Microsoft YaHei UI", 9),
            anchor="w",
        ).pack(fill=tk.X)
        original_text = self._create_text_widget(frame, original, POPUP_FG_COLOR, orig_height)
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
        translation_text = self._create_text_widget(frame, translation, POPUP_ACCENT_COLOR, trans_height)
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
        speak_btn.bind("<Button-1>", lambda e: self._on_speak(original))
        self._speak_btn = speak_btn
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

    def _start_drag(self, event):
        self._drag_start = (event.x_root, event.y_root)

    def _do_drag(self, event):
        if self._drag_start and self._window:
            dx = event.x_root - self._drag_start[0]
            dy = event.y_root - self._drag_start[1]
            x = self._window.winfo_x() + dx
            y = self._window.winfo_y() + dy
            self._window.geometry(f"+{x}+{y}")
            self._drag_start = (event.x_root, event.y_root)

    def _on_speak(self, text):
        if self._speak_btn:
            self._speak_btn.config(text="加载中...", state=tk.DISABLED)
        if self._tts_player:
            self._tts_player.speak(text, on_complete=self._on_tts_done)
        elif self._tts_callback:
            self._tts_callback(text)
        self._start_close_timer()

    def _on_tts_done(self):
        """TTS 完成回调（TTS 线程中调用，需切到主线程更新 UI）"""
        root = TranslationPopup._root
        if root:
            root.after(0, self._restore_speak_btn)

    def _restore_speak_btn(self):
        """恢复朗读按钮状态到正常"""
        if self._speak_btn:
            try:
                self._speak_btn.config(text="朗读原文", state=tk.NORMAL)
            except tk.TclError:
                self._speak_btn = None

    def close(self):
        self._cancel_close_timer()
        if self._window:
            try:
                self._window.destroy()
            except Exception:
                pass
            self._window = None
