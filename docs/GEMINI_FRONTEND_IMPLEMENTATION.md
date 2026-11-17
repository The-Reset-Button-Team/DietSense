# DietSense Gemini Frontend Integration (Phase 7)

## 1. Overview & Architecture

Phase 7 integrates the Google Gemini-powered AI backend (implemented in Phase 6) into the DietSense Next.js 14 frontend.
All AI features respect DietSense's core architectural and safety principles:
- **No Direct Browser-to-Gemini Calls**: The Next.js frontend interacts strictly with DietSense FastAPI endpoints (`/api/ai/*`) via the authenticated `apiClient()`.
- **Zero API Key Exposure**: No `GEMINI_API_KEY` or `NEXT_PUBLIC_GEMINI_*` variables are bundled or accessible in client-side code.
- **Nutrition Ground Truth**: All nutritional values displayed in the UI are anchored in authoritative USDA / ICMR-NIN database queries retrieved through the backend.
- **Dietary & Allergen Pre-Filtering**: The deterministic safety shield runs before AI processing.
- **Non-Diagnostic Medical Disclaimer**: Every AI view and modal visibly displays the standard disclaimer: *"Dataset estimates only. Not medical advice or diagnosis."*
- **Visual Identity Preservation**: Seamlessly adopts DietSense's warm editorial aesthetic (cream `#faf7f2`, deep maroon `#581825`, serif headings, rounded-3xl cards).

