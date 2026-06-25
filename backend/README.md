# Crop Disease Detection - Backend API

## 🌾 Overview

Production-ready FastAPI backend for AI-Enabled Crop Disease Diagnosis & Remediation System. This system provides comprehensive disease detection, treatment recommendations, and multi-language support for farmers.

## ✨ Features

### Epic 1: User Management & Dashboard
- ✅ Secure registration with email/phone
- ✅ JWT-based authentication (access + refresh tokens)
- ✅ Profile management & language preferences
- ✅ Multi-device session management
- ✅ Password reset with OTP
- ✅ Diagnosis history with filtering
- ✅ Analytics and insights
- ✅ PDF report generation

### Epic 2: Remediation & Guidance
- ✅ Step-by-step treatment instructions
- ✅ Organic & chemical treatment options
- ✅ Dosage and frequency recommendations
- ✅ Safety warnings and precautions
- ✅ Severity-based guidance
- ✅ Prevention tips

### Epic 3: AI Disease Detection
- ✅ Image quality check (blur detection)
- ✅ Multi-crop disease detection
- ✅ Video analysis with frame extraction
- ✅ Confidence scoring
- ✅ Heatmap generation (Grad-CAM)
- ✅ Bounding box detection
- ✅ Severity calculation

### Epic 4: Multi-Language Support
- ✅ Support for 6 languages (EN, HI, KN, TA, TE, MA)
- ✅ Auto-detection from headers
- ✅ Localized notifications
- ✅ Simplified vocabulary mode

### Epic 5: Offline Support
- ✅ Offline-first architecture
- ✅ Data sync management
- ✅ Local caching support
- ✅ Background task processing

## 🛠️ Tech Stack

- **Framework**: FastAPI 0.109.0
- **Database**: MongoDB (Motor async driver)
- **Security**: OAuth2 + JWT (passlib + python-jose)
- **Image Processing**: OpenCV + NumPy
- **PDF Generation**: ReportLab
- **Python**: 3.10+

