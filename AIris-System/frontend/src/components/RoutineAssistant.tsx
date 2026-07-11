/**
 * Routine Assistant Component
 * Helps with daily routines, schedules, and transitions
 */

import { useState, useEffect } from 'react';
import { apiClient } from '../services/api';

interface RoutineAssistantProps {
  cameraOn: boolean;
  voiceOnlyMode: boolean;
  cameraSource: string;
  onStatsUpdate?: (key: 'objectsFound' | 'textRead' | 'peopleDetected' | 'incidents', increment?: number) => void;
}

export default function RoutineAssistant({ cameraOn: _cameraOn, voiceOnlyMode, cameraSource: _cameraSource, onStatsUpdate: _onStatsUpdate }: RoutineAssistantProps) {
  const [routines, setRoutines] = useState<any>({});
  const [selectedRoutine, setSelectedRoutine] = useState<string>('');
  const [currentStep, setCurrentStep] = useState<any>(null);
  const [progress, setProgress] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadRoutines();
  }, []);

  const loadRoutines = async () => {
    try {
      const allRoutines = await apiClient.getAllRoutines();
      setRoutines(allRoutines);
    } catch (error) {
      console.error('Error loading routines:', error);
    }
  };

  const handleRoutineSelect = async (routineName: string) => {
    setSelectedRoutine(routineName);
    if (!routineName) {
      setCurrentStep(null);
      return;
    }

    setLoading(true);
    try {
      const result = await apiClient.startRoutine(routineName);
      setCurrentStep(result);
      
      // Voice feedback
      if (voiceOnlyMode && result.current_step) {
        const utterance = new SpeechSynthesisUtterance(`Starting routine: ${routineName}. First step: ${result.current_step}`);
        speechSynthesis.speak(utterance);
      }
    } catch (error) {
      console.error('Error starting routine:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCompleteStep = async () => {
    if (!selectedRoutine) return;

    setLoading(true);
    try {
      const result = await apiClient.completeRoutineStep(selectedRoutine);
      setCurrentStep(result);
      setProgress(result.progress || '');
      
      // Voice feedback
      if (voiceOnlyMode) {
        if (result.all_done) {
          const utterance = new SpeechSynthesisUtterance('Great job! You completed the routine!');
          speechSynthesis.speak(utterance);
        } else if (result.next_step) {
          const utterance = new SpeechSynthesisUtterance(`Step completed. Next: ${result.next_step}`);
          speechSynthesis.speak(utterance);
        }
      }
    } catch (error) {
      console.error('Error completing step:', error);
    } finally {
      setLoading(false);
    }
  };

  const routineNames = Object.keys(routines);

  return (
    <div className="relative w-full h-full bg-gradient-to-br from-green-900 to-blue-900 flex items-center justify-center p-8">
      <div className="bg-black/80 text-white p-8 rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        <div className="text-3xl font-bold mb-6">
          📋 Routine Assistant
        </div>
        
        <div className="mb-6">
          <label className="block text-lg font-semibold mb-3">
            Choose a routine:
          </label>
          <select
            value={selectedRoutine}
            onChange={(e) => handleRoutineSelect(e.target.value)}
            className="w-full bg-gray-800 border border-gray-600 rounded-lg px-4 py-3 text-lg focus:outline-none focus:border-green-400"
          >
            <option value="">-- Select a routine --</option>
            {routineNames.map((name) => (
              <option key={name} value={name}>
                {name}
              </option>
            ))}
          </select>
        </div>

        {loading && (
          <div className="text-center py-8">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-green-400"></div>
            <div className="mt-4 text-gray-400">Loading...</div>
          </div>
        )}

        {currentStep && !loading && (
          <div className="space-y-6">
            {/* Progress */}
            {progress && (
              <div className="bg-blue-600/30 border border-blue-400 rounded-lg p-4">
                <div className="font-semibold text-lg mb-2">📊 Progress:</div>
                <div className="text-2xl font-bold">{progress}</div>
              </div>
            )}

            {/* Current Step */}
            <div className="bg-green-600/30 border border-green-400 rounded-lg p-6">
              <div className="font-semibold text-lg mb-3">
                {currentStep.all_done ? '✅ Routine Complete!' : '👉 Current Step:'}
              </div>
              <div className="text-2xl font-bold">
                {currentStep.all_done ? 'Great job!' : currentStep.current_step}
              </div>
            </div>

            {/* Next Step Preview */}
            {currentStep.next_step && !currentStep.all_done && (
              <div className="bg-gray-700/50 border border-gray-600 rounded-lg p-4">
                <div className="font-semibold mb-2">⏭️ Next step:</div>
                <div className="text-lg text-gray-300">{currentStep.next_step}</div>
              </div>
            )}

            {/* Complete Button */}
            {!currentStep.all_done && (
              <button
                onClick={handleCompleteStep}
                className="w-full bg-green-600 hover:bg-green-700 text-white font-bold py-4 px-6 rounded-lg text-xl transition-colors"
              >
                ✓ Mark Step Complete
              </button>
            )}

            {/* Restart Button */}
            {currentStep.all_done && (
              <button
                onClick={() => handleRoutineSelect(selectedRoutine)}
                className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-4 px-6 rounded-lg text-xl transition-colors"
              >
                🔄 Restart Routine
              </button>
            )}
          </div>
        )}

        {!selectedRoutine && !loading && (
          <div className="text-center py-12 text-gray-400">
            <div className="text-6xl mb-4">📅</div>
            <div className="text-xl">Select a routine above to get started</div>
          </div>
        )}
      </div>
    </div>
  );
}
