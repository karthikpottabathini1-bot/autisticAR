"""
Communication Helper Service - Suggest appropriate responses and social scripts
Helps autistic individuals navigate conversations and social interactions
"""

from typing import Dict, List, Optional
from collections import deque
import time


class CommunicationHelperService:
    def __init__(self):
        self.conversation_history = deque(maxlen=50)
        
        # Common social situations with concrete scripts
        self.social_scripts = {
            "greeting": {
                "when": "When someone says hello or hi to you",
                "scripts": [
                    "Hi! How are you?",
                    "Hello! Good to see you.",
                    "Hey there!",
                    "Hi! What's up?"
                ],
                "tips": [
                    "You can smile when you say hello",
                    "It's okay to keep it simple",
                    "You don't have to start a long conversation"
                ]
            },
            "farewell": {
                "when": "When someone is leaving or saying goodbye",
                "scripts": [
                    "Goodbye! See you later.",
                    "Bye! Have a good day.",
                    "See you!",
                    "Take care!"
                ],
                "tips": [
                    "You can wave or nod",
                    "It's okay to just say 'bye'",
                    "You don't need to stop them from leaving"
                ]
            },
            "thanking": {
                "when": "When someone helps you or does something nice",
                "scripts": [
                    "Thank you!",
                    "Thanks so much!",
                    "I appreciate it.",
                    "Thank you for helping."
                ],
                "tips": [
                    "A simple 'thank you' is enough",
                    "You can smile when you say it",
                    "You don't need to say more"
                ]
            },
            "apologizing": {
                "when": "When you make a mistake or hurt someone",
                "scripts": [
                    "I'm sorry.",
                    "I'm sorry about that.",
                    "I apologize.",
                    "Sorry, I didn't mean to."
                ],
                "tips": [
                    "Keep it simple",
                    "You don't need to explain too much",
                    "It's okay to feel bad, but don't be too hard on yourself"
                ]
            },
            "asking_for_help": {
                "when": "When you need assistance",
                "scripts": [
                    "Can you help me?",
                    "I need help with this.",
                    "Could you show me how?",
                    "I don't understand. Can you explain?"
                ],
                "tips": [
                    "It's okay to ask for help",
                    "Be specific about what you need",
                    "You can ask more than once if needed"
                ]
            },
            "answering_question": {
                "when": "When someone asks you a question",
                "scripts": [
                    "Yes.",
                    "No.",
                    "I don't know.",
                    "I'm not sure.",
                    "Let me think about that.",
                    "Can you repeat the question?"
                ],
                "tips": [
                    "Short answers are okay",
                    "It's okay to say 'I don't know'",
                    "You can ask them to repeat if you didn't hear"
                ]
            },
            "starting_conversation": {
                "when": "When you want to talk to someone",
                "scripts": [
                    "Hi! How are you?",
                    "What are you doing?",
                    "Do you want to talk about [topic]?",
                    "I like your [item]. Where did you get it?"
                ],
                "tips": [
                    "Start with a simple greeting",
                    "Ask about something they're doing",
                    "It's okay if the conversation is short"
                ]
            },
            "ending_conversation": {
                "when": "When you want to stop talking",
                "scripts": [
                    "I need to go now. Bye!",
                    "It was nice talking to you.",
                    "I'll talk to you later.",
                    "I need a break. See you!"
                ],
                "tips": [
                    "It's okay to end conversations",
                    "You can say you need to go",
                    "You don't need to give a long explanation"
                ]
            },
            "rejecting_request": {
                "when": "When you don't want to do something",
                "scripts": [
                    "No, thank you.",
                    "I don't want to right now.",
                    "I'm not interested.",
                    "Maybe later."
                ],
                "tips": [
                    "It's okay to say no",
                    "You don't need to explain why",
                    "Be firm but polite"
                ]
            },
            "expressing_feelings": {
                "when": "When you want to tell someone how you feel",
                "scripts": [
                    "I feel happy.",
                    "I feel sad.",
                    "I feel overwhelmed.",
                    "I need a break.",
                    "I'm feeling [emotion].",
                    "This is too much for me."
                ],
                "tips": [
                    "Use simple words",
                    "It's okay to say you need a break",
                    "People can't help if they don't know how you feel"
                ]
            }
        }
        
        # Conversation starters based on context
        self.conversation_starters = {
            "school": [
                "What class do you have next?",
                "Did you understand the homework?",
                "What did you think of the lesson?",
                "Do you want to study together?"
            ],
            "work": [
                "How's your day going?",
                "What are you working on?",
                "Do you need help with anything?",
                "When's your next break?"
            ],
            "casual": [
                "How are you?",
                "What are you up to?",
                "Did you do anything fun this weekend?",
                "Have you seen any good movies lately?"
            ]
        }

    def get_script(self, situation: str) -> Dict:
        """
        Get a social script for a specific situation
        Returns: when to use it, example scripts, and tips
        """
        script = self.social_scripts.get(situation)
        
        if not script:
            return {
                "when": "Unknown situation",
                "scripts": ["I'm not sure what to say."],
                "tips": ["It's okay to be quiet if you don't know what to say."]
            }
        
        return script

    def get_all_scripts(self) -> Dict:
        """Get all available social scripts"""
        return self.social_scripts

    def get_conversation_starters(self, context: str = "casual") -> List[str]:
        """Get conversation starters for a specific context"""
        return self.conversation_starters.get(context, self.conversation_starters["casual"])

    def suggest_response(self, what_they_said: str, emotion: Optional[str] = None) -> Dict:
        """
        Suggest a response based on what someone said
        Returns: suggested response, explanation, and tips
        """
        what_they_said_lower = what_they_said.lower()
        
        # Simple keyword-based response suggestions
        if any(word in what_they_said_lower for word in ["hello", "hi", "hey"]):
            return {
                "suggested_response": "Hi! How are you?",
                "explanation": "They're greeting you. You can greet them back.",
                "tips": ["Smile if you want to", "Keep it simple"]
            }
        
        elif any(word in what_they_said_lower for word in ["bye", "goodbye", "see you"]):
            return {
                "suggested_response": "Goodbye! See you later.",
                "explanation": "They're leaving. You can say goodbye back.",
                "tips": ["You can wave", "It's okay to just say 'bye'"]
            }
        
        elif any(word in what_they_said_lower for word in ["thank", "thanks"]):
            return {
                "suggested_response": "You're welcome!",
                "explanation": "They're thanking you. You can acknowledge it.",
                "tips": ["A simple response is enough", "You can smile"]
            }
        
        elif any(word in what_they_said_lower for word in ["sorry", "apologize"]):
            return {
                "suggested_response": "It's okay.",
                "explanation": "They're apologizing. You can accept it.",
                "tips": ["You don't have to forgive immediately", "It's okay to say 'I need time'"]
            }
        
        elif any(word in what_they_said_lower for word in ["help", "assist"]):
            return {
                "suggested_response": "Sure, what do you need help with?",
                "explanation": "They're asking for help. You can offer to help.",
                "tips": ["It's okay to say no if you can't help", "Ask what they need specifically"]
            }
        
        elif any(word in what_they_said_lower for word in ["how are you", "how's it going"]):
            return {
                "suggested_response": "I'm good, thanks. How about you?",
                "explanation": "They're asking how you are. You can tell them.",
                "tips": ["You can say 'good', 'okay', or 'not great'", "It's okay to be honest"]
            }
        
        elif any(word in what_they_said_lower for word in ["what's your name", "who are you"]):
            return {
                "suggested_response": "My name is [your name].",
                "explanation": "They're asking your name. You can tell them.",
                "tips": ["Just say your name", "You can ask their name too"]
            }
        
        elif any(word in what_they_said_lower for word in ["do you want", "would you like"]):
            if emotion == "angry" or emotion == "fearful":
                return {
                    "suggested_response": "No, thank you.",
                    "explanation": "They're offering something. You can say no.",
                    "tips": ["It's okay to say no", "You don't need to explain why"]
                }
            else:
                return {
                    "suggested_response": "Yes, please." or "No, thank you.",
                    "explanation": "They're offering something. You can accept or decline.",
                    "tips": ["It's okay to say yes or no", "Say 'please' and 'thank you'"]
                }
        
        else:
            return {
                "suggested_response": "I'm not sure what to say.",
                "explanation": "I don't have a specific suggestion for this.",
                "tips": [
                    "It's okay to be quiet",
                    "You can say 'I don't know what to say'",
                    "You can ask them to explain more"
                ]
            }

    def get_emotion_response_guide(self, emotion: str) -> Dict:
        """
        Get guidance on how to respond when someone shows a specific emotion
        """
        guides = {
            "happy": {
                "what_it_means": "They're feeling good and positive",
                "what_to_do": [
                    "You can smile back",
                    "Share in their happiness if you want",
                    "Ask what made them happy"
                ],
                "what_not_to_do": [
                    "Don't ignore their happiness",
                    "Don't change the subject abruptly"
                ]
            },
            "sad": {
                "what_it_means": "They're feeling down or upset",
                "what_to_do": [
                    "Be gentle and patient",
                    "Ask if they want to talk about it",
                    "Just be there for them",
                    "You can say 'I'm sorry you're sad'"
                ],
                "what_not_to_do": [
                    "Don't tell them to 'cheer up'",
                    "Don't ignore them",
                    "Don't make it about yourself"
                ]
            },
            "angry": {
                "what_it_means": "They're frustrated or mad",
                "what_to_do": [
                    "Give them space",
                    "Don't argue right now",
                    "Wait until they're calmer",
                    "You can say 'I can see you're upset'"
                ],
                "what_not_to_do": [
                    "Don't argue back",
                    "Don't tell them to calm down",
                    "Don't take it personally"
                ]
            },
            "fearful": {
                "what_it_means": "They're scared or anxious",
                "what_to_do": [
                    "Speak softly and calmly",
                    "Help them feel safe",
                    "Don't rush them",
                    "You can say 'It's okay, you're safe'"
                ],
                "what_not_to_do": [
                    "Don't scare them more",
                    "Don't dismiss their fears",
                    "Don't force them to do something"
                ]
            },
            "surprised": {
                "what_it_means": "Something unexpected happened",
                "what_to_do": [
                    "Give them a moment to process",
                    "Wait before talking",
                    "You can ask 'Are you okay?'"
                ],
                "what_not_to_do": [
                    "Don't overwhelm them with questions",
                    "Don't startle them more"
                ]
            },
            "neutral": {
                "what_it_means": "They're calm, no strong emotion",
                "what_to_do": [
                    "Normal conversation is fine",
                    "You can talk about anything",
                    "Everything is okay"
                ],
                "what_not_to_do": [
                    "Nothing specific to avoid"
                ]
            }
        }
        
        return guides.get(emotion, {
            "what_it_means": "Unknown emotion",
            "what_to_do": ["Be yourself", "Be kind"],
            "what_not_to_do": ["Don't be mean"]
        })

    def log_conversation(self, what_they_said: str, your_response: str, situation: str):
        """Log a conversation for reference"""
        self.conversation_history.append({
            "what_they_said": what_they_said,
            "your_response": your_response,
            "situation": situation,
            "timestamp": time.time()
        })

    def get_conversation_history(self) -> List[Dict]:
        """Get recent conversation history"""
        return list(self.conversation_history)
