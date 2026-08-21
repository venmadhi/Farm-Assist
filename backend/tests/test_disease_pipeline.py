"""
test_disease_pipeline.py
========================
Tests for the refactored 2-Stage FarmAssist Disease Scanner Pipeline.

Stage 1: Image Quality Check + Leaf/Non-Leaf Validation (LeafValidator)
Stage 2: ConvGeM-NeXt Disease Inference + Thresholding

Result States:
    non_leaf  -> Quality pass + leaf validation fail
    uncertain -> Leaf detected + confidence < threshold
    healthy   -> Leaf detected + confidence >= threshold + healthy class
    confirmed -> Leaf detected + confidence >= threshold + disease class
"""

import os
import sys
import unittest
import numpy as np
import cv2

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.ml.disease_agent import DiseaseAgent


class TestDiseasePipeline(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Standard agent (default threshold = from checkpoint config = 0.70)
        cls.agent = DiseaseAgent()

        # Paths for temporary synthetic test images
        cls.clear_leaf_path    = "test_clear_leaf.jpg"
        cls.diseased_leaf_path = "test_diseased_leaf.jpg"
        cls.non_leaf_path      = "test_non_leaf.jpg"
        cls.blurry_leaf_path   = "test_blurry_leaf.jpg"

        # Gaussian noise to give images enough texture to pass blur check
        np.random.seed(42)
        noise = np.random.normal(0, 15, (300, 300, 3)).astype(np.int16)

        # 1. Clear healthy green leaf
        img_clear = np.zeros((300, 300, 3), dtype=np.int16)
        cv2.circle(img_clear, (150, 150), 90, (0, 180, 0), -1)
        img_clear = np.clip(img_clear + noise, 0, 255).astype(np.uint8)
        cv2.imwrite(cls.clear_leaf_path, img_clear)

        # 2. Diseased leaf: green leaf body + brown/yellow lesion spots
        img_diseased = np.zeros((300, 300, 3), dtype=np.int16)
        cv2.circle(img_diseased, (150, 150), 90, (0, 180, 0), -1)
        cv2.circle(img_diseased, (110, 110), 22, (30, 80, 120), -1)   # brown lesion
        cv2.circle(img_diseased, (190, 175), 28, (0, 80, 80), -1)    # dark necrotic spot
        img_diseased = np.clip(img_diseased + noise, 0, 255).astype(np.uint8)
        cv2.imwrite(cls.diseased_leaf_path, img_diseased)

        # 3. Non-leaf: solid blue block (no green foliage)
        img_nonleaf = np.ones((300, 300, 3), dtype=np.int16) * [255, 0, 0]
        img_nonleaf = np.clip(img_nonleaf + noise, 0, 255).astype(np.uint8)
        cv2.imwrite(cls.non_leaf_path, img_nonleaf)

        # 4. Blurry leaf (will fail the Laplacian variance check)
        img_blurry = np.zeros((300, 300, 3), dtype=np.uint8)
        cv2.circle(img_blurry, (150, 150), 90, (0, 180, 0), -1)
        img_blurry = cv2.GaussianBlur(img_blurry, (51, 51), 0)
        cv2.imwrite(cls.blurry_leaf_path, img_blurry)

    @classmethod
    def tearDownClass(cls):
        for path in [
            cls.clear_leaf_path,
            cls.diseased_leaf_path,
            cls.non_leaf_path,
            cls.blurry_leaf_path,
        ]:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except Exception:
                    pass

    # ------------------------------------------------------------------
    # 1. Image Quality Check
    # ------------------------------------------------------------------
    def test_image_quality_pass(self):
        """Clear leaf image must pass the quality gate."""
        is_ok, err = self.agent.validate_image_quality_check(self.clear_leaf_path)
        self.assertTrue(is_ok, f"Expected quality pass but got: {err}")

    def test_image_quality_blurry_fail(self):
        """Heavily blurred leaf must be rejected as low quality."""
        is_ok, err = self.agent.validate_image_quality_check(self.blurry_leaf_path)
        self.assertFalse(is_ok)
        self.assertIn("blurry", err.lower())

    # ------------------------------------------------------------------
    # 2. Full Pipeline — Quality Rejection
    # ------------------------------------------------------------------
    def test_pipeline_rejects_blurry_image(self):
        """Blurry image must return non_leaf / low-quality status."""
        res = self.agent.analyze_image(self.blurry_leaf_path)
        print(f"\n[Quality Rejection] detected_disease={res['detected_disease']!r}, status={res['classification_status']!r}")
        self.assertEqual(res["classification_status"], "non_leaf")
        self.assertIn("Quality", res["detected_disease"])
        self.assertFalse(res["is_leaf"])
        self.assertEqual(res["affected_percent"], 0.0)
        self.assertEqual(res["affected_area_ratio"], 0.0)

    # ------------------------------------------------------------------
    # 3. Full Pipeline — Non-Leaf Rejection
    # ------------------------------------------------------------------
    def test_pipeline_rejects_non_leaf(self):
        """Solid blue block must be rejected as non-leaf."""
        res = self.agent.analyze_image(self.non_leaf_path)
        print(f"\n[Non-Leaf Rejection] detected_disease={res['detected_disease']!r}, status={res['classification_status']!r}")
        self.assertEqual(res["classification_status"], "non_leaf")
        self.assertFalse(res["is_leaf"])
        # ConvGeM-NeXt must NOT have run
        self.assertEqual(res["confidence"], 0.0)
        self.assertEqual(res["affected_percent"], 0.0)

    # ------------------------------------------------------------------
    # 4. Full Pipeline — Valid Leaf Result States
    # ------------------------------------------------------------------
    def test_pipeline_valid_leaf_result_state(self):
        """Clear leaf must produce healthy / uncertain / confirmed — never non_leaf."""
        res = self.agent.analyze_image(self.clear_leaf_path)
        print(f"\n[Valid Leaf] detected_disease={res['detected_disease']!r}, status={res['classification_status']!r}, confidence={res['confidence']:.4f}")
        self.assertTrue(res["is_leaf"])
        self.assertIn(res["classification_status"], ["healthy", "uncertain", "confirmed", "needs_verification"])
        self.assertEqual(res["model"], "ConvGeM-NeXt")

    def test_pipeline_uncertain_when_threshold_1(self):
        """Agent with threshold=1.0 must classify all predictions as uncertain."""
        strict_agent = DiseaseAgent(confidence_threshold=1.0)
        res = strict_agent.analyze_image(self.clear_leaf_path)
        print(f"\n[Strict Threshold=1.0] detected_disease={res['detected_disease']!r}, status={res['classification_status']!r}")
        self.assertTrue(res["is_leaf"])
        self.assertEqual(res["classification_status"], "uncertain")
        self.assertEqual(res["detected_disease"], "Disease Classification Uncertain")
        # Affected area must be N/A (0.0) for uncertain state
        self.assertEqual(res["affected_percent"], 0.0)
        self.assertEqual(res["severity_level"], "Uncertain Risk")

    # ------------------------------------------------------------------
    # 5. Affected Area — only for confirmed disease
    # ------------------------------------------------------------------
    def test_affected_area_zero_for_non_leaf(self):
        res = self.agent.analyze_image(self.non_leaf_path)
        self.assertEqual(res["affected_percent"], 0.0)
        self.assertEqual(res["affected_area_ratio"], 0.0)

    def test_affected_area_zero_for_uncertain(self):
        strict_agent = DiseaseAgent(confidence_threshold=1.0)
        res = strict_agent.analyze_image(self.clear_leaf_path)
        self.assertEqual(res["affected_percent"], 0.0)
        self.assertEqual(res["affected_area_ratio"], 0.0)

    # ------------------------------------------------------------------
    # 6. ConvGeM-NeXt top-k inference shape
    # ------------------------------------------------------------------
    def test_classify_convgem_next_returns_top_k(self):
        """classify_convgem_next must return predicted_class, confidence, and top_k list."""
        result = self.agent.classify_convgem_next(self.clear_leaf_path)
        self.assertIn("predicted_class", result)
        self.assertIn("confidence", result)
        self.assertIn("top_k", result)
        self.assertIsInstance(result["top_k"], list)
        self.assertLessEqual(len(result["top_k"]), 3)
        for entry in result["top_k"]:
            self.assertIn("class_name", entry)
            self.assertIn("confidence", entry)


if __name__ == "__main__":
    unittest.main()
