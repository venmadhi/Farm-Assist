"""
ConvGeM-NeXt Architecture for Plant Disease Classification
===========================================================

Architecture:
    Input Leaf Image (224×224 or 384×384 RGB)
        ↓
    ImageNet Normalization (mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ↓
    ConvNeXt Backbone (pretrained on ImageNet-1K/22K)
        ↓
    Generalized Mean (GeM) Pooling  ← key innovation over AvgPool
        ↓
    Batch Normalization 1D
        ↓
    ReLU
        ↓
    Dropout (p=0.4)
        ↓
    Fully Connected Classification Layer (backbone_dim → num_classes)
        ↓
    Softmax Disease Probabilities (applied during inference)

GeM Pooling Formula:
    GeM(x, p) = (1/|Ω| · Σ x_i^p)^(1/p)
    - p=1 → Average Pooling
    - p→∞ → Max Pooling
    - p≈3 (default, learnable) → optimal for fine-grained visual recognition

Design rationale:
    - ConvNeXt is a pure-CNN architecture that matches or exceeds Vision Transformers
      on image classification while being simpler to deploy (no attention memory).
    - GeM pooling retains more spatial discriminative information than global AvgPool,
      making it significantly better for fine-grained tasks like distinguishing disease
      subtypes from leaf photographs with complex backgrounds.
    - The learnable parameter p allows the network to self-calibrate pooling behavior
      per training run and dataset.

Reference:
    "Towards Robust Plant Disease Classification using ConvGeM-NeXt" —
    adapted architecture combining ConvNeXt (Liu et al., 2022) with
    GeM pooling (Radenović et al., 2019).
"""

import os
import sys

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
if sys.platform == "win32":
    import site
    site_packages = site.getsitepackages()
    for sp in site_packages:
        torch_lib = os.path.join(sp, "torch", "lib")
        if os.path.exists(torch_lib):
            try:
                os.add_dll_directory(torch_lib)
            except Exception:
                pass

import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision.models as models
from typing import Optional, Tuple


# ---------------------------------------------------------------------------
# Generalized Mean Pooling
# ---------------------------------------------------------------------------

