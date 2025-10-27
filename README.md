# Sprint Connect

A peer support platform designed for SRH Haarlem's 5-week sprint system, helping students connect, collaborate, and support each other through their academic journey.

## Features

- **Study Circles**: Smart matching system to find study partners with similar preferences
- **Wellness Check-ins**: Daily mood tracking and wellness monitoring
- **Community Hub**: Share tips, ask questions, and celebrate achievements
- **Events**: Organize and join student events
- **Cultural Calendar**: Celebrate diverse backgrounds and holidays
- **Peer Support**: Connect with trained peer supporters

## Tech Stack

- **Backend**: FastAPI (Python)
- **Frontend**: Streamlit
- **Database**: SQLite (easy to get started, no setup needed)
- **Authentication**: JWT tokens with OAuth2

## Prerequisites

- Python 3.12 or higher
- pip (Python package manager)
- Git

## Quick Start

### Option 1: Automated Setup (Recommended)

**Windows:**
```bash
cd scripts
setup.bat
```

**macOS/Linux:**
```bash
cd scripts
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
python -m backend.init_db
```

## Running the Application

You need **TWO terminals** running at the same time:

### Terminal 1 - Backend API
```bash
# Activate venv first
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Start backend
uvicorn backend.main:app --reload --port 8000
```

The API will be available at:
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### Terminal 2 - Frontend
```bash
# Activate venv first (in new terminal)
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Start frontend
streamlit run frontend/app.py
```

The app will open automatically at: http://localhost:8501

## Demo Accounts

After running setup, you can login with:

- **Student Account**:
  - Email: `sarah@srh.nl`
  - Password: `demo123`

- **Admin Account**:
  - Email: `admin@srh.nl`
  - Password: `admin123`

## Project Structure

```
sprint-connect/
├── backend/                 # FastAPI backend
│   ├── __init__.py         # Package initializer
│   ├── main.py             # FastAPI application & routes
│   ├── models.py           # SQLAlchemy database models
│   ├── schemas.py          # Pydantic schemas for validation
│   ├── auth.py             # Authentication & authorization
│   ├── database.py         # Database configuration
│   └── init_db.py          # Database initialization with demo data
│
├── frontend/               # Streamlit frontend
│   └── app.py              # Streamlit application & UI
│
├── docs/                   # Documentation
│   ├── QUICK_START.md      # Quick start guide
│   ├── CONTRIBUTING.md     # Developer contribution guide
│   └── DEPLOYMENT_GUIDE.md # Deployment instructions
│
├── scripts/                # Automation scripts
│   ├── setup.sh            # Unix setup script
│   ├── setup.bat           # Windows setup script
│   └── start.bat           # Windows quick start
│
├── data/                   # Database storage (auto-created)
│   └── sprint_connect.db   # SQLite database
│
├── tests/                  # Test files (to be implemented)
│
├── .gitignore             # Git ignore rules
├── .env.example           # Environment variables template
├── requirements.txt       # Python dependencies
└── README.md              # This file
```

## Development

### Running Tests

```bash
# Backend API will be available at:
http://localhost:8000

# API Documentation (Swagger):
http://localhost:8000/docs

# Frontend will be available at:
http://localhost:8501
```

### Common Issues

**Issue: Cannot connect to backend**
- Make sure the backend is running on port 8000
- Check if another application is using port 8000
- Verify the API_BASE_URL in `frontend/app.py` is set to `http://localhost:8000`

**Issue: Module not found errors**
- Make sure you activated the virtual environment
- Run `pip install -r requirements.txt` again
- Make sure you're running from the project root directory

**Issue: Database errors**
- Delete the `data/` folder and run `python -m backend.init_db` again

**Issue: Port already in use**
- For backend: `uvicorn backend.main:app --reload --port 8001` (change port)
- For frontend: `streamlit run frontend/app.py --server.port 8502` (change port)

## Environment Variables

You can create a `.env` file in the root directory for custom configuration:

```env
SECRET_KEY=your-super-secret-key-change-this-in-production
DATABASE_URL=sqlite:///./data/sprint_connect.db
```

## Contributing

See [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) for detailed contribution guidelines.

Quick steps:
1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Commit: `git commit -am 'Add new feature'`
5. Push: `git push origin feature-name`
6. Create a Pull Request

## Security Notes

- The default `SECRET_KEY` in `backend/auth.py` should be changed for production
- Never commit your `.env` file with real credentials
- Use HTTPS in production
- Review CORS settings in `backend/main.py` before deploying

## Documentation

- 📖 [Quick Start Guide](docs/QUICK_START.md) - Get started in 5 minutes
- 👥 [Contributing Guide](docs/CONTRIBUTING.md) - How to contribute
- 🚀 [Deployment Guide](docs/DEPLOYMENT_GUIDE.md) - Deploy to production

## License

This project is for educational purposes as part of SRH Haarlem's curriculum.

## Support

For issues or questions, please create an issue on GitHub or contact the development team.

---

Made with ❤️ for SRH Haarlem students
