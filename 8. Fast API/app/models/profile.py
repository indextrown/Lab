from pydantic import BaseModel

class ProfileResponse(BaseModel):
    message: str
