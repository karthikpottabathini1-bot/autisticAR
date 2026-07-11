/**
 * AI Assistant - Continuous voice-to-voice conversation
 * Like talking on the phone. AI speaks back to you.
 * Press Start - pause/resume between turns.
 */

import { useState, useEffect, useRef } from 'react';
import { apiClient } from '../services/api';
import { Mic, MicOff, Send, Volume2, Phone, PhoneOff } from 'lucide-react';

interface AIAssistantProps {
  cameraOn: boolean;
  voiceOnlyMode: boolean;
  cameraSource: string;
  onStatsUpdate?: (key: 'objectsFound' | 'textRead' | 'peopleDetected' | 'incidents', increment?: number) => void;
  mode?: string;
}

export default function AIAssistant({ cameraOn: _c, voiceOnlyMode: _v, cameraSource: _cs, onStatsUpdate: _os, mode = '' }: AIAssistantProps) {
  const [messages, setMessages] = useState<Array<{ role: string; content: string }>>([]);
  const [isCallActive, setIsCallActive] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [isThinking, setIsThinking] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [inputText, setInputText] = useState('');
  const [error, setError] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const recognitionRef = useRef<any>(null);
  const shouldListenRef = useRef(false);
  const isSpeakingRef = useRef(false);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Stop everything on unmount
  useEffect(() => {
    return () => {
      stopVoiceInput();
      speechSynthesis.cancel();
    };
  }, []);

  // Speak the AI's response and then auto-listen again
  const speakAndListen = (text: string) => {
    if (!('speechSynthesis' in window)) return;

    speechSynthesis.cancel();
    setIsSpeaking(true);
    isSpeakingRef.current = true;

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 0.95;
    utterance.pitch = 1.0;

    utterance.onend = () => {
      setIsSpeaking(false);
      isSpeakingRef.current = false;
      // Auto-start listening again if call is still active
      if (shouldListenRef.current && isCallActive) {
        setTimeout(() => startVoiceInput(), 400);
      }
    };

    utterance.onerror = () => {
      setIsSpeaking(false);
      isSpeakingRef.current = false;
      if (shouldListenRef.current && isCallActive) {
        setTimeout(() => startVoiceInput(), 400);
      }
    };

    speechSynthesis.speak(utterance);
  };

  // Send message to AI
  const sendMessage = async (text: string) => {
    if (!text.trim() || isThinking) return;

    const userMsg = { role: 'user', content: text };
    setMessages(prev => [...prev, userMsg]);
    setInputText('');
    setIsThinking(true);
    setIsListening(false);
    setError('');

    // Build context about current mode
    let contextualMessage = text;
    if (mode === 'Activity Guide') {
      contextualMessage = `[User is in Activity Guide mode. They need help finding objects.] ${text}`;
    } else if (mode === 'Scene Description') {
      contextualMessage = `[User is viewing their environment.] ${text}`;
    }

    try {
      const result = await apiClient.chatWithAI(contextualMessage);
      const aiMsg = { role: 'assistant', content: result.response };
      setMessages(prev => [...prev, aiMsg]);

      // Speak the response, then resume listening
      if (isCallActive) {
        speakAndListen(result.response);
      } else {
        justSpeak(result.response);
      }
    } catch (err) {
      setMessages(prev => [...prev, { role: 'assistant', content: "Sorry, I had trouble. Say that again?" }]);
      setError('Connection error. Try again.');
      if (shouldListenRef.current && isCallActive) {
        setTimeout(() => startVoiceInput(), 500);
      }
    } finally {
      setIsThinking(false);
    }
  };

  const justSpeak = (text: string) => {
    if (!('speechSynthesis' in window)) return;
    speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 0.95;
    speechSynthesis.speak(utterance);
  };

  // Voice recognition for continuous conversation
  const startVoiceInput = () => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setError('Voice input needs Chrome browser.');
      return;
    }

    if (isSpeakingRef.current || isThinking) {
      setTimeout(() => startVoiceInput(), 300);
      return;
    }

    stopVoiceInput();

    const recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = 'en-US';

    recognition.onresult = (event: any) => {
      const text = event.results[0][0].transcript.trim();
      if (text && shouldListenRef.current) {
        sendMessage(text);
      }
    };

    recognition.onerror = (event: any) => {
      if (event.error === 'no-speech' && shouldListenRef.current && isCallActive && !isThinking && !isSpeakingRef.current) {
        setTimeout(() => startVoiceInput(), 500);
      } else if (event.error !== 'aborted') {
        console.warn('Speech error:', event.error);
        if (shouldListenRef.current && isCallActive) {
          setTimeout(() => startVoiceInput(), 1000);
        }
      }
      setIsListening(false);
    };

    recognition.onend = () => {
      setIsListening(false);
    };

    recognitionRef.current = recognition;
    setIsListening(true);
    shouldListenRef.current = true;

    try {
      recognition.start();
    } catch (e) {
      console.warn('Recognition start failed:', e);
      setIsListening(false);
    }
  };

  const stopVoiceInput = () => {
    if (recognitionRef.current) {
      try { recognitionRef.current.stop(); } catch (e) {}
      try { recognitionRef.current.abort(); } catch (e) {}
      recognitionRef.current = null;
    }
    setIsListening(false);
    shouldListenRef.current = false;
  };

  // Start / Stop the conversation call
  const toggleCall = () => {
    if (isCallActive) {
      setIsCallActive(false);
      stopVoiceInput();
      speechSynthesis.cancel();
      setIsSpeaking(false);
      isSpeakingRef.current = false;
      setIsListening(false);
      shouldListenRef.current = false;
    } else {
      setIsCallActive(true);
      shouldListenRef.current = true;
      const greeting = messages.length === 0
        ? `Hi! I'm your AI assistant. ${mode ? `You're in ${mode} mode. ` : ''}How can I help you?`
        : "I'm here. What else can I help with?";
      speakAndListen(greeting);
    }
  };

  const suggestions = [
    "Help me find my water bottle",
    "What do I see around me?",
    "How do I know if someone is angry?",
    "I feel overwhelmed, what should I do?",
    "Tell me how to start a conversation",
  ];

  return (
    <div className="flex flex-col h-full bg-gradient-to-b from-gray-900 to-black">
      {/* Header */}
      <div className="bg-black/50 px-6 py-3 border-b border-gray-800 flex-shrink-0 flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold text-white">🤖 AI Voice Chat</h2>
          <p className="text-gray-400 text-xs">Talk naturally — I speak back</p>
        </div>
        <button
          onClick={toggleCall}
          className={`flex items-center gap-2 px-5 py-2.5 rounded-full font-bold text-sm transition-all ${
            isCallActive
              ? 'bg-red-600 hover:bg-red-700 text-white animate-pulse'
              : 'bg-green-600 hover:bg-green-700 text-white'
          }`}
        >
          {isCallActive ? (
            <><PhoneOff className="w-4 h-4" /> End Call</>
          ) : (
            <><Phone className="w-4 h-4" /> Start Call</>
          )}
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-3">
        {messages.length === 0 && !isCallActive && (
          <div className="text-center py-8">
            <div className="text-5xl mb-4">🤖</div>
            <p className="text-gray-400 mb-2">Press <span className="text-green-400 font-bold">Start Call</span> to begin a voice conversation</p>
            <p className="text-gray-600 text-sm mb-6">The AI will speak back to you — like talking on the phone</p>
            <div className="flex flex-wrap justify-center gap-2">
              {suggestions.map((s, i) => (
                <button key={i} onClick={() => sendMessage(s)} className="px-4 py-2 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-full text-sm transition-colors">
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[80%] rounded-2xl px-4 py-2.5 ${
              msg.role === 'user'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-800 text-gray-100'
            }`}>
              <p className="text-sm leading-relaxed">{msg.content}</p>
              {msg.role === 'assistant' && (
                <button onClick={() => { speechSynthesis.cancel(); justSpeak(msg.content); }}
                  className="mt-1.5 text-gray-400 hover:text-white transition-colors">
                  <Volume2 className="w-3.5 h-3.5" />
                </button>
              )}
            </div>
          </div>
        ))}

        {/* Status indicators */}
        {(isThinking || isListening || isSpeaking) && (
          <div className="flex justify-center">
            <div className={`px-4 py-1.5 rounded-full text-xs font-medium ${
              isThinking ? 'bg-yellow-600/30 text-yellow-300' :
              isSpeaking ? 'bg-blue-600/30 text-blue-300' :
              'bg-red-600/30 text-red-300'
            }`}>
              {isThinking && '🤔 Thinking...'}
              {isListening && '🎤 Listening...'}
              {isSpeaking && '🔊 Speaking...'}
            </div>
          </div>
        )}

        {error && (
          <div className="flex justify-center">
            <div className="px-4 py-1.5 rounded-full text-xs bg-red-600/30 text-red-300">{error}</div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Type input (alternative to voice) */}
      <div className="bg-black/50 px-4 py-3 border-t border-gray-800 flex-shrink-0">
        <div className="flex gap-2 items-center">
          <div className="flex-1 relative">
            <input
              type="text"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && sendMessage(inputText)}
              placeholder={
                isCallActive
                  ? isListening ? '🎤 Speak now...' : isThinking ? 'AI thinking...' : 'Ready...'
                  : 'Type a message or call mode...'
              }
              disabled={isListening || isThinking}
              className="w-full bg-gray-800 border border-gray-700 rounded-xl px-4 py-2.5 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 disabled:opacity-50"
            />
            {isCallActive && (
              <div className="absolute right-2 top-1/2 -translate-y-1/2">
                <div className={`w-3 h-3 rounded-full ${
                  isListening ? 'bg-red-500 animate-pulse' :
                  isThinking ? 'bg-yellow-500' :
                  isSpeaking ? 'bg-blue-500' : 'bg-gray-500'
                }`} />
              </div>
            )}
          </div>

          <button
            onClick={() => sendMessage(inputText)}
            disabled={!inputText.trim() || isThinking}
            className="p-2.5 rounded-xl bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 transition-all"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>

        {isCallActive && (
          <div className="flex justify-center gap-3 mt-2">
            <button
              onClick={isListening ? stopVoiceInput : startVoiceInput}
              disabled={isThinking || isSpeaking}
              className={`flex items-center gap-1 px-3 py-1 rounded-full text-xs font-medium transition-all ${
                isListening ? 'bg-red-600/30 text-red-300' : 'bg-blue-600/30 text-blue-300 hover:bg-blue-600/50'
              } disabled:opacity-30`}
            >
              {isListening ? <MicOff className="w-3 h-3" /> : <Mic className="w-3 h-3" />}
              {isListening ? 'Stop Mic' : 'Start Mic'}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
