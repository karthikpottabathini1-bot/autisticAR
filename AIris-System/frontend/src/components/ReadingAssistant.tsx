/**
 * Reading Assistant Component
 * Provides OCR text detection and reading assistance
 */

import { useEffect, useRef, useState } from 'react';
import { apiClient } from '../services/api';
import { getBrowserCameraService } from '../services/browserCamera';

interface ReadingAssistantProps {
  cameraOn: boolean;
  voiceOnlyMode: boolean;
  cameraSource: string;
  onStatsUpdate?: (key: 'objectsFound' | 'textRead' | 'peopleDetected' | 'incidents', increment?: number) => void;
}

export default function ReadingAssistant({ cameraOn, voiceOnlyMode, cameraSource, onStatsUpdate }: ReadingAssistantProps) {
  const [isReading, setIsReading] = useState(false);
  const [detectedText, setDetectedText] = useState('');
  const [confidence, setConfidence] = useState(0);
  const [textRegions, setTextRegions] = useState<any[]>([]);
  const [lastSpokenText, setLastSpokenText] = useState('');
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const frameIntervalRef = useRef<number | null>(null);

  useEffect(() => {
    if (cameraOn && !isReading) {
      startReading();
    } else if (!cameraOn && isReading) {
      stopReading();
    }

    return () => {
      if (isReading) {
        stopReading();
      }
    };
  }, [cameraOn]);

  const startReading = async () => {
    try {
      await apiClient.startReadingAssistant();
      setIsReading(true);
      startFrameProcessing();
    } catch (error) {
      console.error('Failed to start reading assistant:', error);
    }
  };

  const stopReading = async () => {
    try {
      await apiClient.stopReadingAssistant();
      setIsReading(false);
      if (frameIntervalRef.current) {
        clearInterval(frameIntervalRef.current);
        frameIntervalRef.current = null;
      }
    } catch (error) {
      console.error('Failed to stop reading assistant:', error);
    }
  };

  const startFrameProcessing = () => {
    const browserCamera = getBrowserCameraService();

    const processFrame = async (frameBase64: string) => {
      try {
        const result = await apiClient.processReadingFrameUpload(frameBase64);
        
        setDetectedText(result.text || '');
        setConfidence(result.confidence || 0);
        setTextRegions(result.regions || []);

        // Update stats when new text is detected
        if (result.text && result.text !== lastSpokenText) {
          onStatsUpdate?.('textRead');
        }

        // Draw annotated frame
        if (canvasRef.current && result.annotated_frame) {
          const ctx = canvasRef.current.getContext('2d');
          if (ctx) {
            const img = new Image();
            img.onload = () => {
              ctx.clearRect(0, 0, canvasRef.current!.width, canvasRef.current!.height);
              ctx.drawImage(img, 0, 0);
            };
            img.src = `data:image/jpeg;base64,${result.annotated_frame}`;
          }
        }

        // Voice feedback for new text
        if (result.text && result.text !== lastSpokenText && voiceOnlyMode) {
          setLastSpokenText(result.text);
          const utterance = new SpeechSynthesisUtterance(result.text);
          utterance.rate = 0.9; // Slightly slower for clarity
          speechSynthesis.speak(utterance);
        }
      } catch (error) {
        console.error('Frame processing error:', error);
      }
    };

    browserCamera.start(cameraSource === 'browser' ? 'user' : 'environment', processFrame);
  };

  return (
    <div className="relative w-full h-full bg-black flex items-center justify-center">
      <video
        ref={videoRef}
        autoPlay
        playsInline
        muted
        className="absolute inset-0 w-full h-full object-cover opacity-0"
      />
      
      <canvas
        ref={canvasRef}
        width={640}
        height={480}
        className="max-w-full max-h-full"
      />

      {/* Reading Status Overlay */}
      <div className="absolute top-4 left-4 right-4 bg-black/70 text-white p-4 rounded-lg">
        <div className="text-lg font-semibold mb-2">
          📖 Reading Assistant
        </div>
        {detectedText ? (
          <>
            <div className="text-sm mb-2">{detectedText}</div>
            <div className="text-xs text-gray-300">
              Confidence: {(confidence * 100).toFixed(1)}% | Regions: {textRegions.length}
            </div>
          </>
        ) : (
          <div className="text-sm text-gray-400">
            Point camera at text to read...
          </div>
        )}
      </div>

      {/* Text Regions Info */}
      {textRegions.length > 0 && (
        <div className="absolute bottom-4 left-4 right-4 bg-black/70 text-white p-3 rounded-lg">
          <div className="text-sm font-semibold mb-2">Detected Text Regions:</div>
          <div className="text-xs space-y-1 max-h-32 overflow-y-auto">
            {textRegions.map((region, idx) => (
              <div key={idx} className="flex justify-between">
                <span className="truncate mr-2">{region.text}</span>
                <span className="text-gray-400">{(region.confidence * 100).toFixed(0)}%</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
