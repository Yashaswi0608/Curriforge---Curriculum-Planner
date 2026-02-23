from sqlalchemy import Column, Integer, String, Text, Boolean, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=False)
    phone = Column(String(20), nullable=True)
    password_hash = Column(String(255), nullable=True)  # null if Google OAuth
    age = Column(Integer, nullable=True)
    hobbies = Column(Text, nullable=True)          # JSON string: [{"name":"Cricket","timings":"6-8pm"}]
    habits = Column(Text, nullable=True)            # JSON string
    educational_qualification = Column(String(255), nullable=True)
    educational_interests = Column(Text, nullable=True)  # JSON string: ["AI","Web Dev"]
    daily_routine = Column(Text, nullable=True)     # JSON string describing daily schedule
    google_id = Column(String(100), nullable=True, unique=True)
    avatar_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    courses = relationship("Course", back_populates="user", cascade="all, delete-orphan")


class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    level = Column(String(50), nullable=True)       # beginner, intermediate, advanced
    reason = Column(Text, nullable=True)             # Why user wants to learn
    status = Column(String(50), default="ongoing")   # ongoing, completed
    curriculum = Column(Text, nullable=True)         # Full AI-generated curriculum JSON
    roadmap = Column(Text, nullable=True)            # AI-generated roadmap JSON
    resources = Column(Text, nullable=True)          # Links & recommendations JSON
    schedule = Column(Text, nullable=True)           # Daily schedule JSON
    progress = Column(Float, default=0.0)            # 0-100 percentage
    total_topics = Column(Integer, default=0)
    completed_topics = Column(Integer, default=0)
    learning_scores = Column(Text, nullable=True)    # JSON array of practice scores over time
    enrolled_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="courses")
    topics = relationship("Topic", back_populates="course", cascade="all, delete-orphan")
    practice_sessions = relationship("PracticeSession", back_populates="course", cascade="all, delete-orphan")


class Topic(Base):
    __tablename__ = "topics"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    week = Column(Integer, nullable=True)            # Week number
    day = Column(Integer, nullable=True)             # Day number within the plan
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    resources = Column(Text, nullable=True)          # JSON links
    duration_minutes = Column(Integer, nullable=True)
    order_index = Column(Integer, default=0)
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)

    course = relationship("Course", back_populates="topics")


class PracticeSession(Base):
    __tablename__ = "practice_sessions"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=True)
    topic_title = Column(String(255), nullable=True)
    questions = Column(Text, nullable=True)          # JSON array of questions
    answers = Column(Text, nullable=True)            # JSON array of user answers
    score = Column(Float, nullable=True)             # Score out of 10
    total_questions = Column(Integer, default=10)
    correct_answers = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    course = relationship("Course", back_populates="practice_sessions")
    topic = relationship("Topic")
