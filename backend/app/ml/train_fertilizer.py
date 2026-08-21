import os
import pickle
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, classification_report
from xgboost import XGBClassifier

def download_and_save_dataset():
    url = "https://raw.githubusercontent.com/Lanchavi/AgroTechh/main/Fertilizer%20Prediction.csv"
    ml_dir = os.path.dirname(os.path.abspath(__file__))
    local_path = os.path.join(ml_dir, 'fertilizer_dataset.csv')
    
    print(f"Downloading real fertilizer dataset from: {url}...")
    try:
        df = pd.read_csv(url)
        df.to_csv(local_path, index=False)
        print(f"Dataset saved to: {local_path} (Shape: {df.shape})")
        return df
    except Exception as e:
        print(f"Error downloading dataset: {e}")
        if os.path.exists(local_path):
            print(f"Loading local dataset from: {local_path}")
            return pd.read_csv(local_path)
        else:
            raise FileNotFoundError("Could not download or find fertilizer dataset locally.")

def train_fertilizer_model():
    print("\n--- ML FERTILIZER RECOMMENDATION MODEL TRAINING ---")
    
    # 1. Load dataset
    df = download_and_save_dataset()
    
    # Standardize column naming
    df.rename(columns={
        'Temparature': 'temperature',
        'Humidity ': 'humidity',
        'Humidity': 'humidity',
        'Moisture': 'moisture',
        'Soil Type': 'soil_type',
        'Crop Type': 'crop_type',
        'Nitrogen': 'nitrogen',
        'Potassium': 'potassium',
        'Phosphorous': 'phosphorus',
        'Fertilizer Name': 'fertilizer'
    }, inplace=True)
    
    # Clean any whitespace in column names
    df.columns = df.columns.str.strip()
    
    # 2. Encode categorical variables
    encoders = {}
    df_encoded = df.copy()
    
    categorical_cols = ['soil_type', 'crop_type']
    for col in categorical_cols:
        le = LabelEncoder()
        df_encoded[col] = le.fit_transform(df[col])
        encoders[col] = le
        
    target_le = LabelEncoder()
    df_encoded['fertilizer'] = target_le.fit_transform(df['fertilizer'])
    encoders['fertilizer'] = target_le
    
    # 3. Define features & target
    features = ['temperature', 'humidity', 'moisture', 'soil_type', 'crop_type', 'nitrogen', 'potassium', 'phosphorus']
    X = df_encoded[features]
    y = df_encoded['fertilizer']
    
    # Train/Test Split (Stratified to maintain class distributions)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    # 4. Compare models
    models = {
        "LogisticRegression": LogisticRegression(max_iter=1000, random_state=42),
        "RandomForest": RandomForestClassifier(n_estimators=100, max_depth=8, random_state=42),
        "XGBoost": XGBClassifier(n_estimators=100, max_depth=6, learning_rate=0.1, random_state=42)
    }
    
    best_model_name = None
    best_accuracy = 0.0
    best_model_obj = None
    
    print("\n--- FERTILIZER MODEL COMPARISON ---")
    for name, model in models.items():
        print(f"Training {name}...")
        model.fit(X_train, y_train)
        preds = model.predict(X_test)
        acc = accuracy_score(y_test, preds)
        print(f"-> {name} Accuracy: {acc * 100:.2f}%")
        
        if acc > best_accuracy:
            best_accuracy = acc
            best_model_name = name
            best_model_obj = model
            
    print(f"\nWinning Model: {best_model_name} with Accuracy {best_accuracy * 100:.2f}%")
    
    # Evaluation Report for the Champion Model
    champion_preds = best_model_obj.predict(X_test)
    print("\nClassification Report (Champion Model):")
    print(classification_report(y_test, champion_preds, target_names=target_le.classes_))
    
    # 5. Save the trained bundle
    ml_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(ml_dir, 'fertilizer_model.pkl')
    
    model_bundle = {
        'model': best_model_obj,
        'model_name': best_model_name,
        'feature_names': features,
        'encoders': encoders,
        'accuracy': best_accuracy,
        'X_train_sample': X_train.head(20)  # Safe reference sample for SHAP explainers
    }
    
    with open(model_path, 'wb') as f:
        pickle.dump(model_bundle, f)
    print(f"Successfully saved model to: {model_path}")
    return best_model_name, best_accuracy, len(X_train) + len(X_test)

if __name__ == '__main__':
    train_fertilizer_model()
