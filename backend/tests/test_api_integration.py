"""
Integration test: calls the live /disease/scan API endpoint to verify
the three-stage pipeline (quality -> leaf detection -> classification)
returns correct classification_status, is_leaf, and leaf_confidence fields.
"""
import os
import sys
import requests
import numpy as np
import cv2

BASE = "http://127.0.0.1:8000/api/v1"


def make_leaf_image(path):
    """Green circle with Gaussian noise (clear leaf)."""
    img = np.zeros((300, 300, 3), dtype=np.int16)
    cv2.circle(img, (150, 150), 90, (0, 180, 0), -1)
    noise = np.random.normal(0, 15, (300, 300, 3)).astype(np.int16)
    img = np.clip(img + noise, 0, 255).astype(np.uint8)
    cv2.imwrite(path, img)


def make_nonleaf_image(path):
    """Pure blue block with noise (non-leaf)."""
    img = np.ones((300, 300, 3), dtype=np.int16) * [255, 20, 20]
    noise = np.random.normal(0, 15, (300, 300, 3)).astype(np.int16)
    img = np.clip(img + noise, 0, 255).astype(np.uint8)
    cv2.imwrite(path, img)


def make_blurry_image(path):
    """Heavily blurred green circle (blurry, fails quality check)."""
    img = np.zeros((300, 300, 3), dtype=np.uint8)
    cv2.circle(img, (150, 150), 90, (0, 180, 0), -1)
    img = cv2.GaussianBlur(img, (45, 45), 0)
    cv2.imwrite(path, img)


def login():
    r = requests.post(BASE + "/auth/login",
                      json={"phone_number": "0987654321", "password": "password"})
    token = r.json().get("access_token", "")
    print(f"Login: HTTP {r.status_code} | Token: {token[:20]}...")
    return token


def scan(token, filepath):
    headers = {"Authorization": f"Bearer {token}"}
    with open(filepath, "rb") as f:
        fname = os.path.basename(filepath)
        r = requests.post(
            BASE + "/disease/scan",
            headers=headers,
            files={"file": (fname, f, "image/jpeg")}
        )
    return r.json()


def run():
    paths = {
        "leaf": "test_api_leaf.jpg",
        "nonleaf": "test_api_nonleaf.jpg",
        "blurry": "test_api_blurry.jpg"
    }

    np.random.seed(99)
    make_leaf_image(paths["leaf"])
    make_nonleaf_image(paths["nonleaf"])
    make_blurry_image(paths["blurry"])

    token = login()
    failures = []

    # ---- TEST 1: Clear leaf ----
    d = scan(token, paths["leaf"])
    print("\n=== TEST 1: Clear Leaf ===")
    for k in ["detected_disease", "classification_status", "is_leaf",
              "leaf_confidence", "confidence", "severity_level", "affected_percent"]:
        print(f"  {k}: {d.get(k)}")

    if d.get("classification_status") not in ("confirmed", "uncertain"):
        failures.append(f"T1 classification_status should be 'confirmed' or 'uncertain', got: {d.get('classification_status')}")
    if d.get("is_leaf") is False:
        failures.append("T1 is_leaf should be True for a clear leaf image")
    if d.get("detected_disease") == "Non-Leaf Image":
        failures.append("T1 CRITICAL: clear leaf was incorrectly classified as 'Non-Leaf Image'")

    # ---- TEST 2: Non-leaf (blue block) ----
    d2 = scan(token, paths["nonleaf"])
    print("\n=== TEST 2: Non-Leaf (Blue Block) ===")
    for k in ["detected_disease", "classification_status", "is_leaf", "leaf_confidence", "confidence"]:
        print(f"  {k}: {d2.get(k)}")

    if d2.get("classification_status") != "non_leaf":
        failures.append(f"T2 classification_status should be 'non_leaf', got: {d2.get('classification_status')}")
    if d2.get("is_leaf") is not False:
        failures.append("T2 is_leaf should be False for a non-leaf image")
    if d2.get("detected_disease") != "Non-Leaf Image":
        failures.append(f"T2 detected_disease should be 'Non-Leaf Image', got: {d2.get('detected_disease')}")

    # ---- TEST 3: Blurry image ----
    d3 = scan(token, paths["blurry"])
    print("\n=== TEST 3: Blurry Image ===")
    for k in ["detected_disease", "classification_status", "is_leaf", "confidence"]:
        print(f"  {k}: {d3.get(k)}")

    if d3.get("detected_disease") != "Image Quality Too Low":
        failures.append(f"T3 detected_disease should be 'Image Quality Too Low', got: {d3.get('detected_disease')}")
    if d3.get("classification_status") != "uncertain":
        failures.append(f"T3 classification_status should be 'uncertain', got: {d3.get('classification_status')}")

    # Cleanup
    for p in paths.values():
        if os.path.exists(p):
            os.remove(p)

    print()
    if failures:
        print("FAILURES:")
        for f in failures:
            print(f"  [FAIL] {f}")
        sys.exit(1)
    else:
        print("ALL TESTS PASSED")


if __name__ == "__main__":
    run()
