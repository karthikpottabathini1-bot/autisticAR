/**
 * Communication Helper Component
 * Provides social scripts and response suggestions
 */

import { useState, useEffect } from 'react';
import { apiClient } from '../services/api';

interface CommunicationHelperProps {
  cameraOn: boolean;
  voiceOnlyMode: boolean;
  cameraSource: string;
  onStatsUpdate?: (key: 'objectsFound' | 'textRead' | 'peopleDetected' | 'incidents', increment?: number) => void;
}

export default function CommunicationHelper({ cameraOn: _cameraOn, voiceOnlyMode, cameraSource: _cameraSource, onStatsUpdate: _onStatsUpdate }: CommunicationHelperProps) {
  const [selectedSituation, setSelectedSituation] = useState<string>('');
  const [script, setScript] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [_allScripts, setAllScripts] = useState<any>({});

  useEffect(() => {
    loadAllScripts();
  }, []);

  const loadAllScripts = async () => {
    try {
      const scripts = await apiClient.getAllCommunicationScripts();
      setAllScripts(scripts);
    } catch (error) {
      console.error('Error loading scripts:', error);
    }
  };

  const handleSituationChange = async (situation: string) => {
    setSelectedSituation(situation);
    if (!situation) {
      setScript(null);
      return;
    }

    setLoading(true);
    try {
      const result = await apiClient.getCommunicationScript(situation);
      setScript(result);
      
      // Voice feedback
      if (voiceOnlyMode && result.description) {
        const utterance = new SpeechSynthesisUtterance(result.description);
        speechSynthesis.speak(utterance);
      }
    } catch (error) {
      console.error('Error loading script:', error);
    } finally {
      setLoading(false);
    }
  };

  const situations = [
    { value: 'greeting', label: '👋 Greeting someone' },
    { value: 'farewell', label: '👋 Saying goodbye' },
    { value: 'thanking', label: '🙏 Thanking someone' },
    { value: 'apologizing', label: '😔 Apologizing' },
    { value: 'asking_for_help', label: '🆘 Asking for help' },
    { value: 'answering_question', label: '❓ Answering a question' },
    { value: 'starting_conversation', label: '💬 Starting a conversation' },
    { value: 'ending_conversation', label: '👋 Ending a conversation' },
    { value: 'rejecting_request', label: '🚫 Saying no' },
    { value: 'expressing_feelings', label: '💭 Expressing feelings' }
  ];

  return (
    <div className="relative w-full h-full bg-gradient-to-br from-blue-900 to-purple-900 flex items-center justify-center p-8">
      <div className="bg-black/80 text-white p-8 rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        <div className="text-3xl font-bold mb-6">
          💬 Communication Helper
        </div>
        
        <div className="mb-6">
          <label className="block text-lg font-semibold mb-3">
            Choose a situation:
          </label>
          <select
            value={selectedSituation}
            onChange={(e) => handleSituationChange(e.target.value)}
            className="w-full bg-gray-800 border border-gray-600 rounded-lg px-4 py-3 text-lg focus:outline-none focus:border-blue-400"
          >
            <option value="">-- Select a situation --</option>
            {situations.map((sit) => (
              <option key={sit.value} value={sit.value}>
                {sit.label}
              </option>
            ))}
          </select>
        </div>

        {loading && (
          <div className="text-center py-8">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-400"></div>
            <div className="mt-4 text-gray-400">Loading script...</div>
          </div>
        )}

        {script && !loading && (
          <div className="space-y-6">
            {/* When to use */}
            <div className="bg-blue-600/30 border border-blue-400 rounded-lg p-4">
              <div className="font-semibold text-lg mb-2">📍 When to use this:</div>
              <div className="text-lg">{script.when}</div>
            </div>

            {/* Example scripts */}
            <div className="bg-green-600/30 border border-green-400 rounded-lg p-4">
              <div className="font-semibold text-lg mb-3">💬 What you can say:</div>
              <ul className="space-y-2">
                {script.scripts.map((s: string, idx: number) => (
                  <li key={idx} className="flex items-start">
                    <span className="mr-2 text-green-400">•</span>
                    <span className="text-lg">"{s}"</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Tips */}
            <div className="bg-purple-600/30 border border-purple-400 rounded-lg p-4">
              <div className="font-semibold text-lg mb-3">💡 Tips:</div>
              <ul className="space-y-2">
                {script.tips.map((tip: string, idx: number) => (
                  <li key={idx} className="flex items-start">
                    <span className="mr-2 text-purple-400">•</span>
                    <span>{tip}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}

        {!selectedSituation && !loading && (
          <div className="text-center py-12 text-gray-400">
            <div className="text-6xl mb-4">💭</div>
            <div className="text-xl">Select a situation above to get help with what to say</div>
          </div>
        )}
      </div>
    </div>
  );
}
