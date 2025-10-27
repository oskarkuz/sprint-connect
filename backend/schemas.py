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
