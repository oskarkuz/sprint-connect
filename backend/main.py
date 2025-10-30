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

                # Award points for joining circle
                from . import gamification
                gamification.award_points(db, current_user.id, "join_circle", f"Joined {circle.name}")

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

    # Award points for check-in and update streak (import gamification at top of file)
    from . import gamification
    gamification.award_points(db, current_user.id, "daily_checkin", "Daily wellness check-in")
    gamification.update_streak(db, current_user.id)

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

    # Award points for creating post
    from . import gamification
    gamification.award_points(db, current_user.id, "create_post", "Created community post")

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

# ============== Gamification Endpoints ==============

from . import gamification

@app.get("/gamification/stats", response_model=schemas.UserStatsResponse)
def get_my_gamification_stats(
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get current user's gamification statistics"""
    stats = gamification.get_user_stats(db, current_user.id)
    return schemas.UserStatsResponse(**stats)

@app.get("/gamification/leaderboard")
def get_leaderboard(
    limit: int = 10,
    timeframe: str = "all_time",
    db: Session = Depends(get_db)
):
    """Get leaderboard - timeframe: all_time, week, month"""
    leaders = gamification.get_leaderboard(db, limit, timeframe)

    leaderboard_data = []
    for idx, leader in enumerate(leaders, 1):
        user = db.query(models.User).filter(models.User.id == leader.user_id).first()
        leaderboard_data.append({
            "rank": idx,
            "user_id": leader.user_id,
            "username": user.username if user else "Unknown",
            "points": leader.points,
            "level": leader.level
        })

    return {
        "timeframe": timeframe,
        "leaderboard": leaderboard_data
    }

@app.get("/gamification/badges", response_model=List[schemas.Badge])
def get_all_badges(db: Session = Depends(get_db)):
    """Get all available badges"""
    return db.query(models.Badge).all()

@app.get("/gamification/my-badges")
def get_my_badges(
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get current user's earned badges"""
    user_badges = db.query(models.UserBadge).filter(
        models.UserBadge.user_id == current_user.id
    ).all()

    result = []
    for ub in user_badges:
        badge = db.query(models.Badge).filter(models.Badge.id == ub.badge_id).first()
        result.append({
            "id": ub.id,
            "earned_at": ub.earned_at,
            "progress": ub.progress,
            "badge": badge
        })

    return result

@app.get("/gamification/transactions")
def get_my_transactions(
    limit: int = 20,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get user's recent points transactions"""
    transactions = db.query(models.PointsTransaction).filter(
        models.PointsTransaction.user_id == current_user.id
    ).order_by(models.PointsTransaction.created_at.desc()).limit(limit).all()

    return transactions

# ============== Pomodoro Endpoints ==============

@app.post("/pomodoro/start", response_model=schemas.PomodoroSession)
def start_pomodoro_session(
    session_data: schemas.PomodoroSessionCreate,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Start a new Pomodoro session"""
    session = models.PomodoroSession(
        user_id=current_user.id,
        circle_id=session_data.circle_id,
        duration_minutes=session_data.duration_minutes,
        break_minutes=session_data.break_minutes,
        is_group_session=session_data.is_group_session,
        started_at=datetime.utcnow()
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    return session

@app.post("/pomodoro/{session_id}/complete")
def complete_pomodoro_session(
    session_id: int,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Mark a Pomodoro session as completed"""
    session = db.query(models.PomodoroSession).filter(
        models.PomodoroSession.id == session_id,
        models.PomodoroSession.user_id == current_user.id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    session.ended_at = datetime.utcnow()
    session.completed = True

    # Award points for completing Pomodoro
    gamification.award_points(db, current_user.id, "pomodoro_complete",
                             f"Completed {session.duration_minutes} min Pomodoro")

    db.commit()
    db.refresh(session)

    return {"message": "Pomodoro completed!", "session": session}

@app.get("/pomodoro/stats", response_model=schemas.PomodoroStats)
def get_pomodoro_stats(
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get user's Pomodoro statistics"""
    sessions = db.query(models.PomodoroSession).filter(
        models.PomodoroSession.user_id == current_user.id,
        models.PomodoroSession.completed == True
    ).all()

    today = datetime.utcnow().date()
    completed_today = sum(1 for s in sessions if s.ended_at and s.ended_at.date() == today)

    total_sessions = len(sessions)
    total_minutes = sum(s.duration_minutes for s in sessions)
    total_hours = total_minutes / 60

    # Calculate average per day
    if sessions:
        first_session = min(s.started_at for s in sessions)
        days_active = (datetime.utcnow() - first_session).days + 1
        average_per_day = total_sessions / days_active if days_active > 0 else 0
    else:
        average_per_day = 0

    return schemas.PomodoroStats(
        total_sessions=total_sessions,
        total_minutes=total_minutes,
        total_hours=total_hours,
        completed_today=completed_today,
        average_per_day=average_per_day
    )

@app.get("/pomodoro/active")
def get_active_pomodoro(
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get user's current active Pomodoro session"""
    active = db.query(models.PomodoroSession).filter(
        models.PomodoroSession.user_id == current_user.id,
        models.PomodoroSession.completed == False,
        models.PomodoroSession.ended_at.is_(None)
    ).order_by(models.PomodoroSession.started_at.desc()).first()

    if not active:
        return {"active": False, "session": None}

    # Calculate time remaining
    elapsed = (datetime.utcnow() - active.started_at).total_seconds() / 60
    remaining = max(0, active.duration_minutes - elapsed)

    return {
        "active": True,
        "session": active,
        "elapsed_minutes": elapsed,
        "remaining_minutes": remaining
    }

# ============== Video Room Endpoints ==============

@app.post("/video-rooms/create")
def create_video_room(
    circle_id: int,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create or get a video room for a study circle"""
    circle = db.query(models.StudyCircle).filter(
        models.StudyCircle.id == circle_id
    ).first()

    if not circle:
        raise HTTPException(status_code=404, detail="Circle not found")

    # Check if user is a member
    is_member = db.query(models.CircleMember).filter(
        models.CircleMember.circle_id == circle_id,
        models.CircleMember.student_id == current_user.id
    ).first()

    if not is_member:
        raise HTTPException(status_code=403, detail="You must be a circle member")

    # Get or create room
    room = db.query(models.VideoRoom).filter(
        models.VideoRoom.circle_id == circle_id,
        models.VideoRoom.is_active == True
    ).first()

    if not room:
        import uuid
        room = models.VideoRoom(
            circle_id=circle_id,
            room_name=f"SprintConnect-Circle-{circle_id}",
            jitsi_room_id=f"SprintConnect-{circle_id}-{str(uuid.uuid4())[:8]}",
            created_by=current_user.id
        )
        db.add(room)
        db.commit()
        db.refresh(room)

    room.last_used = datetime.utcnow()
    db.commit()

    return {
        "room": room,
        "jitsi_url": f"https://meet.jit.si/{room.room_name}",
        "room_name": room.room_name
    }

@app.get("/video-rooms/{circle_id}")
def get_video_room(
    circle_id: int,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get video room for a circle"""
    room = db.query(models.VideoRoom).filter(
        models.VideoRoom.circle_id == circle_id,
        models.VideoRoom.is_active == True
    ).first()

    if not room:
        return {"exists": False, "room": None}

    return {
        "exists": True,
        "room": room,
        "jitsi_url": f"https://meet.jit.si/{room.room_name}"
    }

# ============== Stress Analysis Endpoints ==============

@app.get("/wellness/stress-analysis", response_model=schemas.StressAnalysis)
def analyze_stress_patterns(
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Analyze user's stress patterns from wellness check-ins"""
    # Get last 30 days of check-ins
    days_ago_30 = datetime.utcnow() - timedelta(days=30)
    checkins = db.query(models.WellnessCheckIn).filter(
        models.WellnessCheckIn.user_id == current_user.id,
        models.WellnessCheckIn.created_at >= days_ago_30
    ).order_by(models.WellnessCheckIn.created_at).all()

    if len(checkins) < 7:
        return schemas.StressAnalysis(
            average_mood=0.0,
            recent_average=0.0,
            trend="insufficient_data",
            low_mood_days_count=0,
            alert=False,
            alert_message="Need at least 7 check-ins for analysis",
            total_checkins=len(checkins)
        )

    # Analyze patterns
    mood_scores = [c.mood_score for c in checkins]
    avg_mood = sum(mood_scores) / len(mood_scores)

    # Recent vs older average
    recent_avg = sum(mood_scores[-7:]) / 7
    older_avg = sum(mood_scores[-14:-7]) / 7 if len(mood_scores) >= 14 else avg_mood

    # Detect trend
    if recent_avg < older_avg - 0.5:
        trend = "declining"
    elif recent_avg > older_avg + 0.5:
        trend = "improving"
    else:
        trend = "stable"

    # Count low mood days
    low_mood_count = sum(1 for score in mood_scores[-7:] if score <= 2)

    # Determine if alert needed
    alert = False
    alert_message = ""

    if trend == "declining" and low_mood_count >= 3:
        alert = True
        alert_message = "We've noticed your mood has been declining. Consider reaching out to a peer supporter."

        # Create notification
        notification = models.Notification(
            user_id=current_user.id,
            title="Wellness Check-In Alert",
            message=alert_message,
            notification_type="alert",
            action_url="/peer-support"
        )
        db.add(notification)
        db.commit()
    elif low_mood_count >= 4:
        alert = True
        alert_message = "You've had several low mood days. Would you like to connect with support?"

    return schemas.StressAnalysis(
        average_mood=avg_mood,
        recent_average=recent_avg,
        trend=trend,
        low_mood_days_count=low_mood_count,
        alert=alert,
        alert_message=alert_message,
        total_checkins=len(checkins)
    )

# ============== Notification Endpoints ==============

@app.get("/notifications", response_model=List[schemas.Notification])
def get_my_notifications(
    limit: int = 20,
    unread_only: bool = False,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get user's notifications"""
    query = db.query(models.Notification).filter(
        models.Notification.user_id == current_user.id
    )

    if unread_only:
        query = query.filter(models.Notification.is_read == False)

    notifications = query.order_by(
        models.Notification.created_at.desc()
    ).limit(limit).all()

    return notifications

@app.post("/notifications/{notification_id}/read")
def mark_notification_read(
    notification_id: int,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Mark a notification as read"""
    notification = db.query(models.Notification).filter(
        models.Notification.id == notification_id,
        models.Notification.user_id == current_user.id
    ).first()

    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    notification.is_read = True
    db.commit()

    return {"message": "Notification marked as read"}

@app.post("/notifications/read-all")
def mark_all_notifications_read(
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Mark all notifications as read"""
    db.query(models.Notification).filter(
        models.Notification.user_id == current_user.id,
        models.Notification.is_read == False
    ).update({"is_read": True})

    db.commit()

    return {"message": "All notifications marked as read"}

# ============== Health Check ==============

@app.get("/")
def root():
    """API health check"""
    return {
        "message": "Sprint Connect API is running!",
        "version": "2.0.0",  # Updated version
        "docs": "/docs",
        "features": [
            "Gamification System",
            "Pomodoro Timer",
            "Video Chat (Jitsi)",
            "Stress Analysis",
            "Notifications"
        ]
    }

@app.get("/health")
def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "database": "connected"
    }
