from hashlib import sha1

from app.core.errors import AppError
from app.modules.notifications.wechat import parse_message, valid_signature, xml_reply


def test_wechat_signature_uses_sorted_token_parts() -> None:
    token, timestamp, nonce = "secret", "1700000000", "abc"
    signature = sha1("".join(sorted((token, timestamp, nonce))).encode()).hexdigest()
    assert valid_signature(token=token, timestamp=timestamp, nonce=nonce, signature=signature)
    assert not valid_signature(token=token, timestamp=timestamp, nonce=nonce, signature="bad")


def test_wechat_xml_message_round_trip() -> None:
    body = xml_reply(open_id="user", account_id="account", content="绑定成功")
    parsed = parse_message(body.encode())
    assert parsed["FromUserName"] == "account"
    assert parsed["ToUserName"] == "user"
    assert parsed["Content"] == "绑定成功"


def test_invalid_binding_code_error_contract() -> None:
    error = AppError(status_code=400, code="INVALID_WECHAT_BINDING_CODE", message="invalid")
    assert error.status_code == 400
    assert error.code == "INVALID_WECHAT_BINDING_CODE"
