"""Database models for Sprint Connect"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Float, Boolean, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="student")  # student, staff, admin
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    profile = relationship("StudentProfile", back_populates="user", uselist=False)
    checkins = relationship("WellnessCheckIn", back_populates="user")
    posts = relationship("CommunityPost", back_populates="author")
    study_circles = relationship("CircleMember", back_populates="student")
    created_events = relationship("Event", back_populates="creator")

class StudentProfile(Base):
    __tablename__ = "student_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    full_name = Column(String, nullable=False)
    student_id = Column(String, unique=True)
    nationality = Column(String)
    native_language = Column(String)
    program = Column(String)  # e.g., "Digital Transformation Management"
    year = Column(Integer)
    bio = Column(Text)
    interests = Column(JSON)  # List of interests
    study_preferences = Column(JSON)  # Study style preferences
    avatar_emoji = Column(String, default="🎓")
    
    # Relationships
    user = relationship("User", back_populates="profile")

class Course(Base):
    __tablename__ = "courses"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, nullable=False)  # e.g., "DTM101"
    title = Column(String, nullable=False)
    sprint_number = Column(Integer)
    academic_year = Column(String)
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    
    # Relationships
    study_circles = relationship("StudyCircle", back_populates="course")

class StudyCircle(Base):
    __tablename__ = "study_circles"
    
    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"))
    name = Column(String)
    sprint_id = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="active")  # active, completed
    max_members = Column(Integer, default=5)
    
    # Relationships
    course = relationship("Course", back_populates="study_circles")
    members = relationship("CircleMember", back_populates="circle")
    resources = relationship("Resource", back_populates="circle")

class CircleMember(Base):
    __tablename__ = "circle_members"
    
    id = Column(Integer, primary_key=True, index=True)
    circle_id = Column(Integer, ForeignKey("study_circles.id"))
    student_id = Column(Integer, ForeignKey("users.id"))
    joined_at = Column(DateTime, default=datetime.utcnow)
    participation_score = Column(Float, default=0.0)
    role = Column(String, default="member")  # member, leader
    
    # Relationships
    circle = relationship("StudyCircle", back_populates="members")
    student = relationship("User", back_populates="study_circles")

class WellnessCheckIn(Base):
    __tablename__ = "wellness_checkins"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    mood_emoji = Column(String)  # 😊, 😐, 😔, etc.
    mood_score = Column(Integer)  # 1-5 scale
    note = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    sprint_week = Column(String)  # e.g., "Sprint3_Week2"
    
    # Relationships
    user = relationship("User", back_populates="checkins")

class CommunityPost(Base):
    __tablename__ = "community_posts"
    
    id = Column(Integer, primary_key=True, index=True)
    author_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    category = Column(String)  # event, question, tip, celebration
    likes_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    author = relationship("User", back_populates="posts")
    comments = relationship("Comment", back_populates="post")

class Comment(Base):
    __tablename__ = "comments"
    
    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("community_posts.id"))
    author_id = Column(Integer, ForeignKey("users.id"))
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    post = relationship("CommunityPost", back_populates="comments")
    author = relationship("User")

class Event(Base):
    __tablename__ = "events"
    
    id = Column(Integer, primary_key=True, index=True)
    creator_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String, nullable=False)
    description = Column(Text)
    location = Column(String)
    event_date = Column(DateTime)
    attendee_count = Column(Integer, default=0)
    max_attendees = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    creator = relationship("User", back_populates="created_events")
    attendees = relationship("EventAttendee", back_populates="event")

class EventAttendee(Base):
    __tablename__ = "event_attendees"
    
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    rsvp_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    event = relationship("Event", back_populates="attendees")
    user = relationship("User")

class Resource(Base):
    __tablename__ = "resources"
    
    id = Column(Integer, primary_key=True, index=True)
    circle_id = Column(Integer, ForeignKey("study_circles.id"))
    uploaded_by = Column(Integer, ForeignKey("users.id"))
    title = Column(String, nullable=False)
    description = Column(Text)
    url = Column(String)
    resource_type = Column(String)  # link, note, flashcard, guide
    upvotes = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    circle = relationship("StudyCircle", back_populates="resources")
    uploader = relationship("User")

class PeerSupport(Base):
    __tablename__ = "peer_support"
    
    id = Column(Integer, primary_key=True, index=True)
    supporter_id = Column(Integer, ForeignKey("users.id"))
    seeker_id = Column(Integer, ForeignKey("users.id"))
    status = Column(String, default="pending")  # pending, active, completed
    message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    supporter = relationship("User", foreign_keys=[supporter_id])
    seeker = relationship("User", foreign_keys=[seeker_id])

# ============== Gamification Models ==============

class GamificationPoints(Base):
    __tablename__ = "gamification_points"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    points = Column(Integer, default=0)
    level = Column(Integer, default=1)
    total_points_earned = Column(Integer, default=0)
    streak_days = Column(Integer, default=0)
    last_activity = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User")

class Badge(Base):
    __tablename__ = "badges"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(Text)
    icon = Column(String)  # emoji or icon name
    category = Column(String)  # wellness, participation, achievement, etc.
    points_required = Column(Integer, default=0)
    criteria = Column(JSON)  # Flexible criteria for earning badge
    rarity = Column(String, default="common")  # common, rare, epic, legendary
    created_at = Column(DateTime, default=datetime.utcnow)

class UserBadge(Base):
    __tablename__ = "user_badges"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    badge_id = Column(Integer, ForeignKey("badges.id"))
    earned_at = Column(DateTime, default=datetime.utcnow)
    progress = Column(Float, default=0.0)  # 0.0 to 1.0

    # Relationships
    user = relationship("User")
    badge = relationship("Badge")

class PointsTransaction(Base):
    __tablename__ = "points_transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    points = Column(Integer)  # Can be positive or negative
    action_type = Column(String)  # checkin, post, comment, event_rsvp, etc.
    description = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User")

# ============== Pomodoro & Study Session Models ==============

class PomodoroSession(Base):
    __tablename__ = "pomodoro_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    circle_id = Column(Integer, ForeignKey("study_circles.id"), nullable=True)
    duration_minutes = Column(Integer, default=25)
    break_minutes = Column(Integer, default=5)
    started_at = Column(DateTime)
    ended_at = Column(DateTime, nullable=True)
    completed = Column(Boolean, default=False)
    is_group_session = Column(Boolean, default=False)

    # Relationships
    user = relationship("User")
    circle = relationship("StudyCircle")

class StudySession(Base):
    __tablename__ = "study_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    circle_id = Column(Integer, ForeignKey("study_circles.id"), nullable=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    duration_minutes = Column(Integer, nullable=True)
    session_type = Column(String)  # solo, group, pomodoro
    notes = Column(Text)
    productivity_rating = Column(Integer)  # 1-5

    # Relationships
    user = relationship("User")
    circle = relationship("StudyCircle")
    course = relationship("Course")

# ============== Video & Collaboration Models ==============

class VideoRoom(Base):
    __tablename__ = "video_rooms"

    id = Column(Integer, primary_key=True, index=True)
    circle_id = Column(Integer, ForeignKey("study_circles.id"))
    room_name = Column(String, unique=True, nullable=False)
    jitsi_room_id = Column(String, unique=True)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    last_used = Column(DateTime)
    participant_count = Column(Integer, default=0)

    # Relationships
    circle = relationship("StudyCircle")
    creator = relationship("User")

class WhiteboardSession(Base):
    __tablename__ = "whiteboard_sessions"

    id = Column(Integer, primary_key=True, index=True)
    circle_id = Column(Integer, ForeignKey("study_circles.id"))
    session_name = Column(String)
    session_data = Column(Text)  # JSON string of whiteboard data
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    # Relationships
    circle = relationship("StudyCircle")
    creator = relationship("User")

# ============== Notification Models ==============

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(String)  # event, message, achievement, alert
    is_read = Column(Boolean, default=False)
    action_url = Column(String)  # URL to navigate to when clicked
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User")

# ============== Analytics & Insights Models ==============

class UserEngagement(Base):
    __tablename__ = "user_engagement"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    date = Column(DateTime, default=datetime.utcnow)
    checkins_count = Column(Integer, default=0)
    posts_count = Column(Integer, default=0)
    comments_count = Column(Integer, default=0)
    study_minutes = Column(Integer, default=0)
    circles_joined = Column(Integer, default=0)
    events_attended = Column(Integer, default=0)
    engagement_score = Column(Float, default=0.0)  # Calculated score

    # Relationships
    user = relationship("User")
