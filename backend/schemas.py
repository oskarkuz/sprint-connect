"""Pydantic schemas for Sprint Connect API"""

from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime

# User schemas
class UserBase(BaseModel):
    email: EmailStr
    username: Optional[str] = None
    role: str = "student"

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class UserWithProfile(User):
    profile: Optional["StudentProfile"] = None

# Student Profile schemas
class StudentProfileBase(BaseModel):
    full_name: str
    student_id: Optional[str] = None
    nationality: Optional[str] = None
    native_language: Optional[str] = None
    program: Optional[str] = None
    year: Optional[int] = None
    bio: Optional[str] = None
    interests: Optional[List[str]] = []
    study_preferences: Optional[Dict[str, Any]] = {}
    avatar_emoji: str = "🎓"

class StudentProfileCreate(StudentProfileBase):
    pass

class StudentProfile(StudentProfileBase):
    id: int
    user_id: int
    
    class Config:
        from_attributes = True

# Course schemas
class CourseBase(BaseModel):
    code: str
    title: str
    sprint_number: int
    academic_year: str
    start_date: datetime
    end_date: datetime

class CourseCreate(CourseBase):
    pass

class Course(CourseBase):
    id: int
    
    class Config:
        from_attributes = True

# Study Circle schemas
class StudyCircleBase(BaseModel):
    course_id: int
    name: str
    sprint_id: str
    max_members: int = 5

class StudyCircleCreate(StudyCircleBase):
    pass

class StudyCircle(StudyCircleBase):
    id: int
    created_at: datetime
    status: str
    members: List["CircleMember"] = []
    
    class Config:
        from_attributes = True

class CircleMemberBase(BaseModel):
    circle_id: int
    student_id: int
    role: str = "member"

class CircleMemberCreate(CircleMemberBase):
    pass

class CircleMember(CircleMemberBase):
    id: int
    joined_at: datetime
    participation_score: float
    
    class Config:
        from_attributes = True

# Wellness Check-in schemas
class WellnessCheckInBase(BaseModel):
    mood_emoji: str
    mood_score: int  # 1-5 scale
    note: Optional[str] = None
    sprint_week: Optional[str] = None

class WellnessCheckInCreate(WellnessCheckInBase):
    pass

class WellnessCheckIn(WellnessCheckInBase):
    id: int
    user_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# Community Post schemas
class CommunityPostBase(BaseModel):
    title: str
    content: str
    category: Optional[str] = "general"

class CommunityPostCreate(CommunityPostBase):
    pass

class CommunityPost(CommunityPostBase):
    id: int
    author_id: int
    likes_count: int
    created_at: datetime
    updated_at: datetime
    author: Optional[User] = None
    comments: List["Comment"] = []
    
    class Config:
        from_attributes = True

class CommentBase(BaseModel):
    content: str

class CommentCreate(CommentBase):
    post_id: int

class Comment(CommentBase):
    id: int
    post_id: int
    author_id: int
    created_at: datetime
    author: Optional[User] = None
    
    class Config:
        from_attributes = True

# Event schemas
class EventBase(BaseModel):
    title: str
    description: Optional[str] = None
    location: Optional[str] = None
    event_date: datetime
    max_attendees: Optional[int] = None

class EventCreate(EventBase):
    pass

class Event(EventBase):
    id: int
    creator_id: int
    attendee_count: int
    created_at: datetime
    creator: Optional[User] = None
    
    class Config:
        from_attributes = True

# Resource schemas
class ResourceBase(BaseModel):
    title: str
    description: Optional[str] = None
    url: Optional[str] = None
    resource_type: str = "link"

class ResourceCreate(ResourceBase):
    circle_id: int

class Resource(ResourceBase):
    id: int
    circle_id: int
    uploaded_by: int
    upvotes: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# Authentication schemas
class Token(BaseModel):
    access_token: str
    token_type: str
    user: User

class TokenData(BaseModel):
    email: Optional[str] = None

