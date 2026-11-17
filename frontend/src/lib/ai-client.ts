/**
 * DietSense — Typed AI API Client
 * Exclusively invokes local FastAPI backend endpoints under /api/ai.
 * Never directly invokes Google Gemini or handles third-party credentials.
 */

import { apiClient } from "./api-client";
import {
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
} from "@/types/ai";

export const aiApi = {
  /**
   * Conversational nutrition assistant.
   */
  askAssistant: (data: AIMealAssistantRequest): Promise<AIMealAssistantResponse> =>
    apiClient<AIMealAssistantResponse>("/api/ai/assistant", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  /**
   * Explains why a meal recommendation was selected using verified nutrition and score factors.
   */
  explainRecommendation: (
    foodId: number,
    data?: Partial<ExplainRecommendationRequest>
  ): Promise<ExplainRecommendationResponse> =>
    apiClient<ExplainRecommendationResponse>(`/api/ai/recommendations/${foodId}/explain`, {
      method: "POST",
      body: JSON.stringify({ food_id: foodId, ...(data || {}) }),
    }),

  /**
   * Suggests balanced recipes tailored to meal slot and calorie targets.
   */
  suggestRecipes: (data: RecipeSuggestionRequest): Promise<RecipeSuggestionResponse> =>
    apiClient<RecipeSuggestionResponse>("/api/ai/recipes/suggest", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  /**
   * Generates low-waste home meals utilizing available pantry items.
   */
  pantryCook: (data: PantryCookingRequest): Promise<PantryCookingResponse> =>
    apiClient<PantryCookingResponse>("/api/ai/pantry/cook", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  /**
   * Performs an objective side-by-side macronutrient comparison for 2 to 5 meals.
   */
  compareMeals: (data: MealComparisonRequest): Promise<MealComparisonResponse> =>
    apiClient<MealComparisonResponse>("/api/ai/compare", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  /**
   * Generates step-by-step beginner-friendly culinary instructions with scaled nutrition.
   */
  getCookingInstructions: (
    foodId: number,
    data?: Partial<CookingInstructionRequest>
  ): Promise<CookingInstructionResponse> =>
    apiClient<CookingInstructionResponse>(`/api/ai/recipes/${foodId}/instructions`, {
      method: "POST",
      body: JSON.stringify({ food_id: foodId, ...(data || {}) }),
    }),
};
