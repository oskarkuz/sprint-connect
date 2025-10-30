"""Gamification system for Sprint Connect"""

from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from . import models

# Points configuration
POINTS_CONFIG = {
    "daily_checkin": 10,
    "wellness_streak_bonus": 5,  # Per day in streak
    "create_post": 15,
    "comment": 5,
    "like_post": 1,
    "join_circle": 20,
    "event_rsvp": 10,
    "event_attend": 15,
    "pomodoro_complete": 5,
    "study_session_hour": 10,
    "help_peer": 25,
}

# Badge definitions
BADGES = [
    {
        "name": "First Steps",
        "description": "Complete your first wellness check-in",
        "icon": "👣",
        "category": "wellness",
        "points_required": 10,
        "criteria": {"checkins": 1},
        "rarity": "common"
    },
    {
        "name": "Wellness Warrior",
        "description": "Complete 7 consecutive wellness check-ins",
        "icon": "💪",
        "category": "wellness",
        "points_required": 70,
        "criteria": {"checkin_streak": 7},
        "rarity": "rare"
    },
    {
        "name": "Community Builder",
        "description": "Create 5 community posts",
        "icon": "🏗️",
        "category": "participation",
        "points_required": 75,
        "criteria": {"posts": 5},
        "rarity": "rare"
    },
    {
        "name": "Study Buddy",
        "description": "Join your first study circle",
        "icon": "🎓",
        "category": "achievement",
        "points_required": 20,
        "criteria": {"circles": 1},
        "rarity": "common"
    },
    {
        "name": "Social Butterfly",
        "description": "Join 3 study circles",
        "icon": "🦋",
        "category": "achievement",
        "points_required": 60,
        "criteria": {"circles": 3},
        "rarity": "rare"
    },
    {
        "name": "Time Master",
        "description": "Complete 10 Pomodoro sessions",
        "icon": "⏰",
        "category": "productivity",
        "points_required": 50,
        "criteria": {"pomodoros": 10},
        "rarity": "rare"
    },
    {
        "name": "Marathon Studier",
        "description": "Study for 20 hours total",
        "icon": "📚",
        "category": "productivity",
        "points_required": 200,
        "criteria": {"study_hours": 20},
        "rarity": "epic"
    },
    {
        "name": "Helping Hand",
        "description": "Help 10 peers in study circles",
        "icon": "🤝",
        "category": "participation",
        "points_required": 250,
        "criteria": {"peer_helps": 10},
        "rarity": "epic"
    },
    {
        "name": "Sprint Champion",
        "description": "Reach level 10",
        "icon": "🏆",
        "category": "achievement",
        "points_required": 1000,
        "criteria": {"level": 10},
        "rarity": "legendary"
    },
]

def get_or_create_user_points(db: Session, user_id: int):
    """Get or create gamification points record for user"""
    points = db.query(models.GamificationPoints).filter(
        models.GamificationPoints.user_id == user_id
    ).first()

    if not points:
        points = models.GamificationPoints(user_id=user_id)
        db.add(points)
        db.commit()
        db.refresh(points)

    return points

