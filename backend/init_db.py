"""Initialize database with demo data for Sprint Connect"""

from datetime import datetime, timedelta
import random
from . import models
from .database import engine, SessionLocal
from .auth import get_password_hash

# Create all tables
models.Base.metadata.create_all(bind=engine)

# Create session
db = SessionLocal()

def init_demo_data():
    """Initialize database with demo data"""
    print("🚀 Initializing Sprint Connect database...")
    
    # Clear existing data
    db.query(models.EventAttendee).delete()
    db.query(models.Event).delete()
    db.query(models.Comment).delete()
    db.query(models.CommunityPost).delete()
    db.query(models.WellnessCheckIn).delete()
    db.query(models.Resource).delete()
    db.query(models.CircleMember).delete()
    db.query(models.StudyCircle).delete()
    db.query(models.Course).delete()
    db.query(models.PeerSupport).delete()
    db.query(models.StudentProfile).delete()
    db.query(models.User).delete()
    db.commit()
    
    # Create admin user
    admin = models.User(
        email="admin@srh.nl",
        username="admin",
        hashed_password=get_password_hash("admin123"),
        role="admin"
    )
    db.add(admin)
    
    # Create demo students with diverse backgrounds
    students_data = [
        ("Sarah Chen", "sarah@srh.nl", "Singapore", "English", "🎯"),
        ("Max Mueller", "max@srh.nl", "Germany", "German", "🚀"),
        ("Priya Sharma", "priya@srh.nl", "India", "Hindi", "📚"),
        ("João Silva", "joao@srh.nl", "Brazil", "Portuguese", "⚡"),
        ("Emma Johnson", "emma@srh.nl", "USA", "English", "🌟"),
        ("Ahmed Hassan", "ahmed@srh.nl", "Egypt", "Arabic", "💡"),
        ("Maria Garcia", "maria@srh.nl", "Spain", "Spanish", "🎨"),
        ("Li Wei", "li@srh.nl", "China", "Mandarin", "🔬"),
        ("Sophie Dubois", "sophie@srh.nl", "France", "French", "🌍"),
        ("Olaf Petersen", "olaf@srh.nl", "Netherlands", "Dutch", "🎪"),
    ]
    
    students = []
    for i, (name, email, nationality, language, emoji) in enumerate(students_data):
        user = models.User(
            email=email,
            username=email.split("@")[0],
            hashed_password=get_password_hash("demo123"),
            role="student"
        )
        db.add(user)
        db.flush()
        
        profile = models.StudentProfile(
            user_id=user.id,
            full_name=name,
            student_id=f"SRH{2024000 + i + 1}",
            nationality=nationality,
            native_language=language,
            program="Digital Transformation Management",
            year=random.choice([1, 2, 3]),
            bio=f"Passionate about technology and innovation. Excited to be part of SRH Haarlem!",
            interests=random.sample(
                ["Coding", "AI", "Sustainability", "Design", "Entrepreneurship", 
                 "Gaming", "Photography", "Music", "Sports", "Travel"], 
                k=random.randint(3, 5)
            ),
            study_preferences={
                "preferred_times": random.sample(["morning", "afternoon", "evening"], k=2),
                "study_style": random.choice(["visual", "auditory", "kinesthetic"]),
                "group_size": random.choice(["small", "medium"])
            },
            avatar_emoji=emoji
        )
        db.add(profile)
        students.append(user)
    
    # Create courses for current sprint
    courses_data = [
        ("DTM101", "Digital Business Models", 3),
        ("DTM102", "Data Analytics Fundamentals", 3),
        ("DTM201", "AI and Machine Learning", 4),
        ("DTM202", "Agile Project Management", 4),
        ("DTM301", "Innovation Strategy", 5),
    ]
    
    courses = []
    for code, title, sprint in courses_data:
        start_date = datetime.utcnow() - timedelta(days=random.randint(0, 10))
        course = models.Course(
            code=code,
            title=title,
            sprint_number=sprint,
            academic_year="2024-2025",
            start_date=start_date,
            end_date=start_date + timedelta(days=35)  # 5-week sprint
        )
        db.add(course)
        courses.append(course)
    
    db.flush()
    
    # Create study circles
    for course in courses[:3]:  # Active circles for first 3 courses
        for i in range(2):  # 2 circles per course
            circle = models.StudyCircle(
                course_id=course.id,
                name=f"{course.code} Circle {i+1}",
                sprint_id=f"Sprint{course.sprint_number}",
                status="active"
            )
            db.add(circle)
            db.flush()
            
            # Add 3-4 random students to each circle
            num_members = random.randint(3, 4)
            selected_students = random.sample(students, num_members)
            for j, student in enumerate(selected_students):
                member = models.CircleMember(
                    circle_id=circle.id,
                    student_id=student.id,
                    role="leader" if j == 0 else "member",
                    participation_score=random.uniform(0.5, 1.0)
                )
                db.add(member)
    
    # Create wellness check-ins for the past week
    moods = [
        ("😊", 5, "Feeling great!"),
        ("😌", 4, "Pretty good today"),
        ("😐", 3, "Okay, managing"),
        ("😔", 2, "Bit stressed"),
        ("😫", 1, "Really tough day")
    ]
    
    for student in students:
        for days_ago in range(7):
            if random.random() > 0.3:  # 70% chance of check-in
                check_date = datetime.utcnow() - timedelta(days=days_ago)
                mood = random.choice(moods)
                checkin = models.WellnessCheckIn(
                    user_id=student.id,
                    mood_emoji=mood[0],
                    mood_score=mood[1],
                    note=mood[2] if random.random() > 0.5 else None,
                    sprint_week=f"Sprint3_Week{(days_ago // 7) + 1}",
                    created_at=check_date
                )
                db.add(checkin)
    
    # Create community posts
    post_templates = [
        ("Looking for study buddy for Data Analytics", "Hey everyone! Anyone want to team up for the Data Analytics assignment?", "question"),
        ("Coffee at Cupola Café - Sunday 3pm", "Let's meet for coffee and discuss the sprint project! Everyone welcome 🍵", "event"),
        ("5 Tips for Surviving Sprint Week 3", "Here's what I learned about managing stress during intensive sprints...", "tip"),
        ("We did it! Sprint 3 complete! 🎉", "Congratulations everyone on completing another sprint!", "celebration"),
        ("Dutch Language Practice Group", "Starting a weekly Dutch practice session for internationals. Interested?", "event"),
        ("Found: Great YouTube Channel for ML", "Check out this amazing resource for our AI course!", "tip"),
    ]
    
    for title, content, category in post_templates:
        author = random.choice(students)
        post = models.CommunityPost(
            author_id=author.id,
            title=title,
            content=content,
            category=category,
            likes_count=random.randint(0, 25),
            created_at=datetime.utcnow() - timedelta(days=random.randint(0, 5))
        )
        db.add(post)
        db.flush()
        
        # Add some comments
        if random.random() > 0.5:
            for _ in range(random.randint(1, 3)):
                commenter = random.choice(students)
                comment = models.Comment(
                    post_id=post.id,
                    author_id=commenter.id,
                    content=random.choice([
                        "Great idea! Count me in!",
                        "Thanks for sharing!",
                        "This is really helpful 👍",
                        "See you there!",
                        "Interested! DMing you"
                    ])
                )
                db.add(comment)
    
    # Create events
    events_data = [
        ("International Food Festival", "Bring a dish from your home country! Let's celebrate our diversity 🌍", 
         "SRH Cafeteria", datetime.utcnow() + timedelta(days=3)),
        ("Sprint 3 Study Session", "Group study session for all Sprint 3 courses. Snacks provided!",
         "Library Room 201", datetime.utcnow() + timedelta(days=1)),
        ("Weekend Hike to Bloemendaal", "Let's explore Dutch nature! Meeting at Haarlem Station.",
         "Haarlem Central Station", datetime.utcnow() + timedelta(days=5)),
        ("Coding Workshop: FastAPI Basics", "Learn to build APIs with Python FastAPI framework",
         "Computer Lab 3", datetime.utcnow() + timedelta(days=2)),
        ("Mental Health & Wellness Talk", "Tips for managing stress during intensive learning",
         "Auditorium", datetime.utcnow() + timedelta(days=4)),
    ]
    
    for title, desc, location, event_date in events_data:
        creator = random.choice(students)
        event = models.Event(
            creator_id=creator.id,
            title=title,
            description=desc,
            location=location,
            event_date=event_date,
            max_attendees=random.choice([None, 20, 30]),
            attendee_count=0
        )
        db.add(event)
        db.flush()
        
        # Add some RSVPs
        num_attendees = random.randint(2, 8)
        attendees = random.sample(students, num_attendees)
        for attendee in attendees:
            rsvp = models.EventAttendee(
                event_id=event.id,
                user_id=attendee.id
            )
            db.add(rsvp)
            event.attendee_count += 1
    
    # Create some study resources
    circles = db.query(models.StudyCircle).all()
    for circle in circles[:3]:  # Add resources to first 3 circles
        members = db.query(models.CircleMember).filter(
            models.CircleMember.circle_id == circle.id
        ).all()
        
        if members:
            uploader = random.choice(members)
            resource = models.Resource(
                circle_id=circle.id,
                uploaded_by=uploader.student_id,
                title=f"{circle.name} Study Notes",
                description="Comprehensive notes from this week's lectures",
                url="https://docs.google.com/document/example",
                resource_type="note",
                upvotes=random.randint(1, 10)
            )
            db.add(resource)
    
    # Commit all changes
    db.commit()

    # Initialize gamification badges
    print("\n🏆 Initializing gamification system...")
    from .gamification import initialize_badges
    initialize_badges(db)

    # Create gamification points records for all users
    for student in students:
        from .gamification import get_or_create_user_points
        get_or_create_user_points(db, student.id)

    db.commit()

    print("✅ Database initialized successfully!")
    print("\n📝 Demo Accounts:")
    print("Student: sarah@srh.nl / password: demo123")
    print("Admin: admin@srh.nl / password: admin123")
    print("\n🎓 Created:")
    print(f"- {len(students)} students")
    print(f"- {len(courses)} courses")
    print(f"- {db.query(models.StudyCircle).count()} study circles")
    print(f"- {db.query(models.WellnessCheckIn).count()} wellness check-ins")
    print(f"- {db.query(models.CommunityPost).count()} community posts")
    print(f"- {db.query(models.Event).count()} events")
    print(f"- {db.query(models.Badge).count()} badges")
    print("\n🎮 Gamification system ready!")

if __name__ == "__main__":
    try:
        init_demo_data()
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        db.rollback()
    finally:
        db.close()
