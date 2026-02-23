import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import User, Course
from schemas import AIChatRequest
from auth import get_current_user
from services.ai_service import ai_chat

router = APIRouter(prefix="/api/chat", tags=["AI Chat"])


@router.post("/ask")
async def ask_ai(
    data: AIChatRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Ask AI about courses, planner, or general learning queries."""
    course_context = ""

    if data.course_id:
        course = db.query(Course).filter(Course.id == data.course_id, Course.user_id == user.id).first()
        if course:
            course_context = f"Course: {course.title} ({course.level}). Description: {course.description}. Progress: {course.progress}%"
            curriculum = json.loads(course.curriculum or "{}")
            if curriculum:
                course_context += f". Curriculum overview: {curriculum.get('overview', '')}"

    user_profile = {
        "name": user.name,
        "educational_qualification": user.educational_qualification,
        "educational_interests": user.educational_interests,
    }

    response = await ai_chat(
        message=data.message,
        user_profile=user_profile,
        course_context=course_context or data.context or "",
    )

    return {"response": response}
