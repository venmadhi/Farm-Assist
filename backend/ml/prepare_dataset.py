"""
FarmAssist Master Dataset Preparation Orchestrator
===================================================
Runs the complete dataset preparation pipeline:
1. Ingestion / Download check (`download_datasets.py`)
2. Image verification, cleaning, duplicate detection, splitting (`validate_datasets.py`)
3. Metrics reporting (`dataset_summary.py`)
"""

import sys
import json
import yaml
from pathlib import Path

BACKEND_ML_DIR = Path(__file__).parent
sys.path.insert(0, str(BACKEND_ML_DIR))

from download_datasets import main as download_main
from validate_datasets import run_validation_and_splitting
from dataset_summary import generate_summary

CONFIG_PATH = BACKEND_ML_DIR / "config.yaml"
with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

REPORTS_DIR = Path(config["data"]["reports_dir"]).resolve()


def run_pipeline():
    print("\n" + "="*50)
    print(" FarmAssist ConvGeM-NeXt Dataset Pipeline ")
    print("="*50)

    # 1. Download / Ingest
    print("\n[Step 1/3] Checking & Downloading Datasets...")
    download_main()

    # 2. Validate, Clean, Split
    print("\n[Step 2/3] Validating Images, Cleaning, Splitting...")
    run_validation_and_splitting()

    # 3. Reports & Summary
    print("\n[Step 3/3] Generating Dataset Summary & Class Distributions...")
    generate_summary()

    # Read dataset_summary.json to display final banner
    summary_path = REPORTS_DIR / "dataset_summary.json"
    if summary_path.exists():
        with open(summary_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        datasets = data.get("datasets", {})
        pv_cnt = datasets.get("PlantVillage", 0)
        pd_cnt = datasets.get("PlantDoc", 0)
        cc_cnt = datasets.get("Coconut", 0)
        pe_cnt = datasets.get("Pepper", 0)

        print("\n====================================")
        print("FarmAssist Dataset Preparation Done")
        print("====================================\n")
        print(f"PlantVillage: {pv_cnt} images")
        print(f"PlantDoc: {pd_cnt} images")
        print(f"Coconut: {cc_cnt} images")
        print(f"Pepper: {pe_cnt} images\n")
        print(f"Total valid images: {data.get('total_images', 0)}\n")
        print(f"Final classes: {data.get('classes', 0)}\n")
        print(f"Train: {data.get('train', 0)}")
        print(f"Validation: {data.get('validation', 0)}")
        print(f"Test: {data.get('test', 0)}\n")
        print(f"Corrupt images: {data.get('corrupt', 0)}")
        print(f"Duplicates removed: {data.get('duplicates', 0)}\n")
        print("# Ready for ConvGeM-NeXt training.\n")
    else:
        print("\n[!] Preparation finished, but dataset_summary.json was not found.")


if __name__ == "__main__":
    run_pipeline()
