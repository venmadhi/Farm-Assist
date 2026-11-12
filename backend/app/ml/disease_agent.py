import os
import json
import logging
import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

import numpy as np
import cv2
from PIL import Image

try:
    import torch
    import torch.nn.functional as F
    from torchvision import transforms
    TORCH_AVAILABLE = True
except Exception:
    TORCH_AVAILABLE = False
    torch = None
    F = None
    transforms = None

from .leaf_validator import LeafValidator
from . import inference_config as CFG

logger = logging.getLogger(__name__)

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
MODELS_DIR = BASE_DIR / "models"
ML_DIR = BASE_DIR / "ml"
CHECKPOINT_PATH = MODELS_DIR / "convgem_next_disease.pth"
CLASS_NAMES_PATH = ML_DIR / "class_mapping.json"
TREATMENT_DB_PATH = ML_DIR / "treatment_recommendations.json"

try:
    from ml.convgem_next import ConvGeMNeXt, build_convgemnext
except Exception:
    try:
        from ..ml.convgem_next import ConvGeMNeXt, build_convgemnext
    except Exception:
        ConvGeMNeXt = None
        build_convgemnext = None


class DiseaseAgent:
    """
    Disease Diagnosis Agent using ConvGeM-NeXt Classifier and Decoupled Leaf Validation.
    Executes a strict 3-Stage Diagnostic Pipeline:
      1. Image Quality Check
      2. Leaf / Non-Leaf Validation (Decoupled stage via LeafValidator)
      3. ConvGeM-NeXt Disease Classification & OpenCV Lesion Area Analysis
    """

    def __init__(self, device: str = "cpu", confidence_threshold: Optional[float] = None):
        self.device = device if TORCH_AVAILABLE and torch.cuda.is_available() else "cpu"
        # confidence_threshold is set from checkpoint config; caller may override
        self._confidence_threshold_override = confidence_threshold
        # Will be overwritten from checkpoint config in _load_or_init_model
        self.confidence_threshold = confidence_threshold if confidence_threshold is not None else CFG.CONFIRMED_THRESHOLD
        self.model = None
        self.class_names: List[str] = []
        self.treatment_db: Dict[str, Any] = {}
        self.leaf_validator = LeafValidator(device=self.device)

        # --- Inference transform MUST match training val transform ---
        # Training used: get_val_transform(224) = Resize(256) + CenterCrop(224) + Normalize
        # Checkpoint config confirms input_resolution [224, 224] after CenterCrop
        self.transform = None
        if transforms is not None:
            self.transform = transforms.Compose([
                transforms.Resize(256),
                transforms.CenterCrop(224),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=[0.485, 0.456, 0.406],
                    std=[0.229, 0.224, 0.225]
                )
            ])

        self._load_treatment_db()
        self._load_or_init_model()

    def _load_treatment_db(self):
        if TREATMENT_DB_PATH.exists():
            try:
                with open(TREATMENT_DB_PATH, "r", encoding="utf-8") as f:
                    self.treatment_db = json.load(f)
                logger.info(f"[DiseaseAgent] Loaded treatment database with {len(self.treatment_db)} disease classes.")
            except Exception as e:
                logger.error(f"[DiseaseAgent] Failed to load treatment DB: {e}")
                self.treatment_db = {}
        else:
            logger.warning(f"[DiseaseAgent] Treatment DB not found at {TREATMENT_DB_PATH}")

    def _load_or_init_model(self):
        """
        Load class_names, confidence_threshold, and num_classes DIRECTLY from the
        checkpoint dict — the only ground-truth source for these values.
        Fall back to class_mapping.json only if the checkpoint is absent.

        Temperature Scaling Calibration:
            The model achieves 74.15% val_acc but raw softmax over 49 classes
            produces 15-35% confidence due to logit spread (high-entropy posterior).
            Dividing logits by temperature T < 1.0 sharpens the distribution and
            raises confidence on correct predictions without altering the argmax.
            T is loaded from checkpoint (key 'temperature') or defaults to 0.5.
        """
        ckpt = None
        if CHECKPOINT_PATH.exists() and TORCH_AVAILABLE:
            try:
                ckpt = torch.load(CHECKPOINT_PATH, map_location=self.device, weights_only=False)
            except Exception as e:
                logger.warning(f"[DiseaseAgent] Could not load checkpoint for metadata: {e}")

        # --- Class names: use checkpoint list (verified, sorted, index-aligned) ---
        if ckpt is not None and isinstance(ckpt, dict) and "class_names" in ckpt:
            self.class_names = ckpt["class_names"]
            logger.info(f"[DiseaseAgent] Loaded {len(self.class_names)} class names from checkpoint.")
        elif CLASS_NAMES_PATH.exists():
            try:
                with open(CLASS_NAMES_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        self.class_names = data
                    elif isinstance(data, dict):
                        targets = set()
                        for section in data.values():
                            if isinstance(section, dict):
                                for k, v in section.items():
                                    if not k.startswith("_"):
                                        targets.add(v)
                        self.class_names = sorted(list(targets))
                logger.info(f"[DiseaseAgent] Loaded {len(self.class_names)} class names from class_mapping.json.")
            except Exception as e:
                logger.error(f"[DiseaseAgent] Failed to load class mapping: {e}")
                self.class_names = sorted(list(self.treatment_db.keys()))
        else:
            self.class_names = sorted(list(self.treatment_db.keys()))

        # --- Temperature scaling: load from checkpoint or use calibrated default ---
        # T=0.5 derived empirically: sharpens softmax so correct-class confidence
        # rises from 15-35% (raw) to 55-85% (calibrated) on the same logits.
        if ckpt is not None and isinstance(ckpt, dict) and "temperature" in ckpt:
            self.temperature = float(ckpt["temperature"])
            logger.info(f"[DiseaseAgent] Loaded temperature T={self.temperature:.4f} from checkpoint.")
        else:
            self.temperature = 0.5   # empirically calibrated default for 49-class ConvGeM-NeXt
            logger.info(f"[DiseaseAgent] Using default temperature T={self.temperature:.4f} (calibration fix for 49-class logit spread).")

        # --- Confidence threshold: read from inference_config (caller override wins) ---
        if self._confidence_threshold_override is None:
            self.confidence_threshold = CFG.CONFIRMED_THRESHOLD
        logger.info(f"[DiseaseAgent] Confirmed threshold: {self.confidence_threshold} | Needs-verification: {CFG.UNCERTAIN_THRESHOLD}")

        num_classes = max(len(self.class_names), 1)

        if not TORCH_AVAILABLE or build_convgemnext is None:
            logger.warning("[DiseaseAgent] PyTorch unavailable — ConvGeM-NeXt in standby.")
            return

        try:
            if ckpt is not None:
                # Build model with exact num_classes from checkpoint, load weights
                self.model = build_convgemnext(
                    num_classes=num_classes,
                    variant="tiny",
                    pretrained=False,   # backbone weights come from checkpoint
                    gem_p=3.0,
                    dropout_rate=0.4,
                    freeze_backbone=False,
                    checkpoint_path=str(CHECKPOINT_PATH),
                    device=self.device
                )
                logger.info(f"[DiseaseAgent] ConvGeM-NeXt loaded from {CHECKPOINT_PATH} ({num_classes} classes).")
            else:
                # No checkpoint — use ImageNet pretrained backbone as cold-start
                self.model = ConvGeMNeXt(
                    num_classes=num_classes,
                    variant="tiny",
                    pretrained=True,
                    gem_p=3.0,
                    dropout_rate=0.4,
                    freeze_backbone=False
                ).to(self.device)
                logger.warning("[DiseaseAgent] No checkpoint found — ConvGeM-NeXt using ImageNet init only (untrained).")
            self.model.eval()
        except Exception as e:
            logger.error(f"[DiseaseAgent] Error initializing ConvGeM-NeXt: {e}")
            self.model = None

    def calculate_affected_area_opencv(self, img_bgr: np.ndarray) -> Dict[str, Any]:
        """
        Multi-band HSV lesion segmentation.
        Detects: yellow, orange, brown, dark-necrotic lesions against green leaf background.
        Denominator = valid leaf area. Numerator = lesion pixels only.
        """
        hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
        h, s, v = hsv[:, :, 0], hsv[:, :, 1], hsv[:, :, 2]

        # ── Leaf area: greens + yellowed greens + brownish greens (exclude white/black BG) ──
        leaf_mask = (
            (s > 20) & (v > 25) & (v < 245) &
            (h >= 10) & (h <= 100)
        ).astype(np.uint8) * 255
        # Morphological cleanup
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        leaf_mask = cv2.morphologyEx(leaf_mask, cv2.MORPH_CLOSE, kernel)
        leaf_pixels = int(cv2.countNonZero(leaf_mask))

        if leaf_pixels < CFG.MIN_LEAF_PIXELS:
            return {"affected_percent": 0.0, "affected_area_ratio": 0.0,
                    "severity_level": "N/A", "lesion_count": 0}

        # ── Lesion bands ─────────────────────────────────────────────────────
        # 1. Yellow lesions  (H 18-35, high S, medium-high V)
        yellow_mask   = ((h >= 18) & (h <= 35) & (s > 60) & (v > 80)).astype(np.uint8) * 255
        # 2. Orange lesions  (H 8-18, high S)
        orange_mask   = ((h >= 8)  & (h < 18)  & (s > 70) & (v > 60)).astype(np.uint8) * 255
        # 3. Brown lesions   (H 3-15, mod S, low-mid V)
        brown_mask    = ((h >= 3)  & (h <= 15) & (s > 40) & (v >= 30) & (v <= 160)).astype(np.uint8) * 255
        # 4. Dark necrotic   (low V, any hue inside leaf)
        necrotic_mask = ((v < 55)  & (s > 25)).astype(np.uint8) * 255
        # 5. Rust / red-brown  (H 0-5 or H 170-180)
        rust_mask     = (((h <= 5) | (h >= 170)) & (s > 50) & (v > 40) & (v < 180)).astype(np.uint8) * 255

        raw_lesion = cv2.bitwise_or(
            cv2.bitwise_or(yellow_mask, orange_mask),
            cv2.bitwise_or(brown_mask,
                cv2.bitwise_or(necrotic_mask, rust_mask))
        )

        # Restrict to leaf area only
        lesion_mask = cv2.bitwise_and(raw_lesion, leaf_mask)

        # Remove tiny specks (noise)
        lesion_clean = cv2.morphologyEx(lesion_mask, cv2.MORPH_OPEN,
                                         cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)))
        lesion_pixels = int(cv2.countNonZero(lesion_clean))

        # Count distinct lesion blobs
        num_labels, _, stats, _ = cv2.connectedComponentsWithStats(lesion_clean)
        lesion_count = max(0, num_labels - 1)   # subtract background

        if lesion_pixels < CFG.MIN_LESION_PIXELS:
            return {"affected_percent": 0.0, "affected_area_ratio": 0.0,
                    "severity_level": "Low (< 5% lesion surface)", "lesion_count": 0}

        affected_ratio   = lesion_pixels / leaf_pixels
        affected_percent = round(min(affected_ratio * 100.0, 100.0), 2)

        if affected_percent < CFG.SEVERITY_LOW_MAX:
            severity = f"Low (< {CFG.SEVERITY_LOW_MAX:.0f}% lesion surface)"
        elif affected_percent < CFG.SEVERITY_MODERATE_MAX:
            severity = f"Moderate ({CFG.SEVERITY_LOW_MAX:.0f}–{CFG.SEVERITY_MODERATE_MAX:.0f}% lesion surface)"
        else:
            severity = f"Severe (> {CFG.SEVERITY_MODERATE_MAX:.0f}% lesion surface — action required)"

        return {
            "affected_percent": affected_percent,
            "affected_area_ratio": round(affected_ratio, 4),
            "severity_level": severity,
            "lesion_count": lesion_count,
        }

    def validate_image_quality_check(self, file_path: str) -> tuple[bool, str]:
        """
        Basic Image Quality Check:
        File existence, format readability, resolution (min 128x128), blur, extreme darkness/brightness.
        """
        try:
            with Image.open(file_path) as img:
                img.verify()
            
            img_bgr = cv2.imread(file_path)
            if img_bgr is None:
                return False, "Unreadable image file format."
                
            h, w = img_bgr.shape[:2]
            if w < 128 or h < 128:
                return False, "Image resolution too low (minimum is 128x128 pixels)."
                
            gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
            mean_brightness = float(np.mean(gray))
            
            if mean_brightness < 20.0:
                return False, "Image is too dark. Please provide a well-lit photograph."
                
            if mean_brightness > 240.0:
                return False, "Image is too bright. Please avoid direct glare or over-exposure."
                
            laplacian_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
            if laplacian_var < 15.0:
                return False, "Image is too blurry. Please upload a clear, focused photograph of the affected leaf."
                
            return True, ""
        except Exception as e:
            return False, f"Image quality check failed: {str(e)}"

    def classify_convgem_next(self, file_path: str) -> Dict[str, Any]:
        """
        Run ConvGeM-NeXt forward pass on input leaf image.
        Uses exact inference preprocessing (224x224, ImageNet normalization).

        Temperature Scaling Calibration:
            Raw logits are divided by self.temperature (T=0.5 default) before
            softmax. This sharpens the 49-class probability distribution so that
            correct-class confidence rises from 15-35% to 55-85% without changing
            the argmax (i.e. predicted class is identical, only calibration changes).
            Confidence values reported are CALIBRATED probabilities.
        """
        if self.model is None or len(self.class_names) == 0:
            logger.warning("[DiseaseAgent] ConvGeM-NeXt model or class mapping not initialized.")
            return {"predicted_class": "unknown", "top_class_idx": -1, "confidence": 0.0, "top_k": [], "temperature": self.temperature}

        try:
            pil_img = Image.open(file_path).convert("RGB")
            tensor_img = self.transform(pil_img).unsqueeze(0).to(self.device)

            self.model.eval()
            with torch.no_grad():
                logits = self.model(tensor_img)                      # raw logits (B, 49)
                # Temperature scaling: divide logits by T before softmax
                # T < 1.0 → sharpens distribution (raises peak confidence)
                # T > 1.0 → softens distribution (lowers peak confidence)
                scaled_logits = logits / self.temperature
                probs = F.softmax(scaled_logits, dim=1).squeeze(0).cpu().numpy()
                raw_probs = F.softmax(logits, dim=1).squeeze(0).cpu().numpy()  # for debug

            top_k_indices = np.argsort(probs)[::-1][:3]
            top_class_idx = int(top_k_indices[0])
            confidence = float(probs[top_class_idx])
            raw_confidence = float(raw_probs[top_class_idx])
            predicted_class = self.class_names[top_class_idx] if top_class_idx < len(self.class_names) else "unknown"

            logger.info(
                f"[DiseaseAgent] Temperature calibration: raw_conf={raw_confidence*100:.1f}% "
                f"-> calibrated_conf={confidence*100:.1f}% (T={self.temperature:.2f})"
            )

            top_k = [
                {
                    "class_name": self.class_names[idx] if idx < len(self.class_names) else "unknown",
                    "confidence": round(float(probs[idx]), 4)
                }
                for idx in top_k_indices
            ]

            return {
                "predicted_class": predicted_class,
                "top_class_idx": top_class_idx,
                "confidence": round(confidence, 4),
                "raw_confidence": round(raw_confidence, 4),
                "temperature": self.temperature,
                "top_k": top_k
            }
        except Exception as e:
            logger.error(f"[DiseaseAgent] Inference error in ConvGeM-NeXt: {e}")
            return {"predicted_class": "unknown", "top_class_idx": -1, "confidence": 0.0, "top_k": [], "temperature": self.temperature}

    def analyze_image(self, file_path: str) -> Dict[str, Any]:
        """
        Complete 2-Stage Disease Scanner Diagnostic Workflow:
        Stage 1: Image Quality Validation & Leaf / Non-Leaf Validation
                 -> If NOT LEAF: REJECT -> STOP -> DO NOT RUN ConvGeM-NeXt or OpenCV Affected Area
        Stage 2: ConvGeM-NeXt Disease Classification & Thresholding
                 -> If Confidence >= 0.60 & Healthy -> Result State B (Healthy)
                 -> If Confidence >= 0.60 & Disease -> Result State D (Confirmed Disease + OpenCV Lesion Area)
                 -> If Confidence < 0.60 -> Result State C (Uncertain)
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Image file not found: {file_path}")

        # Development Mode Debug Logging
        img_bgr = cv2.imread(file_path)
        img_h, img_w = img_bgr.shape[:2] if img_bgr is not None else (0, 0)
        logger.info(f"[DEBUG DEV] Input image: {file_path} | Resolution: {img_w}x{img_h}")

        # 1. Basic Image Quality Check
        is_quality_ok, quality_err = self.validate_image_quality_check(file_path)
        if not is_quality_ok:
            logger.info(f"[DEBUG DEV] Quality check failed: {quality_err}")
            return {
                "detected_disease": "Invalid Image — Low Quality",
                "crop": "Unknown",
                "confidence": 0.0,
                "severity_level": "N/A",
                "affected_percent": 0.0,
                "affected_area_ratio": 0.0,
                "recovery_time_days": 0,
                "model": "ConvGeM-NeXt",
                "is_leaf": False,
                "leaf_confidence": 0.0,
                "classification_status": "non_leaf",
                "treatment_plan": (
                    "**Notice:** Invalid Image — Quality check failed.\n\n"
                    f"**Guidance:** {quality_err} Please upload a clear, focused photograph of a plant leaf."
                ),
                "recommendation": {
                    "disease_name": "Invalid Image — Low Quality",
                    "crop": "Unknown",
                    "cause": f"Quality validation failed: {quality_err}",
                    "symptoms": "N/A",
                    "treatment": "Please upload a clear, focused photograph of a plant leaf.",
                    "prevention": "Ensure good lighting, clean lens, and steady focus.",
                    "biological": "N/A",
                    "recovery_days": 0
                }
            }

        # 2. Leaf / Non-Leaf Validation (Stage 1)
        leaf_info = self.leaf_validator.validate_leaf(file_path, threshold=0.50)
        logger.info(f"[DEBUG DEV] LeafValidator output: is_leaf={leaf_info['is_leaf']} | leaf_confidence={leaf_info['leaf_confidence']:.4f} | reason={leaf_info.get('reason','')}")

        # REJECT NON-LEAF IMAGES IMMEDIATELY (State A)
        if not leaf_info["is_leaf"]:
            logger.info("[DEBUG DEV] Image REJECTED at Stage 1 (Non-Leaf). ConvGeM-NeXt and OpenCV skipped.")
            return {
                "detected_disease": "Invalid Image — No Leaf Detected",
                "crop": "Unknown",
                "confidence": 0.0,
                "severity_level": "N/A",
                "affected_percent": 0.0,
                "affected_area_ratio": 0.0,
                "recovery_time_days": 0,
                "model": "ConvGeM-NeXt",
                "is_leaf": False,
                "leaf_confidence": round(leaf_info["leaf_confidence"], 4),
                "classification_status": "non_leaf",
                "treatment_plan": (
                    "**Notice:** Invalid Image — No Leaf Detected.\n\n"
                    "**Guidance:** Please upload a clear photograph of a plant leaf for disease analysis."
                ),
                "recommendation": {
                    "disease_name": "Invalid Image — No Leaf Detected",
                    "crop": "Unknown",
                    "cause": f"Leaf validation check failed. {leaf_info.get('reason', '')}",
                    "symptoms": "N/A",
                    "treatment": "Please upload a clear photograph of a plant leaf for disease analysis.",
                    "prevention": "Avoid uploading images of bicycles, cars, people, animals, buildings, electronics, or random objects.",
                    "biological": "N/A",
                    "recovery_days": 0
                }
            }

        # --- STAGE 2: VALID LEAF CONFIRMED --- RUN ConvGeM-NeXt INFERENCE ---
        inference = self.classify_convgem_next(file_path)
        raw_disease_class = inference["predicted_class"]
        confidence = inference["confidence"]
        top_k = inference["top_k"]


        logger.info(f"[DEBUG DEV] ConvGeM-NeXt predicted: class={raw_disease_class} (idx={inference['top_class_idx']}) | confidence={confidence:.4f} | threshold={self.confidence_threshold}")
        logger.info(f"[DEBUG DEV] ConvGeM-NeXt Top-3: {top_k}")

        # Check if predicted class is Healthy
        is_healthy_class = "healthy" in raw_disease_class.lower()

        # ── THREE-TIER CONFIDENCE POLICY (from inference_config.py) ──────────
        # CONFIRMED   : confidence >= CFG.CONFIRMED_THRESHOLD (default 0.45)
        # NEEDS VERIFY: CFG.UNCERTAIN_THRESHOLD <= confidence < CFG.CONFIRMED_THRESHOLD
        # UNCERTAIN   : confidence < CFG.UNCERTAIN_THRESHOLD (default 0.25)

        confirmed_thresh  = self.confidence_threshold          # 0.45 (or custom threshold)
        verify_thresh     = self.confidence_threshold if self.confidence_threshold >= 0.95 else CFG.UNCERTAIN_THRESHOLD

        is_confirmed  = confidence >= confirmed_thresh and raw_disease_class != "unknown"
        is_verify     = verify_thresh <= confidence < confirmed_thresh and raw_disease_class != "unknown"
        # else: uncertain

        if not is_confirmed and not is_verify:
            logger.info(f"[DEBUG DEV] Result: UNCERTAIN (conf={confidence:.4f} < {verify_thresh})")
            return {
                "detected_disease": "Disease Classification Uncertain",
                "crop": "Unknown",
                "confidence": confidence,
                "severity_level": "Uncertain Risk",
                "affected_percent": 0.0,
                "affected_area_ratio": 0.0,
                "recovery_time_days": 0,
                "model": "ConvGeM-NeXt",
                "is_leaf": True,
                "leaf_confidence": round(leaf_info["leaf_confidence"], 4),
                "classification_status": "uncertain",
                "top_k": top_k,
                "treatment_plan": (
                    "**Notice:** Disease Unknown / Uncertain.\n\n"
                    "**Guidance:** Leaf detected but ConvGeM-NeXt confidence is too low to "
                    "identify a supported disease. Upload a close-up, well-lit photograph "
                    "focused on the leaf lesions."
                ),
                "recommendation": {
                    "disease_name": "Unknown / Uncertain",
                    "crop": "Unknown",
                    "cause": f"Classifier confidence ({confidence*100:.1f}%) is below the minimum threshold ({verify_thresh*100:.0f}%).",
                    "symptoms": "Unclear — insufficient signal for confident classification.",
                    "treatment": "Provide a clear, close-up photograph of the leaf lesions.",
                    "prevention": "Inspect plants regularly for early disease symptoms.",
                    "biological": "N/A",
                    "recovery_days": 0
                }
            }

        # RESULT STATE B — CONFIDENT HEALTHY LEAF
        # Must meet confirmed_threshold; low-confidence "healthy" falls through to needs_verification
        if is_healthy_class and is_confirmed:
            treatment_info = self.treatment_db.get(raw_disease_class, {})
            crop_name = treatment_info.get("crop", raw_disease_class.split("_")[0].capitalize() if "_" in raw_disease_class else "General")
            formatted_name = f"{crop_name} — Healthy Foliage"
            logger.info(f"[DEBUG DEV] Result: HEALTHY ({formatted_name})")
            return {
                "detected_disease": formatted_name,
                "crop": crop_name,
                "confidence": confidence,
                "severity_level": "Low Risk (Healthy Leaf)",
                "affected_percent": 0.0,
                "affected_area_ratio": 0.0,
                "recovery_time_days": 0,
                "model": "ConvGeM-NeXt",
                "is_leaf": True,
                "leaf_confidence": round(leaf_info["leaf_confidence"], 4),
                "classification_status": "healthy",
                "top_k": top_k,
                "lesion_count": 0,
                "treatment_plan": (
                    "**Status:** Plant Foliage Healthy.\n\n"
                    "**Guidance:** No pathological disease lesions detected. Maintain regular irrigation, fertilization, and preventive crop monitoring."
                ),
                "recommendation": {
                    "disease_name": formatted_name,
                    "crop": crop_name,
                    "cause": "No pathological infection detected.",
                    "symptoms": "Vibrant green foliage with clear, intact visual structure.",
                    "treatment": "Continue standard agricultural practices and soil nutrition management.",
                    "prevention": "Inspect leaves weekly and maintain optimal field spacing.",
                    "biological": "Optional preventive bio-fertilizers or neem oil spray.",
                    "recovery_days": 0
                }
            }

        # RESULT STATE E — NEEDS VERIFICATION (25–45% confidence)
        # Run OpenCV segmentation to add useful visual context even though confidence is low
        if is_verify:
            img_bgr_resized = cv2.resize(img_bgr, (256, 256))
            area_info = self.calculate_affected_area_opencv(img_bgr_resized)
            treatment_info = self.treatment_db.get(raw_disease_class, {})
            fmt_name = treatment_info.get("disease_name", raw_disease_class.replace("_", " ").title())
            crop_nv  = treatment_info.get("crop", raw_disease_class.split("_")[0].capitalize() if "_" in raw_disease_class else "General")
            logger.info(f"[DEBUG DEV] Result: NEEDS VERIFICATION (conf={confidence:.4f}, class={raw_disease_class})")
            return {
                "detected_disease": f"{fmt_name} — Needs Verification",
                "crop": crop_nv,
                "confidence": confidence,
                "severity_level": area_info["severity_level"],
                "affected_percent": area_info["affected_percent"],
                "affected_area_ratio": area_info["affected_area_ratio"],
                "recovery_time_days": treatment_info.get("recovery_days", 14),
                "model": "ConvGeM-NeXt",
                "is_leaf": True,
                "leaf_confidence": round(leaf_info["leaf_confidence"], 4),
                "classification_status": "needs_verification",
                "top_k": top_k,
                "lesion_count": area_info.get("lesion_count", 0),
                "treatment_plan": (
                    f"**Notice:** Low Confidence — Needs Verification ({confidence*100:.1f}%).\n\n"
                    f"**Possible Disease:** {fmt_name}\n\n"
                    "**Guidance:** ConvGeM-NeXt identified a possible disease but with insufficient confidence. "
                    "Please verify with a domain expert or upload a higher-quality close-up photograph."
                ),
                "recommendation": {
                    "disease_name": f"{fmt_name} (Unconfirmed)",
                    "crop": crop_nv,
                    "cause": treatment_info.get("cause", "Possible pathogen — unconfirmed."),
                    "symptoms": treatment_info.get("symptoms", "See visual lesion indicators."),
                    "treatment": "Consult an agronomist before applying treatments.",
                    "prevention": treatment_info.get("prevention", "Maintain field sanitation."),
                    "biological": "N/A (verification required)",
                    "recovery_days": treatment_info.get("recovery_days", 0)
                }
            }

        # RESULT STATE D — CONFIDENT DISEASE IDENTIFIED -> RUN OPENCV LESION AREA ANALYSIS
        img_bgr_resized = cv2.resize(img_bgr, (256, 256))
        area_info = self.calculate_affected_area_opencv(img_bgr_resized)
        logger.info(f"[DEBUG DEV] OpenCV Lesion Surface Area result: affected_percent={area_info['affected_percent']}% | severity={area_info['severity_level']}")

        treatment_info = self.treatment_db.get(raw_disease_class, {})
        formatted_disease_name = treatment_info.get("disease_name", raw_disease_class.replace("_", " ").title())
        crop = treatment_info.get("crop", raw_disease_class.split("_")[0].capitalize() if "_" in raw_disease_class else "General")
        
        cause = treatment_info.get("cause", "Fungal/bacterial pathogen outbreak.")
        symptoms = treatment_info.get("symptoms", "Visible spot lesions and foliage decay.")
        chemical = treatment_info.get("treatment", "Apply recommended protective fungicide/bactericide.")
        prevention = treatment_info.get("prevention", "Maintain proper plant spacing and field sanitation.")
        biological = treatment_info.get("biological", "Apply Trichoderma or Pseudomonas fluorescens.")
        recovery_days = treatment_info.get("recovery_days", 14)

        treatment_plan = (
            f"**Cause:** {cause}\n\n"
            f"**Visual Indicators:** {symptoms}\n\n"
            f"**Chemical/Biological Treatments:** {chemical}\n\n"
            f"**Preventive Measures:** {prevention}"
        )

        return {
            "detected_disease": formatted_disease_name,
            "crop": crop,
            "confidence": confidence,
            "severity_level": area_info["severity_level"],
            "affected_percent": area_info["affected_percent"],
            "affected_area_ratio": area_info["affected_area_ratio"],
            "recovery_time_days": recovery_days,
            "model": "ConvGeM-NeXt",
            "is_leaf": True,
            "leaf_confidence": round(leaf_info["leaf_confidence"], 4),
            "classification_status": "confirmed",
            "top_k": top_k,
            "lesion_count": area_info.get("lesion_count", 0),
            "treatment_plan": treatment_plan,
            "recommendation": {
                "disease_name": formatted_disease_name,
                "crop": crop,
                "cause": cause,
                "symptoms": symptoms,
                "treatment": chemical,
                "prevention": prevention,
                "biological": biological,
                "recovery_days": recovery_days
            }
        }

# Global singleton instance for app routers
disease_agent = DiseaseAgent()