def award_points(db: Session, user_id: int, action_type: str, description: str = None):
    """Award points to a user for an action"""
    if action_type not in POINTS_CONFIG:
        return None

    points_value = POINTS_CONFIG[action_type]

    # Get user's points record
    user_points = get_or_create_user_points(db, user_id)

    # Create transaction
    transaction = models.PointsTransaction(
        user_id=user_id,
        points=points_value,
        action_type=action_type,
        description=description or action_type.replace("_", " ").title()
    )
    db.add(transaction)

    # Update user's total points
    user_points.points += points_value
    user_points.total_points_earned += points_value
    user_points.last_activity = datetime.utcnow()

    # Calculate new level (every 100 points = 1 level)
    user_points.level = (user_points.total_points_earned // 100) + 1

    db.commit()
    db.refresh(user_points)

    # Check for badge achievements
    check_and_award_badges(db, user_id)

    return user_points

def update_streak(db: Session, user_id: int):
    """Update user's check-in streak"""
    user_points = get_or_create_user_points(db, user_id)

    today = datetime.utcnow().date()
    last_activity = user_points.last_activity.date() if user_points.last_activity else None

    if last_activity:
        # If last activity was yesterday, increment streak
        if (today - last_activity).days == 1:
            user_points.streak_days += 1
            # Award bonus points for streak
            bonus_points = POINTS_CONFIG["wellness_streak_bonus"] * user_points.streak_days
            transaction = models.PointsTransaction(
                user_id=user_id,
                points=bonus_points,
                action_type="wellness_streak_bonus",
                description=f"{user_points.streak_days} day streak bonus!"
            )
            db.add(transaction)
            user_points.points += bonus_points
            user_points.total_points_earned += bonus_points
        # If missed a day, reset streak
        elif (today - last_activity).days > 1:
            user_points.streak_days = 1
    else:
        user_points.streak_days = 1

    user_points.last_activity = datetime.utcnow()
    db.commit()
    db.refresh(user_points)

    return user_points

def initialize_badges(db: Session):
    """Initialize default badges in the database"""
    for badge_data in BADGES:
        existing = db.query(models.Badge).filter(
            models.Badge.name == badge_data["name"]
        ).first()

        if not existing:
            badge = models.Badge(**badge_data)
            db.add(badge)

    db.commit()

def check_and_award_badges(db: Session, user_id: int):
    """Check if user qualifies for any badges and award them"""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        return []

    # Get user's current badges
    current_badges = db.query(models.UserBadge).filter(
        models.UserBadge.user_id == user_id
    ).all()
    current_badge_ids = [ub.badge_id for ub in current_badges]

    # Get all available badges
    all_badges = db.query(models.Badge).all()

    newly_awarded = []

    for badge in all_badges:
        # Skip if user already has this badge
        if badge.id in current_badge_ids:
            continue

        # Check if user meets criteria
        if check_badge_criteria(db, user_id, badge.criteria):
            # Award badge
            user_badge = models.UserBadge(
                user_id=user_id,
                badge_id=badge.id,
                progress=1.0
            )
            db.add(user_badge)
            newly_awarded.append(badge)

            # Create notification
            notification = models.Notification(
                user_id=user_id,
                title=f"New Badge Earned: {badge.icon} {badge.name}!",
                message=badge.description,
                notification_type="achievement"
            )
            db.add(notification)

    if newly_awarded:
        db.commit()

    return newly_awarded

def check_badge_criteria(db: Session, user_id: int, criteria: dict) -> bool:
    """Check if user meets the criteria for a badge"""
    if not criteria:
        return False

    # Check wellness check-ins
    if "checkins" in criteria:
        count = db.query(models.WellnessCheckIn).filter(
            models.WellnessCheckIn.user_id == user_id
        ).count()
        if count < criteria["checkins"]:
            return False

    # Check check-in streak
    if "checkin_streak" in criteria:
        user_points = get_or_create_user_points(db, user_id)
        if user_points.streak_days < criteria["checkin_streak"]:
            return False

    # Check posts
    if "posts" in criteria:
        count = db.query(models.CommunityPost).filter(
            models.CommunityPost.author_id == user_id
        ).count()
        if count < criteria["posts"]:
            return False

    # Check circles
    if "circles" in criteria:
        count = db.query(models.CircleMember).filter(
            models.CircleMember.student_id == user_id
        ).count()
        if count < criteria["circles"]:
            return False

    # Check Pomodoros
    if "pomodoros" in criteria:
        count = db.query(models.PomodoroSession).filter(
            models.PomodoroSession.user_id == user_id,
            models.PomodoroSession.completed == True
        ).count()
        if count < criteria["pomodoros"]:
            return False

    # Check study hours
    if "study_hours" in criteria:
        sessions = db.query(models.StudySession).filter(
            models.StudySession.user_id == user_id,
            models.StudySession.duration_minutes.isnot(None)
        ).all()
        total_hours = sum(s.duration_minutes for s in sessions) / 60
        if total_hours < criteria["study_hours"]:
            return False

    # Check level
    if "level" in criteria:
        user_points = get_or_create_user_points(db, user_id)
        if user_points.level < criteria["level"]:
            return False

    return True

def get_leaderboard(db: Session, limit: int = 10, timeframe: str = "all_time"):
    """Get top users by points"""
    query = db.query(models.GamificationPoints).join(models.User)

    if timeframe == "week":
        week_ago = datetime.utcnow() - timedelta(days=7)
        query = query.filter(models.GamificationPoints.last_activity >= week_ago)
    elif timeframe == "month":
        month_ago = datetime.utcnow() - timedelta(days=30)
        query = query.filter(models.GamificationPoints.last_activity >= month_ago)

    leaderboard = query.order_by(
        models.GamificationPoints.points.desc()
    ).limit(limit).all()

    return leaderboard

def get_user_stats(db: Session, user_id: int):
    """Get comprehensive stats for a user"""
    user_points = get_or_create_user_points(db, user_id)

    # Get badges
    badges = db.query(models.UserBadge).filter(
        models.UserBadge.user_id == user_id
    ).all()

    # Get recent transactions
    transactions = db.query(models.PointsTransaction).filter(
        models.PointsTransaction.user_id == user_id
    ).order_by(models.PointsTransaction.created_at.desc()).limit(10).all()

    # Calculate rank
    total_users = db.query(models.GamificationPoints).count()
    higher_ranked = db.query(models.GamificationPoints).filter(
        models.GamificationPoints.points > user_points.points
    ).count()
    rank = higher_ranked + 1

    return {
        "points": user_points.points,
        "level": user_points.level,
        "total_points_earned": user_points.total_points_earned,
        "streak_days": user_points.streak_days,
        "badges_count": len(badges),
        "rank": rank,
        "total_users": total_users,
        "recent_transactions": transactions,
        "badges": badges
    }
