import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import cv2
import numpy as np
from PIL import Image

try:
    from ultralytics import YOLO
    ULTRALYTICS_AVAILABLE = True
except ImportError:
    ULTRALYTICS_AVAILABLE = False

from .leaf_validator import LeafValidator
from .disease_config import YOLO_DISEASE_MODEL_PATH, YOLO_CONFIDENCE_THRESHOLD, SUPPORTED_CROPS

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
MODELS_DIR = BASE_DIR / "models"
ML_DIR = BASE_DIR / "ml"
TREATMENT_DB_PATH = ML_DIR / "treatment_recommendations.json"

class YOLODiseaseClassifier:
    def __init__(self, device: str = "cpu", confidence_threshold: Optional[float] = None):
        self.device = device
        self.confidence_threshold = confidence_threshold if confidence_threshold is not None else YOLO_CONFIDENCE_THRESHOLD
        self.model = None
        self.class_names: List[str] = []
        self.treatment_db: Dict[str, Any] = {}
        self.leaf_validator = LeafValidator(device=self.device)

        self._load_treatment_db()
        self._load_or_init_model()

    def _is_basic_valid_image(self, image: Image.Image) -> bool:
        try:
            if image.width < 10 or image.height < 10:
                return False
            # Check if image is completely uniform (e.g. all black or all white)
            extrema = image.convert("L").getextrema()
            if extrema[0] == extrema[1]:
                return False
            return True
        except:
            return False

    def _normalize_disease_name(self, name: str) -> str:
        """Normalizes a disease name for robust lookup."""
        if not name:
            return ""
        import re
        normalized = name.lower()
        normalized = normalized.replace("-", " ").replace("_", " ")
        normalized = re.sub(r'[^a-z0-9 ]', '', normalized)
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        return normalized

    def _load_treatment_db(self):
        if TREATMENT_DB_PATH.exists():
            try:
                with open(TREATMENT_DB_PATH, "r", encoding="utf-8") as f:
                    raw_db = json.load(f)
                    
                # Normalize keys
                self.treatment_db = {}
                for key, val in raw_db.items():
                    norm_key = self._normalize_disease_name(key)
                    self.treatment_db[norm_key] = val
                    
                logger.info(f"[YOLODiseaseClassifier] Loaded treatment database with {len(self.treatment_db)} disease classes.")
            except Exception as e:
                logger.error(f"[YOLODiseaseClassifier] Failed to load treatment DB: {e}")
                self.treatment_db = {}
        else:
            logger.warning(f"[YOLODiseaseClassifier] Treatment DB not found at {TREATMENT_DB_PATH}")

    def _load_or_init_model(self):
        if not ULTRALYTICS_AVAILABLE:
            logger.error("[YOLODiseaseClassifier] Ultralytics is not installed. YOLO model cannot be loaded.")
            return

        model_path = Path(YOLO_DISEASE_MODEL_PATH)
        if not model_path.is_absolute():
            # BASE_DIR is backend/, so BASE_DIR.parent is Farm-Assist-main/
            model_path = BASE_DIR.parent / YOLO_DISEASE_MODEL_PATH

        if model_path.exists():
            try:
                self.model = YOLO(str(model_path))
                self.class_names = list(self.model.names.values())
                logger.info(f"[YOLODiseaseClassifier] MODEL LOADED: {model_path} with {len(self.class_names)} classes.")
            except Exception as e:
                logger.error(f"[YOLODiseaseClassifier] Failed to load YOLO model: {e}")
                raise ValueError(f"YOLO model failed to load: {e}")
        else:
            error_msg = f"YOLO model not found at path: {model_path}. Please place the YOLO .pt file at this location."
            logger.error(f"[YOLODiseaseClassifier] {error_msg}")
            raise ValueError(error_msg)

    def preprocess(self, image: Image.Image) -> Image.Image:
        # ultralytics YOLO handles preprocessing natively, but we can do basic validation
        return image

    def _get_crop_key(self, crop_name: str) -> Optional[str]:
        if not crop_name:
            return None
        crop_name_lower = crop_name.lower().strip()
        for key, crop_data in SUPPORTED_CROPS.items():
            if crop_name_lower == key or crop_name_lower in [a.lower() for a in crop_data.get("aliases", [])]:
                return key
            # Also check display name
            if crop_name_lower == crop_data.get("display_name", "").lower():
                return key
        return None


    def predict(self, image: Image.Image, filename: str = "unknown.jpg", debug: bool = False) -> Dict[str, Any]:
        if self.model is None:
            return {"success": False, "status": "error", "reason": "model_not_loaded"}

        # Basic Validation
        if not self._is_basic_valid_image(image):
            return {
                "success": False,
                "status": "error",
                "reason": "invalid_image",
                "message": "The uploaded image is invalid or completely uniform (e.g., completely black). Please upload a valid image."
            }

        # 1. Image Quality / Leaf Validation (ADVISORY)
        is_leaf_advisory = True
        try:
            val_result = self.leaf_validator.validate_leaf(image)
            is_leaf_advisory = val_result.get("is_leaf", True)
            if not is_leaf_advisory:
                logger.info("[YOLODiseaseClassifier] OpenCV/MobileNet suggests this is NOT a leaf, but proceeding to YOLO to be sure.")
        except Exception as e:
            logger.warning(f"[YOLODiseaseClassifier] Leaf validation failed: {e}")

        # 2. YOLO Inference
        try:
            logger.info(f"[YOLODiseaseClassifier] YOLO INFERENCE STARTED for {filename}")
            results = self.model(image, verbose=False, conf=0.15)
            logger.info(f"[YOLODiseaseClassifier] YOLO INFERENCE COMPLETED for {filename}")
            if not results or not len(results):
                return {"success": False, "status": "error", "reason": "inference_failed"}
            
            result = results[0]
            bbox = None
            
            if debug:
                logger.info(f"[DEBUG DIAGNOSIS] Image: {filename} | Dimensions: {image.width}x{image.height}")
                logger.info(f"[DEBUG DIAGNOSIS] Model loaded: {self.model.ckpt_path if hasattr(self.model, 'ckpt_path') else 'YOLOv8'} with {len(self.class_names)} classes.")
                
            if result.probs is not None:
                # YOLO Classification model
                top_prob = int(result.probs.top1)
                confidence = float(result.probs.top1conf)
                predicted_class = self.class_names[top_prob]
                model_name = "YOLO11 Classification"
                
                # Extract top-5
                top5_indices = result.probs.top5
                top5_confs = [float(c) for c in result.probs.top5conf]
                top5_classes = [self.class_names[i] for i in top5_indices]
                top5_preds = [
                    {"disease": self.class_names[i].replace("_", " ").title(), "confidence": round(float(c), 4), "raw_class": self.class_names[i]}
                    for i, c in zip(top5_indices, top5_confs)
                ]
                
                if debug:
                    logger.info(f"[DEBUG DIAGNOSIS] Detections count: 1 (Classification)")
                    logger.info(f"[DEBUG DIAGNOSIS] Class: {predicted_class} | Confidence: {confidence:.4f} | Top5: {top5_preds}")
            elif hasattr(result, "boxes") and result.boxes is not None and len(result.boxes) > 0:
                # Object detection model
                boxes = result.boxes
                model_name = "YOLO11 Detection"
                top5_preds = []
                
                if debug:
                    logger.info(f"[DEBUG DIAGNOSIS] Detections count: {len(boxes)}")
                    for i in range(len(boxes)):
                        box = boxes[i]
                        c = float(box.conf[0])
                        cls = int(box.cls[0])
                        cls_name = self.class_names[cls]
                        b = box.xyxy[0].tolist()
                        logger.info(f"[DEBUG DIAGNOSIS] Class: {cls_name} | Confidence: {c:.4f} | BBox: {[round(x, 2) for x in b]}")
                        
                best_box_idx = boxes.conf.argmax()
                confidence = float(boxes.conf[best_box_idx])
                cls_idx = int(boxes.cls[best_box_idx])
                predicted_class = self.class_names[cls_idx]
                bbox = boxes.xyxy[best_box_idx].tolist()
            else:
                # No predictions. If advisory says it's a leaf, assume it's healthy.
                model_name = "YOLO11 Classification"
                if is_leaf_advisory:
                    prediction_data = {
                        "disease": "Healthy",
                        "confidence": 0.99,
                        "severity": "None",
                        "model": model_name
                    }
                    management_data = {
                        "available": True,
                        "cause_type": "N/A",
                        "immediate_actions": [],
                        "cultural_management": ["Maintain current crop management practices."],
                        "biological_management": [],
                        "chemical_management": [],
                        "prevention": ["Continue routine monitoring and fertilization."]
                    }
                    return {
                        "success": True,
                        "prediction": prediction_data,
                        "management": management_data,
                        "is_healthy": True,
                        "source": None,
                        "top5": []
                    }
                else:
                    return {
                        "success": True,
                        "prediction": {
                            "disease": "Unknown",
                            "confidence": 0.0,
                            "severity": "None",
                            "model": model_name
                        },
                        "management": {"available": False},
                        "is_healthy": False,
                        "source": None,
                        "top5": []
                    }
                
            logger.info(f"[YOLODiseaseClassifier] PREDICTED CLASS: {predicted_class}")
            logger.info(f"[YOLODiseaseClassifier] CONFIDENCE: {confidence}")

            # Format human-readable disease name
            display_disease = predicted_class.replace("_", " ").title()
            
            # Add treatment info if available
            norm_pred_class = self._normalize_disease_name(predicted_class)
            treatment = self.treatment_db.get(norm_pred_class, None)

            # 5. Build structured response components
            prediction_data = {
                "disease": display_disease,
                "confidence": confidence,
                "severity": "Moderate", # Default, overridden by treatment if available
                "bbox": bbox,
                "model": model_name
            }

            management_data = {
                "available": False
            }
            
            is_healthy = False
            # Check if predicted class is healthy by looking across all supported crops healthy_classes
            for crop_config in SUPPORTED_CROPS.values():
                if any(hc in predicted_class.lower().replace("_", " ") for hc in crop_config.get("healthy_classes", [])):
                    is_healthy = True
                    break
            
            if is_healthy:
                prediction_data["severity"] = "None"
                management_data["available"] = True
                management_data["cause_type"] = "N/A"
                management_data["immediate_actions"] = []
                management_data["cultural_management"] = ["Maintain current crop management practices."]
                management_data["biological_management"] = []
                management_data["chemical_management"] = []
                management_data["prevention"] = ["Continue routine monitoring and fertilization."]
            elif treatment:
                prediction_data["severity"] = treatment.get("severity_guidance", "Moderate")
                management_data = {
                    "available": True,
                    "cause_type": treatment.get("cause_type", "unknown"),
                    "immediate_actions": treatment.get("immediate_actions", []),
                    "cultural_management": treatment.get("cultural_management", []),
                    "biological_management": treatment.get("biological_management", []),
                    "chemical_management": treatment.get("chemical_management", []),
                    "prevention": treatment.get("prevention", [])
                }

            return {
                "success": True,
                "prediction": prediction_data,
                "management": management_data,
                "is_healthy": is_healthy,
                "raw_class": predicted_class,
                "top5": top5_preds if 'top5_preds' in locals() else [],
                "source": treatment.get("source", "Verified Agricultural Knowledge Base") if treatment else None
            }
        except Exception as e:
            logger.error(f"[YOLODiseaseClassifier] YOLO Inference error: {e}")
            return {"success": False, "status": "error", "reason": str(e)}
