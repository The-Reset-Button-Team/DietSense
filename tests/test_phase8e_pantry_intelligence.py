"""
Phase 8E — Tests for Pantry Intelligence.

Validates:
1. OCR failures & invalid document handling:
   - Corrupted image bytes return 400 with descriptive error.
   - Corrupted or invalid PDF bytes return 400.
   - Unsupported file extensions return 400.
2. PDF ingredient extraction:
   - Real multi-item receipt PDF parses ingredients and quantities.
3. Ingredient matching against SQLite food catalog:
   - Extracted ingredients are mapped to authoritative database IDs, calories, and categories.
4. Confidence scoring and review gating:
   - Items with uncertain or partial recognition are flagged with needs_review: true.
5. Manual correction:
   - Users can update name, category, quantity, and expiry_date on pantry items.
6. Expiry-date tracking & Freshness indicators:
   - Categorizes items into fresh, expiring_soon, and expired with days remaining.
7. Missing-ingredient shopping lists:
   - Computes missing ingredients between recipe requirements and in-stock pantry items.
8. Pantry-based recipe recommendations:
   - Ranks recipes by pantry coverage percentage and identifies can_cook_now meals.
"""

import io
import time
from datetime import datetime, timezone, date, timedelta
import pypdf
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import settings
from app.core.security import create_access_token
from backend.routes.pantry import (
    compute_freshness,
    match_ingredient_to_database,
    _extract_items_from_text,
)

client = TestClient(app)


def generate_auth_headers(user_id: str = "usr_pantry_intel_tester") -> dict:
    token = create_access_token(user_id, f"{user_id}@dietsense.ai")
    return {"Authorization": f"Bearer {token}"}


def create_mock_receipt_pdf(lines: list[str]) -> bytes:
    """Helper to generate a real, in-memory PDF containing receipt lines."""
    text_commands = []
    y = 700
    for line in lines:
        clean = line.replace("(", "\\(").replace(")", "\\)")
        text_commands.append(f"1 0 0 1 50 {y} Tm ({clean}) Tj")
        y -= 25
    stream_content = "BT\n/F1 12 Tf\n" + "\n".join(text_commands) + "\nET"
    stream_bytes = stream_content.encode("latin-1")
    length = len(stream_bytes)
    return (
        b"%PDF-1.4\n"
        b"1 0 obj <</Type /Catalog /Pages 2 0 R>> endobj\n"
        b"2 0 obj <</Type /Pages /Kids [3 0 R] /Count 1>> endobj\n"
        b"3 0 obj <</Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >> endobj\n"
        b"4 0 obj <</Length " + str(length).encode("latin-1") + b">> stream\n"
        + stream_bytes +
        b"\nendstream\nendobj\n"
        b"5 0 obj <</Type /Font /Subtype /Type1 /BaseFont /Helvetica>> endobj\n"
        b"xref\n0 6\n0000000000 65535 f \n"
        b"trailer <</Size 6 /Root 1 0 R>>\nstartxref\n999\n%%EOF"
    )


# ─── 1. OCR Failures & Document Error Tests ──────────────────────────────────

def test_ocr_corrupted_image_returns_400():
    """Corrupted image bytes trigger 400 error instead of uncaught crash."""
    corrupt_bytes = b"NOT_A_REAL_IMAGE_BYTES_12345"
    files = {"file": ("corrupt_receipt.jpg", io.BytesIO(corrupt_bytes), "image/jpeg")}
    res = client.post("/api/pantry/scan", files=files, data={"scan_type": "receipt"})
    assert res.status_code == 400
    assert "image" in res.json()["detail"].lower() or "invalid" in res.json()["detail"].lower()


def test_ocr_corrupted_pdf_returns_400():
    """Corrupted PDF bytes trigger 400 error."""
    corrupt_pdf = b"NOT_A_PDF_FILE"
    files = {"file": ("bad_receipt.pdf", io.BytesIO(corrupt_pdf), "application/pdf")}
    res = client.post("/api/pantry/scan", files=files, data={"scan_type": "receipt"})
    assert res.status_code == 400
    assert "pdf" in res.json()["detail"].lower() or "invalid" in res.json()["detail"].lower()


def test_unsupported_file_type_returns_400():
    """Unsupported document types (.exe, .zip, .txt) return 400."""
    fake_exe = b"MZ\x90\x00\x03\x00\x00\x00"
    files = {"file": ("malicious.exe", io.BytesIO(fake_exe), "application/x-msdownload")}
    res = client.post("/api/pantry/scan", files=files, data={"scan_type": "receipt"})
    assert res.status_code == 400
    assert "unsupported" in res.json()["detail"].lower()


# ─── 2. PDF Ingredient Extraction Tests ──────────────────────────────────────

def test_pdf_grocery_receipt_extraction():
    """Real PDF receipt extracts grocery items with units and categorizes them."""
    receipt_lines = [
        "1. Amul Malai Paneer 200 g - Rs 95",
        "2. Farm Fresh Palak 1 bunch - Rs 30",
        "3. Fortune Yellow Moong Dal 500 g - Rs 85",
        "4. Tata Salt 1 kg - Rs 28",
    ]
    pdf_bytes = create_mock_receipt_pdf(receipt_lines)
    files = {"file": ("grocery_bill.pdf", io.BytesIO(pdf_bytes), "application/pdf")}

    res = client.post("/api/pantry/scan", files=files, data={"scan_type": "receipt"})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["ocr_engine"] == "pypdf"
    items = data["detected_items"]
    assert len(items) >= 3

    names = [i["name"].lower() for i in items]
    assert any("paneer" in n for n in names)
    assert any("palak" in n or "spinach" in n for n in names)
    assert any("moong" in n or "dal" in n for n in names)


