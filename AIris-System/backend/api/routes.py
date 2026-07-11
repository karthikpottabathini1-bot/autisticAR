"""
API Routes for autisticAR Backend
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import json
import base64
import cv2
import numpy as np
import time
import asyncio
import os
from io import BytesIO

from services.camera_service import CameraService
from services.model_service import ModelService
from services.activity_guide_service import ActivityGuideService
from services.scene_description_service import SceneDescriptionService
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
from services.tts_service import TTSService
from services.stt_service import STTService
from services.email_service import get_email_service
from models.schemas import (
    TaskRequest, TaskResponse, GuidanceResponse, 
    SceneDescriptionRequest, SceneDescriptionResponse,
    FeedbackRequest, CameraStatusResponse
)

router = APIRouter(prefix="/api/v1", tags=["airis"])

# Services will be initialized in main.py and passed here
_camera_service: CameraService = None
_model_service: ModelService = None
_activity_guide_service: ActivityGuideService = None
_scene_description_service: SceneDescriptionService = None
_navigation_service: NavigationService = None
_reading_assistant_service: ReadingAssistantService = None
_color_recognition_service: ColorRecognitionService = None
_people_counter_service: PeopleCounterService = None
_emotion_recognition_service: EmotionRecognitionService = None
_social_cues_service: SocialCuesService = None
_sensory_overload_service: SensoryOverloadService = None
_communication_helper_service: CommunicationHelperService = None
_routine_assistant_service: RoutineAssistantService = None
_body_language_service: BodyLanguageService = None
_ai_conversation_service: AIConversationService = None
_tts_service: TTSService = None
_stt_service: STTService = None

def set_global_services(
    camera: CameraService, 
    model: ModelService,
    navigation: NavigationService = None,
    reading_assistant: ReadingAssistantService = None,
    color_recognition: ColorRecognitionService = None,
    people_counter: PeopleCounterService = None,
    emotion_recognition: EmotionRecognitionService = None,
    social_cues: SocialCuesService = None,
    sensory_overload: SensoryOverloadService = None,
    communication_helper: CommunicationHelperService = None,
    routine_assistant: RoutineAssistantService = None,
    body_language: BodyLanguageService = None,
    ai_conversation: AIConversationService = None
):
    """Set global services from main.py"""
    global _camera_service, _model_service, _scene_description_service, _activity_guide_service
    global _navigation_service, _reading_assistant_service, _color_recognition_service, _people_counter_service
    global _emotion_recognition_service, _social_cues_service, _sensory_overload_service
    global _communication_helper_service, _routine_assistant_service, _body_language_service, _ai_conversation_service
    
    _camera_service = camera
    _model_service = model
    _navigation_service = navigation
    _reading_assistant_service = reading_assistant
    _color_recognition_service = color_recognition
    _people_counter_service = people_counter
    _emotion_recognition_service = emotion_recognition
    _social_cues_service = social_cues
    _sensory_overload_service = sensory_overload
    _communication_helper_service = communication_helper
    _routine_assistant_service = routine_assistant
    _body_language_service = body_language
    _ai_conversation_service = ai_conversation
    
    # Eagerly initialize services that need Groq so we see any errors at startup
    print("\n📦 Initializing AI services...")
    _scene_description_service = SceneDescriptionService(_model_service)
    _activity_guide_service = ActivityGuideService(_model_service)
    print("📦 AI services initialized.\n")

def get_camera_service() -> CameraService:
    global _camera_service
    if _camera_service is None:
        _camera_service = CameraService()
    return _camera_service

def get_model_service() -> ModelService:
    global _model_service
    if _model_service is None:
        raise RuntimeError("Model service not initialized. This should be set during app startup.")
    return _model_service

def get_activity_guide_service() -> ActivityGuideService:
    global _activity_guide_service, _model_service
    if _activity_guide_service is None:
        if _model_service is None:
            raise RuntimeError("Model service not initialized. This should be set during app startup.")
        _activity_guide_service = ActivityGuideService(_model_service)
    return _activity_guide_service

def get_scene_description_service() -> SceneDescriptionService:
    global _scene_description_service, _model_service
    if _scene_description_service is None:
        if _model_service is None:
            raise RuntimeError("Model service not initialized. This should be set during app startup.")
        _scene_description_service = SceneDescriptionService(_model_service)
    return _scene_description_service

def get_tts_service() -> TTSService:
    global _tts_service
    if _tts_service is None:
        _tts_service = TTSService()
    return _tts_service

def get_stt_service() -> STTService:
    global _stt_service
    if _stt_service is None:
        _stt_service = STTService()
    return _stt_service

def get_navigation_service() -> NavigationService:
    global _navigation_service
    if _navigation_service is None:
        raise RuntimeError("Navigation service not initialized. This should be set during app startup.")
    return _navigation_service

def get_reading_assistant_service() -> ReadingAssistantService:
    global _reading_assistant_service
    if _reading_assistant_service is None:
        raise RuntimeError("Reading assistant service not initialized. This should be set during app startup.")
    return _reading_assistant_service

def get_color_recognition_service() -> ColorRecognitionService:
    global _color_recognition_service
    if _color_recognition_service is None:
        raise RuntimeError("Color recognition service not initialized. This should be set during app startup.")
    return _color_recognition_service

def get_people_counter_service() -> PeopleCounterService:
    global _people_counter_service
    if _people_counter_service is None:
        raise RuntimeError("People counter service not initialized. This should be set during app startup.")
    return _people_counter_service

def get_emotion_recognition_service() -> EmotionRecognitionService:
    global _emotion_recognition_service
    if _emotion_recognition_service is None:
        raise RuntimeError("Emotion recognition service not initialized. This should be set during app startup.")
    return _emotion_recognition_service

def get_social_cues_service() -> SocialCuesService:
    global _social_cues_service
    if _social_cues_service is None:
        raise RuntimeError("Social cues service not initialized. This should be set during app startup.")
    return _social_cues_service

def get_sensory_overload_service() -> SensoryOverloadService:
    global _sensory_overload_service
    if _sensory_overload_service is None:
        raise RuntimeError("Sensory overload service not initialized. This should be set during app startup.")
    return _sensory_overload_service

def get_communication_helper_service() -> CommunicationHelperService:
    global _communication_helper_service
    if _communication_helper_service is None:
        raise RuntimeError("Communication helper service not initialized. This should be set during app startup.")
    return _communication_helper_service

def get_routine_assistant_service() -> RoutineAssistantService:
    global _routine_assistant_service
    if _routine_assistant_service is None:
        raise RuntimeError("Routine assistant service not initialized. This should be set during app startup.")
    return _routine_assistant_service

def get_body_language_service() -> BodyLanguageService:
    global _body_language_service
    if _body_language_service is None:
        raise RuntimeError("Body language service not initialized.")
    return _body_language_service

def get_ai_conversation_service() -> AIConversationService:
    global _ai_conversation_service
    if _ai_conversation_service is None:
        raise RuntimeError("AI conversation service not initialized.")
    return _ai_conversation_service

# ==================== Camera Endpoints ====================
class CameraConfigRequest(BaseModel):
    source_type: str  # "webcam" or "esp32"
    ip_address: Optional[str] = None

class ESP32WiFiProvisionRequest(BaseModel):
    ssid: str
    password: str = ""

@router.post("/camera/config")
async def set_camera_config(config: CameraConfigRequest):
    """Set camera configuration"""
    camera_service = get_camera_service()
    await camera_service.set_config(config.source_type, config.ip_address)
    return {"status": "success", "message": "Camera configuration updated"}

@router.post("/camera/esp32/provision-wifi")
async def provision_esp32_wifi(request: ESP32WiFiProvisionRequest):
    """Provision WiFi credentials to ESP32-CAM in setup mode"""
    import aiohttp
    import asyncio
    
    if not request.ssid:
        raise HTTPException(status_code=400, detail="SSID is required")
    
    # ESP32 in AP mode is always at 192.168.4.1
    setup_url = f"http://192.168.4.1/set-wifi?ssid={request.ssid}&pass={request.password}"
    
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
            async with session.get(setup_url) as response:
                if response.status == 200:
                    return {
                        "status": "success",
                        "success": True,
                        "message": "Credentials received! The camera is restarting. Please reconnect your PC to your Home WiFi now."
                    }
                else:
                    error_text = await response.text()
                    return {
                        "status": "error",
                        "success": False,
                        "message": f"Error: {error_text}"
                    }
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=408,
            detail="Connection timeout. Are you connected to ESP32-CAM-SETUP network?"
        )
    except aiohttp.ClientError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Connection failed: {str(e)}. Are you connected to ESP32-CAM-SETUP network?"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/camera/start")
async def start_camera():
    """Start the camera feed"""
    try:
        camera_service = get_camera_service()
        success = await camera_service.start()
        if success:
            return {"status": "success", "message": "Camera started"}
        else:
            raise HTTPException(status_code=500, detail="Failed to start camera")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/camera/stop")
async def stop_camera():
    """Stop the camera feed"""
    try:
        camera_service = get_camera_service()
        await camera_service.stop()
        return {"status": "success", "message": "Camera stopped"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/camera/status")
async def get_camera_status():
    """Get camera status"""
    camera_service = get_camera_service()
    return {
        "is_running": camera_service.is_running(),
        "is_available": camera_service.is_available()
    }

@router.get("/camera/frame")
async def get_camera_frame():
    """Get a single frame from the camera"""
    camera_service = get_camera_service()
    frame = await camera_service.get_frame()
    if frame is None:
        raise HTTPException(status_code=404, detail="No frame available")
    
    # Encode frame as JPEG
    _, buffer = cv2.imencode('.jpg', frame)
    frame_bytes = buffer.tobytes()
    
    return StreamingResponse(
        BytesIO(frame_bytes),
        media_type="image/jpeg"
    )

@router.websocket("/camera/stream")
async def camera_stream(websocket: WebSocket):
    """WebSocket endpoint for streaming camera frames with optimized frame rate"""
    await websocket.accept()
    camera_service = get_camera_service()
    
    # Adaptive frame rate based on source type
    frame_interval = 0.033  # Default ~30 FPS for webcam (1/30 seconds)
    if camera_service.source_type == "esp32":
        frame_interval = 0.05  # ~20 FPS for ESP32 (more stable, reduces network load)
    
    last_frame_sent_time = 0
    
    try:
        while True:
            current_time = time.time()
            
            # Frame rate control: Ensure minimum time between frames
            # This prevents encoding/sending frames too quickly, saving CPU and bandwidth
            time_since_last_frame = current_time - last_frame_sent_time
            if time_since_last_frame < frame_interval:
                # Calculate exact sleep time needed to maintain target frame rate
                sleep_time = frame_interval - time_since_last_frame
                await asyncio.sleep(sleep_time)
                # After sleeping, update current time and proceed
                current_time = time.time()
            
            # Get frame from camera service
            frame = await camera_service.get_frame()
            if frame is None:
                await websocket.send_json({"error": "No frame available"})
                await asyncio.sleep(0.1)  # Wait a bit before retrying
                continue
            
            # Encode frame as JPEG with quality based on source
            # Lower quality for ESP32 = smaller file size = faster transmission = smoother playback
            jpeg_quality = 90 if camera_service.source_type == "webcam" else 75
            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, jpeg_quality])
            frame_bytes = buffer.tobytes()
            frame_base64 = base64.b64encode(frame_bytes).decode()
            
            # Send frame to client
            await websocket.send_json({
                "type": "frame",
                "data": frame_base64,
                "timestamp": camera_service.get_timestamp()
            })
            
            # Update timestamp after successful send
            last_frame_sent_time = time.time()
            
            # Small yield to allow other async tasks to run
            await asyncio.sleep(0.001)
    except WebSocketDisconnect:
        print("Client disconnected from camera stream")
    except Exception as e:
        print(f"Error in camera stream: {e}")
        import traceback
        traceback.print_exc()
        try:
            await websocket.close()
        except:
            pass

# ==================== Activity Guide Endpoints ====================

@router.post("/activity-guide/start-task", response_model=TaskResponse)
async def start_task(request: TaskRequest):
    """Start a new activity guide task"""
    try:
        activity_guide_service = get_activity_guide_service()
        result = await activity_guide_service.start_task(
            goal=request.goal,
            target_objects=request.target_objects
        )
        return TaskResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/activity-guide/process-frame")
async def process_activity_frame():
    """Process a frame for activity guide mode"""
    try:
        camera_service = get_camera_service()
        activity_guide_service = get_activity_guide_service()
        frame = await camera_service.get_frame()
        if frame is None:
            raise HTTPException(status_code=404, detail="No frame available")
        
        result = await activity_guide_service.process_frame(frame)
        
        # Encode processed frame (always process, even when idle, to show YOLO boxes)
        processed_frame = result.get("annotated_frame", frame)
        if processed_frame is None:
            processed_frame = frame
        
        try:
            _, buffer = cv2.imencode('.jpg', processed_frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
            frame_bytes = buffer.tobytes()
            frame_base64 = base64.b64encode(frame_bytes).decode()
        except Exception as e:
            print(f"Error encoding frame: {e}")
            # Fallback: encode original frame
            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
            frame_bytes = buffer.tobytes()
            frame_base64 = base64.b64encode(frame_bytes).decode()
        
        return {
            "frame": frame_base64,
            "guidance": result.get("guidance"),
            "stage": result.get("stage"),
            "instruction": result.get("instruction"),
            "detected_objects": result.get("detected_objects", []),
            "hand_detected": result.get("hand_detected", False)
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in process_activity_frame: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error processing frame: {str(e)}")

class FrameUploadRequest(BaseModel):
    frame: str  # base64 encoded JPEG frame

@router.post("/activity-guide/process-frame-upload")
async def process_activity_frame_upload(request: FrameUploadRequest):
    """Process a frame uploaded from the browser camera"""
    try:
        activity_guide_service = get_activity_guide_service()
        
        # Decode base64 frame to numpy array
        frame_bytes = base64.b64decode(request.frame)
        nparr = np.frombuffer(frame_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if frame is None:
            raise HTTPException(status_code=400, detail="Invalid frame data")
        
        result = await activity_guide_service.process_frame(frame)
        
        # Encode processed frame
        processed_frame = result.get("annotated_frame", frame)
        if processed_frame is None:
            processed_frame = frame
        
        try:
            _, buffer = cv2.imencode('.jpg', processed_frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
            frame_bytes = buffer.tobytes()
            frame_base64 = base64.b64encode(frame_bytes).decode()
        except Exception as e:
            print(f"Error encoding frame: {e}")
            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
            frame_bytes = buffer.tobytes()
            frame_base64 = base64.b64encode(frame_bytes).decode()
        
        return {
            "frame": frame_base64,
            "guidance": result.get("guidance"),
            "stage": result.get("stage"),
            "instruction": result.get("instruction"),
            "detected_objects": result.get("detected_objects", []),
            "hand_detected": result.get("hand_detected", False)
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in process_activity_frame_upload: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error processing frame: {str(e)}")

@router.post("/scene-description/process-frame-upload")
async def process_scene_frame_upload(request: FrameUploadRequest):
    """Process a scene description frame uploaded from the browser camera"""
    try:
        scene_description_service = get_scene_description_service()
        
        # Decode base64 frame to numpy array
        frame_bytes = base64.b64decode(request.frame)
        nparr = np.frombuffer(frame_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if frame is None:
            raise HTTPException(status_code=400, detail="Invalid frame data")
        
        result = await scene_description_service.process_frame(frame)
        
        # Encode processed frame
        processed_frame = result.get("annotated_frame", frame)
        if processed_frame is None:
            processed_frame = frame
        
        try:
            _, buffer = cv2.imencode('.jpg', processed_frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
            frame_bytes = buffer.tobytes()
            frame_base64 = base64.b64encode(frame_bytes).decode()
        except Exception as e:
            print(f"Error encoding frame: {e}")
            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
            frame_bytes = buffer.tobytes()
            frame_base64 = base64.b64encode(frame_bytes).decode()
        
        return {
            "frame": frame_base64,
            "description": result.get("description"),
            "summary": result.get("summary"),
            "safety_alert": result.get("safety_alert", False),
            "risk_score": result.get("risk_score"),
            "risk_factors": result.get("risk_factors", []),
            "confidence": result.get("confidence"),
            "is_recording": result.get("is_recording", False),
            "stats": result.get("stats"),
            "recent_observations": result.get("recent_observations", []),
            "fall_alert_sent": result.get("fall_alert_sent", False),
            "alert_sent": result.get("alert_sent", False)
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in process_scene_frame_upload: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error processing frame: {str(e)}")

@router.post("/activity-guide/feedback")
async def submit_feedback(request: FeedbackRequest):
    """Submit feedback for activity guide"""
    try:
        activity_guide_service = get_activity_guide_service()
        result = await activity_guide_service.handle_feedback(
            confirmed=request.confirmed,
            feedback_text=request.feedback_text
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/activity-guide/status")
async def get_activity_guide_status():
    """Get current activity guide status"""
    activity_guide_service = get_activity_guide_service()
    return activity_guide_service.get_status()

@router.post("/activity-guide/reset")
async def reset_activity_guide():
    """Reset the activity guide state"""
    activity_guide_service = get_activity_guide_service()
    activity_guide_service.reset()
    return {"status": "success", "message": "Activity guide reset"}

class CameraOrientationRequest(BaseModel):
    facing_towards_user: bool

@router.post("/activity-guide/set-camera-orientation")
async def set_camera_orientation(request: CameraOrientationRequest):
    """Set camera orientation for activity guide"""
    activity_guide_service = get_activity_guide_service()
    activity_guide_service.set_camera_orientation(request.facing_towards_user)
    return {
        "status": "success",
        "message": f"Camera orientation set to {'facing towards user' if request.facing_towards_user else 'facing away from user'}",
        "facing_towards_user": request.facing_towards_user
    }

# ==================== Scene Description Endpoints ====================

@router.post("/scene-description/start-recording")
async def start_recording():
    """Start scene description recording"""
    try:
        scene_description_service = get_scene_description_service()
        result = await scene_description_service.start_recording()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/scene-description/stop-recording")
async def stop_recording():
    """Stop scene description recording and save log"""
    try:
        scene_description_service = get_scene_description_service()
        result = await scene_description_service.stop_recording()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/scene-description/process-frame")
async def process_scene_frame():
    """Process a frame for scene description mode"""
    camera_service = get_camera_service()
    scene_description_service = get_scene_description_service()
    frame = await camera_service.get_frame()
    if frame is None:
        raise HTTPException(status_code=404, detail="No frame available")
    
    result = await scene_description_service.process_frame(frame)
    
    # Encode processed frame
    processed_frame = result.get("annotated_frame", frame)
    _, buffer = cv2.imencode('.jpg', processed_frame)
    frame_bytes = buffer.tobytes()
    frame_base64 = base64.b64encode(frame_bytes).decode()
    
    return {
        "frame": frame_base64,
        "description": result.get("description"),
        "summary": result.get("summary"),
        "safety_alert": result.get("safety_alert", False),
        "is_recording": result.get("is_recording", False)
    }

@router.get("/scene-description/logs")
async def get_recording_logs():
    """Get all recording logs"""
    scene_description_service = get_scene_description_service()
    logs = scene_description_service.get_logs()
    return {"logs": logs}

@router.get("/scene-description/log/{log_id}")
async def get_recording_log(log_id: str):
    """Get a specific recording log"""
    scene_description_service = get_scene_description_service()
    log = scene_description_service.get_log(log_id)
    if log is None:
        raise HTTPException(status_code=404, detail="Log not found")
    return log

# ==================== Text-to-Speech Endpoints ====================

@router.post("/tts/generate")
async def generate_speech(text: str):
    """Generate speech from text"""
    try:
        tts_service = get_tts_service()
        audio_data = await tts_service.generate(text)
        if audio_data:
            return JSONResponse({
                "audio_base64": base64.b64encode(audio_data).decode(),
                "duration": tts_service.estimate_duration(text)
            })
        else:
            raise HTTPException(status_code=500, detail="Failed to generate speech")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tts/stream/{text}")
async def stream_speech(text: str):
    """Stream speech audio"""
    try:
        tts_service = get_tts_service()
        audio_data = await tts_service.generate(text)
        if audio_data:
            return StreamingResponse(
                BytesIO(audio_data),
                media_type="audio/mpeg"
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to generate speech")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Speech-to-Text Endpoints ====================

@router.post("/stt/transcribe")
async def transcribe_audio(audio: UploadFile = File(...), sample_rate: int = 16000):
    """Transcribe audio to text using free offline Whisper model"""
    try:
        stt_service = get_stt_service()
        
        # Read audio file
        audio_data = await audio.read()
        
        # Transcribe
        transcription = await stt_service.transcribe(audio_data, sample_rate)
        
        if transcription:
            return JSONResponse({
                "text": transcription,
                "success": True
            })
        else:
            raise HTTPException(status_code=500, detail="Failed to transcribe audio")
    except Exception as e:
        print(f"STT error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/stt/transcribe-base64")
async def transcribe_audio_base64(request: Dict[str, Any]):
    """Transcribe base64-encoded audio to text"""
    try:
        stt_service = get_stt_service()
        
        audio_base64 = request.get("audio_base64")
        sample_rate = request.get("sample_rate", 16000)
        
        if not audio_base64:
            raise HTTPException(status_code=400, detail="audio_base64 is required")
        
        # Decode base64
        audio_data = base64.b64decode(audio_base64)
        
        # Transcribe
        transcription = await stt_service.transcribe(audio_data, sample_rate)
        
        if transcription:
            return JSONResponse({
                "text": transcription,
                "success": True
            })
        else:
            raise HTTPException(status_code=500, detail="Failed to transcribe audio")
    except Exception as e:
        print(f"STT error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Email Notification Endpoints ====================

@router.get("/email/status")
async def get_email_status():
    """Get email service configuration status"""
    email_service = get_email_service()
    return {
        "configured": email_service.is_configured(),
        "sender": email_service.config.sender_email if email_service.config else None,
        "recipient": email_service.config.recipient_email if email_service.config else None,
        "cooldown_minutes": email_service.alert_cooldown_minutes,
        "pending_events": len(email_service.daily_events)
    }

@router.post("/email/test")
async def send_test_email():
    """Send a test email to verify configuration"""
    email_service = get_email_service()
    
    if not email_service.is_configured():
        raise HTTPException(
            status_code=400, 
            detail="Email not configured. Please set EMAIL_SENDER, EMAIL_PASSWORD, and EMAIL_RECIPIENT in .env"
        )
    
    print(f"📧 Sending test email to: {email_service.config.recipient_email}")
    
    try:
        success = await email_service.send_test_email()
        
        if success:
            return {"status": "success", "message": "Test email sent successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to send test email - check server logs")
    except Exception as e:
        print(f"❌ Test email error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send test email: {str(e)}")

@router.post("/email/test-alert")
async def send_test_alert_email():
    """Send a dummy safety alert email for testing"""
    email_service = get_email_service()
    
    if not email_service.is_configured():
        raise HTTPException(status_code=400, detail="Email not configured")
    
    # Dummy alert data
    from datetime import datetime
    success = await email_service.send_safety_alert(
        summary="Person appears to have fallen near the kitchen counter. They are lying on the floor and have not moved for several seconds.",
        raw_descriptions=[
            "a person lying on the kitchen floor",
            "kitchen with counter and stove visible",
            "a knocked over chair nearby",
            "person not moving",
            "arms extended on the ground"
        ],
        timestamp=datetime.now()
    )
    
    # Reset cooldown for testing purposes
    email_service.last_alert_time = None
    
    if success:
        return {"status": "success", "message": "Test alert email sent"}
    else:
        raise HTTPException(status_code=500, detail="Failed to send test alert email")

@router.post("/email/test-daily")
async def send_test_daily_email():
    """Send a dummy daily summary email for testing"""
    email_service = get_email_service()
    
    if not email_service.is_configured():
        raise HTTPException(status_code=400, detail="Email not configured")
    
    from datetime import datetime, timedelta
    from services.email_service import ActivityEvent
    
    # Store original events
    original_daily = email_service.daily_events.copy()
    original_hourly = dict(email_service.hourly_activity)
    
    # Create dummy events
    now = datetime.now()
    dummy_events = [
        ActivityEvent(
            timestamp=now.replace(hour=8, minute=15),
            event_type="OBSERVATION",
            summary="Person preparing breakfast in the kitchen, moving around the counter area.",
            location="kitchen",
            descriptions=["person standing at counter", "kitchen appliances visible"]
        ),
        ActivityEvent(
            timestamp=now.replace(hour=10, minute=30),
            event_type="OBSERVATION",
            summary="Person seated on the couch watching television in the living room.",
            location="living room",
            descriptions=["person sitting on couch", "television on", "living room"]
        ),
        ActivityEvent(
            timestamp=now.replace(hour=12, minute=45),
            event_type="OBSERVATION",
            summary="Person eating lunch at the dining table.",
            location="dining room",
            descriptions=["person at table", "eating meal", "dining area"]
        ),
        ActivityEvent(
            timestamp=now.replace(hour=14, minute=20),
            event_type="SAFETY_ALERT",
            summary="Person stumbled near the stairs but regained balance. No fall occurred.",
            location="stairs",
            descriptions=["person near stairs", "grabbed railing", "regained balance"]
        ),
        ActivityEvent(
            timestamp=now.replace(hour=16, minute=0),
            event_type="OBSERVATION",
            summary="Person resting in the bedroom.",
            location="bedroom",
            descriptions=["person lying on bed", "bedroom visible", "resting"]
        ),
        ActivityEvent(
            timestamp=now.replace(hour=18, minute=30),
            event_type="OBSERVATION",
            summary="Person preparing dinner in the kitchen.",
            location="kitchen",
            descriptions=["person at stove", "cooking", "kitchen"]
        ),
    ]
    
    # Set dummy data
    email_service.daily_events = dummy_events
    email_service.hourly_activity = {8: 2, 10: 1, 12: 1, 14: 1, 16: 1, 18: 2}
    
    # Send email
    success = await email_service.send_daily_summary(force=True)
    
    # Restore original events
    email_service.daily_events = original_daily
    email_service.hourly_activity = original_hourly
    
    if success:
        return {"status": "success", "message": "Test daily summary email sent"}
    else:
        raise HTTPException(status_code=500, detail="Failed to send test daily summary email")

@router.post("/email/test-weekly")
async def send_test_weekly_email():
    """Send a dummy weekly report email for testing"""
    email_service = get_email_service()
    
    if not email_service.is_configured():
        raise HTTPException(status_code=400, detail="Email not configured")
    
    from datetime import datetime, timedelta
    from services.email_service import ActivityEvent
    
    # Store original events
    original_weekly = email_service.weekly_events.copy()
    
    # Create dummy events for a week
    now = datetime.now()
    dummy_events = []
    
    # Monday - normal day
    monday = now - timedelta(days=6)
    dummy_events.extend([
        ActivityEvent(timestamp=monday.replace(hour=9), event_type="OBSERVATION", summary="Morning routine in kitchen", location="kitchen", descriptions=[]),
        ActivityEvent(timestamp=monday.replace(hour=14), event_type="OBSERVATION", summary="Afternoon in living room", location="living room", descriptions=[]),
        ActivityEvent(timestamp=monday.replace(hour=19), event_type="OBSERVATION", summary="Evening dinner preparation", location="kitchen", descriptions=[]),
    ])
    
    # Tuesday - alert day
    tuesday = now - timedelta(days=5)
    dummy_events.extend([
        ActivityEvent(timestamp=tuesday.replace(hour=8), event_type="OBSERVATION", summary="Breakfast in kitchen", location="kitchen", descriptions=[]),
        ActivityEvent(timestamp=tuesday.replace(hour=11), event_type="SAFETY_ALERT", summary="Person slipped in bathroom but caught themselves on the sink.", location="bathroom", descriptions=["person in bathroom", "slipped", "grabbed sink"]),
        ActivityEvent(timestamp=tuesday.replace(hour=16), event_type="OBSERVATION", summary="Reading in bedroom", location="bedroom", descriptions=[]),
    ])
    
    # Wednesday - normal day
    wednesday = now - timedelta(days=4)
    dummy_events.extend([
        ActivityEvent(timestamp=wednesday.replace(hour=10), event_type="OBSERVATION", summary="Morning activities in living room", location="living room", descriptions=[]),
        ActivityEvent(timestamp=wednesday.replace(hour=13), event_type="OBSERVATION", summary="Lunch in dining room", location="dining room", descriptions=[]),
        ActivityEvent(timestamp=wednesday.replace(hour=20), event_type="OBSERVATION", summary="Evening relaxation", location="living room", descriptions=[]),
    ])
    
    # Thursday - normal day
    thursday = now - timedelta(days=3)
    dummy_events.extend([
        ActivityEvent(timestamp=thursday.replace(hour=7), event_type="OBSERVATION", summary="Early morning in kitchen", location="kitchen", descriptions=[]),
        ActivityEvent(timestamp=thursday.replace(hour=15), event_type="OBSERVATION", summary="Afternoon nap in bedroom", location="bedroom", descriptions=[]),
    ])
    
    # Friday - alert day
    friday = now - timedelta(days=2)
    dummy_events.extend([
        ActivityEvent(timestamp=friday.replace(hour=12), event_type="OBSERVATION", summary="Midday activities", location="kitchen", descriptions=[]),
        ActivityEvent(timestamp=friday.replace(hour=17), event_type="SAFETY_ALERT", summary="Smoke detected from kitchen - burnt toast, no fire.", location="kitchen", descriptions=["smoke visible", "kitchen", "toaster"]),
    ])
    
    # Saturday & Sunday - normal
    saturday = now - timedelta(days=1)
    dummy_events.extend([
        ActivityEvent(timestamp=saturday.replace(hour=10), event_type="OBSERVATION", summary="Weekend morning routine", location="kitchen", descriptions=[]),
        ActivityEvent(timestamp=saturday.replace(hour=14), event_type="OBSERVATION", summary="Afternoon in living room", location="living room", descriptions=[]),
        ActivityEvent(timestamp=now.replace(hour=9), event_type="OBSERVATION", summary="Sunday morning", location="bedroom", descriptions=[]),
    ])
    
    # Set dummy data
    email_service.weekly_events = dummy_events
    
    # Send email
    success = await email_service.send_weekly_report()
    
    # Restore original events
    email_service.weekly_events = original_weekly
    
    if success:
        return {"status": "success", "message": "Test weekly report email sent"}
    else:
        raise HTTPException(status_code=500, detail="Failed to send test weekly report email")

@router.post("/email/send-daily-summary")
async def trigger_daily_summary():
    """Manually trigger sending a daily summary email"""
    email_service = get_email_service()
    
    if not email_service.is_configured():
        raise HTTPException(status_code=400, detail="Email not configured")
    
    success = await email_service.send_daily_summary(force=True)
    
    if success:
        return {"status": "success", "message": "Daily summary sent"}
    else:
        return {"status": "error", "message": "Failed to send daily summary"}

@router.post("/email/send-weekly-report")
async def trigger_weekly_report():
    """Manually trigger sending a weekly report email"""
    email_service = get_email_service()
    
    if not email_service.is_configured():
        raise HTTPException(status_code=400, detail="Email not configured")
    
    success = await email_service.send_weekly_report()
    
    if success:
        return {"status": "success", "message": "Weekly report sent"}
    else:
        return {"status": "error", "message": "Failed to send weekly report"}

class EmailConfigUpdate(BaseModel):
    recipient_email: Optional[str] = None
    cooldown_minutes: Optional[int] = None

class GuardianSetupRequest(BaseModel):
    email: str
    name: Optional[str] = "Guardian"

@router.post("/email/config")
async def update_email_config(config: EmailConfigUpdate):
    """Update email configuration (recipient, cooldown)"""
    email_service = get_email_service()
    
    if config.recipient_email:
        email_service.set_recipient(config.recipient_email)
    
    if config.cooldown_minutes is not None:
        email_service.alert_cooldown_minutes = config.cooldown_minutes
    
    return {
        "status": "success",
        "recipient": email_service.config.recipient_email if email_service.config else None,
        "cooldown_minutes": email_service.alert_cooldown_minutes
    }

@router.post("/email/setup-guardian")
async def setup_guardian(request: GuardianSetupRequest):
    """Set up guardian email and send welcome email"""
    email_service = get_email_service()
    
    # Check if sender credentials are configured
    sender = os.environ.get("EMAIL_SENDER", "")
    password = os.environ.get("EMAIL_PASSWORD", "")
    
    if not sender or not password:
        raise HTTPException(
            status_code=400,
            detail="Email sender not configured. Please set EMAIL_SENDER and EMAIL_PASSWORD in .env"
        )
    
    # Set the recipient
    email_service.set_recipient(request.email)
    
    # Send welcome email
    success = await email_service.send_welcome_email(request.name)
    
    if success:
        return {
            "status": "success",
            "message": f"Guardian email set and welcome email sent to {request.email}",
            "recipient": request.email
        }
    else:
        raise HTTPException(status_code=500, detail="Failed to send welcome email")

@router.get("/email/guardian")
async def get_guardian_email():
    """Get current guardian email configuration"""
    email_service = get_email_service()
    
    return {
        "configured": email_service.is_configured(),
        "recipient": email_service.config.recipient_email if email_service.config else None,
        "sender_configured": bool(os.environ.get("EMAIL_SENDER")) and bool(os.environ.get("EMAIL_PASSWORD"))
    }


# ===================== RISK THRESHOLD ENDPOINTS =====================

class RiskThresholdUpdate(BaseModel):
    threshold: float


@router.get("/email/risk-threshold")
async def get_risk_threshold():
    """Get current risk threshold for alerts"""
    email_service = get_email_service()
    
    return {
        "threshold": email_service.risk_threshold,
        "min": email_service.MIN_RISK_THRESHOLD,
        "max": email_service.MAX_RISK_THRESHOLD,
        "description": {
            "0.1": "Maximum Sensitivity - Alert on any detected concern",
            "0.2": "Very Sensitive - Alert on minor concerns",
            "0.3": "Balanced (Default) - Alert on moderate concerns",
            "0.4": "Conservative - Only notable concerns",
            "0.5": "Low Sensitivity - Only significant concerns trigger alerts"
        }
    }


@router.post("/email/risk-threshold")
async def set_risk_threshold(update: RiskThresholdUpdate):
    """Set risk threshold for alerts (0.4 - 0.8)"""
    email_service = get_email_service()
    
    threshold = update.threshold
    
    # Clamp to valid range
    if threshold < email_service.MIN_RISK_THRESHOLD:
        threshold = email_service.MIN_RISK_THRESHOLD
    elif threshold > email_service.MAX_RISK_THRESHOLD:
        threshold = email_service.MAX_RISK_THRESHOLD
    
    email_service.set_risk_threshold(threshold)
    
    return {
        "status": "success",
        "threshold": email_service.risk_threshold,
        "message": f"Risk threshold set to {threshold:.2f}"
    }


# ==================== NAVIGATION ENDPOINTS ====================

@router.post("/navigation/start")
async def start_navigation():
    """Start navigation mode"""
    try:
        navigation_service = get_navigation_service()
        result = await navigation_service.start_navigation()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/navigation/stop")
async def stop_navigation():
    """Stop navigation mode"""
    try:
        navigation_service = get_navigation_service()
        result = await navigation_service.stop_navigation()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/navigation/process-frame")
async def process_navigation_frame():
    """Process a frame for navigation assistance"""
    try:
        navigation_service = get_navigation_service()
        camera_service = get_camera_service()
        
        frame = await camera_service.get_frame()
        if frame is None:
            raise HTTPException(status_code=400, detail="No frame available")
        
        result = await navigation_service.process_frame(frame)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/navigation/process-frame-upload")
async def process_navigation_frame_upload(frame_data: dict):
    """Process an uploaded frame for navigation assistance"""
    try:
        navigation_service = get_navigation_service()
        
        # Decode base64 frame
        frame_bytes = base64.b64decode(frame_data['frame'])
        nparr = np.frombuffer(frame_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if frame is None:
            raise HTTPException(status_code=400, detail="Invalid frame data")
        
        result = await navigation_service.process_frame(frame)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/navigation/status")
async def get_navigation_status():
    """Get navigation service status"""
    try:
        navigation_service = get_navigation_service()
        return navigation_service.get_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== READING ASSISTANT ENDPOINTS ====================

@router.post("/reading-assistant/start")
async def start_reading_assistant():
    """Start reading assistant mode"""
    try:
        reading_service = get_reading_assistant_service()
        result = await reading_service.start_reading()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reading-assistant/stop")
async def stop_reading_assistant():
    """Stop reading assistant mode"""
    try:
        reading_service = get_reading_assistant_service()
        result = await reading_service.stop_reading()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reading-assistant/process-frame")
async def process_reading_frame():
    """Process a frame for text recognition"""
    try:
        reading_service = get_reading_assistant_service()
        camera_service = get_camera_service()
        
        frame = await camera_service.get_frame()
        if frame is None:
            raise HTTPException(status_code=400, detail="No frame available")
        
        result = await reading_service.process_frame(frame)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reading-assistant/process-frame-upload")
async def process_reading_frame_upload(frame_data: dict):
    """Process an uploaded frame for text recognition"""
    try:
        reading_service = get_reading_assistant_service()
        
        # Decode base64 frame
        frame_bytes = base64.b64decode(frame_data['frame'])
        nparr = np.frombuffer(frame_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if frame is None:
            raise HTTPException(status_code=400, detail="Invalid frame data")
        
        result = await reading_service.process_frame(frame)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/reading-assistant/status")
async def get_reading_assistant_status():
    """Get reading assistant status"""
    try:
        reading_service = get_reading_assistant_service()
        return reading_service.get_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/reading-assistant/history")
async def get_reading_history():
    """Get text recognition history"""
    try:
        reading_service = get_reading_assistant_service()
        return {"history": reading_service.get_text_history()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== COLOR RECOGNITION ENDPOINTS ====================

@router.post("/color-recognition/start")
async def start_color_recognition():
    """Start color recognition mode"""
    try:
        color_service = get_color_recognition_service()
        result = await color_service.start_color_recognition()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/color-recognition/stop")
async def stop_color_recognition():
    """Stop color recognition mode"""
    try:
        color_service = get_color_recognition_service()
        result = await color_service.stop_color_recognition()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/color-recognition/process-frame")
async def process_color_frame():
    """Process a frame for color recognition"""
    try:
        color_service = get_color_recognition_service()
        camera_service = get_camera_service()
        
        frame = await camera_service.get_frame()
        if frame is None:
            raise HTTPException(status_code=400, detail="No frame available")
        
        result = await color_service.process_frame(frame)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/color-recognition/process-frame-upload")
async def process_color_frame_upload(frame_data: dict):
    """Process an uploaded frame for color recognition"""
    try:
        color_service = get_color_recognition_service()
        
        # Decode base64 frame
        frame_bytes = base64.b64decode(frame_data['frame'])
        nparr = np.frombuffer(frame_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if frame is None:
            raise HTTPException(status_code=400, detail="Invalid frame data")
        
        result = await color_service.process_frame(frame)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/color-recognition/status")
async def get_color_recognition_status():
    """Get color recognition status"""
    try:
        color_service = get_color_recognition_service()
        return color_service.get_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== PEOPLE COUNTER ENDPOINTS ====================

@router.post("/people-counter/start")
async def start_people_counter():
    """Start people counting mode"""
    try:
        people_service = get_people_counter_service()
        result = await people_service.start_counting()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/people-counter/stop")
async def stop_people_counter():
    """Stop people counting mode"""
    try:
        people_service = get_people_counter_service()
        result = await people_service.stop_counting()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/people-counter/process-frame")
async def process_people_frame():
    """Process a frame to count people"""
    try:
        people_service = get_people_counter_service()
        camera_service = get_camera_service()
        
        frame = await camera_service.get_frame()
        if frame is None:
            raise HTTPException(status_code=400, detail="No frame available")
        
        result = await people_service.process_frame(frame)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/people-counter/process-frame-upload")
async def process_people_frame_upload(frame_data: dict):
    """Process an uploaded frame to count people"""
    try:
        people_service = get_people_counter_service()
        
        # Decode base64 frame
        frame_bytes = base64.b64decode(frame_data['frame'])
        nparr = np.frombuffer(frame_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if frame is None:
            raise HTTPException(status_code=400, detail="Invalid frame data")
        
        result = await people_service.process_frame(frame)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/people-counter/status")
async def get_people_counter_status():
    """Get people counter status"""
    try:
        people_service = get_people_counter_service()
        return people_service.get_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/people-counter/history")
async def get_people_count_history():
    """Get people count history"""
    try:
        people_service = get_people_counter_service()
        return {"history": people_service.get_count_history()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== EMOTION RECOGNITION ENDPOINTS ====================

class FrameUploadRequest(BaseModel):
    frame: str  # base64 encoded frame

@router.post("/emotion-recognition/process-frame")
async def process_emotion_frame():
    """Process a frame for emotion recognition"""
    try:
        emotion_service = get_emotion_recognition_service()
        camera_service = get_camera_service()
        
        frame = await camera_service.get_frame()
        if frame is None:
            raise HTTPException(status_code=400, detail="No frame available")
        
        result = await emotion_service.process_frame(frame)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/emotion-recognition/process-frame-upload")
async def process_emotion_frame_upload(request: FrameUploadRequest):
    """Process an uploaded frame for emotion recognition"""
    try:
        emotion_service = get_emotion_recognition_service()
        
        # Decode base64 frame
        frame_bytes = base64.b64decode(request.frame)
        nparr = np.frombuffer(frame_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if frame is None:
            raise HTTPException(status_code=400, detail="Invalid frame data")
        
        result = await emotion_service.process_frame(frame)
        
        # Encode annotated frame to base64
        annotated = result.get("annotated_frame")
        if annotated is not None:
            _, buffer = cv2.imencode('.jpg', annotated, [cv2.IMWRITE_JPEG_QUALITY, 90])
            result["annotated_frame"] = base64.b64encode(buffer.tobytes()).decode()
        elif frame is not None:
            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
            result["annotated_frame"] = base64.b64encode(buffer.tobytes()).decode()
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/emotion-recognition/history")
async def get_emotion_history():
    """Get emotion recognition history"""
    try:
        emotion_service = get_emotion_recognition_service()
        return {"history": emotion_service.get_emotion_history()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== SOCIAL CUES ENDPOINTS ====================

@router.post("/social-cues/analyze")
async def analyze_social_cues(request: FrameUploadRequest):
    """Analyze social cues from a frame"""
    try:
        social_service = get_social_cues_service()
        
        # Decode base64 frame
        frame_bytes = base64.b64decode(request.frame)
        nparr = np.frombuffer(frame_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if frame is None:
            raise HTTPException(status_code=400, detail="Invalid frame data")
        
        result = await social_service.analyze_situation(frame)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/social-cues/history")
async def get_social_cues_history():
    """Get social cues analysis history"""
    try:
        social_service = get_social_cues_service()
        return {"history": social_service.get_situation_history()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== SENSORY OVERLOAD ENDPOINTS ====================

@router.post("/sensory-overload/analyze")
async def analyze_sensory_environment(request: FrameUploadRequest):
    """Analyze environment for sensory overload factors"""
    try:
        sensory_service = get_sensory_overload_service()
        
        # Decode base64 frame
        frame_bytes = base64.b64decode(request.frame)
        nparr = np.frombuffer(frame_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if frame is None:
            raise HTTPException(status_code=400, detail="Invalid frame data")
        
        result = await sensory_service.analyze_environment(frame)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sensory-overload/history")
async def get_sensory_history():
    """Get sensory analysis history"""
    try:
        sensory_service = get_sensory_overload_service()
        return {"history": sensory_service.get_sensory_history()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== COMMUNICATION HELPER ENDPOINTS ====================

class CommunicationRequest(BaseModel):
    what_they_said: str
    emotion: Optional[str] = None

@router.post("/communication-helper/suggest-response")
async def suggest_response(request: CommunicationRequest):
    """Suggest a response based on what someone said"""
    try:
        comm_service = get_communication_helper_service()
        result = comm_service.suggest_response(request.what_they_said, request.emotion)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/communication-helper/scripts")
async def get_all_scripts():
    """Get all available social scripts"""
    try:
        comm_service = get_communication_helper_service()
        return comm_service.get_all_scripts()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/communication-helper/scripts/{situation}")
async def get_script(situation: str):
    """Get a specific social script"""
    try:
        comm_service = get_communication_helper_service()
        return comm_service.get_script(situation)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/communication-helper/emotion-guide/{emotion}")
async def get_emotion_response_guide(emotion: str):
    """Get guidance on how to respond to a specific emotion"""
    try:
        comm_service = get_communication_helper_service()
        return comm_service.get_emotion_response_guide(emotion)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/communication-helper/conversation-starters/{context}")
async def get_conversation_starters(context: str = "casual"):
    """Get conversation starters for a specific context"""
    try:
        comm_service = get_communication_helper_service()
        return {"starters": comm_service.get_conversation_starters(context)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== ROUTINE ASSISTANT ENDPOINTS ====================

class RoutineRequest(BaseModel):
    name: str
    steps: List[str]

@router.post("/routine-assistant/create")
async def create_routine(request: RoutineRequest):
    """Create a new routine"""
    try:
        routine_service = get_routine_assistant_service()
        result = routine_service.create_routine(request.name, request.steps)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/routine-assistant/all")
async def get_all_routines():
    """Get all routines"""
    try:
        routine_service = get_routine_assistant_service()
        return routine_service.get_all_routines()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/routine-assistant/templates")
async def get_routine_templates():
    """Get routine templates"""
    try:
        routine_service = get_routine_assistant_service()
        return routine_service.get_routine_templates()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/routine-assistant/start/{name}")
async def start_routine(name: str):
    """Start a routine"""
    try:
        routine_service = get_routine_assistant_service()
        result = routine_service.start_routine(name)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/routine-assistant/complete-step/{name}")
async def complete_step(name: str):
    """Complete the current step in a routine"""
    try:
        routine_service = get_routine_assistant_service()
        result = routine_service.complete_step(name)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/routine-assistant/current/{name}")
async def get_current_step(name: str):
    """Get the current step in a routine"""
    try:
        routine_service = get_routine_assistant_service()
        result = routine_service.get_current_step(name)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/routine-assistant/transition")
async def get_transition_support(from_activity: str, to_activity: str):
    """Get support for transitioning between activities"""
    try:
        routine_service = get_routine_assistant_service()
        result = routine_service.get_transition_support(from_activity, to_activity)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/routine-assistant/today")
async def get_today_schedule():
    """Get today's schedule"""
    try:
        routine_service = get_routine_assistant_service()
        result = routine_service.get_schedule_for_today()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/routine-assistant/{name}")
