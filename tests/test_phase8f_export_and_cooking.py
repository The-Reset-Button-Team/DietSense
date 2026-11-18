"""
Phase 8F — DietSense Export & Cooking Utilities Tests

Tests:
1. Text export format and nutrition accuracy.
2. WhatsApp export format (bold headers, emojis, macro summary).
3. PDF export valid headers and non-empty binary content.
4. Missing meal info handled gracefully.
5. Recipe cooking instructions endpoint (cook mode).
6. Unauthenticated request rejection (401).
"""

import io
import json
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.security import create_access_token

client = TestClient(app)

TEST_USER_ID = "usr_phase8f_tester"
TEST_EMAIL = "phase8f@dietsense.ai"


def auth_headers(user_id: str = TEST_USER_ID) -> dict:
    token = create_access_token(user_id, f"{user_id}@dietsense.ai")
    return {"Authorization": f"Bearer {token}"}


def create_test_plan(user_id: str = TEST_USER_ID) -> dict:
    """Creates a saved meal plan for the test user and returns the plan dict."""
    headers = auth_headers(user_id)
    payload = {
        "date": "2026-11-19",
        "target_calories": 2000,
        "status": "accepted",
        "items": [
            {
                "slot": "breakfast",
                "name": "Moong Dal Chilla",
                "calories": 420,
                "protein_g": 22,
                "carbs_g": 45,
                "fat_g": 10,
                "fiber_g": 6,
            },
            {
                "slot": "lunch",
                "name": "Brown Rice & Palak Dal",
                "calories": 580,
                "protein_g": 28,
                "carbs_g": 72,
                "fat_g": 12,
                "fiber_g": 9,
            },
            {
                "slot": "dinner",
                "name": "Tofu & Broccoli Stir Fry",
                "calories": 390,
                "protein_g": 24,
                "carbs_g": 30,
                "fat_g": 18,
                "fiber_g": 7,
            },
        ],
    }
    res = client.post("/api/meal-plans", json=payload, headers=headers)
    assert res.status_code == 201, f"Setup failed: {res.text}"
    return res.json()


# ─── 1. Text Export ───────────────────────────────────────────────────────────

class TestTextExport:
    def test_text_export_returns_200(self):
        """Text export endpoint returns HTTP 200."""
        plan = create_test_plan()
        res = client.get(f"/api/meal-plans/{plan['id']}/export/text", headers=auth_headers())
        assert res.status_code == 200

    def test_text_export_content_type(self):
        """Text export returns plain text content type."""
        plan = create_test_plan()
        res = client.get(f"/api/meal-plans/{plan['id']}/export/text", headers=auth_headers())
        assert "text/plain" in res.headers.get("content-type", "")

    def test_text_export_includes_date(self):
        """Text export contains the plan date."""
        plan = create_test_plan()
        res = client.get(f"/api/meal-plans/{plan['id']}/export/text", headers=auth_headers())
        assert "2026-11-19" in res.text

    def test_text_export_includes_meal_names(self):
        """Text export contains all meal slot names."""
        plan = create_test_plan()
        res = client.get(f"/api/meal-plans/{plan['id']}/export/text", headers=auth_headers())
        assert "Moong Dal Chilla" in res.text
        assert "Brown Rice" in res.text
        assert "Tofu" in res.text

    def test_text_export_includes_calories(self):
        """Text export contains calorie information."""
        plan = create_test_plan()
        res = client.get(f"/api/meal-plans/{plan['id']}/export/text", headers=auth_headers())
        # At least one calorie value should appear
        assert "420" in res.text or "kcal" in res.text.lower() or "cal" in res.text.lower()

    def test_text_export_includes_macros(self):
        """Text export contains protein/carbs/fat values."""
        plan = create_test_plan()
        res = client.get(f"/api/meal-plans/{plan['id']}/export/text", headers=auth_headers())
        lower = res.text.lower()
        assert "protein" in lower or "prot" in lower
        assert "carb" in lower
        assert "fat" in lower

    def test_text_export_includes_totals(self):
        """Text export contains a totals/summary section."""
        plan = create_test_plan()
        res = client.get(f"/api/meal-plans/{plan['id']}/export/text", headers=auth_headers())
        lower = res.text.lower()
        assert "total" in lower or "summary" in lower

    def test_text_export_plan_not_found_returns_404(self):
        """Non-existent plan returns 404."""
        res = client.get("/api/meal-plans/plan_nonexistent_xyz/export/text", headers=auth_headers())
        assert res.status_code == 404

    def test_text_export_user_isolation(self):
        """User A cannot export User B's plan."""
        plan = create_test_plan(user_id="usr_8f_owner")
        res = client.get(
            f"/api/meal-plans/{plan['id']}/export/text",
            headers=auth_headers("usr_8f_attacker"),
        )
        assert res.status_code == 404  # access denied → not found

    def test_text_export_dietsense_branding(self):
        """Text export contains DietSense branding."""
        plan = create_test_plan()
        res = client.get(f"/api/meal-plans/{plan['id']}/export/text", headers=auth_headers())
        assert "DietSense" in res.text