```
┌─────────────────────────────────────────────────────────────┐
│                   DietSense Next.js Frontend                │
│                                                             │
│  ┌────────────────────┐  ┌───────────────────────────────┐  │
│  │    MealCard.tsx    │  │       TabNav.tsx ("ai")       │  │
│  │ ✨ Explain with AI │  │   🤖 Evidence AI Meal Coach   │  │
│  │ 👨‍🍳 AI Cooking      │  └───────────────┬───────────────┘  │
│  └─────────┬──────────┘                  │                  │
│            ▼                             ▼                  │
│  ┌────────────────────┐  ┌───────────────────────────────┐  │
│  │ AIExplanationModal │  │       AIAssistantView         │  │
│  │ CookingInstructModal│ │  - Interactive Chat           │  │
│  │ MealComparisonModal│  │  - Context Grounding Picker   │  │
│  │ PantryCookAssistant│  │  - Starter Inquiries          │  │
│  │ RecipeSuggestView  │  │  - Recipe Suggestions         │  │
│  └─────────┬──────────┘  └───────────────┬───────────────┘  │
│            │                             │                  │
│            └──────────────┬──────────────┘                  │
│                           ▼                                 │
│                    lib/ai-client.ts                         │
│                    (Typed API Client)                       │
└───────────────────────────┬─────────────────────────────────┘
                            │ HTTP POST (Cookie / Bearer Auth)
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                 FastAPI Backend (/api/ai/*)                 │
│                                                             │
│   Rate Limiter ──► SQLite DB (Verified Nutrition)           │
│   SHA-256 Cache ──► Google Gemini API (or Rule Fallback)    │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Component Inventory

| Component | File Path | Description & Features |
|---|---|---|
| **Typed AI Client** | `frontend/src/lib/ai-client.ts` | 6 typed methods (`askAssistant`, `explainRecommendation`, `suggestRecipes`, `pantryCook`, `compareMeals`, `getCookingInstructions`) calling `/api/ai/*`. |
| **TypeScript Types** | `frontend/src/types/ai.ts` | Full TypeScript interfaces mirroring backend Pydantic models with verified nutrition. |
| **AI Meal Assistant** | `frontend/src/components/ai/AIAssistantView.tsx` | Full-featured conversational coach with meal context selection, starter prompt chips, message stream with loading spinners, retry banners, and evidence source badges. |
| **Meal Explanation Modal** | `frontend/src/components/ai/AIExplanationModal.tsx` | Triggered by "✨ Explain with AI" button on any meal card. Shows headline, why recommended, key health benefits, chef tip, verified nutrition grid, and "Ask AI about this meal" shortcut. |
| **AI Cooking Guide Modal** | `frontend/src/components/ai/CookingInstructionsModal.tsx` | Triggered by "👨‍🍳 AI Cooking". Step-by-step culinary guide with servings adjuster, skill level selector (beginner/intermediate/advanced), kitchen equipment, and pro chef tips. |
| **Meal Comparison Modal** | `frontend/src/components/ai/MealComparisonModal.tsx` | Multi-meal comparator (2-5 items). Food selector chips, priority selector (protein, calories, fiber, balanced), winner badge, side-by-side macro comparison table, and trade-offs. |
| **Pantry Cooking Assistant** | `frontend/src/components/ai/PantryCookAssistant.tsx` | Embedded directly into Grocery AI Scanner tab. Takes OCR-scanned grocery receipts & pantry stock, generates zero-waste recipes with prep time filter (15/25/40 min). |
| **Recipe Suggestions** | `frontend/src/components/ai/RecipeSuggestionView.tsx` | Slot-based creative recipe finder with calorie target and cuisine preferences (Indian, Pan-Asian, Mediterranean). |
| **Updated MealCard** | `frontend/src/components/MealCard.tsx` | Added "✨ Explain with AI" and "👨‍🍳 AI Cooking" interactive action buttons. |
| **Updated TabNav** | `frontend/src/components/TabNav.tsx` | Added 7th tab: `🤖 AI Meal Coach`. |
| **Root Page Integration** | `frontend/src/app/page.tsx` | Full state management, context forwarding ("Ask AI about this meal"), global modal overlays, and responsive rendering. |

---

## 3. UI States Implemented

Every AI view implements all 4 essential UX states:
1. **Loading State**: Subtle pulsing spinners and informative copy ("Consulting USDA & ICMR-NIN verified nutrition data...", "Matching scanned pantry items with clinical catalog...").
2. **Error State**: Amber/Red banner with exact error message and an interactive **Retry** button.
3. **Empty State**: Guided onboarding illustrations, explanatory benefits, and clickable quick starters.
4. **Success State**: Richly formatted cards with verified nutrition numbers, effort tags, and fallback indicators ("Evidence Engine" vs "Gemini 3.8 Flash").

---

## 4. End-to-End User Journeys

### Journey 1: Meal Plan Card ➔ Explanation ➔ AI Chat
1. User views daily meal plan on the **"Daily Meal Plan"** tab.
2. User clicks **"✨ Explain with AI"** on any dish card.
3. `AIExplanationModal` opens, calls `POST /api/ai/recommendations/{food_id}/explain`, and renders verified calories, protein, carbs, and health rationale.
4. User clicks **"💬 Ask AI about this meal"**.
5. Modal closes, active tab switches to **"AI Meal Coach"**, and input is pre-populated with context set to the selected meal.

### Journey 2: Scanned Grocery Bill ➔ Pantry Cooking
1. User scans a supermarket bill in the **"Grocery AI Scanner & Pantry"** tab.
2. Items are recognized and saved to in-stock pantry items.
3. Below the scanner, user clicks **"✨ Generate Pantry Recipe"** in `PantryCookAssistant`.
4. Backend matches in-stock items against verified food profiles and returns zero-waste recipes using what's already in the kitchen.

### Journey 3: Comparing Two Dishes for High Protein
1. In the **"AI Meal Coach"** tab, user clicks **"⚖️ Compare Meals"**.
2. User checks 2 or 3 dishes from the catalog.
3. User selects priority: *"High Protein"*.
4. System displays side-by-side macronutrient table with winner highlighted and trade-off explanations.

---

## 5. Security & Verification

- **Automated Frontend Contract Tests**: `tests/test_gemini_frontend_contract.py` verifies zero secret leaks and strict routing.
- **TypeScript Static Verification**: `npm run type-check` compiles with zero errors across all components.
- **Production Build**: Verified with Next.js production build (`next build`).
