# make_db.py
import pandas as pd
import sqlite3
from pathlib import Path

# --------- Paths ---------
BASE_DIR = Path(__file__).parent
EXCEL_PATH = BASE_DIR / "C:/Users/gunja/Documents/Unified_portal/E-commerce/dataset/Afficionado Coffee Roasters.xlsx"
DB_PATH = BASE_DIR / "coffee_roasters.db"

# --------- Load Excel ---------
# The main sheet is named "Transactions"
df = pd.read_excel(EXCEL_PATH, sheet_name="Transactions")

# Ensure expected columns exist
expected_cols = [
    "transaction_id", "year", "transaction_time", "transaction_qty",
    "store_id", "store_location", "product_id",
    "unit_price", "product_category", "product_type", "product_detail"
]
missing = set(expected_cols) - set(df.columns)
if missing:
    raise ValueError(f"Missing columns in Excel: {missing}")

# --------- Add revenue column ---------
df["revenue"] = df["transaction_qty"] * df["unit_price"]

# Optional sanity filter: drop fully empty product rows
df = df.dropna(subset=["product_id", "unit_price", "transaction_qty"])

# --------- Write to SQLite ---------
# Create / connect to the database
conn = sqlite3.connect(DB_PATH)

# Write the dataframe as a table called 'transactions'
df.to_sql("transactions", conn, if_exists="replace", index=False)

conn.close()
print(f"Database created at: {DB_PATH}")