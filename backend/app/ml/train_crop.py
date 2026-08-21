import os
import pickle
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier, GradientBoostingClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, classification_report
from xgboost import XGBClassifier

def download_and_enrich_dataset():
    # 1. READ REAL KAGGLE CROP RECOMMENDATION DATASET (2200 records)
    url = "https://raw.githubusercontent.com/gabbygab1233/Crop-Recommender/main/Crop_recommendation.csv"
    print(f"Downloading real crop recommendation dataset from: {url}...")
    try:
        df = pd.read_csv(url)
        print(f"Successfully loaded raw dataset. Shape: {df.shape}")
    except Exception as e:
        print(f"Error downloading dataset: {e}. Falling back to generating simulated raw data.")
        # Fallback to local csv or generate structure if offline
        df = generate_fallback_raw_data()
    
    # Standardize column names
    df.rename(columns={
        'N': 'nitrogen', 'P': 'phosphorus', 'K': 'potassium', 
        'temperature': 'temp', 'humidity': 'humidity', 
        'ph': 'ph', 'rainfall': 'rainfall', 'label': 'crop'
    }, inplace=True)
    
    # 2. ENRICH WITH KERALA-SPECIFIC INDUSTRIAL AGRICULTURAL VARIABLES
    print("Enriching dataset with advanced soil, irrigation, history, and market variables...")
    np.random.seed(42)
    n_samples = len(df)
    
    # Soil types based on crop needs
    soil_types = []
    for idx, row in df.iterrows():
        c = row['crop']
        if c in ['rice', 'paddy', 'coconut', 'jute']:
            soil_types.append(np.random.choice(['Clayey', 'Laterite', 'Sandy Loam'], p=[0.6, 0.3, 0.1]))
        elif c in ['coffee', 'tea', 'cardamom']:
            soil_types.append(np.random.choice(['Acidic Forest Loam', 'Laterite'], p=[0.7, 0.3]))
        else:
            soil_types.append(np.random.choice(['Laterite', 'Clayey', 'Red Loam', 'Sandy Loam'], p=[0.4, 0.2, 0.2, 0.2]))
    df['soil_type'] = soil_types
    
    # Organic Carbon (%)
    # Correlated with Nitrogen
    df['organic_carbon'] = np.clip(df['nitrogen'] * 0.008 + np.random.normal(0.1, 0.05, n_samples), 0.1, 2.5)
    
    # Micronutrients (ppm)
    df['boron'] = np.clip(df['ph'] * 0.05 + np.random.normal(0.2, 0.08, n_samples), 0.05, 1.5)
    df['iron'] = np.clip(10.0 - df['ph'] * 1.1 + np.random.normal(2.0, 0.5, n_samples), 0.5, 15.0)
    df['zinc'] = np.clip(df['phosphorus'] * 0.015 + np.random.normal(0.5, 0.1, n_samples), 0.1, 3.5)
    
    # Water Availability & Irrigation types
    water_avail = []
    irrigation = []
    for idx, row in df.iterrows():
        rain = row['rainfall']
        if rain > 180.0:
            water_avail.append('high')
            irrigation.append(np.random.choice(['rainfed', 'manual'], p=[0.8, 0.2]))
        elif rain > 95.0:
            water_avail.append('medium')
            irrigation.append(np.random.choice(['drip', 'sprinkler', 'manual'], p=[0.4, 0.3, 0.3]))
        else:
            water_avail.append('low')
            irrigation.append(np.random.choice(['drip', 'sprinkler'], p=[0.7, 0.3]))
    df['water_availability'] = water_avail
    df['irrigation_type'] = irrigation
    
    # Previous Crop (to train crop rotation logic)
    # Give it realistic rotation rules
    prev_crops = []
    crops_pool = df['crop'].unique()
    for idx, row in df.iterrows():
        c = row['crop']
        # Rotate legumes with cereals
        if c == 'rice':
            prev_crops.append(np.random.choice(['lentil', 'blackgram', 'mungbean', 'fallow'], p=[0.3, 0.3, 0.3, 0.1]))
        elif c in ['lentil', 'blackgram', 'mungbean']:
            prev_crops.append('rice')
        else:
            # Random selection excluding current crop
            pool = [cp for cp in crops_pool if cp != c]
            prev_crops.append(np.random.choice(pool))
    df['previous_crop'] = prev_crops
    
    # Seasons (Kharif, Rabi, Summer) based on rainfall & temp
    seasons = []
    for idx, row in df.iterrows():
        rain = row['rainfall']
        t = row['temp']
        if rain > 120.0:
            seasons.append('Kharif') # Southwest Monsoon
        elif t < 23.0:
            seasons.append('Rabi') # Cool Winter
        else:
            seasons.append('Summer') # Zaid / Hot
    df['season'] = seasons
    
    # Market metrics
    market_demands = []
    prices = []
    base_prices = {
        'rice': 30.0, 'maize': 22.0, 'chickpea': 55.0, 'kidneybeans': 65.0,
        'pigeonpeas': 75.0, 'mothbeans': 48.0, 'mungbean': 70.0, 'blackgram': 72.0,
        'lentil': 68.0, 'pomegranate': 120.0, 'banana': 42.0, 'mango': 85.0,
        'grapes': 110.0, 'watermelon': 18.0, 'muskmelon': 25.0, 'apple': 150.0,
        'orange': 60.0, 'papaya': 35.0, 'coconut': 14.0, 'cotton': 62.0,
        'jute': 32.0, 'coffee': 170.0, 'tea': 120.0, 'cardamom': 1450.0
    }
    for idx, row in df.iterrows():
        c = row['crop']
        base = base_prices.get(c, 50.0)
        prices.append(round(base * np.random.uniform(0.9, 1.15), 2))
        market_demands.append(np.random.choice(['High', 'Medium', 'Low'], p=[0.5, 0.4, 0.1]))
    df['current_price'] = prices
    df['market_demand'] = market_demands
    
    # Preprocess missing values or outliers (dataset is generally clean, but good practice)
    df.fillna(method='ffill', inplace=True)
    
    # Save the cleaned and enriched dataset
    ml_dir = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(ml_dir, exist_ok=True)
    df.to_csv(os.path.join(ml_dir, 'enriched_kerala_crops.csv'), index=False)
    print("Enriched dataset saved to: enriched_kerala_crops.csv")
    
    return df

