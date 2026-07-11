/**
 * People Counter Component
 * Detects and counts people in the camera view
 */

import { useEffect, useRef, useState } from 'react';
import { apiClient } from '../services/api';
import { getBrowserCameraService } from '../services/browserCamera';

interface PeopleCounterProps {
  cameraOn: boolean;
  voiceOnlyMode: boolean;
  cameraSource: string;
  onStatsUpdate?: (key: 'objectsFound' | 'textRead' | 'peopleDetected' | 'incidents', increment?: number) => void;
}

export default function PeopleCounter({ cameraOn, voiceOnlyMode, cameraSource, onStatsUpdate }: PeopleCounterProps) {
  const [isCounting, setIsCounting] = useState(false);
  const [peopleCount, setPeopleCount] = useState(0);
  const [people, setPeople] = useState<any[]>([]);
  const [lastSpokenCount, setLastSpokenCount] = useState(-1);
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const frameIntervalRef = useRef<number | null>(null);

  useEffect(() => {
    if (cameraOn && !isCounting) {
      startCounting();
    } else if (!cameraOn && isCounting) {
      stopCounting();
    }

    return () => {
      if (isCounting) {
        stopCounting();
      }
    };
  }, [cameraOn]);

  const startCounting = async () => {
    try {
      await apiClient.startPeopleCounter();
      setIsCounting(true);
      startFrameProcessing();
    } catch (error) {
      console.error('Failed to start people counter:', error);
    }
  };

  const stopCounting = async () => {
    try {
      await apiClient.stopPeopleCounter();
      setIsCounting(false);
      if (frameIntervalRef.current) {
        clearInterval(frameIntervalRef.current);
        frameIntervalRef.current = null;
      }
    } catch (error) {
      console.error('Failed to stop people counter:', error);
    }
  };

  const startFrameProcessing = () => {
    const browserCamera = getBrowserCameraService();

    const processFrame = async (frameBase64: string) => {
      try {
        const result = await apiClient.processPeopleFrameUpload(frameBase64);
        
        setPeopleCount(result.count || 0);
        setPeople(result.people || []);

        // Update stats when people are detected
        if (result.count && result.count > 0) {
          onStatsUpdate?.('peopleDetected', result.count);
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

        // Voice feedback for count changes
        if (result.count !== lastSpokenCount && voiceOnlyMode) {
          setLastSpokenCount(result.count);
          let message = '';
          if (result.count === 0) {
            message = 'No people detected';
          } else if (result.count === 1) {
            message = 'One person detected';
          } else {
            message = `${result.count} people detected`;
          }
          const utterance = new SpeechSynthesisUtterance(message);
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

      {/* People Count Overlay */}
      <div className="absolute top-4 left-4 right-4 bg-black/70 text-white p-4 rounded-lg">
        <div className="text-lg font-semibold mb-2">
          👥 People Counter
        </div>
        <div className="flex items-center gap-4">
          <div className="text-5xl font-bold">{peopleCount}</div>
          <div>
            <div className="text-xl">
              {peopleCount === 0 ? 'No people' : peopleCount === 1 ? '1 person' : `${peopleCount} people`}
            </div>
            <div className="text-xs text-gray-300">detected in view</div>
          </div>
        </div>
      </div>

      {/* People Details */}
      {people.length > 0 && (
        <div className="absolute bottom-4 left-4 right-4 bg-black/70 text-white p-3 rounded-lg">
          <div className="text-sm font-semibold mb-2">People Details:</div>
          <div className="space-y-2 max-h-40 overflow-y-auto">
            {people.map((person, idx) => (
              <div key={idx} className="flex justify-between items-center text-sm">
                <span>Person {idx + 1}</span>
                <div className="flex gap-3 text-xs text-gray-300">
                  <span>{person.distance.toFixed(1)}m away</span>
                  <span className="capitalize">{person.position}</span>
                  <span>{(person.confidence * 100).toFixed(0)}%</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
