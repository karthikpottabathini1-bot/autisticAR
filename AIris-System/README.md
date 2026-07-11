# autisticAR System

**autisticAR** is an AI-powered support assistant designed specifically for autistic individuals. It helps users understand emotions, navigate social situations, manage sensory environments, and build daily routines.

## Overview

This folder contains the **current, working version** of the autisticAR software. It includes:

- **FastAPI Backend** — AI services, emotion recognition, social cues analysis, sensory overload detection
- **React Frontend** — Interactive interface with real-time camera processing and voice support

### Features

| Mode | Status | Description |
|:-----|:------:|:------------|
| **Emotion Recognition** | ✅ Working | Detects and explains facial emotions in real-time |
| **Social Cues** | ✅ Working | Analyzes social situations and provides concrete guidance |
| **Sensory Overload** | ✅ Working | Monitors environment for overwhelming sensory factors |
| **Communication Helper** | ✅ Working | Suggests responses and provides social scripts |
| **Routine Assistant** | ✅ Working | Helps with daily routines, schedules, and transitions |
| **Scene Description** | ✅ Working | Continuous environment analysis with safety alerts |

## Architecture

```
AIris-System/
├── backend/
│   ├── api/                  # FastAPI routes
│   │   └── routes.py         # REST and WebSocket endpoints
│   ├── services/             # Core AI services
│   │   ├── emotion_recognition_service.py    # Facial emotion detection
│   │   ├── social_cues_service.py            # Social situation analysis
│   │   ├── sensory_overload_service.py       # Sensory environment monitoring
│   │   ├── communication_helper_service.py   # Response suggestions
│   │   ├── routine_assistant_service.py      # Daily routine support
│   │   ├── scene_description_service.py      # Scene analysis
│   │   ├── camera_service.py                 # Camera handling
│   │   ├── model_service.py                  # YOLO, MediaPipe, emotion models
│   │   └── email_service.py                  # Guardian alerts
│   ├── models/               # Pydantic schemas
│   ├── utils/                # Helper utilities
│   ├── main.py               # FastAPI entry point
│   └── requirements.txt      # Python dependencies
│
└── frontend/
    ├── src/
    │   ├── components/       # React components
    │   ├── services/         # API client
    │   └── App.tsx           # Main application
    ├── package.json
    └── vite.config.ts
```

## Prerequisites

- **Python 3.10+**
- **Node.js 18+**
- **Groq API Key** — Get free at [console.groq.com](https://console.groq.com)
- **Computer with webcam and microphone** — Built-in hardware works perfectly

## Quick Setup

See [QUICKSTART.md](./QUICKSTART.md) for step-by-step instructions.

### Backend

```bash
cd backend

# Create environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
echo "GROQ_API_KEY=your_key_here" > .env

# Run server
python main.py
```

Backend runs at `http://localhost:8000`

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Run dev server
npm run dev
```

Frontend runs at `http://localhost:5173`

## Usage

1. Start the backend server
2. Start the frontend dev server
3. Open `http://localhost:5173` in your browser
4. Click "Start Camera" to enable video feed
5. Choose a mode:
   - **Emotion Recognition**: Understand what people are feeling
   - **Social Cues**: Get guidance on social situations
   - **Sensory Overload**: Monitor your environment
   - **Communication Helper**: Get help with conversations
   - **Routine Assistant**: Manage daily routines
   - **Scene Description**: Continuous environment awareness

### Keyboard Shortcuts

- **1** - Emotion Recognition
- **2** - Social Cues
- **3** - Sensory Overload
- **4** - Communication Helper
- **5** - Routine Assistant
- **6** - Scene Description

### Voice Mode

Enable **Voice-Only Mode** for hands-free operation:
- Click the microphone icon in the header to enable
- Use voice commands to control the system
- All instructions and descriptions are automatically spoken
- Perfect for users who prefer audio feedback

## API Documentation

Once the backend is running, visit `http://localhost:8000/docs` for interactive API documentation.

## Environment Variables

### Backend (.env)
```bash
# Required
GROQ_API_KEY=your_groq_api_key

# Optional - Model Configuration
YOLO_MODEL_PATH=yolo26s.pt        # Default: yolo26s.pt (auto-downloads if missing)

# Optional - Email/Guardian Features
EMAIL_SENDER=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
EMAIL_RECIPIENT=guardian@example.com
EMAIL_DAILY_HOUR=3                # Daily summary at 3 AM (default)
EMAIL_WEEKLY_DAY=friday           # Weekly report day (default)
EMAIL_WEEKLY_HOUR=0                # Weekly report hour (default: midnight)
```

### Frontend (.env)
```bash
VITE_API_BASE_URL=http://localhost:8000  # Optional, default shown
```

## Tech Stack

| Component | Technology |
|:----------|:-----------|
| Backend | FastAPI, Python 3.10+ |
| Object Detection | YOLO26s (Ultralytics) |
| Face Detection | MediaPipe |
| Emotion Recognition | Deep Learning Models |
| LLM Reasoning | Groq API (GPT OSS 120B) |
| Speech-to-Text | Web Speech API |
| Text-to-Speech | Web Speech API |
| Email Notifications | aiosmtplib (Gmail SMTP) |
| Frontend | React, TypeScript, Vite |
| Styling | Tailwind CSS v4 |

## Key Features

### 😊 Emotion Recognition
- **Real-time Detection**: Identifies facial emotions (happy, sad, angry, surprised, neutral, fearful, disgusted)
- **Clear Explanations**: Concrete descriptions of what emotions look like
- **Social Guidance**: Actionable tips on how to respond
- **Visual Feedback**: Color-coded emotion indicators

### 👥 Social Cues
- **Situation Analysis**: Understands social context
- **Response Suggestions**: Concrete scripts for different situations
- **What to Avoid**: Clear guidance on what not to do
- **Context-Aware**: Adapts to different social scenarios

### 🌊 Sensory Overload Detection
- **Environment Monitoring**: Detects crowd density, brightness, movement, visual complexity
- **Early Warnings**: Alerts before overload occurs
- **Coping Strategies**: Concrete suggestions for managing sensory input
- **Real-time Analysis**: Continuous monitoring of sensory factors

### 💬 Communication Helper
- **Social Scripts**: Pre-written responses for common situations
- **Conversation Starters**: Help initiating conversations
- **Response Suggestions**: Real-time help during conversations
- **Emotion Response Guide**: How to respond to different emotions

### 📋 Routine Assistant
- **Daily Routines**: Create and follow structured routines
- **Step-by-Step Guidance**: Track progress through routines
- **Transition Support**: Help moving between activities
- **Custom Routines**: Create personalized routines

### 🔍 Scene Description
- **Continuous Analysis**: Real-time environment understanding
- **Safety Alerts**: Automatic notifications for concerning situations
- **Object Detection**: Identifies objects and people in the environment
- **Voice Control**: Full handsfree operation

## License

MIT
