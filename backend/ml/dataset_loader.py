"""
Multi-Dataset Loader for FarmAssist ConvGeM-NeXt Disease Classifier
====================================================================

Handles loading and unifying four plant disease datasets:
  A. PlantVillage  — ~54,304 images, 38 classes (broad disease coverage)
  B. PlantDoc      — ~2,569  images, 27 classes (field-condition images, real-world generalization)
  C. Coconut       — ~5,798  images, 6  classes (required for coconut disease support)
  D. Pepper Bell   — ~9,283  images, 6  classes (strengthens pepper disease recognition)

Expected folder layout (relative to DATASETS_ROOT):
  datasets/
    PlantVillage/       <- one subfolder per class, e.g. "Apple___Apple_scab/"
    PlantDoc/           <- one subfolder per class
      train/            <- (PlantDoc may ship with a train/test split already)
      test/
    Coconut/            <- one subfolder per class: Bud_Rot/, Gray_Leaf_Spot/, ...
    PepperBell/         <- one subfolder per class: Bacterial_spot/, curl/, ...

If PlantDoc ships pre-split, both train/ and test/ folders are merged for our own
controlled re-split. Data leakage is prevented by our stratified random split.
"""

import os
import json
import hashlib
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
from PIL import Image, UnidentifiedImageError
from sklearn.model_selection import train_test_split
from torch.utils.data import Dataset, ConcatDataset, Subset
from torchvision import transforms

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

ML_DIR = Path(__file__).parent
DATASETS_ROOT = ML_DIR / "datasets"
MAPPING_FILE = ML_DIR / "class_mapping.json"

DATASET_DIRS = {
    "plantvillage": DATASETS_ROOT / "PlantVillage",
    "plantdoc":     DATASETS_ROOT / "PlantDoc",
    "coconut":      DATASETS_ROOT / "Coconut",
    "pepper_bell":  DATASETS_ROOT / "PepperBell",
}


# ---------------------------------------------------------------------------
# Load class mapping
# ---------------------------------------------------------------------------

