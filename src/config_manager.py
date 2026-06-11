"""EnPop JSON 配置读写管理"""

import json
import sys
import os
from pathlib import Path
from src.constants import DEFAULT_CONFIG, APP_DIR, APPDATA_CONFIG_DIR, DEV_MODE


class ConfigManager:
    """配置文件管理，支持便携模式和安装模式"""

    CONFIG_FILENAME = "config.json"

    def __init__(self):
        self._config = dict(DEFAULT_CONFIG)
        self._config_path = self._find_config_path()
        self._load()

    def _find_config_path(self) -> Path:
        """按优先级查找配置文件路径"""
        if DEV_MODE:
            # 开发模式：始终使用 %APPDATA%/EnPop/ ，不暴露于项目目录
            appdata_path = APPDATA_CONFIG_DIR / self.CONFIG_FILENAME
            # 一次性迁移：如果旧版 config.json 在项目根目录，搬到 %APPDATA% 并删除
            old_path = APP_DIR / self.CONFIG_FILENAME
            if old_path.exists() and not appdata_path.exists():
                try:
                    appdata_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(old_path, "r", encoding="utf-8") as f_src:
                        data = f_src.read()
                    with open(appdata_path, "w", encoding="utf-8") as f_dst:
                        f_dst.write(data)
                    old_path.unlink()
                except OSError:
                    pass
            return appdata_path

        # 打包模式：便携优先，其次 %APPDATA%
        local_path = APP_DIR / self.CONFIG_FILENAME
        if local_path.exists():
            return local_path

        return APPDATA_CONFIG_DIR / self.CONFIG_FILENAME

    def _load(self):
        """从文件加载配置"""
        try:
            if self._config_path.exists():
                with open(self._config_path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    for k, v in DEFAULT_CONFIG.items():
                        if k in loaded:
                            self._config[k] = loaded[k]
        except (json.JSONDecodeError, OSError):
            pass  # 加载失败使用默认值

    def save(self):
        """保存配置到文件"""
        try:
            self._config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self._config_path, "w", encoding="utf-8") as f:
                json.dump(self._config, f, ensure_ascii=False, indent=2)
        except OSError as e:
            print(f"保存配置失败: {e}")

    def get(self, key: str):
        """获取配置项"""
        return self._config.get(key)

    def set(self, key: str, value):
        """设置配置项并保存"""
        self._config[key] = value
        self.save()

    def get_all(self) -> dict:
        """获取全部配置"""
        return dict(self._config)
