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
  const inStockNames = pantryItems.filter((i) => i.inStock).map((i) => i.name.toLowerCase());
  let matchCount = 0;
  const missing: string[] = [];

  recipe.requiredPantryItems.forEach((req) => {
    const isPresent = inStockNames.some(
      (stock) => stock.includes(req.toLowerCase()) || req.toLowerCase().includes(stock)
    );
    if (isPresent) {
      matchCount++;
    } else {
      missing.push(req);
    }
  });

  const isFullMatch = missing.length === 0;
  return { isFullMatch, matchCount, total: recipe.requiredPantryItems.length, missing };
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
  pantryStatus: { isFullMatch: boolean; missing: string[] };
}

export function calculateMealPlanItems(
  activeSlots: ActiveSlotsMap,
  targetCalories: number,
  macros: { carbsGrams: number; proteinGrams: number; fatGrams: number },
  weekdayBreakfastEffort: EffortLevel,
  weekdayLunchEffort: EffortLevel,
  recipeCatalog: Record<string, RecipeData>,
  pantryItems: PantryItem[]
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

  slotOrder.forEach((slot) => {
    if (activeSlots[slot]) {
      const normalizedRatio = slotBaseWeights[slot].cal / totalActiveCalWeight;
      const slotCals = Math.round(targetCalories * normalizedRatio);
      const slotProt = Math.round(macros.proteinGrams * normalizedRatio);
      const slotCarbs = Math.round(macros.carbsGrams * normalizedRatio);
      const slotFat = Math.round(macros.fatGrams * normalizedRatio);

      let recipe = recipeCatalog[slot];
      if (slot === "breakfast") {
        recipe = weekdayBreakfastEffort === "low" ? recipeCatalog.breakfast_low_effort : recipeCatalog.breakfast_instant;
      } else if (slot === "lunch") {
        recipe = weekdayLunchEffort === "moderate" ? recipeCatalog.lunch_moderate_effort : recipeCatalog.lunch_one_pot;
      }

      const pantryStatus = checkPantryMatch(recipe, pantryItems);

      items.push({
        key: slot,
        recipe,
        calories: slotCals,
        protein: slotProt,
        carbs: slotCarbs,
        fat: slotFat,
        fibre: recipe.baseFibreG,
        pctShare: Math.round(normalizedRatio * 100),
        pantryStatus,
      });
    }
  });

  return items;
}
