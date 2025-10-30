"""Sprint Connect - Streamlit Frontend Application"""

import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json

# Page configuration
st.set_page_config(
    page_title="Sprint Connect - SRH Haarlem",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Configuration
API_BASE_URL = "http://localhost:8000"

# Custom CSS for better styling with SRH Haarlem orange branding
st.markdown("""
    <style>
    .main {
        padding-top: 2rem;
    }
    .stButton > button {
        width: 100%;
        background-color: #F97316;
        color: white;
        font-weight: 600;
        border: none;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        background-color: #EA580C;
        transform: translateY(-2px);
        box-shadow: 0 4px 6px rgba(249, 115, 22, 0.3);
    }
    .metric-card {
        background-color: #FFF7ED;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        border-left: 4px solid #F97316;
    }
    .success-message {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #10B981;
        color: white;
        margin-bottom: 1rem;
    }
    .info-message {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #F97316;
        color: white;
        margin-bottom: 1rem;
    }
    h1, h2, h3 {
        color: #EA580C;
    }
    .stSelectbox > div > div {
        border-color: #F97316;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0 0;
        padding: 10px 20px;
        background-color: #FFF7ED;
    }
    .stTabs [aria-selected="true"] {
        background-color: #F97316;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

# Session state initialization
if 'token' not in st.session_state:
    st.session_state.token = None
if 'user' not in st.session_state:
    st.session_state.user = None
if 'active_video_circle' not in st.session_state:
    st.session_state.active_video_circle = None

# Helper functions
def make_request(method, endpoint, data=None, authenticated=True):
    """Make API request with authentication"""
    url = f"{API_BASE_URL}{endpoint}"
    headers = {}
    if authenticated and st.session_state.token:
        headers["Authorization"] = f"Bearer {st.session_state.token}"
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, params=data)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data)
        elif method == "PUT":
            response = requests.put(url, headers=headers, json=data)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers)
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 401:
            st.session_state.token = None
            st.session_state.user = None
            st.error("Session expired. Please login again.")
            st.rerun()
        else:
            st.error(f"Error: {response.status_code} - {response.text}")
            return None
    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot connect to backend. Please make sure the API server is running on port 8000.")
        st.info("Run: `uvicorn backend.main:app --reload --port 8000`")
        return None
    except Exception as e:
        st.error(f"Request failed: {str(e)}")
        return None

def login_form():
    """Display login form"""
    st.title("🎓 Welcome to Sprint Connect")
    st.subheader("Peer Support Platform for SRH Haarlem")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("### Login to Your Account")
        
        with st.form("login_form"):
            email = st.text_input("Email", placeholder="sarah@srh.nl")
            password = st.text_input("Password", type="password", placeholder="Enter password")
            
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                login_button = st.form_submit_button("🔐 Login", use_container_width=True)
            with col_btn2:
                demo_button = st.form_submit_button("👁️ Use Demo Account", use_container_width=True)
            
            if login_button:
                data = {"username": email, "password": password}
                response = requests.post(f"{API_BASE_URL}/token", data=data)
                
                if response.status_code == 200:
                    token_data = response.json()
                    st.session_state.token = token_data["access_token"]
                    st.session_state.user = token_data["user"]
                    st.success("✅ Login successful!")
                    st.rerun()
                else:
                    st.error("❌ Invalid email or password")
            
            if demo_button:
                data = {"username": "sarah@srh.nl", "password": "demo123"}
                response = requests.post(f"{API_BASE_URL}/token", data=data)
                
                if response.status_code == 200:
                    token_data = response.json()
                    st.session_state.token = token_data["access_token"]
                    st.session_state.user = token_data["user"]
                    st.success("✅ Logged in with demo account!")
                    st.rerun()
                else:
                    st.error("❌ Demo account not available. Please run init_db.py first.")
        
        st.markdown("---")
        st.info("**Demo Accounts:**\n- Student: sarah@srh.nl / demo123\n- Admin: admin@srh.nl / admin123")

def display_sidebar():
    """Display sidebar navigation"""
    with st.sidebar:
        st.image("https://via.placeholder.com/300x100/F97316/FFFFFF?text=Sprint+Connect", width=250)
        
        if st.session_state.user:
            st.markdown(f"### 👋 Welcome, {st.session_state.user['username']}!")
            st.markdown(f"**Role:** {st.session_state.user['role'].title()}")

            st.markdown("---")

            # Notifications Section
            notifications_data = make_request("GET", "/notifications")
            if notifications_data:
                unread_count = len([n for n in notifications_data if not n['is_read']])

                if unread_count > 0:
                    st.markdown(f"### 🔔 Notifications ({unread_count})")

                    with st.expander("View Notifications", expanded=False):
                        for notification in notifications_data[:5]:  # Show last 5
                            if not notification['is_read']:
                                st.markdown(f"**{notification['title']}**")
                                st.write(notification['message'])
                                st.caption(notification['created_at'][:16])

                                if st.button("Mark as Read", key=f"read_{notification['id']}"):
                                    make_request("POST", f"/notifications/{notification['id']}/read")
                                    st.rerun()

                                st.markdown("---")

                        if len(notifications_data) > 0:
                            if st.button("Mark All as Read", use_container_width=True):
                                make_request("POST", "/notifications/read-all")
                                st.rerun()
                else:
                    st.markdown("### 🔔 Notifications")
                    st.caption("✅ No new notifications")

            st.markdown("---")

            # Navigation
            st.markdown("###  🧭 Navigation")
            page = st.selectbox(
                "Choose a page",
                ["Dashboard", "Study Circles", "Wellness Check-In", "Community Hub", "Events", "Achievements 🏆", "Pomodoro ⏱️", "Profile"]
            )
            
            if st.button("🚪 Logout", use_container_width=True):
                st.session_state.token = None
                st.session_state.user = None
                st.rerun()
            
            return page
    return None

def dashboard_page():
    """Display main dashboard"""
    st.title("📊 Your Sprint Dashboard")
    
    # Get dashboard data
    dashboard_data = make_request("GET", "/dashboard")
    
    if not dashboard_data:
        return
    
    # Sprint Progress
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Current Sprint", "Sprint 3", "Week 2 of 5")
    
    with col2:
        st.metric("Active Circles", len(dashboard_data.get("active_circles", [])))
    
    with col3:
        checkins = dashboard_data.get("recent_checkins", [])
        if checkins:
            latest = checkins[0]
            st.metric("Today's Mood", latest.get("mood_emoji", "😐"), f"Score: {latest.get('mood_score', 0)}/5")
        else:
            st.metric("Today's Mood", "Not checked in", "Check in now →")
    
    with col4:
        st.metric("Upcoming Events", len(dashboard_data.get("upcoming_events", [])))
    
    st.markdown("---")
    
    # Main content area
    col_left, col_right = st.columns([2, 1])
    
    with col_left:
        # Study Circles
        st.markdown("### 📚 Your Study Circles")
        circles = dashboard_data.get("active_circles", [])
        
        if circles:
            for circle in circles:
                with st.expander(f"🔵 {circle['name']}", expanded=True):
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.write(f"**Sprint:** {circle['sprint_id']}")
                        st.write(f"**Status:** {circle['status'].title()}")
                    with col_b:
                        st.button(f"Enter Circle Room →", key=f"circle_{circle['id']}")
        else:
            st.info("You're not in any study circles yet. Join one to start collaborating!")
        
        # Community Feed
        st.markdown("### 🌍 Community Activity")
        posts = dashboard_data.get("community_posts", [])[:5]
        
        for post in posts:
            with st.container():
                st.markdown(f"**{post['title']}**")
                st.write(post['content'][:150] + "..." if len(post['content']) > 150 else post['content'])
                st.caption(f"Category: {post['category']} | 👍 {post['likes_count']} likes")
                st.markdown("---")
    
    with col_right:
        # Wellness Trend
        st.markdown("### 💚 Your Wellness Trend")
        
        checkins = dashboard_data.get("recent_checkins", [])
        if checkins:
            # Create mood trend chart
            df_checkins = pd.DataFrame(checkins)
            df_checkins['created_at'] = pd.to_datetime(df_checkins['created_at'])
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df_checkins['created_at'],
                y=df_checkins['mood_score'],
                mode='lines+markers',
                line=dict(color='#10B981', width=2),
                marker=dict(size=8),
                fill='tozeroy',
                fillcolor='rgba(16, 185, 129, 0.1)'
            ))
            
            fig.update_layout(
                title="7-Day Mood Trend",
                xaxis_title="Date",
                yaxis_title="Mood Score",
                yaxis=dict(range=[0, 6]),
                height=300,
                showlegend=False
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Start tracking your wellness to see trends!")
        
        # Upcoming Events
        st.markdown("### 📅 Upcoming Events")
        events = dashboard_data.get("upcoming_events", [])[:3]
        
        for event in events:
            event_date = datetime.fromisoformat(event['event_date'])
            st.markdown(f"**{event['title']}**")
            st.caption(f"📍 {event['location']}")
            st.caption(f"🕐 {event_date.strftime('%b %d, %I:%M %p')}")
            st.markdown("---")

def study_circles_page():
    """Study Circles management page"""
    st.title("📚 Study Circles")
    
    tab1, tab2, tab3 = st.tabs(["My Circles", "Find Circles", "Resources"])
    
    with tab1:
        st.markdown("### Your Active Study Circles")
        
        # Get user's circles
        dashboard_data = make_request("GET", "/dashboard")
        if dashboard_data:
            circles = dashboard_data.get("active_circles", [])
            
            if circles:
                for circle in circles:
                    with st.expander(f"📘 {circle['name']}", expanded=True):
                        # Get circle members
                        members = make_request("GET", f"/study-circles/{circle['id']}/members")
                        
                        if members:
                            st.markdown("**Circle Members:**")
                            cols = st.columns(len(members))
                            
                            for i, member in enumerate(members):
                                with cols[i]:
                                    profile = member.get('profile', {})
                                    if profile:
                                        st.markdown(f"**{profile.get('avatar_emoji', '🎓')} {profile.get('full_name', 'Unknown')}**")
                                        st.caption(f"{profile.get('nationality', 'Unknown')}")
                                        st.caption(f"Role: {member['role']}")
                        
                        st.markdown("---")
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.button("💬 Group Chat", key=f"chat_{circle['id']}", use_container_width=True)
                        with col2:
                            if st.button("📹 Video Room", key=f"video_{circle['id']}", use_container_width=True):
                                st.session_state.active_video_circle = circle['id']
                                st.rerun()
                        with col3:
                            st.button("📁 Resources", key=f"resources_{circle['id']}", use_container_width=True)

                        # Show video chat if this circle is selected
                        if st.session_state.active_video_circle == circle['id']:
                            st.markdown("---")
                            video_chat_component(circle['id'], circle['name'])
                            if st.button("❌ Close Video Room", key=f"close_video_{circle['id']}", use_container_width=True):
                                st.session_state.active_video_circle = None
                                st.rerun()
            else:
                st.info("You haven't joined any study circles yet. Check the 'Find Circles' tab to get started!")
    
    with tab2:
        st.markdown("### Find and Join Study Circles")
        
        # Get available courses
        courses = make_request("GET", "/courses")
        
        if courses:
            selected_course = st.selectbox(
                "Select a course",
                options=[(c['id'], f"{c['code']} - {c['title']}") for c in courses],
                format_func=lambda x: x[1]
            )
            
            if selected_course:
                st.markdown("### Study Preferences")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    study_style = st.selectbox(
                        "Your learning style",
                        ["visual", "auditory", "kinesthetic"]
                    )
                    
                    preferred_times = st.multiselect(
                        "Preferred study times",
                        ["morning", "afternoon", "evening"]
                    )
                
                with col2:
                    group_size = st.selectbox(
                        "Group size preference",
                        ["small", "medium", "large"]
                    )
                    
                    goals = st.selectbox(
                        "Your goals",
                        ["top_grades", "pass", "deep_understanding"]
                    )
                
                if st.button("🎯 Find My Perfect Circle", use_container_width=True):
                    # Prepare matching request
                    matching_data = {
                        "course_id": selected_course[0],
                        "preferences": {
                            "preferred_times": preferred_times or ["afternoon"],
                            "study_style": study_style,
                            "group_size_preference": group_size,
                            "goals": goals
                        }
                    }
                    
                    # Make matching request
                    result = make_request("POST", "/study-circles/match", matching_data)
                    
                    if result:
                        st.success(f"✅ Successfully matched to {result['name']}!")
                        st.balloons()
                        st.rerun()
    
    with tab3:
        st.markdown("### Study Resources Library")
        st.info("📚 Access shared notes, flashcards, and study guides from your circles")
        
        # This would show resources from user's circles
        if circles:
            for circle in circles[:1]:  # Show resources from first circle as demo
                st.markdown(f"**{circle['name']} Resources:**")
                
                # Demo resources
                resources = [
                    {"title": "Week 2 Lecture Notes", "type": "📝 Notes", "upvotes": 12},
                    {"title": "Practice Quiz Questions", "type": "❓ Quiz", "upvotes": 8},
                    {"title": "Concept Mind Map", "type": "🗺️ Visual", "upvotes": 15}
                ]
                
                for resource in resources:
                    col1, col2, col3 = st.columns([3, 1, 1])
                    with col1:
                        st.write(f"{resource['type']} **{resource['title']}**")
                    with col2:
                        st.write(f"👍 {resource['upvotes']}")
                    with col3:
                        st.button("View", key=f"view_{resource['title']}")

def wellness_checkin_page():
    """Wellness check-in page"""
    st.title("💚 Wellness Check-In")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("### How are you feeling today?")
        
        # Mood selection
        mood_options = {
            "😊": (5, "Great!"),
            "😌": (4, "Good"),
            "😐": (3, "Okay"),
            "😔": (2, "Not great"),
            "😫": (1, "Struggling")
        }
        
        selected_mood = st.radio(
            "Select your mood",
            options=list(mood_options.keys()),
            format_func=lambda x: f"{x} {mood_options[x][1]}",
            horizontal=True
        )
        
        # Optional note
        note = st.text_area("Any thoughts to share? (optional)", max_chars=200)
        
        if st.button("✅ Submit Check-In", use_container_width=True):
            checkin_data = {
                "mood_emoji": selected_mood,
                "mood_score": mood_options[selected_mood][0],
                "note": note if note else None,
                "sprint_week": "Sprint3_Week2"
            }
            
            result = make_request("POST", "/checkin", checkin_data)
            
            if result:
                st.success("✅ Check-in recorded! Keep up the great work! 💪")
                st.balloons()
                st.rerun()
    
    with col2:
        st.markdown("### Your Wellness Journey")
        
        # Get wellness stats
        stats = make_request("GET", "/wellness/stats")
        
        if stats:
            col_a, col_b, col_c = st.columns(3)
            
            with col_a:
                st.metric("Check-in Streak", f"{stats['streak']} days 🔥")
            
            with col_b:
                avg_mood = stats['average_mood']
                mood_emoji = "😊" if avg_mood >= 4 else "😌" if avg_mood >= 3 else "😐" if avg_mood >= 2 else "😔"
                st.metric("Average Mood", f"{mood_emoji} {avg_mood:.1f}/5")
            
            with col_c:
                trend = stats['trend']
                trend_emoji = "📈" if trend == "improving" else "📉" if trend == "declining" else "➡️"
                st.metric("Trend", f"{trend_emoji} {trend.title()}")
        
        # Get recent check-ins for chart
        checkins = make_request("GET", "/checkins", {"days": 14})
        
        if checkins:
            df = pd.DataFrame(checkins)
            df['created_at'] = pd.to_datetime(df['created_at'])
            
            # Create mood chart
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=df['created_at'],
                y=df['mood_score'],
                mode='lines+markers',
                name='Mood',
                line=dict(color='#10B981', width=3),
                marker=dict(size=10),
                fill='tozeroy',
                fillcolor='rgba(16, 185, 129, 0.2)'
            ))
            
            # Add emoji annotations
            for _, row in df.iterrows():
                fig.add_annotation(
                    x=row['created_at'],
                    y=row['mood_score'],
                    text=row['mood_emoji'],
                    showarrow=False,
                    font=dict(size=20)
                )
            
            fig.update_layout(
                title="Your 14-Day Mood Trend",
                xaxis_title="Date",
                yaxis_title="Mood Score",
                yaxis=dict(range=[0, 6]),
                height=400,
                hovermode='x unified'
            )
            
            st.plotly_chart(fig, use_container_width=True)

        # Stress Analysis Section
        st.markdown("### 🧠 Stress Pattern Analysis")

        stress_analysis = make_request("GET", "/wellness/stress-analysis")

        if stress_analysis:
            if stress_analysis.get('alert'):
                st.warning(f"⚠️ {stress_analysis['alert_message']}")

                # Show detailed analysis
                with st.expander("📊 View Detailed Analysis", expanded=True):
                    col_x, col_y, col_z = st.columns(3)

                    with col_x:
                        st.metric("Average Mood", f"{stress_analysis['average_mood']:.1f}/5")

                    with col_y:
                        st.metric("Recent Average", f"{stress_analysis['recent_average']:.1f}/5")

                    with col_z:
                        trend_emoji = "📉" if stress_analysis['trend'] == "declining" else "📈" if stress_analysis['trend'] == "improving" else "➡️"
                        st.metric("Trend", f"{trend_emoji} {stress_analysis['trend'].title()}")

                    st.info(f"We've analyzed {stress_analysis['total_checkins']} check-ins from the past 30 days.")

                    if stress_analysis['low_mood_days_count'] > 0:
                        st.warning(f"You've had {stress_analysis['low_mood_days_count']} days with mood below 2/5 in the last 30 days.")
            else:
                st.success("✅ Your mood patterns look healthy! Keep up the great work!")

                col_a, col_b = st.columns(2)
                with col_a:
                    st.metric("Trend", f"📈 {stress_analysis['trend'].title()}")
                with col_b:
                    st.metric("Average Mood", f"{stress_analysis['average_mood']:.1f}/5")

        # Peer support section
        st.markdown("### 🤝 Peer Support")
        st.info("Feeling overwhelmed? Our trained peer supporters are here to help!")
        
        if st.button("Connect with a Peer Supporter", use_container_width=True):
            st.success("✅ A peer supporter will reach out to you soon!")

def community_hub_page():
    """Community Hub page"""
    st.title("🌍 Community Hub")
    
    tab1, tab2, tab3 = st.tabs(["Feed", "Create Post", "Cultural Calendar"])
    
    with tab1:
        st.markdown("### Community Feed")
        
        # Filter options
        category_filter = st.selectbox(
            "Filter by category",
            ["all", "event", "question", "tip", "celebration"]
        )
        
        # Get posts
        params = {"limit": 20}
        if category_filter != "all":
            params["category"] = category_filter
        
        posts = make_request("GET", "/posts", params)
        
        if posts:
            for post in posts:
                with st.container():
                    col1, col2 = st.columns([10, 1])
                    
                    with col1:
                        author = post.get('author', {})
                        author_name = author.get('username', 'Unknown')
                        
                        st.markdown(f"### {post['title']}")
                        st.write(post['content'])
                        
                        created_at = datetime.fromisoformat(post['created_at'])
                        st.caption(f"Posted by **{author_name}** • {created_at.strftime('%b %d, %I:%M %p')} • {post['category']}")
                    
                    with col2:
                        if st.button(f"👍 {post['likes_count']}", key=f"like_{post['id']}"):
                            make_request("POST", f"/posts/{post['id']}/like")
                            st.rerun()
                    
                    # Comments section
                    with st.expander(f"💬 Comments ({len(post.get('comments', []))})"):
                        comments = post.get('comments', [])
                        for comment in comments:
                            comment_author = comment.get('author', {})
                            st.write(f"**{comment_author.get('username', 'Unknown')}:** {comment['content']}")
                        
                        # Add comment
                        new_comment = st.text_input("Add a comment", key=f"comment_input_{post['id']}")
                        if st.button("Post Comment", key=f"comment_btn_{post['id']}"):
                            if new_comment:
                                make_request("POST", f"/posts/{post['id']}/comment", {"content": new_comment})
                                st.rerun()
                    
                    st.markdown("---")
    
    with tab2:
        st.markdown("### Create a New Post")
        
        with st.form("create_post"):
            title = st.text_input("Title")
            content = st.text_area("Content", height=150)
            category = st.selectbox(
                "Category",
                ["general", "event", "question", "tip", "celebration"]
            )
            
            if st.form_submit_button("📝 Post", use_container_width=True):
                if title and content:
                    post_data = {
                        "title": title,
                        "content": content,
                        "category": category
                    }
                    
                    result = make_request("POST", "/posts", post_data)
                    
                    if result:
                        st.success("✅ Post created successfully!")
                        st.rerun()
                else:
                    st.error("Please fill in all fields")
    
    with tab3:
        st.markdown("### 🌍 Cultural Calendar")
        st.info("Celebrating our diverse community!")
        
        # Display cultural holidays (demo data)
        holidays = [
            {"date": "Oct 31", "holiday": "Diwali", "country": "🇮🇳 India", "desc": "Festival of Lights"},
            {"date": "Nov 11", "holiday": "St. Martin's Day", "country": "🇳🇱 Netherlands", "desc": "Lantern processions"},
            {"date": "Nov 23", "holiday": "Thanksgiving", "country": "🇺🇸 USA", "desc": "Gratitude celebration"},
            {"date": "Dec 25", "holiday": "Christmas", "country": "🌍 Multiple", "desc": "Christian holiday"},
        ]
        
        for holiday in holidays:
            col1, col2, col3 = st.columns([1, 2, 3])
            with col1:
                st.markdown(f"**{holiday['date']}**")
            with col2:
                st.markdown(f"**{holiday['holiday']}**")
                st.caption(holiday['country'])
            with col3:
                st.write(holiday['desc'])
            st.markdown("---")

def events_page():
    """Events page"""
    st.title("📅 Events")
    
    tab1, tab2 = st.tabs(["Upcoming Events", "Create Event"])
    
    with tab1:
        st.markdown("### Upcoming Events")
        
        events = make_request("GET", "/events")
        
        if events:
            for event in events:
                with st.expander(f"📍 {event['title']}", expanded=True):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.write(event.get('description', 'No description'))
                        event_date = datetime.fromisoformat(event['event_date'])
                        st.write(f"**📅 Date:** {event_date.strftime('%B %d, %Y at %I:%M %p')}")
                        st.write(f"**📍 Location:** {event.get('location', 'TBA')}")
                        
                        creator = event.get('creator', {})
                        st.write(f"**👤 Organized by:** {creator.get('username', 'Unknown')}")
                    
                    with col2:
                        st.metric("Attendees", f"{event['attendee_count']}/{event.get('max_attendees', '∞')}")
                        
                        if st.button(f"✅ RSVP", key=f"rsvp_{event['id']}", use_container_width=True):
                            result = make_request("POST", f"/events/{event['id']}/rsvp")
                            if result:
                                st.success("✅ RSVP successful!")
                                st.rerun()
        else:
            st.info("No upcoming events. Create one!")
    
    with tab2:
        st.markdown("### Create a New Event")
        
        with st.form("create_event"):
            title = st.text_input("Event Title")
            description = st.text_area("Description")
            location = st.text_input("Location")
            
            col1, col2 = st.columns(2)
            with col1:
                event_date = st.date_input("Date", min_value=datetime.now().date())
            with col2:
                event_time = st.time_input("Time")
            
            max_attendees = st.number_input("Max Attendees (0 for unlimited)", min_value=0, value=0)
            
            if st.form_submit_button("📅 Create Event", use_container_width=True):
                if title and event_date and event_time:
                    event_datetime = datetime.combine(event_date, event_time)
                    
                    event_data = {
                        "title": title,
                        "description": description,
                        "location": location,
                        "event_date": event_datetime.isoformat(),
                        "max_attendees": max_attendees if max_attendees > 0 else None
                    }
                    
                    result = make_request("POST", "/events", event_data)
                    
                    if result:
                        st.success("✅ Event created successfully!")
                        st.rerun()
                else:
                    st.error("Please fill in required fields")

def profile_page():
    """Profile management page"""
    st.title("👤 Your Profile")
    
    # Get current profile
    user_data = make_request("GET", "/me")
    
    if user_data:
        profile = user_data.get('profile', {})
        
        with st.form("update_profile"):
            st.markdown("### Personal Information")
            
            col1, col2 = st.columns(2)
            
            with col1:
                full_name = st.text_input("Full Name", value=profile.get('full_name', ''))
                nationality = st.text_input("Nationality", value=profile.get('nationality', ''))
                native_language = st.text_input("Native Language", value=profile.get('native_language', ''))
            
            with col2:
                program = st.text_input("Program", value=profile.get('program', ''))
                year = st.number_input("Year", min_value=1, max_value=4, value=profile.get('year', 1))
                avatar_emoji = st.text_input("Avatar Emoji", value=profile.get('avatar_emoji', '🎓'))
            
            bio = st.text_area("Bio", value=profile.get('bio', ''), max_chars=500)
            
            interests_text = ', '.join(profile.get('interests', []))
            interests = st.text_input("Interests (comma-separated)", value=interests_text)
            
            st.markdown("### Study Preferences")
            
            prefs = profile.get('study_preferences', {})
            
            col3, col4 = st.columns(2)
            
            with col3:
                preferred_times = st.multiselect(
                    "Preferred Study Times",
                    ["morning", "afternoon", "evening"],
                    default=prefs.get('preferred_times', [])
                )
                
                study_style = st.selectbox(
                    "Learning Style",
                    ["visual", "auditory", "kinesthetic"],
                    index=["visual", "auditory", "kinesthetic"].index(prefs.get('study_style', 'visual'))
                )
            
            with col4:
                group_size = st.selectbox(
                    "Group Size Preference",
                    ["small", "medium", "large"],
                    index=["small", "medium", "large"].index(prefs.get('group_size', 'medium'))
                )
            
            if st.form_submit_button("💾 Update Profile", use_container_width=True):
                profile_data = {
                    "full_name": full_name,
                    "nationality": nationality,
                    "native_language": native_language,
                    "program": program,
                    "year": year,
                    "bio": bio,
                    "interests": [i.strip() for i in interests.split(',') if i.strip()],
                    "study_preferences": {
                        "preferred_times": preferred_times,
                        "study_style": study_style,
                        "group_size": group_size
                    },
                    "avatar_emoji": avatar_emoji
                }
                
                result = make_request("POST", "/profile", profile_data)
                
                if result:
                    st.success("✅ Profile updated successfully!")
                    st.rerun()

# ============== New Features Pages ==============

def achievements_page():
    """Gamification and achievements page"""
    st.title("🏆 Achievements & Leaderboard")

    # Get user stats
    stats = make_request("GET", "/gamification/stats")

    if stats:
        # Display user stats at top
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Points", stats['points'])
            st.caption(f"Total earned: {stats['total_points_earned']}")

        with col2:
            st.metric("Level", stats['level'], f"🎯")

        with col3:
            st.metric("Streak", f"{stats['streak_days']} days", "🔥")

        with col4:
            st.metric("Rank", f"#{stats['rank']}", f"of {stats['total_users']}")

        st.markdown("---")

        # Tabs for badges, leaderboard, and history
        tab1, tab2, tab3 = st.tabs(["🎖️ My Badges", "📊 Leaderboard", "📜 Points History"])

        with tab1:
            st.markdown("### Your Badges")

            my_badges = make_request("GET", "/gamification/my-badges")
            all_badges = make_request("GET", "/gamification/badges")

            if my_badges:
                st.success(f"You've earned {len(my_badges)} badges!")

                # Display earned badges
                cols = st.columns(min(len(my_badges), 3))
                for i, badge_data in enumerate(my_badges):
                    badge = badge_data['badge']
                    with cols[i % 3]:
                        st.markdown(f"## {badge['icon']}")
                        st.markdown(f"**{badge['name']}**")
                        st.caption(badge['description'])
                        st.caption(f"✨ {badge['rarity'].title()}")
                        st.caption(f"Earned: {badge_data['earned_at'][:10]}")
            else:
                st.info("No badges earned yet. Keep participating to unlock badges!")

            # Show available badges
            st.markdown("### Available Badges")
            if all_badges:
                earned_badge_ids = [b['badge']['id'] for b in my_badges] if my_badges else []

                for badge in all_badges:
                    if badge['id'] not in earned_badge_ids:
                        col_a, col_b = st.columns([1, 4])
                        with col_a:
                            st.markdown(f"### {badge['icon']}")
                        with col_b:
                            st.markdown(f"**{badge['name']}** - {badge['rarity'].title()}")
                            st.caption(badge['description'])
                            st.progress(0, text="Not earned yet")

        with tab2:
            st.markdown("### Leaderboard")

            timeframe = st.selectbox("Timeframe", ["all_time", "week", "month"], format_func=lambda x: x.replace("_", " ").title())

            leaderboard_data = make_request("GET", f"/gamification/leaderboard?timeframe={timeframe}&limit=20")

            if leaderboard_data:
                st.markdown(f"**Top Students - {timeframe.replace('_', ' ').title()}**")

                for entry in leaderboard_data['leaderboard']:
                    col_rank, col_user, col_level, col_points = st.columns([1, 3, 1, 2])

                    with col_rank:
                        if entry['rank'] == 1:
                            st.markdown("### 🥇")
                        elif entry['rank'] == 2:
                            st.markdown("### 🥈")
                        elif entry['rank'] == 3:
                            st.markdown("### 🥉")
                        else:
                            st.write(f"**#{entry['rank']}**")

                    with col_user:
                        st.write(entry['username'])

                    with col_level:
                        st.write(f"Lvl {entry['level']}")

                    with col_points:
                        st.write(f"**{entry['points']} pts**")

                    st.markdown("---")

        with tab3:
            st.markdown("### Points History")

            transactions = make_request("GET", "/gamification/transactions?limit=30")

            if transactions:
                for trans in transactions:
                    col_desc, col_pts, col_date = st.columns([3, 1, 2])

                    with col_desc:
                        st.write(f"**{trans['description']}**")

                    with col_pts:
                        color = "green" if trans['points'] > 0 else "red"
                        st.markdown(f":{color}[+{trans['points']} pts]" if trans['points'] > 0 else f":{color}[{trans['points']} pts]")

                    with col_date:
                        st.caption(trans['created_at'][:16])
            else:
                st.info("No transactions yet. Start participating to earn points!")

def pomodoro_page():
    """Pomodoro timer page"""
    st.title("⏱️ Pomodoro Timer")

    # Get stats first
    stats = make_request("GET", "/pomodoro/stats")

    if stats:
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Sessions", stats['total_sessions'])

        with col2:
            st.metric("Total Hours", f"{stats['total_hours']:.1f}h")

        with col3:
            st.metric("Today", stats['completed_today'])

        with col4:
            st.metric("Avg/Day", f"{stats['average_per_day']:.1f}")

    st.markdown("---")

    # Check for active session
    active_session_data = make_request("GET", "/pomodoro/active")

    if active_session_data and active_session_data.get('active'):
        # Show active timer
        session = active_session_data['session']
        remaining = active_session_data['remaining_minutes']

        st.success(f"⏰ Session in progress!")

        # Display timer
        minutes_left = int(remaining)
        st.markdown(f"## {minutes_left} minutes remaining")

        progress = 1 - (remaining / session['duration_minutes'])
        st.progress(progress)

        if st.button("✅ Complete Session"):
            result = make_request("POST", f"/pomodoro/{session['id']}/complete")
            if result:
                st.success("🎉 Pomodoro completed! +5 points earned!")
                st.balloons()
                st.rerun()

    else:
        # Start new timer
        st.markdown("### Start New Pomodoro Session")

        col_a, col_b = st.columns(2)

        with col_a:
            duration = st.selectbox("Work Duration (minutes)", [25, 30, 45, 60], index=0)

        with col_b:
            break_duration = st.selectbox("Break Duration (minutes)", [5, 10, 15], index=0)

        # Option to sync with circle
        circles_data = make_request("GET", "/dashboard")
        circles = circles_data.get('active_circles', []) if circles_data else []

        if circles:
            sync_with_circle = st.checkbox("Sync with study circle (group Pomodoro)")

            if sync_with_circle:
                selected_circle = st.selectbox(
                    "Select Circle",
                    options=[(c['id'], c['name']) for c in circles],
                    format_func=lambda x: x[1]
                )
                circle_id = selected_circle[0]
            else:
                circle_id = None
        else:
            circle_id = None

        if st.button("▶️ Start Pomodoro", use_container_width=True):
            session_data = {
                "duration_minutes": duration,
                "break_minutes": break_duration,
                "circle_id": circle_id,
                "is_group_session": circle_id is not None
            }

            result = make_request("POST", "/pomodoro/start", session_data)

            if result:
                st.success(f"✅ Started {duration} minute Pomodoro session!")
                st.info("💡 Stay focused! You'll earn 5 points when you complete the session.")
                st.rerun()

    # Tips section
    st.markdown("---")
    st.markdown("### 📚 Pomodoro Tips")
    st.info("""
    **How it works:**
    1. ⏱️ Work for 25 minutes (or your chosen duration)
    2. ☕ Take a 5 minute break
    3. 🔁 Repeat 4 times, then take a longer break

    **Tips for success:**
    - Remove distractions before starting
    - Use breaks to rest your eyes
    - Track your progress over time
    - Sync with study circles for group accountability
    """)

def video_chat_component(circle_id, circle_name):
    """Jitsi video chat component"""
    st.markdown("### 📹 Video Chat Room")

    # Get or create room
    room_data = make_request("POST", f"/video-rooms/create?circle_id={circle_id}")

    if room_data:
        room_name = room_data['room_name']
        jitsi_url = room_data['jitsi_url']

        st.info(f"**Room:** {room_name}")

        # Jitsi iframe embed
        jitsi_html = f"""
        <div id="jitsi-container" style="height: 600px; width: 100%;">
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
                        startWithVideoMuted: false,
                        prejoinPageEnabled: false
                    }},
                    interfaceConfigOverrides: {{
                        TOOLBAR_BUTTONS: [
                            'microphone', 'camera', 'closedcaptions', 'desktop',
                            'fullscreen', 'fodeviceselection', 'hangup', 'chat',
                            'raisehand', 'videoquality', 'filmstrip', 'tileview'
                        ],
                        SHOW_JITSI_WATERMARK: false
                    }}
                }};
                const api = new JitsiMeetExternalAPI(domain, options);
            </script>
        </div>
        """

        st.components.v1.html(jitsi_html, height=650)

        st.caption("💡 Click 'Join' to enter the video room with your study circle members")
        st.caption(f"🔗 Share this link: {jitsi_url}")

# Main app logic
def main():
    if not st.session_state.token:
        login_form()
    else:
        page = display_sidebar()
        
        if page == "Dashboard":
            dashboard_page()
        elif page == "Study Circles":
            study_circles_page()
        elif page == "Wellness Check-In":
            wellness_checkin_page()
        elif page == "Community Hub":
            community_hub_page()
        elif page == "Events":
            events_page()
        elif page == "Achievements 🏆":
            achievements_page()
        elif page == "Pomodoro ⏱️":
            pomodoro_page()
        elif page == "Profile":
            profile_page()

if __name__ == "__main__":
    main()
