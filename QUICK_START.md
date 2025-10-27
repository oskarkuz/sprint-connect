# Quick Start Guide - Sprint Connect

Get up and running in 5 minutes! 🚀

## First Time Setup

### Option 1: Automated Setup (Recommended)

**Windows:**
```bash
setup.bat
```

**macOS/Linux:**
```bash
chmod +x setup.sh
./setup.sh
```

### Option 2: Manual Setup

```bash
# 1. Create virtual environment
python -m venv venv

# 2. Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Initialize database
python init_db.py
```

## Running the Application

You need **TWO terminals** running at the same time:

### Terminal 1 - Backend API
```bash
# Activate venv first
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Start backend
uvicorn main:app --reload --port 8000
```

The API will be available at:
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### Terminal 2 - Frontend
```bash
# Activate venv first (in new terminal)
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Start frontend
streamlit run app.py
```

The app will open automatically at: http://localhost:8501

## Demo Accounts

### Student Account
- **Email**: `sarah@srh.nl`
- **Password**: `demo123`

### Admin Account
- **Email**: `admin@srh.nl`
- **Password**: `admin123`

## Troubleshooting

### "ModuleNotFoundError"
```bash
# Make sure virtual environment is activated and dependencies are installed
pip install -r requirements.txt
```

### "Cannot connect to backend"
- Make sure backend is running on port 8000
- Check Terminal 1 for errors
- Visit http://localhost:8000 to verify backend is running

### "Port already in use"
```bash
# Backend on different port
uvicorn main:app --reload --port 8001

# Frontend on different port
streamlit run app.py --server.port 8502
```

### Database Issues
```bash
# Reset database
rm -rf data/       # On Windows: rmdir /s /q data
python init_db.py
```

## Project Requirements

- **Python**: 3.12 or higher
- **pip**: Latest version
- **OS**: Windows, macOS, or Linux

## What's Included

After setup, you'll have:
- ✅ 10 demo student accounts
- ✅ 5 courses across different sprints
- ✅ 6 active study circles
- ✅ Sample wellness check-ins
- ✅ Community posts and events
- ✅ Fully functional authentication

## Next Steps

1. **Login** with a demo account
2. **Explore** the different pages:
   - Dashboard
   - Study Circles
   - Wellness Check-In
   - Community Hub
   - Events
   - Profile
3. **Test** features:
   - Join a study circle
   - Create a wellness check-in
   - Post in the community
   - RSVP to events
4. **Read** CONTRIBUTING.md if you want to modify code

## Need More Help?

- 📖 Read the full [README.md](README.md)
- 👥 Check [CONTRIBUTING.md](CONTRIBUTING.md) for development
- 🔧 See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for deployment
- 🐛 Report issues on GitHub

---

**Ready to start?** Run the setup script and you're good to go! 🎉
