import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
from config import settings

# Import routes
from routes.users import router as users_router
from routes.courses import router as courses_router
from routes.practice import router as practice_router
from routes.ai_chat import router as chat_router

# Create database tables
Base.metadata.create_all(bind=engine)

# FastAPI app
app = FastAPI(
    title="CurriForge",
    description="Generative AI-Powered Curriculum Design System",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(users_router)
app.include_router(courses_router)
app.include_router(practice_router)
app.include_router(chat_router)

# Serve static frontend files
app.mount("/static", StaticFiles(directory="../frontend"), name="static")


# Frontend page routes
@app.get("/")
async def serve_login():
    return FileResponse("../frontend/index.html")


@app.get("/dashboard")
async def serve_dashboard():
    return FileResponse("../frontend/dashboard.html")


@app.get("/enroll")
async def serve_enroll():
    return FileResponse("../frontend/enroll.html")


@app.get("/courses")
async def serve_courses():
    return FileResponse("../frontend/courses.html")


@app.get("/planner/{course_id}")
async def serve_planner(course_id: int):
    return FileResponse("../frontend/planner.html")


@app.get("/practice")
async def serve_practice():
    return FileResponse("../frontend/practice.html")


@app.get("/profile")
async def serve_profile():
    return FileResponse("../frontend/profile.html")


if __name__ == "__main__":
    uvicorn.run("main:app", host=settings.APP_HOST, port=settings.APP_PORT, reload=True)