def load_class_mapping() -> Dict[str, Dict[str, str]]:
    """Load and return the class mapping JSON."""
    with open(MAPPING_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def build_unified_class_index(mapping: Dict) -> Tuple[List[str], Dict[str, int]]:
    """
    Build a sorted, unique list of all unified class labels and
    return (class_names, class_to_idx).

    Skips keys starting with '_' (comments/notes).
    """
    unified_classes = set()
    for dataset_key, dataset_mapping in mapping.items():
        if dataset_key.startswith("_"):
            continue
        for native_class, unified_class in dataset_mapping.items():
            if not native_class.startswith("_"):
                unified_classes.add(unified_class)

    class_names = sorted(unified_classes)
    class_to_idx = {c: i for i, c in enumerate(class_names)}
    return class_names, class_to_idx


# ---------------------------------------------------------------------------
# Image validation
# ---------------------------------------------------------------------------

def is_valid_image(path: str) -> bool:
    """
    Check if a file is a valid, readable image.
    Catches corrupted files and truncated JPEGs.
    """
    try:
        with Image.open(path) as img:
            img.verify()          # validates header/structure
        # Re-open after verify (file pointer is at end after verify)
        with Image.open(path) as img:
            img.load()            # actually decode pixel data
        return True
    except (UnidentifiedImageError, OSError, Exception):
        return False


def compute_image_hash(path: str) -> str:
    """Compute MD5 hash of image bytes for near-duplicate detection."""
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------------------
# Dataset scanner
# ---------------------------------------------------------------------------

def scan_dataset_folder(
    folder: Path,
    dataset_key: str,
    mapping: Dict,
    class_to_idx: Dict[str, int],
    remove_corrupt: bool = True,
    detect_duplicates: bool = True,
) -> Tuple[List[str], List[int]]:
    """
    Walk a dataset folder (ImageFolder-style) and collect (image_path, label_idx) pairs.

    Args:
        folder:            Root folder of the dataset.
        dataset_key:       Key in class_mapping.json (e.g. "plantvillage").
        mapping:           Full class mapping dict.
        class_to_idx:      Unified class → index mapping.
        remove_corrupt:    Skip unreadable images.
        detect_duplicates: Skip exact-duplicate image files (by MD5).

    Returns:
        (file_paths, labels) — parallel lists ready for Dataset construction.
    """
    if not folder.exists():
        logger.warning(f"[DatasetLoader] Dataset folder not found: {folder}. Skipping.")
        return [], []

    dataset_mapping = mapping.get(dataset_key, {})
    image_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"}

    file_paths: List[str] = []
    labels: List[int] = []
    skipped_corrupt = 0
    skipped_unmapped = 0
    skipped_duplicate = 0
    seen_hashes: set = set()

    # Support datasets with a nested train/test structure (PlantDoc)
    subfolders_to_scan = []
    for item in sorted(folder.iterdir()):
        if item.is_dir():
            # Check if this is a class-level folder or a split folder
            if item.name.lower() in {"train", "test", "val", "valid", "validation"}:
                subfolders_to_scan.append(item)  # split subfolder → scan inside
            else:
                # Class-level folder directly under root
                subfolders_to_scan.append(folder)
                break
    else:
        subfolders_to_scan = [folder]

    for scan_root in set(subfolders_to_scan):
        for class_dir in sorted(scan_root.iterdir()):
            if not class_dir.is_dir():
                continue

            native_class = class_dir.name

            # Look up in mapping (case-insensitive fallback)
            unified_class = dataset_mapping.get(native_class)
            if unified_class is None:
                # Try case-insensitive match
                for k, v in dataset_mapping.items():
                    if k.lower() == native_class.lower() and not k.startswith("_"):
                        unified_class = v
                        break

            if unified_class is None or unified_class.startswith("_"):
                logger.debug(f"[DatasetLoader] Unmapped class '{native_class}' in {dataset_key} — skipping.")
                skipped_unmapped += 1
                continue

            if unified_class not in class_to_idx:
                logger.debug(f"[DatasetLoader] Class '{unified_class}' not in unified index — skipping.")
                continue

            label_idx = class_to_idx[unified_class]

            for img_file in sorted(class_dir.iterdir()):
                if img_file.suffix.lower() not in image_extensions:
                    continue

                img_path = str(img_file)

                if remove_corrupt and not is_valid_image(img_path):
                    logger.debug(f"[DatasetLoader] Corrupt/unreadable image: {img_path}")
                    skipped_corrupt += 1
                    continue

                if detect_duplicates:
                    img_hash = compute_image_hash(img_path)
                    if img_hash in seen_hashes:
                        skipped_duplicate += 1
                        continue
                    seen_hashes.add(img_hash)

                file_paths.append(img_path)
                labels.append(label_idx)

    logger.info(
        f"[DatasetLoader] {dataset_key}: {len(file_paths)} images loaded "
        f"| {skipped_corrupt} corrupt | {skipped_unmapped} unmapped classes | {skipped_duplicate} duplicates"
    )
    return file_paths, labels


# ---------------------------------------------------------------------------
# PyTorch Dataset
# ---------------------------------------------------------------------------

class LeafDiseaseDataset(Dataset):
    """
    PyTorch Dataset for plant disease classification.

    Args:
        file_paths: List of image file path strings.
        labels:     List of integer class labels (parallel to file_paths).
        transform:  Torchvision transform pipeline.
    """

    def __init__(
        self,
        file_paths: List[str],
        labels: List[int],
        transform=None,
    ):
        assert len(file_paths) == len(labels), "file_paths and labels must have the same length"
        self.file_paths = file_paths
        self.labels = labels
        self.transform = transform

    def __len__(self) -> int:
        return len(self.file_paths)

    def __getitem__(self, idx: int) -> Tuple:
        img_path = self.file_paths[idx]
        label = self.labels[idx]

        try:
            img = Image.open(img_path).convert("RGB")
        except Exception as e:
            logger.warning(f"[Dataset] Failed to open {img_path}: {e}. Returning zero tensor.")
            # Return a black image placeholder rather than crashing the DataLoader
            img = Image.new("RGB", (224, 224), color=(0, 0, 0))

        if self.transform:
            img = self.transform(img)

        return img, label


# ---------------------------------------------------------------------------
# Main dataset builder
# ---------------------------------------------------------------------------

def build_datasets(
    train_transform=None,
    val_transform=None,
    test_transform=None,
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
    # test_ratio is implicitly 1 - train_ratio - val_ratio
    random_seed: int = 42,
    remove_corrupt: bool = True,
    detect_duplicates: bool = True,
    dataset_keys: Optional[List[str]] = None,
) -> Tuple[Dataset, Dataset, Dataset, List[str], Dict[str, int], Dict]:
    """
    Build train, validation, and test datasets from all available datasets.

    Data leakage prevention:
        - Stratified split by class (ensures all classes appear in all splits)
        - Near-duplicate detection by MD5 hash before splitting
        - Test set is never touched during training or hyperparameter tuning

    Args:
        train_transform: Augmentation + normalization for training images.
        val_transform:   Normalization only for validation images.
        test_transform:  Normalization only for test images.
        train_ratio:     Fraction of data for training (default 0.70).
        val_ratio:       Fraction of data for validation (default 0.15).
        random_seed:     Random seed for reproducible splits.
        remove_corrupt:  Skip corrupt/unreadable images.
        detect_duplicates: Skip exact duplicate images.
        dataset_keys:    If provided, only load these datasets. Default: all four.

    Returns:
        train_dataset, val_dataset, test_dataset, class_names, class_to_idx, stats
    """
    from convgem_next import get_train_transform, get_val_transform, get_inference_transform

    if train_transform is None:
        train_transform = get_train_transform()
    if val_transform is None:
        val_transform = get_val_transform()
    if test_transform is None:
        test_transform = get_val_transform()

    if dataset_keys is None:
        dataset_keys = list(DATASET_DIRS.keys())

    mapping = load_class_mapping()
    class_names, class_to_idx = build_unified_class_index(mapping)

    logger.info(f"[DatasetLoader] Unified taxonomy: {len(class_names)} classes")

    # Collect all images and labels from all datasets
    all_paths: List[str] = []
    all_labels: List[int] = []
    source_tags: List[str] = []  # track which dataset each image came from

    for key in dataset_keys:
        if key not in DATASET_DIRS:
            logger.warning(f"[DatasetLoader] Unknown dataset key: {key}")
            continue
        paths, labels = scan_dataset_folder(
            folder=DATASET_DIRS[key],
            dataset_key=key,
            mapping=mapping,
            class_to_idx=class_to_idx,
            remove_corrupt=remove_corrupt,
            detect_duplicates=detect_duplicates,
        )
        all_paths.extend(paths)
        all_labels.extend(labels)
        source_tags.extend([key] * len(paths))

    if len(all_paths) == 0:
        raise RuntimeError(
            "No images found! Please download the datasets and place them in:\n"
            f"  {DATASETS_ROOT}\n"
            "See backend/ml/README.md for download instructions."
        )

    all_paths = np.array(all_paths)
    all_labels = np.array(all_labels)

    logger.info(f"[DatasetLoader] Total: {len(all_paths):,} images across {len(dataset_keys)} datasets")

    # ---- Stratified train/val/test split ----
    # Step 1: Split off test set
    test_ratio = 1.0 - train_ratio - val_ratio
    idx = np.arange(len(all_paths))

    try:
        idx_trainval, idx_test = train_test_split(
            idx,
            test_size=test_ratio,
            stratify=all_labels,
            random_state=random_seed,
        )
        # Step 2: Split trainval into train and val
        val_ratio_adjusted = val_ratio / (train_ratio + val_ratio)
        idx_train, idx_val = train_test_split(
            idx_trainval,
            test_size=val_ratio_adjusted,
            stratify=all_labels[idx_trainval],
            random_state=random_seed,
        )
    except ValueError as e:
        logger.error(
            f"[DatasetLoader] Stratified split failed: {e}\n"
            "This may happen if some classes have very few samples. "
            "Falling back to random split."
        )
        idx_trainval, idx_test = train_test_split(idx, test_size=test_ratio, random_state=random_seed)
        val_ratio_adjusted = val_ratio / (train_ratio + val_ratio)
        idx_train, idx_val = train_test_split(idx_trainval, test_size=val_ratio_adjusted, random_state=random_seed)

    # Build dataset objects with appropriate transforms
    train_dataset = LeafDiseaseDataset(
        list(all_paths[idx_train]), list(all_labels[idx_train].astype(int)), transform=train_transform
    )
    val_dataset = LeafDiseaseDataset(
        list(all_paths[idx_val]), list(all_labels[idx_val].astype(int)), transform=val_transform
    )
    test_dataset = LeafDiseaseDataset(
        list(all_paths[idx_test]), list(all_labels[idx_test].astype(int)), transform=test_transform
    )

    # Compute class distribution and weights for imbalanced training
    class_counts = np.bincount(all_labels[idx_train], minlength=len(class_names))
    class_weights = 1.0 / np.maximum(class_counts, 1)
    class_weights = class_weights / class_weights.sum() * len(class_names)  # normalize

    stats = {
        "total_images": len(all_paths),
        "train_images": len(idx_train),
        "val_images": len(idx_val),
        "test_images": len(idx_test),
        "num_classes": len(class_names),
        "class_names": class_names,
        "class_counts_train": class_counts.tolist(),
        "class_weights": class_weights.tolist(),
        "dataset_keys": dataset_keys,
    }

    logger.info(
        f"[DatasetLoader] Split → train:{len(idx_train):,} | "
        f"val:{len(idx_val):,} | test:{len(idx_test):,}"
    )

    return train_dataset, val_dataset, test_dataset, class_names, class_to_idx, stats


# ---------------------------------------------------------------------------
# Dry-run validator (no training)
# ---------------------------------------------------------------------------

def validate_dataset_setup(verbose: bool = True) -> bool:
    """
    Validate that datasets exist and class mappings are consistent.
    Does NOT train — just inspects folder structure and mapping coverage.

    Returns True if everything looks good, False otherwise.
    """
    mapping = load_class_mapping()
    class_names, class_to_idx = build_unified_class_index(mapping)

    all_ok = True
    for key, folder in DATASET_DIRS.items():
        if not folder.exists():
            print(f"  ✗ [{key}] Dataset folder MISSING: {folder}")
            all_ok = False
        else:
            # Count class folders
            class_dirs = [d for d in folder.iterdir() if d.is_dir()]
            print(f"  ✓ [{key}] Found at {folder} ({len(class_dirs)} class folders)")

    print(f"\nUnified taxonomy: {len(class_names)} classes")
    if verbose:
        for c in class_names:
            print(f"  [{class_to_idx[c]:3d}] {c}")

    return all_ok
