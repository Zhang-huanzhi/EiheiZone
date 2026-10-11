"""Authenticated notification settings and public WeChat callback endpoints."""

from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AppError
from app.db.session import get_db
from app.modules.auth.dependencies import CurrentUser, require_family_access, validate_csrf_request
from app.modules.notifications.service import bind_open_id_by_code, binding_status, create_binding_code, unbind
from app.modules.notifications.wechat import parse_message, valid_signature, xml_reply

router = APIRouter(prefix="/notifications", tags=["notifications"])
wechat_router = APIRouter(prefix="/wechat", tags=["wechat"])


@router.get("/wechat", response_model=dict[str, object])
def get_status(current_user: CurrentUser = Depends(require_family_access), db: Session = Depends(get_db)) -> dict[str, object]:
    return binding_status(db, user=current_user.user)


@router.post("/wechat/code", response_model=dict[str, object])
def generate_code(request: Request, current_user: CurrentUser = Depends(require_family_access), db: Session = Depends(get_db)) -> dict[str, object]:
    validate_csrf_request(request, current_user.session_id)
    code, expires_at = create_binding_code(db, user=current_user.user)
    return {"code": code, "expires_at": expires_at}


@router.delete("/wechat", status_code=204)
def delete_binding(request: Request, current_user: CurrentUser = Depends(require_family_access), db: Session = Depends(get_db)) -> None:
    validate_csrf_request(request, current_user.session_id)
    unbind(db, user=current_user.user)


@wechat_router.get("/callback")
def verify_callback(signature: str = Query(), timestamp: str = Query(), nonce: str = Query(), echostr: str = Query()) -> Response:
    settings = get_settings()
    if not settings.wechat_token or not valid_signature(token=settings.wechat_token, timestamp=timestamp, nonce=nonce, signature=signature):
        raise AppError(status_code=403, code="WECHAT_SIGNATURE_INVALID", message="Invalid WeChat signature")
    return Response(content=echostr, media_type="text/plain")


@wechat_router.post("/callback")
async def receive_callback(request: Request, signature: str = Query(), timestamp: str = Query(), nonce: str = Query(), db: Session = Depends(get_db)) -> Response:
    settings = get_settings()
    if not settings.wechat_token or not valid_signature(token=settings.wechat_token, timestamp=timestamp, nonce=nonce, signature=signature):
        raise AppError(status_code=403, code="WECHAT_SIGNATURE_INVALID", message="Invalid WeChat signature")
    message = parse_message(await request.body())
    if message.get("MsgType") == "text" and message.get("Content", "").strip():
        try:
            content = bind_open_id_by_code(db, open_id=message.get("FromUserName", ""), raw_code=message["Content"])
        except AppError:
            content = "绑定码无效或已过期，请回网站重新生成。"
    elif message.get("Event") == "subscribe":
        content = "欢迎关注，请先在网站通知设置中生成绑定码，再把绑定码发给我。"
    else:
        content = "请在网站通知设置中生成绑定码。"
    return Response(content=xml_reply(open_id=message.get("FromUserName", ""), account_id=message.get("ToUserName", ""), content=content), media_type="application/xml")
