from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime


# ── User Schemas ──
class UserSignup(BaseModel):
    name: str
    email: EmailStr
    password: str
    phone: Optional[str] = None
    age: Optional[int] = None
    hobbies: Optional[str] = None
    habits: Optional[str] = None
    educational_qualification: Optional[str] = None
    educational_interests: Optional[str] = None
    daily_routine: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class GoogleAuthRequest(BaseModel):
    token: str


class UserProfileUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    age: Optional[int] = None
    hobbies: Optional[str] = None
    habits: Optional[str] = None
    educational_qualification: Optional[str] = None
    educational_interests: Optional[str] = None
    daily_routine: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    phone: Optional[str] = None
    age: Optional[int] = None
    hobbies: Optional[str] = None
    habits: Optional[str] = None
    educational_qualification: Optional[str] = None
    educational_interests: Optional[str] = None
    daily_routine: Optional[str] = None
    avatar_url: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ── Course Schemas ──
class CourseEnrollRequest(BaseModel):
    subject: str
    level: str = "beginner"          # beginner, intermediate, advanced
    reason: Optional[str] = None     # Why user wants to learn
    preferred_duration_weeks: Optional[int] = 4
    daily_hours: Optional[float] = 1.0


class CourseResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    level: Optional[str] = None
    reason: Optional[str] = None
    status: str
    curriculum: Optional[str] = None
    roadmap: Optional[str] = None
    resources: Optional[str] = None
    schedule: Optional[str] = None
    progress: float
    total_topics: int
    completed_topics: int
    learning_scores: Optional[str] = None
    enrolled_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ── Topic Schemas ──
class TopicResponse(BaseModel):
    id: int
    course_id: int
    week: Optional[int] = None
    day: Optional[int] = None
    title: str
    description: Optional[str] = None
    resources: Optional[str] = None
    duration_minutes: Optional[int] = None
    order_index: int
    is_completed: bool
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TopicToggle(BaseModel):
    is_completed: bool


# ── Practice Schemas ──
class PracticeRequest(BaseModel):
    course_id: int
    topic_id: Optional[int] = None
    topic_title: Optional[str] = None


class AnswerSubmit(BaseModel):
    session_id: int
    answers: List[str]


class PracticeResponse(BaseModel):
    id: int
    course_id: int
    topic_id: Optional[int] = None
    topic_title: Optional[str] = None
    questions: Optional[str] = None
    answers: Optional[str] = None
    score: Optional[float] = None
    total_questions: int
    correct_answers: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ── AI Chat Schema ──
class AIChatRequest(BaseModel):
    message: str
    course_id: Optional[int] = None
    context: Optional[str] = None
