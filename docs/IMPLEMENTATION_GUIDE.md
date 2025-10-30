# Sprint Connect - New Features Implementation Guide

This guide will help you implement the new features step by step.

## 🎯 What's New

### ✅ Already Implemented

1. **Database Models** - All new tables added to `backend/models.py`:
   - Gamification (points, badges, transactions)
   - Pomodoro sessions
   - Video rooms
   - Study sessions
   - Notifications
   - User engagement tracking

2. **Gamification System** - Complete system in `backend/gamification.py`:
   - Points for actions
   - Badge system
   - Leaderboards
   - Streak tracking

### 🚧 Ready to Implement (Next Steps)

## Feature 1: Jitsi Video Chat Integration 🎥

### What it does:
- One-click video calls in study circles
- No backend needed (uses Jitsi servers)
- Screen sharing, chat built-in

### How to implement:

#### Step 1: Add Jitsi to Frontend

Add this to `frontend/app.py` in the study circles page:

```python
def video_chat_component(circle_id, circle_name):
    """Embed Jitsi video chat"""
    st.markdown("### 📹 Video Chat")

    # Generate unique room name
    room_name = f"SprintConnect-Circle-{circle_id}"

    # Jitsi iframe embed
    jitsi_html = f"""
    <div id="jitsi-container" style="height: 600px;">
        <script src='https://meet.jit.si/external_api.js'></script>
        <script>
            const domain = 'meet.jit.si';
            const options = {{
                roomName: '{room_name}',
                width: '100%',
                height: 600,
                parentNode: document.querySelector('#jitsi-container'),
                configOverrides: {{
                    startWithAudioMuted: true,
                    startWithVideoMuted: false
                }},
                interfaceConfigOverrides: {{
                    TOOLBAR_BUTTONS: [
                        'microphone', 'camera', 'closedcaptions', 'desktop',
                        'fullscreen', 'fodeviceselection', 'hangup', 'chat',
                        'recording', 'etherpad', 'sharedvideo', 'settings',
                        'raisehand', 'videoquality', 'filmstrip', 'stats',
                        'shortcuts', 'tileview'
                    ]
                }}
            }};
            const api = new JitsiMeetExternalAPI(domain, options);
        </script>
    </div>
    """

    st.components.v1.html(jitsi_html, height=650)

# Usage in study circles page:
if st.button("🎥 Start Video Chat"):
    video_chat_component(circle['id'], circle['name'])
```

#### Step 2: Add Backend API endpoint (optional - for tracking)

Add to `backend/main.py`:

```python
@app.post("/video-rooms/create")
def create_video_room(
    circle_id: int,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a video room for a study circle"""
    circle = db.query(models.StudyCircle).filter(
        models.StudyCircle.id == circle_id
    ).first()

    if not circle:
        raise HTTPException(status_code=404, detail="Circle not found")

    # Create or get existing room
    room = db.query(models.VideoRoom).filter(
        models.VideoRoom.circle_id == circle_id,
        models.VideoRoom.is_active == True
    ).first()

    if not room:
        room = models.VideoRoom(
            circle_id=circle_id,
            room_name=f"SprintConnect-Circle-{circle_id}",
            jitsi_room_id=f"SprintConnect-{circle_id}-{datetime.utcnow().timestamp()}",
            created_by=current_user.id
        )
        db.add(room)
        db.commit()
        db.refresh(room)

    room.last_used = datetime.utcnow()
    db.commit()

    return {
        "room_name": room.room_name,
        "jitsi_room_id": room.jitsi_room_id,
        "jitsi_url": f"https://meet.jit.si/{room.room_name}"
    }
```

---

## Feature 2: Gamification System 🏆

### What it does:
- Award points for actions (check-ins, posts, study sessions)
- Unlock badges
- Compete on leaderboards

### How to implement:

#### Step 1: Initialize Badges

Run once to create badges:

```python
# In backend/init_db.py, add:
from backend.gamification import initialize_badges

# After creating demo data:
initialize_badges(db)
```

#### Step 2: Award Points Automatically

Modify existing endpoints in `backend/main.py`:

