"""
DietSense - Pydantic Schemas
Data models for User, FoodItem, Recipe, MealPlan, MealLog, and Feedback.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class UserProfileSchema(BaseModel):
    """Schema representing user profile and onboarding constraints."""
    id: Optional[str] = None
    age: Optional[int] = None
    diet: Optional[str] = None
    budget: Optional[float] = None
    prep_time_limit: Optional[int] = None
    allergies: List[str] = Field(default_factory=list)


class FoodItemSchema(BaseModel):
    """Schema for individual food item and macro details."""
    id: Optional[int] = None
    name: str
    category: Optional[str] = None
    calories: Optional[float] = None
    protein: Optional[float] = None
    carbs: Optional[float] = None
    fat: Optional[float] = None


class RecipeSchema(BaseModel):
    """Schema for recipe containing ingredients and metadata."""
    id: Optional[int] = None
    title: str
    prep_time: Optional[int] = None
    ingredients: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)


class MealPlanSchema(BaseModel):
    """Schema for an output meal plan."""
    id: Optional[str] = None
    user_id: str
    items: List[RecipeSchema] = Field(default_factory=list)
    created_at: Optional[datetime] = None


class MealLogSchema(BaseModel):
    """Schema for recording user adherence (eaten vs skipped)."""
    meal_id: str
    user_id: str
    status: str  # 'eaten' | 'skipped'
    reason: Optional[str] = None
    timestamp: Optional[datetime] = None


class FeedbackSchema(BaseModel):
    """Schema for user rating and recipe feedback."""
    user_id: str
    recipe_id: int
    rating: Optional[int] = None
    comments: Optional[str] = None
