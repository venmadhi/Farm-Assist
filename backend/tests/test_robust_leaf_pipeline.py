import os
import glob
import unittest
import numpy as np
import cv2
from PIL import Image, ImageDraw

from app.ml.disease_agent import DiseaseAgent

class TestRobustLeafPipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.agent = DiseaseAgent()
        cls.test_dir = "test_pipeline_temp"
        os.makedirs(cls.test_dir, exist_ok=True)

    @classmethod
    def tearDownClass(cls):
        import shutil
        if os.path.exists(cls.test_dir):
            shutil.rmtree(cls.test_dir)

    def test_01_non_leaf_rejection_bicycle(self):
        """TEST 1: Bicycle / Non-Leaf Image must be rejected immediately."""
        path = os.path.join(self.test_dir, "test_bike.jpg")
        img = Image.new("RGB", (300, 300), color=(80, 140, 240)) # Metallic blue background
        d = ImageDraw.Draw(img)
        d.ellipse([50, 150, 130, 230], outline="silver", width=8) # Bike wheel 1
        d.ellipse([170, 150, 250, 230], outline="silver", width=8) # Bike wheel 2
        d.line([90, 190, 150, 100], fill="black", width=6) # Frame
        d.line([150, 100, 210, 190], fill="black", width=6) # Frame
        img.save(path)

        res = self.agent.analyze_image(path)
        self.assertFalse(res["is_leaf"])
        self.assertEqual(res["classification_status"], "non_leaf")
        self.assertEqual(res["detected_disease"], "Invalid Image — No Leaf Detected")
        self.assertEqual(res["confidence"], 0.0)
        self.assertEqual(res["affected_percent"], 0.0)
        self.assertEqual(res["model"], "ConvGeM-NeXt")
        print("[PASSED] TEST 1 (Bicycle Non-Leaf Rejection):", res["detected_disease"], "Leaf Confidence:", res["leaf_confidence"])

    def test_02_non_leaf_rejection_car(self):
        """TEST 2: Car / Person / Random Object must be rejected as Non-Leaf."""
        path = os.path.join(self.test_dir, "test_car.jpg")
        img = Image.new("RGB", (300, 300), color=(180, 50, 50)) # Red car body
        d = ImageDraw.Draw(img)
        d.rectangle([50, 120, 250, 220], fill="crimson")
        d.ellipse([70, 200, 110, 240], fill="black") # Tire 1
        d.ellipse([190, 200, 230, 240], fill="black") # Tire 2
        img.save(path)

        res = self.agent.analyze_image(path)
        self.assertFalse(res["is_leaf"])
        self.assertEqual(res["classification_status"], "non_leaf")
        self.assertEqual(res["confidence"], 0.0)
        self.assertEqual(res["affected_percent"], 0.0)
        print("[PASSED] TEST 2 (Car Non-Leaf Rejection):", res["detected_disease"])

    def test_03_valid_leaf_image(self):
        """TEST 3: Clear valid plant leaf must pass leaf validation."""
        uploads = glob.glob("static/uploads/*.jpg")
        leaf_path = None
        for u in uploads:
            # Pick a known real leaf photo from uploads
            if "08288573" in u or "13e2b248" in u:
                leaf_path = u
                break
        
        if not leaf_path:
            leaf_path = os.path.join(self.test_dir, "test_valid_leaf.jpg")
            img_bgr = np.ones((300, 300, 3), dtype=np.uint8) * 220
            cv2.ellipse(img_bgr, (150, 150), (90, 130), 15, 0, 360, (34, 139, 34), -1)
            cv2.imwrite(leaf_path, img_bgr)

        res = self.agent.analyze_image(leaf_path)
        self.assertTrue(res["is_leaf"])
        self.assertIn(res["classification_status"], ["healthy", "uncertain", "confirmed"])
        self.assertEqual(res["model"], "ConvGeM-NeXt")
        print("[PASSED] TEST 3 (Valid Leaf Validation): is_leaf =", res["is_leaf"], "Status =", res["classification_status"])

    def test_04_low_quality_blurry_image(self):
        """TEST 4: Extremely blurry/dark image must be rejected."""
        path = os.path.join(self.test_dir, "test_blurry.jpg")
        img = Image.new("RGB", (300, 300), color=(10, 10, 10)) # Extremely dark
        img.save(path)

        res = self.agent.analyze_image(path)
        self.assertFalse(res["is_leaf"])
        self.assertEqual(res["classification_status"], "non_leaf")
        print("[PASSED] TEST 4 (Low Quality Image Rejection):", res["detected_disease"])

if __name__ == "__main__":
    unittest.main()
