"""
Social Cues Service - Analyze social situations and provide concrete guidance
Helps autistic individuals understand social context and appropriate responses
"""

import cv2
import numpy as np
from typing import Dict, List, Optional
from collections import deque
import time


class SocialCuesService:
    def __init__(self, model_service):
        self.model_service = model_service
        self.situation_history = deque(maxlen=20)
        self.last_situation = None
        
        # Social situation types with clear descriptions
        self.situation_types = {
            "greeting": "👋 GREETING - Someone is saying hello or starting a conversation",
            "farewell": "👋 SAYING GOODBYE - Someone is leaving or ending a conversation",
            "asking_question": "❓ ASKING A QUESTION - Someone wants information from you",
            "giving_compliment": "💬 GIVING A COMPLIMENT - Someone is saying something nice",
            "showing_frustration": "😤 SHOWING FRUSTRATION - Someone is upset about something",
            "seeking_help": "🆘 ASKING FOR HELP - Someone needs assistance",
            "sharing_excitement": "🎉 SHARING EXCITEMENT - Something good happened to them",
            "need_space": "🚪 NEEDING SPACE - They want to be alone right now",
            "normal_conversation": "💬 NORMAL CONVERSATION - Regular talking, nothing special"
        }
        
        # Concrete response suggestions
        self.response_suggestions = {
            "greeting": [
                "Say 'Hi' or 'Hello' back",
                "You can smile and wave",
                "Ask 'How are you?' if you want to continue talking"
            ],
            "farewell": [
                "Say 'Goodbye' or 'See you later'",
                "You can wave",
                "It's okay to just nod and let them go"
            ],
            "asking_question": [
                "Listen to what they're asking",
                "If you know the answer, tell them",
                "If you don't know, say 'I don't know' - that's okay!"
            ],
            "giving_compliment": [
                "Say 'Thank you'",
                "You can smile",
                "You don't need to say anything else - 'Thank you' is enough"
            ],
            "showing_frustration": [
                "Give them space",
                "Don't try to fix it unless they ask",
                "You can say 'I'm sorry you're upset' if you want"
            ],
            "seeking_help": [
                "Listen to what they need",
                "If you can help, do it",
                "If you can't help, say 'I can't help with that' - that's okay"
            ],
            "sharing_excitement": [
                "You can say 'That's great!' or 'Cool!'",
                "You can smile",
                "Ask them more about it if you're interested"
            ],
            "need_space": [
                "Give them physical space",
                "Don't talk to them right now",
                "They'll come back when they're ready"
            ],
            "normal_conversation": [
                "Just talk normally",
                "Listen and take turns talking",
                "It's okay to ask questions"
            ]
        }
        
        # What NOT to do (important for autistic individuals)
        self.avoid_actions = {
            "greeting": ["Don't ignore them", "Don't walk away without responding"],
            "farewell": ["Don't stop them from leaving", "Don't start a new topic"],
            "asking_question": ["Don't make fun of the question", "Don't ignore them"],
            "giving_compliment": ["Don't argue with the compliment", "Don't say negative things about yourself"],
            "showing_frustration": ["Don't argue", "Don't tell them to calm down", "Don't take it personally"],
            "seeking_help": ["Don't ignore them", "Don't pretend you didn't hear"],
            "sharing_excitement": ["Don't change the subject", "Don't say 'that's not important'"],
            "need_space": ["Don't follow them", "Don't keep talking", "Don't take it personally"],
            "normal_conversation": ["Don't interrupt", "Don't talk over them"]
        }

    async def analyze_situation(self, frame: np.ndarray, emotion_data: Dict) -> Dict:
        """
        Analyze the social situation based on visual cues and emotions
        Returns: situation type, description, response suggestions, what to avoid
        """
        try:
            # Detect people and their positions
            people = self.model_service.detect_people(frame)
            
            if not people or len(people) == 0:
                return {
                    "situation": "alone",
                    "description": "No one else is around. You're alone right now.",
                    "response_suggestions": [],
                    "avoid_actions": [],
                    "people_count": 0
                }
            
            # Analyze the social context
            situation = self.determine_situation(people, emotion_data)
            
            # Get response suggestions
            suggestions = self.response_suggestions.get(situation, [])
            avoid = self.avoid_actions.get(situation, [])
            description = self.situation_types.get(situation, "")
            
            # Store in history
            self.situation_history.append({
                'situation': situation,
                'timestamp': time.time(),
                'people_count': len(people)
            })
            self.last_situation = situation
            
            return {
                "situation": situation,
                "description": description,
                "response_suggestions": suggestions,
                "avoid_actions": avoid,
                "people_count": len(people),
                "people": people
            }
            
        except Exception as e:
            print(f"Error in social cues analysis: {e}")
            return {
                "situation": "unknown",
                "description": f"Error analyzing situation: {str(e)}",
                "response_suggestions": [],
                "avoid_actions": [],
                "people_count": 0,
                "people": []
            }
    
    def determine_situation(self, people: List[Dict], emotion_data: Dict) -> str:
        """
        Determine the social situation based on visual and emotional cues
        """
        try:
            # Check if there's an emotion detected
            emotion = emotion_data.get('emotion')
            
            if not emotion:
                return "normal_conversation"
            
            # Simple rule-based situation detection
            # In a real implementation, this would use more sophisticated analysis
            
            if emotion == "happy":
                return "sharing_excitement"
            elif emotion == "sad":
                return "showing_frustration"
            elif emotion == "angry":
                return "showing_frustration"
            elif emotion == "fearful":
                return "need_space"
            elif emotion == "surprised":
                return "asking_question"
            else:
                return "normal_conversation"
                
        except Exception as e:
            print(f"Error determining situation: {e}")
            return "normal_conversation"
    
    def get_situation_history(self) -> List[Dict]:
        """Get recent situation history"""
        return list(self.situation_history)
    
    def clear_history(self):
        """Clear situation history"""
        self.situation_history.clear()
        self.last_situation = None
