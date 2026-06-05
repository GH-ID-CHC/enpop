"""EnPop 有道翻译 API 客户端"""

import hashlib
import time
import uuid
from typing import Optional

import requests

from src.constants import YOUDAO_API_URL, YOUDAO_SIGN_TYPE


class YoudaoTranslator:
    """有道云翻译 API 客户端
    API 文档：https://ai.youdao.com/DOCSIRMA/html/trans/api/wbfy/index.html
    """

    API_URL = YOUDAO_API_URL

    def __init__(self, app_key: str, app_secret: str):
        """
        Args:
            app_key: 有道智云应用的 appKey
            app_secret: 有道智云应用的 appSecret
        """
        if not app_key or not app_secret:
            raise ValueError("需要配置有道翻译 API 的 appKey 和 appSecret")
        self._app_key = app_key
        self._app_secret = app_secret

    def _truncate(self, text: str, max_len: int = 20) -> str:
        """截取文本用于签名，取前 max_len 个字符"""
        if len(text) <= max_len:
            return text
        return text[:max_len]

    def _generate_sign(self, text: str, salt: str, curtime: str) -> str:
        """生成签名
        sign = sha256(appKey + truncate(text) + salt + curtime + appSecret)
        """
        raw = self._app_key + self._truncate(text) + salt + curtime + self._app_secret
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def translate(self, text: str, from_lang: str = "en", to_lang: str = "zh-CHS") -> dict:
        """调用有道翻译 API

        Args:
            text: 待翻译文本
            from_lang: 源语言（auto 自动检测）
            to_lang: 目标语言（zh-CHS 简体中文）

        Returns:
            包含翻译结果的字典：
            {
                "success": bool,
                "query": str,              # 原文
                "translation": str,        # 翻译结果
                "phonetic": str or None,   # 音标（如果有）
                "error_code": str,         # 错误码，"0" 为成功
                "error_msg": str or None,  # 错误描述
            }
        """
        if not text or not text.strip():
            return {"success": False, "error_msg": "翻译文本为空"}

        salt = str(uuid.uuid4())
        curtime = str(int(time.time()))

        params = {
            "q": text,
            "from": from_lang,
            "to": to_lang,
            "appKey": self._app_key,
            "salt": salt,
            "sign": self._generate_sign(text, salt, curtime),
            "signType": YOUDAO_SIGN_TYPE,
            "curtime": curtime,
        }

        try:
            resp = requests.post(
                self.API_URL,
                data=params,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=10,
            )
            resp.raise_for_status()
            result = resp.json()
        except requests.RequestException as e:
            return {"success": False, "error_msg": f"API 请求失败: {e}"}
        except ValueError as e:
            return {"success": False, "error_msg": f"API 响应解析失败: {e}"}

        error_code = result.get("errorCode", "-1")

        # 成功响应
        if error_code == "0":
            translations = result.get("translation", [])
            basic = result.get("basic", {})
            return {
                "success": True,
                "query": result.get("query", text),
                "translation": translations[0] if translations else "",
                "phonetic": basic.get("phonetic"),
                "explains": basic.get("explains", []),
                "error_code": "0",
                "error_msg": None,
            }

        # 错误处理
        error_msgs = {
            "101": "缺少必填参数",
            "103": "appKey 无效，请检查有道翻译配置",
            "108": "签名错误",
            "113": "翻译文本超限",
            "105": "不支持的语言类型",
        "1203": "请求过于频繁，请稍后重试",
            "-1": "未知错误",
        }
        return {
            "success": False,
            "query": text,
            "translation": "",
            "error_code": error_code,
            "error_msg": error_msgs.get(error_code, f"API 错误码: {error_code}"),
        }

    @staticmethod
    def format_result(result: dict) -> str:
        """格式化翻译结果为可读文本"""
        if not result.get("success"):
            return f"[翻译失败] {result.get('error_msg', '未知错误')}"

        lines = [f"原文: {result.get('query', '')}"]
        phonetic = result.get("phonetic")
        if phonetic:
            lines.append(f"音标: [{phonetic}]")
        lines.append(f"译文: {result.get('translation', '')}")
        explains = result.get("explains", [])
        if explains:
            lines.append("---")
            lines.extend(f"  • {exp}" for exp in explains[:3])
        return "\n".join(lines)
