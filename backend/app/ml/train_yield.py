import os
import pickle
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor, ExtraTreesRegressor
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import r2_score, mean_absolute_error
from xgboost import XGBRegressor

def train_yield_model():
    print("\n--- YIELD PREDICTION MODEL TRAINING ---")
    
    # 1. READ THE ENRICHED DATASET
    ml_dir = os.path.dirname(os.path.abspath(__file__))
    dataset_path = os.path.join(ml_dir, 'enriched_kerala_crops.csv')
    if not os.path.exists(dataset_path):
        print("Enriched dataset not found. Generating...")
        from .train_crop import download_and_enrich_dataset
        df = download_and_enrich_dataset()
    else:
        df = pd.read_csv(dataset_path)

    n_samples = len(df)
    np.random.seed(42)

    # 2. GENERATE TARGET VARIABLE (YIELD KG PER ACRE) WITH REALISTIC CORRELATIONS
    # Yield is heavily dependent on moisture/rainfall, organic carbon, pH (closer to 6.5 is higher), NPK values, and crop type.
    base_yields = {
        'rice': 2200.0, 'maize': 2500.0, 'chickpea': 800.0, 'kidneybeans': 750.0,
        'pigeonpeas': 700.0, 'mothbeans': 550.0, 'mungbean': 600.0, 'blackgram': 620.0,
        'lentil': 650.0, 'pomegranate': 5500.0, 'banana': 7500.0, 'mango': 4500.0,
        'grapes': 8000.0, 'watermelon': 12000.0, 'muskmelon': 9500.0, 'apple': 9000.0,
        'orange': 6500.0, 'papaya': 11000.0, 'coconut': 4500.0, 'cotton': 1000.0,
        'jute': 2800.0, 'coffee': 900.0, 'tea': 4000.0, 'cardamom': 250.0
    }
    
    yields = []
    for idx, row in df.iterrows():
        crop = row['crop']
        base = base_yields.get(crop, 1200.0)
        
        # pH factor: optimal is around 6.5, yield drops at extremes
        ph_factor = 1.0 - 0.12 * abs(row['ph'] - 6.5) ** 2
        
        # Organic Carbon factor: higher carbon = higher yield
        oc_factor = 0.8 + 0.35 * row['organic_carbon']
        
        # NPK factor (simple deviation from baseline 100)
        npk_total = row['nitrogen'] + row['phosphorus'] + row['potassium']
        npk_factor = 0.85 + 0.001 * npk_total
        
        # Random environmental noise
        noise = np.random.normal(1.0, 0.05)
        
        predicted_yield = base * max(0.4, ph_factor) * max(0.5, oc_factor) * npk_factor * noise
        yields.append(round(predicted_yield, 2))
        
    df['yield_kg_per_acre'] = yields

    # 3. ENCODE CATEGORICALS
    categorical_cols = ['soil_type', 'water_availability', 'irrigation_type', 'previous_crop', 'season', 'market_demand']
    encoders = {}
    
    df_encoded = df.copy()
    for col in categorical_cols:
        le = LabelEncoder()
        df_encoded[col] = le.fit_transform(df[col])
        encoders[col] = le
        
    # Crop label encoder
    crop_le = LabelEncoder()
    df_encoded['crop'] = crop_le.fit_transform(df['crop'])
    encoders['crop'] = crop_le
    
    # Split
    X = df_encoded.drop(columns=['crop', 'yield_kg_per_acre', 'current_price', 'market_demand'])
    y = df_encoded['yield_kg_per_acre']
    
    feature_names = list(X.columns)
    
    # Incorporate crop name back into the training features since it's the strongest predictor of base yield!
    X['crop'] = df_encoded['crop']
    feature_names.append('crop')

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # 4. TRAINING REGRESSORS
    models = {
        "RandomForestRegressor": RandomForestRegressor(n_estimators=100, max_depth=12, random_state=42),
        "ExtraTreesRegressor": ExtraTreesRegressor(n_estimators=100, max_depth=12, random_state=42),
        "XGBRegressor": XGBRegressor(n_estimators=100, max_depth=6, learning_rate=0.1, random_state=42)
    }

    best_model_name = None
    best_r2 = -1.0
    best_model_obj = None

    for name, model in models.items():
        print(f"Training {name}...")
        model.fit(X_train, y_train)
        preds = model.predict(X_test)
        r2 = r2_score(y_test, preds)
        mae = mean_absolute_error(y_test, preds)
        print(f"-> {name} R2 Score: {r2:.4f} | MAE: {mae:.2f} kg/acre")
        
        if r2 > best_r2:
            best_r2 = r2
            best_model_name = name
            best_model_obj = model

    print(f"\nWinner: {best_model_name} with R2 Score {best_r2:.4f}")

    # 5. SAVE MODEL BUNDLE
    model_data = {
        'model': best_model_obj,
        'feature_names': feature_names,
        'encoders': encoders,
        'r2_score': best_r2,
        'model_name': best_model_name
    }
    
    model_path = os.path.join(ml_dir, 'yield_model.pkl')
    with open(model_path, 'wb') as f:
        pickle.dump(model_data, f)
        
    print(f"Saved yield regressor to: {model_path}")

if __name__ == '__main__':
    train_yield_model()
