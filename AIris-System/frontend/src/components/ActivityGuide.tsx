import { useState, useEffect, useRef } from "react";
import {
  Volume2,
  CheckCircle,
  XCircle,
  Loader2,
  Mic,
  MicOff,
} from "lucide-react";
import { apiClient } from "../services/api";
import { getBrowserCameraService } from "../services/browserCamera";

interface ActivityGuideProps {
  cameraOn: boolean;
  voiceOnlyMode?: boolean;
  cameraSource?: "browser" | "backend" | "esp32";
  onStatsUpdate?: (key: 'objectsFound' | 'textRead' | 'peopleDetected' | 'incidents', increment?: number) => void;
}

// Global speech synthesis helper
function speakText(text: string) {
  if (!text || typeof window === 'undefined' || !('speechSynthesis' in window)) return;
  window.speechSynthesis.cancel();
  const u = new SpeechSynthesisUtterance(text);
  u.rate = 0.95;
  window.speechSynthesis.speak(u);
}

export default function ActivityGuide({
  cameraOn,
  voiceOnlyMode: _voiceOnlyMode,
  cameraSource = "backend",
  onStatsUpdate: _onStatsUpdate,
}: ActivityGuideProps) {
  const [taskInput, setTaskInput] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);
  const [currentInstruction, setCurrentInstruction] = useState(
    "Tap the microphone button and say what you need to find."
  );
  const [stage, setStage] = useState("IDLE");
  const [awaitingFeedback, setAwaitingFeedback] = useState(false);
  const [frameUrl, setFrameUrl] = useState<string | null>(null);
  const [detectedObjects, setDetectedObjects] = useState<
    Array<{ name: string; box: number[] }>
  >([]);
  const [handDetected, setHandDetected] = useState(false);
  const [cameraFacingTowardsUser, _setCameraFacingTowardsUser] = useState<boolean>(true);
  const [isRecording, setIsRecording] = useState(false);
  const [aiMessage, setAiMessage] = useState("");
  const frameIntervalRef = useRef<number | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const lastInstructionRef = useRef<string>("");
  const recognitionRef = useRef<any>(null);
  const isRecordingRef = useRef(false);

  const yesButtonRef = useRef<HTMLButtonElement>(null);
  const noButtonRef = useRef<HTMLButtonElement>(null);

  // Refs to avoid stale closures in keyboard handlers
  const cameraOnRef = useRef(cameraOn);
  const taskInputRef = useRef('');
  const frameUrlRef = useRef<string | null>(null);
  const detectedObjectsRef = useRef(detectedObjects);
  const stageRef = useRef(stage);

  // Keep refs in sync
  useEffect(() => { cameraOnRef.current = cameraOn; }, [cameraOn]);
  useEffect(() => { taskInputRef.current = taskInput; }, [taskInput]);
  useEffect(() => { frameUrlRef.current = frameUrl; }, [frameUrl]);
  useEffect(() => { detectedObjectsRef.current = detectedObjects; }, [detectedObjects]);
  useEffect(() => { stageRef.current = stage; }, [stage]);

  // ==================== PUSH-TO-TALK VOICE SYSTEM ====================

  const startRecording = () => {
    if (!cameraOnRef.current) return;
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      console.warn('SpeechRecognition not supported in this browser');
      setAiMessage('Voice recognition not supported. Try Chrome or Edge.');
      return;
    }

    // Cancel any ongoing speech
    window.speechSynthesis.cancel();

    const recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-US';

    recognition.onresult = (event: any) => {
      let transcript = '';
      for (let i = 0; i < event.results.length; i++) {
        transcript += event.results[i][0].transcript;
      }
      taskInputRef.current = transcript;
      setTaskInput(transcript);
    };

    recognition.onerror = (e: any) => {
      if (e.error !== 'aborted' && e.error !== 'no-speech') {
        console.warn('Speech error:', e.error);
      }
    };

    recognition.onend = () => {
      if (isRecordingRef.current) {
        try { recognition.start(); } catch (e) {}
      }
    };

    recognitionRef.current = recognition;
    isRecordingRef.current = true;
    setIsRecording(true);
    setTaskInput('');
    setAiMessage('');

    try {
      recognition.start();
    } catch (e) {
      console.warn('Recognition start error:', e);
    }
  };

  const stopRecording = async () => {
    if (!isRecordingRef.current) return;

    isRecordingRef.current = false;
    setIsRecording(false);
    if (recognitionRef.current) {
      try { recognitionRef.current.stop(); } catch (e) {}
      recognitionRef.current = null;
    }

    // Read from ref to get the latest transcript
    const userText = taskInputRef.current.trim();
    if (!userText || userText.length < 1) {
      setTaskInput('');
      return;
    }

    setIsProcessing(true);
    setAiMessage('');

    const objects = detectedObjectsRef.current;
    const currentFrame = frameUrlRef.current;
    const currentStage = stageRef.current;

    const objectContext = objects.length > 0
      ? `Detected objects: ${objects.map(o => o.name).join(', ')}. `
      : '';

    try {
      const result = await apiClient.chatWithVision(
        userText,
        currentFrame ? currentFrame.replace('data:image/jpeg;base64,', '') : '',
        objectContext + `The user is looking at this camera feed. Help them. ${currentStage !== 'IDLE' ? `Current task stage: ${currentStage.replace(/_/g, ' ')}` : ''}`
      );

      if (result.response) {
        setAiMessage(result.response);
        speakText(result.response);
      }
    } catch (error) {
      console.error('AI error:', error);
      setAiMessage("Sorry, I couldn't process that.");
      speakText("Sorry, I couldn't process that.");
    } finally {
      setIsProcessing(false);
    }
  };

  // Spacebar handler — runs ONCE, uses refs internally
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.code !== 'Space') return;
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return;
      if (!isRecordingRef.current) {
        e.preventDefault();
        startRecording();
      }
    };
    const handleKeyUp = (e: KeyboardEvent) => {
      if (e.code !== 'Space') return;
      if (isRecordingRef.current) {
        e.preventDefault();
        stopRecording();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    window.addEventListener('keyup', handleKeyUp);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      window.removeEventListener('keyup', handleKeyUp);
    };
  }, []); // empty deps — runs once

  useEffect(() => {
    if (cameraOn) {
      startFrameProcessing().catch(err => {
        console.error("[ActivityGuide] Failed to start frame processing:", err);
      });
    } else {
      stopFrameProcessing();
      setFrameUrl(null);
    }
    return () => stopFrameProcessing();
  }, [cameraOn, stage, cameraSource]);

  // Update camera orientation when toggle changes
  useEffect(() => {
    if (cameraOn) {
      apiClient.setCameraOrientation(cameraFacingTowardsUser).catch((error) => {
        console.error("Failed to set camera orientation:", error);
      });
    }
  }, [cameraFacingTowardsUser, cameraOn]);

  const startFrameProcessing = async () => {
    if (frameIntervalRef.current) return;

    let consecutiveErrors = 0;
    let lastFrameTime = 0;
    const FRAME_INTERVAL_MS = 100; // 10 FPS - smooth video feed
    const MAX_CONSECUTIVE_ERRORS = 5;

    // For browser camera, start it with the frame callback
    if (cameraSource === "browser") {
      const browserCamera = getBrowserCameraService();
      
      const processBrowserFrame = async (frameBase64: string) => {
        const now = Date.now();
        if (now - lastFrameTime < FRAME_INTERVAL_MS) {
          return;
        }
        lastFrameTime = now;

        try {
          const result = await apiClient.processActivityFrameUpload(frameBase64);
          
          consecutiveErrors = 0;
          
          setFrameUrl(`data:image/jpeg;base64,${result.frame}`);
          setCurrentInstruction(result.instruction);
          setStage(result.stage);
          setDetectedObjects(result.detected_objects || []);
          setHandDetected(result.hand_detected || false);

          if (
            result.instruction &&
            result.instruction !== lastInstructionRef.current
          ) {
            lastInstructionRef.current = result.instruction;
          }

          if (result.stage === "AWAITING_FEEDBACK") {
            setAwaitingFeedback(true);
          }
        } catch (error: any) {
          consecutiveErrors++;
          if (consecutiveErrors > 3) {
            console.error("Error processing browser frame:", error);
            consecutiveErrors = 0;
          }
        }
      };

      // Start the browser camera with the frame callback
      const deviceId = undefined; // Use default camera
      const success = await browserCamera.start(deviceId, processBrowserFrame);
      
      if (!success) {
        console.error("[ActivityGuide] Failed to start browser camera");
        return;
      }
      
      // Set up a polling interval for UI updates
      frameIntervalRef.current = window.setInterval(() => {
        // Keep the interval alive for UI updates
      }, FRAME_INTERVAL_MS);
      
      return;
    }

    // For backend/ESP32 camera, use the original polling approach
    const processFrame = async () => {
      // Stop if camera is off
      if (!cameraOn) {
        if (frameIntervalRef.current) {
          clearInterval(frameIntervalRef.current);
          frameIntervalRef.current = null;
        }
        return;
      }

      const now = Date.now();
      // Throttle to prevent overwhelming the backend
      if (now - lastFrameTime < FRAME_INTERVAL_MS) {
        return;
      }
      lastFrameTime = now;

      try {
        // Always use process-frame endpoint to get annotated frames with YOLO boxes and hand tracking
        const result = await apiClient.processActivityFrame();

        // Reset error counter on success
        consecutiveErrors = 0;

        setFrameUrl(`data:image/jpeg;base64,${result.frame}`);
        setCurrentInstruction(result.instruction);
        setStage(result.stage);
        setDetectedObjects(result.detected_objects || []);
        setHandDetected(result.hand_detected || false);

        // Only add to log if instruction is meaningfully different from the last one
        if (
          result.instruction &&
          result.instruction !== lastInstructionRef.current
        ) {
          lastInstructionRef.current = result.instruction;
        }

        if (result.stage === "AWAITING_FEEDBACK") {
          setAwaitingFeedback(true);
        }
      } catch (error: any) {
        consecutiveErrors++;

        // Check for specific error types (Axios errors have error.code, error.response, etc.)
        const errorCode = error?.code || error?.response?.status || "";
        const errorMessage = error?.message || String(error) || "";
        const isResourceError =
          errorCode === "ERR_EMPTY_RESPONSE" ||
          errorCode === "ERR_INSUFFICIENT_RESOURCES" ||
          errorCode === 503 ||
          errorCode === 500 ||
          errorMessage.includes("ERR_EMPTY_RESPONSE") ||
          errorMessage.includes("ERR_INSUFFICIENT_RESOURCES") ||
          errorMessage.includes("Network Error") ||
          (error?.response?.status >= 500 && error?.response?.status < 600);

        if (isResourceError) {
          // Backend is overwhelmed or crashed - back off
          console.warn(
            `[ActivityGuide] Backend resource error (${consecutiveErrors}/${MAX_CONSECUTIVE_ERRORS}):`,
            {
              code: errorCode,
              message: errorMessage,
              status: error?.response?.status,
            }
          );

          if (consecutiveErrors >= MAX_CONSECUTIVE_ERRORS) {
            // Too many errors - stop processing and wait
            console.error(
              "[ActivityGuide] Too many consecutive errors, stopping frame processing"
            );
            if (frameIntervalRef.current) {
              clearInterval(frameIntervalRef.current);
              frameIntervalRef.current = null;
            }
            // Restart after delay
            setTimeout(() => {
              if (cameraOn && frameIntervalRef.current === null) {
                console.log(
                  "[ActivityGuide] Retrying frame processing after backoff"
                );
                consecutiveErrors = 0;
                startFrameProcessing();
              }
            }, 5000); // Wait 5 seconds before retrying
            return;
          }
        } else {
          // Other errors - log but continue (reset counter after a few non-resource errors)
          if (consecutiveErrors > 3) {
            console.error("Error processing frame:", {
              error,
              code: errorCode,
              message: errorMessage,
              status: error?.response?.status,
            });
            consecutiveErrors = 0; // Reset after logging to prevent false positives
          }
        }
      }
    };

    processFrame();
    frameIntervalRef.current = window.setInterval(processFrame, 100); // Update every 100ms for smooth video (~10 FPS)
  };

  const stopFrameProcessing = () => {
    if (frameIntervalRef.current) {
      clearInterval(frameIntervalRef.current);
      frameIntervalRef.current = null;
    }
    
    // Stop browser camera if in browser mode
    if (cameraSource === "browser") {
      const browserCamera = getBrowserCameraService();
      browserCamera.stop().catch(err => {
        console.error("[ActivityGuide] Failed to stop browser camera:", err);
      });
    }
  };

  const handleFeedback = async (confirmed: boolean) => {
    try {
      const response = await apiClient.submitFeedback({ confirmed });
      setAwaitingFeedback(false);
      setStage(response.next_stage);
      setCurrentInstruction(response.message);
      lastInstructionRef.current = "";

      if (confirmed && response.next_stage === "DONE") {
        // Task completed
      } else if (!confirmed) {
        // User said no
      }
    } catch (error) {
      console.error("Error submitting feedback:", error);
    }
  };


  const handlePlayAudio = () => {
    if (currentInstruction) speakText(currentInstruction);
  };

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden relative">
      {/* Camera Feed - Full Screen */}
      <div className="flex-1 bg-black relative min-h-0">
        {cameraOn && frameUrl ? (
          <img
            src={frameUrl}
            alt="Camera feed"
            className="w-full h-full object-contain"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-dark-text-secondary bg-dark-surface/50">
            <div className="text-center">
              <p className="text-lg">Camera feed will appear here</p>
              {!cameraOn && (
                <p className="text-sm mt-2">Click the camera icon in the header to start</p>
              )}
            </div>
          </div>
        )}

        {/* Detection overlay badges */}
        {cameraOn && (
          <div className="absolute top-4 right-4 flex gap-3">
            <div className="bg-black/70 backdrop-blur rounded-lg px-3 py-2 text-sm text-white">
              Objects: <span className="font-bold text-brand-gold">{detectedObjects.length}</span>
            </div>
            <div className="bg-black/70 backdrop-blur rounded-lg px-3 py-2 text-sm text-white">
              Hand: <span className={`font-bold ${handDetected ? "text-green-400" : "text-gray-400"}`}>{handDetected ? "Yes" : "No"}</span>
            </div>
            <div className="bg-black/70 backdrop-blur rounded-lg px-3 py-2 text-sm text-white">
              Stage: <span className="font-bold text-brand-gold">{stage.replace(/_/g, " ")}</span>
            </div>
          </div>
        )}
      </div>

      {/* Bottom Bar - Push to Talk */}
      <div className="bg-dark-surface border-t border-dark-border px-6 py-4">
        <div className="flex items-center gap-4">
          {/* Push-to-Talk Button (press & hold, or hold spacebar) */}
          <button
            onMouseDown={startRecording}
            onMouseUp={stopRecording}
            onMouseLeave={stopRecording}
            onTouchStart={(e) => { e.preventDefault(); startRecording(); }}
            onTouchEnd={(e) => { e.preventDefault(); stopRecording(); }}
            disabled={!cameraOn}
            className={`p-4 rounded-2xl transition-all flex-shrink-0 select-none ${
              isRecording
                ? "bg-red-600 text-white scale-110 shadow-lg shadow-red-500/30"
                : "bg-brand-gold text-brand-charcoal hover:bg-opacity-85 disabled:opacity-40 active:scale-95"
            }`}
            title="Hold SPACEBAR or click & hold to talk"
          >
            {isRecording ? (
              <MicOff className="w-6 h-6" />
            ) : (
              <Mic className="w-6 h-6" />
            )}
          </button>

          {/* Status area */}
          <div className="flex-1 min-w-0">
            {isRecording ? (
              <>
                <div className="text-red-400 font-medium text-sm flex items-center gap-2">
                  <span className="animate-pulse">●</span> Recording... Release to send
                </div>
                {taskInput && (
                  <div className="text-dark-text-primary text-base font-medium truncate mt-0.5">
                    "{taskInput}"
                  </div>
                )}
              </>
            ) : isProcessing ? (
              <div className="flex items-center gap-2 text-dark-text-secondary">
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>AI is thinking...</span>
              </div>
            ) : (
              <>
                <div className="text-dark-text-primary font-medium leading-snug">
                  {aiMessage || currentInstruction}
                </div>
                <div className="text-dark-text-secondary text-xs mt-0.5">
                  Hold <kbd className="px-1.5 py-0.5 bg-dark-bg border border-dark-border rounded text-dark-text-primary text-xs">SPACE</kbd> or press button to talk
                </div>
              </>
            )}

            {/* Feedback buttons */}
            {awaitingFeedback && !isRecording && (
              <div className="mt-3 flex gap-3">
                <button
                  ref={yesButtonRef}
                  onClick={() => handleFeedback(true)}
                  className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 bg-green-600 text-white rounded-xl font-semibold hover:bg-green-700 transition-all"
                >
                  <CheckCircle className="w-5 h-5" />
                  Yes, I got it
                </button>
                <button
                  ref={noButtonRef}
                  onClick={() => handleFeedback(false)}
                  className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 bg-red-600 text-white rounded-xl font-semibold hover:bg-red-700 transition-all"
                >
                  <XCircle className="w-5 h-5" />
                  No, not yet
                </button>
              </div>
            )}
          </div>

          {/* Audio replay */}
          <button
            onClick={handlePlayAudio}
            className="p-3 border border-dark-border text-dark-text-secondary rounded-xl hover:border-brand-gold hover:text-brand-gold transition-all flex-shrink-0"
            title="Replay last instruction"
          >
            <Volume2 className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Hidden audio element */}
      <audio ref={audioRef} />
    </div>
  );
}
