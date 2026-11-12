import os
import logging
from typing import Tuple, Dict, Any, Optional
from pathlib import Path
from PIL import Image, ImageStat
import torch
import torch.nn as nn
from torchvision import models, transforms

logger = logging.getLogger(__name__)

class AgriculturalValidator:
    """
    Dedicated Out-of-Domain (OOD) & Agricultural Image Validator.
    Acts as Gate 1 before any crop classification or disease detection.
    """
    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = None
        self.is_loaded = False
        self.classes = ['agricultural', 'non_agricultural']
        self._load_model()
        
        self.transform = transforms.Compose([
            transforms.Resize((256, 256)),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ])

    def _load_model(self):
        try:
            base_dir = Path(__file__).resolve().parent.parent.parent
            model_path = base_dir / "ml" / "models" / "agricultural_validator.pth"
            
            if not model_path.exists():
                logger.warning(f"[AgriculturalValidator] Model file not found at {model_path}. Fallback to heuristic checks.")
                return

            checkpoint = torch.load(model_path, map_location=self.device, weights_only=False)
            
            # Recreate MobileNetV3-Small architecture
            self.model = models.mobilenet_v3_small(weights=None)
            in_features = self.model.classifier[3].in_features
            self.model.classifier[3] = nn.Linear(in_features, 2)
            
            if isinstance(checkpoint, dict) and "model_state_dict" in checkpoint:
                self.model.load_state_dict(checkpoint["model_state_dict"])
                self.classes = checkpoint.get("classes", ['agricultural', 'non_agricultural'])
            else:
                self.model.load_state_dict(checkpoint)
                
            self.model.to(self.device)
            self.model.eval()
            self.is_loaded = True
            logger.info(f"[AgriculturalValidator] Loaded successfully on {self.device}")
        except Exception as e:
            logger.error(f"[AgriculturalValidator] Failed to load model: {e}")
            self.is_loaded = False

    def check_image_quality(self, image: Image.Image) -> Tuple[bool, str]:
        """Check for basic corruptions, blank images, or invalid dimensions."""
        try:
            w, h = image.size
            if w < 50 or h < 50:
                return False, "Image resolution is too low (minimum 50x50 required)."

            # Check for completely blank / solid color images
            img_gray = image.convert("L")
            stat = ImageStat.Stat(img_gray)
            variance = stat.var[0] if stat.var else 0
            if variance < 5.0:
                return False, "Image contains no meaningful visual content (blank or uniform color)."

            return True, "Image quality valid."
        except Exception as e:
            return False, f"Invalid image format: {e}"

    def validate(self, image: Image.Image) -> Dict[str, Any]:
        """
        Validates if an image is a valid agricultural / crop plant image.
        Returns:
            {
                "is_agricultural": bool,
                "confidence": float,
                "label": str, # 'agricultural' or 'non_agricultural'
                "status": str,
                "reason": str
            }
        """
        # 1. Quality Check
        quality_ok, quality_msg = self.check_image_quality(image)
        if not quality_ok:
            return {
                "is_agricultural": False,
                "confidence": 0.0,
                "label": "invalid_quality",
                "status": "invalid_image",
                "reason": quality_msg
            }

        # 2. Model Prediction
        if not self.is_loaded or self.model is None:
            # If validator model is missing, pass through to crop classifier gate
            return {
                "is_agricultural": True,
                "confidence": 1.0,
                "label": "agricultural",
                "status": "bypass",
                "reason": "Validator model unavailable; delegating to crop classifier gate."
            }

        try:
            img_rgb = image.convert("RGB")
            tensor = self.transform(img_rgb).unsqueeze(0).to(self.device)
            
            with torch.no_grad():
                outputs = self.model(tensor)
                probs = torch.softmax(outputs[0], dim=0)
            
            agri_idx = self.classes.index("agricultural") if "agricultural" in self.classes else 0
            non_agri_idx = self.classes.index("non_agricultural") if "non_agricultural" in self.classes else 1
            
            agri_prob = probs[agri_idx].item()
            non_agri_prob = probs[non_agri_idx].item()
            
            is_agri = agri_prob >= 0.50
            
            logger.info(f"[IMAGE VALIDATION] Agricultural Prob: {agri_prob*100:.2f}% | Non-Agricultural Prob: {non_agri_prob*100:.2f}% | Result: {'YES' if is_agri else 'NO'}")
            
            if is_agri:
                return {
                    "is_agricultural": True,
                    "confidence": agri_prob,
                    "label": "agricultural",
                    "status": "valid",
                    "reason": "Verified agricultural crop image."
                }
            else:
                return {
                    "is_agricultural": False,
                    "confidence": non_agri_prob,
                    "label": "non_agricultural",
                    "status": "unsupported_image",
                    "reason": "The uploaded image does not appear to contain a supported agricultural crop or plant leaf."
                }
        except Exception as e:
            logger.error(f"[AgriculturalValidator] Inference failed: {e}")
            return {
                "is_agricultural": False,
                "confidence": 0.0,
                "label": "error",
                "status": "error",
                "reason": f"Validation failed: {e}"
            }

agricultural_validator = AgriculturalValidator()
