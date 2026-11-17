"""
DietSense — AI & Gemini Router
Exposes the 6 Gemini-powered capabilities through FastAPI endpoints with
strict input validation, user isolation, and automatic offline fallbacks.
"""

from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status, Path

from app.core.dependencies import get_optional_current_user
from app.ai.service import ai_service
from app.schemas.ai import (
    AIMealAssistantRequest,
    AIMealAssistantResponse,
    ExplainRecommendationRequest,
    ExplainRecommendationResponse,
    RecipeSuggestionRequest,
    RecipeSuggestionResponse,
    PantryCookingRequest,
    PantryCookingResponse,
    MealComparisonRequest,
    MealComparisonResponse,
    CookingInstructionRequest,
    CookingInstructionResponse,
)

router = APIRouter(prefix="/api/ai", tags=["Gemini AI Assistant"])


# ─── 1. AI Meal Assistant ───────────────────────────────────────────────────

@router.post("/assistant", response_model=AIMealAssistantResponse)
async def ai_meal_assistant(
    request: AIMealAssistantRequest,
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_current_user),
):
    """
    Conversational nutrition assistant grounded in authoritative database nutrition facts.
    Respects user allergies and dietary preferences; never provides medical diagnoses.
    """
    user_id = current_user["id"] if current_user else "anonymous"
    return await ai_service.assistant_chat(
        query=request.query,
        user_id=user_id,
        context_food_ids=request.context_food_ids,
        meal_slot=request.meal_slot,
    )


# ─── 2. Meal Recommendation Explanation ─────────────────────────────────────

@router.post("/recommendations/{food_id}/explain", response_model=ExplainRecommendationResponse)
async def explain_recommendation(
    food_id: int = Path(..., description="Food catalog ID to explain"),
    payload: Optional[ExplainRecommendationRequest] = None,
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_current_user),
):
    """
    Explains why a specific meal was recommended based on real score factors and verified nutrition.
    """
    user_id = current_user["id"] if current_user else "anonymous"
    target_food_id = payload.food_id if (payload and payload.food_id is not None) else food_id
    score_breakdown = payload.score_breakdown if payload else None
    tone = payload.tone if payload else "friendly"
    food_name_override = payload.food_name if payload else None

    return await ai_service.explain_recommendation(
        food_id=target_food_id,
        user_id=user_id,
        score_breakdown=score_breakdown,
        tone=tone,
        food_name=food_name_override,
    )


# ─── 3. Recipe Suggestion ────────────────────────────────────────────────────

@router.post("/recipes/suggest", response_model=RecipeSuggestionResponse)
async def suggest_recipes(
    request: RecipeSuggestionRequest,
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_current_user),
):
    """
    Generates balanced, nutritious recipe ideas for a meal slot matching profile constraints.
    """
    user_id = current_user["id"] if current_user else "anonymous"
    return await ai_service.suggest_recipes(
        user_id=user_id,
        meal_slot=request.meal_slot or "lunch",
        target_calories=request.target_calories,
        prep_time_limit=request.prep_time_limit or 30,
        cuisine=request.cuisine or "indian",
    )


# ─── 4. Pantry-Based Cooking Assistant ──────────────────────────────────────

@router.post("/pantry/cook", response_model=PantryCookingResponse)
async def pantry_cooking_assistant(
    request: PantryCookingRequest,
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_current_user),
):
    """
    Suggests fast, low-waste recipes utilizing ingredients currently detected in user's pantry.
    """
    user_id = current_user["id"] if current_user else "anonymous"
    return await ai_service.pantry_cooking_assistant(
        user_id=user_id,
        custom_ingredients=request.custom_ingredients,
        max_prep_time_mins=request.max_prep_time_mins or 25,
        meal_slot=request.meal_slot or "dinner",
    )


# ─── 5. Meal Comparison ─────────────────────────────────────────────────────

@router.post("/compare", response_model=MealComparisonResponse)
async def compare_meals(
    request: MealComparisonRequest,
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_current_user),
):
    """
    Compares 2 to 5 meals objectively based on verified USDA/ICMR macronutrients.
    """
    user_id = current_user["id"] if current_user else "anonymous"
    try:
        return await ai_service.compare_meals(
            food_ids=request.food_ids,
            user_id=user_id,
            preference_priority=request.preference_priority or "balanced",
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ─── 6. Cooking Instructions ────────────────────────────────────────────────

@router.post("/recipes/{food_id}/instructions", response_model=CookingInstructionResponse)
async def cooking_instructions(
    food_id: int = Path(..., description="Food catalog ID"),
    payload: Optional[CookingInstructionRequest] = None,
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_current_user),
):
    """
    Generates beginner-friendly step-by-step cooking instructions for a catalog meal.
    """
    user_id = current_user["id"] if current_user else "anonymous"
    target_food_id = payload.food_id if (payload and payload.food_id is not None) else food_id
    servings = payload.servings if payload else 1
    skill_level = payload.skill_level if payload else "beginner"
    food_name_override = payload.food_name if payload else None

    return await ai_service.generate_cooking_instructions(
        food_id=target_food_id,
        user_id=user_id,
        servings=servings,
        skill_level=skill_level,
        food_name=food_name_override,
    )
