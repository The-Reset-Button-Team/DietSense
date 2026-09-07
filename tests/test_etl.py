"""
Phase 2 — ETL & Database Ingestion Validation Tests
Tests data integrity for both USDA and ICMR-NIN extracted datasets.
"""

import os
import sqlite3
import pandas as pd
import pytest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "database", "dietsense.db")
MERGED_CSV = os.path.join(BASE_DIR, "data", "processed", "foods_merged.csv")

def test_merged_csv_exists_and_populated():
    """Verify that foods_merged.csv exists and has more than 10,000 foods."""
    assert os.path.exists(MERGED_CSV), "foods_merged.csv must exist"
    df = pd.read_csv(MERGED_CSV)
    assert len(df) > 10000, f"Expected >10,000 foods, got {len(df)}"

def test_both_sources_present():
    """Verify both USDA and ICMR_NIN sources are in merged dataset."""
    df = pd.read_csv(MERGED_CSV)
    sources = set(df["data_source"].unique())
    assert "USDA" in sources, "USDA data source missing"
    assert "ICMR_NIN" in sources, "ICMR_NIN data source missing"

def test_database_foods_loaded():
    """Verify foods table in dietsense.db has loaded records."""
    assert os.path.exists(DB_PATH), "dietsense.db must exist"
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    count = cur.execute("SELECT COUNT(id) FROM foods").fetchone()[0]
    conn.close()
    assert count > 10000, f"Expected >10,000 foods in DB, got {count}"

def test_no_nan_calories():
    """Verify calories are non-negative and valid."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    invalid_cals = cur.execute("SELECT COUNT(id) FROM foods WHERE calories_kcal < 0 OR calories_kcal > 1000").fetchone()[0]
    conn.close()
    assert invalid_cals == 0, f"Found {invalid_cals} foods with invalid calories"
