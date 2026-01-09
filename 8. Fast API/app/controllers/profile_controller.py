from fastapi import APIRouter
from app.services.profile_service import get_profile_message
from app.models.profile import ProfileResponse

router = APIRouter(
    prefix="/profile",
    tags=["Profile"]
)

@router.get(
    "",
    summary="프로필 화면",
    description="프로필 화면에서 사용할 사용자 기본 정보를 반환합니다."
)
def profile() -> ProfileResponse:
    return get_profile_message()