```python
from backend import gamification

# In create_checkin endpoint:
@app.post("/checkin", response_model=schemas.WellnessCheckIn)
def create_checkin(...):
    # ... existing code ...

    # Award points for check-in
    gamification.award_points(db, current_user.id, "daily_checkin")
    gamification.update_streak(db, current_user.id)

    return db_checkin

# In create_post endpoint:
@app.post("/posts", response_model=schemas.CommunityPost)
def create_post(...):
    # ... existing code ...

    # Award points for creating post
    gamification.award_points(db, current_user.id, "create_post")

    return db_post

# Add new endpoints:
@app.get("/gamification/stats")
def get_my_stats(
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get current user's gamification stats"""
    return gamification.get_user_stats(db, current_user.id)

@app.get("/gamification/leaderboard")
def get_leaderboard(
    limit: int = 10,
    timeframe: str = "all_time",
    db: Session = Depends(get_db)
):
    """Get leaderboard"""
    leaders = gamification.get_leaderboard(db, limit, timeframe)
    return {
        "leaderboard": leaders,
        "timeframe": timeframe
    }

@app.get("/gamification/badges")
def get_all_badges(db: Session = Depends(get_db)):
    """Get all available badges"""
    return db.query(models.Badge).all()

@app.get("/gamification/my-badges")
def get_my_badges(
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get current user's badges"""
    badges = db.query(models.UserBadge).filter(
        models.UserBadge.user_id == current_user.id
    ).all()
    return badges
```

#### Step 3: Add Gamification UI

Add to `frontend/app.py`:

```python
def gamification_page():
    """Gamification dashboard"""
    st.title("🏆 Your Achievements")

    # Get user stats
    stats = make_request("GET", "/gamification/stats")

    if stats:
        # Display stats
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Points", stats['points'])
            st.caption(f"Total earned: {stats['total_points_earned']}")

        with col2:
            st.metric("Level", stats['level'])

        with col3:
            st.metric("Streak", f"{stats['streak_days']} days 🔥")

        with col4:
            st.metric("Rank", f"#{stats['rank']}")
            st.caption(f"out of {stats['total_users']}")

        # Display badges
        st.markdown("### 🎖️ Your Badges")
        badges = make_request("GET", "/gamification/my-badges")

        if badges:
            cols = st.columns(min(len(badges), 4))
            for i, badge_data in enumerate(badges):
                badge = badge_data['badge']
                with cols[i % 4]:
                    st.markdown(f"### {badge['icon']}")
                    st.markdown(f"**{badge['name']}**")
                    st.caption(badge['description'])

        # Leaderboard
        st.markdown("### 📊 Leaderboard")
        timeframe = st.selectbox("Timeframe", ["all_time", "week", "month"])

        leaderboard = make_request("GET", f"/gamification/leaderboard?timeframe={timeframe}")

        if leaderboard:
            for i, entry in enumerate(leaderboard['leaderboard'], 1):
                col_a, col_b, col_c = st.columns([1, 3, 1])
                with col_a:
                    st.write(f"**#{i}**")
                with col_b:
                    st.write(entry['user']['username'])
                with col_c:
                    st.write(f"{entry['points']} pts")
```

---

## Feature 3: Pomodoro Timer ⏱️

### What it does:
- 25-min focus sessions
- 5-min breaks
- Group sync option
- Track study time

### How to implement:

#### Step 1: Add Backend Endpoints

Add to `backend/main.py`:

```python
@app.post("/pomodoro/start")
def start_pomodoro(
    circle_id: int = None,
    duration_minutes: int = 25,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Start a Pomodoro session"""
    session = models.PomodoroSession(
        user_id=current_user.id,
        circle_id=circle_id,
        duration_minutes=duration_minutes,
        started_at=datetime.utcnow(),
        is_group_session=circle_id is not None
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    return session

@app.post("/pomodoro/{session_id}/complete")
def complete_pomodoro(
    session_id: int,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Mark Pomodoro as completed"""
    session = db.query(models.PomodoroSession).filter(
        models.PomodoroSession.id == session_id,
        models.PomodoroSession.user_id == current_user.id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    session.ended_at = datetime.utcnow()
    session.completed = True

    # Award points
    gamification.award_points(db, current_user.id, "pomodoro_complete")

    db.commit()
    return session

@app.get("/pomodoro/stats")
def get_pomodoro_stats(
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get user's Pomodoro statistics"""
    sessions = db.query(models.PomodoroSession).filter(
        models.PomodoroSession.user_id == current_user.id,
        models.PomodoroSession.completed == True
    ).all()

    total_sessions = len(sessions)
    total_minutes = sum(s.duration_minutes for s in sessions)

    return {
        "total_sessions": total_sessions,
        "total_minutes": total_minutes,
        "total_hours": total_minutes / 60
    }
```

