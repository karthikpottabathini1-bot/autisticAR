/**
 * Body Language Component
 * Shows full body pose skeleton + face mesh AR overlay
 * Analyzes how someone is feeling toward the user
 */

import { useState, useEffect } from 'react';
import { apiClient } from '../services/api';
import { getBrowserCameraService } from '../services/browserCamera';

interface BodyLanguageProps {
  cameraOn: boolean;
  voiceOnlyMode: boolean;
  cameraSource: string;
  onStatsUpdate?: (key: 'objectsFound' | 'textRead' | 'peopleDetected' | 'incidents', increment?: number) => void;
}

export default function BodyLanguage({ cameraOn, voiceOnlyMode, cameraSource: _cs, onStatsUpdate: _os }: BodyLanguageProps) {
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [personDetected, setPersonDetected] = useState(false);
  const [faceDetected, setFaceDetected] = useState(false);
  const [bodyLanguage, setBodyLanguage] = useState<any>({});
  const [frameUrl, setFrameUrl] = useState<string | null>(null);

  useEffect(() => {
    if (cameraOn && !isAnalyzing) {
      startAnalysis();
    } else if (!cameraOn && isAnalyzing) {
      stopAnalysis();
    }
    return () => { if (isAnalyzing) stopAnalysis(); };
  }, [cameraOn]);

  const startAnalysis = async () => { setIsAnalyzing(true); startFrameProcessing(); };
  const stopAnalysis = async () => { setIsAnalyzing(false); getBrowserCameraService().stop(); };

  const startFrameProcessing = () => {
    const browserCamera = getBrowserCameraService();
    let lastFrameTime = 0;
    let processingRef = false;

    const processFrame = async (frameBase64: string) => {
      // Show raw feed immediately so screen is never blank
      setFrameUrl(`data:image/jpeg;base64,${frameBase64}`);

      // Gate: skip if already processing a request
      if (processingRef) return;

      const now = Date.now();
      if (now - lastFrameTime < 500) return; // 2 FPS - enough for body analysis
      lastFrameTime = now;

      processingRef = true;
      try {
        const result = await apiClient.processBodyLanguageFrameUpload(frameBase64);
        
        setPersonDetected(result.person_detected || false);
        setFaceDetected(result.face_detected || false);
        setBodyLanguage(result.body_language || {});

        // Overlay annotated frame (has skeleton + face mesh)
        if (result.annotated_frame) {
          setFrameUrl(`data:image/jpeg;base64,${result.annotated_frame}`);
        }

        if (result.body_language?.interpretation && voiceOnlyMode) {
          speechSynthesis.speak(new SpeechSynthesisUtterance(result.body_language.interpretation));
        }
      } catch (error) {
        console.error('Body language error:', error);
      } finally {
        processingRef = false;
      }
    };

    browserCamera.start(undefined, processFrame);
  };

  const { posture, engagement, comfort, details, interpretation } = bodyLanguage;

  return (
    <div className="relative w-full h-full bg-black flex items-center justify-center">
      {frameUrl ? (
        <img src={frameUrl} alt="Body language AR" className="w-full h-full object-contain" />
      ) : (
        <div className="w-full h-full flex items-center justify-center text-dark-text-secondary bg-dark-surface/50">
          <div className="text-center">
            <p className="text-lg">Body Language analysis will appear here</p>
            {!cameraOn && <p className="text-sm mt-2">Click the camera icon to start</p>}
          </div>
        </div>
      )}

      {/* Top-left: Detection status */}
      <div className="absolute top-4 left-4 flex gap-2">
        <div className={`px-3 py-1.5 rounded-full text-sm font-bold ${personDetected ? 'bg-green-600 text-white' : 'bg-gray-700 text-gray-400'}`}>
          {personDetected ? '✓ Person' : '✗ No person'}
        </div>
        <div className={`px-3 py-1.5 rounded-full text-sm font-bold ${faceDetected ? 'bg-green-600 text-white' : 'bg-gray-700 text-gray-400'}`}>
          {faceDetected ? '✓ Face' : '✗ No face'}
        </div>
      </div>

      {/* Bottom panel: Body Language Analysis */}
      <div className="absolute bottom-4 left-4 right-4 bg-black/80 backdrop-blur text-white p-4 rounded-lg">
        {personDetected ? (
          <div className="grid grid-cols-3 gap-3 mb-3">
            <div className="bg-white/10 rounded-lg p-2 text-center">
              <div className="text-xs text-gray-400 uppercase">Posture</div>
              <div className="font-bold capitalize">{posture || '...'}</div>
            </div>
            <div className="bg-white/10 rounded-lg p-2 text-center">
              <div className="text-xs text-gray-400 uppercase">Engagement</div>
              <div className={`font-bold capitalize ${engagement === 'positive' ? 'text-green-400' : engagement === 'interested' ? 'text-yellow-400' : ''}`}>{engagement || '...'}</div>
            </div>
            <div className="bg-white/10 rounded-lg p-2 text-center">
              <div className="text-xs text-gray-400 uppercase">Comfort</div>
              <div className={`font-bold capitalize ${comfort === 'relaxed' ? 'text-green-400' : comfort === 'tense' || comfort === 'defensive' ? 'text-red-400' : ''}`}>{comfort || '...'}</div>
            </div>
          </div>
        ) : (
          <div className="text-center text-gray-400 py-2">
            {isAnalyzing ? 'Looking for person...' : 'Start camera to detect body language'}
          </div>
        )}

        {/* Interpretation */}
        {interpretation && (
          <div className="text-sm text-white/90 italic border-l-2 border-yellow-400 pl-3">
            {interpretation}
          </div>
        )}

        {/* Detail tags */}
        {details && Object.keys(details).length > 0 && (
          <div className="flex flex-wrap gap-1 mt-2">
            {Object.entries(details).map(([k, v]) => (
              <span key={k} className="text-xs px-2 py-0.5 bg-white/10 rounded-full text-gray-300">
                {k}: {(v as string).substring(0, 40)}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Legend */}
      <div className="absolute top-4 right-4 bg-black/70 text-xs text-white rounded-lg p-2 space-y-1">
        <div className="flex items-center gap-1"><span className="w-3 h-3 rounded-full bg-green-400 inline-block"></span> Skeleton</div>
        <div className="flex items-center gap-1"><span className="w-3 h-3 rounded-full bg-yellow-400 inline-block"></span> Face outline</div>
        <div className="flex items-center gap-1"><span className="w-3 h-3 rounded-full bg-pink-400 inline-block"></span> Lips</div>
        <div className="flex items-center gap-1"><span className="w-3 h-3 rounded-full bg-purple-400 inline-block"></span> Cheeks</div>
      </div>
    </div>
  );
}
