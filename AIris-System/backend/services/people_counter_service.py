"""
People Counter Service - Detect and count people in the scene
"""

import cv2
import numpy as np
from typing import Dict, List
from collections import deque
import time

class PeopleCounterService:
    def __init__(self, model_service):
        self.model_service = model_service
        self.is_active = False
        self.last_count = 0
        self.count_history = deque(maxlen=10)
        self.person_class_id = 0  # COCO class ID for person
        
    async def start_counting(self):
        """Start people counting mode"""
        self.is_active = True
        return {
            "status": "success",
            "message": "People counting started. I'll tell you how many people are nearby."
        }
    
    async def stop_counting(self):
        """Stop people counting mode"""
        self.is_active = False
        return {
            "status": "success",
            "message": "People counting stopped."
        }
    
    async def process_frame(self, frame: np.ndarray) -> Dict:
        """Process a frame to count people"""
        if not self.is_active:
            return {
                "count": 0,
                "people": [],
                "message": "People counting is not active"
            }
        
        # Get YOLO model
        yolo_model = self.model_service.get_yolo_model()
        if yolo_model is None:
            return {
                "count": 0,
                "people": [],
                "message": "Object detection model not loaded"
            }
        
        # Run YOLO detection
        yolo_device = self.model_service.get_yolo_device()
        results = yolo_model(frame, verbose=False, device=yolo_device)
        
        people = []
        frame_height, frame_width = frame.shape[:2]
        
        # Analyze detections for people
        for result in results:
            if result.boxes is not None:
                for box in result.boxes:
                    cls_id = int(box.cls[0])
                    
                    # Check if it's a person
                    if cls_id == self.person_class_id:
                        conf = float(box.conf[0])
                        if conf < 0.5:
                            continue
                        
                        # Get bounding box
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        box_width = x2 - x1
                        box_height = y2 - y1
                        
                        # Estimate distance based on person size
                        estimated_distance = self._estimate_distance(
                            box_width, box_height, frame_width, frame_height
                        )
                        
                        # Determine position
                        box_center_x = (x1 + x2) // 2
                        position = self._get_position(box_center_x, frame_width)
                        
                        people.append({
                            "confidence": conf,
                            "position": position,
                            "distance": estimated_distance,
                            "bbox": [x1, y1, x2, y2]
                        })
        
        count = len(people)
        
        # Update history
        self.count_history.append({
            "count": count,
            "timestamp": time.time()
        })
        
        # Check if count changed
        count_changed = count != self.last_count
        self.last_count = count
        
        # Generate message
        if count == 0:
            message = "No people detected"
        elif count == 1:
            position = people[0]["position"]
            distance = people[0]["distance"]
            message = f"One person detected, {distance:.1f} meters away, on your {position}"
        else:
            # Group by position
            left_count = sum(1 for p in people if "left" in p["position"])
            right_count = sum(1 for p in people if "right" in p["position"])
            center_count = sum(1 for p in people if p["position"] == "center")
            
            parts = []
            if center_count > 0:
                parts.append(f"{center_count} ahead")
            if left_count > 0:
                parts.append(f"{left_count} on your left")
            if right_count > 0:
                parts.append(f"{right_count} on your right")
            
            message = f"{count} people detected: {', '.join(parts)}"
        
        # Annotate frame
        annotated_frame = self._annotate_frame(frame, people)
        
        return {
            "count": count,
            "people": people,
            "message": message,
            "count_changed": count_changed,
            "annotated_frame": annotated_frame
        }
    
    def _estimate_distance(self, box_width: int, box_height: int, 
                          frame_width: int, frame_height: int) -> float:
        """Estimate distance to person based on bounding box size"""
        # Average person height: 1.7m
        # Estimate based on box height relative to frame
        box_height_ratio = box_height / frame_height
        
        # Larger box = closer person
        if box_height_ratio > 0.6:
            return 1.0
        elif box_height_ratio > 0.3:
            return 2.0
        elif box_height_ratio > 0.15:
            return 3.5
        else:
            return 5.0
    
    def _get_position(self, box_center_x: int, frame_width: int) -> str:
        """Get position of person relative to frame center"""
        frame_center_x = frame_width // 2
        relative_pos = (box_center_x - frame_center_x) / frame_width
        
        if relative_pos < -0.2:
            return "far left"
        elif relative_pos < -0.05:
            return "left"
        elif relative_pos > 0.2:
            return "far right"
        elif relative_pos > 0.05:
            return "right"
        else:
            return "center"
    
    def _annotate_frame(self, frame: np.ndarray, people: List[Dict]) -> np.ndarray:
        """Annotate frame with detected people"""
        annotated = frame.copy()
        
        # Draw bounding boxes
        for i, person in enumerate(people):
            x1, y1, x2, y2 = person["bbox"]
            cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            # Label
            label = f"Person {i+1} ({person['distance']:.1f}m)"
            cv2.putText(annotated, label, (x1, y1 - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        # Add count at top
        cv2.putText(annotated, f"People: {len(people)}", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)
        
        return annotated
    
    def get_status(self) -> Dict:
        """Get people counter status"""
        return {
            "is_active": self.is_active,
            "last_count": self.last_count,
            "history_count": len(self.count_history)
        }
    
    def get_count_history(self) -> List[Dict]:
        """Get history of people counts"""
        return list(self.count_history)