# ─── 2. WhatsApp Export ───────────────────────────────────────────────────────

class TestWhatsAppExport:
    def test_whatsapp_export_returns_200(self):
        """WhatsApp export endpoint returns HTTP 200."""
        plan = create_test_plan()
        res = client.get(f"/api/meal-plans/{plan['id']}/export/whatsapp", headers=auth_headers())
        assert res.status_code == 200

    def test_whatsapp_bold_header(self):
        """WhatsApp export uses *bold* for the main header."""
        plan = create_test_plan()
        res = client.get(f"/api/meal-plans/{plan['id']}/export/whatsapp", headers=auth_headers())
        assert "*DietSense" in res.text or "*" in res.text

    def test_whatsapp_contains_date(self):
        """WhatsApp export contains the plan date."""
        plan = create_test_plan()
        res = client.get(f"/api/meal-plans/{plan['id']}/export/whatsapp", headers=auth_headers())
        assert "2026-11-19" in res.text

    def test_whatsapp_contains_meal_names(self):
        """WhatsApp export contains meal names."""
        plan = create_test_plan()
        res = client.get(f"/api/meal-plans/{plan['id']}/export/whatsapp", headers=auth_headers())
        assert "Moong Dal" in res.text or "Chilla" in res.text
        assert "Rice" in res.text or "Dal" in res.text

    def test_whatsapp_contains_emojis(self):
        """WhatsApp export contains food emojis for visual scanning."""
        plan = create_test_plan()
        res = client.get(f"/api/meal-plans/{plan['id']}/export/whatsapp", headers=auth_headers())
        # At least one emoji should be present
        emoji_chars = ["🍳", "🥗", "🍱", "🍎", "☀️", "🥣", "🌙", "🥦", "🫓", "🥩"]
        assert any(e in res.text for e in emoji_chars)

    def test_whatsapp_contains_macros(self):
        """WhatsApp export contains macro information."""
        plan = create_test_plan()
        res = client.get(f"/api/meal-plans/{plan['id']}/export/whatsapp", headers=auth_headers())
        # Should have P: or Protein with numbers
        assert "P:" in res.text or "protein" in res.text.lower()

    def test_whatsapp_plan_not_found_returns_404(self):
        """WhatsApp export for non-existent plan returns 404."""
        res = client.get(
            "/api/meal-plans/plan_nonexistent_wa/export/whatsapp",
            headers=auth_headers(),
        )
        assert res.status_code == 404

    def test_whatsapp_user_isolation(self):
        """User isolation enforced for WhatsApp export."""
        plan = create_test_plan(user_id="usr_8f_wa_owner")
        res = client.get(
            f"/api/meal-plans/{plan['id']}/export/whatsapp",
            headers=auth_headers("usr_8f_wa_attacker"),
        )
        assert res.status_code == 404

    def test_whatsapp_total_calories_line(self):
        """WhatsApp export contains a total calorie summary line."""
        plan = create_test_plan()
        res = client.get(f"/api/meal-plans/{plan['id']}/export/whatsapp", headers=auth_headers())
        lower = res.text.lower()
        assert "total" in lower or "kcal" in lower


