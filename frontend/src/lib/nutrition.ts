import { GoalType, Gender, RecipeData, PantryItem, EffortLevel } from "@/types";

export interface ActiveSlotsMap {
  early_morning: boolean;
  breakfast: boolean;
  lunch: boolean;
  evening_snack: boolean;
  dinner: boolean;
}

export function calculateBMR(weight: number, height: number, age: number, gender: Gender): number {
  let val = 10 * weight + 6.25 * height - 5 * age;
  val = gender === "male" ? val + 5 : val - 161;
  return Math.round(val);
}

export function calculateTDEE(bmr: number, activity: number): number {
  return Math.round(bmr * activity);
}

export function calculateTargetCalories(tdee: number, goal: GoalType): number {
  if (goal === "lose_weight") {
    return Math.max(1200, tdee - 400);
  } else if (goal === "gain_weight") {
    return tdee + 300;
  }
  return tdee;
}

export function calculateMacroGrams(targetCalories: number) {
  return {
    carbsGrams: Math.round((targetCalories * 0.5) / 4),
    proteinGrams: Math.round((targetCalories * 0.2) / 4),
    fatGrams: Math.round((targetCalories * 0.3) / 9),
  };
}

export function checkPantryMatch(recipe: RecipeData, pantryItems: PantryItem[]) {
  const inStockNames = pantryItems
    .filter((i) => i.inStock)
    .map((i) => i.name.toLowerCase().trim());
  let matchCount = 0;
  const missing: string[] = [];
  const matched: string[] = [];

  recipe.requiredPantryItems.forEach((req) => {
    // Split requirement by "/" or "(" to extract keywords (e.g. "Paneer / Tofu" -> ["paneer", "tofu"])
    const cleanTokens = req
      .toLowerCase()
      .replace(/[()]/g, "")
      .split(/[\/,]/)
      .map((t) => t.trim())
      .filter((t) => t.length > 1);

    const isPresent = inStockNames.some((stock) => {
      // Direct substring match
      if (cleanTokens.some((tok) => stock.includes(tok) || tok.includes(stock))) {
        return true;
      }
      // Word-level token overlap
      const stockWords = stock.split(/[\s-]+/).filter((w) => w.length > 2);
      return cleanTokens.some((tok) => stockWords.some((w) => tok.includes(w) || w.includes(tok)));
    });

    if (isPresent) {
      matchCount++;
      matched.push(req);
    } else {
      missing.push(req);
    }
  });

  const isFullMatch = missing.length === 0 && recipe.requiredPantryItems.length > 0;
  return {
    isFullMatch,
    matchCount,
    total: recipe.requiredPantryItems.length,
    missing,
    matched,
  };
}

export interface CalculatedMealItem {
  key: keyof ActiveSlotsMap;
  recipe: RecipeData;
  calories: number;
  protein: number;
  carbs: number;
  fat: number;
  fibre: number;
  pctShare: number;
  pantryStatus: {
    isFullMatch: boolean;
    matchCount: number;
    total: number;
    missing: string[];
    matched: string[];
  };
  availableAlternatives?: RecipeData[];
}

export function calculateMealPlanItems(
  activeSlots: ActiveSlotsMap,
  targetCalories: number,
  macros: { carbsGrams: number; proteinGrams: number; fatGrams: number },
  weekdayBreakfastEffort: EffortLevel,
  weekdayLunchEffort: EffortLevel,
  recipeCatalog: Record<string, RecipeData>,
  pantryItems: PantryItem[],
  customSelectedRecipes?: Record<string, string>,
  prioritizePantry: boolean = true
): CalculatedMealItem[] {
  const slotBaseWeights: Record<keyof ActiveSlotsMap, { cal: number; prot: number; carb: number; fat: number }> = {
    early_morning: { cal: 0.05, prot: 0.06, carb: 0.03, fat: 0.09 },
    breakfast: { cal: 0.25, prot: 0.25, carb: 0.26, fat: 0.22 },
    lunch: { cal: 0.35, prot: 0.38, carb: 0.36, fat: 0.32 },
    evening_snack: { cal: 0.10, prot: 0.08, carb: 0.11, fat: 0.10 },
    dinner: { cal: 0.25, prot: 0.23, carb: 0.24, fat: 0.27 },
  };

  let totalActiveCalWeight = 0;
  (Object.keys(activeSlots) as (keyof ActiveSlotsMap)[]).forEach((slot) => {
    if (activeSlots[slot]) {
      totalActiveCalWeight += slotBaseWeights[slot].cal;
    }
  });

  const items: CalculatedMealItem[] = [];
  const slotOrder: (keyof ActiveSlotsMap)[] = ["early_morning", "breakfast", "lunch", "evening_snack", "dinner"];

  // Group all available recipes by slot
  const catalogList = Object.entries(recipeCatalog).map(([key, recipe]) => ({ key, recipe }));

  slotOrder.forEach((slot) => {
    if (activeSlots[slot]) {
      const normalizedRatio = slotBaseWeights[slot].cal / totalActiveCalWeight;
      const slotCals = Math.round(targetCalories * normalizedRatio);
      const slotProt = Math.round(macros.proteinGrams * normalizedRatio);
      const slotCarbs = Math.round(macros.carbsGrams * normalizedRatio);
      const slotFat = Math.round(macros.fatGrams * normalizedRatio);

      // Find all candidates for this slot
      const candidates = catalogList.filter(
        (c) => c.recipe.slotId === slot || c.key.startsWith(slot)
      );

      // Evaluate pantry match for all candidates
      const scoredCandidates = candidates.map((c) => {
        const pStatus = checkPantryMatch(c.recipe, pantryItems);
        const matchRatio = pStatus.total > 0 ? pStatus.matchCount / pStatus.total : 0;
        return {
          ...c,
          pStatus,
          matchRatio,
        };
      });

      // Sort candidates: highest pantry match first if prioritizePantry is true
      if (prioritizePantry) {
        scoredCandidates.sort((a, b) => {
          if (b.matchRatio !== a.matchRatio) {
            return b.matchRatio - a.matchRatio;
          }
          if (b.pStatus.matchCount !== a.pStatus.matchCount) {
            return b.pStatus.matchCount - a.pStatus.matchCount;
          }
          // Fall back to preferred effort level
          if (slot === "breakfast" && a.recipe.effortLevel === weekdayBreakfastEffort) return -1;
          if (slot === "lunch" && a.recipe.effortLevel === weekdayLunchEffort) return -1;
          return 0;
        });
      }

      // Check if user manually picked a recipe for this slot
      let chosen = scoredCandidates[0];
      const customKey = customSelectedRecipes?.[slot];
      if (customKey) {
        const found = scoredCandidates.find(
          (c) => c.key === customKey || c.recipe.name.toLowerCase() === customKey.toLowerCase()
        );
        if (found) chosen = found;
      }

      if (!chosen && recipeCatalog[slot]) {
        chosen = {
          key: slot,
          recipe: recipeCatalog[slot],
          pStatus: checkPantryMatch(recipeCatalog[slot], pantryItems),
          matchRatio: 0,
        };
      }

      const activeRecipe = chosen.recipe;
      const pantryStatus = chosen.pStatus;
      const alternatives = scoredCandidates.map((c) => c.recipe);

      items.push({
        key: slot,
        recipe: activeRecipe,
        calories: slotCals,
        protein: slotProt,
        carbs: slotCarbs,
        fat: slotFat,
        fibre: activeRecipe.baseFibreG,
        pctShare: Math.round(normalizedRatio * 100),
        pantryStatus,
        availableAlternatives: alternatives,
      });
    }
  });

  return items;
}
