from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def root():
    return {"message": "Hello, World!"}

@router.get("/home")
def home():
    return {"message": "Welcome to the Home Page!"}