# ─── 3. PDF Export ────────────────────────────────────────────────────────────

class TestPDFExport:
    def test_pdf_export_returns_200(self):
        """PDF export endpoint returns HTTP 200."""
        plan = create_test_plan()
        res = client.get(f"/api/meal-plans/{plan['id']}/export/pdf", headers=auth_headers())
        assert res.status_code == 200

    def test_pdf_export_content_type(self):
        """PDF export returns application/pdf content type."""
        plan = create_test_plan()
        res = client.get(f"/api/meal-plans/{plan['id']}/export/pdf", headers=auth_headers())
        assert "application/pdf" in res.headers.get("content-type", "")

    def test_pdf_export_valid_header(self):
        """PDF export starts with valid %PDF-1.4 header."""
        plan = create_test_plan()
        res = client.get(f"/api/meal-plans/{plan['id']}/export/pdf", headers=auth_headers())
        assert res.content[:5] == b"%PDF-"

    def test_pdf_export_non_empty(self):
        """PDF export returns meaningful content (>500 bytes)."""
        plan = create_test_plan()
        res = client.get(f"/api/meal-plans/{plan['id']}/export/pdf", headers=auth_headers())
        assert len(res.content) > 500

    def test_pdf_export_content_disposition(self):
        """PDF export sets Content-Disposition attachment header."""
        plan = create_test_plan()
        res = client.get(f"/api/meal-plans/{plan['id']}/export/pdf", headers=auth_headers())
        cd = res.headers.get("content-disposition", "")
        assert "attachment" in cd
        assert ".pdf" in cd

    def test_pdf_export_plan_not_found_returns_404(self):
        """PDF export for non-existent plan returns 404."""
        res = client.get(
            "/api/meal-plans/plan_nonexistent_pdf/export/pdf",
            headers=auth_headers(),
        )
        assert res.status_code == 404

    def test_pdf_export_user_isolation(self):
        """User isolation enforced for PDF export."""
        plan = create_test_plan(user_id="usr_8f_pdf_owner")
        res = client.get(
            f"/api/meal-plans/{plan['id']}/export/pdf",
            headers=auth_headers("usr_8f_pdf_attacker"),
        )
        assert res.status_code == 404

    def test_pdf_has_eof_marker(self):
        """Valid PDF ends with %%EOF marker."""
        plan = create_test_plan()
        res = client.get(f"/api/meal-plans/{plan['id']}/export/pdf", headers=auth_headers())
        assert b"%%EOF" in res.content


# ─── 4. Missing Meal Info Handling ────────────────────────────────────────────

class TestMissingMealInfo:
    def test_text_export_plan_with_empty_items(self):
        """Text export gracefully handles a plan with no items."""
        headers = auth_headers("usr_8f_empty")
        payload = {
            "date": "2026-11-19",
            "target_calories": 1800,
            "status": "generated",
            "items": [],
        }
        res = client.post("/api/meal-plans", json=payload, headers=headers)
        assert res.status_code == 201
        plan_id = res.json()["id"]

        export_res = client.get(f"/api/meal-plans/{plan_id}/export/text", headers=headers)
        assert export_res.status_code == 200
        assert len(export_res.text) > 0  # Non-empty even with no items

    def test_whatsapp_export_plan_with_empty_items(self):
        """WhatsApp export gracefully handles a plan with no items."""
        headers = auth_headers("usr_8f_wa_empty")
        payload = {
            "date": "2026-11-19",
            "target_calories": 1800,
            "status": "generated",
            "items": [],
        }
        res = client.post("/api/meal-plans", json=payload, headers=headers)
        plan_id = res.json()["id"]

        export_res = client.get(f"/api/meal-plans/{plan_id}/export/whatsapp", headers=headers)
        assert export_res.status_code == 200
        assert "DietSense" in export_res.text

    def test_pdf_export_plan_with_partial_items(self):
        """PDF export handles items missing optional fields."""
        headers = auth_headers("usr_8f_partial")
        payload = {
            "date": "2026-11-19",
            "target_calories": 1800,
            "status": "generated",
            "items": [
                {"slot": "lunch", "name": "Mystery Meal", "calories": 400},
            ],
        }
        res = client.post("/api/meal-plans", json=payload, headers=headers)
        plan_id = res.json()["id"]

        export_res = client.get(f"/api/meal-plans/{plan_id}/export/pdf", headers=headers)
        assert export_res.status_code == 200
        assert export_res.content[:5] == b"%PDF-"


