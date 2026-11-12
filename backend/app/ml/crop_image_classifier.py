import os
import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path
from PIL import Image

logger = logging.getLogger(__name__)

from .disease_config import SUPPORTED_CROPS

class CropImageClassifier:
    """
    Dedicated Crop Identification service using the locally trained PyTorch EfficientNetV2_S model.
    """
    def __init__(self):
        self.model_name = "EfficientNet-B0"
        self.model = None
        self.class_names = []
        self.min_crop_confidence = 0.65
        self.min_confidence_margin = 0.15
        self.is_loaded = False
        
        self.transform = None
        self.device = None
        
        self._load_model()

    def _load_model(self):
        try:
            base_dir = Path(__file__).resolve().parent.parent.parent
            model_path = base_dir / "ml" / "models" / "crop_classifier_best.pth"
            classes_path = base_dir / "ml" / "models" / "crop_class_names.json"
            
            if not model_path.exists() or not classes_path.exists():
                logger.error(f"[CROP MODEL] Missing model files at {model_path} or {classes_path}")
                return
                
            logger.info(f"[CROP MODEL] Loading {self.model_name} classifier (PyTorch)...")
            
            import torch
            import torch.nn as nn
            from torchvision import models, transforms
            
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            
            with open(classes_path, 'r') as f:
                classes_data = json.load(f)
                if isinstance(classes_data, dict):
                    self.class_names = [classes_data[str(i)] for i in range(len(classes_data))]
                else:
                    self.class_names = classes_data
                    
            logger.info(f"[CROP MODEL] Classes: {self.class_names} ({len(self.class_names)})")
                
            self.model = models.efficientnet_b0(weights=None)
            num_ftrs = self.model.classifier[1].in_features
            self.model.classifier[1] = nn.Linear(num_ftrs, len(self.class_names))
            
            self.model.load_state_dict(torch.load(model_path, map_location=self.device, weights_only=True))
            self.model.to(self.device)
            self.model.eval()
            
            self.transform = transforms.Compose([
                transforms.Resize((256, 256)),
                transforms.CenterCrop((224, 224)),
                transforms.ToTensor(),
                transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
            ])
                
            logger.info(f"[CROP MODEL] Loaded successfully on {self.device}")
            self.is_loaded = True
        except Exception as e:
            logger.error(f"[CROP MODEL] Failed to load model: {e}")
            self.is_loaded = False

    def _get_crop_key(self, crop_name: str) -> Optional[str]:
        if not crop_name:
            return None
        crop_name_lower = crop_name.lower().strip()
        for key, crop_data in SUPPORTED_CROPS.items():
            if crop_name_lower == key or crop_name_lower in [a.lower() for a in crop_data.get("aliases", [])]:
                return key
            if crop_name_lower == crop_data.get("display_name", "").lower():
                return key
        return None

    def predict(self, image: Image.Image) -> Dict[str, Any]:
        if not self.is_loaded:
            logger.error("[CropClassifier] No valid crop model loaded.")
            return {
                "crop": "Unavailable",
                "crop_key": None,
                "confidence": 0.0,
                "top2_crop": "None",
                "top2_confidence": 0.0,
                "confidence_margin": 0.0,
                "is_valid_crop": False,
                "model": self.model_name,
                "status": "model_unavailable",
                "message": "Crop model is unavailable."
            }
            
        try:
            import torch
            
            img = image.convert('RGB')
            tensor = self.transform(img).unsqueeze(0).to(self.device)
            
            with torch.no_grad():
                outputs = self.model(tensor)
                probs = torch.nn.functional.softmax(outputs[0], dim=0)
                topk = torch.topk(probs, min(5, len(self.class_names)))
            
            top1_idx = topk.indices[0].item()
            top1_conf = topk.values[0].item()
            top1_class = self.class_names[top1_idx]
            
            top2_idx = topk.indices[1].item() if len(topk.indices) > 1 else top1_idx
            top2_conf = topk.values[1].item() if len(topk.values) > 1 else 0.0
            top2_class = self.class_names[top2_idx] if len(topk.indices) > 1 else "None"
            
            margin = top1_conf - top2_conf
            
            logger.info(f"[CROP MODEL] Prediction: {top1_class} | Confidence: {top1_conf:.4f} | Top-2: {top2_class} ({top2_conf:.4f}) | Margin: {margin:.4f}")
            
            crop_key = self._get_crop_key(top1_class)
            is_confident = (top1_conf >= self.min_crop_confidence)
            is_distinct = (margin >= self.min_confidence_margin)
            is_valid = is_confident and is_distinct and (crop_key is not None)
            
            if is_valid:
                display_name = SUPPORTED_CROPS[crop_key]["display_name"] if crop_key in SUPPORTED_CROPS else top1_class.title()
                return {
                    "crop": display_name,
                    "crop_key": crop_key,
                    "confidence": top1_conf,
                    "top2_crop": top2_class,
                    "top2_confidence": top2_conf,
                    "confidence_margin": margin,
                    "is_valid_crop": True,
                    "model": self.model_name,
                    "status": "high_confidence",
                    "message": "Crop identified successfully."
                }
            else:
                return {
                    "crop": "Unknown",
                    "crop_key": None,
                    "confidence": top1_conf,
                    "top2_crop": top2_class,
                    "top2_confidence": top2_conf,
                    "confidence_margin": margin,
                    "is_valid_crop": False,
                    "model": self.model_name,
                    "status": "low_confidence",
                    "message": "Crop could not be identified confidently."
                }
                
        except Exception as e:
            logger.error(f"[CropClassifier] Inference failed: {e}")
            return {
                "crop": "Unknown",
                "crop_key": None,
                "confidence": 0.0,
                "top2_crop": "None",
                "top2_confidence": 0.0,
                "confidence_margin": 0.0,
                "is_valid_crop": False,
                "model": self.model_name,
                "status": "error",
                "message": "Crop model failed to process."
            }