class GeMPooling(nn.Module):
    """
    Generalized Mean Pooling layer.

    Applies: GeM(x) = (1/|Ω| * Σ x_i^p)^(1/p)

    Args:
        p (float): Initial pooling power. Default=3.
                   p=1 → AvgPool, p→∞ → MaxPool.
        eps (float): Small constant for numerical stability.
        learnable (bool): If True, p is a trainable parameter.
    """

    def __init__(self, p: float = 3.0, eps: float = 1e-6, learnable: bool = True):
        super(GeMPooling, self).__init__()
        self.eps = eps
        if learnable:
            self.p = nn.Parameter(torch.ones(1) * p)
        else:
            self.p = p

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: Feature map of shape (B, C, H, W)
        Returns:
            Pooled tensor of shape (B, C, 1, 1)
        """
        return F.avg_pool2d(
            x.clamp(min=self.eps).pow(self.p),
            kernel_size=(x.size(-2), x.size(-1))
        ).pow(1.0 / self.p)

    def extra_repr(self) -> str:
        p_val = self.p.item() if isinstance(self.p, nn.Parameter) else self.p
        return f"p={p_val:.4f}, eps={self.eps}, learnable={isinstance(self.p, nn.Parameter)}"


# ---------------------------------------------------------------------------
# ConvGeM-NeXt Model
# ---------------------------------------------------------------------------

class ConvGeMNeXt(nn.Module):
    """
    ConvGeM-NeXt: ConvNeXt backbone with Generalized Mean Pooling head.

    This architecture is designed for fine-grained plant disease classification
    with improved generalization to real-world field photographs.

    Args:
        num_classes (int): Number of disease classes.
        variant (str): ConvNeXt variant — 'tiny', 'small', 'base', 'large'.
        pretrained (bool): Use ImageNet pretrained weights.
        gem_p (float): Initial GeM pooling power.
        dropout_rate (float): Dropout probability before classifier FC.
        freeze_backbone (bool): If True, freeze backbone weights initially.
    """

    # Output feature dimensions for each ConvNeXt variant
    VARIANT_DIMS = {
        "tiny":  768,
        "small": 768,
        "base":  1024,
        "large": 1536,
    }

    def __init__(
        self,
        num_classes: int,
        variant: str = "tiny",
        pretrained: bool = True,
        gem_p: float = 3.0,
        dropout_rate: float = 0.4,
        freeze_backbone: bool = True,
    ):
        super(ConvGeMNeXt, self).__init__()

        if variant not in self.VARIANT_DIMS:
            raise ValueError(
                f"Unknown ConvNeXt variant '{variant}'. "
                f"Choose from: {list(self.VARIANT_DIMS.keys())}"
            )

        self.variant = variant
        self.num_classes = num_classes
        self.feature_dim = self.VARIANT_DIMS[variant]

        # ---- 1. ConvNeXt Backbone ----
        weights_map = {
            "tiny":  models.ConvNeXt_Tiny_Weights.IMAGENET1K_V1 if pretrained else None,
            "small": models.ConvNeXt_Small_Weights.IMAGENET1K_V1 if pretrained else None,
            "base":  models.ConvNeXt_Base_Weights.IMAGENET1K_V1 if pretrained else None,
            "large": models.ConvNeXt_Large_Weights.IMAGENET1K_V1 if pretrained else None,
        }
        builder_map = {
            "tiny":  models.convnext_tiny,
            "small": models.convnext_small,
            "base":  models.convnext_base,
            "large": models.convnext_large,
        }

        backbone_full = builder_map[variant](weights=weights_map[variant])

        # Remove the original classifier head; keep only the feature extraction stages
        # ConvNeXt in torchvision has: features (Sequential) + avgpool + classifier
        self.backbone = backbone_full.features  # Output shape: (B, C, H', W')

        # Optionally freeze backbone for Phase 1 training (head-only)
        if freeze_backbone:
            self.freeze_backbone()

        # ---- 2. GeM Pooling ----
        # Replaces the default avgpool with learnable GeM
        self.gem_pool = GeMPooling(p=gem_p, eps=1e-6, learnable=True)

        # ---- 3. Classifier Head ----
        # BN → ReLU → Dropout → FC
        self.head = nn.Sequential(
            nn.Flatten(),                                           # (B, C, 1, 1) → (B, C)
            nn.BatchNorm1d(self.feature_dim),
            nn.ReLU(inplace=True),
            nn.Dropout(p=dropout_rate),
            nn.Linear(self.feature_dim, num_classes),
        )

        # Store config for serialization
        self.config = {
            "num_classes": num_classes,
            "variant": variant,
            "pretrained": pretrained,
            "gem_p": gem_p,
            "dropout_rate": dropout_rate,
        }

    def freeze_backbone(self):
        """Freeze all backbone parameters (Phase 1 training — head only)."""
        for param in self.backbone.parameters():
            param.requires_grad = False

    def unfreeze_top_stages(self, num_stages: int = 2):
        """
        Progressively unfreeze the top N stages of ConvNeXt for fine-tuning.

        ConvNeXt backbone stages in torchvision:
            backbone[0] = DownsampleLayer (stem)
            backbone[1] = Stage 1
            backbone[2] = DownsampleLayer
            backbone[3] = Stage 2
            backbone[4] = DownsampleLayer
            backbone[5] = Stage 3   ← unfreeze these last
            backbone[6] = DownsampleLayer
            backbone[7] = Stage 4   ← unfreeze these first

        Args:
            num_stages: How many top stages to unfreeze (1-4).
        """
        # First freeze everything
        for param in self.backbone.parameters():
            param.requires_grad = False

        # Then unfreeze from the back
        stage_indices = list(range(7, max(7 - num_stages * 2, -1), -1))
        for idx in stage_indices:
            if idx < len(self.backbone):
                for param in self.backbone[idx].parameters():
                    param.requires_grad = True

    def unfreeze_all(self):
        """Unfreeze entire backbone for full fine-tuning."""
        for param in self.backbone.parameters():
            param.requires_grad = True

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass.
        Args:
            x: Input tensor of shape (B, 3, H, W) — normalized RGB images
        Returns:
            Logits tensor of shape (B, num_classes)
        """
        features = self.backbone(x)   # (B, C, H', W')
        pooled = self.gem_pool(features)  # (B, C, 1, 1)
        logits = self.head(pooled)    # (B, num_classes)
        return logits

    def predict_with_confidence(
        self,
        x: torch.Tensor,
        top_k: int = 3
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Run inference and return top-k class predictions with probabilities.

        Args:
            x: Input tensor (B, 3, H, W)
            top_k: Number of top predictions to return

        Returns:
            probs: Full probability tensor (B, num_classes)
            top_k_probs: Top-k probabilities (B, k)
            top_k_indices: Top-k class indices (B, k)
        """
        self.eval()
        with torch.no_grad():
            logits = self.forward(x)
            probs = F.softmax(logits, dim=1)
            top_k_probs, top_k_indices = torch.topk(probs, k=min(top_k, self.num_classes), dim=1)
        return probs, top_k_probs, top_k_indices

    def get_trainable_params(self) -> int:
        """Return count of trainable parameters."""
        return sum(p.numel() for p in self.parameters() if p.requires_grad)

    def get_total_params(self) -> int:
        """Return total parameter count."""
        return sum(p.numel() for p in self.parameters())


# ---------------------------------------------------------------------------
# Model Factory
# ---------------------------------------------------------------------------

def build_convgemnext(
    num_classes: int,
    variant: str = "tiny",
    pretrained: bool = True,
    gem_p: float = 3.0,
    dropout_rate: float = 0.4,
    freeze_backbone: bool = True,
    checkpoint_path: Optional[str] = None,
    device: Optional[torch.device] = None,
) -> ConvGeMNeXt:
    """
    Build a ConvGeM-NeXt model, optionally loading from checkpoint.

    Args:
        num_classes: Number of plant disease classes.
        variant: ConvNeXt size variant ('tiny', 'small', 'base', 'large').
        pretrained: Load ImageNet pretrained ConvNeXt weights.
        gem_p: GeM pooling power initial value.
        dropout_rate: Dropout before classifier layer.
        freeze_backbone: Whether to freeze backbone initially.
        checkpoint_path: If provided, load weights from this .pth file.
        device: Torch device to place model on.

    Returns:
        ConvGeMNeXt model instance.
    """
    if device is None:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    model = ConvGeMNeXt(
        num_classes=num_classes,
        variant=variant,
        pretrained=pretrained,
        gem_p=gem_p,
        dropout_rate=dropout_rate,
        freeze_backbone=freeze_backbone,
    )

    if checkpoint_path is not None:
        checkpoint = torch.load(checkpoint_path, map_location=device)
        # Support both raw state_dict and wrapped checkpoint dicts
        if isinstance(checkpoint, dict) and "model_state_dict" in checkpoint:
            model.load_state_dict(checkpoint["model_state_dict"])
        else:
            model.load_state_dict(checkpoint)
        print(f"[ConvGeM-NeXt] Loaded weights from: {checkpoint_path}")

    model = model.to(device)

    total = model.get_total_params()
    trainable = model.get_trainable_params()
    print(
        f"[ConvGeM-NeXt] variant={variant} | classes={num_classes} | "
        f"params={total:,} total | {trainable:,} trainable"
    )

    return model


# ---------------------------------------------------------------------------
# Preprocessing transform (for inference)
# ---------------------------------------------------------------------------

def get_inference_transform(input_size: int = 224):
    """
    Returns the preprocessing transform pipeline for inference.
    Uses the same ImageNet normalization as training (no augmentation).
    """
    from torchvision import transforms
    return transforms.Compose([
        transforms.Resize((input_size, input_size)),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225]
        ),
    ])


def get_train_transform(input_size: int = 224):
    """
    Returns the augmentation + preprocessing pipeline for training.
    Only biologically plausible augmentations are applied.
    """
    from torchvision import transforms
    return transforms.Compose([
        transforms.RandomResizedCrop(input_size, scale=(0.7, 1.0)),
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.RandomVerticalFlip(p=0.3),         # leaves can be upside-down
        transforms.RandomRotation(degrees=15),
        transforms.ColorJitter(
            brightness=0.3,
            contrast=0.3,
            saturation=0.2,
            hue=0.05,                                  # small hue shift — disease color matters
        ),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225]
        ),
        # Mild Gaussian noise via a lambda (applied on tensor)
        transforms.Lambda(
            lambda x: x + torch.randn_like(x) * 0.01  # σ=0.01, very mild
        ),
    ])


def get_val_transform(input_size: int = 224):
    """
    Returns the preprocessing transform for validation/test (no augmentation).
    """
    from torchvision import transforms
    return transforms.Compose([
        transforms.Resize(int(input_size * 1.14)),     # slight upscale for center crop
        transforms.CenterCrop(input_size),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225]
        ),
    ])
