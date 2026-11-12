import os
import json
import tensorflow as tf
import numpy as np
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

BASE_DIR = os.path.dirname(__file__)
TRAIN_DIR = os.path.join(BASE_DIR, "datasets", "crop_classification", "train")
MODEL_PATH = os.path.join(BASE_DIR, "models", "crop_classifier.keras")
METRICS_PATH = os.path.join(BASE_DIR, "models", "crop_metrics.json")

def evaluate():
    if not os.path.exists(MODEL_PATH) or not os.path.exists(TRAIN_DIR):
        print("Missing model or training dataset.")
        return

    print("Loading model...")
    model = tf.keras.models.load_model(MODEL_PATH)
    
    print("Loading validation dataset from 20% split of training data...")
    val_dataset = tf.keras.utils.image_dataset_from_directory(
        TRAIN_DIR,
        validation_split=0.2,
        subset="validation",
        seed=1337,
        shuffle=False,
        batch_size=32,
        image_size=(224, 224)
    )
    
    class_names = val_dataset.class_names
    
    y_true = []
    y_pred = []
    
    print("Evaluating...")
    for images, labels in val_dataset:
        # DO NOT apply preprocess_input here because it's baked into the model or native to EfficientNetV2
        preds = model.predict(images, verbose=0)
        y_true.extend(labels.numpy())
        y_pred.extend(np.argmax(preds, axis=1))
        
    accuracy = accuracy_score(y_true, y_pred)
    precision = precision_score(y_true, y_pred, average='macro', zero_division=0)
    recall = recall_score(y_true, y_pred, average='macro', zero_division=0)
    f1 = f1_score(y_true, y_pred, average='macro', zero_division=0)
    
    metrics = {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "num_classes": len(class_names)
    }
    
    print(metrics)
    with open(METRICS_PATH, 'w') as f:
        json.dump(metrics, f, indent=4)
    print("Saved to crop_metrics.json")

if __name__ == "__main__":
    evaluate()
