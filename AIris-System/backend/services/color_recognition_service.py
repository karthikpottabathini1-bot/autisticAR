"""
Color Recognition Service - Identify colors in the scene
"""

import cv2
import numpy as np
from typing import Dict, List, Tuple
from collections import Counter
import asyncio

class ColorRecognitionService:
    def __init__(self, model_service):
        self.model_service = model_service
        self.is_active = False
        self.last_color = ""
        self.color_history = []
        
        # Color ranges in HSV
        self.color_ranges = {
            'red': [(0, 70, 50), (10, 255, 255)],
            'red2': [(170, 70, 50), (180, 255, 255)],  # Red has two ranges
            'orange': [(10, 70, 50), (25, 255, 255)],
            'yellow': [(25, 70, 50), (35, 255, 255)],
            'green': [(35, 70, 50), (85, 255, 255)],
            'blue': [(85, 70, 50), (130, 255, 255)],
            'purple': [(130, 70, 50), (170, 255, 255)],
            'pink': [(160, 70, 50), (175, 255, 255)],
            'white': [(0, 0, 200), (180, 30, 255)],
            'black': [(0, 0, 0), (180, 255, 50)],
            'gray': [(0, 0, 50), (180, 30, 200)],
            'brown': [(10, 70, 50), (25, 255, 200)]
        }
        
        # Color names for display
        self.color_names = {
            'red': 'Red',
            'red2': 'Red',
            'orange': 'Orange',
            'yellow': 'Yellow',
            'green': 'Green',
            'blue': 'Blue',
            'purple': 'Purple',
            'pink': 'Pink',
            'white': 'White',
            'black': 'Black',
            'gray': 'Gray',
            'brown': 'Brown'
        }
    
    async def start_color_recognition(self):
        """Start color recognition mode"""
        self.is_active = True
        return {
            "status": "success",
            "message": "Color recognition started. Point camera at objects to identify colors."
        }
    
    async def stop_color_recognition(self):
        """Stop color recognition mode"""
        self.is_active = False
        return {
            "status": "success",
            "message": "Color recognition stopped."
        }
    
    async def process_frame(self, frame: np.ndarray) -> Dict:
        """Process a frame to identify dominant colors"""
        if not self.is_active:
            return {
                "dominant_color": "",
                "colors": [],
                "message": "Color recognition is not active"
            }
        
        # Analyze colors in the frame
        colors = self._analyze_colors(frame)
        
        # Get dominant color
        dominant_color = colors[0] if colors else ""
        
        # Check if color changed
        color_changed = dominant_color != self.last_color
        self.last_color = dominant_color
        
        if dominant_color:
            self.color_history.append({
                "color": dominant_color,
                "timestamp": asyncio.get_event_loop().time()
            })
            # Keep only last 20 colors
            if len(self.color_history) > 20:
                self.color_history = self.color_history[-20:]
        
        # Generate message
        if dominant_color:
            if color_changed:
                message = f"I see {dominant_color}"
            else:
                message = f"Still seeing {dominant_color}"
        else:
            message = "No clear color detected"
        
        # Annotate frame
        annotated_frame = self._annotate_frame(frame, colors)
        
        return {
            "dominant_color": dominant_color,
            "colors": colors,
            "message": message,
            "color_changed": color_changed,
            "annotated_frame": annotated_frame
        }
    
    def _analyze_colors(self, frame: np.ndarray) -> List[str]:
        """Analyze colors in the frame"""
        # Convert to HSV
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # Count pixels in each color range
        color_counts = {}
        
        for color_key, (lower, upper) in self.color_ranges.items():
            lower_np = np.array(lower, dtype=np.uint8)
            upper_np = np.array(upper, dtype=np.uint8)
            mask = cv2.inRange(hsv, lower_np, upper_np)
            count = cv2.countNonZero(mask)
            
            if count > 1000:  # Minimum pixel threshold
                color_name = self.color_names[color_key]
                color_counts[color_name] = count
        
        if not color_counts:
            return []
        
        # Sort by count (most pixels first)
        sorted_colors = sorted(color_counts.items(), key=lambda x: x[1], reverse=True)
        
        # Return top 3 colors
        return [color for color, count in sorted_colors[:3]]
    
    def _annotate_frame(self, frame: np.ndarray, colors: List[str]) -> np.ndarray:
        """Annotate frame with detected colors"""
        annotated = frame.copy()
        
        # Add color labels at the top
        y_offset = 30
        for i, color in enumerate(colors[:3]):
            text = f"{i+1}. {color}"
            cv2.putText(annotated, text, (10, y_offset + i*30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        return annotated
    
    def get_status(self) -> Dict:
        """Get color recognition status"""
        return {
            "is_active": self.is_active,
            "last_color": self.last_color,
            "history_count": len(self.color_history)
        }
    
    def get_color_history(self) -> List[Dict]:
        """Get history of detected colors"""
        return self.color_history
