"""Main FastAPI application for Sprint Connect"""

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Optional
import random

from . import models, schemas, auth
from .database import engine, get_db

# Create database tables
models.Base.metadata.create_all(bind=engine)

# Create FastAPI app
app = FastAPI(
    title="Sprint Connect API",
    description="Peer support platform for SRH Haarlem's 5-week sprint system",
    version="1.0.0"
)

# Add CORS middleware (allow Streamlit frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your Streamlit URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============== Authentication Endpoints ==============

@app.post("/register", response_model=schemas.User)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    # Check if user exists
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    hashed_password = auth.get_password_hash(user.password)
    db_user = models.User(
        email=user.email,
        username=user.username or user.email.split("@")[0],
        hashed_password=hashed_password,
        role=user.role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Create empty profile for students
    if user.role == "student":
        profile = models.StudentProfile(
            user_id=db_user.id,
            full_name=db_user.username,
            student_id=f"SRH{db_user.id:04d}"
        )
        db.add(profile)
        db.commit()
    
    return db_user

@app.post("/token", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Login and get access token"""
    user = auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

@app.get("/me", response_model=schemas.UserWithProfile)
def get_current_user(current_user: models.User = Depends(auth.get_current_active_user), db: Session = Depends(get_db)):
    """Get current user with profile"""
    user = db.query(models.User).filter(models.User.id == current_user.id).first()
    return user

# ============== Profile Endpoints ==============

@app.post("/profile", response_model=schemas.StudentProfile)
def create_or_update_profile(
    profile: schemas.StudentProfileCreate,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create or update student profile"""
    db_profile = db.query(models.StudentProfile).filter(
        models.StudentProfile.user_id == current_user.id
    ).first()
    
    if db_profile:
        # Update existing profile
        for key, value in profile.dict(exclude_unset=True).items():
            setattr(db_profile, key, value)
    else:
        # Create new profile
        db_profile = models.StudentProfile(
            user_id=current_user.id,
            **profile.dict()
        )
        db.add(db_profile)
    
    db.commit()
    db.refresh(db_profile)
    return db_profile

@app.get("/profile/{user_id}", response_model=schemas.StudentProfile)
def get_profile(user_id: int, db: Session = Depends(get_db)):
    """Get a user's profile"""
    profile = db.query(models.StudentProfile).filter(
        models.StudentProfile.user_id == user_id
    ).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile

# ============== Study Circle Endpoints ==============

@app.get("/courses", response_model=List[schemas.Course])
def get_courses(db: Session = Depends(get_db)):
    """Get all available courses"""
    return db.query(models.Course).all()

@app.post("/courses", response_model=schemas.Course)
def create_course(
    course: schemas.CourseCreate,
    current_user: models.User = Depends(auth.get_admin_user),
    db: Session = Depends(get_db)
):
    """Create a new course (admin only)"""
    db_course = models.Course(**course.dict())
    db.add(db_course)
    db.commit()
    db.refresh(db_course)
    return db_course

@app.get("/study-circles", response_model=List[schemas.StudyCircle])
def get_study_circles(
    course_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get all study circles, optionally filtered by course"""
    query = db.query(models.StudyCircle)
    if course_id:
        query = query.filter(models.StudyCircle.course_id == course_id)
    return query.all()

@app.post("/study-circles/match", response_model=schemas.StudyCircle)
def match_to_circle(
    request: schemas.MatchingRequest,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Smart matching to find or create a study circle"""
    # Get active circles for the course
    circles = db.query(models.StudyCircle).filter(
        models.StudyCircle.course_id == request.course_id,
        models.StudyCircle.status == "active"
    ).all()
    
    # Find circle with available spots
    for circle in circles:
        member_count = db.query(models.CircleMember).filter(
            models.CircleMember.circle_id == circle.id
        ).count()
        
        if member_count < circle.max_members:
            # Check if user already in this circle
            existing = db.query(models.CircleMember).filter(
                models.CircleMember.circle_id == circle.id,
                models.CircleMember.student_id == current_user.id
            ).first()
            
            if not existing:
                # Add user to circle
                member = models.CircleMember(
                    circle_id=circle.id,
                    student_id=current_user.id
                )
                db.add(member)
                db.commit()
                db.refresh(circle)
                return circle
    
    # No suitable circle found, create new one
    course = db.query(models.Course).filter(models.Course.id == request.course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    new_circle = models.StudyCircle(
        course_id=request.course_id,
        name=f"{course.code} Study Circle {len(circles) + 1}",
        sprint_id=f"Sprint{course.sprint_number}"
    )
    db.add(new_circle)
    db.commit()
    
    # Add creator as first member
    member = models.CircleMember(
        circle_id=new_circle.id,
        student_id=current_user.id,
        role="leader"
    )
    db.add(member)
    db.commit()
    db.refresh(new_circle)
    
    return new_circle

@app.get("/study-circles/{circle_id}/members")
def get_circle_members(circle_id: int, db: Session = Depends(get_db)):
    """Get members of a study circle with their profiles"""
    members = db.query(models.CircleMember).filter(
        models.CircleMember.circle_id == circle_id
    ).all()
    
    member_details = []
    for member in members:
        user = db.query(models.User).filter(models.User.id == member.student_id).first()
        profile = db.query(models.StudentProfile).filter(
            models.StudentProfile.user_id == member.student_id
        ).first()
        
        member_details.append({
            "id": member.id,
            "user": user,
            "profile": profile,
            "joined_at": member.joined_at,
            "role": member.role,
            "participation_score": member.participation_score
        })
    
    return member_details

# ============== Wellness Check-in Endpoints ==============

@app.post("/checkin", response_model=schemas.WellnessCheckIn)
def create_checkin(
    checkin: schemas.WellnessCheckInCreate,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a daily wellness check-in"""
    # Check if already checked in today
    today = datetime.utcnow().date()
    existing = db.query(models.WellnessCheckIn).filter(
        models.WellnessCheckIn.user_id == current_user.id,
        models.WellnessCheckIn.created_at >= datetime.combine(today, datetime.min.time())
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Already checked in today")
    
    db_checkin = models.WellnessCheckIn(
        user_id=current_user.id,
        **checkin.dict()
    )
    db.add(db_checkin)
    db.commit()
    db.refresh(db_checkin)
    return db_checkin

@app.get("/checkins", response_model=List[schemas.WellnessCheckIn])
def get_my_checkins(
    days: int = 7,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get user's recent check-ins"""
    since = datetime.utcnow() - timedelta(days=days)
    return db.query(models.WellnessCheckIn).filter(
        models.WellnessCheckIn.user_id == current_user.id,
        models.WellnessCheckIn.created_at >= since
    ).order_by(models.WellnessCheckIn.created_at.desc()).all()

@app.get("/wellness/stats")
def get_wellness_stats(
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get wellness statistics for the current user"""
    # Last 7 days of check-ins
    week_ago = datetime.utcnow() - timedelta(days=7)
    checkins = db.query(models.WellnessCheckIn).filter(
        models.WellnessCheckIn.user_id == current_user.id,
        models.WellnessCheckIn.created_at >= week_ago
    ).all()
    
    if not checkins:
        return {
            "average_mood": 0,
            "trend": "neutral",
            "streak": 0,
            "total_checkins": 0
        }
    
    # Calculate statistics
    mood_scores = [c.mood_score for c in checkins]
    avg_mood = sum(mood_scores) / len(mood_scores)
    
    # Calculate trend (comparing last 3 days to previous 4)
    if len(mood_scores) >= 4:
        recent = sum(mood_scores[-3:]) / min(3, len(mood_scores[-3:]))
        older = sum(mood_scores[:-3]) / len(mood_scores[:-3])
        trend = "improving" if recent > older else "declining" if recent < older else "stable"
    else:
        trend = "neutral"
    
    # Calculate streak
    today = datetime.utcnow().date()
    streak = 0
    for i in range(7):
        check_date = today - timedelta(days=i)
        if any(c.created_at.date() == check_date for c in checkins):
            streak += 1
        else:
            break
    
    return {
        "average_mood": avg_mood,
        "trend": trend,
        "streak": streak,
        "total_checkins": len(checkins)
    }

# ============== Community Endpoints ==============

@app.get("/posts", response_model=List[schemas.CommunityPost])
def get_posts(
    category: Optional[str] = None,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Get community posts"""
    query = db.query(models.CommunityPost)
    if category:
        query = query.filter(models.CommunityPost.category == category)
    
    posts = query.order_by(models.CommunityPost.created_at.desc()).limit(limit).all()
    
    # Load author information
    for post in posts:
        post.author = db.query(models.User).filter(models.User.id == post.author_id).first()
    
    return posts

@app.post("/posts", response_model=schemas.CommunityPost)
def create_post(
    post: schemas.CommunityPostCreate,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a community post"""
    db_post = models.CommunityPost(
        author_id=current_user.id,
        **post.dict()
    )
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    db_post.author = current_user
    return db_post

@app.post("/posts/{post_id}/like")
def like_post(
    post_id: int,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Like a community post"""
    post = db.query(models.CommunityPost).filter(models.CommunityPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    post.likes_count += 1
    db.commit()
    return {"likes": post.likes_count}

@app.post("/posts/{post_id}/comment", response_model=schemas.Comment)
def create_comment(
    post_id: int,
    comment: schemas.CommentBase,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Comment on a post"""
    post = db.query(models.CommunityPost).filter(models.CommunityPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    db_comment = models.Comment(
        post_id=post_id,
        author_id=current_user.id,
        content=comment.content
    )
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    db_comment.author = current_user
    return db_comment

# ============== Event Endpoints ==============

@app.get("/events", response_model=List[schemas.Event])
def get_events(
    upcoming_only: bool = True,
    db: Session = Depends(get_db)
):
    """Get events"""
    query = db.query(models.Event)
    if upcoming_only:
        query = query.filter(models.Event.event_date >= datetime.utcnow())
    
    events = query.order_by(models.Event.event_date).all()
    
    # Load creator information
    for event in events:
        event.creator = db.query(models.User).filter(models.User.id == event.creator_id).first()
    
    return events

@app.post("/events", response_model=schemas.Event)
def create_event(
    event: schemas.EventCreate,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create an event"""
    db_event = models.Event(
        creator_id=current_user.id,
        **event.dict()
    )
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    db_event.creator = current_user
    return db_event

@app.post("/events/{event_id}/rsvp")
def rsvp_event(
    event_id: int,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """RSVP to an event"""
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Check if already RSVP'd
    existing = db.query(models.EventAttendee).filter(
        models.EventAttendee.event_id == event_id,
        models.EventAttendee.user_id == current_user.id
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Already RSVP'd")
    
    # Check max attendees
    if event.max_attendees and event.attendee_count >= event.max_attendees:
        raise HTTPException(status_code=400, detail="Event is full")
    
    # Add RSVP
    attendee = models.EventAttendee(
        event_id=event_id,
        user_id=current_user.id
    )
    db.add(attendee)
    event.attendee_count += 1
    db.commit()
    
    return {"message": "RSVP successful", "attendee_count": event.attendee_count}

# ============== Dashboard Endpoints ==============

@app.get("/dashboard", response_model=schemas.StudentDashboard)
def get_student_dashboard(
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get student dashboard data"""
    # Get user with profile
    user = db.query(models.User).filter(models.User.id == current_user.id).first()
    
    # Get active study circles
    circle_memberships = db.query(models.CircleMember).filter(
        models.CircleMember.student_id == current_user.id
    ).all()
    
    active_circles = []
    for membership in circle_memberships:
        circle = db.query(models.StudyCircle).filter(
            models.StudyCircle.id == membership.circle_id,
            models.StudyCircle.status == "active"
        ).first()
        if circle:
            active_circles.append(circle)
    
    # Get recent check-ins
    week_ago = datetime.utcnow() - timedelta(days=7)
    recent_checkins = db.query(models.WellnessCheckIn).filter(
        models.WellnessCheckIn.user_id == current_user.id,
        models.WellnessCheckIn.created_at >= week_ago
    ).order_by(models.WellnessCheckIn.created_at.desc()).limit(7).all()
    
    # Get upcoming events
    upcoming_events = db.query(models.Event).filter(
        models.Event.event_date >= datetime.utcnow()
    ).order_by(models.Event.event_date).limit(5).all()
    
    # Get recent community posts
    community_posts = db.query(models.CommunityPost).order_by(
        models.CommunityPost.created_at.desc()
    ).limit(10).all()
    
    return {
        "user": user,
        "active_circles": active_circles,
        "recent_checkins": recent_checkins,
        "upcoming_events": upcoming_events,
        "community_posts": community_posts
    }

@app.get("/admin/stats", response_model=schemas.DashboardStats)
def get_admin_stats(
    current_user: models.User = Depends(auth.get_admin_user),
    db: Session = Depends(get_db)
):
    """Get admin dashboard statistics"""
    today = datetime.utcnow().date()
    week_ago = datetime.utcnow() - timedelta(days=7)
    
    total_users = db.query(models.User).count()
    active_circles = db.query(models.StudyCircle).filter(
        models.StudyCircle.status == "active"
    ).count()
    
    checkins_today = db.query(models.WellnessCheckIn).filter(
        models.WellnessCheckIn.created_at >= datetime.combine(today, datetime.min.time())
    ).count()
    
    posts_this_week = db.query(models.CommunityPost).filter(
        models.CommunityPost.created_at >= week_ago
    ).count()
    
    # Calculate average mood
    recent_checkins = db.query(models.WellnessCheckIn).filter(
        models.WellnessCheckIn.created_at >= week_ago
    ).all()
    
    avg_mood = 0
    if recent_checkins:
        mood_scores = [c.mood_score for c in recent_checkins]
        avg_mood = sum(mood_scores) / len(mood_scores)
    
    upcoming_events = db.query(models.Event).filter(
        models.Event.event_date >= datetime.utcnow()
    ).count()
    
    return {
        "total_users": total_users,
        "active_study_circles": active_circles,
        "wellness_checkins_today": checkins_today,
        "community_posts_this_week": posts_this_week,
        "average_mood_score": avg_mood,
        "upcoming_events": upcoming_events
    }

# ============== Health Check ==============

@app.get("/")
def root():
    """API health check"""
    return {
        "message": "Sprint Connect API is running!",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "database": "connected"
    }