def generate_fallback_raw_data():
    print("Generating synthetic fallback dataset with realistic crop profiles...")
    np.random.seed(42)
    crops = ['rice', 'maize', 'banana', 'coconut', 'coffee', 'tea', 'cardamom', 'blackgram']
    
    profiles = {
        'rice':     {'n': 80,  'p': 48,  'k': 48,  'ph': 6.2,  'rain': 2000, 'temp': 27.0, 'hum': 80},
        'coconut':  {'n': 55,  'p': 32,  'k': 115, 'ph': 6.5,  'rain': 1700, 'temp': 30.0, 'hum': 75},
        'banana':   {'n': 105, 'p': 58,  'k': 140, 'ph': 6.8,  'rain': 1400, 'temp': 28.0, 'hum': 80},
        'coffee':   {'n': 68,  'p': 38,  'k': 72,  'ph': 6.2,  'rain': 1600, 'temp': 25.0, 'hum': 70},
        'tea':      {'n': 80,  'p': 32,  'k': 60,  'ph': 4.8,  'rain': 2650, 'temp': 18.0, 'hum': 85},
        'cardamom': {'n': 70,  'p': 45,  'k': 85,  'ph': 5.8,  'rain': 2750, 'temp': 19.0, 'hum': 90},
        'maize':    {'n': 90,  'p': 50,  'k': 40,  'ph': 6.0,  'rain': 900,  'temp': 26.0, 'hum': 65},
        'blackgram':{'n': 40,  'p': 40,  'k': 30,  'ph': 7.0,  'rain': 750,  'temp': 29.0, 'hum': 60}
    }
    
    data = []
    for _ in range(1200):
        c = np.random.choice(crops)
        prof = profiles[c]
        data.append({
            'nitrogen': float(np.random.normal(prof['n'], 12)),
            'phosphorus': float(np.random.normal(prof['p'], 8)),
            'potassium': float(np.random.normal(prof['k'], 15)),
            'temp': float(np.random.normal(prof['temp'], 2.5)),
            'humidity': float(np.clip(np.random.normal(prof['hum'], 8), 10, 100)),
            'ph': float(np.clip(np.random.normal(prof['ph'], 0.5), 3.5, 9.0)),
            'rainfall': float(np.clip(np.random.normal(prof['rain'], 250), 300, 4500)),
            'crop': c
        })
    return pd.DataFrame(data)

def train_crop_model():
    ml_dir = os.path.dirname(os.path.abspath(__file__))
    df = download_and_enrich_dataset()
    
    # 3. ENCODE CATEGORICAL VARIABLES
    categorical_cols = ['soil_type', 'water_availability', 'irrigation_type', 'previous_crop', 'season', 'market_demand']
    encoders = {}
    
    df_encoded = df.copy()
    for col in categorical_cols:
        le = LabelEncoder()
        df_encoded[col] = le.fit_transform(df[col])
        encoders[col] = le
        
    # Target variable encoding
    target_le = LabelEncoder()
    df_encoded['crop'] = target_le.fit_transform(df['crop'])
    encoders['crop'] = target_le
    
    # Split features and target
    X = df_encoded.drop(columns=['crop'])
    y = df_encoded['crop']
    
    feature_names = list(X.columns)
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    # 4. TRAIN AND COMPARE MULTIPLE MODELS
    models = {
        "RandomForest": RandomForestClassifier(n_estimators=150, max_depth=15, random_state=42),
        "ExtraTrees": ExtraTreesClassifier(n_estimators=150, max_depth=15, random_state=42),
        "GradientBoosting": GradientBoostingClassifier(n_estimators=100, max_depth=6, random_state=42),
        "XGBoost": XGBClassifier(n_estimators=100, max_depth=6, learning_rate=0.1, random_state=42)
    }
    
    best_model_name = None
    best_accuracy = 0.0
    best_model_obj = None
    
    print("\n--- MODEL PERFORMANCE COMPARISON ---")
    for name, model in models.items():
        print(f"Training {name} Classifier...")
        model.fit(X_train, y_train)
        preds = model.predict(X_test)
        acc = accuracy_score(y_test, preds)
        print(f"-> {name} Accuracy: {acc * 100:.2f}%")
        
        if acc > best_accuracy:
            best_accuracy = acc
            best_model_name = name
            best_model_obj = model
            
    print(f"\nWinner: {best_model_name} with Accuracy {best_accuracy * 100:.2f}%")
    
    # Show classification report for the champion
    champion_preds = best_model_obj.predict(X_test)
    print("\nClassification Report (Champion Model):")
    print(classification_report(y_test, champion_preds, target_names=target_le.classes_))
    
    # 5. SAVE CHAMPION MODEL
    model_data = {
        'model': best_model_obj,
        'feature_names': feature_names,
        'encoders': encoders,
        'accuracy': best_accuracy,
        'model_name': best_model_name
    }
    
    model_path = os.path.join(ml_dir, 'crop_model.pkl')
    with open(model_path, 'wb') as f:
        pickle.dump(model_data, f)
        
    print(f"Saved best model package to: {model_path}")

if __name__ == '__main__':
    train_crop_model()
