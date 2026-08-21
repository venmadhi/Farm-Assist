"""
FarmAssist Inference Configuration
===================================
Single file controlling all thresholds, tiers, and pipeline behaviour.
Edit this file to tune the disease scanner without touching model code.
"""

# ─── Confidence tiers ────────────────────────────────────────────────────────
# ConvGeM-NeXt (49 classes) with T=0.5 temperature scaling produces calibrated
# softmax peaks in these ranges on real leaf images:
#   Clearly diseased leaf   → 35–85%  (calibrated)
#   Ambiguous / dirty image → 20–35%  (calibrated)
#   Wrong domain image      → 10–20%  (calibrated)
#
# Disease is reported only when softmax probability >= CONFIRMED_THRESHOLD.
# Values between UNCERTAIN_THRESHOLD and CONFIRMED_THRESHOLD show "Needs
# Verification".  Below UNCERTAIN_THRESHOLD → "Unknown / Uncertain".
CONFIRMED_THRESHOLD   = 0.30   # ≥30% calibrated → Confirmed disease
UNCERTAIN_THRESHOLD   = 0.15   # 15–30% calibrated → Needs verification
# Below UNCERTAIN_THRESHOLD → Uncertain
# NOTE: These thresholds match T=0.5 temperature scaling in disease_agent.py.
# If you refit T using ml/fit_temperature.py, adjust these values accordingly.

# ─── Leaf validation ─────────────────────────────────────────────────────────
LEAF_CONFIDENCE_THRESHOLD = 0.50   # LeafValidator fused score cutoff

# ─── OpenCV lesion segmentation ──────────────────────────────────────────────
# Minimum leaf area (pixels) to bother with segmentation
MIN_LEAF_PIXELS = 500
# Minimum lesion pixels to report a non-zero area
MIN_LESION_PIXELS = 50
# Severity thresholds (% of leaf area covered by lesions)
SEVERITY_LOW_MAX        = 5.0     # < 5%   → Low
SEVERITY_MODERATE_MAX   = 20.0    # 5–20%  → Moderate
                                   # > 20%  → Severe

# ─── Visual similarity booster ───────────────────────────────────────────────
# When ConvGeM-NeXt softmax is below CONFIRMED_THRESHOLD, the pipeline uses
# HSV/LAB colour-profile similarity to boost or demote confidence for disease
# classes that have known colour signatures.
USE_COLOUR_SIMILARITY_BOOST = True
# A boost can raise confidence by at most this fraction of the gap to threshold
BOOST_SCALE = 0.35

# ─── Development logging ─────────────────────────────────────────────────────
DEBUG_LOGGING = True   # Set False in production to silence per-image logs