#### Step 2: Add Frontend Timer

Add to `frontend/app.py`:

```python
import time

def pomodoro_timer():
    """Pomodoro timer component"""
    st.markdown("### ⏱️ Pomodoro Timer")

    # Timer settings
    col1, col2 = st.columns(2)
    with col1:
        duration = st.selectbox("Duration", [25, 30, 45, 60], index=0)
    with col2:
        break_duration = st.selectbox("Break", [5, 10, 15], index=0)

    # State management
    if 'pomodoro_running' not in st.session_state:
        st.session_state.pomodoro_running = False
        st.session_state.pomodoro_session_id = None

    if st.button("▶️ Start Pomodoro"):
        # Start session
        result = make_request("POST", "/pomodoro/start", {
            "duration_minutes": duration
        })

        if result:
            st.session_state.pomodoro_running = True
            st.session_state.pomodoro_session_id = result['id']
            st.success(f"Started {duration} minute session!")

            # Timer display (simplified - in production use websockets)
            st.info("Focus for 25 minutes... 🎯")

    # Stats
    stats = make_request("GET", "/pomodoro/stats")
    if stats:
        col_a, col_b = st.columns(2)
        with col_a:
            st.metric("Total Sessions", stats['total_sessions'])
        with col_b:
            st.metric("Total Hours", f"{stats['total_hours']:.1f}")
```

---

## Feature 4: Stress Pattern Detection 📊

### How to implement:

Add to `backend/main.py`:

```python
@app.get("/wellness/stress-analysis")
def analyze_stress_patterns(
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Analyze user's stress patterns"""
    # Get last 30 days of check-ins
    days_ago_30 = datetime.utcnow() - timedelta(days=30)
    checkins = db.query(models.WellnessCheckIn).filter(
        models.WellnessCheckIn.user_id == current_user.id,
        models.WellnessCheckIn.created_at >= days_ago_30
    ).order_by(models.WellnessCheckIn.created_at).all()

    if len(checkins) < 7:
        return {"status": "insufficient_data", "message": "Need at least 7 check-ins"}

    # Analyze patterns
    mood_scores = [c.mood_score for c in checkins]
    avg_mood = sum(mood_scores) / len(mood_scores)

    # Detect declining trend
    recent_avg = sum(mood_scores[-7:]) / 7
    older_avg = sum(mood_scores[-14:-7]) / 7 if len(mood_scores) >= 14 else avg_mood

    declining = recent_avg < older_avg - 0.5

    # Count low mood days
    low_mood_count = sum(1 for score in mood_scores[-7:] if score <= 2)

    alert = False
    alert_message = ""

    if declining and low_mood_count >= 3:
        alert = True
        alert_message = "We've noticed your mood has been declining. Consider reaching out to a peer supporter."
    elif low_mood_count >= 4:
        alert = True
        alert_message = "You've had several low mood days. Would you like to connect with support?"

    return {
        "average_mood": avg_mood,
        "recent_average": recent_avg,
        "trend": "declining" if declining else "stable" if recent_avg == older_avg else "improving",
        "low_mood_days_count": low_mood_count,
        "alert": alert,
        "alert_message": alert_message,
        "total_checkins": len(checkins)
    }
```

---

## Next Steps

1. **Run Database Migration**:
   ```bash
   # Delete old database
   rm -rf data/

   # Recreate with new models
   python -m backend.init_db
   ```

2. **Test Each Feature**:
   - Start backend: `uvicorn backend.main:app --reload --port 8000`
   - Start frontend: `streamlit run frontend/app.py`
   - Test gamification, video chat, pomodoro

3. **Add More Features**:
   - Follow the roadmap in FEATURE_ROADMAP.md
   - Implement phase by phase

## Resources

- **Jitsi API Docs**: https://jitsi.github.io/handbook/docs/dev-guide/dev-guide-iframe/
- **Streamlit Components**: https://docs.streamlit.io/library/components
- **FastAPI Docs**: https://fastapi.tiangolo.com/

## Support

If you need help implementing any feature:
1. Check this guide
2. Review the FEATURE_ROADMAP.md
3. Check API docs at http://localhost:8000/docs
4. Create an issue on GitHub

---

**Happy Coding! 🚀**
