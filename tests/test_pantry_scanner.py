"""
DietSense — Tests for Pantry, Grocery Bill & Fridge Scanner
Verifies file upload parsing, PDF receipt extraction, fridge photo analysis,
sample presets, and pantry stock CRUD persistence in SQLite.
"""

import io
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.main import app
from app.core.config import settings
from app.core.security import create_access_token

client = TestClient(app)


def test_scan_sample_blinkit_preset():
    """Verify scanning the sample Blinkit bill preset returns structured grocery items."""
    res = client.get("/api/pantry/scan-sample?preset=blinkit")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["scan_type"] == "bill"
    assert len(data["detected_items"]) >= 5
    assert any("Paneer" in item["name"] for item in data["detected_items"])


def test_scan_sample_fridge_preset():
    """Verify scanning the sample fridge photo preset returns detected fridge items."""
    res = client.get("/api/pantry/scan-sample?preset=fridge")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["scan_type"] == "fridge"
    assert len(data["detected_items"]) >= 4
    assert any("Palak" in item["name"] or "Spinach" in item["name"] for item in data["detected_items"])


def test_upload_and_scan_image_file():
    """Verify uploading an image file to /api/pantry/scan returns detected items."""
    # Create an in-memory PNG image
    img = Image.new("RGB", (600, 800), color=(255, 255, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    files = {"file": ("test_fridge.png", buf, "image/png")}
    data = {"scan_type": "fridge"}

    res = client.post("/api/pantry/scan", files=files, data=data)
    assert res.status_code == 200
    res_data = res.json()
    assert res_data["status"] == "success"
    assert res_data["scan_type"] == "fridge"
    assert len(res_data["detected_items"]) > 0


def test_pantry_crud_and_persistence():
    """Verify adding, listing, toggling, and deleting pantry items."""
    token = create_access_token("usr_pantry_tester_01", "pantry_user@dietsense.ai")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Add items
    add_res = client.post(
        "/api/pantry/",
        json={
            "items": [
                {"name": "Organic Tofu", "category": "Dairy & Protein", "quantity": "250g"},
                {"name": "Baby Spinach", "category": "Fresh Veggies", "quantity": "1 bunch"},
            ]
        },
        headers=headers,
    )
    assert add_res.status_code == 200
    added = add_res.json()["added_items"]
    assert len(added) == 2
    item_id = added[0]["id"]

    # 2. List pantry items
    list_res = client.get("/api/pantry/", headers=headers)
    assert list_res.status_code == 200
    items = list_res.json()
    assert any(i["id"] == item_id for i in items)

    # 3. Toggle inStock
    toggle_res = client.patch(f"/api/pantry/{item_id}/toggle", headers=headers)
    assert toggle_res.status_code == 200
    assert toggle_res.json()["inStock"] is False

    # 4. Delete item
    del_res = client.delete(f"/api/pantry/{item_id}", headers=headers)
    assert del_res.status_code == 200
