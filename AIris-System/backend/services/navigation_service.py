"""
Navigation Service - Real-time obstacle detection and navigation assistance
"""

import cv2
import numpy as np
from typing import List, Dict, Tuple, Optional
import asyncio
from collections import deque
import time

class NavigationService:
    def __init__(self, model_service):
        self.model_service = model_service
        self.is_active = False
        self.obstacle_history = deque(maxlen=5)
        self.last_alert_time = 0
        self.alert_cooldown = 2.0  # seconds between alerts
        
        # Distance estimation (approximate, based on object size)
        self.distance_map = {
            'person': (0.5, 2.0),  # min, max meters
            'car': (1.0, 5.0),
            'bicycle': (0.5, 3.0),
            'motorcycle': (0.5, 3.0),
            'bus': (2.0, 8.0),
            'truck': (2.0, 8.0),
            'chair': (0.3, 2.0),
            'couch': (0.5, 3.0),
            'pottedplant': (0.3, 2.0),
            'diningtable': (0.5, 3.0),
            'tvmonitor': (0.5, 3.0),
            'laptop': (0.3, 1.5),
        }
        
        # Obstacle classes that should trigger alerts
        self.obstacle_classes = [
            'person', 'car', 'bicycle', 'motorcycle', 'bus', 'truck',
            'chair', 'couch', 'pottedplant', 'diningtable', 'tvmonitor',
            'laptop', 'dog', 'cat', 'bottle', 'cup', 'bowl'
        ]
    
    async def start_navigation(self):
        """Start navigation mode"""
        self.is_active = True
        self.obstacle_history.clear()
        return {
            "status": "success",
            "message": "Navigation mode started. I'll guide you around obstacles."
        }
    
    async def stop_navigation(self):
        """Stop navigation mode"""
        self.is_active = False
        return {
            "status": "success",
            "message": "Navigation mode stopped."
        }
    
    async def process_frame(self, frame: np.ndarray) -> Dict:
        """Process a frame for navigation assistance"""
        if not self.is_active:
            return {
                "obstacles": [],
                "guidance": "Navigation mode is not active",
                "safe_path": "center",
                "alert": False
            }
        
        # Get YOLO model
        yolo_model = self.model_service.get_yolo_model()
        if yolo_model is None:
            return {
                "obstacles": [],
                "guidance": "Object detection model not loaded",
                "safe_path": "center",
                "alert": False
            }
        
        # Run YOLO detection
        yolo_device = self.model_service.get_yolo_device()
        results = yolo_model(frame, verbose=False, device=yolo_device)
        
        obstacles = []
        frame_height, frame_width = frame.shape[:2]
        frame_center_x = frame_width // 2
        
        # Analyze detections
        for result in results:
            if result.boxes is not None:
                for box in result.boxes:
                    cls_id = int(box.cls[0])
                    cls_name = result.names[cls_id]
                    conf = float(box.conf[0])
                    
                    if conf < 0.5:
                        continue
                    
                    # Get bounding box
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    box_width = x2 - x1
                    box_height = y2 - y1
                    box_center_x = (x1 + x2) // 2
                    box_center_y = (y1 + y2) // 2
                    
                    # Estimate distance based on object size
                    estimated_distance = self._estimate_distance(
                        cls_name, box_width, box_height, frame_width, frame_height
                    )
                    
                    # Determine position relative to center
                    position = self._get_position(box_center_x, frame_center_x, frame_width)
                    
                    # Check if this is an obstacle
                    is_obstacle = cls_name in self.obstacle_classes
                    
                    if is_obstacle:
                        obstacles.append({
                            "class": cls_name,
                            "confidence": conf,
                            "position": position,
                            "distance": estimated_distance,
                            "bbox": [x1, y1, x2, y2]
                        })
        
        # Generate navigation guidance
        guidance = self._generate_guidance(obstacles)
        safe_path = self._get_safe_path(obstacles, frame_width)
        
        # Check for immediate danger
        alert = self._check_alert(obstacles)
        
        # Annotate frame
        annotated_frame = self._annotate_frame(frame, obstacles, safe_path)
        
        return {
            "obstacles": obstacles,
            "guidance": guidance,
            "safe_path": safe_path,
            "alert": alert,
            "alert_message": self._get_alert_message(obstacles) if alert else None,
            "annotated_frame": annotated_frame
        }
    
    def _estimate_distance(self, cls_name: str, box_width: int, box_height: int, 
                          frame_width: int, frame_height: int) -> float:
        """Estimate distance to object based on bounding box size"""
        # Simple estimation based on object size relative to frame
        box_area = box_width * box_height
        frame_area = frame_width * frame_height
        size_ratio = box_area / frame_area
        
        # Get expected size range for this class
        min_dist, max_dist = self.distance_map.get(cls_name, (0.5, 3.0))
        
        # Larger box = closer object
        if size_ratio > 0.3:
            return min_dist
        elif size_ratio > 0.1:
            return (min_dist + max_dist) / 2
        elif size_ratio > 0.03:
            return max_dist
        else:
            return max_dist * 1.5
    
    def _get_position(self, box_center_x: int, frame_center_x: int, frame_width: int) -> str:
        """Get position of object relative to frame center"""
        relative_pos = (box_center_x - frame_center_x) / frame_width
        
        if relative_pos < -0.2:
            return "far_left"
        elif relative_pos < -0.05:
            return "left"
        elif relative_pos > 0.2:
            return "far_right"
        elif relative_pos > 0.05:
            return "right"
        else:
            return "center"
    
    def _generate_guidance(self, obstacles: List[Dict]) -> str:
        """Generate navigation guidance based on obstacles"""
        if not obstacles:
            return "Path is clear. Safe to move forward."
        
        # Sort by distance (closest first)
        sorted_obstacles = sorted(obstacles, key=lambda x: x["distance"])
        closest = sorted_obstacles[0]
        
        # Generate guidance based on closest obstacle
        distance = closest["distance"]
        position = closest["position"]
        obj_class = closest["class"]
        
        if distance < 1.0:
            # Very close - immediate action needed
            if position == "center":
                return f"Stop! {obj_class} directly in front of you, very close."
            elif position in ["left", "far_left"]:
                return f"Stop! {obj_class} very close on your left."
            else:
                return f"Stop! {obj_class} very close on your right."
        elif distance < 2.0:
            # Close - caution needed
            if position == "center":
                return f"Caution: {obj_class} ahead, about {distance:.1f} meters. Move left or right."
            elif position in ["left", "far_left"]:
                return f"Caution: {obj_class} on your left, about {distance:.1f} meters. Move right."
            else:
                return f"Caution: {obj_class} on your right, about {distance:.1f} meters. Move left."
        else:
            # Far - just awareness
            if position == "center":
                return f"Note: {obj_class} ahead, about {distance:.1f} meters away."
            else:
                side = "left" if "left" in position else "right"
                return f"Note: {obj_class} on your {side}, about {distance:.1f} meters away."
    
    def _get_safe_path(self, obstacles: List[Dict], frame_width: int) -> str:
        """Determine the safest path direction"""
        if not obstacles:
            return "center"
        
        # Count obstacles in each zone
        left_count = sum(1 for obs in obstacles if "left" in obs["position"])
        right_count = sum(1 for obs in obstacles if "right" in obs["position"])
        center_count = sum(1 for obs in obstacles if obs["position"] == "center")
        
        # Find closest obstacle in each zone
        left_min_dist = min([obs["distance"] for obs in obstacles if "left" in obs["position"]], default=999)
        right_min_dist = min([obs["distance"] for obs in obstacles if "right" in obs["position"]], default=999)
        center_min_dist = min([obs["distance"] for obs in obstacles if obs["position"] == "center"], default=999)
        
        # Determine safest path
        if center_min_dist > 2.0 and center_count == 0:
            return "center"
        elif left_min_dist > right_min_dist:
            return "left"
        elif right_min_dist > left_min_dist:
            return "right"
        else:
            return "center"
    
    def _check_alert(self, obstacles: List[Dict]) -> bool:
        """Check if immediate alert is needed"""
        current_time = time.time()
        
        # Cooldown check
        if current_time - self.last_alert_time < self.alert_cooldown:
            return False
        
        # Check for very close obstacles
        for obs in obstacles:
            if obs["distance"] < 1.0 and obs["position"] == "center":
                self.last_alert_time = current_time
                return True
        
        return False
    
    def _get_alert_message(self, obstacles: List[Dict]) -> str:
        """Get alert message for immediate danger"""
        for obs in obstacles:
            if obs["distance"] < 1.0:
                return f"DANGER! {obs['class']} very close!"
        return "DANGER! Obstacle very close!"
    
    def _annotate_frame(self, frame: np.ndarray, obstacles: List[Dict], safe_path: str) -> np.ndarray:
        """Annotate frame with obstacle boxes and safe path indicator"""
        annotated = frame.copy()
        
        # Draw obstacle boxes
        for obs in obstacles:
            x1, y1, x2, y2 = obs["bbox"]
            color = (0, 0, 255) if obs["distance"] < 1.5 else (0, 165, 255)
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
            
            # Label
            label = f"{obs['class']} {obs['distance']:.1f}m"
            cv2.putText(annotated, label, (x1, y1 - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        
        # Draw safe path indicator
        frame_height, frame_width = annotated.shape[:2]
        if safe_path == "left":
            cv2.arrowedLine(annotated, (frame_width//4, frame_height//2),
                          (frame_width//4, frame_height//2 - 50), (0, 255, 0), 3)
        elif safe_path == "right":
            cv2.arrowedLine(annotated, (3*frame_width//4, frame_height//2),
                          (3*frame_width//4, frame_height//2 - 50), (0, 255, 0), 3)
        else:
            cv2.arrowedLine(annotated, (frame_width//2, frame_height//2),
                          (frame_width//2, frame_height//2 - 50), (0, 255, 0), 3)
        
        return annotated
    
    def get_status(self) -> Dict:
        """Get navigation service status"""
        return {
            "is_active": self.is_active,
            "obstacle_count": len(self.obstacle_history) if self.obstacle_history else 0
        }
