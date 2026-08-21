import os
import logging
import numpy as np
import cv2
from PIL import Image
import torch
import torch.nn.functional as F
import torchvision.transforms as transforms
import torchvision.models as models

logger = logging.getLogger(__name__)

# ImageNet Class Index sets for non-leaf objects vs plant/leaf/foliage objects
HARD_NON_LEAF_KEYWORDS = [
    # Vehicles & Transportation
    'bicycle', 'bike', 'cycle', 'car', 'automobile', 'vehicle', 'wheel', 'motorcycle', 'scooter',
    'truck', 'bus', 'train', 'airplane', 'boat', 'ship', 'moped', 'cart',
    # Humans & Apparel
    'person', 'man', 'woman', 'face', 'human', 'suit', 'jersey', 'shoe', 'boot',
    'shirt', 'coat', 'pants', 'ballplayer', 'groom', 'bride',
    # Electronics & Computing
    'phone', 'laptop', 'computer', 'monitor', 'keyboard', 'mouse', 'screen', 'tv',
    'camera', 'microphone', 'radio', 'cellular', 'joystick',
    # Furniture
    'chair', 'table', 'couch', 'sofa', 'bed', 'desk',
    # Buildings & Infrastructure
    'building', 'house', 'church', 'castle', 'bridge', 'street', 'road',
    'monument', 'tower', 'barn', 'store', 'skyscraper'
]

SOFT_NON_LEAF_KEYWORDS = [
    'bottle', 'mug', 'cup', 'can', 'plate', 'bowl', 'toilet', 'bucket', 'clock', 'mirror',
    'pillow', 'dog', 'cat', 'horse', 'cow', 'sheep', 'bird', 'lizard', 'fish', 'snake',
    'guitar', 'piano', 'toy', 'ball', 'racket', 'umbrella', 'bag', 'backpack', 'suitcase',
    'book', 'box', 'envelope', 'hammer', 'screwdriver', 'scissors', 'knife', 'fork', 'spoon'
]

NON_LEAF_KEYWORDS = HARD_NON_LEAF_KEYWORDS + SOFT_NON_LEAF_KEYWORDS

PLANT_LEAF_KEYWORDS = [
    'leaf', 'plant', 'cabbage', 'broccoli', 'cauliflower', 'squash', 'pepper',
    'cucumber', 'zucchini', 'mushroom', 'strawberry', 'banana', 'jackfruit',
    'corn', 'acorn', 'daisy', 'rapeseed', 'hay', 'rose', 'tree', 'foliage',
    'crop', 'fungus', 'head cabbage', 'bell pepper', 'pot', 'greenhouse',
    'fig', 'pineapple', 'pomegranate', 'artichoke', 'cardoon'
]


