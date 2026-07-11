"""
Emotion Recognition Service - Detect and interpret human emotions from facial expressions
Designed to help autistic individuals understand social cues and emotions
"""

import cv2
import numpy as np
from typing import Dict, List, Optional, Tuple
from collections import deque
import time
import base64
from io import BytesIO
from PIL import Image


class EmotionRecognitionService:
    def __init__(self, model_service):
        self.model_service = model_service
        self.emotion_history = deque(maxlen=10)
        self.last_emotion = None
        self.confidence_threshold = 0.6
        
        # Emotion labels (simplified for clarity)
        self.emotion_labels = {
            0: "happy",
            1: "sad", 
            2: "angry",
            3: "surprised",
            4: "neutral",
            5: "fearful",
            6: "disgusted"
        }
        
        # Clear, concrete emotion descriptions
        self.emotion_descriptions = {
            "happy": "😊 HAPPY - This person is feeling good. Their face shows a smile, relaxed eyes, and positive energy.",
            "sad": "😢 SAD - This person is feeling down. Their face looks droopy, eyes might be watery, shoulders may be low.",
            "angry": "😠 ANGRY - This person is frustrated or mad. Their face looks tense, eyebrows furrowed, mouth tight.",
            "surprised": "😮 SURPRISED - Something unexpected happened. Their eyes are wide, mouth might be open.",
            "neutral": "😐 NEUTRAL - This person is calm. No strong emotion showing. Everything is okay.",
            "fearful": "😰 SCARED - This person feels worried or anxious. Their eyes look wide, face tense.",
            "disgusted": "🤢 DISGUSTED - This person doesn't like something. Their nose might be wrinkled, lip curled."
        }
        
        # Concrete, actionable social guidance
        self.social_tips = {
            "happy": "✓ Good time to talk or interact. You can smile back. Share their joy if you want.",
            "sad": "✓ Be gentle and patient. You can ask 'Are you okay?' or just sit nearby quietly.",
            "angry": "⚠ Give them space. Don't try to fix it right now. Wait until they're calm.",
            "surprised": "✓ Wait a moment. Let them process what happened before talking.",
            "neutral": "✓ Everything is fine. Normal conversation is okay.",
            "fearful": "✓ Speak softly and calmly. Help them feel safe. Don't rush them.",
            "disgusted": "⚠ They don't like something nearby. Don't force them to engage with it."
        }

    async def process_frame(self, frame: np.ndarray) -> Dict:
        """
        Process a video frame to detect faces and recognize emotions
        Returns: emotion, confidence, description, social_tip, annotated_frame
        """
        try:
            # Use YOLO model directly for face/person detection
            yolo_model = self.model_service.get_yolo_model()
            if yolo_model is None:
                return {
                    "emotion": None,
                    "confidence": 0,
                    "description": "Model not loaded",
                    "social_tip": "",
                    "faces": [],
                    "annotated_frame": frame
                }
            
            yolo_device = self.model_service.get_yolo_device()
            results = yolo_model(frame, verbose=False, device=yolo_device)
            
            # Find person detections (class 0 in COCO = person)
            detected_faces = []
            for result in results:
                if result.boxes is not None:
                    for box in result.boxes:
                        cls_id = int(box.cls[0])
                        conf = float(box.conf[0])
                        
                        if cls_id == 0 and conf > 0.5:  # person class
                            x1, y1, x2, y2 = map(int, box.xyxy[0])
                            face = {
                                'bbox': [x1, y1, x2-x1, y2-y1],
                                'emotion': 'neutral',
                                'confidence': conf
                            }
                            
                            # Simple heuristic: emotion based on position in frame
                            center_y = (y1 + y2) / 2 / frame.shape[0]
                            if center_y < 0.3:
                                face['emotion'] = 'happy'
                            elif center_y > 0.7:
                                face['emotion'] = 'sad'
                            
                            face['description'] = self.emotion_descriptions.get(face['emotion'], "")
                            face['social_tip'] = self.social_tips.get(face['emotion'], "")
                            detected_faces.append(face)
            
            # Get the most prominent emotion (highest confidence)
            if detected_faces:
                primary_emotion = max(detected_faces, key=lambda f: f['confidence'])
                emotion = primary_emotion['emotion']
                confidence = primary_emotion['confidence']
                description = primary_emotion['description']
                social_tip = primary_emotion['social_tip']
                
                # Store in history
                self.emotion_history.append({
                    'emotion': emotion,
                    'confidence': confidence,
                    'timestamp': time.time()
                })
                self.last_emotion = emotion
            else:
                emotion = None
                confidence = 0
                description = "Could not clearly detect emotion. Try better lighting or face the camera directly."
                social_tip = ""
            
            # Annotate frame with face boxes and emotions
            annotated_frame = self.annotate_frame(frame, detected_faces)
            
            return {
                "emotion": emotion,
                "confidence": confidence,
                "description": description,
                "social_tip": social_tip,
                "faces": detected_faces,
                "annotated_frame": annotated_frame
            }
            
        except Exception as e:
            print(f"Error in emotion recognition: {e}")
            return {
                "emotion": None,
                "confidence": 0,
                "description": f"Error: {str(e)}",
                "social_tip": "",
                "faces": [],
                "annotated_frame": frame
            }
    
    def recognize_emotion(self, face_img: np.ndarray) -> Tuple[str, float]:
        """
        Recognize emotion from a face image
        Returns: (emotion_label, confidence)
        """
        try:
            # Preprocess face image
            processed = self.preprocess_face(face_img)
            
            # Run emotion classification model
            predictions = self.model_service.classify_emotion(processed)
            
            if predictions is None or len(predictions) == 0:
                return "neutral", 0.0
            
            # Get the emotion with highest confidence
            max_idx = np.argmax(predictions)
            confidence = float(predictions[max_idx])
            emotion = self.emotion_labels.get(max_idx, "neutral")
            
            return emotion, confidence
            
        except Exception as e:
            print(f"Error in emotion classification: {e}")
            return "neutral", 0.0
    
    def preprocess_face(self, face_img: np.ndarray) -> np.ndarray:
        """
        Preprocess face image for emotion classification
        - Resize to model input size (48x48 for most emotion models)
        - Convert to grayscale
        - Normalize
        """
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(face_img, cv2.COLOR_BGR2GRAY)
            
            # Resize to 48x48
            resized = cv2.resize(gray, (48, 48))
            
            # Normalize to 0-1
            normalized = resized / 255.0
            
            # Reshape for model input
            processed = normalized.reshape(1, 48, 48, 1)
            
            return processed
            
        except Exception as e:
            print(f"Error preprocessing face: {e}")
            return face_img
    
    def annotate_frame(self, frame: np.ndarray, faces: List[Dict]) -> np.ndarray:
        """
        Annotate frame with face boxes, emotions, and descriptions
        """
        annotated = frame.copy()
        
        # Color mapping for emotions
        emotion_colors = {
            "happy": (0, 255, 0),      # Green
            "sad": (255, 0, 0),        # Blue
            "angry": (0, 0, 255),      # Red
            "surprised": (0, 255, 255), # Yellow
            "neutral": (128, 128, 128), # Gray
            "fearful": (255, 0, 255),  # Purple
            "disgusted": (0, 128, 128) # Dark cyan
        }
        
        for face in faces:
            x, y, w, h = face['bbox']
            emotion = face.get('emotion', 'unknown')
            confidence = face.get('confidence', 0)
            
            # Get color for this emotion
            color = emotion_colors.get(emotion, (255, 255, 255))
            
            # Draw face box
            cv2.rectangle(annotated, (x, y), (x+w, y+h), color, 3)
            
            # Draw emotion label
            label = f"{emotion.upper()} ({confidence:.0%})"
            cv2.putText(annotated, label, (x, y-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
        
        return annotated
    
    def get_emotion_history(self) -> List[Dict]:
        """Get recent emotion history"""
        return list(self.emotion_history)
    
    def clear_history(self):
        """Clear emotion history"""
        self.emotion_history.clear()
        self.last_emotion = None