## 📁 Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application
│   ├── api/
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── auth.py         # Authentication endpoints
│   │       ├── user.py         # User management
│   │       ├── diagnosis.py    # AI diagnosis
│   │       ├── remediation.py  # Treatment recommendations
│   │       ├── history.py      # History & analytics
│   │       └── notifications.py # Notifications
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py           # Configuration
│   │   ├── database.py         # MongoDB connection
│   │   └── security.py         # JWT & password handling
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py          # Pydantic models
│   ├── services/
│   │   ├── __init__.py
│   │   ├── ai_service.py       # AI model service
│   │   ├── remediation_service.py
│   │   └── notification_service.py
│   └── utils/
│       ├── __init__.py
│       ├── image_processing.py # Image utilities
│       ├── localization.py     # Multi-language support
│       ├── pdf_generator.py    # PDF reports
│       └── file_handler.py     # File operations
├── uploads/                    # Upload directory (auto-created)
├── models/                     # AI models directory
├── .env                        # Environment variables
├── requirements.txt            # Python dependencies
└── README.md
```

## 🚀 Getting Started

### Prerequisites

- Python 3.10 or higher
- MongoDB 4.4+ (local or MongoDB Atlas)
- pip (Python package manager)

### Installation

1. **Clone the repository**
   ```bash
   cd backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   # Copy .env file and update with your settings
   cp .env .env.local
   
   # IMPORTANT: Update these values in .env:
   # - MONGODB_URL (your MongoDB connection string)
   # - SECRET_KEY (generate: python -c "import secrets; print(secrets.token_hex(32))")
   ```

5. **Start MongoDB**
   ```bash
   # Local MongoDB
   mongod --dbpath ./data/db
   
   # Or use MongoDB Atlas (update MONGODB_URL in .env)
   ```

6. **Run the application**
   ```bash
   # Development mode
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   
   # Or using Python
   python app/main.py
   ```

7. **Access the API**
   - API Documentation: http://localhost:8000/docs
   - Alternative Docs: http://localhost:8000/redoc
   - Health Check: http://localhost:8000/health

## 📚 API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login
- `POST /api/v1/auth/refresh` - Refresh token
- `POST /api/v1/auth/logout` - Logout
- `POST /api/v1/auth/logout-all` - Logout from all devices
- `POST /api/v1/auth/forgot-password` - Request password reset
- `POST /api/v1/auth/reset-password` - Reset password
- `GET /api/v1/auth/me` - Get current user

### User Management
- `GET /api/v1/user/profile` - Get profile
- `PATCH /api/v1/user/profile` - Update profile
- `GET /api/v1/user/sessions` - Get active sessions
- `DELETE /api/v1/user/sessions/{id}` - Revoke session

### Diagnosis
- `POST /api/v1/diagnosis/check-quality` - Check image quality
- `POST /api/v1/diagnosis/` - Create diagnosis from image
- `POST /api/v1/diagnosis/video` - Create diagnosis from video
- `GET /api/v1/diagnosis/{id}` - Get diagnosis details
- `GET /api/v1/diagnosis/` - List all diagnoses

### Remediation
- `GET /api/v1/remediation/{disease_id}` - Get treatment plan
- `GET /api/v1/remediation/healthy/guidance` - Healthy plant guidance

### History
- `GET /api/v1/history/` - Get history (with filters)
- `DELETE /api/v1/history/{id}` - Delete history entry
- `GET /api/v1/history/analytics` - Get analytics
- `GET /api/v1/history/report/{diagnosis_id}` - Download PDF report

### Notifications
- `GET /api/v1/notifications/` - Get notifications
- `GET /api/v1/notifications/unread-count` - Unread count
- `PATCH /api/v1/notifications/{id}/read` - Mark as read
- `POST /api/v1/notifications/mark-all-read` - Mark all as read

## 🔐 Security

### JWT Authentication
All protected endpoints require JWT token in the Authorization header:
```
Authorization: Bearer <access_token>
```

### Token Generation
```python
# Generate secure SECRET_KEY
python -c "import secrets; print(secrets.token_hex(32))"
```

### Password Requirements
- Minimum 8 characters
- Stored as bcrypt hash
- 12 rounds of hashing

## 🗄️ Database Schema

### Collections

**users**
```json
{
  "_id": "ObjectId",
  "name": "string",
  "email": "string",
  "phone": "string",
  "hashed_password": "string",
  "preferred_language": "string",
  "location": {},
  "is_active": true,
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

**diagnoses**
```json
{
  "_id": "ObjectId",
  "user_id": "string",
  "crop_type": "string",
  "disease_id": "string",
  "disease_name": "string",
  "confidence": 0.92,
  "severity": "medium",
  "image_url": "string",
  "heatmap_url": "string",
  "bounding_boxes": [],
  "created_at": "datetime"
}
```

## 🌐 Multi-Language Support

Supported languages:
- English (en)
- Hindi (hi)
- Tamil (ta)
- Telugu (te)
- Kannada (kn)
- Malayalam (ml)

Set language via:
1. User preference (in profile)
2. Accept-Language header
3. Defaults to English

## 🧪 Testing

```bash
# Run tests
pytest

# With coverage
pytest --cov=app tests/

# Specific test file
pytest tests/test_auth.py
```

## 🚀 Production Deployment

### Using Docker

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Using Gunicorn + Uvicorn

```bash
pip install gunicorn

gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 120
```

### Environment Variables for Production

```bash
DEBUG=False
ENVIRONMENT=production
MONGODB_URL=<production-mongodb-url>
SECRET_KEY=<strong-secret-key>
BACKEND_CORS_ORIGINS=["https://yourdomain.com"]
```

## 📊 Monitoring

- Health check: `GET /health`
- Request logging: Automatic via middleware
- Performance metrics: X-Process-Time header

## 🐛 Troubleshooting

### Database Connection Issues
```bash
# Check MongoDB is running
mongod --version

# Test connection
mongo --eval "db.version()"
```

### Import Errors
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Port Already in Use
```bash
# Windows: Kill process on port 8000
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:8000 | xargs kill -9
```

## 📝 Development Guidelines

### Code Style
- Follow PEP 8
- Use Black for formatting: `black app/`
- Type hints recommended
- Docstrings for all functions

### Adding New Endpoints
1. Create/update router in `app/api/v1/`
2. Add business logic in `app/services/`
3. Update models in `app/models/schemas.py`
4. Update this README

## 🤝 Contributing

1. Create feature branch
2. Make changes
3. Add tests
4. Update documentation
5. Submit pull request

## 📄 License

Copyright © 2026 Crop Disease Detection System

## 📧 Support

For issues and questions:
- GitHub Issues: [Your repo URL]
- Email: support@yourdomain.com

## 🙏 Acknowledgments

- FastAPI framework
- MongoDB team
- OpenCV community
- All contributors

---

**Built with ❤️ for farmers around the world** 🌾
