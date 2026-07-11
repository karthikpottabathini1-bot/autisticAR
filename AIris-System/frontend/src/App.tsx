import { useState, useEffect, useRef } from "react";
import { Camera, CameraOff, Settings, Mic, MicOff } from "lucide-react";
import ActivityGuide from "./components/ActivityGuide";
import SceneDescription from "./components/SceneDescription";
import NavigationMode from "./components/NavigationMode";
import ReadingAssistant from "./components/ReadingAssistant";
import ColorRecognition from "./components/ColorRecognition";
import PeopleCounter from "./components/PeopleCounter";
import EmotionRecognition from "./components/EmotionRecognition";
import SocialCues from "./components/SocialCues";
import SensoryOverload from "./components/SensoryOverload";
import CommunicationHelper from "./components/CommunicationHelper";
import RoutineAssistant from "./components/RoutineAssistant";
import BodyLanguage from "./components/BodyLanguage";
import AIAssistant from "./components/AIAssistant";
import HardwareSettings from "./components/HardwareSettings";
import TranscriptionBubble from "./components/TranscriptionBubble";
import { apiClient } from "./services/api";
import { getVoiceControlService } from "./services/voiceControl";
import { generateWelcomeMessage } from "./utils/welcomeMessages";
import { getBrowserCameraService } from "./services/browserCamera";

type Mode = "Activity Guide" | "Scene Description" | "Navigation" | "Reading" | "Color" | "People Counter" | "Emotion Recognition" | "Social Cues" | "Sensory Overload" | "Communication Helper" | "Routine Assistant" | "Body Language" | "AI Assistant";
type CameraSource = "browser" | "backend" | "esp32";

