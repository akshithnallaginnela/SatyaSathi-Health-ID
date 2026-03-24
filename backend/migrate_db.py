"""
Quick migration: add missing columns to blood_reports table.
Run once: python migrate_db.py
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vitalid.db")

NEW_COLUMNS = [
    ("rdw_sd", "FLOAT"),
    ("mpv", "FLOAT"),
    ("neutrophils_abs", "FLOAT"),
    ("lymphocytes_abs", "FLOAT"),
    ("monocytes_abs", "FLOAT"),
    ("eosinophils_abs", "FLOAT"),
    ("p_lcr", "FLOAT"),
    ("hba1c", "FLOAT"),
    ("uric_acid", "FLOAT"),
    ("egfr", "FLOAT"),
    ("sgpt", "FLOAT"),
    ("sgot", "FLOAT"),
    ("bilirubin_total", "FLOAT"),
    ("bilirubin_direct", "FLOAT"),
    ("alkaline_phosphatase", "FLOAT"),
    ("albumin", "FLOAT"),
    ("total_protein", "FLOAT"),
    ("total_cholesterol", "FLOAT"),
    ("hdl", "FLOAT"),
    ("ldl", "FLOAT"),
    ("triglycerides", "FLOAT"),
    ("vldl", "FLOAT"),
    ("tsh", "FLOAT"),
    ("t3", "FLOAT"),
    ("t4", "FLOAT"),
    ("vitamin_d", "FLOAT"),
    ("vitamin_b12", "FLOAT"),
    ("iron", "FLOAT"),
    ("ferritin", "FLOAT"),
    ("calcium", "FLOAT"),
    ("sodium", "FLOAT"),
    ("potassium", "FLOAT"),
    ("peripheral_smear", "TEXT"),
]

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Get existing columns
cursor.execute("PRAGMA table_info(blood_reports)")
existing = {row[1] for row in cursor.fetchall()}

added = []
for col_name, col_type in NEW_COLUMNS:
    if col_name not in existing:
        try:
            cursor.execute(f"ALTER TABLE blood_reports ADD COLUMN {col_name} {col_type}")
            added.append(col_name)
        except Exception as e:
            print(f"  Skipped {col_name}: {e}")

conn.commit()
conn.close()

if added:
    print(f"✅ Added {len(added)} columns: {', '.join(added)}")
else:
    print("✅ All columns already exist — no changes needed")
