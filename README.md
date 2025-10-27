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

## Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/oskarkuz/sprint-connect.git
cd sprint-connect
```

### 2. Create a Virtual Environment

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Initialize the Database

```bash
python init_db.py
```

This will:
- Create the database with all necessary tables
- Add demo accounts for testing
- Add sample courses and data

### 5. Run the Application

You need to run both the backend and frontend in separate terminals:

**Terminal 1 - Backend API:**
```bash
uvicorn main:app --reload --port 8000
```

**Terminal 2 - Frontend (in a new terminal, activate venv first):**
```bash
streamlit run app.py
```

The application will open in your browser at `http://localhost:8501`

## Demo Accounts

After running `init_db.py`, you can login with:

- **Student Account**:
  - Email: `sarah@srh.nl`
  - Password: `demo123`

- **Admin Account**:
  - Email: `admin@srh.nl`
  - Password: `admin123`

## Project Structure

```
sprint-connect/
├── main.py              # FastAPI backend application
├── app.py               # Streamlit frontend application
├── models.py            # Database models (SQLAlchemy)
├── schemas.py           # Pydantic schemas for API
├── auth.py              # Authentication logic
├── database.py          # Database configuration
├── init_db.py           # Database initialization script
├── requirements.txt     # Python dependencies
├── .gitignore          # Git ignore rules
├── README.md           # This file
├── DEPLOYMENT_GUIDE.md # Deployment instructions
└── data/               # Database storage (created automatically)
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
- Verify the API_BASE_URL in `app.py` is set to `http://localhost:8000`

**Issue: Module not found errors**
- Make sure you activated the virtual environment
- Run `pip install -r requirements.txt` again

**Issue: Database errors**
- Delete the `data/` folder and run `python init_db.py` again

**Issue: Port already in use**
- For backend: `uvicorn main:app --reload --port 8001` (change port)
- For frontend: `streamlit run app.py --server.port 8502` (change port)

## Environment Variables

You can create a `.env` file in the root directory for custom configuration:

```env
SECRET_KEY=your-super-secret-key-change-this-in-production
DATABASE_URL=sqlite:///./data/sprint_connect.db
```

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Commit: `git commit -am 'Add new feature'`
5. Push: `git push origin feature-name`
6. Create a Pull Request

## Security Notes

- The default `SECRET_KEY` in `auth.py` should be changed for production
- Never commit your `.env` file with real credentials
- Use HTTPS in production
- Review CORS settings in `main.py` before deploying

## License

This project is for educational purposes as part of SRH Haarlem's curriculum.

## Support

For issues or questions, please create an issue on GitHub or contact the development team.

---

Made with ❤️ for SRH Haarlem students
