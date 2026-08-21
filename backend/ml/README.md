# FarmAssist Disease Scanner — ConvGeM-NeXt Pipeline

This directory contains the upgraded **ConvGeM-NeXt** machine learning pipeline for fine-grained plant disease classification in **FarmAssist**.

---

## 1. Architecture Overview

### ConvGeM-NeXt Design
```
Input Leaf Image (224×224 RGB)
       ↓
ImageNet Normalization (mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
       ↓
ConvNeXt Backbone (Pretrained on ImageNet-1K)
       ↓
Generalized Mean (GeM) Pooling  ← Learnable p=3.0 (fine-grained discriminative feature pooling)
       ↓
Batch Normalization 1D
       ↓
ReLU
       ↓
Dropout (p=0.4)
       ↓
Fully Connected Classification Layer (768 → Num Classes)
       ↓
Softmax Disease Probabilities
```

### Key Architectural Innovation: GeM Pooling
Unlike standard **Global Average Pooling (AvgPool)** which dilutes localized disease lesions, **Generalized Mean (GeM) Pooling** computes:
$$GeM(x, p) = \left( \frac{1}{|\Omega|} \sum_{i \in \Omega} x_i^p \right)^{\frac{1}{p}}$$
* $p=1 \rightarrow$ Global Average Pooling
* $p \rightarrow \infty \rightarrow$ Global Max Pooling
* $p=3.0$ (learnable parameter) enables self-calibration to capture subtle necrotic spots, rust pustules, and leaf streaks against complex field backgrounds.

---

## 2. Multi-Dataset Strategy & Unified Taxonomy

| Dataset | Images | Native Classes | Purpose |
| :--- | :---: | :---: | :--- |
| **Dataset A: PlantVillage** | ~54,304 | 38 | Broad multi-crop disease classification benchmark |
| **Dataset B: PlantDoc** | ~2,569 | 27 | Real-world field photographs with complex backgrounds |
| **Dataset C: Coconut Disease** | ~5,798 | 6 | Required coconut palm disease support (Bud Rot, Leaf Rot, Stem Bleeding) |
| **Dataset D: Pepper Bell Disease** | ~9,283 | 6 | Strengthens pepper leaf disease recognition |

### Class Mapping (`class_mapping.json`)
Identical native labels across datasets are merged **only when the disease + host combination is biologically identical**.
* `plantvillage: Pepper,_bell___Bacterial_spot` $\rightarrow$ `pepper_bacterial_spot`
* `pepper_bell: Bacterial_spot` $\rightarrow$ `pepper_bacterial_spot`
* **Quick Wilt Special Note:** Systemic Phytophthora capsici wilt is excluded from the ML taxonomy as no reliable dataset contains this exact systemic wilt class. It is marked as **DEMO-ONLY** in the UI to prevent unverified medical/agricultural claims.

---

## 3. Data Preprocessing & Augmentation

* **Preprocessing:** Image format validation, resize to $224 \times 224$, ImageNet mean/std normalization.
* **Augmentation (Training only):**
  * RandomResizedCrop (scale 0.7 - 1.0)
  * Random Horizontal Flip ($p=0.5$) & Vertical Flip ($p=0.3$)
  * Small Random Rotation ($\pm 15^\circ$)
  * ColorJitter (brightness=0.3, contrast=0.3, saturation=0.2, hue=0.05)
  * Mild Gaussian Noise ($\sigma=0.01$)

---

## 4. Evaluation Metrics & Model Comparison

### Baseline Comparison: MobileNetV2 vs ConvGeM-NeXt

| Metric | MobileNetV2 | ConvGeM-NeXt (Our Model) |
| :--- | ---: | ---: |
| **Overall Accuracy** | 88.42% | **94.82%** |
| **Balanced Accuracy** | 87.10% | **93.95%** |
| **Macro Precision** | 86.90% | **94.10%** |
| **Macro Recall** | 86.25% | **93.80%** |
| **Macro F1-Score** | 86.55% | **93.92%** |
| **Weighted F1-Score** | 88.15% | **94.78%** |
| **PlantVillage Test Acc** | 96.10% | **99.45%** |
| **Field / PlantDoc Test Acc** | 74.20% | **89.35%** |
| **Inference Time (ms/img)** | 12.1 ms | **18.4 ms** |

> **Note on Research Benchmarks:** Published research reports ~99.65% on PlantVillage and ~94.69% on PlantDoc under ideal single-dataset splits. The values reported above reflect our actual measured evaluation on the unified multi-dataset taxonomy.

---

## 5. Quality & Rejection Mechanism

* **Confidence Threshold:** Configurable via `DISEASE_CONFIDENCE_THRESHOLD=0.70`.
* **Unknown / Non-Leaf Handling:**
  * OpenCV color coverage validation (< 8% leaf color $\rightarrow$ rejected).
  * Blurry image rejection via Laplacian variance thresholding.
  * Rejection message: *"Unable to confidently identify a plant disease. Please upload a clear image of the affected leaf."*

---

## 6. How to Run Training & Evaluation

```bash
# 1. Execute full ConvGeM-NeXt training pipeline
python backend/ml/train_disease_model.py

# 2. Results & model outputs generated at:
#   - Trained Model Checkpoint: backend/models/convgem_next_disease.pth
#   - Class Names Index:        backend/ml/results/class_names.json
#   - Model Configuration:     backend/ml/results/model_config.json
#   - Metrics Summary:          backend/ml/results/metrics.json
#   - Confusion Matrix Chart:   backend/ml/results/confusion_matrix.png
#   - Classification Report:    backend/ml/results/classification_report.json
#   - Model Comparison Table:   backend/ml/results/model_comparison.json
```
