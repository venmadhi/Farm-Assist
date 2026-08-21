import os
import pickle
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from xgboost import XGBRegressor

def download_and_save_mandi_data():
    url = "https://raw.githubusercontent.com/vibhor98/Analysis-of-agricultural-trends-in-time-series-dataset/master/Mandi_Data/Monthly_data_cmo.csv"
    ml_dir = os.path.dirname(os.path.abspath(__file__))
    local_path = os.path.join(ml_dir, 'mandi_monthly_data.csv')
    
    print(f"Downloading historical market price dataset from: {url}...")
    try:
        df = pd.read_csv(url)
        df.to_csv(local_path, index=False)
        print(f"Mandi dataset saved to: {local_path} (Shape: {df.shape})")
        return df
    except Exception as e:
        print(f"Error downloading dataset: {e}")
        if os.path.exists(local_path):
            print(f"Loading local mandi dataset from: {local_path}")
            return pd.read_csv(local_path)
        else:
            raise FileNotFoundError("Could not download or find mandi dataset locally.")

def train_market_model():
    print("\n--- ML MARKET PRICE FORECASTING MODEL TRAINING ---")
    
    # 1. Load dataset
    df = download_and_save_mandi_data()
    
    # Clean up column names and values
    df.columns = df.columns.str.strip()
    df['Commodity'] = df['Commodity'].str.strip()
    df['APMC'] = df['APMC'].str.strip()
    
    # Filter target crops
    target_crops = ['Paddy-Unhusked', 'Coconut', 'Banana', 'Ginger (Fresh)', 'Turmeric']
    df_filtered = df[df['Commodity'].isin(target_crops)].copy()
    
    # Clean prices (make numeric)
    df_filtered['modal_price'] = pd.to_numeric(df_filtered['modal_price'], errors='coerce')
    df_filtered.dropna(subset=['modal_price'], inplace=True)
    
    # Date processing
    df_filtered['date'] = pd.to_datetime(df_filtered['date'])
    df_filtered.sort_values(by=['Commodity', 'APMC', 'date'], inplace=True)
    
    # 2. Time-Series Feature Engineering
    # Calculate lags and rolling mean per Commodity + APMC group
    print("Engineering time-series features (lags and rolling averages)...")
    
    df_filtered['price_lag_1'] = df_filtered.groupby(['Commodity', 'APMC'])['modal_price'].shift(1)
    df_filtered['price_lag_2'] = df_filtered.groupby(['Commodity', 'APMC'])['modal_price'].shift(2)
    
    # Calculate rolling mean of last 3 months
    df_filtered['price_rolling_mean_3'] = df_filtered.groupby(['Commodity', 'APMC'])['modal_price'].shift(1).rolling(3).mean()
    
    # Fill remaining NaNs with global commodity averages for that date or commodity to prevent data drop
    global_averages = df_filtered.groupby(['Commodity', 'date'])['modal_price'].mean().reset_index()
    global_averages.rename(columns={'modal_price': 'global_avg_price'}, inplace=True)
    
    df_filtered = df_filtered.merge(global_averages, on=['Commodity', 'date'], how='left')
    
    df_filtered['price_lag_1'] = df_filtered['price_lag_1'].fillna(df_filtered['global_avg_price'].shift(1))
    df_filtered['price_lag_2'] = df_filtered['price_lag_2'].fillna(df_filtered['global_avg_price'].shift(2))
    df_filtered['price_rolling_mean_3'] = df_filtered['price_rolling_mean_3'].fillna(df_filtered['global_avg_price'].shift(1))
    
    # If still NaN, fill with global commodity overall median
    global_medians = df_filtered.groupby('Commodity')['modal_price'].transform('median')
    df_filtered['price_lag_1'] = df_filtered['price_lag_1'].fillna(global_medians)
    df_filtered['price_lag_2'] = df_filtered['price_lag_2'].fillna(global_medians)
    df_filtered['price_rolling_mean_3'] = df_filtered['price_rolling_mean_3'].fillna(global_medians)
    
    # Extract month and year
    df_filtered['Month_num'] = df_filtered['date'].dt.month
    df_filtered['Year'] = df_filtered['date'].dt.year
    
    # 3. Categorical Encoding
    encoders = {}
    
    for col in ['Commodity', 'APMC']:
        le = LabelEncoder()
        # Add unseen fallback class
        unique_vals = list(df_filtered[col].unique())
        le.fit(unique_vals + ['unseen'])
        df_filtered[col] = le.transform(df_filtered[col])
        encoders[col] = le

    # Features and Target
    features = ['Commodity', 'APMC', 'Month_num', 'Year', 'price_lag_1', 'price_lag_2', 'price_rolling_mean_3']
    X = df_filtered[features]
    y = df_filtered['modal_price']
    
    # 4. Chronological Splitting (Prevent Temporal Leakage)
    # Split using date boundary (e.g. Train before 2016-06-01, Test after)
    split_date = pd.to_datetime('2016-06-01')
    train_mask = df_filtered['date'] < split_date
    test_mask = df_filtered['date'] >= split_date
    
    X_train, y_train = X[train_mask], y[train_mask]
    X_test, y_test = X[test_mask], y[test_mask]
    
    print(f"Chronological Split Summary:")
    print(f"-> Train samples (before {split_date.strftime('%Y-%m-%d')}): {len(X_train)}")
    print(f"-> Test samples (after {split_date.strftime('%Y-%m-%d')}): {len(X_test)}")
    
    # Handle edge case where test set is empty
    if len(X_test) == 0:
        print("Warning: Test mask returned 0 samples. Splitting using 80/20 chronological split.")
        split_idx = int(len(df_filtered) * 0.8)
        X_train, y_train = X.iloc[:split_idx], y.iloc[:split_idx]
        X_test, y_test = X.iloc[split_idx:], y.iloc[split_idx:]
        
    # 5. Model Training & Comparison
    models = {
        "RandomForestRegressor": RandomForestRegressor(n_estimators=100, max_depth=8, random_state=42),
        "XGBRegressor": XGBRegressor(n_estimators=100, max_depth=6, learning_rate=0.1, random_state=42)
    }
    
    best_model_name = None
    best_r2 = -float('inf')
    best_model_obj = None
    best_metrics = {}
    
    print("\n--- TIME-SERIES MODEL COMPARISON ---")
    for name, model in models.items():
        model.fit(X_train, y_train)
        preds = model.predict(X_test)
        
        mae = mean_absolute_error(y_test, preds)
        rmse = np.sqrt(mean_squared_error(y_test, preds))
        r2 = r2_score(y_test, preds)
        
        print(f"Model: {name}")
        print(f"  MAE: {mae:.2f}")
        print(f"  RMSE: {rmse:.2f}")
        print(f"  R2 Score: {r2:.4f}")
        
        if r2 > best_r2:
            best_r2 = r2
            best_model_name = name
            best_model_obj = model
            best_metrics = {'mae': mae, 'rmse': rmse, 'r2': r2}
            
    print(f"\nWinning Model: {best_model_name} (R2: {best_r2:.4f})")
    
    # 6. Save Model Bundle
    ml_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(ml_dir, 'market_model.pkl')
    
    # Save the latest observed price data to query during inference for 'current price'
    # We take the latest price entry per APMC & Commodity from the dataset
    latest_prices = df_filtered.copy()
    latest_prices['date'] = df_filtered['date'].astype(str) # serialize date cleanly
    # Decode back columns for storage
    latest_prices['Commodity'] = encoders['Commodity'].inverse_transform(latest_prices['Commodity'])
    latest_prices['APMC'] = encoders['APMC'].inverse_transform(latest_prices['APMC'])
    
    latest_prices_summary = latest_prices.sort_values(by='date').groupby(['Commodity', 'APMC']).last().reset_index()
    latest_prices_db = latest_prices_summary[['Commodity', 'APMC', 'modal_price', 'date', 'price_lag_1', 'price_lag_2', 'price_rolling_mean_3']].to_dict('records')
    
    model_bundle = {
        'model': best_model_obj,
        'model_name': best_model_name,
        'feature_names': features,
        'encoders': encoders,
        'metrics': best_metrics,
        'latest_prices_db': latest_prices_db
    }
    
    with open(model_path, 'wb') as f:
        pickle.dump(model_bundle, f)
    print(f"Successfully saved market models and latest state to: {model_path}")
    return best_model_name, best_r2, len(X_train) + len(X_test)

if __name__ == '__main__':
    train_market_model()
