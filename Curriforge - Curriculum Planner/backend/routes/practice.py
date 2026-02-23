import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import User, Course, Topic, PracticeSession
from schemas import PracticeRequest, AnswerSubmit
from auth import get_current_user
from services.ai_service import generate_practice_questions, evaluate_answers

router = APIRouter(prefix="/api/practice", tags=["Practice"])


@router.post("/generate")
async def generate_questions(
    data: PracticeRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generate 10 practice questions for a topic."""
    course = db.query(Course).filter(Course.id == data.course_id, Course.user_id == user.id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    topic_title = data.topic_title
    if data.topic_id:
        topic = db.query(Topic).filter(Topic.id == data.topic_id).first()
        if topic:
            topic_title = topic.title

    if not topic_title:
        raise HTTPException(status_code=400, detail="Topic title is required")

    # Generate questions using AI
    result = await generate_practice_questions(
        subject=course.title,
        topic_title=topic_title,
        level=course.level or "beginner",
        course_context=course.description or "",
    )

    if "error" in result and not result.get("questions"):
        raise HTTPException(status_code=500, detail=result["error"])

    # Create practice session
    session = PracticeSession(
        course_id=course.id,
        topic_id=data.topic_id,
        topic_title=topic_title,
        questions=json.dumps(result.get("questions", [])),
        total_questions=len(result.get("questions", [])),
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    return {
        "session_id": session.id,
        "topic_title": topic_title,
        "questions": result.get("questions", []),
    }


@router.post("/submit")
async def submit_answers(
    data: AnswerSubmit,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Submit answers and get evaluation."""
    session = db.query(PracticeSession).filter(PracticeSession.id == data.session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Practice session not found")

    # Verify course belongs to user
    course = db.query(Course).filter(Course.id == session.course_id, Course.user_id == user.id).first()
    if not course:
        raise HTTPException(status_code=403, detail="Not authorized")

    questions = json.loads(session.questions or "[]")

    # Evaluate using AI
    evaluation = await evaluate_answers(questions, data.answers)

    # Update session
    session.answers = json.dumps(data.answers)
    session.score = evaluation.get("score", 0)
    session.correct_answers = evaluation.get("total_correct", 0)

    # Update course learning scores
    scores = json.loads(course.learning_scores or "[]")
    scores.append({
        "session_id": session.id,
        "topic": session.topic_title,
        "score": session.score,
        "total_correct": session.correct_answers,
        "total_questions": session.total_questions,
    })
    course.learning_scores = json.dumps(scores)

    db.commit()

    return {
        "session_id": session.id,
        "score": session.score,
        "correct_answers": session.correct_answers,
        "total_questions": session.total_questions,
        "results": evaluation.get("results", []),
        "overall_feedback": evaluation.get("overall_feedback", ""),
    }


@router.get("/history/{course_id}")
async def get_practice_history(
    course_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get practice history for a course."""
    course = db.query(Course).filter(Course.id == course_id, Course.user_id == user.id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    sessions = db.query(PracticeSession).filter(
        PracticeSession.course_id == course_id
    ).order_by(PracticeSession.created_at.desc()).all()

    return [{
        "id": s.id,
        "topic_title": s.topic_title,
        "score": s.score,
        "correct_answers": s.correct_answers,
        "total_questions": s.total_questions,
        "created_at": s.created_at.isoformat() if s.created_at else None,
    } for s in sessions]
