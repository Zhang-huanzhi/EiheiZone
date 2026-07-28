from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.router import router as auth_router
from app.modules.posts.router import public_router as public_posts_router
from app.modules.posts.router import router as posts_router
from app.modules.qas.router import router as qas_router


router = APIRouter()
router.include_router(auth_router)
router.include_router(public_posts_router)
router.include_router(posts_router)
router.include_router(qas_router)


@router.get("/health")
def health_check(db: Session = Depends(get_db)) -> dict[str, str]:
    db.execute(text("SELECT 1"))
    return {"status": "ok"}
