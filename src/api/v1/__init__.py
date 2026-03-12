from fastapi import APIRouter
from src.api.v1.auth.router import router as auth_router
from src.api.v1.users.router import router as users_router
from src.api.v1.staff.router import router as staff_router

router = APIRouter(prefix="/v1")

router.include_router(auth_router)
router.include_router(users_router)
router.include_router(staff_router)
