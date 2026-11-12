import os
import json
import tensorflow as tf
from tensorflow.keras.applications import EfficientNetV2B0
from tensorflow.keras.layers import Dense, GlobalAveragePooling2D, Dropout, BatchNormalization
from tensorflow.keras.models import Model
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
import numpy as np

# Set paths
BASE_DIR = os.path.dirname(__file__)
DATASET_DIR = os.path.join(BASE_DIR, "datasets", "crop_classification")
TRAIN_DIR = os.path.join(DATASET_DIR, "train") # We ONLY use train dir and split it!
MODEL_DIR = os.path.join(BASE_DIR, "models")
MODEL_PATH = os.path.join(MODEL_DIR, "crop_classifier.keras")
CLASSES_PATH = os.path.join(MODEL_DIR, "crop_classes.json")

# Hyperparameters
IMG_SIZE = (224, 224)
BATCH_SIZE = 32
INITIAL_EPOCHS = 10
FINE_TUNE_EPOCHS = 10

def main():
    print("Setting up Crop Classification Training Pipeline (EfficientNetV2B0)...")
    
    os.makedirs(MODEL_DIR, exist_ok=True)
    
    # Data pipelines using a unified train directory to guarantee aligned classes
    print("Loading datasets with 80/20 validation split...")
    train_dataset = tf.keras.utils.image_dataset_from_directory(
        TRAIN_DIR,
        validation_split=0.2,
        subset="training",
        seed=1337,
        shuffle=True,
        batch_size=BATCH_SIZE,
        image_size=IMG_SIZE
    )
    
    val_dataset = tf.keras.utils.image_dataset_from_directory(
        TRAIN_DIR,
        validation_split=0.2,
        subset="validation",
        seed=1337,
        shuffle=False,
        batch_size=BATCH_SIZE,
        image_size=IMG_SIZE
    )
    
    class_names = train_dataset.class_names
    print(f"Discovered {len(class_names)} classes: {class_names}")
    
    # Save class names mapping
    with open(CLASSES_PATH, 'w') as f:
        json.dump(class_names, f, indent=4)
        
    print(f"Class mapping saved to {CLASSES_PATH}")
    
    # Optimize datasets for performance
    AUTOTUNE = tf.data.AUTOTUNE
    train_dataset = train_dataset.prefetch(buffer_size=AUTOTUNE)
    val_dataset = val_dataset.prefetch(buffer_size=AUTOTUNE)
    
    # Data augmentation
    data_augmentation = tf.keras.Sequential([
        tf.keras.layers.RandomFlip('horizontal'),
        tf.keras.layers.RandomRotation(0.2),
        tf.keras.layers.RandomZoom(0.2),
    ])
    
    # Base model (EfficientNetV2B0 expects inputs in [0, 255] and handles scaling internally)
    base_model = EfficientNetV2B0(
        input_shape=IMG_SIZE + (3,),
        include_top=False,
        weights='imagenet'
    )
    base_model.trainable = False # Freeze base model initially
    
    # Build model according to specified architecture
    inputs = tf.keras.Input(shape=IMG_SIZE + (3,))
    x = data_augmentation(inputs)
    x = base_model(x, training=False)
    x = GlobalAveragePooling2D()(x)
    
    # Dropout (0.3 - 0.5)
    x = Dropout(0.3)(x)
    
    # Dense Layer (ReLU) - 256 units
    x = Dense(256, activation='relu')(x)
    
    # Dropout (Optional)
    x = Dropout(0.3)(x)
    
    # Output Dense Layer (N Crop Classes, Softmax)
    outputs = Dense(len(class_names), activation='softmax')(x)
    
    model = Model(inputs, outputs)
    
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=1e-3),
        loss=tf.keras.losses.SparseCategoricalCrossentropy(),
        metrics=['accuracy']
    )
    
    # Callbacks
    early_stop = EarlyStopping(
        monitor='val_loss', 
        patience=3, 
        restore_best_weights=True
    )
    
    print("--- Phase 1: Training top layer ---")
    history = model.fit(
        train_dataset,
        validation_data=val_dataset,
        epochs=INITIAL_EPOCHS,
        callbacks=[early_stop]
    )
    
    print("--- Phase 2: Fine-tuning top 20 layers ---")
    base_model.trainable = True
    
    # Freeze all layers except the top 20
    for layer in base_model.layers[:-20]:
        layer.trainable = False
        
    # Recompile with lower learning rate for fine-tuning
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=1e-4),
        loss=tf.keras.losses.SparseCategoricalCrossentropy(),
        metrics=['accuracy']
    )
    
    history_fine = model.fit(
        train_dataset,
        validation_data=val_dataset,
        epochs=FINE_TUNE_EPOCHS,
        callbacks=[early_stop]
    )
    
    print("Evaluating final model on validation set...")
    val_loss, val_acc = model.evaluate(val_dataset)
    print(f"Final Validation Accuracy: {val_acc:.4f} | Validation Loss: {val_loss:.4f}")
    
    # Save model
    model.save(MODEL_PATH)
    print(f"EfficientNetV2 model saved to: {MODEL_PATH}")

if __name__ == "__main__":
    main()
