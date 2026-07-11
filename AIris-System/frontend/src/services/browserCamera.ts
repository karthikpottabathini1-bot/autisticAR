/**
 * Browser Camera Service - Handles camera capture using getUserMedia
 */

export type BrowserCameraStatus = {
  isRunning: boolean;
  availableDevices: MediaDeviceInfo[];
  selectedDeviceId: string | null;
};

class BrowserCameraService {
  private stream: MediaStream | null = null;
  private videoElement: HTMLVideoElement | null = null;
  private canvas: HTMLCanvasElement | null = null;
  private canvasCtx: CanvasRenderingContext2D | null = null;
  private isRunning = false;
  private availableDevices: MediaDeviceInfo[] = [];
  private selectedDeviceId: string | null = null;
  private frameCallback: ((frameBase64: string) => void) | null = null;
  private frameInterval: number | null = null;

  async initialize(): Promise<void> {
    this.canvas = document.createElement('canvas');
    this.canvasCtx = this.canvas.getContext('2d');
    await this.enumerateDevices();
  }

  async enumerateDevices(): Promise<MediaDeviceInfo[]> {
    try {
      const devices = await navigator.mediaDevices.enumerateDevices();
      this.availableDevices = devices.filter(device => device.kind === 'videoinput');
      return this.availableDevices;
    } catch (error) {
      console.error('[BrowserCamera] Failed to enumerate devices:', error);
      return [];
    }
  }

  async start(deviceId?: string, onFrame?: (frameBase64: string) => void): Promise<boolean> {
    if (this.isRunning) {
      // Update callback even if already running (for mode switching)
      this.frameCallback = onFrame || null;
      return true;
    }

    try {
      const effectiveDeviceId = deviceId || this.selectedDeviceId;
      const constraints: MediaStreamConstraints = {
        video: effectiveDeviceId
          ? { deviceId: { exact: effectiveDeviceId }, width: { ideal: 640 }, height: { ideal: 480 } }
          : { width: { ideal: 640 }, height: { ideal: 480 } },
        audio: false,
      };

      this.stream = await navigator.mediaDevices.getUserMedia(constraints);
      this.selectedDeviceId = effectiveDeviceId || null;
      this.frameCallback = onFrame || null;

      // Create hidden video element
      this.videoElement = document.createElement('video');
      this.videoElement.srcObject = this.stream;
      this.videoElement.autoplay = true;
      this.videoElement.playsInline = true;
      this.videoElement.muted = true;
      
      // Wait for video to be ready
      await new Promise<void>((resolve, reject) => {
        if (!this.videoElement) {
          reject(new Error('Video element not created'));
          return;
        }
        this.videoElement.onloadedmetadata = () => {
          if (this.videoElement) {
            this.videoElement.play();
            resolve();
          } else {
            reject(new Error('Video element not created'));
          }
        };
        this.videoElement.onerror = () => reject(new Error('Video element error'));
      });

      // Set canvas size to match video
      if (this.videoElement && this.canvas) {
        this.canvas.width = this.videoElement.videoWidth || 640;
        this.canvas.height = this.videoElement.videoHeight || 480;
      }

      this.isRunning = true;

      // Start frame capture loop
      this.startFrameCapture();

      console.log('[BrowserCamera] Started successfully');
      return true;
    } catch (error) {
      console.error('[BrowserCamera] Failed to start:', error);
      this.cleanup();
      return false;
    }
  }

  private startFrameCapture(): void {
    if (this.frameInterval) {
      clearInterval(this.frameInterval);
    }

    // Capture frames at ~10 FPS
    this.frameInterval = window.setInterval(() => {
      if (!this.isRunning || !this.videoElement || !this.canvas || !this.canvasCtx) {
        return;
      }

      try {
        // Draw current video frame to canvas
        this.canvasCtx.drawImage(this.videoElement, 0, 0, this.canvas.width, this.canvas.height);
        
        // Convert to base64 JPEG at high quality for better detection
        const dataUrl = this.canvas.toDataURL('image/jpeg', 0.95);
        const base64Frame = dataUrl.split(',')[1];

        // Call the frame callback if provided
        if (this.frameCallback) {
          this.frameCallback(base64Frame);
        }
      } catch (error) {
        console.error('[BrowserCamera] Frame capture error:', error);
      }
    }, 100);
  }

  async stop(): Promise<void> {
    if (!this.isRunning) {
      return;
    }

    this.isRunning = false;
    this.frameCallback = null;

    if (this.frameInterval) {
      clearInterval(this.frameInterval);
      this.frameInterval = null;
    }

    this.cleanup();
    console.log('[BrowserCamera] Stopped');
  }

  private cleanup(): void {
    if (this.stream) {
      this.stream.getTracks().forEach(track => track.stop());
      this.stream = null;
    }

    if (this.videoElement) {
      this.videoElement.srcObject = null;
      this.videoElement = null;
    }
  }

  getStatus(): BrowserCameraStatus {
    return {
      isRunning: this.isRunning,
      availableDevices: this.availableDevices,
      selectedDeviceId: this.selectedDeviceId,
    };
  }

  getAvailableDevices(): MediaDeviceInfo[] {
    return this.availableDevices;
  }

  getSelectedDeviceId(): string | null {
    return this.selectedDeviceId;
  }

  async switchDevice(deviceId: string): Promise<boolean> {
    const wasRunning = this.isRunning;
    this.selectedDeviceId = deviceId; // Always store, even if not running
    
    if (wasRunning) {
      await this.stop();
      return await this.start(deviceId, this.frameCallback || undefined);
    }
    
    return true;
  }

  isCameraRunning(): boolean {
    return this.isRunning;
  }
}

// Singleton instance
let browserCameraInstance: BrowserCameraService | null = null;

export function getBrowserCameraService(): BrowserCameraService {
  if (!browserCameraInstance) {
    browserCameraInstance = new BrowserCameraService();
  }
  return browserCameraInstance;
}
