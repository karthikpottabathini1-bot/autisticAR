"""
autisticAR - FastAPI Backend
Autism Support Assistant - Main application entry point
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from contextlib import asynccontextmanager
import uvicorn
import os
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from api.routes import router, set_global_services
from services.camera_service import CameraService
from services.model_service import ModelService
from services.navigation_service import NavigationService
from services.reading_assistant_service import ReadingAssistantService
from services.color_recognition_service import ColorRecognitionService
from services.people_counter_service import PeopleCounterService
from services.emotion_recognition_service import EmotionRecognitionService
from services.social_cues_service import SocialCuesService
from services.sensory_overload_service import SensoryOverloadService
from services.communication_helper_service import CommunicationHelperService
from services.routine_assistant_service import RoutineAssistantService
from services.body_language_service import BodyLanguageService
from services.ai_conversation_service import AIConversationService
from services.email_service import get_email_service

# Load .env file - try multiple locations
backend_dir = Path(__file__).parent
env_paths = [
    backend_dir / ".env",
    backend_dir.parent / ".env",
    backend_dir / ".env.example"
]

# Load .env file
env_loaded = False
for env_path in env_paths:
    if env_path.exists():
        load_dotenv(env_path, override=True)
        print(f"✓ Loaded .env from: {env_path}")
        env_loaded = True
        break

if not env_loaded:
    # Try default location (current directory)
    load_dotenv()
    print("⚠️  No .env file found in expected locations, using default")

# Debug: Check if GROQ_API_KEY is loaded
groq_key = os.environ.get("GROQ_API_KEY")
if groq_key:
    print(f"✓ GROQ_API_KEY found: {groq_key[:8]}...{groq_key[-4:] if len(groq_key) > 12 else '****'}")
else:
    print("⚠️  GROQ_API_KEY not found in environment variables!")
    print(f"   Checked paths: {[str(p) for p in env_paths]}")

# Global services
camera_service = CameraService()
model_service = ModelService()
navigation_service = None
reading_assistant_service = None
color_recognition_service = None
people_counter_service = None
emotion_recognition_service = None
social_cues_service = None
sensory_overload_service = None
communication_helper_service = None
routine_assistant_service = None
body_language_service = None
ai_conversation_service = None
scheduler = AsyncIOScheduler()


async def send_daily_summary_job():
    """Scheduled job to send daily summary email"""
    print("📧 Running scheduled daily summary...")
    email_service = get_email_service()
    if email_service.is_configured():
        await email_service.send_daily_summary()
    else:
        print("⚠️  Email not configured - skipping daily summary")


async def send_weekly_summary_job():
    """Scheduled job to send weekly report email"""
    print("📧 Running scheduled weekly report...")
    email_service = get_email_service()
    if email_service.is_configured():
        await email_service.send_weekly_report()
    else:
        print("⚠️  Email not configured - skipping weekly report")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan - startup and shutdown"""
    global navigation_service, reading_assistant_service, color_recognition_service, people_counter_service
    global emotion_recognition_service, social_cues_service, sensory_overload_service
    global communication_helper_service, routine_assistant_service, body_language_service, ai_conversation_service
    
    # Startup
    print("Initializing autisticAR backend...")
    print("🧠 autisticAR - Autism Support Assistant")
    await model_service.initialize()
    
    # Initialize new services
    navigation_service = NavigationService(model_service)
    reading_assistant_service = ReadingAssistantService(model_service)
    color_recognition_service = ColorRecognitionService(model_service)
    people_counter_service = PeopleCounterService(model_service)
    emotion_recognition_service = EmotionRecognitionService(model_service)
    social_cues_service = SocialCuesService(model_service)
    sensory_overload_service = SensoryOverloadService(model_service)
    communication_helper_service = CommunicationHelperService()
    routine_assistant_service = RoutineAssistantService()
    body_language_service = BodyLanguageService(model_service)
    ai_conversation_service = AIConversationService()
    
    # Set global services in routes module
    set_global_services(
        camera_service, 
        model_service,
        navigation_service,
        reading_assistant_service,
        color_recognition_service,
        people_counter_service,
        emotion_recognition_service,
        social_cues_service,
        sensory_overload_service,
        communication_helper_service,
        routine_assistant_service,
        body_language_service,
        ai_conversation_service
    )
    
    # Initialize email service
    email_service = get_email_service()
    
    # Setup email scheduler
    daily_hour = int(os.environ.get("EMAIL_DAILY_HOUR", "3"))  # Default 3 AM
    weekly_day = os.environ.get("EMAIL_WEEKLY_DAY", "friday").lower()
    weekly_hour = int(os.environ.get("EMAIL_WEEKLY_HOUR", "0"))  # Default midnight
    
    # Map day names to APScheduler format
    day_map = {
        "monday": "mon", "tuesday": "tue", "wednesday": "wed",
        "thursday": "thu", "friday": "fri", "saturday": "sat", "sunday": "sun"
    }
    weekly_day_short = day_map.get(weekly_day, "fri")
    
    # Add daily summary job (runs every day at specified hour)
    scheduler.add_job(
        send_daily_summary_job,
        CronTrigger(hour=daily_hour, minute=0),
        id="daily_summary",
        replace_existing=True
    )
    
    # Add weekly report job (runs on specified day at specified hour)
    scheduler.add_job(
        send_weekly_summary_job,
        CronTrigger(day_of_week=weekly_day_short, hour=weekly_hour, minute=0),
        id="weekly_report",
        replace_existing=True
    )
    
    scheduler.start()
    print(f"📧 Email scheduler started:")
    print(f"   • Daily summary: Every day at {daily_hour}:00")
    print(f"   • Weekly report: Every {weekly_day.capitalize()} at {weekly_hour}:00")
    
    yield
    
    # Shutdown
    print("Shutting down autisticAR backend...")
    scheduler.shutdown(wait=False)
    await camera_service.cleanup()
    await model_service.cleanup()

app = FastAPI(
    title="autisticAR API",
    description="Backend API for autisticAR - Autism Support Assistant. Helps autistic individuals understand emotions, social cues, and navigate daily life.",
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Vite default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router)

@app.get("/")
async def root():
    return {
        "message": "autisticAR - Autism Support Assistant",
        "version": "2.0.0",
        "purpose": "Helping autistic individuals understand emotions, social cues, and navigate daily life"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "camera_available": camera_service.is_available(),
        "models_loaded": model_service.are_models_loaded()
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

