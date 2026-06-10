"""EnPop 有道翻译 API 配置对话框

功能：
- 首次启动时若未配置 API Key，自动弹出配置窗口
- 提供有道翻译 appKey / appSecret 的输入
- 给出有道智云注册地址的可点击链接
- 配置保存后立即生效
"""

import tkinter as tk
from tkinter import ttk
import webbrowser

from src.constants import APP_NAME

# 有道智云注册地址
YOUDAO_REGISTER_URL = "https://ai.youdao.com/#/register"


class ConfigDialog:
 """有道翻译 API 配置对话框，模态，居中显示"""

 @staticmethod
 def show(parent: tk.Tk, config_manager, on_save=None):
     """显示配置对话框（必须在 tkinter 主线程调用）

     Args:
         parent: tkinter 根窗口
         config_manager: ConfigManager 实例
         on_save: 保存成功后的回调（可选），参数为 (app_key, app_secret)
     """
     dialog = tk.Toplevel(parent)
     dialog.title(f"{APP_NAME} - API 配置")
     dialog.configure(bg="#2D2D2D")
     dialog.resizable(False, False)

     # 窗口尺寸
     win_w, win_h = 500, 380
 
     # 定位：优先居中屏幕，贴合鼠标位置避免覆盖任务栏
     try:
         screen_w = parent.winfo_screenwidth()
         screen_h = parent.winfo_screenheight()
         # 主屏幕居中
         pos_x = (screen_w - win_w) // 2
         pos_y = (screen_h - win_h) // 3  # 略偏上，视觉效果更好
     except Exception:
         pos_x, pos_y = 200, 200
 
     # 边界保护（适应多显示器、第二屏等场景）
     if pos_x < 20:
         pos_x = 20
     if pos_y < 20:
         pos_y = 20
 
     dialog.geometry(f"{win_w}x{win_h}+{pos_x}+{pos_y}")

     # ---- 拖拽支持 ----
     _drag_data = {"x": 0, "y": 0}
 
     def _start_drag(event):
         _drag_data["x"] = event.x_root
         _drag_data["y"] = event.y_root
 
     def _do_drag(event):
         dx = event.x_root - _drag_data["x"]
         dy = event.y_root - _drag_data["y"]
         x = dialog.winfo_x() + dx
         y = dialog.winfo_y() + dy
         dialog.geometry(f"+{x}+{y}")
         _drag_data["x"] = event.x_root
         _drag_data["y"] = event.y_root
 
     # 模态：禁止操作其他窗口
     dialog.grab_set()
     dialog.focus_set()

     # 主框架
     frame = tk.Frame(dialog, bg="#2D2D2D", padx=20, pady=18)
     frame.pack(fill=tk.BOTH, expand=True)

     # 标题
     title_label = tk.Label(
         frame,
         text="有道翻译 API 配置",
         bg="#2D2D2D", fg="#4FC3F7",
         font=("Microsoft YaHei UI", 13, "bold"),
         anchor="w",
     )
     title_label.pack(fill=tk.X, pady=(0, 6))
     title_label.bind("<Button-1>", _start_drag)
     title_label.bind("<B1-Motion>", _do_drag)
     frame.bind("<Button-1>", _start_drag)
     frame.bind("<B1-Motion>", _do_drag)

     # 说明文字
     tk.Label(
         frame,
         text="按 Ctrl+Alt+E 翻译前，请先配置有道翻译 API Key。",
         bg="#2D2D2D", fg="#CCCCCC",
         font=("Microsoft YaHei UI", 9),
         anchor="w", justify="left",
     ).pack(fill=tk.X, pady=(0, 4))

     # 注册链接（可点击）
     link_frame = tk.Frame(frame, bg="#2D2D2D")
     link_frame.pack(fill=tk.X, pady=(0, 12))
     tk.Label(
         link_frame, text="注册地址：",
         bg="#2D2D2D", fg="#CCCCCC",
         font=("Microsoft YaHei UI", 9),
     ).pack(side=tk.LEFT)
     link_label = tk.Label(
         link_frame, text=YOUDAO_REGISTER_URL,
         bg="#2D2D2D", fg="#4FC3F7",
         font=("Microsoft YaHei UI", 9, "underline"),
         cursor="hand2",
     )
     link_label.pack(side=tk.LEFT)
     link_label.bind("<Button-1>", lambda e: webbrowser.open(YOUDAO_REGISTER_URL))
     # 鼠标悬浮效果
     link_label.bind("<Enter>", lambda e: link_label.config(fg="#81D4FA"))
     link_label.bind("<Leave>", lambda e: link_label.config(fg="#4FC3F7"))

     # 分隔线
     tk.Frame(frame, bg="#444444", height=1).pack(fill=tk.X, pady=(0, 12))

     # 表单
     form = tk.Frame(frame, bg="#2D2D2D")
     form.pack(fill=tk.X)

     # AppKey 行
     tk.Label(
         form, text="AppKey：",
         bg="#2D2D2D", fg="#EEEEEE",
         font=("Microsoft YaHei UI", 10),
         anchor="e", width=12,
     ).grid(row=0, column=0, sticky="e", padx=(0, 8), pady=(0, 10))

     key_var = tk.StringVar(value=config_manager.get("youdao_app_key") or "")
     key_entry = tk.Entry(
         form, textvariable=key_var,
         bg="#3A3A3A", fg="#FFFFFF",
         font=("Consolas", 10),
         relief=tk.FLAT, bd=2,
         insertbackground="#FFFFFF",
         width=30,
     )
     key_entry.grid(row=0, column=1, sticky="ew", pady=(0, 10))
     key_entry.focus_set()

     # AppSecret 行
     tk.Label(
         form, text="AppSecret：",
         bg="#2D2D2D", fg="#EEEEEE",
         font=("Microsoft YaHei UI", 10),
         anchor="e", width=12,
     ).grid(row=1, column=0, sticky="e", padx=(0, 8), pady=(0, 14))

     secret_var = tk.StringVar(value=config_manager.get("youdao_app_secret") or "")
     secret_entry = tk.Entry(
         form, textvariable=secret_var,
         bg="#3A3A3A", fg="#FFFFFF",
         font=("Consolas", 10),
         show="*",
         relief=tk.FLAT, bd=2,
         insertbackground="#FFFFFF",
         width=30,
     )
     secret_entry.grid(row=1, column=1, sticky="ew", pady=(0, 14))

     form.columnconfigure(1, weight=1)

     # 错误提示（初始隐藏）
     error_label = tk.Label(
         frame, text="",
         bg="#2D2D2D", fg="#FF5252",
         font=("Microsoft YaHei UI", 9),
         anchor="w",
     )
     error_label.pack(fill=tk.X, pady=(0, 10))

     # 按钮行
     btn_frame = tk.Frame(frame, bg="#2D2D2D")
     btn_frame.pack(fill=tk.X, pady=(6, 0))

     cancelled = [False]  # 闭包可写标记

     def _on_save():
         key = key_var.get().strip()
         secret = secret_var.get().strip()
         if not key or not secret:
             error_label.config(text="请填写完整的 AppKey 和 AppSecret")
             return
         config_manager.set("youdao_app_key", key)
         config_manager.set("youdao_app_secret", secret)
         dialog.grab_release()
         dialog.destroy()
         if on_save:
             on_save(key, secret)

     def _on_cancel():
         cancelled[0] = True
         dialog.grab_release()
         dialog.destroy()

     def _on_close():
         _on_cancel()

     # 保存按钮
     save_btn = tk.Button(
         btn_frame, text="保存",
         bg="#4FC3F7", fg="#1A1A1A",
         activebackground="#39A9DB", activeforeground="#1A1A1A",
         font=("Microsoft YaHei UI", 10, "bold"),
         relief=tk.FLAT, padx=20, pady=4,
         cursor="hand2", borderwidth=0,
         command=_on_save,
     )
     save_btn.pack(side=tk.RIGHT, padx=(8, 0))

     # 取消按钮
     cancel_btn = tk.Button(
         btn_frame, text="稍后配置",
         bg="#444444", fg="#AAAAAA",
         activebackground="#555555", activeforeground="#CCCCCC",
         font=("Microsoft YaHei UI", 10),
         relief=tk.FLAT, padx=16, pady=4,
         cursor="hand2", borderwidth=0,
         command=_on_cancel,
     )
     cancel_btn.pack(side=tk.RIGHT)

     # 按 Enter 键触发保存
     dialog.bind("<Return>", lambda e: _on_save())
     dialog.bind("<Escape>", lambda e: _on_cancel())

     # 窗口关闭按钮也触发取消
     dialog.protocol("WM_DELETE_WINDOW", _on_close)
     dialog.wait_window()

     return not cancelled[0]
