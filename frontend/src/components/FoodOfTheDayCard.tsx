"use client";

import React, { useState, useEffect, useCallback } from "react";
import { apiClient } from "@/lib/api-client";
import { useAuth } from "@/context/AuthContext";
import { FoodOfTheDayResponse, FoodOfTheDayItem } from "@/types";

interface FoodOfTheDayCardProps {
  onPantryUpdated?: () => void;
  onExploreSimilar?: (category: string) => void;
  onOpenCatalogFood?: (foodId: number) => void;
}

export const FoodOfTheDayCard: React.FC<FoodOfTheDayCardProps> = ({
  onPantryUpdated,
  onExploreSimilar,
  onOpenCatalogFood,
}) => {
  const { isAuthenticated } = useAuth();

  const [data, setData] = useState<FoodOfTheDayResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Modal and action states
  const [isDetailModalOpen, setIsDetailModalOpen] = useState<boolean>(false);
  const [isAddingToPantry, setIsAddingToPantry] = useState<boolean>(false);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  // Region switcher for card
  const [selectedRegion, setSelectedRegion] = useState<string>("National");

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 3500);
  };

  const fetchFoodOfTheDay = useCallback(async (region: string = selectedRegion) => {
    setIsLoading(true);
    setErrorMsg(null);
    try {
      const res = await apiClient<FoodOfTheDayResponse>(
        `/api/foods/food-of-the-day?region=${encodeURIComponent(region)}`
      );
      setData(res);
    } catch (err: any) {
      console.error("Failed to load Food of the Day:", err);
      setErrorMsg(err.message || "Unable to fetch today's featured food.");
    } finally {
      setIsLoading(false);
    }
  }, [selectedRegion]);

  useEffect(() => {
    fetchFoodOfTheDay(selectedRegion);
  }, [fetchFoodOfTheDay, selectedRegion]);

  // Handle Add to Pantry
  const handleAddToPantry = async (foodId: number) => {
    if (!isAuthenticated) {
      showToast("Please sign in to add ingredients to your pantry.");
      return;
    }

    setIsAddingToPantry(true);
    try {
      const res = await apiClient<{
        status: string;
        message: string;
        already_in_pantry: boolean;
        pantry_item: any;
      }>(`/api/foods/${foodId}/add-to-pantry`, {
        method: "POST",
        body: JSON.stringify({ quantity: "1 unit", in_stock: true }),
      });

      // Update local pantry state immediately
      setData((prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          food: {
            ...prev.food,
            pantry: {
              in_pantry: true,
              pantry_item_id: res.pantry_item?.id || "pantry_added",
              pantry_quantity: res.pantry_item?.quantity || "1 unit",
              pantry_in_stock: true,
              pantry_expiry_date: null,
            },
          },
        };
      });

      showToast(res.message || "Added to your pantry!");
      if (onPantryUpdated) {
        onPantryUpdated();
      }
    } catch (err: any) {
      console.error("Error adding to pantry:", err);
      showToast(err.message || "Failed to add food to pantry.");
    } finally {
      setIsAddingToPantry(false);
    }
  };

  // Helper for category-based icon / visual badge
  const getCategoryIcon = (category: string) => {
    const cat = category.toLowerCase();
    if (cat.includes("cereal") || cat.includes("millet")) return "grain";
    if (cat.includes("legume") || cat.includes("pulse") || cat.includes("dal")) return "spa";
    if (cat.includes("vegetable") || cat.includes("leafy")) return "eco";
    if (cat.includes("fruit")) return "nutrition";
    if (cat.includes("milk") || cat.includes("dairy")) return "local_drink";
    if (cat.includes("nut") || cat.includes("seed")) return "egg_alt";
    if (cat.includes("spice") || cat.includes("condiment")) return "local_fire_department";
    if (cat.includes("meat") || cat.includes("poultry") || cat.includes("fish")) return "set_meal";
    return "restaurant";
  };

  // Loading Skeleton State
  if (isLoading) {
    return (
      <div className="bg-white rounded-2xl border border-slate-200/90 p-5 md:p-6 shadow-sm animate-pulse space-y-4">
        <div className="flex items-center justify-between">
          <div className="h-6 bg-slate-200 rounded-full w-40" />
          <div className="h-5 bg-slate-100 rounded w-24" />
        </div>
        <div className="flex flex-col md:flex-row gap-5 items-start">
          <div className="w-24 h-24 rounded-2xl bg-slate-100 shrink-0" />
          <div className="flex-1 space-y-2 w-full">
            <div className="h-6 bg-slate-200 rounded w-1/2" />
            <div className="h-4 bg-slate-100 rounded w-full" />
            <div className="h-4 bg-slate-100 rounded w-3/4" />
            <div className="grid grid-cols-5 gap-2 pt-2">
              {[0, 1, 2, 3, 4].map((i) => (
                <div key={i} className="h-10 bg-slate-100 rounded" />
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Error State
  if (errorMsg || !data) {
    return (
      <div className="bg-white rounded-2xl border border-slate-200/90 p-6 text-center space-y-3 shadow-sm">
        <div className="w-12 h-12 rounded-full bg-slate-100 text-slate-400 mx-auto flex items-center justify-center">
          <span className="material-symbols-outlined text-[28px]">error_outline</span>
        </div>
        <h4 className="font-bold text-[#142D4E] text-base">Food of the Day Unavailable</h4>
        <p className="text-xs text-slate-500 max-w-md mx-auto">
          {errorMsg || "Could not retrieve today's featured food item from the database."}
        </p>
        <button
          type="button"
          onClick={() => fetchFoodOfTheDay()}
          className="px-4 py-2 bg-[#142D4E] hover:bg-[#1b3d6a] text-white text-xs font-semibold rounded-lg transition-colors inline-flex items-center gap-1.5"
        >
          <span className="material-symbols-outlined text-[16px]">refresh</span>
          <span>Retry</span>
        </button>
      </div>
    );
  }

  const { food, similar_foods } = data;
  const inPantry = food.pantry?.in_pantry;
  const pricing = food.pricing;
  const editorial = food.editorial;
  const micronutrients = food.micronutrients;

  // Filter non-null micronutrients
  const availableMicros = Object.entries(micronutrients || {}).filter(
    ([, val]) => val !== null && val !== undefined && val > 0
  );

  return (
    <>
      {/* Toast Notification */}
      {toastMessage && (
        <div className="fixed bottom-6 right-6 z-50 bg-[#142D4E] text-white text-xs md:text-sm font-semibold px-4 py-2.5 rounded-xl shadow-2xl flex items-center gap-2 animate-in fade-in slide-in-from-bottom-2 duration-150">
          <span className="material-symbols-outlined text-[18px] text-[#16A66A]">check_circle</span>
          <span>{toastMessage}</span>
        </div>
      )}

      {/* Main Food of the Day Card */}
      <section className="bg-gradient-to-br from-white via-[#FCFDFD] to-[#F2FAF6] rounded-2xl border border-[#16A66A]/25 p-5 md:p-6 shadow-sm hover:shadow-md transition-all relative overflow-hidden">
        {/* Subtle decorative emerald glow corner */}
        <div className="absolute top-0 right-0 w-44 h-44 bg-[#DDF5E8]/40 rounded-full blur-3xl -z-10 pointer-events-none" />

        {/* Card Header: Badge & Date */}
        <div className="flex flex-wrap items-center justify-between gap-2 pb-4 border-b border-slate-100">
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-[#DDF5E8] text-[#0E6842] border border-[#16A66A]/30">
              <span className="material-symbols-outlined text-[16px] text-[#16A66A]">
                stars
              </span>
              <span>Food of the Day</span>
            </span>
            <span className="text-xs text-slate-500 font-medium">
              Featured on {data.date}
            </span>
          </div>

          {/* Region Switcher */}
          <div className="flex items-center gap-1.5 text-xs">
            <span className="text-slate-400 font-medium hidden sm:inline">Region:</span>
            <select
              value={selectedRegion}
              onChange={(e) => {
                setSelectedRegion(e.target.value);
                fetchFoodOfTheDay(e.target.value);
              }}
              className="py-1 px-2.5 bg-white border border-slate-200 rounded-lg text-xs font-semibold text-slate-700 focus:outline-none focus:ring-1 focus:ring-[#16A66A] shadow-sm"
              title="Select pricing benchmark region"
            >
              <option value="National">🇮🇳 National</option>
              <option value="Delhi">📍 Delhi</option>
              <option value="Mumbai">📍 Mumbai</option>
              <option value="Bengaluru">📍 Bengaluru</option>
              <option value="Kolkata">📍 Kolkata</option>
            </select>
          </div>
        </div>

        {/* Card Content Layout */}
        <div className="pt-4 grid grid-cols-1 md:grid-cols-12 gap-5 items-start">
          {/* Visual Column: Food Emblem / Illustration & Category */}
          <div className="md:col-span-3 flex flex-row md:flex-col items-center md:items-start gap-4">
            <div className="w-20 h-20 md:w-28 md:h-28 rounded-2xl bg-[#DDF5E8] text-[#16A66A] flex items-center justify-center border border-[#16A66A]/30 shadow-inner shrink-0 group relative overflow-hidden">
              <span className="material-symbols-outlined text-[42px] md:text-[54px] text-[#0E6842] group-hover:scale-110 transition-transform">
                {getCategoryIcon(food.food_category)}
              </span>
            </div>

            <div className="space-y-1">
              <span className="text-[11px] font-bold tracking-wider text-slate-500 uppercase block">
                {food.food_category}
              </span>
              <span className="text-xs text-slate-400 font-medium block">
                Source: {food.data_source}
              </span>

              {/* In Pantry Indicator */}
              <div className="pt-1">
                {inPantry ? (
                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-bold bg-[#DDF5E8] text-[#0E6842] border border-[#16A66A]/30">
                    <span className="material-symbols-outlined text-[13px]">check_circle</span>
                    <span>In Your Pantry ({food.pantry?.pantry_quantity || "1 unit"})</span>
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-medium bg-slate-100 text-slate-600">
                    <span className="material-symbols-outlined text-[13px]">inventory_2</span>
                    <span>Not in Pantry</span>
                  </span>
                )}
              </div>
            </div>
          </div>

          {/* Details & Nutrition Column */}
          <div className="md:col-span-9 space-y-4">
            {/* Title & Introduction */}
            <div>
              <div className="flex flex-wrap items-baseline gap-2">
                <h3 className="font-extrabold text-[#142D4E] text-lg md:text-xl font-serif">
                  {food.name}
                </h3>
                {food.name_local && food.name_local !== food.name && (
                  <span className="text-sm font-medium text-slate-500 italic">
                    ({food.name_local})
                  </span>
                )}
              </div>
              <p className="text-xs md:text-sm text-slate-600 mt-1 leading-relaxed">
                {editorial.short_intro}
              </p>
            </div>

            {/* Nutrition Highlights Grid per 100g */}
            <div className="bg-white p-3 rounded-xl border border-slate-200/80 shadow-sm space-y-2">
              <div className="flex items-center justify-between text-[11px] text-slate-500 font-semibold uppercase tracking-wider">
                <span>Verified Nutrition (per 100g serving)</span>
                {food.fiber_g !== null && food.fiber_g !== undefined && (
                  <span className="text-indigo-700 lowercase font-normal">
                    fiber: {food.fiber_g}g
                  </span>
                )}
              </div>

              <div className="grid grid-cols-4 sm:grid-cols-5 gap-2 text-center">
                <div className="p-2 bg-slate-50 rounded-lg border border-slate-100">
                  <span className="block text-[10px] text-slate-500 uppercase">Energy</span>
                  <strong className="block text-sm md:text-base font-bold text-slate-900">
                    {Math.round(food.calories_kcal)}
                  </strong>
                  <span className="text-[10px] text-slate-400">kcal</span>
                </div>
                <div className="p-2 bg-slate-50 rounded-lg border border-slate-100">
                  <span className="block text-[10px] text-slate-500 uppercase">Protein</span>
                  <strong className="block text-sm md:text-base font-bold text-emerald-700">
                    {food.protein_g}g
                  </strong>
                  <span className="text-[10px] text-slate-400">macros</span>
                </div>
                <div className="p-2 bg-slate-50 rounded-lg border border-slate-100">
                  <span className="block text-[10px] text-slate-500 uppercase">Carbs</span>
                  <strong className="block text-sm md:text-base font-bold text-amber-700">
                    {food.carbohydrates_g}g
                  </strong>
                  <span className="text-[10px] text-slate-400">complex</span>
                </div>
                <div className="p-2 bg-slate-50 rounded-lg border border-slate-100">
                  <span className="block text-[10px] text-slate-500 uppercase">Fats</span>
                  <strong className="block text-sm md:text-base font-bold text-rose-700">
                    {food.fat_g}g
                  </strong>
                  <span className="text-[10px] text-slate-400">healthy</span>
                </div>
                <div className="hidden sm:block p-2 bg-slate-50 rounded-lg border border-slate-100">
                  <span className="block text-[10px] text-slate-500 uppercase">Fiber</span>
                  <strong className="block text-sm md:text-base font-bold text-indigo-700">
                    {food.fiber_g !== null && food.fiber_g !== undefined ? `${food.fiber_g}g` : "0g"}
                  </strong>
                  <span className="text-[10px] text-slate-400">dietary</span>
                </div>
              </div>

              {/* Key Micronutrient Chips if available */}
              {availableMicros.length > 0 && (
                <div className="flex flex-wrap items-center gap-1.5 pt-1 border-t border-slate-100">
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mr-1">
                    Minerals &amp; Vitamins:
                  </span>
                  {availableMicros.slice(0, 4).map(([key, val]) => {
                    const label = key.replace("_mg", " mg").replace("_mcg", " mcg").replace("_", " ");
                    return (
                      <span
                        key={key}
                        className="text-[10px] font-semibold bg-slate-100 text-slate-700 px-2 py-0.5 rounded capitalize"
                      >
                        {label}: {val}
                      </span>
                    );
                  })}
                </div>
              )}
            </div>

            {/* Price & Primary Action Strip */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-1">
              {/* Indian Pricing Badge */}
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-lg bg-[#DDF5E8] text-[#16A66A] flex items-center justify-center shrink-0">
                  <span className="material-symbols-outlined text-[18px]">payments</span>
                </div>
                <div>
                  <div className="flex items-center gap-1.5">
                    <span className="font-extrabold text-[#142D4E] text-base md:text-lg">
                      {pricing.available ? pricing.formatted_price : "Price unavailable"}
                    </span>
                    {pricing.available && pricing.price_type === "verified" && (
                      <span
                        className="text-[10px] font-bold bg-[#DDF5E8] text-[#0E6842] border border-[#16A66A]/30 px-1.5 py-0.5 rounded-full"
                        title={`Verified by ${pricing.source || "Mandi Price Cell"}`}
                      >
                        ✓ Verified
                      </span>
                    )}
                    {pricing.available && pricing.price_type === "estimated" && (
                      <span
                        className="text-[10px] font-semibold bg-amber-50 text-amber-800 border border-amber-200 px-1.5 py-0.5 rounded-full"
                        title="Curated Indian Retail Market Index estimate"
                      >
                        est.
                      </span>
                    )}
                  </div>
                  <span className="text-[11px] text-slate-500 block">
                    {pricing.available
                      ? `${pricing.region || selectedRegion} benchmark • ${pricing.source || "Market Index"}`
                      : "Official price benchmark not yet published"}
                  </span>
                </div>
              </div>

              {/* Action Buttons Cluster */}
              <div className="flex flex-wrap items-center gap-2">
                {/* Action 1: View Nutrition / Full Details */}
                <button
                  type="button"
                  onClick={() => setIsDetailModalOpen(true)}
                  className="px-3.5 py-2 bg-white hover:bg-slate-50 text-[#142D4E] border border-slate-200 rounded-lg text-xs font-semibold transition-all shadow-sm flex items-center gap-1.5"
                >
                  <span className="material-symbols-outlined text-[16px] text-[#16A66A]">
                    menu_book
                  </span>
                  <span>View Nutrition</span>
                </button>

                {/* Action 2: Add to Pantry */}
                <button
                  type="button"
                  disabled={isAddingToPantry}
                  onClick={() => handleAddToPantry(food.id)}
                  className={`px-4 py-2 text-xs font-semibold rounded-lg transition-all flex items-center gap-1.5 shadow-sm disabled:opacity-50 ${
                    inPantry
                      ? "bg-[#DDF5E8] text-[#0E6842] border border-[#16A66A]/40 hover:bg-[#cdeedc]"
                      : "bg-[#16A66A] hover:bg-[#138e5b] text-white"
                  }`}
                >
                  {isAddingToPantry ? (
                    <span className="material-symbols-outlined text-[16px] animate-spin">
                      progress_activity
                    </span>
                  ) : (
                    <span className="material-symbols-outlined text-[16px]">
                      {inPantry ? "task_alt" : "add_shopping_cart"}
                    </span>
                  )}
                  <span>{inPantry ? "In Pantry (Add More)" : "Add to Pantry"}</span>
                </button>

                {/* Action 3: Explore Similar Foods */}
                <button
                  type="button"
                  onClick={() => {
                    if (onExploreSimilar) {
                      onExploreSimilar(food.food_category);
                    } else {
                      setIsDetailModalOpen(true);
                    }
                  }}
                  className="px-3 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-semibold transition-colors flex items-center gap-1"
                  title="Browse related staples in the food catalog"
                >
                  <span className="material-symbols-outlined text-[16px]">explore</span>
                  <span className="hidden sm:inline">Similar Foods</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ─── DETAILED FOOD OF THE DAY MODAL ─── */}
      {isDetailModalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full border border-slate-200 overflow-hidden animate-in fade-in zoom-in-95 duration-150 max-h-[92vh] flex flex-col">
            {/* Header */}
            <div className="p-5 border-b border-slate-100 flex items-start justify-between bg-gradient-to-r from-slate-50 to-[#F2FAF6] shrink-0">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-[#DDF5E8] text-[#0E6842]">
                    Food of the Day • {data.date}
                  </span>
                  <span className="px-2 py-0.5 rounded-full text-[11px] font-semibold bg-slate-200 text-slate-700">
                    {food.food_category}
                  </span>
                </div>
                <h3 className="font-extrabold text-[#142D4E] text-xl font-serif">
                  {food.name}
                </h3>
                {food.name_local && food.name_local !== food.name && (
                  <p className="text-xs text-slate-500 italic">Commonly known as: {food.name_local}</p>
                )}
              </div>
              <button
                type="button"
                onClick={() => setIsDetailModalOpen(false)}
                className="text-slate-400 hover:text-slate-600 p-1 rounded-lg"
              >
                <span className="material-symbols-outlined text-[24px]">close</span>
              </button>
            </div>

            {/* Scrollable Body */}
            <div className="p-6 space-y-6 overflow-y-auto">
              {/* Section 1: Overview & Factual Profile */}
              <div className="space-y-2">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center gap-1.5">
                  <span className="material-symbols-outlined text-[16px] text-[#16A66A]">info</span>
                  <span>Factual Overview</span>
                </h4>
                <div className="text-xs md:text-sm text-slate-700 leading-relaxed space-y-2 bg-slate-50 p-4 rounded-xl border border-slate-100">
                  {editorial.description.split("\n\n").map((para, i) => (
                    <p key={i}>{para}</p>
                  ))}
                </div>
              </div>

              {/* Section 2: Culinary Context & Preparation Methods */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="bg-white p-4 rounded-xl border border-slate-200 space-y-1.5">
                  <h5 className="text-xs font-bold uppercase tracking-wider text-slate-600 flex items-center gap-1">
                    <span className="material-symbols-outlined text-[15px] text-[#16A66A]">soup_kitchen</span>
                    <span>Common Culinary Usage</span>
                  </h5>
                  <p className="text-xs text-slate-600 leading-relaxed">
                    {editorial.common_usage}
                  </p>
                </div>

                <div className="bg-white p-4 rounded-xl border border-slate-200 space-y-1.5">
                  <h5 className="text-xs font-bold uppercase tracking-wider text-slate-600 flex items-center gap-1">
                    <span className="material-symbols-outlined text-[15px] text-[#16A66A]">skillet</span>
                    <span>Preparation Guidelines</span>
                  </h5>
                  <p className="text-xs text-slate-600 leading-relaxed">
                    {editorial.preparation_methods}
                  </p>
                </div>
              </div>

              {/* Section 3: Nutritional Values (per 100g) */}
              <div className="space-y-2.5">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center gap-1.5">
                  <span className="material-symbols-outlined text-[16px] text-emerald-600">monitor_heart</span>
                  <span>Nutritional Composition (per 100g)</span>
                </h4>

                <div className="grid grid-cols-5 gap-2 text-center">
                  <div className="p-2.5 bg-slate-50 rounded-xl border border-slate-200">
                    <span className="text-[10px] text-slate-500 uppercase block">Energy</span>
                    <strong className="text-sm font-bold text-slate-900 block">
                      {Math.round(food.calories_kcal)}
                    </strong>
                    <span className="text-[10px] text-slate-400">kcal</span>
                  </div>
                  <div className="p-2.5 bg-slate-50 rounded-xl border border-slate-200">
                    <span className="text-[10px] text-slate-500 uppercase block">Protein</span>
                    <strong className="text-sm font-bold text-emerald-700 block">
                      {food.protein_g}g
                    </strong>
                    <span className="text-[10px] text-slate-400">protein</span>
                  </div>
                  <div className="p-2.5 bg-slate-50 rounded-xl border border-slate-200">
                    <span className="text-[10px] text-slate-500 uppercase block">Carbs</span>
                    <strong className="text-sm font-bold text-amber-700 block">
                      {food.carbohydrates_g}g
                    </strong>
                    <span className="text-[10px] text-slate-400">carbohydrates</span>
                  </div>
                  <div className="p-2.5 bg-slate-50 rounded-xl border border-slate-200">
                    <span className="text-[10px] text-slate-500 uppercase block">Fat</span>
                    <strong className="text-sm font-bold text-rose-700 block">
                      {food.fat_g}g
                    </strong>
                    <span className="text-[10px] text-slate-400">total lipids</span>
                  </div>
                  <div className="p-2.5 bg-slate-50 rounded-xl border border-slate-200">
                    <span className="text-[10px] text-slate-500 uppercase block">Fiber</span>
                    <strong className="text-sm font-bold text-indigo-700 block">
                      {food.fiber_g !== null && food.fiber_g !== undefined ? `${food.fiber_g}g` : "0g"}
                    </strong>
                    <span className="text-[10px] text-slate-400">dietary</span>
                  </div>
                </div>

                {/* Full Micronutrients breakdown */}
                {availableMicros.length > 0 && (
                  <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 space-y-1.5">
                    <span className="text-[11px] font-bold text-slate-600 uppercase tracking-wider block">
                      Micronutrient Details (per 100g)
                    </span>
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs text-slate-700">
                      {availableMicros.map(([key, val]) => (
                        <div key={key} className="bg-white p-2 rounded-lg border border-slate-100 flex justify-between">
                          <span className="capitalize text-slate-500">
                            {key.replace("_mg", "").replace("_mcg", "").replace("_", " ")}:
                          </span>
                          <span className="font-bold">
                            {val} {key.includes("_mcg") ? "mcg" : "mg"}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Section 4: Indian Food Pricing & Market Regional Options */}
              <div className="p-4 bg-gradient-to-br from-slate-50 to-[#F2FAF6] rounded-xl border border-slate-200 space-y-3">
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700 flex items-center gap-1.5">
                    <span className="material-symbols-outlined text-[16px] text-[#16A66A]">payments</span>
                    <span>Indian Food Pricing Breakdown</span>
                  </h4>
                  <span className="text-xs text-slate-500">
                    Selected Region: <strong>{pricing.region || selectedRegion}</strong>
                  </span>
                </div>

                {pricing.available ? (
                  <div className="space-y-3">
                    <div className="flex items-baseline justify-between bg-white p-3 rounded-lg border border-slate-100">
                      <div>
                        <span className="text-2xl font-black text-[#142D4E]">
                          {pricing.formatted_price}
                        </span>
                        <span className="text-xs text-slate-500 ml-1.5">
                          in Indian Rupees (INR)
                        </span>
                      </div>
                      <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-[#DDF5E8] text-[#0E6842] border border-[#16A66A]/30">
                        {pricing.price_type === "verified" ? "✓ Verified Mandi Price" : "Curated Market Estimate"}
                      </span>
                    </div>

                    <div className="text-xs text-slate-600 space-y-1">
                      <p>
                        <span className="font-semibold text-slate-700">Data Source:</span>{" "}
                        {pricing.source || "Government Mandi Price Cell"}
                      </p>
                      {pricing.last_updated && (
                        <p>
                          <span className="font-semibold text-slate-700">Last Updated:</span>{" "}
                          {pricing.last_updated}
                        </p>
                      )}
                    </div>

                    {/* Regional alternatives list */}
                    {pricing.regional_options && pricing.regional_options.length > 1 && (
                      <div className="pt-2">
                        <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block mb-1.5">
                          Compare Other Regions:
                        </span>
                        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                          {pricing.regional_options.map((opt) => (
                            <button
                              key={opt.price_id}
                              type="button"
                              onClick={() => {
                                setSelectedRegion(opt.region);
                                fetchFoodOfTheDay(opt.region);
                              }}
                              className={`p-2 rounded-lg border text-xs text-left transition-colors flex justify-between items-center ${
                                opt.region?.toLowerCase() === (pricing.region || selectedRegion).toLowerCase()
                                  ? "bg-[#DDF5E8] border-[#16A66A] text-[#0E6842] font-bold"
                                  : "bg-white border-slate-200 hover:bg-slate-50 text-slate-700"
                              }`}
                            >
                              <span>{opt.region}</span>
                              <span className="font-bold">{opt.formatted_price}</span>
                            </button>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="p-3 bg-white rounded-lg text-center text-xs text-slate-500">
                    Official market price benchmark currently unavailable for this food.
                  </div>
                )}
              </div>

              {/* Section 5: Similar Catalog Foods */}
              {similar_foods && similar_foods.length > 0 && (
                <div className="space-y-2.5">
                  <div className="flex items-center justify-between">
                    <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center gap-1.5">
                      <span className="material-symbols-outlined text-[16px] text-slate-600">travel_explore</span>
                      <span>Similar Foods from {food.food_category}</span>
                    </h4>
                    {onExploreSimilar && (
                      <button
                        type="button"
                        onClick={() => {
                          setIsDetailModalOpen(false);
                          onExploreSimilar(food.food_category);
                        }}
                        className="text-xs text-[#16A66A] hover:underline font-semibold"
                      >
                        Browse all in catalog →
                      </button>
                    )}
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                    {similar_foods.map((sf) => (
                      <div
                        key={sf.id}
                        className="p-3 bg-slate-50 hover:bg-white rounded-xl border border-slate-200 transition-all flex items-center justify-between gap-2"
                      >
                        <div className="space-y-0.5 min-w-0">
                          <p className="font-bold text-xs text-slate-900 truncate">{sf.name}</p>
                          <p className="text-[11px] text-slate-500">
                            {Math.round(sf.calories_kcal)} kcal • {sf.protein_g}g prot • {sf.price_formatted}
                          </p>
                        </div>
                        {onOpenCatalogFood && (
                          <button
                            type="button"
                            onClick={() => {
                              setIsDetailModalOpen(false);
                              onOpenCatalogFood(sf.id);
                            }}
                            className="p-1.5 bg-white hover:bg-slate-100 text-slate-600 rounded border border-slate-200 shrink-0"
                            title="View in food catalog"
                          >
                            <span className="material-symbols-outlined text-[16px]">visibility</span>
                          </button>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="p-4 bg-slate-50 border-t border-slate-100 flex items-center justify-between shrink-0">
              <button
                type="button"
                onClick={() => setIsDetailModalOpen(false)}
                className="px-4 py-2 text-xs md:text-sm font-semibold text-slate-600 hover:bg-slate-200 rounded-lg transition-colors"
              >
                Close
              </button>

              <button
                type="button"
                disabled={isAddingToPantry}
                onClick={() => handleAddToPantry(food.id)}
                className="px-5 py-2 text-xs md:text-sm font-semibold bg-[#16A66A] hover:bg-[#138e5b] disabled:opacity-50 text-white rounded-lg transition-colors flex items-center gap-1.5 shadow-sm"
              >
                {isAddingToPantry ? (
                  <span className="material-symbols-outlined text-[16px] animate-spin">
                    progress_activity
                  </span>
                ) : (
                  <span className="material-symbols-outlined text-[16px]">
                    {inPantry ? "task_alt" : "add_shopping_cart"}
                  </span>
                )}
                <span>{inPantry ? "In Pantry (Add More)" : "Add to Pantry"}</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};
