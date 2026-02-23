import json
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import User, Course, Topic
from schemas import CourseEnrollRequest, CourseResponse
from auth import get_current_user
from services.ai_service import generate_curriculum

router = APIRouter(prefix="/api/courses", tags=["Courses"])


@router.post("/enroll")
async def enroll_course(
    data: CourseEnrollRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Enroll in a new course - AI generates personalized curriculum."""

    # Gather user profile for AI context
    ongoing_courses = db.query(Course).filter(
        Course.user_id == user.id, Course.status == "ongoing"
    ).all()
    ongoing_titles = [c.title for c in ongoing_courses]

    user_profile = {
        "age": user.age,
        "educational_qualification": user.educational_qualification,
        "educational_interests": user.educational_interests,
        "hobbies": user.hobbies,
        "habits": user.habits,
        "daily_routine": user.daily_routine,
        "ongoing_courses": ", ".join(ongoing_titles) if ongoing_titles else "None",
    }

    # Generate curriculum using AI
    ai_result = await generate_curriculum(
        subject=data.subject,
        level=data.level,
        reason=data.reason or "",
        duration_weeks=data.preferred_duration_weeks or 4,
        daily_hours=data.daily_hours or 1.0,
        user_profile=user_profile,
    )

    if "error" in ai_result and "title" not in ai_result:
        raise HTTPException(status_code=500, detail=ai_result["error"])

    # Create course record
    topics_data = ai_result.get("topics", [])

    course = Course(
        user_id=user.id,
        title=ai_result.get("title", data.subject),
        description=ai_result.get("description", ""),
        level=data.level,
        reason=data.reason,
        status="ongoing",
        curriculum=json.dumps(ai_result.get("curriculum", {})),
        roadmap=json.dumps(ai_result.get("roadmap", {})),
        resources=json.dumps(ai_result.get("resources", {})),
        schedule=json.dumps(ai_result.get("schedule", {})),
        progress=0.0,
        total_topics=len(topics_data),
        completed_topics=0,
        learning_scores=json.dumps([]),
    )
    db.add(course)
    db.commit()
    db.refresh(course)

    # Create topic records
    for i, topic_data in enumerate(topics_data):
        topic = Topic(
            course_id=course.id,
            week=topic_data.get("week", 1),
            day=topic_data.get("day", i + 1),
            title=topic_data.get("title", f"Topic {i + 1}"),
            description=topic_data.get("description", ""),
            resources=json.dumps(topic_data.get("resources", [])),
            duration_minutes=topic_data.get("duration_minutes", 60),
            order_index=i,
            is_completed=False,
        )
        db.add(topic)

    db.commit()

    return {
        "message": "Course enrolled successfully!",
        "course_id": course.id,
        "title": course.title,
        "total_topics": course.total_topics,
        "curriculum": ai_result,
    }


@router.get("/", response_model=list[CourseResponse])
async def get_all_courses(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get all courses for the current user."""
    courses = db.query(Course).filter(Course.user_id == user.id).order_by(Course.enrolled_at.desc()).all()
    return courses


@router.get("/dashboard")
async def get_dashboard(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get dashboard data."""
    all_courses = db.query(Course).filter(Course.user_id == user.id).order_by(Course.enrolled_at.desc()).all()

    recent = all_courses[:3]
    ongoing = [c for c in all_courses if c.status == "ongoing"]
    completed = [c for c in all_courses if c.status == "completed"]

    # Learning curve data: collect scores from all practice sessions
    learning_data = []
    for course in all_courses:
        scores = json.loads(course.learning_scores or "[]")
        learning_data.append({
            "course_id": course.id,
            "title": course.title,
            "progress": course.progress,
            "scores": scores,
            "status": course.status,
        })

    return {
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "avatar_url": user.avatar_url,
        },
        "recent_courses": [{
            "id": c.id, "title": c.title, "progress": c.progress,
            "status": c.status, "level": c.level,
            "enrolled_at": c.enrolled_at.isoformat() if c.enrolled_at else None,
        } for c in recent],
        "ongoing_count": len(ongoing),
        "completed_count": len(completed),
        "total_courses": len(all_courses),
        "ongoing_courses": [{
            "id": c.id, "title": c.title, "progress": c.progress, "level": c.level,
        } for c in ongoing],
        "completed_courses": [{
            "id": c.id, "title": c.title, "completed_at": c.completed_at.isoformat() if c.completed_at else None,
        } for c in completed],
        "learning_data": learning_data,
    }


@router.get("/{course_id}")
async def get_course(
    course_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a specific course with all details."""
    course = db.query(Course).filter(Course.id == course_id, Course.user_id == user.id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    topics = db.query(Topic).filter(Topic.course_id == course_id).order_by(Topic.order_index).all()

    return {
        "id": course.id,
        "title": course.title,
        "description": course.description,
        "level": course.level,
        "reason": course.reason,
        "status": course.status,
        "curriculum": json.loads(course.curriculum or "{}"),
        "roadmap": json.loads(course.roadmap or "{}"),
        "resources": json.loads(course.resources or "{}"),
        "schedule": json.loads(course.schedule or "{}"),
        "progress": course.progress,
        "total_topics": course.total_topics,
        "completed_topics": course.completed_topics,
        "learning_scores": json.loads(course.learning_scores or "[]"),
        "enrolled_at": course.enrolled_at.isoformat() if course.enrolled_at else None,
        "completed_at": course.completed_at.isoformat() if course.completed_at else None,
        "topics": [{
            "id": t.id,
            "week": t.week,
            "day": t.day,
            "title": t.title,
            "description": t.description,
            "resources": json.loads(t.resources or "[]"),
            "duration_minutes": t.duration_minutes,
            "order_index": t.order_index,
            "is_completed": t.is_completed,
            "completed_at": t.completed_at.isoformat() if t.completed_at else None,
        } for t in topics],
    }


@router.put("/{course_id}/topics/{topic_id}/toggle")
async def toggle_topic(
    course_id: int,
    topic_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Toggle topic completion status."""
    course = db.query(Course).filter(Course.id == course_id, Course.user_id == user.id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    topic = db.query(Topic).filter(Topic.id == topic_id, Topic.course_id == course_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    # Toggle
    topic.is_completed = not topic.is_completed
    topic.completed_at = datetime.now(timezone.utc) if topic.is_completed else None

    # Recalculate course progress
    all_topics = db.query(Topic).filter(Topic.course_id == course_id).all()
    completed_count = sum(1 for t in all_topics if t.is_completed or (t.id == topic_id and topic.is_completed))
    # Adjust for current toggle
    if topic.id in [t.id for t in all_topics]:
        completed_count = sum(1 for t in all_topics if t.id != topic_id and t.is_completed)
        completed_count += 1 if topic.is_completed else 0

    total = len(all_topics)
    course.completed_topics = completed_count
    course.progress = (completed_count / total * 100) if total > 0 else 0

    # Check if course is completed
    if completed_count == total and total > 0:
        course.status = "completed"
        course.completed_at = datetime.now(timezone.utc)
    else:
        course.status = "ongoing"
        course.completed_at = None

    db.commit()

    return {
        "topic_id": topic.id,
        "is_completed": topic.is_completed,
        "course_progress": course.progress,
        "course_status": course.status,
        "completed_topics": course.completed_topics,
        "total_topics": total,
    }


@router.delete("/{course_id}")
async def delete_course(
    course_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a course."""
    course = db.query(Course).filter(Course.id == course_id, Course.user_id == user.id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    db.delete(course)
    db.commit()
    return {"message": "Course deleted successfully"}