async def delete_routine(name: str):
    """Delete a routine"""
    try:
        routine_service = get_routine_assistant_service()
        result = routine_service.delete_routine(name)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== BODY LANGUAGE ENDPOINTS ====================

@router.post("/body-language/process-frame-upload")
async def process_body_language_frame_upload(request: FrameUploadRequest):
    """Process an uploaded frame for body language analysis"""
    try:
        body_service = get_body_language_service()
        
        frame_bytes = base64.b64decode(request.frame)
        nparr = np.frombuffer(frame_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if frame is None:
            raise HTTPException(status_code=400, detail="Invalid frame data")
        
        result = await body_service.process_frame(frame)
        
        annotated = result.get("annotated_frame")
        if annotated is not None:
            _, buffer = cv2.imencode('.jpg', annotated, [cv2.IMWRITE_JPEG_QUALITY, 90])
            result["annotated_frame"] = base64.b64encode(buffer.tobytes()).decode()
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/body-language/history")
async def get_body_language_history():
    """Get body language analysis history"""
    try:
        body_service = get_body_language_service()
        return {"history": body_service.get_history()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== AI CONVERSATION ENDPOINTS ====================

class ChatRequest(BaseModel):
    message: str

class VisionChatRequest(BaseModel):
    message: str
    image: str  # base64 JPEG
    context: str = ""  # optional context about what's detected

@router.post("/ai-assistant/chat")
async def chat_with_ai(request: ChatRequest):
    """Have a conversation with the AI assistant"""
    try:
        ai_service = get_ai_conversation_service()
        result = ai_service.chat(request.message)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ai-assistant/chat-with-vision")
async def chat_with_vision(request: VisionChatRequest):
    """Have a conversation with the AI - it can SEE the image"""
    try:
        ai_service = get_ai_conversation_service()
        result = ai_service.chat_with_vision(request.message, request.image, request.context)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/ai-assistant/history")
async def get_conversation_history():
    """Get conversation history"""
    try:
        ai_service = get_ai_conversation_service()
        return {"history": ai_service.get_history()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ai-assistant/clear")
async def clear_conversation():
    """Clear conversation history"""
    try:
        ai_service = get_ai_conversation_service()
        ai_service.clear_history()
        return {"status": "success", "message": "Conversation history cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

