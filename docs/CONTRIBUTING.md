# Contributing to Sprint Connect

Thank you for your interest in contributing to Sprint Connect! This guide will help you get started.

## Getting Started

### Prerequisites
- Python 3.12+ installed
- Git installed
- Code editor (VS Code, PyCharm, etc.)
- Basic knowledge of Python, FastAPI, and Streamlit

### Setting Up Your Development Environment

1. **Fork and Clone the Repository**
   ```bash
   git clone https://github.com/YOUR-USERNAME/sprint-connect.git
   cd sprint-connect
   ```

2. **Run the Setup Script**

   **Windows:**
   ```bash
   setup.bat
   ```

   **macOS/Linux:**
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```

   Or manually:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   python init_db.py
   ```

3. **Verify Installation**
   ```bash
   # Test imports
   python -c "import models, schemas, auth, database; print('✓ All imports successful')"
   ```

## Project Structure

```
sprint-connect/
├── main.py              # FastAPI backend (REST API)
├── app.py               # Streamlit frontend (UI)
├── models.py            # SQLAlchemy database models
├── schemas.py           # Pydantic schemas for validation
├── auth.py              # Authentication & authorization
├── database.py          # Database configuration
├── init_db.py          # Database initialization with demo data
├── requirements.txt     # Python dependencies
├── .gitignore          # Files to exclude from git
├── README.md           # Project documentation
├── CONTRIBUTING.md     # This file
└── data/               # SQLite database (auto-created)
```

## Development Workflow

### Running the Application

You need TWO terminal windows:

**Terminal 1 - Backend:**
```bash
source venv/bin/activate  # On Windows: venv\Scripts\activate
uvicorn main:app --reload --port 8000
```

**Terminal 2 - Frontend:**
```bash
source venv/bin/activate  # On Windows: venv\Scripts\activate
streamlit run app.py
```

### Making Changes

1. **Create a new branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Follow the existing code style
   - Add comments for complex logic
   - Update documentation if needed

3. **Test your changes**
   - Test the API endpoints at http://localhost:8000/docs
   - Test the UI at http://localhost:8501
   - Make sure both backend and frontend work together

4. **Commit your changes**
   ```bash
   git add .
   git commit -m "Add: brief description of changes"
   ```

5. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Create a Pull Request**
   - Go to GitHub
   - Click "New Pull Request"
   - Describe your changes
   - Submit for review

## Code Style Guidelines

### Python Style
- Follow PEP 8 style guide
- Use meaningful variable names
- Add docstrings to functions
- Keep functions small and focused

### Example:
```python
def calculate_average_mood(checkins: List[WellnessCheckIn]) -> float:
    """
    Calculate the average mood score from a list of check-ins.

    Args:
        checkins: List of wellness check-in objects

    Returns:
        float: Average mood score (0-5 scale)
    """
    if not checkins:
        return 0.0

    mood_scores = [c.mood_score for c in checkins]
    return sum(mood_scores) / len(mood_scores)
```

### API Development (main.py)
- Use proper HTTP status codes
- Add docstrings to endpoints
- Validate input with Pydantic schemas
- Handle errors gracefully

```python
@app.post("/checkin", response_model=schemas.WellnessCheckIn)
def create_checkin(
    checkin: schemas.WellnessCheckInCreate,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a daily wellness check-in"""
    # Implementation...
```

### Frontend Development (app.py)
- Use clear page titles and descriptions
- Add helpful error messages
- Keep UI components reusable
- Test with demo accounts

## Common Development Tasks

### Adding a New Database Model

1. **Update `models.py`**
   ```python
   class NewModel(Base):
       __tablename__ = "new_models"
       id = Column(Integer, primary_key=True, index=True)
       # Add fields...
   ```

2. **Update `schemas.py`**
   ```python
   class NewModelBase(BaseModel):
       # Add fields...

   class NewModel(NewModelBase):
       id: int
       class Config:
           from_attributes = True
   ```

3. **Recreate the database**
   ```bash
   rm -rf data/
   python init_db.py
   ```

### Adding a New API Endpoint

1. **Add to `main.py`**
   ```python
   @app.get("/new-endpoint", response_model=schemas.NewResponse)
   def new_endpoint(db: Session = Depends(get_db)):
       """Endpoint description"""
       # Implementation...
   ```

2. **Test at** http://localhost:8000/docs

3. **Update frontend in `app.py`**
   ```python
   data = make_request("GET", "/new-endpoint")
   ```

### Resetting the Database

```bash
# Delete the database
rm -rf data/

# Recreate with demo data
python init_db.py
```

## Testing

### Manual Testing
1. Start both backend and frontend
2. Login with demo accounts
3. Test all features
4. Check browser console for errors
5. Check terminal for backend errors

### API Testing
- Use the Swagger UI at http://localhost:8000/docs
- Test authentication first (get a token)
- Use the "Authorize" button with the token

## Framework Compatibility Notes

### Python 3.12
- All dependencies are compatible with Python 3.12
- Use `from_attributes = True` in Pydantic models (v2 syntax)
- SQLAlchemy 2.0 style is used

### Pydantic v2
```python
# ✅ Correct (v2)
class Config:
    from_attributes = True

# ❌ Old (v1) - Don't use
class Config:
    orm_mode = True
```

### SQLAlchemy 2.0
- Use `Session.execute()` for queries when needed
- Current code uses compatible query style
- No deprecation warnings should appear

## Troubleshooting

### Import Errors
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Database Errors
```bash
# Reset database
rm -rf data/
python init_db.py
```

### Port Already in Use
```bash
# Backend on different port
uvicorn main:app --reload --port 8001

# Frontend on different port
streamlit run app.py --server.port 8502
```

### Module Not Found
- Make sure virtual environment is activated
- Check you're in the project root directory
- Verify all imports use absolute imports (not `from .`)

## Getting Help

- Check existing issues on GitHub
- Ask in the project discussions
- Read the API docs at http://localhost:8000/docs
- Review the code examples in this guide

## Areas for Contribution

### High Priority
- [ ] Add unit tests
- [ ] Improve error handling
- [ ] Add input validation
- [ ] Improve mobile responsiveness

### Features
- [ ] Direct messaging between students
- [ ] Video chat integration
- [ ] File upload for resources
- [ ] Email notifications
- [ ] Calendar integration

### Documentation
- [ ] API documentation
- [ ] User guide
- [ ] Deployment tutorials
- [ ] Architecture diagrams

## Questions?

If you have questions or need help, please:
1. Check this guide first
2. Look at existing issues
3. Create a new issue with details
4. Tag it appropriately (bug, question, enhancement)

Happy coding! 🚀
