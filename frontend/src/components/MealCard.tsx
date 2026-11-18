"use client";

import React, { useState } from "react";
import Image from "next/image";
import { RecipeData } from "@/types";
import { CalculatedMealItem } from "@/lib/nutrition";

interface MealCardProps {
  item: CalculatedMealItem;
  slotIndex: number;
  isActiveWindow?: boolean;
  onOpenRecipe: (recipe: RecipeData) => void;
  onSelectAlternative?: (slotKey: string, recipeName: string) => void;
  onExplainWithAI?: (foodId: number, foodName: string) => void;
  onCookWithAI?: (foodId: number, foodName: string) => void;
  onSkipSlot?: (slotKey: string, mealName: string) => void;
  reason?: string;
}

export const MealCard: React.FC<MealCardProps> = ({
  item,
  slotIndex,
  isActiveWindow = false,
  onOpenRecipe,
  onSelectAlternative,
  onExplainWithAI,
  onCookWithAI,
  onSkipSlot,
  reason,
}) => {
  const [isEaten, setIsEaten] = useState(slotIndex === 0); // Slot 1 default eaten like Stitch mock
  const [showSwapModal, setShowSwapModal] = useState(false);

  // Asset image based on slot index
  const slotImages: Record<number, string> = {
    0: "/stitch/assets/stitch_asset_07.png", // Palak Moong Dal Chilla
    1: "/stitch/assets/stitch_asset_03.png", // Paneer Bhurji with Multigrain Roti
    2: "/stitch/assets/stitch_asset_02.png", // Roasted Chana & Makhana
    3: "/stitch/assets/stitch_asset_04.png", // Tofu & Broccoli
  };

  const imageSrc = slotImages[slotIndex % 4] || "/stitch/assets/stitch_asset_03.png";

  const slotTimeLabels: Record<number, string> = {
    0: "Slot 1 • 9:00 AM",
    1: "Slot 2 • 1:30 PM",
    2: "Slot 3 • 5:00 PM",
    3: "Slot 4 • 8:30 PM",
  };

  const slotLabel = slotTimeLabels[slotIndex] || `Slot ${slotIndex + 1} • ${item.recipe.timeSlot}`;

  return (
    <article
      className={`bg-surface-container-lowest p-space-md md:p-space-lg rounded-xl shadow-sm transition-all hover:shadow-md border border-surface-container ${
        isActiveWindow && !isEaten ? "ring-2 ring-primary/20 shadow-md" : ""
      }`}
    >
      {/* Slot Header Status */}
      <div className="flex items-start justify-between gap-space-sm pb-space-sm border-b border-surface-container">
        <div className="flex items-center gap-space-xs flex-wrap">
          <span
            className={`px-2.5 py-1 font-label-sm text-label-sm rounded uppercase font-bold ${
              isActiveWindow && !isEaten
                ? "bg-primary text-on-primary"
                : "bg-surface-container text-on-surface-variant"
            }`}
          >
            {slotLabel}
          </span>
          <span className="font-label-sm text-label-sm text-on-surface-variant">
            {item.recipe.slotLabel}
          </span>

          {isActiveWindow && !isEaten && (
            <span className="font-label-sm text-label-sm text-primary font-semibold flex items-center gap-1 ml-1">
              <span className="w-2 h-2 rounded-full bg-primary animate-ping" />
              Current Active Window
            </span>
          )}
        </div>

        {isEaten ? (
          <div className="flex items-center gap-1.5 bg-secondary/10 px-space-sm py-1 rounded-full text-secondary">
            <span className="material-symbols-outlined text-[16px]">check_circle</span>
            <span className="font-label-sm text-label-sm font-bold">Eaten &amp; Logged</span>
          </div>
        ) : (
          <span className="px-2.5 py-0.5 bg-surface-container font-label-sm text-label-sm rounded-full text-on-surface-variant">
            High Satiety Score (8.9/10)
          </span>
        )}
      </div>

      {/* Card Body */}
      <div className="flex flex-col sm:flex-row items-start gap-space-md pt-space-sm">
        <div className="relative w-full sm:w-32 h-32 rounded-lg overflow-hidden bg-surface-container shrink-0 border border-surface-container">
          <Image
            src={imageSrc}
            alt={item.recipe.name}
            fill
            className="object-cover"
            sizes="(max-width: 640px) 100vw, 128px"
          />
        </div>

        <div className="space-y-space-xs flex-1 min-w-0">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <h3 className="font-headline-sm text-headline-sm text-primary font-serif">
              {item.recipe.name}
            </h3>
            <span className="px-2 py-0.5 rounded font-label-sm text-label-sm bg-surface-container text-on-surface-variant shrink-0">
              {item.recipe.badge || "ICMR-NIN Validated"}
            </span>
          </div>

          {/* Explainable Recommendation Match Pill */}
          <div className="p-space-xs bg-surface-container-low rounded-lg flex flex-wrap items-center gap-y-1 gap-x-space-sm font-label-sm text-label-sm text-on-surface-variant border border-surface-container">
            <span className="flex items-center gap-1 text-primary font-bold">
              <span className="material-symbols-outlined text-[15px]">auto_awesome</span>
              Explainable Match:
            </span>
            <span className="text-secondary font-semibold">+0.42 taste profile</span>
            <span>•</span>
            <span className="text-primary font-semibold">+0.30 macro fit</span>
            <span>•</span>
            <span className="text-on-surface flex items-center gap-1 font-semibold">
              <span className="material-symbols-outlined text-[13px] text-secondary">
                inventory_2
              </span>
              {item.pantryStatus.isFullMatch
                ? "100% Pantry in-stock"
                : item.pantryStatus.matched && item.pantryStatus.matched.length > 0
                ? `${item.pantryStatus.matched.length} ingredients in stock`
                : "Pantry in-stock match"}
            </span>
          </div>

          <p className="font-body-sm text-body-sm text-on-surface-variant pt-0.5">
            {item.recipe.tagline}
          </p>

          {/* Macronutrient Chips */}
          <div className="flex flex-wrap items-center gap-space-xs pt-1">
            <span className="px-2 py-0.5 rounded-full font-label-sm text-label-sm bg-primary/10 text-primary font-bold">
              {item.protein}g Protein
            </span>
            <span className="px-2 py-0.5 rounded-full font-label-sm text-label-sm bg-amber-500/10 text-amber-700 font-medium">
              {item.carbs}g Carbs
            </span>
            <span className="px-2 py-0.5 rounded-full font-label-sm text-label-sm bg-secondary/10 text-secondary font-medium">
              {item.fat}g Fat
            </span>
            <span className="px-2 py-0.5 rounded-full font-label-sm text-label-sm bg-surface-container text-on-surface font-semibold">
              {item.calories} kcal
            </span>
            <span className="font-label-sm text-label-sm text-on-surface-variant ml-auto flex items-center gap-1">
              <span className="material-symbols-outlined text-[14px]">timer</span>
              {item.recipe.prepTimeMins || 18} min prep
            </span>
          </div>
        </div>
      </div>

      {/* Action Cluster (For Active / Upcoming meals) */}
      <div className="flex flex-wrap items-center justify-between gap-space-sm pt-space-xs mt-space-sm border-t border-surface-container">
        <div className="flex flex-wrap items-center gap-space-xs">
          <button
            type="button"
            onClick={() => setIsEaten(!isEaten)}
            className={`px-space-md py-2 rounded font-label-md text-label-md transition-all shadow-sm flex items-center gap-space-xs active:scale-[0.99] ${
              isEaten
                ? "bg-secondary/10 text-secondary border border-secondary/20"
                : "bg-primary hover:bg-primary-container text-on-primary"
            }`}
          >
            <span className="material-symbols-outlined text-[18px]">
              {isEaten ? "undo" : "check"}
            </span>
            {isEaten ? "Logged as Eaten" : "Mark Eaten"}
          </button>

          <button
            type="button"
            onClick={() => onOpenRecipe(item.recipe)}
            className="px-space-md py-2 bg-surface-container hover:bg-surface-container-high text-on-surface rounded font-label-md text-label-md transition-all flex items-center gap-space-xs"
          >
            <span className="material-symbols-outlined text-[18px]">menu_book</span>
            View Recipe &amp; Solo Hacks
          </button>

          {onExplainWithAI && (
            <button
              type="button"
              onClick={() => onExplainWithAI(item.recipe.id || 1, item.recipe.name)}
              className="px-space-sm py-2 bg-primary/10 text-primary hover:bg-primary/20 rounded font-label-md text-label-md transition-all flex items-center gap-1"
            >
              <span className="material-symbols-outlined text-[16px]">psychology</span>
              Explain with AI
            </button>
          )}

          {onCookWithAI && (
            <button
              type="button"
              onClick={() => onCookWithAI(item.recipe.id || 1, item.recipe.name)}
              className="px-space-sm py-2 bg-secondary/10 text-secondary hover:bg-secondary/20 rounded font-label-md text-label-md transition-all flex items-center gap-1"
            >
              <span className="material-symbols-outlined text-[16px]">smart_toy</span>
              AI Cooking
            </button>
          )}
        </div>

        <div className="flex items-center gap-space-xs">
          {onSkipSlot && (
            <button
              type="button"
              onClick={() => onSkipSlot(item.key, item.recipe.name)}
              className="px-space-sm py-2 text-on-surface-variant hover:text-error hover:bg-surface-container-low rounded font-label-md text-label-md transition-all flex items-center gap-1"
            >
              <span className="material-symbols-outlined text-[16px]">cancel</span>
              Skip Meal
            </button>
          )}

          <button
            type="button"
            onClick={() => setShowSwapModal(true)}
            className="px-space-sm py-2 text-primary hover:bg-primary/5 rounded font-label-md text-label-md transition-all flex items-center gap-1"
          >
            <span className="material-symbols-outlined text-[16px]">cached</span>
            Swap Slot
          </button>
        </div>
      </div>

      {/* Alternatives Flyout Modal */}
      {showSwapModal && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-sm flex items-center justify-center p-space-md animate-in fade-in">
          <div className="bg-surface-container-lowest max-w-lg w-full rounded-xl p-space-lg shadow-xl space-y-space-md border border-surface-container">
            <div className="flex items-center justify-between border-b border-surface-container pb-space-xs">
              <div>
                <h4 className="font-headline-sm text-headline-sm text-primary font-serif">
                  Swap {item.recipe.slotLabel}
                </h4>
                <p className="font-body-sm text-body-sm text-on-surface-variant">
                  Equivalent USDA &amp; ICMR-NIN verified alternates that fit your caloric budget.
                </p>
              </div>
              <button
                type="button"
                onClick={() => setShowSwapModal(false)}
                className="text-on-surface-variant hover:text-on-surface p-1"
              >
                <span className="material-symbols-outlined text-[20px]">close</span>
              </button>
            </div>

            <div className="space-y-2 max-h-72 overflow-y-auto">
              {(item.availableAlternatives || []).map((alt: RecipeData, idx: number) => (
                <div
                  key={idx}
                  className="p-space-sm bg-surface-container-low rounded-lg border border-surface-container flex items-center justify-between gap-3 hover:border-primary transition-all"
                >
                  <div>
                    <h5 className="font-headline-sm text-sm text-on-surface font-serif">
                      {alt.name}
                    </h5>
                    <p className="text-body-sm text-on-surface-variant font-body-sm">
                      {alt.prepTimeMins || 15}m prep • {alt.badge || "Verified"}
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={() => {
                      if (onSelectAlternative) {
                        onSelectAlternative(item.key, alt.name);
                      }
                      setShowSwapModal(false);
                    }}
                    className="px-3 py-1.5 bg-primary text-on-primary rounded font-label-sm text-label-sm hover:bg-primary-container"
                  >
                    Select
                  </button>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </article>
  );
};
