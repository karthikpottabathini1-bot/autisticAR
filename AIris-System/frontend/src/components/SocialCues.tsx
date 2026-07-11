/**
 * Social Cues Component
 * Analyzes social situations and provides guidance
 */

import { useState, useEffect, useRef } from 'react';
import { apiClient } from '../services/api';
import { getBrowserCameraService } from '../services/browserCamera';

interface SocialCuesProps {
  cameraOn: boolean;
  voiceOnlyMode: boolean;
  cameraSource: string;
  onStatsUpdate?: (key: 'objectsFound' | 'textRead' | 'peopleDetected' | 'incidents', increment?: number) => void;
}

export default function SocialCues({ cameraOn, voiceOnlyMode, cameraSource: _cameraSource, onStatsUpdate: _onStatsUpdate }: SocialCuesProps) {
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [situation, setSituation] = useState<string | null>(null);
  const [description, setDescription] = useState('');
  const [responseSuggestions, setResponseSuggestions] = useState<string[]>([]);
  const [avoidActions, setAvoidActions] = useState<string[]>([]);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    if (cameraOn && !isAnalyzing) {
      startAnalysis();
    } else if (!cameraOn && isAnalyzing) {
      stopAnalysis();
    }

    return () => {
      if (isAnalyzing) stopAnalysis();
    };
  }, [cameraOn]);

  const startAnalysis = async () => {
    setIsAnalyzing(true);
    startFrameProcessing();
  };

  const stopAnalysis = async () => {
    setIsAnalyzing(false);
    getBrowserCameraService().stop();
  };

  const startFrameProcessing = () => {
    const browserCamera = getBrowserCameraService();

    const processFrame = async (frameBase64: string) => {
      // Show raw feed immediately
      if (canvasRef.current) {
        const ctx = canvasRef.current.getContext('2d');
        if (ctx) {
          const img = new Image();
          img.onload = () => {
            canvasRef.current!.width = img.width;
            canvasRef.current!.height = img.height;
            ctx.drawImage(img, 0, 0);
          };
          img.src = `data:image/jpeg;base64,${frameBase64}`;
        }
      }

      try {
        const result = await apiClient.analyzeSocialCues(frameBase64);
        
        setSituation(result.situation);
        setDescription(result.description || '');
        setResponseSuggestions(result.response_suggestions || []);
        setAvoidActions(result.avoid_actions || []);

        if (result.annotated_frame && canvasRef.current) {
          const ctx = canvasRef.current.getContext('2d');
          if (ctx) {
            const img = new Image();
            img.onload = () => {
              canvasRef.current!.width = img.width;
              canvasRef.current!.height = img.height;
              ctx.drawImage(img, 0, 0);
            };
            img.src = `data:image/jpeg;base64,${result.annotated_frame}`;
          }
        }

        if (result.description && voiceOnlyMode) {
          speechSynthesis.speak(new SpeechSynthesisUtterance(result.description));
        }
      } catch (error) {
        console.error('Error processing frame:', error);
      }
    };

    browserCamera.start(undefined, processFrame);
  };

  return (
    <div className="relative w-full h-full bg-black flex items-center justify-center">
      <canvas ref={canvasRef} className="max-w-full max-h-full object-contain" />

      <div className="absolute top-4 left-4 bg-black/80 text-white p-4 rounded-lg max-w-sm max-h-[90vh] overflow-y-auto">
        <div className="text-xl font-bold mb-2">👥 Social Cues</div>
        
        {situation ? (
          <>
            <div className="inline-block px-3 py-1 rounded-full bg-blue-500 text-white font-bold text-lg mb-2">
              {situation.replace('_', ' ').toUpperCase()}
            </div>
            <div className="text-sm mb-3">{description}</div>
            
            {responseSuggestions.length > 0 && (
              <div className="bg-green-600/30 border border-green-400 rounded p-2 mb-2">
                <div className="font-semibold mb-1 text-sm">✓ What you can do:</div>
                <ul className="space-y-1 text-xs">
                  {responseSuggestions.map((s, idx) => (
                    <li key={idx} className="flex items-start"><span className="mr-1">•</span>{s}</li>
                  ))}
                </ul>
              </div>
            )}
            
            {avoidActions.length > 0 && (
              <div className="bg-red-600/30 border border-red-400 rounded p-2">
                <div className="font-semibold mb-1 text-sm">⚠ What to avoid:</div>
                <ul className="space-y-1 text-xs">
                  {avoidActions.map((a, idx) => (
                    <li key={idx} className="flex items-start"><span className="mr-1">•</span>{a}</li>
                  ))}
                </ul>
              </div>
            )}
          </>
        ) : (
          <div className="text-gray-400 text-sm">
            {isAnalyzing ? 'Analyzing social situation...' : 'Click the camera button to start'}
          </div>
        )}
      </div>
    </div>
  );
}
