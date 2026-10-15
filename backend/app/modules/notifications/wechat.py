"""Minimal WeChat test-account API client and callback helpers."""

from hashlib import sha1
import json
from time import monotonic, time
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from xml.etree import ElementTree

from app.core.config import get_settings
from app.core.errors import AppError


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

    def send_template(self, *, open_id: str, summary: str, happened_at: str) -> str:
        settings = get_settings()
        if not settings.wechat_template_id:
            raise WeChatError("WECHAT_TEMPLATE_ID is not configured")
        payload = {
            "touser": open_id,
            "template_id": settings.wechat_template_id,
            "data": {
                "keyword1": {"value": summary},
                "keyword2": {"value": happened_at},
            },
        }
        result = self._request_json(f"https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={self.access_token()}", payload)
        if result.get("errcode", 0) != 0:
            self._token = None
            self._token_expires_at = 0.0
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
    try:
        root = ElementTree.fromstring(body)
    except ElementTree.ParseError as error:
        raise AppError(status_code=400, code="WECHAT_XML_INVALID", message="Invalid WeChat XML payload") from error
    return {child.tag: child.text or "" for child in root}


def xml_reply(*, open_id: str, account_id: str, content: str) -> str:
    created_at = int(time())
    return f"<xml><ToUserName><![CDATA[{open_id}]]></ToUserName><FromUserName><![CDATA[{account_id}]]></FromUserName><CreateTime>{created_at}</CreateTime><MsgType><![CDATA[text]]></MsgType><Content><![CDATA[{content}]]></Content></xml>"
