"""Minimal WeChat test-account API client and callback helpers."""

from hashlib import sha1
import json
from time import monotonic
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from xml.etree import ElementTree

from app.core.config import get_settings


class WeChatError(RuntimeError):
    pass


class WeChatClient:
    def __init__(self) -> None:
        self._token: str | None = None
        self._token_expires_at = 0.0

    def access_token(self) -> str:
        settings = get_settings()
        if self._token and monotonic() < self._token_expires_at:
            return self._token
        if not settings.wechat_app_id or not settings.wechat_app_secret:
            raise WeChatError("WeChat credentials are not configured")
        query = urlencode({"grant_type": "client_credential", "appid": settings.wechat_app_id, "secret": settings.wechat_app_secret})
        payload = self._request_json(f"https://api.weixin.qq.com/cgi-bin/token?{query}")
        if "access_token" not in payload:
            raise WeChatError(str(payload.get("errmsg", "access token request failed")))
        self._token = str(payload["access_token"])
        self._token_expires_at = monotonic() + int(payload.get("expires_in", 7200)) - 60
        return self._token

    def send_template(self, *, open_id: str, title: str, url: str) -> str:
        settings = get_settings()
        if not settings.wechat_template_id:
            raise WeChatError("WECHAT_TEMPLATE_ID is not configured")
        payload = {
            "touser": open_id,
            "template_id": settings.wechat_template_id,
            "url": url,
            "data": {"first": {"value": title}, "remark": {"value": "点击查看详情"}},
        }
        result = self._request_json(f"https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={self.access_token()}", payload)
        if result.get("errcode", 0) != 0:
            raise WeChatError(str(result.get("errmsg", "template send failed")))
        return str(result.get("msgid", ""))

    @staticmethod
    def _request_json(url: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        request = Request(url, data=json.dumps(payload).encode() if payload else None, headers={"Content-Type": "application/json"} if payload else {})
        with urlopen(request, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))


def valid_signature(*, token: str, timestamp: str, nonce: str, signature: str) -> bool:
    return sha1("".join(sorted((token, timestamp, nonce))).encode()).hexdigest() == signature


def parse_message(body: bytes) -> dict[str, str]:
    root = ElementTree.fromstring(body)
    return {child.tag: child.text or "" for child in root}


def xml_reply(*, open_id: str, account_id: str, content: str) -> str:
    return f"<xml><ToUserName><![CDATA[{open_id}]]></ToUserName><FromUserName><![CDATA[{account_id}]]></FromUserName><CreateTime>0</CreateTime><MsgType><![CDATA[text]]></MsgType><Content><![CDATA[{content}]]></Content></xml>"
