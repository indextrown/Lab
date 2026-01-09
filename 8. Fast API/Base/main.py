from fastapi import FastAPI

app = FastAPI(
    title = "My FastAPI Docs",
    description = "This is a sample FastAPI application.",
    version = "1.0.0"
)

@app.get("/")
def root():
    return {"message": "Hello, World!"}

@app.get("/home")
def home():
    return {"message": "Welcome to the Home Page!"}

@app.get(
    "/profile",
    tags=["Profile"],
    summary="프로필 화면",
    description="""
    description="프로필 화면에서 사용할 사용자 기본 정보를 반환합니다."
    """)
def profile():
    return {"message": "Welcome to the Profile Page!"}
