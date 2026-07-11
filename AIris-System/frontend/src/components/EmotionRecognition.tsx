/**
 * Emotion Recognition Component
 * Detects and explains facial emotions for autistic individuals
 */

import { useState, useEffect, useRef } from 'react';
import { apiClient } from '../services/api';
import { getBrowserCameraService } from '../services/browserCamera';

interface EmotionRecognitionProps {
  cameraOn: boolean;
  voiceOnlyMode: boolean;
  cameraSource: string;
  onStatsUpdate?: (key: 'objectsFound' | 'textRead' | 'peopleDetected' | 'incidents', increment?: number) => void;
}

export default function EmotionRecognition({ cameraOn, voiceOnlyMode, cameraSource: _cameraSource, onStatsUpdate: _onStatsUpdate }: EmotionRecognitionProps) {
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [currentEmotion, setCurrentEmotion] = useState<string | null>(null);
  const [confidence, setConfidence] = useState(0);
  const [description, setDescription] = useState('');
  const [socialTip, setSocialTip] = useState('');
  const [faces, setFaces] = useState<any[]>([]);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const frameIntervalRef = useRef<number | null>(null);

  useEffect(() => {
    if (cameraOn && !isAnalyzing) {
      startAnalysis();
    } else if (!cameraOn && isAnalyzing) {
      stopAnalysis();
    }

    return () => {
      if (isAnalyzing) {
        stopAnalysis();
      }
    };
  }, [cameraOn]);

  const startAnalysis = async () => {
    setIsAnalyzing(true);
    startFrameProcessing();
  };

  const stopAnalysis = async () => {
    setIsAnalyzing(false);
    if (frameIntervalRef.current) {
      clearInterval(frameIntervalRef.current);
      frameIntervalRef.current = null;
    }
    getBrowserCameraService().stop();
  };

  const startFrameProcessing = () => {
    const browserCamera = getBrowserCameraService();

    const processFrame = async (frameBase64: string) => {
      // Show the raw live feed immediately
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

      // Send to backend for processing
      try {
        const result = await apiClient.processEmotionFrameUpload(frameBase64);
        
        setCurrentEmotion(result.emotion);
        setConfidence(result.confidence);
        setDescription(result.description || '');
        setSocialTip(result.social_tip || '');
        setFaces(result.faces || []);

        // Update with annotated frame from backend (has boxes/labels)
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

        if (result.emotion && voiceOnlyMode) {
          const utterance = new SpeechSynthesisUtterance(result.description);
          speechSynthesis.speak(utterance);
        }
      } catch (error) {
        // Even on error, the raw feed is already showing
        console.error('Error processing frame:', error);
      }
    };

    browserCamera.start(undefined, processFrame);
  };

  const getEmotionColor = (emotion: string | null): string => {
    const colors: Record<string, string> = {
      happy: 'bg-green-500',
      sad: 'bg-blue-500',
      angry: 'bg-red-500',
      surprised: 'bg-yellow-500',
      neutral: 'bg-gray-500',
      fearful: 'bg-purple-500',
      disgusted: 'bg-orange-500'
    };
    return emotion ? colors[emotion] || 'bg-gray-500' : 'bg-gray-500';
  };

  return (
    <div className="relative w-full h-full bg-black flex items-center justify-center">
      <canvas
        ref={canvasRef}
        className="max-w-full max-h-full object-contain"
      />

      {/* Emotion Display */}
      <div className="absolute top-4 left-4 bg-black/80 text-white p-4 rounded-lg max-w-sm">
        <div className="text-xl font-bold mb-2">
          😊 Emotion Recognition
        </div>
        
        {currentEmotion ? (
          <>
            <div className={`inline-block px-3 py-1 rounded-full text-white font-bold text-lg mb-2 ${getEmotionColor(currentEmotion)}`}>
              {currentEmotion.toUpperCase()} ({(confidence * 100).toFixed(0)}%)
            </div>
            
            <div className="text-sm mb-2">{description}</div>
            
            {socialTip && (
              <div className="bg-blue-600/30 border border-blue-400 rounded p-2 mt-2 text-sm">
                <div className="font-semibold mb-1">💡 What to do:</div>
                <div>{socialTip}</div>
              </div>
            )}
          </>
        ) : (
          <div className="text-gray-400 text-sm">
            {isAnalyzing ? 'Looking for faces...' : 'Click the camera button to start'}
          </div>
        )}

        {faces.length > 0 && (
          <div className="text-xs mt-2 text-gray-300">
            Faces detected: {faces.length}
          </div>
        )}
      </div>
    </div>
  );
}
