"""
FarmAssist Multi-Dataset Downloader
=====================================
Downloads and verifies the 4 public datasets for FarmAssist Disease Scanner:
1. PlantVillage (via Kaggle API)
2. PlantDoc (via Git Clone)
3. Coconut Tree Disease Dataset (Mendeley / Direct / Manual)
4. Pepper Bell Leaf Disease Dataset (Mendeley / Direct / Manual)

Safe to run multiple times without re-downloading existing datasets.
"""

import os
import sys
import shutil
import subprocess
import urllib.request
import zipfile
import yaml
from pathlib import Path

# Load pipeline configuration
CONFIG_PATH = Path(__file__).parent / "config.yaml"
with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

RAW_DIR = Path(config["data"]["raw_dir"]).resolve()
RAW_DIR.mkdir(parents=True, exist_ok=True)

PLANTVILLAGE_DIR = RAW_DIR / "plantvillage"
PLANTDOC_DIR = RAW_DIR / "plantdoc"
COCONUT_DIR = RAW_DIR / "coconut"
PEPPER_DIR = RAW_DIR / "pepper"


def get_dir_size_mb(path: Path) -> float:
    total_bytes = 0
    if path.exists():
        for p in path.rglob("*"):
            if p.is_file():
                total_bytes += p.stat().st_size
    return round(total_bytes / (1024 * 1024), 2)


def count_images_and_classes(path: Path):
    if not path.exists():
        return 0, []
    supported_ext = set(config["data"]["supported_extensions"])
    image_files = [p for p in path.rglob("*") if p.is_file() and p.suffix.lower() in supported_ext]
    classes = sorted(list({p.parent.name for p in image_files if p.parent != path}))
    return len(image_files), classes


def check_kaggle_credentials() -> bool:
    """Check standard Kaggle credential locations or env vars."""
    if os.environ.get("KAGGLE_USERNAME") and os.environ.get("KAGGLE_KEY"):
        return True
    kaggle_json = Path.home() / ".kaggle" / "kaggle.json"
    return kaggle_json.exists()


def download_plantvillage() -> tuple[bool, str]:
    PLANTVILLAGE_DIR.mkdir(parents=True, exist_ok=True)
    img_count, classes = count_images_and_classes(PLANTVILLAGE_DIR)
    if img_count > 100:
        return True, f"PlantVillage already present ({img_count} images, {len(classes)} classes, {get_dir_size_mb(PLANTVILLAGE_DIR)} MB)"

    print("\n--- [1/4] Processing PlantVillage Dataset ---")
    if not check_kaggle_credentials():
        msg = (
            "Kaggle credentials not found.\n"
            "To download PlantVillage automatically:\n"
            "  1. Create a Kaggle account at https://www.kaggle.com\n"
            "  2. Go to Account Settings -> Create New API Token (kaggle.json)\n"
            "  3. Place kaggle.json in ~/.kaggle/ or set environment variables KAGGLE_USERNAME and KAGGLE_KEY\n"
            "  Alternatively, manually extract PlantVillage images into: data/raw/plantvillage/"
        )
        print(msg)
        return False, "Kaggle credentials missing. Manual setup required."

    try:
        import kaggle
        print("Downloading PlantVillage via Kaggle API (abdallahalidev/plantvillage-dataset)...")
        kaggle.api.dataset_download_files("abdallahalidev/plantvillage-dataset", path=str(PLANTVILLAGE_DIR), unzip=True)
        img_count, classes = count_images_and_classes(PLANTVILLAGE_DIR)
        return True, f"Successfully downloaded PlantVillage ({img_count} images, {len(classes)} classes)"
    except Exception as e:
        print(f"Kaggle API download failed: {e}")
        return False, f"Kaggle download failed: {e}"


def remove_readonly(func, path, exc_info):
    import stat
    os.chmod(path, stat.S_IWRITE)
    func(path)

