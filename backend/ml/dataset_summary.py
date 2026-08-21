"""
FarmAssist Dataset Summary & Distribution Reporter
===================================================
Generates dataset_summary.json and class_distribution.csv from unified_metadata.csv.
Computes real dataset metrics, class balance ratios, and split counts.
"""

import json
import yaml
import pandas as pd
from pathlib import Path

# Load pipeline configuration
CONFIG_PATH = Path(__file__).parent / "config.yaml"
with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

METADATA_DIR = Path(config["data"]["metadata_dir"]).resolve()
REPORTS_DIR = Path(config["data"]["reports_dir"]).resolve()
REJECTED_DIR = Path(config["data"]["rejected_dir"]).resolve() / "corrupt"

UNIFIED_CSV = METADATA_DIR / "unified_metadata.csv"
DUP_REPORT_CSV = REPORTS_DIR / "duplicate_report.csv"


def generate_summary():
    if not UNIFIED_CSV.exists():
        print(f"Unified metadata file ({UNIFIED_CSV}) not found. Please run validation first.")
        return

    df = pd.read_csv(UNIFIED_CSV)
    dup_df = pd.read_csv(DUP_REPORT_CSV) if DUP_REPORT_CSV.exists() else pd.DataFrame()

    total_images = len(df)
    corrupt_count = len(list(REJECTED_DIR.glob("*"))) if REJECTED_DIR.exists() else 0
    duplicate_count = len(dup_df)

    datasets_count = df["dataset"].value_counts().to_dict()
    crops_count = df["crop"].value_counts().to_dict()
    class_counts = df["unified_class"].value_counts()

    train_count = int((df["split"] == "train").sum())
    val_count = int((df["split"] == "val").sum())
    test_count = int((df["split"] == "test").sum())

    min_class_size = int(class_counts.min()) if not class_counts.empty else 0
    max_class_size = int(class_counts.max()) if not class_counts.empty else 0
    imbalance_ratio = round(max_class_size / max(min_class_size, 1), 2)

    # Class distribution CSV
    dist_records = []
    for u_class, total in class_counts.items():
        subset = df[df["unified_class"] == u_class]
        display_name = subset["display_name"].iloc[0] if "display_name" in subset.columns else u_class
        crop_name = subset["crop"].iloc[0] if "crop" in subset.columns else "unknown"
        
        c_train = (subset["split"] == "train").sum()
        c_val = (subset["split"] == "val").sum()
        c_test = (subset["split"] == "test").sum()

        dist_records.append({
            "unified_class": u_class,
            "display_name": display_name,
            "crop": crop_name,
            "total_count": int(total),
            "train_count": int(c_train),
            "val_count": int(c_val),
            "test_count": int(c_test),
            "percentage_of_total": round((total / max(total_images, 1)) * 100, 2)
        })

    dist_df = pd.DataFrame(dist_records)
    dist_csv_path = REPORTS_DIR / "class_distribution.csv"
    dist_df.to_csv(dist_csv_path, index=False)

    summary_json = {
        "total_images": total_images,
        "datasets": datasets_count,
        "crops": crops_count,
        "classes": len(class_counts),
        "train": train_count,
        "validation": val_count,
        "test": test_count,
        "corrupt": corrupt_count,
        "duplicates": duplicate_count,
        "class_imbalance": {
            "min_class_size": min_class_size,
            "max_class_size": max_class_size,
            "imbalance_ratio": imbalance_ratio
        }
    }

    summary_json_path = REPORTS_DIR / "dataset_summary.json"
    with open(summary_json_path, "w", encoding="utf-8") as f:
        json.dump(summary_json, f, indent=2)

    print("\n==========================================")
    print(" Dataset Summary Report Generated")
    print("==========================================")
    print(f"Summary JSON : {summary_json_path}")
    print(f"Class Dist   : {dist_csv_path}")
    print(f"Total Valid  : {total_images}")
    print(f"Total Classes: {len(class_counts)}")
    print(f"Imbalance    : {imbalance_ratio}:1")
    print("==========================================\n")


if __name__ == "__main__":
    generate_summary()
