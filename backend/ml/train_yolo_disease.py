import os
import argparse
from pathlib import Path
try:
    from ultralytics import YOLO
    import torch
except ImportError:
    print("ultralytics or torch package is missing. Install with: pip install ultralytics torch")
    exit(1)

def main():
    parser = argparse.ArgumentParser(description="Train YOLO11 Disease Classifier")
    parser.add_argument("--model", type=str, default="yolo11n-cls.pt", help="Pretrained YOLO classification model")
    parser.add_argument("--data", type=str, default=r"E:\leaf_disease_yolo_processed", help="Path to processed classification dataset")
    parser.add_argument("--epochs", type=int, default=50, help="Number of training epochs")
    parser.add_argument("--imgsz", type=int, default=224, help="Image size for training")
    parser.add_argument("--batch", type=int, default=-1, help="Batch size (-1 for auto)")
    parser.add_argument("--patience", type=int, default=15, help="Early stopping patience")
    parser.add_argument("--project", type=str, default=r"E:\leaf_disease_yolo_training", help="Project dir to save outputs")
    args = parser.parse_args()

    data_path = Path(args.data).resolve()
    if not data_path.exists():
        print(f"Error: Dataset path {data_path} does not exist.")
        exit(1)

    device = "0" if torch.cuda.is_available() else "cpu"
    print(f"Device set to: {device} (CUDA available: {torch.cuda.is_available()})")

    print(f"Initializing YOLO Model: {args.model}")
    model = YOLO(args.model)

    print(f"Starting Training on Dataset: {data_path}")
    print(f"Params: epochs={args.epochs}, imgsz={args.imgsz}, batch={args.batch}, device={device}")

    # Start training with suitable crop leaf augmentation
    results = model.train(
        data=str(data_path),
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        device=device,
        patience=args.patience,
        project=args.project,
        name="models",
        exist_ok=True,
        pretrained=True,
        # Augmentations suitable for leaves:
        fliplr=0.5,
        flipud=0.5,
        degrees=10.0,
        scale=0.2,
        shear=0.0,
        perspective=0.0001,
        bgr=0.0,
        mixup=0.0,
        copy_paste=0.0,
        auto_augment="randaugment"
    )
    
    print("Training Completed.")
    best_model_path = Path(args.project) / "models" / "weights" / "best.pt"
    
    if best_model_path.exists():
        # Rename to yolo11_disease_best.pt to meet requirement
        final_path = Path(args.project) / "models" / "yolo11_disease_best.pt"
        if final_path.exists():
            final_path.unlink()
        os.rename(best_model_path, final_path)
        print(f"Best model successfully saved to: {final_path}")
    else:
        print("Warning: Best model weights not found at expected path.")

if __name__ == "__main__":
    main()