# Matching schemas
class StudyPreferences(BaseModel):
    preferred_times: List[str]  # ["morning", "afternoon", "evening"]
    study_style: str  # "visual", "auditory", "kinesthetic"
    group_size_preference: str  # "small", "medium", "large"
    language_preference: Optional[str] = None
    goals: Optional[str] = None  # "top_grades", "pass", "deep_understanding"

class MatchingRequest(BaseModel):
    course_id: int
    preferences: StudyPreferences

# Dashboard schemas
class DashboardStats(BaseModel):
    total_users: int
    active_study_circles: int
    wellness_checkins_today: int
    community_posts_this_week: int
    average_mood_score: float
    upcoming_events: int

class StudentDashboard(BaseModel):
    user: UserWithProfile
    active_circles: List[StudyCircle]
    recent_checkins: List[WellnessCheckIn]
    upcoming_events: List[Event]
    community_posts: List[CommunityPost]

# ============== Gamification Schemas ==============

class BadgeBase(BaseModel):
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    category: Optional[str] = None
    points_required: int = 0
    criteria: Optional[Dict[str, Any]] = {}
    rarity: str = "common"

class Badge(BadgeBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class UserBadgeBase(BaseModel):
    badge_id: int
    progress: float = 0.0

class UserBadge(UserBadgeBase):
    id: int
    user_id: int
    earned_at: datetime
    badge: Optional[Badge] = None

    class Config:
        from_attributes = True

class GamificationPointsBase(BaseModel):
    points: int = 0
    level: int = 1
    total_points_earned: int = 0
    streak_days: int = 0

class GamificationPoints(GamificationPointsBase):
    id: int
    user_id: int
    last_activity: datetime

    class Config:
        from_attributes = True

class PointsTransactionBase(BaseModel):
    points: int
    action_type: str
    description: Optional[str] = None

class PointsTransaction(PointsTransactionBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class LeaderboardEntry(BaseModel):
    user_id: int
    username: str
    points: int
    level: int
    rank: int

class UserStatsResponse(BaseModel):
    points: int
    level: int
    total_points_earned: int
    streak_days: int
    badges_count: int
    rank: int
    total_users: int

# ============== Pomodoro Schemas ==============

class PomodoroSessionBase(BaseModel):
    duration_minutes: int = 25
    break_minutes: int = 5
    circle_id: Optional[int] = None
    is_group_session: bool = False

class PomodoroSessionCreate(PomodoroSessionBase):
    pass

class PomodoroSession(PomodoroSessionBase):
    id: int
    user_id: int
    started_at: datetime
    ended_at: Optional[datetime] = None
    completed: bool

    class Config:
        from_attributes = True

class PomodoroStats(BaseModel):
    total_sessions: int
    total_minutes: int
    total_hours: float
    completed_today: int
    average_per_day: float

# ============== Study Session Schemas ==============

class StudySessionBase(BaseModel):
    circle_id: Optional[int] = None
    course_id: Optional[int] = None
    session_type: str = "solo"
    notes: Optional[str] = None
    productivity_rating: Optional[int] = None

class StudySessionCreate(StudySessionBase):
    pass

class StudySession(StudySessionBase):
    id: int
    user_id: int
    started_at: datetime
    ended_at: Optional[datetime] = None
    duration_minutes: Optional[int] = None

    class Config:
        from_attributes = True

# ============== Video Room Schemas ==============

class VideoRoomBase(BaseModel):
    circle_id: int
    room_name: str

class VideoRoomCreate(VideoRoomBase):
    pass

class VideoRoom(VideoRoomBase):
    id: int
    jitsi_room_id: str
    created_by: int
    created_at: datetime
    is_active: bool
    last_used: Optional[datetime] = None
    participant_count: int

    class Config:
        from_attributes = True

# ============== Notification Schemas ==============

class NotificationBase(BaseModel):
    title: str
    message: str
    notification_type: str = "info"
    action_url: Optional[str] = None

class Notification(NotificationBase):
    id: int
    user_id: int
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True

# ============== Analytics Schemas ==============

class StressAnalysis(BaseModel):
    average_mood: float
    recent_average: float
    trend: str
    low_mood_days_count: int
    alert: bool
    alert_message: str
    total_checkins: int