def download_plantdoc() -> tuple[bool, str]:
    PLANTDOC_DIR.mkdir(parents=True, exist_ok=True)
    img_count, classes = count_images_and_classes(PLANTDOC_DIR)
    if img_count > 50:
        return True, f"PlantDoc already present ({img_count} images, {len(classes)} classes, {get_dir_size_mb(PLANTDOC_DIR)} MB)"

    print("\n--- [2/4] Processing PlantDoc Dataset ---")
    git_installed = shutil.which("git") is not None
    if not git_installed:
        print("Please clone https://github.com/pratikkayal/PlantDoc-Dataset into: data/raw/plantdoc/")
        return False, "Git unavailable. Manual clone required."

    try:
        if PLANTDOC_DIR.exists() and img_count == 0:
            shutil.rmtree(PLANTDOC_DIR, onerror=remove_readonly)
        print("Cloning PlantDoc repository from https://github.com/pratikkayal/PlantDoc-Dataset...")
        cmd = ["git", "clone", "https://github.com/pratikkayal/PlantDoc-Dataset.git", str(PLANTDOC_DIR)]
        res = subprocess.run(cmd, capture_output=True, text=True)
        img_count, classes = count_images_and_classes(PLANTDOC_DIR)
        if res.returncode == 0 or img_count > 50:
            return True, f"Successfully cloned PlantDoc ({img_count} images, {len(classes)} classes)"
        else:
            return False, f"Git clone notice: {res.stderr.strip() if res.stderr else 'clone incomplete'}"
    except Exception as e:
        return False, f"Notice cloning PlantDoc: {e}"


def download_mendeley_dataset(name: str, target_dir: Path, direct_url: str) -> tuple[bool, str]:
    target_dir.mkdir(parents=True, exist_ok=True)
    
    # Check for zip files inside target_dir or root data/raw/
    zips = list(target_dir.glob("*.zip"))
    if zips:
        for z in zips:
            print(f"Extracting manual archive: {z.name} ...")
            try:
                with zipfile.ZipFile(z, 'r') as zip_ref:
                    zip_ref.extractall(target_dir)
            except Exception as ez:
                print(f"Failed to extract {z.name}: {ez}")

    img_count, classes = count_images_and_classes(target_dir)
    if img_count > 20:
        return True, f"{name} dataset present ({img_count} images, {len(classes)} classes, {get_dir_size_mb(target_dir)} MB)"

    print(f"\n--- Processing {name} Dataset ---")
    if direct_url:
        try:
            zip_path = target_dir / f"{name.lower()}.zip"
            print(f"Attempting download for {name} from direct URL...")
            urllib.request.urlretrieve(direct_url, zip_path)
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(target_dir)
            zip_path.unlink(missing_ok=True)
            img_count, classes = count_images_and_classes(target_dir)
            if img_count > 0:
                return True, f"Downloaded {name} ({img_count} images)"
        except Exception as e:
            print(f"Direct download for {name} not accessible: {e}")

    # Clear instructions if direct download not available
    print(f"\n[!] Manual Dataset Download Required for {name}:")
    print(f"  1. Download dataset archive from official source.")
    print(f"  2. Extract or place the ZIP file into: data/raw/{name.lower()}/")
    print(f"  3. Re-run this script to automatically ingest and preprocess.")

    return False, f"Manual download required. Place files into data/raw/{name.lower()}/"


def main():
    print("==========================================")
    print(" FarmAssist Multi-Dataset Ingestion Status")
    print("==========================================")

    pv_status, pv_msg = download_plantvillage()
    pd_status, pd_msg = download_plantdoc()
    cc_status, cc_msg = download_mendeley_dataset("Coconut", COCONUT_DIR, "https://data.mendeley.com/public-files/datasets/gh56wbsnj5/files/1/file_downloaded")
    pe_status, pe_msg = download_mendeley_dataset("Pepper", PEPPER_DIR, "https://data.mendeley.com/public-files/datasets/w9drvtxg9g/files/1/file_downloaded")

    print("\n==========================================")
    print(" Dataset Availability Summary")
    print("==========================================")
    print(f"[{'OK' if pv_status else '!'}] PlantVillage -- {pv_msg}")
    print(f"[{'OK' if pd_status else '!'}] PlantDoc      -- {pd_msg}")
    print(f"[{'OK' if cc_status else '!'}] Coconut       -- {cc_msg}")
    print(f"[{'OK' if pe_status else '!'}] Pepper        -- {pe_msg}")
    print("==========================================\n")


if __name__ == "__main__":
    main()
