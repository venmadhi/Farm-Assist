import os
import argparse
from pathlib import Path
from ultralytics import YOLO

def main():
    parser = argparse.ArgumentParser(description="Evaluate YOLO11 Disease Classifier")
    parser.add_argument("--model", type=str, default=r"E:\leaf_disease_yolo_training\models\yolo11_disease_best.pt", help="Path to trained model")
    parser.add_argument("--data", type=str, default=r"E:\leaf_disease_yolo_processed", help="Path to processed classification dataset")
    parser.add_argument("--split", type=str, default="test", help="Dataset split to evaluate (val or test)")
    args = parser.parse_args()

    model_path = Path(args.model)
    if not model_path.exists():
        print(f"Error: Model not found at {model_path}")
        return

    print(f"Loading model from: {model_path}")
    model = YOLO(str(model_path))

    print(f"Evaluating on {args.split} split from: {args.data}")
    # ultralytics uses split parameter in val() method for classification
    metrics = model.val(data=args.data, split=args.split)
    
    print("\n" + "=" * 50)
    print("Evaluation Results")
    print("=" * 50)
    
    # YOLO classification metrics
    # top1 and top5 are attributes of the metrics object
    if hasattr(metrics, 'top1'):
        print(f"Top-1 Accuracy: {metrics.top1:.4f}")
    if hasattr(metrics, 'top5'):
        print(f"Top-5 Accuracy: {metrics.top5:.4f}")
        
    print(f"\nDetailed metrics, confusion matrix, and class results are saved by ultralytics in the runs/classify/val directory.")
    print("Review the confusion_matrix.png to see which diseases are commonly confused.")
    print("=" * 50)

if __name__ == "__main__":
    main()
