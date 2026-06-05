"""EnPop TTS 朗读引擎封装"""

import asyncio
import os
import tempfile
import threading
from typing import Optional


class TTSPlayer:
    """语音朗读引擎封装，支持 edge-tts（在线）和 pyttsx3（离线）"""

    def __init__(self, engine: str = "edge"):
        """
        Args:
            engine: "edge"（在线自然语音）或 "sapi5"（离线降级）
        """
        self._engine_name = engine
        self._speaking = False
        self._stop_flag = False
        self._loop = None
        self._loop_lock = threading.Lock()
        self._warmed_up = False

    def speak(self, text: str, on_complete=None):
        print(f"[EnPop TTS] speak() text={text[:30]}")
        """异步朗读文本（不阻塞调用方）

        Args:
            text: 要朗读的文本
            on_complete: 朗读完成後回调
        """
        if not text or self._speaking:
            return

        self._stop_flag = False
        self._speaking = True
        thread = threading.Thread(target=self._speak_sync, args=(text, on_complete), daemon=True)
        thread.start()

    def _speak_sync(self, text: str, on_complete=None):
        """在内部线程中执行朗读"""
        try:
            if self._engine_name == "edge":
                self._speak_edge(text)
            else:
                self._speak_sapi5(text)
        except Exception as e:
            print(f"[EnPop TTS] 朗读失败: {e}")
        finally:
            self._speaking = False
            self._stop_flag = False
            if on_complete:
                try:
                    on_complete()
                except Exception:
                    pass

    def prewarm(self):
        """在后台预热 edge-tts 模块和连接，减少首次朗读延迟"""
        if self._engine_name != "edge":
            print("[EnPop TTS] 非 edge 引擎，跳过预热")
            return
        threading.Thread(target=self._do_prewarm, daemon=True).start()

    def _do_prewarm(self):
        """预热：导入模块 + 初始化事件循环 + 建立 SSL 连接"""
        print("[EnPop TTS] 开始预热...")
        tmp = None
        try:
            import edge_tts  # noqa: F401
            loop = self._get_or_create_loop()
            try:
                import tempfile
                with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                    tmp = f.name
                loop.run_until_complete(
                    asyncio.wait_for(
                        edge_tts.Communicate(
                            "Hello",
                            voice="en-US-JennyNeural",
                        ).save(tmp),
                        timeout=5.0
                    )
                )
            except Exception as e:
                print(f"[EnPop TTS] 预热请求未完成（非致命）: {e}")
            finally:
                if tmp and tmp and os.path.exists(tmp):
                    try:
                        os.unlink(tmp)
                    except Exception:
                        pass

            try:
                import pythoncom
                pythoncom.CoInitialize()
                pythoncom.CoUninitialize()
            except ImportError:
                pass

            self._warmed_up = True
            print("[EnPop TTS] 预热完成")
        except Exception as e:
            print(f"[EnPop TTS] 预热失败（非致命）: {e}")

    def _get_or_create_loop(self):
        """获取或创建可复用的事件循环"""
        with self._loop_lock:
            if self._loop is None or self._loop.is_closed():
                self._loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self._loop)
            return self._loop

    def _speak_edge(self, text: str):
        print("[EnPop TTS] 使用 edge-tts 引擎")
        """使用 edge-tts 生成音频并通过 Windows Media Player 播放"""
        tmp_path = None
        try:
            # 1. 使用 edge-tts 生成 MP3 音频文件
            import edge_tts

            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                tmp_path = f.name

            loop = self._get_or_create_loop()
            loop.run_until_complete(
                edge_tts.Communicate(
                    text,
                    voice="en-US-JennyNeural",
                ).save(tmp_path)
            )

            if self._stop_flag:
                return

            # 2. 使用 Windows Media Player COM 播放（后台播放，无可见窗口）
            self._play_mp3_wmp(tmp_path)

        except ImportError:
            print("edge-tts 未安装，降级到 sapi5")
            self._speak_sapi5(text)
        except Exception as e:
            print(f"[EnPop TTS] Edge TTS 播放失败: {e}")
            print("[EnPop TTS] 降级到 SAPI5")
            self._speak_sapi5(text)
        finally:
            # 3. 清理临时文件
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass

    def _play_mp3_wmp(self, mp3_path: str):
        """使用 Windows Media Player COM 对象播放 MP3（静默播放）"""
        try:
            import pythoncom
            import win32com.client

            pythoncom.CoInitialize()
            wmp = win32com.client.Dispatch("WMPlayer.OCX")
            wmp.settings.volume = 100

            # 添加媒体并播放
            item = wmp.newMedia(mp3_path)
            wmp.currentPlaylist.clear()
            wmp.currentPlaylist.appendItem(item)
            wmp.controls.play()
            print("[EnPop TTS] WMP 开始播放")

            # playState经常返回9(转换中)而不是3(播放中)
            # 所以不用 ==3 判断，改为等待直到结束或超时
            import time
            timeout = 30.0
            while timeout > 0:
                if self._stop_flag:
                    wmp.controls.stop()
                    break
                state = wmp.playState
                if state in (1, 8):  # 1=停止, 8=已结束
                    break
                pythoncom.PumpWaitingMessages()
                time.sleep(0.1)
                timeout -= 0.1

            print("[EnPop TTS] WMP 播放完成")
            pythoncom.CoUninitialize()
        except ImportError:
            # pywin32 未安装，回退到 PowerShell MediaPlayer
            self._play_mp3_fallback(mp3_path)
        except Exception as e:
            print(f"WMP 播放失败: {e}")
            self._play_mp3_fallback(mp3_path)

    def _play_mp3_fallback(self, mp3_path: str):
        """回退方案：使用 PowerShell 播放 MP3"""
        import subprocess
        try:
            proc = subprocess.Popen(
                [
                    "powershell", "-NoProfile", "-Command",
                    f"$wm = New-Object -ComObject WMPlayer.OCX; "
                    f"$wm.URL = '{mp3_path}'; "
                    f"$wm.controls.play(); "
                    f"while ($wm.playState -eq 3) {{ Start-Sleep -Milliseconds 100 }}"
                ],
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            proc.wait()
        except Exception as e:
            print(f"PowerShell 播放失败: {e}")

    def _speak_sapi5(self, text: str):
        print("[EnPop TTS] 使用 SAPI5 引擎")
        """使用 pyttsx3（SAPI5）离线朗读"""
        try:
            import pyttsx3
            engine = pyttsx3.init()
            # 选择英文语音
            voices = engine.getProperty("voices")
            en_voice = None
            for v in voices:
                if "english" in v.name.lower() or "en" in v.id.lower():
                    en_voice = v.id
                    break
            if en_voice:
                engine.setProperty("voice", en_voice)
            engine.setProperty("rate", 150)
            engine.say(text)
            engine.runAndWait()
            engine.stop()
        except Exception as e:
            print(f"SAPI5 朗读失败: {e}")

    def stop(self):
        """停止朗读"""
        self._stop_flag = True
        self._speaking = False

    @property
    def is_speaking(self) -> bool:
        return self._speaking

    @property
    def engine_name(self) -> str:
        return self._engine_name

    @engine_name.setter
    def engine_name(self, name: str):
        self._engine_name = name
