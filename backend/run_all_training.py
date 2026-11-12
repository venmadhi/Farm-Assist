import subprocess
import sys
import time

def main():
    start_time = time.time()
    print("=== Starting Sequential Training Pipeline ===")
    
    print("\n[1/2] Training Crop Classifier (TensorFlow)...")
    try:
        subprocess.run([sys.executable, "ml/train_crop_classifier.py"], check=True)
        print("[1/2] Crop Classifier training completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"[1/2] Crop Classifier training FAILED with exit code {e.returncode}.")
        sys.exit(1)

    print("\n[2/2] Training YOLO Disease Model (PyTorch)...")
    try:
        subprocess.run([sys.executable, "train_yolo.py"], check=True)
        print("[2/2] YOLO training completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"[2/2] YOLO training FAILED with exit code {e.returncode}.")
        sys.exit(1)

    print("\n=== All Training Completed Successfully ===")
    end_time = time.time()
    duration_minutes = (end_time - start_time) / 60
    print(f"Total training time: {duration_minutes:.2f} minutes")

if __name__ == "__main__":
    main()