class LeafValidator:
    """
    Dedicated Deep-Learning Leaf / Non-Leaf Image Validator.
    Uses MobileNetV3 (ImageNet pretrained) combined with organic foliage feature analysis.
    Decoupled from disease classification.
    """
    def __init__(self, device: str = "cpu"):
        self.device = torch.device(device)
        self.model = None
        self.categories = []
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
        ])
        self._init_model()

    def _init_model(self):
        try:
            weights = models.MobileNet_V3_Small_Weights.DEFAULT
            self.categories = weights.meta.get("categories", [])
            self.model = models.mobilenet_v3_small(weights=weights).to(self.device)
            self.model.eval()
            logger.info("[LeafValidator] Loaded MobileNetV3 deep vision feature extractor successfully.")
        except Exception as e:
            logger.warning(f"[LeafValidator] Failed to initialize MobileNetV3 deep vision model: {e}")
            self.model = None

    def validate_leaf(self, file_path: str, threshold: float = 0.50) -> dict:
        """
        Determines whether the image contains a plant leaf.
        Returns:
            {
                "is_leaf": bool,
                "leaf_confidence": float (0.0 to 1.0 probability),
                "reason": str,
                "top_object": str
            }
        """
        try:
            # 1. Organic Foliage Texture & Color Analysis
            img_bgr = cv2.imread(file_path)
            if img_bgr is None:
                return {
                    "is_leaf": False,
                    "leaf_confidence": 0.0,
                    "reason": "Unreadable image file format.",
                    "top_object": "Invalid"
                }

            hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
            
            # Plant foliage color masks (green, yellow, brown/black decay)
            green_mask = cv2.inRange(hsv, np.array([25, 25, 20]), np.array([90, 255, 255]))
            yellow_mask = cv2.inRange(hsv, np.array([12, 25, 20]), np.array([25, 255, 255]))
            brown_mask = cv2.inRange(hsv, np.array([5, 25, 20]), np.array([12, 255, 255]))
            decay_mask = cv2.inRange(hsv, np.array([0, 0, 0]), np.array([180, 255, 50]))

            foliage_mask = cv2.bitwise_or(green_mask, cv2.bitwise_or(yellow_mask, cv2.bitwise_or(brown_mask, decay_mask)))
            total_pixels = img_bgr.shape[0] * img_bgr.shape[1]
            foliage_pixels = cv2.countNonZero(foliage_mask)
            foliage_ratio = foliage_pixels / total_pixels

            # Artificial non-plant color penalty (bright blue, cyan, metallic red/purple)
            artificial_mask = cv2.inRange(hsv, np.array([95, 60, 50]), np.array([140, 255, 255]))
            artificial_ratio = cv2.countNonZero(artificial_mask) / total_pixels

            # Organic contour shape analysis
            contours, _ = cv2.findContours(foliage_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            largest_contour_ratio = 0.0
            if contours and foliage_pixels > 0:
                largest_area = max(cv2.contourArea(c) for c in contours)
                largest_contour_ratio = largest_area / total_pixels

            organic_score = min(1.0, foliage_ratio * 1.4 + largest_contour_ratio * 0.4)
            if artificial_ratio > 0.12:
                organic_score *= 0.3  # Penalty for artificial backgrounds

            # 2. Deep Vision Model Classification (ImageNet pretrained feature extractor)
            deep_leaf_prob = 0.5
            top_object_name = "Unknown Object"
            is_explicit_non_leaf = False

            if self.model is not None:
                pil_img = Image.open(file_path).convert("RGB")
                tensor_img = self.transform(pil_img).unsqueeze(0).to(self.device)
                
                with torch.no_grad():
                    logits = self.model(tensor_img)
                    probs = F.softmax(logits, dim=1).squeeze(0).cpu().numpy()

                top_k_idx = np.argsort(probs)[::-1][:15]
                top_object_name = self.categories[top_k_idx[0]] if top_k_idx[0] < len(self.categories) else "Unknown"

                # Check top-15 predictions for non-leaf vs plant indicators
                non_leaf_sum = 0.0
                plant_sum = 0.0

                for idx in top_k_idx:
                    prob = float(probs[idx])
                    cat_name = self.categories[idx].lower() if idx < len(self.categories) else ""
                    
                    if any(kw in cat_name for kw in HARD_NON_LEAF_KEYWORDS):
                        non_leaf_sum += prob
                    if any(kw in cat_name for kw in PLANT_LEAF_KEYWORDS):
                        plant_sum += prob

                top_1_cat = self.categories[top_k_idx[0]].lower() if top_k_idx[0] < len(self.categories) else ""
                top_1_prob = float(probs[top_k_idx[0]])
                
                has_hard_non_leaf = any(kw in top_1_cat for kw in HARD_NON_LEAF_KEYWORDS)
                has_soft_non_leaf = any(kw in top_1_cat for kw in SOFT_NON_LEAF_KEYWORDS)
                
                if foliage_ratio >= 0.15:
                    # High foliage color (>=15%): hard non-leaf requires top_1_prob > 0.45; soft non-leaf ignored
                    is_explicit_non_leaf = (has_hard_non_leaf and top_1_prob > 0.45) or (non_leaf_sum > 0.65)
                else:
                    # Low foliage color (<15%): standard non-leaf rejection
                    is_explicit_non_leaf = has_hard_non_leaf or (has_soft_non_leaf and top_1_prob > 0.25) or (non_leaf_sum > 0.30)

                if is_explicit_non_leaf or (non_leaf_sum > 0.40 and foliage_ratio < 0.20):
                    deep_leaf_prob = max(0.01, 1.0 - max(non_leaf_sum, float(probs[top_k_idx[0]])))
                elif plant_sum > 0.10:
                    deep_leaf_prob = min(0.99, 0.60 + plant_sum)
                else:
                    # Neutral category — will be guided by organic foliage texture score
                    deep_leaf_prob = 0.55



            # 3. Fuse Deep Vision Probability + Organic Feature Score
            if is_explicit_non_leaf:
                # Primary classifier detected a non-leaf object (e.g. bicycle, car, phone, building)
                final_confidence = min(deep_leaf_prob, 0.15)
            elif self.model is not None:
                fused = 0.60 * deep_leaf_prob + 0.40 * organic_score
                if organic_score >= 0.40:
                    fused = max(fused, organic_score * 0.85)
                final_confidence = fused
            else:
                final_confidence = organic_score

            final_confidence = float(np.clip(final_confidence, 0.0, 0.99))
            is_leaf = final_confidence >= threshold

            reason = f"Non-leaf object detected ({top_object_name})" if not is_leaf else "Plant leaf validation passed."

            return {
                "is_leaf": bool(is_leaf),
                "leaf_confidence": round(final_confidence, 4),
                "reason": reason,
                "top_object": top_object_name
            }

        except Exception as e:
            logger.error(f"[LeafValidator] Leaf validation exception: {e}")
            return {
                "is_leaf": False,
                "leaf_confidence": 0.0,
                "reason": f"Leaf validation failed: {str(e)}",
                "top_object": "Error"
            }
