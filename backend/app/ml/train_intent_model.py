import os
import pickle
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

def train_intent_model():
    print("\n--- INTENT CLASSIFIER MODEL TRAINING ---")
    
    ml_dir = os.path.dirname(os.path.abspath(__file__))
    dataset_path = os.path.abspath(os.path.join(ml_dir, "..", "knowledge_base", "thanglish_agri_dataset.csv"))
    
    if not os.path.exists(dataset_path):
        print(f"Error: Dataset not found at {dataset_path}")
        return
        
    df = pd.read_csv(dataset_path)
    print(f"Loaded dataset containing {len(df)} samples.")
    
    # We use normalized text to train our model
    X_texts = df['normalized_text'].fillna(df['original_text']).values
    y_labels = df['intent'].values
    
    # Split
    X_train, X_test, y_train, y_test = train_test_split(X_texts, y_labels, test_size=0.15, random_state=42)
    
    # Feature extraction via TF-IDF Vectorizer
    # We use character n-grams (3 to 5) as well to make it extremely robust to minor spelling/transliteration variations!
    vectorizer = TfidfVectorizer(ngram_range=(1, 3), analyzer='word', min_df=1)
    
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)
    
    # Train Naive Bayes
    clf = MultinomialNB(alpha=0.1)
    clf.fit(X_train_vec, y_train)
    
    # Evaluate
    train_preds = clf.predict(X_train_vec)
    test_preds = clf.predict(X_test_vec)
    
    train_acc = accuracy_score(y_train, train_preds)
    test_acc = accuracy_score(y_test, test_preds)
    
    print(f"Training Accuracy: {train_acc * 100:.2f}%")
    print(f"Testing Accuracy: {test_acc * 100:.2f}%")
    
    # Save model bundle
    models_dir = os.path.abspath(os.path.join(ml_dir, "..", "models", "intent_model"))
    os.makedirs(models_dir, exist_ok=True)
    
    model_path = os.path.join(models_dir, "intent_model.pkl")
    model_data = {
        'model': clf,
        'vectorizer': vectorizer,
        'classes': list(clf.classes_)
    }
    
    with open(model_path, 'wb') as f:
        pickle.dump(model_data, f)
        
    print(f"Intent model successfully saved to: {model_path}")

if __name__ == '__main__':
    train_intent_model()
