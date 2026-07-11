"""
Sensory Overload Detection Service - Detect overwhelming sensory environments
Helps autistic individuals identify and prepare for sensory challenges
"""

import cv2
import numpy as np
from typing import Dict, List, Optional
from collections import deque
import time


class SensoryOverloadService:
    def __init__(self, model_service):
        self.model_service = model_service
        self.sensory_history = deque(maxlen=30)
        
        # Sensory factors and their thresholds
        self.sensory_thresholds = {
            "crowd_density": {
                "low": 5,      # Few people
                "moderate": 15, # Some people
                "high": 30     # Many people
            },
            "movement": {
                "low": 0.1,    # Little movement
                "moderate": 0.3, # Some movement
                "high": 0.6    # Lots of movement
            },
            "brightness": {
                "low": 50,     # Dim
                "moderate": 150, # Normal
                "high": 220    # Very bright
            },
            "visual_complexity": {
                "low": 10,     # Simple
                "moderate": 30, # Moderate
                "high": 60     # Complex
            }
        }
        
        # Clear warnings and coping strategies
        self.overload_warnings = {
            "crowded": {
                "level": "⚠️ CROWDED SPACE",
                "description": "There are many people here. This might feel overwhelming.",
                "coping": [
                    "Find a quieter spot if possible",
                    "Use noise-canceling headphones",
                    "Take deep breaths",
                    "It's okay to leave if you need to"
                ]
            },
            "bright_lights": {
                "level": "⚠️ BRIGHT LIGHTS",
                "description": "The lights are very bright. This might hurt your eyes.",
                "coping": [
                    "Wear sunglasses or a hat",
                    "Look down or away from bright lights",
                    "Find a dimmer area",
                    "Close your eyes for a moment if needed"
                ]
            },
            "lots_of_movement": {
                "level": "⚠️ LOTS OF MOVEMENT",
                "description": "There's a lot of movement around you. This can be distracting.",
                "coping": [
                    "Focus on one thing at a time",
                    "Find a still spot to stand or sit",
                    "Use noise-canceling headphones",
                    "Take a break in a quieter place"
                ]
            },
            "visually_complex": {
                "level": "⚠️ BUSY VISUAL ENVIRONMENT",
                "description": "There's a lot to look at. This might feel overwhelming.",
                "coping": [
                    "Focus on one thing at a time",
                    "Look at the ground or a simple object",
                    "Take breaks by closing your eyes",
                    "Find a simpler space if possible"
                ]
            },
            "multiple_factors": {
                "level": "🚨 HIGH SENSORY LOAD",
                "description": "Multiple sensory factors are high. This environment might be very overwhelming.",
                "coping": [
                    "Leave this area if you can",
                    "Find a quiet, simple space",
                    "Use all your coping tools (headphones, sunglasses, etc.)",
                    "Take deep breaths and ground yourself",
                    "It's okay to take a break"
                ]
            },
            "manageable": {
                "level": "✓ MANAGEABLE ENVIRONMENT",
                "description": "The sensory levels are okay. This should be manageable.",
                "coping": [
                    "You're doing great",
                    "Use your coping tools if you need them",
                    "Take breaks when you need to"
                ]
            }
        }

    async def analyze_environment(self, frame: np.ndarray) -> Dict:
        """
        Analyze the environment for sensory overload factors
        Returns: sensory levels, warnings, coping strategies
        """
        try:
            # Analyze different sensory factors
            crowd_analysis = self.analyze_crowd_density(frame)
            movement_analysis = self.analyze_movement(frame)
            brightness_analysis = self.analyze_brightness(frame)
            complexity_analysis = self.analyze_visual_complexity(frame)
            
            # Determine overall sensory load
            sensory_factors = {
                "crowd_density": crowd_analysis,
                "movement": movement_analysis,
                "brightness": brightness_analysis,
                "visual_complexity": complexity_analysis
            }
            
            # Count high factors
            high_factors = sum(1 for factor in sensory_factors.values() 
                             if factor['level'] == 'high')
            
            # Determine warning level
            if high_factors >= 2:
                warning_type = "multiple_factors"
            elif crowd_analysis['level'] == 'high':
                warning_type = "crowded"
            elif brightness_analysis['level'] == 'high':
                warning_type = "bright_lights"
            elif movement_analysis['level'] == 'high':
                warning_type = "lots_of_movement"
            elif complexity_analysis['level'] == 'high':
                warning_type = "visually_complex"
            else:
                warning_type = "manageable"
            
            warning = self.overload_warnings[warning_type]
            
            # Store in history
            self.sensory_history.append({
                'sensory_factors': sensory_factors,
                'warning_type': warning_type,
                'timestamp': time.time()
            })
            
            return {
                "sensory_factors": sensory_factors,
                "warning_level": warning['level'],
                "description": warning['description'],
                "coping_strategies": warning['coping'],
                "high_factor_count": high_factors,
                "annotated_frame": self.annotate_frame(frame, sensory_factors)
            }
            
        except Exception as e:
            print(f"Error in sensory analysis: {e}")
            return {
                "sensory_factors": {},
                "warning_level": "Error",
                "description": f"Error analyzing environment: {str(e)}",
                "coping_strategies": [],
                "high_factor_count": 0,
                "annotated_frame": frame
            }
    
    def analyze_crowd_density(self, frame: np.ndarray) -> Dict:
        """Analyze how crowded the environment is"""
        try:
            # Detect people
            people = self.model_service.detect_people(frame)
            count = len(people) if people else 0
            
            # Determine level
            if count >= self.sensory_thresholds['crowd_density']['high']:
                level = "high"
            elif count >= self.sensory_thresholds['crowd_density']['moderate']:
                level = "moderate"
            else:
                level = "low"
            
            return {
                "level": level,
                "count": count,
                "description": f"{count} people detected"
            }
            
        except Exception as e:
            print(f"Error analyzing crowd density: {e}")
            return {"level": "low", "count": 0, "description": "Error"}
    
    def analyze_movement(self, frame: np.ndarray) -> Dict:
        """Analyze how much movement is in the environment"""
        try:
            # Convert to grayscale for motion detection
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Simple motion detection using frame differences
            # In a real implementation, you'd compare with previous frames
            # For now, we'll use edge detection as a proxy for visual activity
            edges = cv2.Canny(gray, 50, 150)
            edge_density = np.sum(edges > 0) / (edges.shape[0] * edges.shape[1])
            
            # Determine level
            if edge_density >= self.sensory_thresholds['movement']['high']:
                level = "high"
            elif edge_density >= self.sensory_thresholds['movement']['moderate']:
                level = "moderate"
            else:
                level = "low"
            
            return {
                "level": level,
                "density": edge_density,
                "description": f"Movement level: {level}"
            }
            
        except Exception as e:
            print(f"Error analyzing movement: {e}")
            return {"level": "low", "density": 0, "description": "Error"}
    
    def analyze_brightness(self, frame: np.ndarray) -> Dict:
        """Analyze the brightness of the environment"""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Calculate average brightness
            brightness = np.mean(gray)
            
            # Determine level
            if brightness >= self.sensory_thresholds['brightness']['high']:
                level = "high"
            elif brightness >= self.sensory_thresholds['brightness']['moderate']:
                level = "moderate"
            else:
                level = "low"
            
            return {
                "level": level,
                "brightness": brightness,
                "description": f"Brightness: {brightness:.0f}/255"
            }
            
        except Exception as e:
            print(f"Error analyzing brightness: {e}")
            return {"level": "low", "brightness": 0, "description": "Error"}
    
    def analyze_visual_complexity(self, frame: np.ndarray) -> Dict:
        """Analyze how visually complex the environment is"""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Use edge detection to measure complexity
            edges = cv2.Canny(gray, 50, 150)
            edge_count = np.sum(edges > 0)
            
            # Determine level
            if edge_count >= self.sensory_thresholds['visual_complexity']['high']:
                level = "high"
            elif edge_count >= self.sensory_thresholds['visual_complexity']['moderate']:
                level = "moderate"
            else:
                level = "low"
            
            return {
                "level": level,
                "complexity": edge_count,
                "description": f"Visual complexity: {level}"
            }
            
        except Exception as e:
            print(f"Error analyzing visual complexity: {e}")
            return {"level": "low", "complexity": 0, "description": "Error"}
    
    def annotate_frame(self, frame: np.ndarray, sensory_factors: Dict) -> np.ndarray:
        """Annotate frame with sensory information"""
        annotated = frame.copy()
        
        # Add sensory level indicators
        y_offset = 30
        for factor_name, factor_data in sensory_factors.items():
            level = factor_data['level']
            
            # Color based on level
            if level == "high":
                color = (0, 0, 255)  # Red
            elif level == "moderate":
                color = (0, 165, 255)  # Orange
            else:
                color = (0, 255, 0)  # Green
            
            # Add text
            text = f"{factor_name.replace('_', ' ').title()}: {level.upper()}"
            cv2.putText(annotated, text, (10, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
            y_offset += 30
        
        return annotated
    
    def get_sensory_history(self) -> List[Dict]:
        """Get recent sensory history"""
        return list(self.sensory_history)
    
    def clear_history(self):
        """Clear sensory history"""
        self.sensory_history.clear()
