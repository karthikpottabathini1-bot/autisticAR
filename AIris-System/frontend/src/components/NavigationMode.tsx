/**
 * Navigation Mode Component
 * Provides real-time obstacle detection and navigation assistance
 */

import { useEffect, useRef, useState } from 'react';
import { apiClient } from '../services/api';
import { getBrowserCameraService } from '../services/browserCamera';

interface NavigationModeProps {
  cameraOn: boolean;
  voiceOnlyMode: boolean;
  cameraSource: string;
  onStatsUpdate?: (key: 'objectsFound' | 'textRead' | 'peopleDetected' | 'incidents', increment?: number) => void;
}

export default function NavigationMode({ cameraOn, voiceOnlyMode, cameraSource, onStatsUpdate }: NavigationModeProps) {
  const [isNavigating, setIsNavigating] = useState(false);
  const [guidance, setGuidance] = useState('');
  const [safePath, setSafePath] = useState('center');
  const [obstacles, setObstacles] = useState<any[]>([]);
  const [alert, setAlert] = useState(false);
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const frameIntervalRef = useRef<number | null>(null);

  useEffect(() => {
    if (cameraOn && !isNavigating) {
      startNavigation();
    } else if (!cameraOn && isNavigating) {
      stopNavigation();
    }

    return () => {
      if (isNavigating) {
        stopNavigation();
      }
    };
  }, [cameraOn]);

  const startNavigation = async () => {
    try {
      await apiClient.startNavigation();
      setIsNavigating(true);
      startFrameProcessing();
    } catch (error) {
      console.error('Failed to start navigation:', error);
    }
  };

  const stopNavigation = async () => {
    try {
      await apiClient.stopNavigation();
      setIsNavigating(false);
      if (frameIntervalRef.current) {
        clearInterval(frameIntervalRef.current);
        frameIntervalRef.current = null;
      }
    } catch (error) {
      console.error('Failed to stop navigation:', error);
    }
  };

  const startFrameProcessing = () => {
    const browserCamera = getBrowserCameraService();

    const processFrame = async (frameBase64: string) => {
      try {
        const result = await apiClient.processNavigationFrameUpload(frameBase64);
        
        setGuidance(result.guidance || '');
        setSafePath(result.safe_path || 'center');
        setObstacles(result.obstacles || []);
        setAlert(result.alert || false);

        // Update stats
        if (result.obstacles && result.obstacles.length > 0) {
          onStatsUpdate?.('objectsFound', result.obstacles.length);
        }
        if (result.alert) {
          onStatsUpdate?.('incidents');
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

        // Voice feedback for alerts
        if (result.alert && voiceOnlyMode) {
          const utterance = new SpeechSynthesisUtterance(result.alert_message || 'Obstacle ahead');
          speechSynthesis.speak(utterance);
        } else if (result.guidance && voiceOnlyMode) {
          // Periodic guidance updates
          const utterance = new SpeechSynthesisUtterance(result.guidance);
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

      {/* Guidance Overlay */}
      <div className="absolute top-4 left-4 right-4 bg-black/70 text-white p-4 rounded-lg">
        <div className="text-lg font-semibold mb-2">
          {alert ? '⚠️ ALERT' : '🧭 Navigation Mode'}
        </div>
        <div className="text-sm">{guidance || 'Starting navigation...'}</div>
        <div className="text-xs mt-2 text-gray-300">
          Safe path: {safePath} | Obstacles: {obstacles.length}
        </div>
      </div>

      {/* Safe Path Indicator */}
      <div className="absolute bottom-4 left-1/2 transform -translate-x-1/2 bg-black/70 text-white px-6 py-3 rounded-lg">
        <div className="text-center">
          <div className="text-2xl">
            {safePath === 'left' ? '←' : safePath === 'right' ? '→' : '↑'}
          </div>
          <div className="text-xs mt-1">
            {safePath === 'left' ? 'Move Left' : safePath === 'right' ? 'Move Right' : 'Go Straight'}
          </div>
        </div>
      </div>

      {/* Obstacle List */}
      {obstacles.length > 0 && (
        <div className="absolute top-4 right-4 bg-black/70 text-white p-3 rounded-lg max-w-xs">
          <div className="text-sm font-semibold mb-2">Detected Obstacles:</div>
          <ul className="text-xs space-y-1">
            {obstacles.slice(0, 5).map((obs, idx) => (
              <li key={idx}>
                • {obs.class} ({obs.distance.toFixed(1)}m, {obs.position})
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
