# API routes
from fastapi import APIRouter
from app.api import chef

router = APIRouter(prefix="/api")

# Chef 라우터 등록
router.include_router(chef.router)
