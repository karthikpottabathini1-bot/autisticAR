"""
Body Language Service - Full body pose + face mesh analysis using MediaPipe
Analyzes body language to determine how someone is feeling toward the user
"""

import cv2
import numpy as np
import mediapipe as mp
from typing import Dict, List, Optional, Tuple
from collections import deque
import time
import math


class BodyLanguageService:
    def __init__(self, model_service):
        self.model_service = model_service
        self.mp_holistic = mp.solutions.holistic
        self.mp_drawing = mp.solutions.drawing_utils
        
        # Initialize MediaPipe Holistic
        self.holistic = self.mp_holistic.Holistic(
            static_image_mode=False,
            model_complexity=0,         # 0 = fastest, best for M1
            refine_face_landmarks=True, # 468-point face mesh (lips, eyes, cheeks)
            min_detection_confidence=0.3,
            min_tracking_confidence=0.3
        )
        
        self.history = deque(maxlen=30)
        
        # Drawing colors
        self.pose_color = (0, 255, 0)      # Green for skeleton
        self.face_color = (255, 255, 0)    # Cyan for face mesh
        self.left_color = (255, 0, 255)    # Purple for left side
        self.right_color = (0, 255, 255)   # Yellow for right side
        
        # Connection definitions for drawing
        self.pose_connections = [
            # Head and torso
            (0, 1), (0, 2), (1, 3), (2, 4),
            # Shoulders and arms
            (11, 12), (11, 13), (13, 15), (12, 14), (14, 16),
            # Hips and legs
            (11, 23), (12, 24), (23, 24), (23, 25), (25, 27),
            (24, 26), (26, 28), (27, 29), (28, 30),
            # Additional connections for full body
            (15, 17), (15, 19), (15, 21), (16, 18),
            (16, 20), (16, 22), (17, 19), (18, 20),
        ]
        
        # Face connections for lips, eyes, cheeks
        self.face_connections = mp.solutions.face_mesh.FACEMESH_TESSELATION

    async def process_frame(self, frame: np.ndarray) -> Dict:
        """Process a frame for full body + face analysis"""
        try:
            # Convert BGR to RGB
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Run MediaPipe Holistic
            results = self.holistic.process(rgb)
            
            print(f"[BodyLang] Pose: {results.pose_landmarks is not None}, Face: {results.face_landmarks is not None}, Frame: {frame.shape}")
            
            # Annotate frame
            annotated = frame.copy()
            
            # Draw pose skeleton
            if results.pose_landmarks:
                annotated = self._draw_pose(annotated, results.pose_landmarks)
            
            # Draw face mesh
            if results.face_landmarks:
                annotated = self._draw_face_mesh(annotated, results.face_landmarks)
            
            # Analyze body language
            body_lang = self._analyze_body_language(results)
            
            # Store in history
            self.history.append({
                'body_language': body_lang,
                'timestamp': time.time()
            })
            
            # Build response
            return {
                "person_detected": results.pose_landmarks is not None,
                "face_detected": results.face_landmarks is not None,
                "body_language": body_lang,
                "annotated_frame": annotated,
                "pose_landmarks": self._extract_pose_landmarks(results.pose_landmarks),
                "face_landmarks": self._extract_face_landmarks(results.face_landmarks)
            }
            
        except Exception as e:
            print(f"Error in body language analysis: {e}")
            import traceback
            traceback.print_exc()
            return {
                "person_detected": False,
                "face_detected": False,
                "body_language": {"posture": "unknown", "engagement": "unknown", "comfort": "unknown"},
                "annotated_frame": frame,
                "pose_landmarks": None,
                "face_landmarks": None
            }
    
    def _draw_pose(self, frame: np.ndarray, landmarks) -> np.ndarray:
        """Draw pose skeleton with stick figure style"""
        h, w = frame.shape[:2]
        
        # Draw connections
        for conn in self.pose_connections:
            start_idx, end_idx = conn
            start = landmarks.landmark[start_idx]
            end = landmarks.landmark[end_idx]
            
            # Only skip if landmark is completely invisible or out of frame
            vis_s = getattr(start, 'visibility', 1.0)
            vis_e = getattr(end, 'visibility', 1.0)
            if vis_s < 0.01 or vis_e < 0.01:
                continue
            
            x1, y1 = int(start.x * w), int(start.y * h)
            x2, y2 = int(end.x * w), int(end.y * h)
            
            # Skip if coords are out of bounds
            if x1 < 0 or x1 >= w or y1 < 0 or y1 >= h:
                continue
            if x2 < 0 or x2 >= w or y2 < 0 or y2 >= h:
                continue
                
            # Color based on body part
            if start_idx < 11:  # Head
                color = (255, 255, 255)
            elif 11 <= start_idx <= 16:  # Arms
                color = self.left_color if start_idx % 2 == 1 else self.right_color
            else:  # Legs
                color = self.pose_color
            
            cv2.line(frame, (x1, y1), (x2, y2), color, 4)  # Thicker skeleton lines
        
        # Draw landmark points
        for idx, lm in enumerate(landmarks.landmark):
            vis = getattr(lm, 'visibility', 1.0)
            if vis < 0.5:
                continue
            x, y = int(lm.x * w), int(lm.y * h)
            
            # Color coding for landmarks
            if idx == 0:  # Nose
                color = (0, 255, 255)
                rad = 8
            elif idx in [11, 12]:  # Shoulders
                color = (255, 0, 255)
                rad = 7
            elif idx in [23, 24]:  # Hips
                color = (255, 255, 0)
                rad = 7
            elif idx in [15, 16]:  # Wrists
                color = (0, 255, 255)
                rad = 8
            else:
                color = (200, 200, 200)
                rad = 5
            
            cv2.circle(frame, (x, y), rad, color, -1)
        
        return frame
    
    def _draw_face_mesh(self, frame: np.ndarray, landmarks) -> np.ndarray:
        """Draw face mesh with key points highlighted"""
        h, w = frame.shape[:2]
        face_mesh = landmarks.landmark
        
        # Draw simplified face mesh (key points only to avoid overwhelming visuals)
        # Eye regions
        left_eye = [33, 133, 157, 158, 159, 160, 161, 173]
        right_eye = [362, 263, 387, 386, 385, 384, 398, 466]
        # Lip regions
        lips = [61, 146, 91, 181, 84, 17, 314, 405, 321, 375, 291, 308, 324, 318, 402, 317, 14, 87, 178, 88, 95]
        # Eyebrows
        left_brow = [70, 63, 105, 66, 107]
        right_brow = [300, 293, 334, 296, 336]
        # Nose
        nose = [1, 2, 98, 327]
        # Cheeks
        left_cheek = [50, 101, 205, 206]
        right_cheek = [280, 330, 425, 426]
        
        # Draw eyes (green)
        for pt in left_eye + right_eye:
            if pt < len(face_mesh):
                x = int(face_mesh[pt].x * w)
                y = int(face_mesh[pt].y * h)
                cv2.circle(frame, (x, y), 1, (0, 255, 0), -1)
        
        # Draw lips (pink)
        for pt in lips:
            if pt < len(face_mesh):
                x = int(face_mesh[pt].x * w)
                y = int(face_mesh[pt].y * h)
                cv2.circle(frame, (x, y), 1, (255, 105, 180), -1)
        
        # Draw eyebrows (yellow)
        for pt in left_brow + right_brow:
            if pt < len(face_mesh):
                x = int(face_mesh[pt].x * w)
                y = int(face_mesh[pt].y * h)
                cv2.circle(frame, (x, y), 1, (255, 255, 0), -1)
        
        # Draw nose (gray)
        for pt in nose:
            if pt < len(face_mesh):
                x = int(face_mesh[pt].x * w)
                y = int(face_mesh[pt].y * h)
                cv2.circle(frame, (x, y), 2, (128, 128, 128), -1)
        
        # Draw cheeks (light purple)
        for pt in left_cheek + right_cheek:
            if pt < len(face_mesh):
                x = int(face_mesh[pt].x * w)
                y = int(face_mesh[pt].y * h)
                cv2.circle(frame, (x, y), 2, (200, 100, 200), -1)
        
        # Connect key face landmarks with lines
        # Face outline
        face_outline = [10, 338, 297, 332, 284, 251, 389, 356, 454, 323, 361, 288, 397, 365, 379, 378, 400, 377, 152, 148, 176, 149, 150, 136, 172, 58, 132, 93, 234, 127, 162, 21, 54, 103, 67, 109, 10]
        for i in range(len(face_outline) - 1):
            p1, p2 = face_outline[i], face_outline[i + 1]
            if p1 < len(face_mesh) and p2 < len(face_mesh):
                x1, y1 = int(face_mesh[p1].x * w), int(face_mesh[p1].y * h)
                x2, y2 = int(face_mesh[p2].x * w), int(face_mesh[p2].y * h)
                cv2.line(frame, (x1, y1), (x2, y2), (255, 255, 255), 1)
        
        return frame
    
    def _analyze_body_language(self, results) -> Dict:
        """Analyze body language to determine how someone is feeling"""
        posture = "unknown"
        engagement = "unknown"
        comfort = "unknown"
        details = {}
        
        if results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark
            
            # Get key points
            nose = landmarks[0]
            left_shoulder = landmarks[11]
            right_shoulder = landmarks[12]
            left_hip = landmarks[23]
            right_hip = landmarks[24]
            
            # Shoulder orientation (are they facing you or turned away?)
            shoulder_diff_x = abs(left_shoulder.x - right_shoulder.x)
            if shoulder_diff_x > 0.15:
                posture = "facing_you"
            else:
                posture = "turned_away"
            
            # Head leaning (engagement)
            head_tilt = abs(nose.x - ((left_shoulder.x + right_shoulder.x) / 2))
            if head_tilt > 0.05:
                engagement = "interested"
                details["head_tilt"] = "Head tilted - showing interest"
            else:
                engagement = "neutral"
            
            # Shoulder height (comfort/tension)
            shoulder_height_diff = abs(left_shoulder.y - right_shoulder.y)
            if shoulder_height_diff > 0.03:
                comfort = "tense"
                details["shoulders"] = "Uneven shoulders - may be tense"
            else:
                comfort = "relaxed"
            
            # Hip orientation
            hip_diff_x = abs(left_hip.x - right_hip.x)
            if hip_diff_x < 0.08:
                details["hips"] = "Hips facing away - may want to leave"
            
            # Arm position (open vs closed)
            left_wrist = landmarks[15]
            right_wrist = landmarks[16]
            left_elbow = landmarks[13]
            right_elbow = landmarks[14]
            
            # Check if arms are crossed
            if left_wrist.visibility > 0.5 and right_wrist.visibility > 0.5:
                wrists_close = abs(left_wrist.x - right_wrist.x) < 0.1
                if wrists_close:
                    comfort = "defensive"
                    details["arms"] = "Arms crossed - defensive posture"
        
        # Face-based analysis
        if results.face_landmarks:
            face = results.face_landmarks.landmark
            
            # Lip corners (smile vs frown)
            left_lip = face[61]   # Left corner
            right_lip = face[291] # Right corner
            top_lip = face[13]    # Top center
            bottom_lip = face[14] # Bottom center
            
            lip_width = abs(left_lip.x - right_lip.x)
            lip_height = abs(top_lip.y - bottom_lip.y)
            
            if lip_width > 0.1 and lip_height > 0.01:
                details["expression"] = "Appears to be smiling - positive engagement"
                engagement = "positive"
            
            # Eyebrow position (raised = surprised/interested, lowered = angry/confused)
            left_brow = face[105]
            right_brow = face[334]
            avg_brow_y = (left_brow.y + right_brow.y) / 2
            
            if avg_brow_y < face[168].y - 0.01:  # Brows above reference
                details["eyebrows"] = "Eyebrows raised - may be surprised or interested"
            elif avg_brow_y > face[168].y + 0.02:  # Brows lowered
                details["eyebrows"] = "Eyebrows lowered - may be annoyed or thinking"
        
        return {
            "posture": posture,
            "engagement": engagement,
            "comfort": comfort,
            "details": details,
            "interpretation": self._generate_interpretation(posture, engagement, comfort, details)
        }
    
    def _generate_interpretation(self, posture: str, engagement: str, comfort: str, details: Dict) -> str:
        """Generate a human-readable interpretation of body language"""
        interpretations = []
        
        if posture == "facing_you":
            interpretations.append("They are facing you directly - engaged in the interaction")
        else:
            interpretations.append("They are slightly turned away - may not be fully engaged")
        
        if comfort == "relaxed":
            interpretations.append("Their posture looks relaxed and comfortable")
        elif comfort == "tense":
            interpretations.append("They seem tense or stressed")
        elif comfort == "defensive":
            interpretations.append("They appear defensive - may feel uncomfortable")
        
        if engagement == "positive":
            interpretations.append("They seem to be responding positively")
        elif engagement == "interested":
            interpretations.append("They appear interested in what's happening")
        
        for detail in details.values():
            if isinstance(detail, str) and not any(d in interpretations for d in [detail]):
                interpretations.append(detail)
        
        return ". ".join(interpretations) + "." if interpretations else "Analyzing body language..."
    
    def _extract_pose_landmarks(self, landmarks) -> Optional[List[Dict]]:
        """Extract pose landmarks as a list"""
        if not landmarks:
            return None
        
        return [
            {
                "x": lm.x,
                "y": lm.y,
                "z": lm.z,
                "visibility": lm.visibility
            }
            for lm in landmarks.landmark
        ]
    
    def _extract_face_landmarks(self, landmarks) -> Optional[List[Dict]]:
        """Extract face landmarks as a list"""
        if not landmarks:
            return None
        
        return [
            {"x": lm.x, "y": lm.y, "z": lm.z}
            for lm in landmarks.landmark
        ]
    
    def get_history(self) -> List[Dict]:
        return list(self.history)
