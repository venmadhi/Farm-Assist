import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'agrigenie.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get existing columns
cursor.execute("PRAGMA table_info(disease_records)")
columns = [info[1] for info in cursor.fetchall()]

new_columns = {
    "crop_confidence": "FLOAT",
    "crop_model": "VARCHAR(100)",
    "disease_model": "VARCHAR(100)",
    "crop_disease_match": "BOOLEAN",
    "model_version": "VARCHAR(100)"
}

for col_name, col_type in new_columns.items():
    if col_name not in columns:
        print(f"Adding column {col_name}...")
        cursor.execute(f"ALTER TABLE disease_records ADD COLUMN {col_name} {col_type}")
    else:
        print(f"Column {col_name} already exists.")

conn.commit()
conn.close()
print("Migration completed.")
