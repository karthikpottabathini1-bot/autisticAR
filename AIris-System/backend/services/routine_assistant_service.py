"""
Routine Assistant Service - Help with daily routines, schedules, and transitions
Provides structure, predictability, and transition support for autistic individuals
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
from collections import deque
import json
import os


class RoutineAssistantService:
    def __init__(self):
        self.routines_file = "user_routines.json"
        self.routines = self.load_routines()
        self.transition_history = deque(maxlen=20)
        
        # Transition support strategies
        self.transition_strategies = {
            "5_minute_warning": {
                "description": "Give a 5-minute warning before transitions",
                "script": "In 5 minutes, we'll need to [next activity].",
                "tips": [
                    "Use a timer if it helps",
                    "Finish what you're doing",
                    "Take a deep breath before switching"
                ]
            },
            "visual_schedule": {
                "description": "Use a visual schedule to see what's coming",
                "script": "Here's what's happening today: [schedule]",
                "tips": [
                    "Check your schedule regularly",
                    "Cross off completed tasks",
                    "It's okay to adjust if needed"
                ]
            },
            "transition_object": {
                "description": "Use a transition object to help switch activities",
                "script": "When you're ready, bring [object] and we'll start [activity].",
                "tips": [
                    "Choose a specific object for transitions",
                    "Use the same object each time",
                    "It helps signal the change"
                ]
            },
            "countdown": {
                "description": "Count down to help with transitions",
                "script": "Let's count down: 5, 4, 3, 2, 1. Time to [activity]!",
                "tips": [
                    "Count slowly and clearly",
                    "Make it predictable",
                    "You can use your fingers to count"
                ]
            },
            "sensory_break": {
                "description": "Take a sensory break before transitions",
                "script": "Let's take a quick break before we switch activities.",
                "tips": [
                    "Close your eyes for a moment",
                    "Take deep breaths",
                    "Stretch or move your body",
                    "Use your coping tools"
                ]
            }
        }
        
        # Routine templates
        self.routine_templates = {
            "morning": {
                "name": "Morning Routine",
                "steps": [
                    "Wake up",
                    "Use the bathroom",
                    "Brush teeth",
                    "Get dressed",
                    "Eat breakfast",
                    "Pack bag",
                    "Leave for school/work"
                ],
                "tips": [
                    "Do these in the same order every day",
                    "Use a checklist if it helps",
                    "It's okay to adjust the order"
                ]
            },
            "bedtime": {
                "name": "Bedtime Routine",
                "steps": [
                    "Put on pajamas",
                    "Brush teeth",
                    "Use the bathroom",
                    "Get in bed",
                    "Read or relax",
                    "Turn off lights",
                    "Go to sleep"
                ],
                "tips": [
                    "Keep the routine consistent",
                    "Use dim lights",
                    "It's okay to need quiet time"
                ]
            },
            "homework": {
                "name": "Homework Routine",
                "steps": [
                    "Get homework materials",
                    "Find a quiet place",
                    "Check what needs to be done",
                    "Do one assignment at a time",
                    "Take breaks if needed",
                    "Put materials away when done"
                ],
                "tips": [
                    "Start with the hardest or easiest task",
                    "Take breaks every 20-30 minutes",
                    "It's okay to ask for help"
                ]
            }
        }

    def load_routines(self) -> Dict:
        """Load user's custom routines from file"""
        try:
            if os.path.exists(self.routines_file):
                with open(self.routines_file, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"Error loading routines: {e}")
            return {}

    def save_routines(self):
        """Save user's routines to file"""
        try:
            with open(self.routines_file, 'w') as f:
                json.dump(self.routines, f, indent=2)
        except Exception as e:
            print(f"Error saving routines: {e}")

    def create_routine(self, name: str, steps: List[str]) -> Dict:
        """Create a new custom routine"""
        routine = {
            "name": name,
            "steps": steps,
            "created": datetime.now().isoformat(),
            "completed_steps": []
        }
        
        self.routines[name] = routine
        self.save_routines()
        
        return {
            "status": "success",
            "message": f"Routine '{name}' created with {len(steps)} steps",
            "routine": routine
        }

    def get_routine(self, name: str) -> Optional[Dict]:
        """Get a specific routine"""
        return self.routines.get(name)

    def get_all_routines(self) -> Dict:
        """Get all routines"""
        return self.routines

    def get_routine_templates(self) -> Dict:
        """Get routine templates"""
        return self.routine_templates

    def start_routine(self, name: str) -> Dict:
        """Start a routine and track progress"""
        routine = self.routines.get(name)
        
        if not routine:
            return {
                "status": "error",
                "message": f"Routine '{name}' not found"
            }
        
        # Reset completed steps
        routine["completed_steps"] = []
        routine["started"] = datetime.now().isoformat()
        
        return {
            "status": "success",
            "message": f"Started routine: {name}",
            "current_step": routine["steps"][0],
            "total_steps": len(routine["steps"]),
            "completed_count": 0
        }

    def complete_step(self, routine_name: str) -> Dict:
        """Mark the current step as complete and move to next"""
        routine = self.routines.get(routine_name)
        
        if not routine:
            return {
                "status": "error",
                "message": f"Routine '{routine_name}' not found"
            }
        
        completed = routine["completed_steps"]
        total = len(routine["steps"])
        
        if len(completed) >= total:
            return {
                "status": "complete",
                "message": f"Routine '{routine_name}' is already complete!",
                "completed_count": len(completed),
                "total_steps": total
            }
        
        # Mark current step as complete
        current_step = routine["steps"][len(completed)]
        completed.append({
            "step": current_step,
            "completed_at": datetime.now().isoformat()
        })
        
        # Check if routine is complete
        if len(completed) >= total:
            routine["completed"] = datetime.now().isoformat()
            return {
                "status": "complete",
                "message": f"Great job! You completed the routine: {routine_name}",
                "completed_count": len(completed),
                "total_steps": total,
                "all_done": True
            }
        
        # Get next step
        next_step = routine["steps"][len(completed)]
        
        return {
            "status": "success",
            "message": f"Step completed: {current_step}",
            "next_step": next_step,
            "completed_count": len(completed),
            "total_steps": total,
            "progress": f"{len(completed)}/{total}"
        }

    def get_current_step(self, routine_name: str) -> Dict:
        """Get the current step in a routine"""
        routine = self.routines.get(routine_name)
        
        if not routine:
            return {
                "status": "error",
                "message": f"Routine '{routine_name}' not found"
            }
        
        completed = len(routine["completed_steps"])
        total = len(routine["steps"])
        
        if completed >= total:
            return {
                "status": "complete",
                "message": "Routine is complete!",
                "current_step": None,
                "completed_count": completed,
                "total_steps": total
            }
        
        current_step = routine["steps"][completed]
        
        return {
            "status": "success",
            "current_step": current_step,
            "step_number": completed + 1,
            "total_steps": total,
            "progress": f"{completed}/{total}",
            "remaining": total - completed
        }

    def get_transition_support(self, from_activity: str, to_activity: str) -> Dict:
        """Get support for transitioning between activities"""
        # Log the transition
        self.transition_history.append({
            "from": from_activity,
            "to": to_activity,
            "timestamp": datetime.now().isoformat()
        })
        
        # Suggest transition strategies
        strategies = [
            self.transition_strategies["5_minute_warning"],
            self.transition_strategies["countdown"],
            self.transition_strategies["sensory_break"]
        ]
        
        return {
            "transition": f"{from_activity} → {to_activity}",
            "strategies": strategies,
            "scripts": [
                f"In 5 minutes, we'll switch from {from_activity} to {to_activity}.",
                f"Let's count down: 5, 4, 3, 2, 1. Time to start {to_activity}!",
                f"Let's take a quick break before we start {to_activity}."
            ],
            "tips": [
                "Take your time with the transition",
                "It's okay to need a moment",
                "Use your coping tools if needed",
                "You can ask for help if the transition is hard"
            ]
        }

    def get_schedule_for_today(self) -> Dict:
        """Get today's schedule based on routines"""
        today = datetime.now().strftime("%A")
        
        # This would integrate with a calendar in a real implementation
        # For now, return a simple structure
        return {
            "date": today,
            "routines": list(self.routines.keys()),
            "message": "Check your routines for today's activities",
            "tip": "You can adjust your schedule if something changes"
        }

    def get_transition_history(self) -> List[Dict]:
        """Get recent transition history"""
        return list(self.transition_history)

    def clear_routine_progress(self, routine_name: str) -> Dict:
        """Clear progress on a routine"""
        routine = self.routines.get(routine_name)
        
        if not routine:
            return {
                "status": "error",
                "message": f"Routine '{routine_name}' not found"
            }
        
        routine["completed_steps"] = []
        if "started" in routine:
            del routine["started"]
        if "completed" in routine:
            del routine["completed"]
        
        return {
            "status": "success",
            "message": f"Progress cleared for routine: {routine_name}"
        }

    def delete_routine(self, name: str) -> Dict:
        """Delete a custom routine"""
        if name in self.routines:
            del self.routines[name]
            self.save_routines()
            return {
                "status": "success",
                "message": f"Routine '{name}' deleted"
            }
        
        return {
            "status": "error",
            "message": f"Routine '{name}' not found"
        }
