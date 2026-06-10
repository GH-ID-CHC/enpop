"""EnPop 文本捕获模块"""

import time
import pyperclip
import ctypes


def _simulate_ctrl_c():
    """模拟 Ctrl+C 按键

    使用 keybd_event API：
    1. 释放 Alt（热键 Ctrl+Alt+E 中 Alt 可能还按着），避免 Ctrl+Alt+C
    2. 按下 Ctrl（用户可能已松开热键，确保 Ctrl 处于按下状态）
    3. 按下并释放 C
    4. 释放 Ctrl
    """
    VK_ALT = 0x12
    VK_CONTROL = 0x11
    VK_C = 0x43
    KEYEVENTF_KEYUP = 0x0002

    user32 = ctypes.windll.user32

    # 1) 释放 Alt（热键残留），避免 Ctrl+Alt+C
    user32.keybd_event(VK_ALT, 0, KEYEVENTF_KEYUP, 0)
    time.sleep(0.03)

    # 2) 按下 Ctrl（确保 Ctrl 按下，用户可能已松开热键）
    user32.keybd_event(VK_CONTROL, 0, 0, 0)
    time.sleep(0.01)

    # 3) 按下 C
    user32.keybd_event(VK_C, 0, 0, 0)
    time.sleep(0.05)

    # 4) 释放 C
    user32.keybd_event(VK_C, 0, KEYEVENTF_KEYUP, 0)
    time.sleep(0.01)

    # 5) 释放 Ctrl
    user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)

    # 6) 等待剪贴板更新：短文本快速，长文本需要更多时间
    time.sleep(0.15)


def _wait_for_new_clipboard(saved, max_wait_ms=1000):
    """等待剪贴板中出现新内容（轮询方式，自适应等待时间）

    Args:
        saved: 之前保存的剪贴板内容，用于判断是否有变化
        max_wait_ms: 最大等待时间（毫秒）

    Returns:
        新剪贴板文本，超时返回空字符串
    """
    waited = 0
    step_ms = 50
    while waited < max_wait_ms:
        time.sleep(step_ms / 1000.0)
        waited += step_ms
        try:
            selected = pyperclip.paste()
            if selected and (not saved or selected != saved):
                text = selected.strip()
                if text:
                    return text
        except Exception:
            pass
    return ""


def capture_selected_text(max_retries=3):
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

            # 先用固定延时快速尝试
            try:
                selected = pyperclip.paste()
                if selected and (not saved or selected != saved):
                    text = selected.strip()
                    if text:
                        return text
            except Exception:
                pass

            # 然后轮询等待（覆盖长文本场景）
            text = _wait_for_new_clipboard(saved, max_wait_ms=500)
            if text:
                return text

            # 重试前短暂避让
            time.sleep(0.05)

        return ""
    finally:
        # 延迟恢复剪贴板，给目标应用处理时间
        if saved:
            try:
                time.sleep(0.3)
                pyperclip.copy(saved)
            except Exception:
                pass
