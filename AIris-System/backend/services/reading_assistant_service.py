"""
Reading Assistant Service - OCR text recognition for reading signs, documents, etc.
"""

import cv2
import numpy as np
from typing import Dict, List, Optional
import asyncio
from collections import deque
import time

class ReadingAssistantService:
    def __init__(self, model_service):
        self.model_service = model_service
        self.is_active = False
        self.last_text = ""
        self.last_detection_time = 0
        self.text_history = deque(maxlen=10)
        self.ocr_processor = None
        
    async def initialize(self):
        """Initialize OCR processor"""
        try:
            # Try to import easyocr
            import easyocr
            self.ocr_processor = easyocr.Reader(['en'], gpu=False)
            print("✓ Reading Assistant initialized with EasyOCR")
        except ImportError:
            print("⚠️ EasyOCR not available. Reading Assistant will use basic text detection.")
            self.ocr_processor = None
    
    async def start_reading(self):
        """Start reading mode"""
        self.is_active = True
        if self.ocr_processor is None:
            await self.initialize()
        return {
            "status": "success",
            "message": "Reading mode started. Point camera at text to read it."
        }
    
    async def stop_reading(self):
        """Stop reading mode"""
        self.is_active = False
        return {
            "status": "success",
            "message": "Reading mode stopped."
        }
    
    async def process_frame(self, frame: np.ndarray) -> Dict:
        """Process a frame to detect and read text"""
        if not self.is_active:
            return {
                "text": "",
                "confidence": 0.0,
                "regions": [],
                "message": "Reading mode is not active"
            }
        
        # Preprocess frame for better OCR
        processed_frame = self._preprocess_frame(frame)
        
        # Perform OCR
        text, confidence, regions = await self._perform_ocr(processed_frame)
        
        # Check if text has changed
        text_changed = text != self.last_text
        self.last_text = text
        
        if text:
            self.text_history.append({
                "text": text,
                "timestamp": time.time(),
                "confidence": confidence
            })
        
        # Generate message
        if text:
            if text_changed:
                message = f"Text detected: {text}"
            else:
                message = f"Still reading: {text}"
        else:
            message = "No text detected. Try pointing camera at text."
        
        # Annotate frame with detected text regions
        annotated_frame = self._annotate_frame(frame, regions)
        
        return {
            "text": text,
            "confidence": confidence,
            "regions": regions,
            "message": message,
            "text_changed": text_changed,
            "annotated_frame": annotated_frame
        }
    
    def _preprocess_frame(self, frame: np.ndarray) -> np.ndarray:
        """Preprocess frame for better OCR results"""
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Apply denoising
        denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
        
        # Adaptive thresholding
        thresh = cv2.adaptiveThreshold(
            denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 11, 2
        )
        
        return thresh
    
    async def _perform_ocr(self, frame: np.ndarray) -> tuple:
        """Perform OCR on the frame"""
        if self.ocr_processor is None:
            # Fallback: basic text detection using contours
            return await self._basic_text_detection(frame)
        
        try:
            # Run OCR
            results = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.ocr_processor.readtext(frame)
            )
            
            if not results:
                return "", 0.0, []
            
            # Combine all detected text
            texts = []
            confidences = []
            regions = []
            
            for bbox, text, conf in results:
                if conf > 0.3:  # Confidence threshold
                    texts.append(text)
                    confidences.append(conf)
                    regions.append({
                        "bbox": bbox,
                        "text": text,
                        "confidence": conf
                    })
            
            combined_text = " ".join(texts)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            return combined_text, avg_confidence, regions
            
        except Exception as e:
            print(f"OCR error: {e}")
            return "", 0.0, []
    
    async def _basic_text_detection(self, frame: np.ndarray) -> tuple:
        """Basic text detection using contours (fallback when EasyOCR not available)"""
        try:
            # Find contours that might be text
            contours, _ = cv2.findContours(
                frame, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )
            
            text_regions = []
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                # Filter by size (text-like aspect ratio)
                if w > 20 and h > 10 and w < frame.shape[1] * 0.8:
                    aspect_ratio = w / h
                    if 0.1 < aspect_ratio < 10:
                        text_regions.append({
                            "bbox": [[x, y], [x+w, y], [x+w, y+h], [x, y+h]],
                            "text": "[Text detected - install EasyOCR for reading]",
                            "confidence": 0.5
                        })
            
            if text_regions:
                return "[Text regions detected]", 0.5, text_regions[:5]
            
            return "", 0.0, []
            
        except Exception as e:
            print(f"Basic text detection error: {e}")
            return "", 0.0, []
    
    def _annotate_frame(self, frame: np.ndarray, regions: List[Dict]) -> np.ndarray:
        """Annotate frame with detected text regions"""
        annotated = frame.copy()
        
        for region in regions:
            bbox = region["bbox"]
            # Convert bbox to numpy array
            pts = np.array(bbox, dtype=np.int32)
            # Draw polygon
            cv2.polylines(annotated, [pts], True, (0, 255, 0), 2)
            
            # Add text label
            text = region["text"][:20] + "..." if len(region["text"]) > 20 else region["text"]
            cv2.putText(annotated, text, (pts[0][0], pts[0][1] - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        return annotated
    
    def get_status(self) -> Dict:
        """Get reading assistant status"""
        return {
            "is_active": self.is_active,
            "last_text": self.last_text,
            "text_count": len(self.text_history),
            "ocr_available": self.ocr_processor is not None
        }
    
    def get_text_history(self) -> List[Dict]:
        """Get history of detected text"""
        return list(self.text_history)
