"""
Full Disease Pipeline Diagnostic
Runs inference on synthetic test images and prints all intermediate values.
Run from: backend/  -> python _diagnose_pipeline.py
"""
import sys, os, torch, numpy as np, cv2
sys.path.insert(0, '.')

from app.ml.disease_agent import DiseaseAgent

agent = DiseaseAgent()
print(f"Model loaded: {agent.model is not None}")
print(f"Classes: {len(agent.class_names)}")
print(f"Threshold: {agent.confidence_threshold}")
print(f"Transform: {agent.transform}")
print()

# --- Generate test images ---

def make_banana_sigatoka(path):
    img = np.zeros((400, 400, 3), dtype=np.uint8)
    cv2.ellipse(img, (200, 200), (160, 190), 15, 0, 360, (34, 120, 34), -1)
    cv2.line(img, (200, 10), (200, 390), (20, 90, 20), 4)
    for i in range(6):
        y = 80 + i * 50
        cv2.line(img, (200, y), (80, y+20), (20, 90, 20), 2)
        cv2.line(img, (200, y), (320, y+20), (20, 90, 20), 2)
    for cx, cy in [(120,130),(180,170),(250,160),(140,220),(220,250)]:
        cv2.ellipse(img, (cx, cy), (30, 8), 15, 0, 360, (20, 160, 200), -1)
        cv2.ellipse(img, (cx, cy), (18, 5), 15, 0, 360, (20, 80, 130), -1)
    cv2.imwrite(path, img)

def make_orange_lesion(path):
    img = np.zeros((400, 400, 3), dtype=np.uint8)
    cv2.ellipse(img, (200, 200), (160, 190), 0, 0, 360, (40, 140, 40), -1)
    for cx, cy in [(130,130),(200,180),(280,160),(150,250),(250,220)]:
        cv2.circle(img, (cx, cy), 35, (0, 165, 255), -1)
        cv2.circle(img, (cx, cy), 20, (0, 80, 200), -1)
        cv2.circle(img, (cx, cy), 35, (0, 200, 255), 3)
    cv2.imwrite(path, img)

def make_healthy_green(path):
    img = np.zeros((400, 400, 3), dtype=np.uint8)
    cv2.ellipse(img, (200, 200), (160, 190), 0, 0, 360, (40, 140, 40), -1)
    cv2.line(img, (200, 20), (200, 380), (20, 100, 20), 4)
    cv2.imwrite(path, img)

def make_non_leaf_blue(path):
    img = np.ones((400, 400, 3), dtype=np.uint8) * np.array([200, 50, 50], dtype=np.uint8)
    cv2.imwrite(path, img)

test_images = [
    ("_test_sigatoka.jpg", make_banana_sigatoka, "Banana Sigatoka (expected: banana/corn disease)"),
    ("_test_orange_lesion.jpg", make_orange_lesion, "Orange Lesion (expected: target/blight)"),
    ("_test_healthy.jpg", make_healthy_green, "Healthy Green Leaf"),
    ("_test_nonleaf.jpg", make_non_leaf_blue, "Non-Leaf Blue Block"),
]

for path, maker, desc in test_images:
    maker(path)

print("=" * 60)
print("DIAGNOSTIC RESULTS")
print("=" * 60)

for path, maker, desc in test_images:
    print(f"\n[{desc}]")

    # Stage 1: Leaf validation
    lv = agent.leaf_validator.validate_leaf(path, threshold=0.50)
    print(f"  Leaf valid:  {lv['is_leaf']}  (confidence: {lv['leaf_confidence']*100:.2f}%)")
    print(f"  Top object:  {lv['top_object']}")

    if lv['is_leaf']:
        # Stage 2: ConvGeM-NeXt inference
        inf = agent.classify_convgem_next(path)
        print(f"  Predicted:   {inf['predicted_class']}  idx={inf['top_class_idx']}")
        print(f"  Confidence:  {inf['confidence']*100:.2f}%")
        print(f"  Top-3:")
        for t in inf['top_k']:
            print(f"    {t['class_name']:40s}  {t['confidence']*100:.2f}%")

        # Stage 3: OpenCV segmentation (only if confirmed would trigger)
        img_bgr = cv2.imread(path)
        img_resized = cv2.resize(img_bgr, (256, 256))
        area = agent.calculate_affected_area_opencv(img_resized)
        print(f"  OpenCV area: {area['affected_percent']}%  severity: {area['severity_level']}")

    # Full pipeline result
    full = agent.analyze_image(path)
    print(f"  Pipeline ->  status={full['classification_status']}  disease={full['detected_disease']}")
    print(f"               affected={full['affected_percent']}%")

# Cleanup
for path, _, _ in test_images:
    if os.path.exists(path):
        os.remove(path)

# Print all 49 class names with indices
print("\n" + "=" * 60)
print("ALL 49 CLASS NAMES (index -> class)")
print("=" * 60)
for i, cls in enumerate(agent.class_names):
    print(f"  {i:2d}: {cls}")