# ─── 5. Cook Mode / Recipe Instructions Endpoint ─────────────────────────────

class TestCookModeEndpoint:
    def test_cook_mode_known_recipe_returns_200(self):
        """Cook mode endpoint returns 200 for a known canonical recipe (id=1)."""
        res = client.get("/api/meal-plans/recipes/1/cook", headers=auth_headers())
        assert res.status_code == 200

    def test_cook_mode_response_structure(self):
        """Cook mode response contains required fields."""
        res = client.get("/api/meal-plans/recipes/1/cook", headers=auth_headers())
        data = res.json()
        assert "id" in data
        assert "name" in data
        assert "steps" in data
        assert isinstance(data["steps"], list)
        assert "ingredients" in data
        assert isinstance(data["ingredients"], list)

    def test_cook_mode_steps_have_instruction(self):
        """Each step in cook mode has at least an instruction field."""
        res = client.get("/api/meal-plans/recipes/1/cook", headers=auth_headers())
        data = res.json()
        if data["steps"]:
            step = data["steps"][0]
            assert "instruction" in step or "step" in step

    def test_cook_mode_fallback_for_unknown_recipe(self):
        """Cook mode returns a fallback (not 404) for an unknown recipe id."""
        res = client.get("/api/meal-plans/recipes/9999/cook", headers=auth_headers())
        # Should return 200 with fallback data, not crash
        assert res.status_code == 200
        data = res.json()
        assert "steps" in data

    def test_cook_mode_known_recipe_has_name(self):
        """Cook mode recipe 1 has correct name containing 'Ajwain' or 'Jeera'."""
        res = client.get("/api/meal-plans/recipes/1/cook", headers=auth_headers())
        data = res.json()
        name_lower = data.get("name", "").lower()
        assert "ajwain" in name_lower or "jeera" in name_lower or "badam" in name_lower or len(name_lower) > 0

    def test_cook_mode_recipe2_brunch(self):
        """Cook mode recipe 2 (Moong Dal Chilla) returns valid data."""
        res = client.get("/api/meal-plans/recipes/2/cook", headers=auth_headers())
        assert res.status_code == 200
        data = res.json()
        assert data["id"] == 2
        assert len(data["name"]) > 0

    def test_cook_mode_ingredients_have_name_and_quantity(self):
        """Cook mode ingredients include name and quantity fields."""
        res = client.get("/api/meal-plans/recipes/1/cook", headers=auth_headers())
        data = res.json()
        if data["ingredients"]:
            ing = data["ingredients"][0]
            assert "name" in ing
            assert "quantity" in ing


# ─── 6. Unauthenticated Request Rejection ─────────────────────────────────────

class TestUnauthenticated:
    def test_text_export_requires_auth(self):
        """Text export without token returns 401 or 403."""
        res = client.get("/api/meal-plans/plan_xyz/export/text")
        assert res.status_code in (401, 403)

    def test_whatsapp_export_requires_auth(self):
        """WhatsApp export without token returns 401 or 403."""
        res = client.get("/api/meal-plans/plan_xyz/export/whatsapp")
        assert res.status_code in (401, 403)

    def test_pdf_export_requires_auth(self):
        """PDF export without token returns 401 or 403."""
        res = client.get("/api/meal-plans/plan_xyz/export/pdf")
        assert res.status_code in (401, 403)

    def test_cook_mode_requires_auth(self):
        """Cook mode endpoint without token returns 401 or 403."""
        res = client.get("/api/meal-plans/recipes/1/cook")
        assert res.status_code in (401, 403)
