"""EnPop 文本捕获模块"""

import time
import pyperclip
import ctypes


def _simulate_ctrl_c():
    """模拟 Ctrl+C 按键

    关键是先释放 Alt（热键 Ctrl+Alt+X 中 Alt 可能还按着），
    再发 Ctrl+C，避免变成 Ctrl+Alt+C 导致复制失败。
    """
    VK_CONTROL = 0x11
    VK_ALT = 0x12
    VK_C = 0x43
    KEYEVENTF_KEYUP = 0x0002

    user32 = ctypes.windll.user32

    # 1) 释放 Alt（热键残留），避免 Ctrl+Alt+C
    user32.keybd_event(VK_ALT, 0, KEYEVENTF_KEYUP, 0)
    time.sleep(0.03)

    # 2) 重新按下 Ctrl 确保状态干净
    user32.keybd_event(VK_CONTROL, 0, 0, 0)
    time.sleep(0.01)

    # 3) 按下 C
    user32.keybd_event(VK_C, 0, 0, 0)
    time.sleep(0.05)

    # 4) 松开 C
    user32.keybd_event(VK_C, 0, KEYEVENTF_KEYUP, 0)
    time.sleep(0.01)

    # 5) 松开 Ctrl
    user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)
    time.sleep(0.08)


def capture_selected_text(max_retries: int = 3) -> str:
    """捕获当前应用中选中的文本。

    策略：保存剪贴板 -> 模拟 Ctrl+C -> 读剪贴板 -> 恢复剪贴板

    Args:
        max_retries: 最大重试次数

    Returns:
        选中文本，失败返回空字符串
    """
    # 保存当前剪贴板
    saved = ""
    try:
        saved = pyperclip.paste()
    except Exception:
        pass

    try:
        for attempt in range(max_retries):
            _simulate_ctrl_c()

            selected = pyperclip.paste()
            if selected and (not saved or selected != saved):
                text = selected.strip()
                if text:
                    return text

            time.sleep(0.05)

        return ""
    finally:
        # 延迟恢复剪贴板，给目标应用处理时间
        if saved:
            try:
                time.sleep(0.2)
                pyperclip.copy(saved)
            except Exception:
                pass
