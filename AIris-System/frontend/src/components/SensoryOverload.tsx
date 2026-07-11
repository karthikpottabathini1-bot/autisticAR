/**
 * Sensory Overload Component
 * Monitors environment for sensory overload factors
 */

import { useState, useEffect, useRef } from 'react';
import { apiClient } from '../services/api';
import { getBrowserCameraService } from '../services/browserCamera';

interface SensoryOverloadProps {
  cameraOn: boolean;
  voiceOnlyMode: boolean;
  cameraSource: string;
  onStatsUpdate?: (key: 'objectsFound' | 'textRead' | 'peopleDetected' | 'incidents', increment?: number) => void;
}

export default function SensoryOverload({ cameraOn, voiceOnlyMode, cameraSource: _cameraSource, onStatsUpdate: _onStatsUpdate }: SensoryOverloadProps) {
  const [isMonitoring, setIsMonitoring] = useState(false);
  const [sensoryFactors, setSensoryFactors] = useState<any>({});
  const [warningLevel, setWarningLevel] = useState('');
  const [description, setDescription] = useState('');
  const [copingStrategies, setCopingStrategies] = useState<string[]>([]);
  const [highFactorCount, setHighFactorCount] = useState(0);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    if (cameraOn && !isMonitoring) {
      startMonitoring();
    } else if (!cameraOn && isMonitoring) {
      stopMonitoring();
    }
    return () => { if (isMonitoring) stopMonitoring(); };
  }, [cameraOn]);

  const startMonitoring = async () => {
    setIsMonitoring(true);
    startFrameProcessing();
  };

  const stopMonitoring = async () => {
    setIsMonitoring(false);
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
        const result = await apiClient.analyzeSensoryEnvironment(frameBase64);
        
        setSensoryFactors(result.sensory_factors || {});
        setWarningLevel(result.warning_level || '');
        setDescription(result.description || '');
        setCopingStrategies(result.coping_strategies || []);
        setHighFactorCount(result.high_factor_count || 0);

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

        if (result.warning_level && !result.warning_level.includes('MANAGEABLE') && voiceOnlyMode) {
          speechSynthesis.speak(new SpeechSynthesisUtterance(result.description));
        }
      } catch (error) {
        console.error('Error processing frame:', error);
      }
    };

    browserCamera.start(undefined, processFrame);
  };

  const getFactorColor = (level: string): string => {
    switch (level) {
      case 'high': return 'text-red-400';
      case 'moderate': return 'text-yellow-400';
      case 'low': return 'text-green-400';
      default: return 'text-gray-400';
    }
  };

  const getWarningColor = (): string => {
    if (highFactorCount >= 2) return 'bg-red-600';
    if (highFactorCount === 1) return 'bg-orange-600';
    return 'bg-green-600';
  };

  return (
    <div className="relative w-full h-full bg-black flex items-center justify-center">
      <canvas ref={canvasRef} className="max-w-full max-h-full object-contain" />

      <div className="absolute top-4 left-4 bg-black/80 text-white p-4 rounded-lg max-w-sm max-h-[90vh] overflow-y-auto">
        <div className="text-xl font-bold mb-2">🌊 Sensory Overload</div>
        
        {warningLevel ? (
          <>
            <div className={`inline-block px-3 py-1 rounded-full text-white font-bold text-lg mb-2 ${getWarningColor()}`}>
              {warningLevel}
            </div>
            <div className="text-sm mb-3">{description}</div>
            
            <div className="bg-gray-800/50 rounded p-2 mb-2">
              <div className="font-semibold mb-1 text-sm">Factors:</div>
              <div className="space-y-1 text-xs">
                {Object.entries(sensoryFactors).map(([factor, data]: [string, any]) => (
                  <div key={factor} className="flex justify-between">
                    <span className="capitalize">{factor.replace('_', ' ')}:</span>
                    <span className={`font-bold ${getFactorColor(data.level)}`}>{data.level.toUpperCase()}</span>
                  </div>
                ))}
              </div>
            </div>
            
            {copingStrategies.length > 0 && (
              <div className="bg-blue-600/30 border border-blue-400 rounded p-2">
                <div className="font-semibold mb-1 text-sm">💡 Coping:</div>
                <ul className="space-y-1 text-xs">
                  {copingStrategies.map((s, idx) => (
                    <li key={idx} className="flex items-start"><span className="mr-1">•</span>{s}</li>
                  ))}
                </ul>
              </div>
            )}
          </>
        ) : (
          <div className="text-gray-400 text-sm">
            {isMonitoring ? 'Monitoring environment...' : 'Click the camera button to start'}
          </div>
        )}
      </div>
    </div>
  );
}
