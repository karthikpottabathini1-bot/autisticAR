"""
AI Conversation Service - Natural back-and-forth conversation for autistic individuals
Uses Groq LLM for intelligent, empathetic responses
"""

import os
from typing import Dict, List, Optional
from collections import deque
import time
from groq import Groq


class AIConversationService:
    def __init__(self):
        self.client = None
        self.conversation_history = deque(maxlen=20)
        self.system_prompt = """You are autisticAR, a warm, patient, and helpful AI assistant designed for autistic individuals. 

Your communication style:
- Use simple, clear language. Avoid sarcasm, idioms, or metaphors unless you explain them.
- Be direct and concrete. Say exactly what you mean.
- Validate feelings and experiences. Never dismiss or minimize.
- Offer choices rather than open-ended questions when possible.
- Break complex tasks into simple steps.
- Be encouraging but not overly emotional.
- If the user seems confused, rephrase rather than repeat verbatim.
- Use gentle, calming language. Avoid overwhelming information.

You help with:
- Understanding emotions and social situations
- Practicing conversations and social scripts
- Managing sensory overload and anxiety
- Planning routines and daily activities
- Answering questions about social norms and expectations
- Providing encouragement and emotional support
- Explaining confusing social interactions

Keep responses concise (2-4 sentences unless more detail is requested). 
Always end by asking if they need more help or have another question."""
        
        # Initialize Groq client
        api_key = os.environ.get("GROQ_API_KEY")
        if api_key:
            try:
                self.client = Groq(api_key=api_key)
                print("✓ AI Conversation service initialized with Groq")
            except Exception as e:
                print(f"⚠️ AI Conversation service: Groq init error: {e}")
    
    def chat(self, user_message: str) -> Dict:
        """Have a conversation with the AI assistant"""
        if not self.client:
            return {
                "response": "I'm having trouble connecting to my brain right now. Please try again in a moment.",
                "success": False
            }
        
        try:
            # Add user message to history
            self.conversation_history.append({
                "role": "user",
                "content": user_message
            })
            
            # Build messages array
            messages = [{"role": "system", "content": self.system_prompt}]
            messages.extend(list(self.conversation_history))
            
            # Call Groq API
            completion = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                temperature=0.7,
                max_tokens=300,
                top_p=1,
                stream=False
            )
            
            response = completion.choices[0].message.content
            
            # Add response to history
            self.conversation_history.append({
                "role": "assistant",
                "content": response
            })
            
            return {
                "response": response,
                "success": True
            }
            
        except Exception as e:
            print(f"AI Conversation error: {e}")
            return {
                "response": "I'm sorry, I got a bit confused. Could you say that again?",
                "success": False
            }
    
    def chat_with_vision(self, user_message: str, image_base64: str, context: str = "") -> Dict:
        """Have a conversation where the AI can SEE the image and respond"""
        if not self.client:
            return {
                "response": "I'm having trouble connecting. Please try again in a moment.",
                "success": False
            }
        
        try:
            self.conversation_history.append({
                "role": "user",
                "content": user_message
            })
            
            vision_prompt = f"""You are autisticAR, a warm AI assistant for autistic individuals. You can SEE the camera feed.

{context if context else ""}

The user said: "{user_message}"

Analyze the image and help them. Describe what you see, then provide clear guidance.
- Use simple, direct language
- If you see objects, tell them what and where
- If they're looking for something, guide them to it
- Be specific about positions (left, right, center, near, far)
- Keep responses concise (2-4 sentences)
- Speak naturally like a helpful friend"""
            
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": vision_prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
                    ]
                }
            ]
            
            completion = self.client.chat.completions.create(
                model="llama-3.2-90b-vision-preview",
                messages=messages,
                temperature=0.7,
                max_tokens=300,
                top_p=1,
                stream=False
            )
            
            response = completion.choices[0].message.content
            
            self.conversation_history.append({
                "role": "assistant",
                "content": response
            })
            
            return {
                "response": response,
                "success": True
            }
            
        except Exception as e:
            print(f"AI Vision error: {e}")
            try:
                return self.chat(f"[The AI can see detected objects: {context}] {user_message}")
            except:
                return {
                    "response": "I can't see clearly right now. Could you describe what you're looking for?",
                    "success": False
                }

    def get_social_advice(self, situation: str) -> Dict:
        """Get specific social advice for a situation"""
        prompt = f"""The user is in this social situation and needs advice: "{situation}"

Provide:
1. What might be happening (explain the social context simply)
2. What they can do (2-3 concrete actions)
3. What to avoid (1-2 things not to do)
4. What they can say (provide a simple script)

Keep it warm, simple, and practical. Use clear language."""

        result = self.chat(prompt)
        return {
            "advice": result["response"],
            "success": result["success"]
        }
    
    def practice_conversation(self, scenario: str) -> Dict:
        """Practice a conversation scenario"""
        prompt = f"""The user wants to practice this conversation scenario: "{scenario}"

You will play the role of the other person. Start the conversation naturally.
Keep your responses brief and realistic. Wait for the user to respond.
This is your first message. What do you say?"""
        
        result = self.chat(prompt)
        return {
            "roleplay_start": result["response"],
            "success": result["success"]
        }
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history.clear()
    
    def get_history(self) -> List[Dict]:
        """Get conversation history"""
        return list(self.conversation_history)
