/**
 * Color Recognition Component
 * Identifies and announces colors in the camera view
 */

import { useEffect, useRef, useState } from 'react';
import { apiClient } from '../services/api';
import { getBrowserCameraService } from '../services/browserCamera';

interface ColorRecognitionProps {
  cameraOn: boolean;
  voiceOnlyMode: boolean;
  cameraSource: string;
  onStatsUpdate?: (key: 'objectsFound' | 'textRead' | 'peopleDetected' | 'incidents', increment?: number) => void;
}

export default function ColorRecognition({ cameraOn, voiceOnlyMode, cameraSource, onStatsUpdate: _onStatsUpdate }: ColorRecognitionProps) {
  const [isRecognizing, setIsRecognizing] = useState(false);
  const [dominantColor, setDominantColor] = useState('');
  const [colors, setColors] = useState<string[]>([]);
  const [lastSpokenColor, setLastSpokenColor] = useState('');
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const frameIntervalRef = useRef<number | null>(null);

  useEffect(() => {
    if (cameraOn && !isRecognizing) {
      startRecognition();
    } else if (!cameraOn && isRecognizing) {
      stopRecognition();
    }

    return () => {
      if (isRecognizing) {
        stopRecognition();
      }
    };
  }, [cameraOn]);

  const startRecognition = async () => {
    try {
      await apiClient.startColorRecognition();
      setIsRecognizing(true);
      startFrameProcessing();
    } catch (error) {
      console.error('Failed to start color recognition:', error);
    }
  };

  const stopRecognition = async () => {
    try {
      await apiClient.stopColorRecognition();
      setIsRecognizing(false);
      if (frameIntervalRef.current) {
        clearInterval(frameIntervalRef.current);
        frameIntervalRef.current = null;
      }
    } catch (error) {
      console.error('Failed to stop color recognition:', error);
    }
  };

  const startFrameProcessing = () => {
    const browserCamera = getBrowserCameraService();

    const processFrame = async (frameBase64: string) => {
      try {
        const result = await apiClient.processColorFrameUpload(frameBase64);
        
        setDominantColor(result.dominant_color || '');
        setColors(result.colors || []);

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

        // Voice feedback for color changes
        if (result.dominant_color && result.dominant_color !== lastSpokenColor && voiceOnlyMode) {
          setLastSpokenColor(result.dominant_color);
          const utterance = new SpeechSynthesisUtterance(`I see ${result.dominant_color}`);
          speechSynthesis.speak(utterance);
        }
      } catch (error) {
        console.error('Frame processing error:', error);
      }
    };

    browserCamera.start(cameraSource === 'browser' ? 'user' : 'environment', processFrame);
  };

  const getColorHex = (colorName: string): string => {
    const colorMap: Record<string, string> = {
      'red': '#ef4444',
      'orange': '#f97316',
      'yellow': '#eab308',
      'green': '#22c55e',
      'blue': '#3b82f6',
      'purple': '#a855f7',
      'pink': '#ec4899',
      'white': '#ffffff',
      'black': '#000000',
      'gray': '#6b7280',
      'brown': '#92400e',
    };
    return colorMap[colorName.toLowerCase()] || '#6b7280';
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

      {/* Color Status Overlay */}
      <div className="absolute top-4 left-4 right-4 bg-black/70 text-white p-4 rounded-lg">
        <div className="text-lg font-semibold mb-2">
          🎨 Color Recognition
        </div>
        {dominantColor ? (
          <div className="flex items-center gap-3">
            <div 
              className="w-12 h-12 rounded-lg border-2 border-white"
              style={{ backgroundColor: getColorHex(dominantColor) }}
            />
            <div>
              <div className="text-xl font-bold capitalize">{dominantColor}</div>
              <div className="text-xs text-gray-300">Dominant color</div>
            </div>
          </div>
        ) : (
          <div className="text-sm text-gray-400">
            Point camera at objects to identify colors...
          </div>
        )}
      </div>

      {/* All Detected Colors */}
      {colors.length > 1 && (
        <div className="absolute bottom-4 left-4 right-4 bg-black/70 text-white p-3 rounded-lg">
          <div className="text-sm font-semibold mb-2">All Detected Colors:</div>
          <div className="flex flex-wrap gap-2">
            {colors.map((color, idx) => (
              <div 
                key={idx}
                className="flex items-center gap-2 bg-white/10 px-3 py-1 rounded-full"
              >
                <div 
                  className="w-4 h-4 rounded-full border border-white"
                  style={{ backgroundColor: getColorHex(color) }}
                />
                <span className="text-sm capitalize">{color}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
