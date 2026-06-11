"""翻译结果缓存，相同文本不重复请求 API"""

import json
import threading
from pathlib import Path
from typing import Optional

from src.constants import APPDATA_CONFIG_DIR, DEV_MODE, APP_DIR


class TranslationCache:
    """翻译结果本地缓存，持久化到 JSON 文件

    缓存键基于原文（去除首尾空格 + 转小写）+ 源/目标语言。
    避免相同文本反复请求有道翻译 API，节约 API 额度并加快响应。
    """

    CACHE_FILENAME = "translation_cache.json"
    MAX_SIZE = 2000  # 最多缓存条目数，超出后裁剪一半

    def __init__(self):
        self._lock = threading.Lock()
        self._cache_path = self._find_cache_path()
        self._cache: dict[str, dict] = {}
        self._load()

    @staticmethod
    def _find_cache_path() -> Path:
        """与配置文件使用同一目录"""
        if DEV_MODE:
            return APPDATA_CONFIG_DIR / TranslationCache.CACHE_FILENAME
        # 打包模式：便携优先，其次 %APPDATA%
        local_path = APP_DIR / TranslationCache.CACHE_FILENAME
        if local_path.parent.exists():
            return local_path
        return APPDATA_CONFIG_DIR / TranslationCache.CACHE_FILENAME

    # ---- 公开接口 ----

    def get(self, text: str, from_lang: str = "en", to_lang: str = "zh-CHS") -> Optional[dict]:
        """获取缓存条目，未命中返回 None"""
        key = self._make_key(text, from_lang, to_lang)
        with self._lock:
            return self._cache.get(key)

    def set(self, text: str, from_lang: str, to_lang: str, result: dict):
        """存储翻译结果到缓存并持久化"""
        key = self._make_key(text, from_lang, to_lang)
        with self._lock:
            self._cache[key] = result
            self._trim()
        self._save()

    def clear(self):
        """清空所有缓存"""
        with self._lock:
            self._cache.clear()
        self._save()

    @property
    def size(self) -> int:
        """当前缓存条目数"""
        with self._lock:
            return len(self._cache)

    # ---- 内部方法 ----

    @staticmethod
    def _make_key(text: str, from_lang: str, to_lang: str) -> str:
        """生成缓存键：以语言对 + 规范化后的原文"""
        normalized = text.strip().lower()
        # 连续空白压缩为一个空格，避免微小排版差异
        normalized = " ".join(normalized.split())
        return f"{from_lang}:{to_lang}:{normalized}"

    def _trim(self):
        """超出 MAX_SIZE 时删除较早的一半"""
        if len(self._cache) <= self.MAX_SIZE:
            return
        # dict 在 Python 3.7+ 保持插入顺序，前面的是较早的条目
        keys_to_remove = list(self._cache.keys())[: self.MAX_SIZE // 2]
        for k in keys_to_remove:
            del self._cache[k]

    def _load(self):
        """从 JSON 文件加载缓存"""
        try:
            if self._cache_path.exists():
                with open(self._cache_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        self._cache = data
        except (json.JSONDecodeError, OSError):
            self._cache = {}

    def _save(self):
        """持久化缓存到 JSON 文件"""
        try:
            self._cache_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self._cache_path, "w", encoding="utf-8") as f:
                json.dump(self._cache, f, ensure_ascii=False, indent=2)
        except OSError as e:
            print(f"[EnPop] 保存翻译缓存失败: {e}")
