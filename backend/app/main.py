from fastapi import FastAPI

from app.api import router as api_router
from app.core.config import get_settings
from app.core.errors import register_exception_handlers
from app.core.request_id import request_id_middleware


settings = get_settings()
app = FastAPI(title=settings.app_name)
app.middleware("http")(request_id_middleware)
register_exception_handlers(app)
app.include_router(api_router, prefix="/api/v1")
