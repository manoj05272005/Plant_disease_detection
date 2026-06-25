# 🌾 AI-Enabled Crop Disease Detection & Remediation System

<div align="center">

![License](https://img.shields.io/badge/license-MIT-green)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Flutter](https://img.shields.io/badge/Flutter-3.10.7-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109.0-009688)
![MongoDB](https://img.shields.io/badge/MongoDB-6.0%2B-green)
![TensorFlow](https://img.shields.io/badge/TensorFlow-2.x-orange)

**A comprehensive AI-powered platform for real-time crop disease diagnosis, treatment recommendations, and agricultural support.**

[Features](#-features) • [Quick Start](#-quick-start) • [Documentation](#-documentation) • [Architecture](#-architecture) • [Contributing](#-contributing)

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [System Architecture](#-system-architecture)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [System Requirements](#-system-requirements)
- [Installation & Setup](#-installation--setup)
  - [Backend Setup](#1-backend-setup)
  - [Frontend Setup](#2-frontend-setup)
  - [AI Model Setup](#3-ai-model-setup)
- [Usage Guide](#-usage-guide)
- [API Documentation](#-api-documentation)
- [Disease Detection Model](#-disease-detection-model)
- [Deployment](#-deployment)
- [Testing](#-testing)
- [Contributing](#-contributing)
- [License](#-license)
- [Support](#-support)

---

## 🌟 Overview

The **AI-Enabled Crop Disease Detection & Remediation System** is a comprehensive agricultural technology platform designed to empower farmers with instant, accurate crop disease diagnosis and personalized treatment recommendations. By leveraging deep learning, computer vision, and multi-language support, this system bridges the gap between advanced agricultural science and practical farming needs.

### 🎯 Problem Statement

Farmers worldwide face significant challenges in:
- Identifying crop diseases accurately and quickly
- Getting timely expert agricultural advice
- Understanding technical disease information
- Accessing treatment recommendations in their native language
- Making informed decisions about crop management

### 💡 Solution

Our platform provides:
- **Real-time disease detection** using AI-powered image analysis
- **Multi-language support** (English, Hindi, Tamil, Telugu, Kannada, Malayalam)
- **Comprehensive treatment plans** with organic and chemical options
- **Offline-first architecture** for remote farming areas
- **Visual explanations** with heatmaps and bounding boxes
- **Historical tracking** and analytics for better crop management

---

## ✨ Features

### 🔬 AI Disease Detection (Epic 3)
- **Multiple Input Methods**: Image upload, camera capture, video recording
- **Blur Detection**: Automatic image quality assessment
- **19 Disease Classes**: Support for Apple, Corn, Potato, Tomato, Pepper, and Strawberry
- **Confidence Scoring**: Probability-based predictions for accuracy
- **Explainable AI**: Grad-CAM heatmaps showing affected leaf regions
- **Bounding Box Detection**: Visual localization of disease symptoms
- **Multi-frame Video Analysis**: Extract and analyze video frames for comprehensive diagnosis

### 👤 User Management (Epic 1)
- **Secure Authentication**: JWT-based login with refresh tokens
- **Multi-device Support**: Login from multiple devices simultaneously
- **Profile Management**: Customizable user profiles with location tracking
- **Password Recovery**: OTP-based password reset via email/phone
- **Diagnosis History**: Complete record of all plant analyses
- **Analytics Dashboard**: Insights into crop health trends
- **PDF Report Generation**: Downloadable treatment and diagnosis reports
- **Notification System**: Real-time alerts and updates

### 💊 Remediation & Guidance (Epic 2)
- **Step-by-step Instructions**: Clear, actionable treatment plans
- **Dual Treatment Options**: Both organic and chemical solutions
- **Dosage Recommendations**: Precise application guidelines
- **Safety Warnings**: Critical precautions and safety information
- **Severity-based Guidance**: Tailored advice based on disease severity
- **Prevention Tips**: Proactive measures to avoid future infections
- **Cost Estimates**: Budget planning for treatments
- **Expert Consultation**: Connection to agricultural experts
- **Community Wisdom**: Shared farmer experiences and tips

### 🌍 Multi-Language Support (Epic 4)
- **6 Languages**: EN, HI, TA, TE, KN, ML
- **Automatic Detection**: Language preference from HTTP headers
- **Localized Content**: All notifications and instructions in native language
- **Simplified Mode**: Technical terms explained in simple vocabulary
- **Voice Support**: Text-to-Speech (TTS) for audio guidance

### 📱 Offline Support (Epic 5)
- **Offline-first Design**: Core functionality without internet
- **Local Data Caching**: Store frequently accessed information
- **Sync Management**: Automatic data synchronization when online
- **Background Processing**: Queue tasks for later execution

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         PRESENTATION LAYER                       │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │         Flutter Mobile App (Android, iOS, Web)           │  │
│  │  • Login/Register  • Camera/Gallery  • History View      │  │
│  │  • Diagnosis Results  • Treatment Plans  • Analytics     │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────────┘
                         │ REST API (HTTPS)
┌────────────────────────┴────────────────────────────────────────┐
│                        APPLICATION LAYER                         │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              FastAPI Backend (Python 3.10+)              │  │
│  │                                                           │  │
│  │  API Routes          Services            Utils           │  │
│  │  • Auth             • AI Service         • Image Proc.   │  │
│  │  • User             • Remediation        • PDF Gen.      │  │
│  │  • Diagnosis        • Notification       • Localization  │  │
│  │  • History          • Weather Service    • File Handler  │  │
│  │  • Remediation                                           │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────┬──────────────────────┬─────────────────────────┘
                 │                      │
    ┌────────────┴────────┐  ┌──────────┴──────────┐
    │   DATA LAYER        │  │    AI/ML LAYER      │
    │                     │  │                     │
    │  ┌──────────────┐  │  │  ┌──────────────┐  │
    │  │   MongoDB    │  │  │  │ TensorFlow/  │  │
    │  │   Database   │  │  │  │   Keras      │  │
    │  │              │  │  │  │              │  │
    │  │ • Users      │  │  │  │ MobileNetV2  │  │
    │  │ • Diagnoses  │  │  │  │ Fine-tuned   │  │
    │  │ • History    │  │  │  │ CNN Model    │  │
    │  │ • Sessions   │  │  │  │              │  │
    │  └──────────────┘  │  │  │ 19 Classes   │  │
    │                     │  │  └──────────────┘  │
    └─────────────────────┘  │                     │
                             │  ┌──────────────┐  │
                             │  │   OpenCV     │  │
                             │  │   Grad-CAM   │  │
                             │  │   Whisper    │  │
                             │  └──────────────┘  │
                             └─────────────────────┘
```

### Architecture Highlights

1. **Microservices-Ready**: Modular design allows easy service separation
2. **Async Processing**: Non-blocking I/O for high performance
3. **Scalable Storage**: MongoDB for flexible document storage
4. **Security-First**: JWT tokens, password hashing, CORS protection
5. **Cloud-Native**: Docker containerization for easy deployment
6. **API-First**: RESTful design enables multiple client applications

---

## 🛠️ Tech Stack

### Backend
| Technology | Purpose | Version |
|-----------|---------|---------|
| **FastAPI** | Web Framework | 0.109.0 |
| **Python** | Programming Language | 3.10+ |
| **MongoDB** | NoSQL Database | 6.0+ |
| **Motor** | Async MongoDB Driver | 3.3.2 |
| **Uvicorn** | ASGI Server | 0.27.0 |
| **PyJWT** | JWT Authentication | via python-jose |
| **Passlib** | Password Hashing | 1.7.4 |
| **Pydantic** | Data Validation | 2.5.3 |
| **OpenCV** | Image Processing | 4.9.0 |
| **NumPy** | Numerical Computing | 1.26.3 |
| **ReportLab** | PDF Generation | 4.0.9 |
| **Pillow** | Image Manipulation | 10.2.0 |
| **Redis** (optional) | Caching & Task Queue | 5.0.1 |
| **Celery** (optional) | Background Tasks | 5.3.6 |

### Frontend
| Technology | Purpose | Version |
|-----------|---------|---------|
| **Flutter** | Cross-platform Framework | 3.10.7+ |
| **Dart** | Programming Language | 3.10.7+ |
| **Hive** | Local NoSQL Database | 2.2.3 |
| **SharedPreferences** | Key-Value Storage | 2.2.2 |
| **ImagePicker** | Camera/Gallery Access | 1.0.7 |
| **ImageCropper** | Image Editing | 8.0.0 |
| **HTTP** | API Communication | 1.2.0 |
| **PathProvider** | File System Access | 2.1.2 |
| **Intl** | Internationalization | 0.19.0 |

### AI/ML
| Technology | Purpose |
|-----------|---------|
| **TensorFlow/Keras** | Deep Learning Framework |
| **MobileNetV2** | CNN Architecture |
| **OpenAI Whisper** | Speech Recognition |
| **Grad-CAM** | Visual Explanations |
| **GoogleTranslator** | Multi-language Translation |
| **gTTS** | Text-to-Speech |
| **LangDetect** | Language Detection |

### DevOps & Tools
| Technology | Purpose |
|-----------|---------|
| **Docker** | Containerization |
| **Docker Compose** | Multi-container Orchestration |
| **Git** | Version Control |
| **Pytest** | Testing Framework |
| **Black** | Code Formatting |
| **Flake8** | Linting |

---

## 📁 Project Structure

```
Plant_disease_detection/
│
├── 📱 frontend/                      # Flutter Mobile Application
│   ├── lib/
│   │   ├── main.dart                 # App entry point
│   │   ├── models/                   # Data models
│   │   ├── screens/                  # UI screens
│   │   │   ├── auth/                 # Login, Register
│   │   │   ├── home.dart             # Dashboard
│   │   │   ├── scan.dart             # Disease scanning
│   │   │   ├── result.dart           # Diagnosis results
│   │   │   └── history.dart          # History view
│   │   ├── services/                 # Business logic
│   │   │   ├── api_service.dart      # Backend API calls
│   │   │   ├── database.dart         # Hive database
│   │   │   ├── ai_handler.dart       # AI processing
│   │   │   └── mock_ai_service.dart  # Testing/offline mode
│   │   └── widgets/                  # Reusable components
│   ├── android/                      # Android-specific config
│   ├── ios/                          # iOS-specific config
│   ├── web/                          # Web-specific config
│   ├── pubspec.yaml                  # Flutter dependencies
│   └── README.md                     # Frontend docs
│
├── 🔧 backend/                       # FastAPI Backend Server
│   ├── app/
│   │   ├── main.py                   # FastAPI application
│   │   ├── api/v1/                   # API endpoints
│   │   │   ├── auth.py               # Authentication routes
│   │   │   ├── user.py               # User management
│   │   │   ├── diagnosis.py          # Disease detection
│   │   │   ├── remediation.py        # Treatment plans
│   │   │   ├── history.py            # Diagnosis history
│   │   │   └── notifications.py      # Notification system
│   │   ├── core/                     # Core functionality
│   │   │   ├── config.py             # Configuration settings
│   │   │   ├── database.py           # MongoDB connection
│   │   │   └── security.py           # JWT & security
│   │   ├── models/                   # Data schemas
│   │   │   └── schemas.py            # Pydantic models
│   │   ├── services/                 # Business services
│   │   │   ├── ai_service.py         # AI model integration
│   │   │   ├── remediation_service.py # Treatment logic
│   │   │   └── notification_service.py # Notifications
│   │   └── utils/                    # Utility functions
│   │       ├── image_processing.py   # Image operations
│   │       ├── localization.py       # Multi-language
│   │       ├── pdf_generator.py      # PDF reports
│   │       └── file_handler.py       # File management
│   ├── models/                       # ML model files
│   │   ├── crop_disease_master_model.keras
│   │   └── new_label_map.txt
│   ├── uploads/                      # User uploads (auto-created)
│   │   ├── images/
│   │   ├── videos/
│   │   ├── heatmaps/
│   │   └── reports/
│   ├── logs/                         # Application logs
│   ├── requirements.txt              # Python dependencies
│   ├── Dockerfile                    # Docker image config
│   ├── docker-compose.yml            # Multi-container setup
│   ├── .env                          # Environment variables
│   ├── README.md                     # Backend documentation
│   ├── API_DOCUMENTATION.md          # API reference
│   ├── DEPLOYMENT.md                 # Deployment guide
│   └── PROJECT_SUMMARY.md            # Implementation summary
│
├── 🤖 Model/                         # AI/ML Training & Research
│   ├── farmer_agent.py               # Multi-modal agent
│   ├── latest_model.ipynb            # Training notebook
│   ├── requirements.txt              # ML dependencies
│   ├── data/                         # Training data
│   │   └── new_label_map.txt
│   ├── model/                        # Trained models
│   │   └── crop_disease_master_model.keras
│   ├── test_samples/                 # Test images
│   └── README.md                     # Model documentation
│
├── LICENSE                           # MIT License
└── README.md                         # This file
```

---

## 💻 System Requirements

### Backend Requirements

**Minimum:**
- OS: Windows 10/11, Ubuntu 20.04+, macOS 11+
- Python: 3.10 or higher
- RAM: 4 GB
- Storage: 2 GB free space
- MongoDB: 6.0+

**Recommended:**
- RAM: 8 GB or more
- CPU: 4+ cores
- SSD storage for faster I/O
- GPU: NVIDIA GPU for faster AI inference (optional)

### Frontend Requirements

**Development:**
- Flutter SDK: 3.10.7 or higher
- Dart SDK: 3.10.7+
- Android Studio / VS Code with Flutter extension
- XCode (for iOS development on macOS)

**Device Support:**
- Android: 6.0+ (API Level 23+)
- iOS: 11.0+
- Web: Modern browsers (Chrome, Firefox, Safari, Edge)
- Desktop: Windows 10+, macOS 11+, Linux

### AI Model Requirements

**Minimum:**
- TensorFlow: 2.x
- RAM: 4 GB
- Storage: 1 GB for model files

**For Training:**
- GPU: NVIDIA with CUDA support
- VRAM: 6 GB+
- RAM: 16 GB+

---

## 🚀 Installation & Setup

### Prerequisites

Before starting, ensure you have:
- ✅ Python 3.10+ installed
- ✅ MongoDB installed and running
- ✅ Flutter SDK installed (for frontend)
- ✅ Git installed
- ✅ Text editor (VS Code recommended)

---

### 1. Backend Setup

#### Step 1: Clone Repository

```bash
git clone https://github.com/yourusername/Plant_disease_detection.git
cd Plant_disease_detection/backend
```

#### Step 2: Create Virtual Environment

**Windows:**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Linux/macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

#### Step 3: Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### Step 4: Configure Environment Variables

Create a `.env` file in the `backend/` directory:

```env
# Application Settings
APP_NAME=Crop Disease Detection API
APP_VERSION=1.0.0
ENVIRONMENT=development
LOG_LEVEL=INFO
LOG_FILE=logs/app.log

# Security
SECRET_KEY=your-super-secret-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Database
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=crop_disease_db

# CORS Origins (comma-separated)
BACKEND_CORS_ORIGINS=http://localhost:3000,http://localhost:8080,http://localhost:5173

# File Upload
MAX_UPLOAD_SIZE=10485760
UPLOAD_DIR=uploads

# AI Model
MODEL_PATH=models/crop_disease_master_model.keras
LABEL_MAP_PATH=models/new_label_map.txt
CONFIDENCE_THRESHOLD=0.6

# Email (Optional - for OTP)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Weather API (Optional)
OPENWEATHER_API_KEY=your-api-key-here

# Redis (Optional - for caching)
REDIS_URL=redis://localhost:6379/0
```

#### Step 5: Generate Secret Key

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Copy the output and replace `SECRET_KEY` in `.env`

#### Step 6: Start MongoDB

```bash
# Windows
mongod --dbpath C:\data\db

# Linux/macOS
sudo systemctl start mongod
# OR
mongod --dbpath /usr/local/var/mongodb
```

#### Step 7: Run Backend Server

```bash
# Development (with auto-reload)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

#### Step 8: Verify Installation

Visit: http://localhost:8000/docs

You should see the interactive API documentation (Swagger UI).

---

### 2. Frontend Setup

#### Step 1: Navigate to Frontend Directory

```bash
cd ../frontend
```

#### Step 2: Install Flutter Dependencies

```bash
flutter pub get
```

#### Step 3: Configure API Endpoint

Edit `lib/services/api_service.dart`:

```dart
class ApiService {
  // Change this to your backend URL
  static const String baseUrl = 'http://localhost:8000/api/v1';
  // For Android Emulator: http://10.0.2.2:8000/api/v1
  // For iOS Simulator: http://localhost:8000/api/v1
  // For Physical Device: http://YOUR_LOCAL_IP:8000/api/v1
}
```

#### Step 4: Run Flutter App

**Android:**
```bash
flutter run -d android
```

**iOS:**
```bash
flutter run -d ios
```

**Web:**
```bash
flutter run -d chrome
```

**Desktop (Windows):**
```bash
flutter run -d windows
```

#### Step 5: Build for Production

**Android APK:**
```bash
flutter build apk --release
```

**iOS:**
```bash
flutter build ios --release
```

**Web:**
```bash
flutter build web --release
```

---

### 3. AI Model Setup

#### Step 1: Navigate to Model Directory

```bash
cd ../Model
```

#### Step 2: Create Virtual Environment

```bash
python -m venv venv312
.\venv312\Scripts\Activate.ps1  # Windows
# source venv312/bin/activate    # Linux/macOS
```

#### Step 3: Install ML Dependencies

```bash
pip install -r requirements.txt
```

#### Step 4: Install FFmpeg (for Whisper)

**Windows:**
```powershell
winget install ffmpeg
```

**Linux:**
```bash
sudo apt install ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

#### Step 5: Download Pre-trained Model

The trained model is already included in:
- `Model/model/crop_disease_master_model.keras`
- `backend/models/crop_disease_master_model.keras`

#### Step 6: Test Model

```bash
python farmer_agent.py
```

#### Step 7: (Optional) Retrain Model

Open `latest_model.ipynb` in Jupyter Notebook:

```bash
jupyter notebook latest_model.ipynb
```

---

## 📖 Usage Guide

### For Farmers (Mobile App)

#### 1. Registration & Login
1. Open the mobile app
2. Click "Register" and fill in your details
3. Choose your preferred language
4. Login with email/phone and password

#### 2. Diagnose Plant Disease
1. Tap "Scan Plant" on the home screen
2. Choose input method:
   - **Camera**: Take a photo
   - **Gallery**: Upload existing image
   - **Video**: Record a short video
3. Select crop type (Apple, Corn, Potato, etc.)
4. Submit for analysis

#### 3. View Results
- **Disease Name**: Identified disease or "Healthy"
- **Confidence**: Accuracy percentage
- **Heatmap**: Visual highlighting of affected areas
- **Severity**: Mild, Moderate, or Severe

#### 4. Get Treatment Recommendations
1. View step-by-step remediation plan
2. Choose between organic or chemical treatment
3. Check dosage and application frequency
4. Read safety warnings
5. Download PDF report

#### 5. Track History
- View all past diagnoses
- Filter by crop type, date, or disease
- Access treatment plans anytime
- Analyze crop health trends

### For Developers (API Usage)

#### Authentication Flow

```python
import requests

BASE_URL = "http://localhost:8000/api/v1"

# 1. Register
response = requests.post(f"{BASE_URL}/auth/register", json={
    "name": "John Farmer",
    "email": "john@example.com",
    "phone": "+919876543210",
    "password": "SecurePass123",
    "preferred_language": "en"
})

# 2. Login
response = requests.post(f"{BASE_URL}/auth/login", data={
    "username": "john@example.com",
    "password": "SecurePass123"
})
tokens = response.json()
access_token = tokens["access_token"]

# 3. Use Protected Endpoints
headers = {"Authorization": f"Bearer {access_token}"}
profile = requests.get(f"{BASE_URL}/user/profile", headers=headers)
```

#### Disease Detection

```python
# Upload image for diagnosis
files = {"file": open("leaf_image.jpg", "rb")}
data = {"crop_type": "tomato"}

response = requests.post(
    f"{BASE_URL}/diagnosis/",
    files=files,
    data=data,
    headers=headers
)

diagnosis = response.json()
print(f"Disease: {diagnosis['disease_name']}")
print(f"Confidence: {diagnosis['confidence']}%")
```

---

## 📚 API Documentation

### Base URL
```
Development: http://localhost:8000/api/v1
Production: https://api.yourdomain.com/api/v1
```

### Authentication

All protected endpoints require JWT token:
```
Authorization: Bearer <access_token>
```

### Key Endpoints

#### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login and get tokens
- `POST /auth/refresh` - Refresh access token
- `POST /auth/logout` - Logout current session
- `POST /auth/forgot-password` - Request password reset
- `POST /auth/reset-password` - Reset password with OTP

#### User Management
- `GET /user/profile` - Get user profile
- `PATCH /user/profile` - Update profile
- `GET /user/sessions` - List active sessions
- `DELETE /user/sessions/{id}` - Revoke session

#### Diagnosis
- `POST /diagnosis/check-quality` - Check image quality
- `POST /diagnosis/` - Create diagnosis from image
- `POST /diagnosis/video` - Create diagnosis from video
- `GET /diagnosis/{id}` - Get diagnosis details
- `GET /diagnosis/` - List all diagnoses

#### Remediation
- `GET /remediation/{disease_id}` - Get treatment plan
- `GET /remediation/healthy/guidance` - Healthy plant guidance

#### History
- `GET /history/` - Get diagnosis history
- `DELETE /history/{id}` - Delete history entry
- `GET /history/analytics` - Get analytics
- `GET /history/report/{diagnosis_id}` - Download PDF report

#### Notifications
- `GET /notifications/` - Get notifications
- `GET /notifications/unread-count` - Get unread count
- `PATCH /notifications/{id}/read` - Mark as read
- `POST /notifications/mark-all-read` - Mark all as read

---

## 🤖 Disease Detection Model

### Model Architecture

**Base Model**: MobileNetV2 (Fine-tuned)
- **Input Size**: 224x224x3
- **Architecture**: CNN (Convolutional Neural Network)
- **Transfer Learning**: Pre-trained on ImageNet
- **Fine-tuning**: Trained on PlantVillage dataset

### Supported Crops & Diseases

| Crop | Diseases Detected | Classes |
|------|------------------|---------|
| **Apple** | Scab, Black rot, Cedar apple rust, Healthy | 4 |
| **Corn (Maize)** | Cercospora/Gray leaf spot, Common rust, Northern leaf blight, Healthy | 4 |
| **Tomato** | Early blight, Late blight, Yellow leaf curl virus, Healthy | 4 |
| **Potato** | Early blight, Late blight, Healthy | 3 |
| **Pepper (Bell)** | Bacterial spot, Healthy | 2 |
| **Strawberry** | Leaf scorch, Healthy | 2 |

**Total**: 19 classes (including healthy variants)

### Model Performance

- **Accuracy**: ~95% on test dataset
- **Inference Time**: ~200ms per image (CPU)
- **Model Size**: ~14 MB
- **Confidence Threshold**: 60%

### Explainability Features

1. **Grad-CAM Heatmaps**: Visual explanation showing which parts of the leaf influenced the prediction
2. **Confidence Scores**: Probability percentage for each prediction
3. **Bounding Boxes**: Localization of disease-affected regions
4. **Severity Assessment**: Mild, Moderate, or Severe classification

### Model Files

- **Keras Model**: `crop_disease_master_model.keras`
- **Label Map**: `new_label_map.txt`
- **Location**: `backend/models/` and `Model/model/`

---

## 🐳 Deployment

### Docker Deployment (Recommended)

#### Using Docker Compose

```bash
cd backend

# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f backend

# Stop services
docker-compose down
```

The `docker-compose.yml` includes:
- Backend API service
- MongoDB database
- Redis (optional) for caching

#### Manual Docker Build

```bash
# Build image
docker build -t crop-disease-backend:latest .

# Run container
docker run -d \
  --name crop-disease-api \
  -p 8000:8000 \
  -e MONGODB_URL="mongodb://host.docker.internal:27017" \
  -e SECRET_KEY="your-secret-key" \
  crop-disease-backend:latest
```

### Cloud Deployment

#### AWS EC2

1. Launch Ubuntu 22.04 instance (t3.medium or higher)
2. Install Docker and Docker Compose
3. Clone repository
4. Configure environment variables
5. Run `docker-compose up -d`

#### Google Cloud Platform (GCP)

1. Create Compute Engine instance
2. Enable Cloud Run or App Engine
3. Deploy using Cloud Build or gcloud CLI

#### DigitalOcean

1. Create Droplet (Ubuntu 22.04)
2. Install Docker
3. Deploy using Docker Compose

#### Heroku

```bash
# Install Heroku CLI
heroku create crop-disease-api

# Add MongoDB addon
heroku addons:create mongolab

# Deploy
git push heroku main
```

For detailed deployment instructions, see: [backend/DEPLOYMENT.md](backend/DEPLOYMENT.md)

---

## 🧪 Testing

### Backend Tests

```bash
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_auth.py

# Run with verbose output
pytest -v
```

### Frontend Tests

```bash
cd frontend

# Run all tests
flutter test

# Run with coverage
flutter test --coverage

# Run integration tests
flutter drive --target=test_driver/app.dart
```

### Manual Testing

#### Test Backend Health

```bash
curl http://localhost:8000/health
```

#### Test Registration

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test User",
    "email": "test@example.com",
    "phone": "+919876543210",
    "password": "Test@123"
  }'
```

---

## 🤝 Contributing

We welcome contributions from the community! Here's how you can help:

### Ways to Contribute

1. 🐛 **Report Bugs**: Open an issue with detailed reproduction steps
2. 💡 **Suggest Features**: Share your ideas for improvements
3. 📝 **Improve Documentation**: Fix typos, add examples
4. 🔧 **Submit Code**: Fix bugs or implement new features

### Development Workflow

1. **Fork** the repository
2. **Clone** your fork:
   ```bash
   git clone https://github.com/Shyam-Sundar-Raju/Plant_disease_detection.git
   ```
3. **Create a branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```
4. **Make changes** and **commit**:
   ```bash
   git commit -m "Add: your feature description"
   ```
5. **Push** to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```
6. **Create Pull Request** on GitHub

### Code Style Guidelines

**Python (Backend):**
```bash
# Format code
black app/

# Check linting
flake8 app/

# Type checking
mypy app/
```

**Dart (Frontend):**
```bash
# Format code
flutter format lib/

# Analyze code
flutter analyze
```

### Commit Message Convention

```
Type: Brief description

- Add: New feature
- Fix: Bug fix
- Update: Dependency update
- Docs: Documentation changes
- Refactor: Code restructuring
- Test: Add or update tests
```

---

## 📄 License

This project is licensed under the **MIT License**.

```
MIT License

Copyright (c) 2025 Shyam Sundar Raju

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
```

See [LICENSE](LICENSE) file for full details.

---

## 👨‍💻 Authors & Acknowledgments

### Project Authors

**Shyam Sundar Raju**
- 📧 Email: contact@example.com
- 🔗 GitHub: [@yourusername](https://github.com/yourusername)
- 💼 LinkedIn: [Your LinkedIn](https://linkedin.com/in/yourprofile)

### Acknowledgments

- **PlantVillage Dataset**: Source of training data
- **TensorFlow Team**: Deep learning framework
- **FastAPI Community**: Modern Python web framework
- **Flutter Team**: Cross-platform UI framework
- **OpenAI**: Whisper speech recognition model
- **OpenWeatherMap**: Weather data API
- **MongoDB**: Database platform
- **Agricultural Experts**: Domain knowledge and validation

---

## 📞 Support

### Getting Help

- 📖 **Documentation**: Check this README and linked docs
- 💬 **Issues**: Open a [GitHub Issue](https://github.com/yourusername/Plant_disease_detection/issues)


### Reporting Issues

When reporting bugs, please include:
- OS and version
- Python/Flutter version
- Steps to reproduce
- Expected vs actual behavior
- Error messages/logs
- Screenshots (if applicable)

---

## 📊 Project Statistics

- **Languages**: Python, Dart, JavaScript
- **Total Lines of Code**: ~15,000+
- **API Endpoints**: 30+
- **Database Collections**: 6
- **Supported Languages**: 6
- **Disease Classes**: 19
- **Supported Crops**: 6

---

## 🌟 Star History

If you find this project useful, please consider giving it a ⭐ on GitHub!

[![Star History Chart](https://api.star-history.com/svg?repos=yourusername/Plant_disease_detection&type=Date)](https://star-history.com/#yourusername/Plant_disease_detection&Date)

---

## 🔗 Related Projects

- [PlantVillage Dataset](https://github.com/spMohanty/PlantVillage-Dataset)
- [TensorFlow Plant Disease Detection](https://github.com/tensorflow/models)
- [FastAPI Best Practices](https://github.com/zhanymkanov/fastapi-best-practices)

---

## 📢 Stay Updated

- 🌟 Star this repository
- 👀 Watch for releases
- 🔔 Enable notifications for updates

---

<div align="center">

**Built with ❤️ for farmers worldwide**

[⬆ Back to Top](#-ai-enabled-crop-disease-detection--remediation-system)

</div>
