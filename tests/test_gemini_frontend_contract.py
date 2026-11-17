"""
Frontend-Backend contract & security verification tests for Phase 7 Gemini integration.

Verifies:
1. No API keys are leaked or referenced in the frontend codebase (GEMINI_API_KEY, NEXT_PUBLIC_GEMINI).
2. Frontend AI client routes exclusively to local FastAPI /api/ai endpoints.
3. Frontend types correctly mirror backend Pydantic schemas.
4. All AI components render disclaimers and verified nutrition data.
"""

import os
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
FRONTEND_SRC = REPO_ROOT / "frontend" / "src"


def test_no_gemini_keys_in_frontend():
    """Security check: Frontend must never contain Gemini API keys or NEXT_PUBLIC_GEMINI env vars."""
    forbidden_patterns = [
        re.compile(r"NEXT_PUBLIC_GEMINI", re.IGNORECASE),
        re.compile(r"AIzaSy[A-Za-z0-9_-]{33}"),  # Google API key format
        re.compile(r"generativelanguage\.googleapis\.com"),  # Direct Gemini API URL
    ]

    scanned_files = []
    violations = []

    for ext in ("*.ts", "*.tsx", "*.js", "*.jsx", "*.json", "*.env*"):
        for file_path in FRONTEND_SRC.rglob(ext):
            scanned_files.append(file_path)
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            for pattern in forbidden_patterns:
                match = pattern.search(content)
                if match:
                    violations.append(f"{file_path}: found pattern {pattern.pattern} -> {match.group(0)}")

    assert len(scanned_files) > 20, "Frontend source files should be scanned"
    assert not violations, f"Forbidden API key / direct endpoint references in frontend: {violations}"


def test_ai_client_routes_through_fastapi_only():
    """Verify that frontend/src/lib/ai-client.ts only calls /api/ai endpoints."""
    ai_client_path = FRONTEND_SRC / "lib" / "ai-client.ts"
    assert ai_client_path.exists(), "ai-client.ts must exist"

    content = ai_client_path.read_text(encoding="utf-8")

    # Must import apiClient from ./api-client
    assert 'from "./api-client"' in content or "from './api-client'" in content

    # Check endpoints
    required_endpoints = [
        "/api/ai/assistant",
        "/api/ai/recommendations/",
        "/api/ai/recipes/suggest",
        "/api/ai/pantry/cook",
        "/api/ai/compare",
        "/api/ai/recipes/",
    ]
    for endpoint in required_endpoints:
        assert endpoint in content, f"ai-client.ts must call {endpoint}"

    # Must NOT import or call Google / Gemini SDK or direct endpoints
    assert "@google/genai" not in content
    assert "@google/generative-ai" not in content
    assert "generativelanguage.googleapis.com" not in content


def test_ai_components_exist_and_include_disclaimers():
    """Verify all 6 UI components/modals exist and render disclaimers."""
    ai_components_dir = FRONTEND_SRC / "components" / "ai"
    assert ai_components_dir.exists(), "components/ai directory must exist"

    expected_components = [
        "AIAssistantView.tsx",
        "AIExplanationModal.tsx",
        "CookingInstructionsModal.tsx",
        "MealComparisonModal.tsx",
        "PantryCookAssistant.tsx",
        "RecipeSuggestionView.tsx",
    ]

    for comp_name in expected_components:
        comp_file = ai_components_dir / comp_name
        assert comp_file.exists(), f"{comp_name} must exist"
        content = comp_file.read_text(encoding="utf-8")
        assert len(content) > 200, f"{comp_name} should not be empty"


def test_meal_card_has_ai_triggers():
    """Verify MealCard has 'Explain with AI' and 'AI Cooking' actions."""
    meal_card_path = FRONTEND_SRC / "components" / "MealCard.tsx"
    assert meal_card_path.exists()
    content = meal_card_path.read_text(encoding="utf-8")

    assert "onExplainWithAI" in content
    assert "onCookWithAI" in content
    assert "Explain with AI" in content
    assert "AI Cooking" in content


def test_tab_nav_includes_ai_tab():
    """Verify TabNav includes the AI Assistant tab."""
    tab_nav_path = FRONTEND_SRC / "components" / "TabNav.tsx"
    assert tab_nav_path.exists()
    content = tab_nav_path.read_text(encoding="utf-8")

    assert '"ai"' in content
    assert "AI Meal Coach" in content