function App() {
  const [mode, setMode] = useState<Mode>("Activity Guide");
  const [cameraOn, setCameraOn] = useState(false);
  const [cameraStatus, setCameraStatus] = useState({
    is_running: false,
    is_available: false,
  });
  const [currentTime, setCurrentTime] = useState(new Date());
  const [showSettings, setShowSettings] = useState(false);
  const [cameraSource, setCameraSource] = useState<CameraSource>(() => {
    const saved = localStorage.getItem("airis-camera-source");
    if (saved === "esp32") return "esp32";
    if (saved === "backend") return "backend";
    return "browser";
  });
  const [availableCameras, setAvailableCameras] = useState<MediaDeviceInfo[]>([]);
  const [selectedCameraId, setSelectedCameraId] = useState<string>("default");
  const [voiceOnlyMode, setVoiceOnlyMode] = useState(false); // Always default to OFF
  const [currentTranscription, setCurrentTranscription] = useState<{
    type: "user" | "system" | "refresh";
    text: string;
  } | null>(null);
  const [sessionStartTime, setSessionStartTime] = useState<number>(Date.now());
  const [sessionStats, setSessionStats] = useState({
    objectsFound: 0,
    textRead: 0,
    peopleDetected: 0,
    incidents: 0,
  });
  const [systemHealth, setSystemHealth] = useState({
    fps: 0,
    latency: 0,
    modelLoaded: false,
  });

  // Function to update session stats
  const updateSessionStats = (key: keyof typeof sessionStats, increment: number = 1) => {
    setSessionStats(prev => ({
      ...prev,
      [key]: prev[key] + increment,
    }));
  };

  const voiceControlRef = useRef(getVoiceControlService());
  const modeButtonRefs = {
    "Activity Guide": useRef<HTMLButtonElement>(null),
    "Scene Description": useRef<HTMLButtonElement>(null),
    "Navigation": useRef<HTMLButtonElement>(null),
    "Reading": useRef<HTMLButtonElement>(null),
    "Color": useRef<HTMLButtonElement>(null),
    "People Counter": useRef<HTMLButtonElement>(null),
    "Emotion Recognition": useRef<HTMLButtonElement>(null),
    "Social Cues": useRef<HTMLButtonElement>(null),
    "Sensory Overload": useRef<HTMLButtonElement>(null),
    "Communication Helper": useRef<HTMLButtonElement>(null),
    "Routine Assistant": useRef<HTMLButtonElement>(null),
    "Body Language": useRef<HTMLButtonElement>(null),
    "AI Assistant": useRef<HTMLButtonElement>(null),
  };
  const cameraButtonRef = useRef<HTMLButtonElement>(null);
  const lastCameraAnnouncementRef = useRef<{
    state: boolean | null;
    timestamp: number;
  }>({ state: null, timestamp: 0 });
  const lastModeAnnouncementRef = useRef<{
    mode: Mode | null;
    timestamp: number;
  }>({ mode: null, timestamp: 0 });

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    const modeKeys: Record<string, Mode> = {
      "1": "Activity Guide",
      "2": "Scene Description",
      "3": "Navigation",
      "4": "Reading",
      "5": "Color",
      "6": "People Counter",
      "7": "Emotion Recognition",
      "8": "Social Cues",
      "9": "Sensory Overload",
      "0": "Communication Helper",
      "q": "Routine Assistant",
      "b": "Body Language",
      "a": "AI Assistant",
    };
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement || e.target instanceof HTMLSelectElement) return;
      const newMode = modeKeys[e.key];
      if (newMode) {
        setMode(newMode);
        if (voiceOnlyMode) {
          voiceControlRef.current.markUserInteracted();
          voiceControlRef.current.speakText(`Switched to ${newMode} mode`, false);
        }
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [voiceOnlyMode]);

  // Update session timer
  useEffect(() => {
    const timer = setInterval(() => {
      setSessionStartTime(prev => prev); // Force re-render
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  // Fetch system health from backend
  useEffect(() => {
    const fetchHealth = async () => {
      try {
        const response = await fetch('http://localhost:8000/health');
        const data = await response.json();
        setSystemHealth(prev => ({
          ...prev,
          modelLoaded: data.models_loaded || false,
        }));
      } catch (error) {
        console.error('Failed to fetch health:', error);
      }
    };
    
    fetchHealth();
    const interval = setInterval(fetchHealth, 5000);
    return () => clearInterval(interval);
  }, []);

  // Update FPS and latency based on camera activity
  useEffect(() => {
    if (!cameraOn) {
      setSystemHealth(prev => ({ ...prev, fps: 0, latency: 0 }));
      return;
    }

    let frameCount = 0;
    let lastTime = Date.now();
    
    const updateFPS = () => {
      const now = Date.now();
      const elapsed = now - lastTime;
      
      if (elapsed >= 1000) {
        const fps = Math.round((frameCount * 1000) / elapsed);
        const latency = Math.round(elapsed / frameCount);
        
        setSystemHealth(prev => ({
          ...prev,
          fps,
          latency: latency || 0,
        }));
        
        frameCount = 0;
        lastTime = now;
      }
      
      frameCount++;
    };

    const interval = setInterval(updateFPS, 100);
    return () => clearInterval(interval);
  }, [cameraOn]);

  useEffect(() => {
    checkCameraStatus();
  }, []);

  useEffect(() => {
    localStorage.setItem("airis-camera-source", cameraSource);
  }, [cameraSource]);

  useEffect(() => {
    const browserCamera = getBrowserCameraService();
    browserCamera.initialize().then(() => {
      const devices = browserCamera.getAvailableDevices();
      setAvailableCameras(devices);
    });
  }, []);

  // Note: Voice-only mode always defaults to OFF and is not persisted to localStorage
  // This ensures a clean state on every page load

  // Voice control setup - only active when voiceOnlyMode is ON
  useEffect(() => {
    const voiceControl = voiceControlRef.current;

    if (!voiceOnlyMode) {
      // Voice-only mode is OFF - stop all voice/TTS activity
      console.log(
        `[App] Voice-only mode disabled, stopping all voice/TTS activity`
      );
      voiceControl.stopListening();
      voiceControl.stopSpeaking();
      return;
    }

    // Voice-only mode is ON - start listening
    console.log(
      `[App] Starting voice control listening. Mode: ${mode}, Camera: ${cameraOn}`
    );

    // Register transcription callback for live transcription display
    const unregisterTranscription = voiceControl.registerTranscriptionCallback(
      (type, text) => {
        setCurrentTranscription({ type, text });
      }
    );

    voiceControl.startListening((command, transcript) => {
      console.log(
        `[App] Voice command received: ${command} - "${transcript}"`,
        {
          mode,
          cameraOn,
          hasActivityGuideButton: !!modeButtonRefs["Activity Guide"].current,
          hasSceneDescriptionButton:
            !!modeButtonRefs["Scene Description"].current,
          hasCameraButton: !!cameraButtonRef.current,
        }
      );

      switch (command) {
        case "switch_mode":
          console.log(`[App] Processing switch_mode command`);
          if (transcript.includes("activity guide")) {
            if (
              mode !== "Activity Guide" &&
              modeButtonRefs["Activity Guide"].current
            ) {
              console.log(`[App] Switching to Activity Guide mode`);
              modeButtonRefs["Activity Guide"].current?.click();
            } else {
              console.log(`[App] Cannot switch to Activity Guide:`, {
                currentMode: mode,
                hasButton: !!modeButtonRefs["Activity Guide"].current,
              });
            }
          } else if (transcript.includes("emotion")) {
            if (
              mode !== "Emotion Recognition" &&
              modeButtonRefs["Emotion Recognition"].current
            ) {
              modeButtonRefs["Emotion Recognition"].current?.click();
            }
          } else if (transcript.includes("scene description")) {
            if (
              mode !== "Scene Description" &&
              modeButtonRefs["Scene Description"].current
            ) {
              console.log(`[App] Switching to Scene Description mode`);
              modeButtonRefs["Scene Description"].current?.click();
            } else {
              console.log(`[App] Cannot switch to Scene Description:`, {
                currentMode: mode,
                hasButton: !!modeButtonRefs["Scene Description"].current,
              });
            }
          }
          break;

        case "camera_on":
          console.log(`[App] Processing camera_on command`);
          if (!cameraOn && cameraButtonRef.current) {
            console.log(`[App] Turning camera on`);
            cameraButtonRef.current.click();
          } else {
            console.log(`[App] Cannot turn camera on:`, {
              cameraOn,
              hasButton: !!cameraButtonRef.current,
            });
          }
          break;

        case "camera_off":
          console.log(`[App] Processing camera_off command`);
          if (cameraOn && cameraButtonRef.current) {
            console.log(`[App] Turning camera off`);
            cameraButtonRef.current.click();
          } else {
            console.log(`[App] Cannot turn camera off:`, {
              cameraOn,
              hasButton: !!cameraButtonRef.current,
            });
          }
          break;

        default:
          console.log(`[App] Unhandled command: ${command}`);
      }
    });

    return () => {
      // Cleanup: stop listening when voice-only mode is disabled or component unmounts
      voiceControl.stopListening();
      unregisterTranscription();
      setCurrentTranscription(null);
    };
  }, [voiceOnlyMode, mode, cameraOn]);

  // Announce mode changes in voice-only mode
  useEffect(() => {
    if (!voiceOnlyMode) {
      return; // Don't announce if voice-only mode is off
    }

    const now = Date.now();
    const timeSinceLastAnnouncement =
      now - lastModeAnnouncementRef.current.timestamp;
    const lastAnnouncedMode = lastModeAnnouncementRef.current.mode;

    // Only announce if:
    // 1. We haven't announced this mode before, OR
    // 2. The last announcement was for a different mode, OR
    // 3. It's been more than 2 seconds since the last announcement
    if (lastAnnouncedMode !== mode || timeSinceLastAnnouncement > 2000) {
      voiceControlRef.current.markUserInteracted(); // Ensure audio can play
      const message = `${mode} mode`;
      voiceControlRef.current.speakText(message, false);
      lastModeAnnouncementRef.current = { mode, timestamp: now };
    }
  }, [mode, voiceOnlyMode]);

  useEffect(() => {
    if (cameraSource === "backend") {
      apiClient.setCameraConfig("webcam").catch(console.error);
    }
  }, []);

  const handleCameraSourceChange = (newSource: CameraSource) => {
    setCameraSource(newSource);
    if (newSource === "backend") {
      apiClient.setCameraConfig("webcam").catch(console.error);
    }
  };

  const handleCameraDeviceChange = async (deviceId: string) => {
    setSelectedCameraId(deviceId);
    const browserCamera = getBrowserCameraService();
    // Always update the device selection, even when camera isn't running
    if (deviceId !== "default") {
      await browserCamera.switchDevice(deviceId);
    }
  };

  const checkCameraStatus = async () => {
    try {
      const status = await apiClient.getCameraStatus();
      setCameraStatus(status);
    } catch (error) {
      console.error("Failed to check camera status:", error);
    }
  };

  const handleCameraToggle = async () => {
    try {
      const newCameraState = !cameraOn;
      const now = Date.now();

      if (cameraOn) {
        if (cameraSource === "browser") {
          const browserCamera = getBrowserCameraService();
          await browserCamera.stop();
        } else {
          await apiClient.stopCamera();
        }
        setCameraOn(false);
      } else {
        if (cameraSource === "browser") {
          // Don't start here - let the mode components handle it with their frame callbacks
          const browserCamera = getBrowserCameraService();
          // Just enumerate devices to ensure we have permissions
          await browserCamera.initialize();
        } else {
          await apiClient.startCamera();
        }
        setCameraOn(true);
      }
      
      if (cameraSource !== "browser") {
        await checkCameraStatus();
      } else {
        const browserCamera = getBrowserCameraService();
        setCameraStatus({
          is_running: browserCamera.isCameraRunning(),
          is_available: true,
        });
      }

      // Audio cue: Only announce if we haven't announced this state recently (within 2 seconds)
      // This prevents duplicate announcements from multiple rapid calls
      if (voiceOnlyMode) {
        const timeSinceLastAnnouncement =
          now - lastCameraAnnouncementRef.current.timestamp;
        const lastAnnouncedState = lastCameraAnnouncementRef.current.state;

        // Only announce if:
        // 1. We haven't announced this state before, OR
        // 2. The last announcement was for a different state, OR
        // 3. It's been more than 2 seconds since the last announcement
        if (
          lastAnnouncedState !== newCameraState ||
          timeSinceLastAnnouncement > 2000
        ) {
          voiceControlRef.current.markUserInteracted(); // Ensure audio can play
          const message = newCameraState ? "Camera is on" : "Camera is off";
          voiceControlRef.current.speakText(message, false);
          lastCameraAnnouncementRef.current = {
            state: newCameraState,
            timestamp: now,
          };
        }
      }
    } catch (error) {
      console.error("Failed to toggle camera:", error);
      alert("Failed to toggle camera. Please check your camera permissions.");
      // Audio cue for error (only in voice-only mode)
      if (voiceOnlyMode) {
        const now = Date.now();
        const timeSinceLastAnnouncement =
          now - lastCameraAnnouncementRef.current.timestamp;
        if (timeSinceLastAnnouncement > 2000) {
          voiceControlRef.current.markUserInteracted();
          voiceControlRef.current.speakText("Failed to toggle camera", false);
          lastCameraAnnouncementRef.current = { state: null, timestamp: now };
        }
      }
    }
  };

  return (
    <div className="w-full h-screen bg-dark-bg flex flex-col font-sans text-dark-text-primary overflow-hidden">
      {/* Header */}
      <header className="flex items-center justify-between px-6 md:px-10 py-5 border-b border-dark-border flex-shrink-0">
        <h1 className="text-3xl font-semibold text-dark-text-primary tracking-logo font-heading">
          autistic<span className="text-2xl align-middle opacity-80">AR</span>
        </h1>

        <TranscriptionBubble
          voiceOnlyMode={voiceOnlyMode}
          transcription={currentTranscription}
        />

        <div className="flex items-center space-x-4 md:space-x-6">
          {/* Voice Only Mode Toggle */}
          <button
            onClick={() => {
              const newMode = !voiceOnlyMode;
              setVoiceOnlyMode(newMode);
              // Mark user interaction for audio playback when enabling voice mode
              if (newMode) {
                // Mark interaction FIRST, then speak
                voiceControlRef.current.markUserInteracted();

                // Speak warm, time-aware welcome message after a short delay
                setTimeout(() => {
                  const welcomeMessage = generateWelcomeMessage({
                    mode,
                    cameraOn,
                  });

                  console.log(
                    "[App] Speaking welcome message:",
                    welcomeMessage
                  );
                  voiceControlRef.current.speakText(welcomeMessage, false);
                }, 500); // Delay to ensure everything is initialized
              } else {
                // When disabling, stop all voice/TTS activity
                voiceControlRef.current.stopListening();
                voiceControlRef.current.stopSpeaking();
              }
            }}
            title={
              voiceOnlyMode
                ? "Disable Voice Only Mode"
                : "Enable Voice Only Mode"
            }
            className={`p-2.5 rounded-xl border-2 transition-all duration-300 ${
              voiceOnlyMode
                ? "bg-brand-gold text-brand-charcoal border-brand-gold"
                : "border-dark-border bg-dark-surface text-dark-text-secondary hover:border-brand-gold hover:text-brand-gold"
            }`}
          >
            {voiceOnlyMode ? (
              <Mic className="w-5 h-5" />
            ) : (
              <MicOff className="w-5 h-5" />
            )}
          </button>

          {/* Mode Selection */}
          <div className="relative">
            <select
              value={mode}
              onChange={(e) => setMode(e.target.value as Mode)}
              className="appearance-none bg-dark-surface border-2 border-dark-border text-dark-text-secondary text-sm rounded-xl px-4 py-2.5 pr-10 focus:outline-none focus:border-brand-gold focus:text-brand-gold transition-all duration-300 cursor-pointer min-w-[180px]"
              title="Select Mode"
            >
              <option value="Activity Guide">🎯 Activity Guide</option>
              <option value="Scene Description">👁️ Scene Description</option>
              <option value="Navigation">🧭 Navigation</option>
              <option value="Reading">📖 Reading Assistant</option>
              <option value="Color">🎨 Color Recognition</option>
              <option value="People Counter">👥 People Counter</option>
              <option value="Emotion Recognition">😊 Emotion Recognition</option>
              <option value="Social Cues">💬 Social Cues</option>
              <option value="Sensory Overload">🌊 Sensory Overload</option>
              <option value="Communication Helper">💡 Communication</option>
              <option value="Routine Assistant">📋 Routine Assistant</option>
              <option value="Body Language">🦴 Body Language</option>
              <option value="AI Assistant">🤖 AI Assistant</option>
            </select>
            <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-3 text-dark-text-secondary">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </div>
          </div>

          {/* Camera Settings */}
          <button
            onClick={() => setShowSettings(true)}
            title="Camera Settings"
            className="p-2.5 rounded-xl border-2 border-dark-border bg-dark-surface text-dark-text-secondary hover:border-brand-gold hover:text-brand-gold transition-all duration-300"
          >
            <Settings className="w-5 h-5" />
          </button>

          {/* Camera Source Dropdown */}
          <div className="relative">
            <select
              value={cameraSource}
              onChange={(e) => handleCameraSourceChange(e.target.value as CameraSource)}
              className="appearance-none bg-dark-surface border-2 border-dark-border text-dark-text-secondary text-sm rounded-xl px-3 py-2.5 pr-8 focus:outline-none focus:border-brand-gold focus:text-brand-gold transition-all duration-300 cursor-pointer"
              title="Camera Source"
            >
              <option value="browser">Browser Camera</option>
              <option value="backend">Backend Webcam</option>
              <option value="esp32">ESP32 Camera</option>
            </select>
            <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-2 text-dark-text-secondary">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </div>
          </div>

          {/* Camera Device Dropdown (only show for browser camera) */}
          {cameraSource === "browser" && availableCameras.length > 0 && (
            <div className="relative">
              <select
                value={selectedCameraId}
                onChange={(e) => handleCameraDeviceChange(e.target.value)}
                className="appearance-none bg-dark-surface border-2 border-dark-border text-dark-text-secondary text-sm rounded-xl px-3 py-2.5 pr-8 focus:outline-none focus:border-brand-gold focus:text-brand-gold transition-all duration-300 cursor-pointer max-w-[150px]"
                title="Select Camera Device"
              >
                <option value="default">Default Camera</option>
                {availableCameras.map((device) => (
                  <option key={device.deviceId} value={device.deviceId}>
                    {device.label || `Camera ${device.deviceId.slice(0, 8)}`}
                  </option>
                ))}
              </select>
              <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-2 text-dark-text-secondary">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </div>
            </div>
          )}

          {/* Camera Toggle */}
          <button
            ref={cameraButtonRef}
            onClick={handleCameraToggle}
            title={cameraOn ? "Turn Camera Off" : "Turn Camera On"}
            className={`p-2.5 rounded-xl border-2 transition-all duration-300 ${
              cameraOn
                ? "border-dark-border text-dark-text-secondary hover:border-brand-gold hover:text-brand-gold"
                : "border-dark-border bg-dark-surface text-dark-text-secondary"
            }`}
          >
            {cameraOn ? (
              <Camera className="w-5 h-5" />
            ) : (
              <CameraOff className="w-5 h-5" />
            )}
          </button>

          {/* Status Indicator */}
          <div className="flex items-center space-x-2">
            <div
              className={`w-2.5 h-2.5 rounded-full ${
                cameraStatus.is_running
                  ? "bg-green-400 shadow-[0_0_8px_rgba(74,222,128,0.5)]"
                  : "bg-gray-500"
              }`}
            ></div>
            <span className="font-medium text-dark-text-secondary hidden sm:block text-sm">
              {cameraStatus.is_running ? "System Active" : "System Inactive"}
            </span>
          </div>

          {/* Time */}
          <div className="text-dark-text-primary font-medium text-base">
            {currentTime.toLocaleTimeString([], {
              hour: "2-digit",
              minute: "2-digit",
            })}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 overflow-hidden">
        {mode === "Activity Guide" && (
          <ActivityGuide 
            cameraOn={cameraOn} 
            voiceOnlyMode={voiceOnlyMode}
            cameraSource={cameraSource}
            onStatsUpdate={updateSessionStats}
          />
        )}
        {mode === "Scene Description" && (
          <SceneDescription 
            cameraOn={cameraOn} 
            voiceOnlyMode={voiceOnlyMode}
            cameraSource={cameraSource}
            onStatsUpdate={updateSessionStats}
          />
        )}
        {mode === "Navigation" && (
          <NavigationMode 
            cameraOn={cameraOn} 
            voiceOnlyMode={voiceOnlyMode}
            cameraSource={cameraSource}
            onStatsUpdate={updateSessionStats}
          />
        )}
        {mode === "Reading" && (
          <ReadingAssistant 
            cameraOn={cameraOn} 
            voiceOnlyMode={voiceOnlyMode}
            cameraSource={cameraSource}
            onStatsUpdate={updateSessionStats}
          />
        )}
        {mode === "Color" && (
          <ColorRecognition 
            cameraOn={cameraOn} 
            voiceOnlyMode={voiceOnlyMode}
            cameraSource={cameraSource}
            onStatsUpdate={updateSessionStats}
          />
        )}
        {mode === "People Counter" && (
          <PeopleCounter 
            cameraOn={cameraOn} 
            voiceOnlyMode={voiceOnlyMode}
            cameraSource={cameraSource}
            onStatsUpdate={updateSessionStats}
          />
        )}
        {mode === "Emotion Recognition" && (
          <EmotionRecognition 
            cameraOn={cameraOn} 
            voiceOnlyMode={voiceOnlyMode}
            cameraSource={cameraSource}
            onStatsUpdate={updateSessionStats}
          />
        )}
        {mode === "Social Cues" && (
          <SocialCues 
            cameraOn={cameraOn} 
            voiceOnlyMode={voiceOnlyMode}
            cameraSource={cameraSource}
            onStatsUpdate={updateSessionStats}
          />
        )}
        {mode === "Sensory Overload" && (
          <SensoryOverload 
            cameraOn={cameraOn} 
            voiceOnlyMode={voiceOnlyMode}
            cameraSource={cameraSource}
            onStatsUpdate={updateSessionStats}
          />
        )}
        {mode === "Communication Helper" && (
          <CommunicationHelper 
            cameraOn={cameraOn} 
            voiceOnlyMode={voiceOnlyMode}
            cameraSource={cameraSource}
            onStatsUpdate={updateSessionStats}
          />
        )}
        {mode === "Routine Assistant" && (
          <RoutineAssistant 
            cameraOn={cameraOn} 
            voiceOnlyMode={voiceOnlyMode}
            cameraSource={cameraSource}
            onStatsUpdate={updateSessionStats}
          />
        )}
        {mode === "Body Language" && (
          <BodyLanguage 
            cameraOn={cameraOn} 
            voiceOnlyMode={voiceOnlyMode}
            cameraSource={cameraSource}
            onStatsUpdate={updateSessionStats}
          />
        )}
        {mode === "AI Assistant" && (
          <AIAssistant 
            cameraOn={cameraOn} 
            voiceOnlyMode={voiceOnlyMode}
            cameraSource={cameraSource}
            onStatsUpdate={updateSessionStats}
            mode={mode}
          />
        )}
      </main>

      {/* Live Stats Bar */}
      <div className="bg-dark-surface border-t border-dark-border px-6 py-3">
        <div className="flex items-center justify-between text-xs text-dark-text-secondary">
          {/* Session Stats */}
          <div className="flex items-center space-x-6">
            <div className="flex items-center space-x-2">
              <span className="text-dark-text-secondary">Session:</span>
              <span className="text-dark-text-primary font-medium">
                {Math.floor((Date.now() - (sessionStartTime || Date.now())) / 1000)}s
              </span>
            </div>
            <div className="flex items-center space-x-2">
              <span className="text-dark-text-secondary">Objects Found:</span>
              <span className="text-brand-gold font-medium">{sessionStats.objectsFound}</span>
            </div>
            <div className="flex items-center space-x-2">
              <span className="text-dark-text-secondary">Text Read:</span>
              <span className="text-brand-gold font-medium">{sessionStats.textRead}</span>
            </div>
            <div className="flex items-center space-x-2">
              <span className="text-dark-text-secondary">People Detected:</span>
              <span className="text-brand-gold font-medium">{sessionStats.peopleDetected}</span>
            </div>
            <div className="flex items-center space-x-2">
              <span className="text-dark-text-secondary">Incidents:</span>
              <span className="text-brand-gold font-medium">{sessionStats.incidents}</span>
            </div>
          </div>

          {/* System Health */}
          <div className="flex items-center space-x-6">
            <div className="flex items-center space-x-2">
              <span className="text-dark-text-secondary">FPS:</span>
              <span className={`font-medium ${systemHealth.fps > 20 ? 'text-green-400' : systemHealth.fps > 10 ? 'text-yellow-400' : 'text-red-400'}`}>
                {systemHealth.fps}
              </span>
            </div>
            <div className="flex items-center space-x-2">
              <span className="text-dark-text-secondary">Latency:</span>
              <span className={`font-medium ${systemHealth.latency < 100 ? 'text-green-400' : systemHealth.latency < 200 ? 'text-yellow-400' : 'text-red-400'}`}>
                {systemHealth.latency}ms
              </span>
            </div>
            <div className="flex items-center space-x-2">
              <span className="text-dark-text-secondary">Model:</span>
              <span className={`font-medium ${systemHealth.modelLoaded ? 'text-green-400' : 'text-red-400'}`}>
                {systemHealth.modelLoaded ? '✓ Ready' : '✗ Loading'}
              </span>
            </div>
            <div className="flex items-center space-x-2">
              <span className="text-dark-text-secondary">Privacy:</span>
              <span className="text-green-400 font-medium">🔒 Local</span>
            </div>
          </div>

          {/* Keyboard Shortcuts */}
          <div className="flex items-center space-x-4">
            <span className="text-dark-text-secondary">Shortcuts:</span>
            <div className="flex items-center space-x-2">
              <kbd className="px-2 py-1 bg-dark-bg border border-dark-border rounded text-dark-text-primary">1</kbd>
              <span className="text-dark-text-secondary">Activity</span>
            </div>
            <div className="flex items-center space-x-2">
              <kbd className="px-2 py-1 bg-dark-bg border border-dark-border rounded text-dark-text-primary">2</kbd>
              <span className="text-dark-text-secondary">Scene</span>
            </div>
            <div className="flex items-center space-x-2">
              <kbd className="px-2 py-1 bg-dark-bg border border-dark-border rounded text-dark-text-primary">3</kbd>
              <span className="text-dark-text-secondary">Nav</span>
            </div>
            <div className="flex items-center space-x-2">
              <kbd className="px-2 py-1 bg-dark-bg border border-dark-border rounded text-dark-text-primary">4</kbd>
              <span className="text-dark-text-secondary">Read</span>
            </div>
            <div className="flex items-center space-x-2">
              <kbd className="px-2 py-1 bg-dark-bg border border-dark-border rounded text-dark-text-primary">5</kbd>
              <span className="text-dark-text-secondary">Color</span>
            </div>
            <div className="flex items-center space-x-2">
              <kbd className="px-2 py-1 bg-dark-bg border border-dark-border rounded text-dark-text-primary">6</kbd>
              <span className="text-dark-text-secondary">People</span>
            </div>
            <div className="flex items-center space-x-2">
              <kbd className="px-2 py-1 bg-dark-bg border border-dark-border rounded text-dark-text-primary">7</kbd>
              <span className="text-dark-text-secondary">Emotion</span>
            </div>
            <div className="flex items-center space-x-2">
              <kbd className="px-2 py-1 bg-dark-bg border border-dark-border rounded text-dark-text-primary">0</kbd>
              <span className="text-dark-text-secondary">Comm</span>
            </div>
          </div>
        </div>
      </div>

      {/* Settings Modal */}
      <HardwareSettings
        isOpen={showSettings}
        onClose={() => setShowSettings(false)}
        cameraSource={cameraSource}
        onCameraSourceChange={handleCameraSourceChange}
      />
    </div>
  );
}

export default App;