# ─── 3. Ingredient Matching against Food Database ────────────────────────────

def test_match_ingredient_to_database():
    """match_ingredient_to_database links extracted items to real SQLite food records."""
    match = match_ingredient_to_database("Paneer")
    assert match is not None
    assert "food_id" in match
    assert match["calories_kcal"] > 0
    assert match["is_vegetarian"] is True

    # Test synonym mapping (Palak -> Spinach)
    palak_match = match_ingredient_to_database("Palak")
    assert palak_match is not None
    assert "spinach" in palak_match["name"].lower() or "palak" in palak_match["name"].lower()


# ─── 4. Confidence Scoring and Review Flagging ──────────────────────────────

def test_uncertain_ocr_sets_needs_review():
    """Uncertain or partial matches are marked with needs_review: true."""
    raw_text = """
    Random Grocery Line with Tomato
    Unclear fragment without unit
    """
    extracted = _extract_items_from_text(raw_text)
    assert len(extracted) >= 1
    # Items without explicit package quantity have lower confidence and require review
    tomato_item = next(i for i in extracted if i["name"] == "Tomato")
    assert tomato_item["confidence"] <= 0.85
    assert tomato_item["needs_review"] is True


# ─── 5. Expiry-Date Tracking and Freshness Indicators ────────────────────────

def test_compute_freshness_categories():
    """Freshness logic correctly categorizes fresh, expiring soon, and expired."""
    today = date(2026, 11, 19)

    # Expired 2 days ago
    exp_past = (today - timedelta(days=2)).isoformat()
    past_res = compute_freshness(exp_past, now_date=today)
    assert past_res["freshness_status"] == "expired"
    assert past_res["days_until_expiry"] == -2
    assert "Expired" in past_res["freshness_indicator"]

    # Expiring in 2 days (expiring_soon)
    exp_soon = (today + timedelta(days=2)).isoformat()
    soon_res = compute_freshness(exp_soon, now_date=today)
    assert soon_res["freshness_status"] == "expiring_soon"
    assert soon_res["days_until_expiry"] == 2

    # Fresh in 10 days
    exp_fresh = (today + timedelta(days=10)).isoformat()
    fresh_res = compute_freshness(exp_fresh, now_date=today)
    assert fresh_res["freshness_status"] == "fresh"
    assert fresh_res["days_until_expiry"] == 10

    # Unspecified
    uns_res = compute_freshness(None)
    assert uns_res["freshness_status"] == "unspecified"


# ─── 6. Manual Correction of Extracted Ingredients ──────────────────────────

def test_manual_correction_of_pantry_item():
    """Users can edit name, quantity, category, and expiry_date of an existing item."""
    headers = generate_auth_headers("usr_manual_correction_tester")

    # 1. Add item
    add_res = client.post(
        "/api/pantry/",
        json={"name": "Raw Tofu", "quantity": "100g", "category": "Dairy & Protein"},
        headers=headers,
    )
    assert add_res.status_code == 200
    item_id = add_res.json()["added_items"][0]["id"]

    # 2. Correct item via PUT/PATCH
    update_res = client.put(
        f"/api/pantry/{item_id}",
        json={
            "name": "Organic Firm Tofu",
            "quantity": "250g",
            "category": "Dairy & Protein",
            "expiry_date": (datetime.now(timezone.utc).date() + timedelta(days=7)).isoformat(),
        },
        headers=headers,
    )
    assert update_res.status_code == 200
    updated = update_res.json()["item"]
    assert updated["name"] == "Organic Firm Tofu"
    assert updated["quantity"] == "250g"
    assert updated["freshness_status"] == "fresh"


# ─── 7. Missing-Ingredient Shopping List Tests ──────────────────────────────

def test_missing_ingredient_shopping_list():
    """Shopping list endpoint correctly computes missing ingredients against recipes."""
    headers = generate_auth_headers("usr_shopping_list_tester")

    # Seed pantry with Paneer and Atta (missing Onion and Tomato for Paneer Bhurji)
    client.post(
        "/api/pantry/",
        json={"items": [{"name": "Paneer", "inStock": True}, {"name": "Atta", "inStock": True}]},
        headers=headers,
    )

    # Request shopping list for Recipe 3 (Paneer Bhurji: requires Paneer, Onion, Tomato, Atta, Ghee)
    res = client.post(
        "/api/pantry/shopping-list",
        json={"recipe_ids": [3]},
        headers=headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["total_required"] == 5
    assert data["in_pantry_count"] >= 2
    assert data["missing_count"] >= 2
    missing_names = [m["name"].lower() for m in data["missing_items"]]
    assert any("onion" in n for n in missing_names)
    assert any("tomato" in n for n in missing_names)


# ─── 8. Pantry-Based Recipe Recommendations Tests ───────────────────────────

def test_pantry_based_recipe_recommendations():
    """Recommends recipes ranked by pantry ingredient coverage."""
    headers = generate_auth_headers("usr_recipe_rec_tester")

    # Add ingredients for Jeera Paani (Jeera, Ajwain, Badam) -> 100% coverage
    client.post(
        "/api/pantry/",
        json={
            "items": [
                {"name": "Jeera", "inStock": True},
                {"name": "Ajwain", "inStock": True},
                {"name": "Badam", "inStock": True},
            ]
        },
        headers=headers,
    )

    res = client.get("/api/pantry/recipe-recommendations", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    recipes = data["recipes"]
    assert len(recipes) >= 1

    # Top recipe should be the 100% match (Warm Ajwain-Jeera Paani)
    top_recipe = recipes[0]
    assert "Jeera" in top_recipe["name"]
    assert top_recipe["can_cook_now"] is True
    assert top_recipe["coverage_pct"] == 100.0
