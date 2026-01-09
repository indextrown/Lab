from app.models.profile import ProfileResponse

def get_profile_message() -> ProfileResponse:
    return ProfileResponse(
        message="Welcome to the Profile Page!"
    )
