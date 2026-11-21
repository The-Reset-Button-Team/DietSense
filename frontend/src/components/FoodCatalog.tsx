"use client";

import React, { useState, useEffect, useCallback, useTransition } from "react";
import { apiClient } from "@/lib/api-client";
import { useAuth } from "@/context/AuthContext";
import { CatalogFood, FoodCatalogResponse } from "@/types";

type CatalogView = "all" | "in_pantry" | "not_in_pantry";
type SortOption = "name" | "calories" | "protein" | "carbs" | "fat" | "price";
type SortOrder = "asc" | "desc";

interface FoodCatalogProps {
  onPantryUpdated?: () => void;
  onGoToPantryScanner?: () => void;
}

export const FoodCatalog: React.FC<FoodCatalogProps> = ({
  onPantryUpdated,
  onGoToPantryScanner,
}) => {
  const { user, isAuthenticated } = useAuth();
  const [, startTransition] = useTransition();

  // Active View Tab
  const [activeView, setActiveView] = useState<CatalogView>("all");

  // Search & Filter State
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [debouncedQuery, setDebouncedQuery] = useState<string>("");
  const [selectedCategory, setSelectedCategory] = useState<string>("");
  const [selectedRegion, setSelectedRegion] = useState<string>("National");
  const [isVegetarian, setIsVegetarian] = useState<boolean | null>(null);
  const [isVegan, setIsVegan] = useState<boolean | null>(null);
  const [isGlutenFree, setIsGlutenFree] = useState<boolean | null>(null);
  const [minProtein, setMinProtein] = useState<string>("");
  const [maxCalories, setMaxCalories] = useState<string>("");

  // Sorting & Pagination
  const [sortBy, setSortBy] = useState<SortOption>("name");
  const [sortOrder, setSortOrder] = useState<SortOrder>("asc");
  const [page, setPage] = useState<number>(1);
  const [limit, setLimit] = useState<number>(24);

  // Data & Status State
  const [categories, setCategories] = useState<string[]>([]);
  const [foods, setFoods] = useState<CatalogFood[]>([]);
  const [totalItems, setTotalItems] = useState<number>(0);
  const [totalPages, setTotalPages] = useState<number>(0);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Food Detail Modal State
  const [detailFood, setDetailFood] = useState<CatalogFood | null>(null);
  const [detailLoading, setDetailLoading] = useState<boolean>(false);
  const [foodDetailData, setFoodDetailData] = useState<any | null>(null);
  const [detailRegion, setDetailRegion] = useState<string>("National");

  // Notification Toast
  const [toast, setToast] = useState<{ message: string; type: "success" | "error" } | null>(null);

  // Modals State
  const [addModalFood, setAddModalFood] = useState<CatalogFood | null>(null);
  const [addQuantity, setAddQuantity] = useState<string>("1 unit");
  const [addExpiry, setAddExpiry] = useState<string>("");
  const [isSubmittingAdd, setIsSubmittingAdd] = useState<boolean>(false);

  const [editModalFood, setEditModalFood] = useState<CatalogFood | null>(null);
  const [editQuantity, setEditQuantity] = useState<string>("");
  const [editInStock, setEditInStock] = useState<boolean>(true);
  const [isSubmittingEdit, setIsSubmittingEdit] = useState<boolean>(false);

  const [deleteConfirmFood, setDeleteConfirmFood] = useState<CatalogFood | null>(null);
  const [isSubmittingDelete, setIsSubmittingDelete] = useState<boolean>(false);

  const showToast = (message: string, type: "success" | "error" = "success") => {
    setToast({ message, type });
    setTimeout(() => {
      setToast(null);
    }, 3500);
  };

  // Debounce search query
  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedQuery(searchQuery.trim());
      setPage(1);
    }, 350);
    return () => clearTimeout(handler);
  }, [searchQuery]);

  // Load Categories on Mount
  useEffect(() => {
    let isMounted = true;
    (async () => {
      try {
        const res = await apiClient<{ categories: string[] }>("/api/foods/categories");
        if (isMounted && res.categories) {
          setCategories(res.categories);
        }
      } catch (err) {
        console.warn("Failed to load food categories:", err);
      }
    })();
    return () => {
      isMounted = false;
    };
  }, []);

  // Fetch Foods on Filter / Page / View changes
  const fetchFoods = useCallback(async () => {
    setIsLoading(true);
    setErrorMsg(null);
    try {
      const params = new URLSearchParams();
      params.set("view", activeView);
      params.set("page", String(page));
      params.set("limit", String(limit));
      params.set("sort_by", sortBy);
      params.set("sort_order", sortOrder);

      if (selectedRegion) params.set("region", selectedRegion);
      if (debouncedQuery) params.set("q", debouncedQuery);
      if (selectedCategory) params.set("category", selectedCategory);
      if (isVegetarian === true) params.set("is_vegetarian", "true");
      if (isVegan === true) params.set("is_vegan", "true");
      if (isGlutenFree === true) params.set("is_gluten_free", "true");
      if (minProtein && !isNaN(Number(minProtein))) params.set("min_protein", minProtein);
      if (maxCalories && !isNaN(Number(maxCalories))) params.set("max_calories", maxCalories);

      const res = await apiClient<FoodCatalogResponse>(`/api/foods/?${params.toString()}`);
      setFoods(res.items || []);
      setTotalItems(res.total || 0);
      setTotalPages(res.total_pages || 0);
    } catch (err: any) {
      console.error("Error fetching food catalog:", err);
      setErrorMsg(err.message || "Failed to load food catalog records.");
    } finally {
      setIsLoading(false);
    }
  }, [
    activeView,
    page,
    limit,
    sortBy,
    sortOrder,
    debouncedQuery,
    selectedCategory,
    selectedRegion,
    isVegetarian,
    isVegan,
    isGlutenFree,
    minProtein,
    maxCalories,
  ]);

  useEffect(() => {
    fetchFoods();
  }, [fetchFoods]);

  // Food Detail Handler
  const handleOpenDetailModal = async (food: CatalogFood, region: string = selectedRegion) => {
    setDetailFood(food);
    setDetailRegion(region);
    setDetailLoading(true);
    try {
      const data = await apiClient<any>(`/api/foods/${food.id}?region=${encodeURIComponent(region)}`);
      setFoodDetailData(data);
    } catch (err) {
      console.error("Failed to load food details:", err);
      setFoodDetailData(food);
    } finally {
      setDetailLoading(false);
    }
  };

  // View Tab Change Handler
  const handleViewChange = (newView: CatalogView) => {
    setActiveView(newView);
    setPage(1);
  };

  // Add Food to Pantry
  const handleOpenAddModal = (food: CatalogFood) => {
    if (!isAuthenticated) {
      showToast("Please sign in to add items to your pantry.", "error");
      return;
    }
    setAddModalFood(food);
    setAddQuantity(food.pantry_quantity || "1 unit");
    setAddExpiry(food.pantry_expiry_date || "");
  };

  const handleConfirmAdd = async () => {
    if (!addModalFood) return;
    setIsSubmittingAdd(true);
    try {
      const res = await apiClient<{
        status: string;
        message: string;
        already_in_pantry: boolean;
        pantry_item: any;
      }>(`/api/foods/${addModalFood.id}/add-to-pantry`, {
        method: "POST",
        body: JSON.stringify({
          quantity: addQuantity.trim() || "1 unit",
          expiry_date: addExpiry.trim() || null,
          in_stock: true,
        }),
      });

      showToast(res.message || `Added ${addModalFood.name} to your pantry!`, "success");
      setAddModalFood(null);

      // Re-fetch food list to update view state
      await fetchFoods();
      if (onPantryUpdated) onPantryUpdated();
    } catch (err: any) {
      showToast(err.message || "Failed to add food to pantry.", "error");
    } finally {
      setIsSubmittingAdd(false);
    }
  };

  // Edit Pantry Item
  const handleOpenEditModal = (food: CatalogFood) => {
    setEditModalFood(food);
    setEditQuantity(food.pantry_quantity || "1 unit");
    setEditInStock(food.pantry_in_stock !== false);
  };

  const handleConfirmEdit = async () => {
    if (!editModalFood) return;
    setIsSubmittingEdit(true);
    try {
      await apiClient(`/api/foods/${editModalFood.id}/pantry-entry`, {
        method: "PATCH",
        body: JSON.stringify({
          quantity: editQuantity.trim() || "1 unit",
          in_stock: editInStock,
        }),
      });

      showToast(`Updated pantry entry for ${editModalFood.name}.`, "success");
      setEditModalFood(null);
      await fetchFoods();
      if (onPantryUpdated) onPantryUpdated();
    } catch (err: any) {
      showToast(err.message || "Failed to update pantry entry.", "error");
    } finally {
      setIsSubmittingEdit(false);
    }
  };

  // Remove Food from Pantry
  const handleOpenDeleteModal = (food: CatalogFood) => {
    setDeleteConfirmFood(food);
  };

  const handleConfirmDelete = async () => {
    if (!deleteConfirmFood) return;
    setIsSubmittingDelete(true);
    try {
      await apiClient(`/api/foods/${deleteConfirmFood.id}/remove-from-pantry`, {
        method: "DELETE",
      });

      showToast(`Removed ${deleteConfirmFood.name} from pantry.`, "success");
      setDeleteConfirmFood(null);
      await fetchFoods();
      if (onPantryUpdated) onPantryUpdated();
    } catch (err: any) {
      showToast(err.message || "Failed to remove item from pantry.", "error");
    } finally {
      setIsSubmittingDelete(false);
    }
  };

  // Reset Filters
  const handleResetFilters = () => {
    setSearchQuery("");
    setSelectedCategory("");
    setIsVegetarian(null);
    setIsVegan(null);
    setIsGlutenFree(null);
    setMinProtein("");
    setMaxCalories("");
    setSortBy("name");
    setSortOrder("asc");
    setPage(1);
  };

  const hasActiveFilters =
    Boolean(searchQuery) ||
    Boolean(selectedCategory) ||
    isVegetarian !== null ||
    isVegan !== null ||
    isGlutenFree !== null ||
    Boolean(minProtein) ||
    Boolean(maxCalories);

  return (
    <div className="space-y-6">
      {/* Toast Notification */}
      {toast && (
        <div
          role="status"
          aria-live="polite"
          className={`fixed bottom-6 right-6 z-50 flex items-center gap-2.5 px-4 py-3 rounded-lg shadow-xl text-sm font-medium transition-all transform animate-in fade-in slide-in-from-bottom-3 duration-200 ${
            toast.type === "success"
              ? "bg-[#142D4E] text-white border-l-4 border-[#16A66A]"
              : "bg-red-900 text-white border-l-4 border-red-500"
          }`}
        >
          <span className="material-symbols-outlined text-[20px] text-[#16A66A]">
            {toast.type === "success" ? "check_circle" : "error"}
          </span>
          <span>{toast.message}</span>
          <button
            onClick={() => setToast(null)}
            className="ml-3 text-white/70 hover:text-white"
            aria-label="Dismiss toast"
          >
            <span className="material-symbols-outlined text-[16px]">close</span>
          </button>
        </div>
      )}

      {/* Header and Three-View Tabs */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200/80 p-5 md:p-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-5 border-b border-slate-100">
          <div>
            <div className="flex items-center gap-2.5">
              <div className="w-9 h-9 rounded-lg bg-[#DDF5E8] text-[#16A66A] flex items-center justify-center">
                <span className="material-symbols-outlined text-[22px]">restaurant_menu</span>
              </div>
              <h2 className="text-xl md:text-2xl font-bold text-[#142D4E]">
                DietSense Food Catalog
              </h2>
            </div>
            <p className="text-xs md:text-sm text-slate-500 mt-1">
              Explore 14,000+ verified foods from USDA & ICMR-NIN with live pantry integration.
            </p>
          </div>

          {onGoToPantryScanner && (
            <button
              type="button"
              onClick={onGoToPantryScanner}
              className="inline-flex items-center gap-1.5 px-3.5 py-2 text-xs md:text-sm font-semibold text-[#142D4E] bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors self-start md:self-auto"
            >
              <span className="material-symbols-outlined text-[18px] text-[#16A66A]">inventory_2</span>
              <span>Go to AI Scanner</span>
            </button>
          )}
        </div>

        {/* The 3 Food Views Tabs */}
        <div className="pt-4">
          <div className="flex items-center gap-2 overflow-x-auto pb-1 scrollbar-none" role="tablist">
            {/* View 1: All Foods */}
            <button
              role="tab"
              aria-selected={activeView === "all"}
              onClick={() => handleViewChange("all")}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-semibold transition-all whitespace-nowrap ${
                activeView === "all"
                  ? "bg-[#142D4E] text-white shadow-sm"
                  : "bg-slate-100 text-slate-600 hover:bg-slate-200 hover:text-slate-900"
              }`}
            >
              <span className="material-symbols-outlined text-[18px]">menu_book</span>
              <span>All Foods</span>
              <span
                className={`ml-1 text-xs px-2 py-0.5 rounded-full font-bold ${
                  activeView === "all" ? "bg-[#16A66A] text-white" : "bg-slate-200 text-slate-700"
                }`}
              >
                {activeView === "all" && !isLoading ? totalItems.toLocaleString() : "14k+"}
              </span>
            </button>

            {/* View 2: In My Pantry */}
            <button
              role="tab"
              aria-selected={activeView === "in_pantry"}
              onClick={() => handleViewChange("in_pantry")}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-semibold transition-all whitespace-nowrap ${
                activeView === "in_pantry"
                  ? "bg-[#16A66A] text-white shadow-sm"
                  : "bg-slate-100 text-slate-600 hover:bg-slate-200 hover:text-slate-900"
              }`}
            >
              <span className="material-symbols-outlined text-[18px]">kitchen</span>
              <span>In My Pantry</span>
              {activeView === "in_pantry" && !isLoading && (
                <span className="ml-1 text-xs px-2 py-0.5 rounded-full bg-white text-[#16A66A] font-bold">
                  {totalItems}
                </span>
              )}
            </button>

            {/* View 3: Not in My Pantry */}
            <button
              role="tab"
              aria-selected={activeView === "not_in_pantry"}
              onClick={() => handleViewChange("not_in_pantry")}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-semibold transition-all whitespace-nowrap ${
                activeView === "not_in_pantry"
                  ? "bg-[#142D4E] text-white shadow-sm"
                  : "bg-slate-100 text-slate-600 hover:bg-slate-200 hover:text-slate-900"
              }`}
            >
              <span className="material-symbols-outlined text-[18px]">add_shopping_cart</span>
              <span>Not in My Pantry</span>
              {activeView === "not_in_pantry" && !isLoading && (
                <span className="ml-1 text-xs px-2 py-0.5 rounded-full bg-slate-700 text-white font-bold">
                  {totalItems.toLocaleString()}
                </span>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Search, Filters & Controls Bar */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200/80 p-5 space-y-4">
        {/* Search Row */}
        <div className="flex flex-col md:flex-row gap-3">
          {/* Search Input */}
          <div className="relative flex-1">
            <span className="material-symbols-outlined absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 text-[20px]">
              search
            </span>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search by food name, Hindi/local name, ingredient (e.g. Oats, Paneer, Rice)..."
              className="w-full pl-10 pr-10 py-2.5 text-sm bg-slate-50 border border-slate-200 rounded-lg text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-[#16A66A]/40 focus:border-[#16A66A] transition-all"
            />
            {searchQuery && (
              <button
                type="button"
                onClick={() => setSearchQuery("")}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                aria-label="Clear search"
              >
                <span className="material-symbols-outlined text-[18px]">close</span>
              </button>
            )}
          </div>

          {/* Category Dropdown */}
          <div className="w-full md:w-64">
            <select
              value={selectedCategory}
              onChange={(e) => {
                setSelectedCategory(e.target.value);
                setPage(1);
              }}
              className="w-full py-2.5 px-3 text-sm bg-slate-50 border border-slate-200 rounded-lg text-slate-800 focus:outline-none focus:ring-2 focus:ring-[#16A66A]/40 focus:border-[#16A66A] transition-all"
            >
              <option value="">All Categories ({categories.length})</option>
              {categories.map((cat) => (
                <option key={cat} value={cat}>
                  {cat}
                </option>
              ))}
            </select>
          </div>

          {/* Region Dropdown */}
          <div className="w-full sm:w-40">
            <select
              value={selectedRegion}
              onChange={(e) => {
                setSelectedRegion(e.target.value);
                setPage(1);
              }}
              className="w-full py-2.5 px-3 text-sm bg-slate-50 border border-slate-200 rounded-lg text-slate-800 focus:outline-none focus:ring-2 focus:ring-[#16A66A]/40 focus:border-[#16A66A] transition-all"
              title="Regional pricing"
            >
              <option value="National">🇮🇳 National</option>
              <option value="Delhi">📍 Delhi</option>
              <option value="Mumbai">📍 Mumbai</option>
              <option value="Bengaluru">📍 Bengaluru</option>
              <option value="Kolkata">📍 Kolkata</option>
            </select>
          </div>

          {/* Sort Control */}
          <div className="flex items-center gap-2">
            <select
              value={sortBy}
              onChange={(e) => {
                setSortBy(e.target.value as SortOption);
                setPage(1);
              }}
              className="py-2.5 px-3 text-sm bg-slate-50 border border-slate-200 rounded-lg text-slate-800 focus:outline-none focus:ring-2 focus:ring-[#16A66A]/40 focus:border-[#16A66A] transition-all"
            >
              <option value="name">Sort: Name (A-Z)</option>
              <option value="price">Sort: Price</option>
              <option value="calories">Sort: Calories</option>
              <option value="protein">Sort: Protein</option>
              <option value="carbs">Sort: Carbs</option>
              <option value="fat">Sort: Fat</option>
            </select>

            <button
              type="button"
              onClick={() => setSortOrder(sortOrder === "asc" ? "desc" : "asc")}
              className="p-2.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg border border-slate-200 transition-colors flex items-center justify-center"
              title={`Sorting ${sortOrder === "asc" ? "Ascending" : "Descending"}`}
              aria-label={`Toggle sort order (currently ${sortOrder})`}
            >
              <span className="material-symbols-outlined text-[20px]">
                {sortOrder === "asc" ? "arrow_upward" : "arrow_downward"}
              </span>
            </button>
          </div>
        </div>

        {/* Secondary Filter Chips Row */}
        <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-slate-100">
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider mr-1">
            Dietary:
          </span>

          {/* Vegetarian Chip */}
          <button
            type="button"
            onClick={() => {
              setIsVegetarian(isVegetarian ? null : true);
              setPage(1);
            }}
            className={`px-3 py-1.5 rounded-full text-xs font-medium transition-colors flex items-center gap-1.5 ${
              isVegetarian
                ? "bg-[#DDF5E8] text-[#0E6842] border border-[#16A66A]/40 font-semibold"
                : "bg-slate-100 text-slate-600 hover:bg-slate-200"
            }`}
          >
            <span className="w-2 h-2 rounded-full bg-emerald-500 inline-block" />
            <span>Vegetarian</span>
            {isVegetarian && <span className="material-symbols-outlined text-[14px]">check</span>}
          </button>

          {/* Vegan Chip */}
          <button
            type="button"
            onClick={() => {
              setIsVegan(isVegan ? null : true);
              setPage(1);
            }}
            className={`px-3 py-1.5 rounded-full text-xs font-medium transition-colors flex items-center gap-1.5 ${
              isVegan
                ? "bg-[#DDF5E8] text-[#0E6842] border border-[#16A66A]/40 font-semibold"
                : "bg-slate-100 text-slate-600 hover:bg-slate-200"
            }`}
          >
            <span className="w-2 h-2 rounded-full bg-green-600 inline-block" />
            <span>Vegan</span>
            {isVegan && <span className="material-symbols-outlined text-[14px]">check</span>}
          </button>

          {/* Gluten-Free Chip */}
          <button
            type="button"
            onClick={() => {
              setIsGlutenFree(isGlutenFree ? null : true);
              setPage(1);
            }}
            className={`px-3 py-1.5 rounded-full text-xs font-medium transition-colors flex items-center gap-1.5 ${
              isGlutenFree
                ? "bg-amber-100 text-amber-800 border border-amber-300 font-semibold"
                : "bg-slate-100 text-slate-600 hover:bg-slate-200"
            }`}
          >
            <span className="material-symbols-outlined text-[14px]">grain</span>
            <span>Gluten-Free</span>
            {isGlutenFree && <span className="material-symbols-outlined text-[14px]">check</span>}
          </button>

          <div className="h-4 w-px bg-slate-200 mx-1 hidden sm:block" />

          {/* Nutrition range quick filters */}
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Nutrients:
            </span>
            <input
              type="number"
              placeholder="Min Protein (g)"
              value={minProtein}
              onChange={(e) => {
                setMinProtein(e.target.value);
                setPage(1);
              }}
              className="w-28 py-1 px-2 text-xs bg-slate-50 border border-slate-200 rounded text-slate-800 focus:outline-none focus:border-[#16A66A]"
              min="0"
            />
            <input
              type="number"
              placeholder="Max Cal (kcal)"
              value={maxCalories}
              onChange={(e) => {
                setMaxCalories(e.target.value);
                setPage(1);
              }}
              className="w-28 py-1 px-2 text-xs bg-slate-50 border border-slate-200 rounded text-slate-800 focus:outline-none focus:border-[#16A66A]"
              min="0"
            />
          </div>

          {/* Reset Filters Button */}
          {hasActiveFilters && (
            <button
              type="button"
              onClick={handleResetFilters}
              className="ml-auto text-xs text-red-600 hover:text-red-700 font-medium flex items-center gap-1 hover:underline"
            >
              <span className="material-symbols-outlined text-[14px]">filter_alt_off</span>
              <span>Reset Filters</span>
            </button>
          )}
        </div>
      </div>

      {/* Results Header / Slices info */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between text-xs text-slate-500 gap-2 px-1">
        <div>
          {isLoading ? (
            <span>Fetching foods from database...</span>
          ) : (
            <span>
              Showing{" "}
              <strong className="text-slate-800">
                {totalItems === 0 ? 0 : (page - 1) * limit + 1}–
                {Math.min(page * limit, totalItems)}
              </strong>{" "}
              of <strong className="text-slate-800">{totalItems.toLocaleString()}</strong> foods
              {debouncedQuery && ` matching "${debouncedQuery}"`}
              {selectedCategory && ` in ${selectedCategory}`}
            </span>
          )}
        </div>

        {/* Per-page selector */}
        <div className="flex items-center gap-1.5 self-end sm:self-auto">
          <span>Show:</span>
          {[12, 24, 48].map((l) => (
            <button
              key={l}
              type="button"
              onClick={() => {
                setLimit(l);
                setPage(1);
              }}
              className={`px-2 py-0.5 rounded text-xs font-semibold ${
                limit === l
                  ? "bg-[#142D4E] text-white"
                  : "bg-slate-100 text-slate-600 hover:bg-slate-200"
              }`}
            >
              {l}
            </button>
          ))}
        </div>
      </div>

      {/* Error Banner */}
      {errorMsg && (
        <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-red-800 text-sm flex items-start gap-3">
          <span className="material-symbols-outlined text-red-600 text-[20px] shrink-0 mt-0.5">
            warning
          </span>
          <div className="flex-1">
            <p className="font-semibold">Failed to fetch foods</p>
            <p className="text-xs text-red-700 mt-0.5">{errorMsg}</p>
          </div>
          <button
            onClick={() => fetchFoods()}
            className="px-3 py-1 bg-red-100 hover:bg-red-200 text-red-900 rounded text-xs font-semibold"
          >
            Retry
          </button>
        </div>
      )}

      {/* Loading Skeletons */}
      {isLoading && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 animate-pulse">
          {Array.from({ length: 8 }).map((_, i) => (
            <div
              key={i}
              className="bg-white rounded-xl border border-slate-200/80 p-4 space-y-3 shadow-sm"
            >
              <div className="flex justify-between items-start">
                <div className="h-5 bg-slate-200 rounded w-2/3" />
                <div className="h-5 bg-slate-100 rounded w-16" />
              </div>
              <div className="h-3 bg-slate-100 rounded w-1/3" />
              <div className="grid grid-cols-4 gap-2 pt-2 border-t border-slate-100">
                <div className="h-8 bg-slate-100 rounded" />
                <div className="h-8 bg-slate-100 rounded" />
                <div className="h-8 bg-slate-100 rounded" />
                <div className="h-8 bg-slate-100 rounded" />
              </div>
              <div className="h-8 bg-slate-200 rounded w-full mt-3" />
            </div>
          ))}
        </div>
      )}

      {/* Empty States */}
      {!isLoading && foods.length === 0 && (
        <div className="bg-white rounded-xl border border-slate-200/80 p-12 text-center shadow-sm">
          {activeView === "in_pantry" ? (
            <div className="max-w-md mx-auto space-y-3">
              <div className="w-14 h-14 rounded-full bg-[#DDF5E8] text-[#16A66A] mx-auto flex items-center justify-center">
                <span className="material-symbols-outlined text-[32px]">kitchen</span>
              </div>
              <h3 className="text-lg font-bold text-[#142D4E]">Your Pantry is Empty</h3>
              <p className="text-xs md:text-sm text-slate-500">
                {isAuthenticated
                  ? "You don't have any food catalog items in your pantry yet. Switch to 'All Foods' or 'Not in My Pantry' to add ingredients you keep at home!"
                  : "Sign in to track your personal pantry inventory and see in-stock ingredients here."}
              </p>
              <div className="pt-2">
                <button
                  type="button"
                  onClick={() => handleViewChange("all")}
                  className="px-4 py-2 bg-[#142D4E] hover:bg-[#1b3d6a] text-white text-xs md:text-sm font-semibold rounded-lg transition-colors inline-flex items-center gap-1.5"
                >
                  <span className="material-symbols-outlined text-[16px]">menu_book</span>
                  <span>Browse All Foods</span>
                </button>
              </div>
            </div>
          ) : (
            <div className="max-w-md mx-auto space-y-3">
              <div className="w-14 h-14 rounded-full bg-slate-100 text-slate-400 mx-auto flex items-center justify-center">
                <span className="material-symbols-outlined text-[32px]">search_off</span>
              </div>
              <h3 className="text-lg font-bold text-[#142D4E]">No Foods Found</h3>
              <p className="text-xs md:text-sm text-slate-500">
                No catalog items match your search & filter criteria. Try adjusting keywords or resetting filters.
              </p>
              {hasActiveFilters && (
                <div className="pt-2">
                  <button
                    type="button"
                    onClick={handleResetFilters}
                    className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-800 text-xs md:text-sm font-semibold rounded-lg transition-colors inline-flex items-center gap-1.5"
                  >
                    <span className="material-symbols-outlined text-[16px]">filter_alt_off</span>
                    <span>Reset All Filters</span>
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Food Cards Grid */}
      {!isLoading && foods.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {foods.map((food) => {
            const inPantry = food.in_pantry;

            return (
              <div
                key={food.id}
                className={`bg-white rounded-xl border transition-all duration-200 flex flex-col justify-between shadow-sm hover:shadow-md ${
                  inPantry ? "border-[#16A66A]/60 bg-gradient-to-b from-white to-[#F2FAF6]" : "border-slate-200/90"
                }`}
              >
                <div className="p-4 space-y-3">
                  {/* Card Header: Category & Pantry Status */}
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-[11px] font-semibold tracking-wide text-slate-600 bg-slate-100 px-2 py-0.5 rounded-full truncate max-w-[150px]">
                      {food.food_category || "General"}
                    </span>

                    <div className="flex items-center gap-1.5 shrink-0">
                      <button
                        type="button"
                        onClick={() => handleOpenDetailModal(food)}
                        className="text-slate-400 hover:text-[#16A66A] p-0.5 rounded transition-colors"
                        title="View nutritional & regional pricing details"
                      >
                        <span className="material-symbols-outlined text-[17px]">info</span>
                      </button>

                      {/* In Pantry Status Badge */}
                      {inPantry ? (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-bold bg-[#DDF5E8] text-[#0E6842] border border-[#16A66A]/30">
                          <span className="material-symbols-outlined text-[13px]">check_circle</span>
                          <span>In Pantry</span>
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-medium bg-slate-100 text-slate-500">
                          <span className="material-symbols-outlined text-[13px]">inventory_2</span>
                          <span>Not in Pantry</span>
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Food Name & Local Name */}
                  <div>
                    <h4 className="font-bold text-slate-900 text-sm md:text-base leading-snug line-clamp-2">
                      {food.name}
                    </h4>
                    {food.name_local && food.name_local !== food.name && (
                      <p className="text-xs text-slate-500 italic mt-0.5 line-clamp-1">
                        {food.name_local}
                      </p>
                    )}
                  </div>

                  {/* Nutrition Highlights Grid */}
                  <div className="grid grid-cols-4 gap-1.5 py-2 px-2.5 bg-slate-50/80 rounded-lg text-center border border-slate-100">
                    <div>
                      <span className="block text-[10px] text-slate-500 uppercase">Cals</span>
                      <strong className="block text-xs font-bold text-slate-800">
                        {Math.round(food.calories_kcal)}
                      </strong>
                    </div>
                    <div>
                      <span className="block text-[10px] text-slate-500 uppercase">Prot</span>
                      <strong className="block text-xs font-bold text-emerald-700">
                        {Number(food.protein_g).toFixed(1)}g
                      </strong>
                    </div>
                    <div>
                      <span className="block text-[10px] text-slate-500 uppercase">Carb</span>
                      <strong className="block text-xs font-bold text-amber-700">
                        {Number(food.carbohydrates_g).toFixed(1)}g
                      </strong>
                    </div>
                    <div>
                      <span className="block text-[10px] text-slate-500 uppercase">Fat</span>
                      <strong className="block text-xs font-bold text-rose-700">
                        {Number(food.fat_g).toFixed(1)}g
                      </strong>
                    </div>
                  </div>

                  {/* Fiber & Price row */}
                  <div className="flex items-center justify-between text-[11px] text-slate-500 pt-1">
                    <div>
                      {food.fiber_g !== null && food.fiber_g !== undefined && food.fiber_g > 0 ? (
                        <span className="font-medium text-slate-700">
                          Fiber: {Number(food.fiber_g).toFixed(1)}g
                        </span>
                      ) : (
                        <span className="text-slate-400">Fiber: 0g</span>
                      )}
                    </div>
                    <div>
                      {food.price !== null && food.price !== undefined ? (
                        <div className="flex items-center gap-1.5 font-medium">
                          <span className="font-bold text-[#142D4E] text-xs">
                            {food.price_formatted || `₹${food.price}/${food.price_unit || "kg"}`}
                          </span>
                          {food.price_type === "estimated" ? (
                            <span
                              className="text-[9px] font-semibold text-amber-700 bg-amber-50 border border-amber-200 px-1 rounded cursor-help"
                              title={`Estimated market price (${food.price_region || "National"})`}
                            >
                              est.
                            </span>
                          ) : (
                            <span
                              className="text-[9px] font-semibold text-emerald-700 bg-emerald-50 border border-emerald-200 px-1 rounded cursor-help"
                              title={`Verified by ${food.price_source || "Govt Mandi / DoCA"}`}
                            >
                              ✓ Verified
                            </span>
                          )}
                        </div>
                      ) : (
                        <span className="text-slate-400">Price unavailable</span>
                      )}
                    </div>
                  </div>

                  {/* Dietary & Allergen Badges */}
                  <div className="flex flex-wrap items-center gap-1 pt-1">
                    {food.is_vegetarian && (
                      <span className="text-[10px] font-semibold bg-emerald-50 text-emerald-800 px-1.5 py-0.5 rounded border border-emerald-200">
                        Veg
                      </span>
                    )}
                    {food.is_vegan && (
                      <span className="text-[10px] font-semibold bg-green-50 text-green-800 px-1.5 py-0.5 rounded border border-green-200">
                        Vegan
                      </span>
                    )}
                    {food.is_gluten_free && (
                      <span className="text-[10px] font-semibold bg-amber-50 text-amber-800 px-1.5 py-0.5 rounded border border-amber-200">
                        Gluten-Free
                      </span>
                    )}
                    {food.allergen_flags && food.allergen_flags.length > 0 && (
                      <span className="text-[10px] font-medium bg-red-50 text-red-700 px-1.5 py-0.5 rounded border border-red-200">
                        Allergen: {food.allergen_flags.slice(0, 2).join(", ")}
                      </span>
                    )}
                  </div>

                  {/* Pantry inventory details if in pantry */}
                  {inPantry && (
                    <div className="p-2 rounded-lg bg-[#DDF5E8]/60 border border-[#16A66A]/20 text-xs text-[#0E6842] flex items-center justify-between">
                      <div className="flex items-center gap-1.5 truncate">
                        <span className="material-symbols-outlined text-[16px] text-[#16A66A]">
                          shopping_bag
                        </span>
                        <span className="font-semibold truncate">
                          Qty: {food.pantry_quantity || "1 unit"}
                        </span>
                      </div>
                      <span className="text-[10px] font-bold text-emerald-800 bg-[#DDF5E8] px-1.5 py-0.5 rounded">
                        {food.pantry_in_stock !== false ? "In Stock" : "Out of Stock"}
                      </span>
                    </div>
                  )}
                </div>

                {/* Card Action Footer */}
                <div className="p-3 border-t border-slate-100 bg-slate-50/50 rounded-b-xl flex items-center gap-2">
                  {inPantry ? (
                    <>
                      {/* Update Quantity Button */}
                      <button
                        type="button"
                        onClick={() => handleOpenEditModal(food)}
                        className="flex-1 py-1.5 px-2 bg-white hover:bg-slate-100 text-slate-800 border border-slate-200 rounded-lg text-xs font-semibold transition-colors flex items-center justify-center gap-1"
                        title="Update pantry quantity"
                      >
                        <span className="material-symbols-outlined text-[15px] text-slate-600">
                          edit
                        </span>
                        <span>Update</span>
                      </button>

                      {/* Remove Button */}
                      <button
                        type="button"
                        onClick={() => handleOpenDeleteModal(food)}
                        className="py-1.5 px-2.5 bg-red-50 hover:bg-red-100 text-red-700 border border-red-200 rounded-lg text-xs font-semibold transition-colors flex items-center justify-center gap-1"
                        title="Remove from pantry"
                      >
                        <span className="material-symbols-outlined text-[15px]">delete</span>
                        <span className="hidden sm:inline">Remove</span>
                      </button>
                    </>
                  ) : (
                    /* Add to Pantry Button */
                    <button
                      type="button"
                      onClick={() => handleOpenAddModal(food)}
                      className="w-full py-2 px-3 bg-[#16A66A] hover:bg-[#138e5b] text-white rounded-lg text-xs md:text-sm font-semibold transition-colors shadow-sm flex items-center justify-center gap-1.5"
                    >
                      <span className="material-symbols-outlined text-[18px]">add_circle</span>
                      <span>Add to Pantry</span>
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Pagination Controls */}
      {!isLoading && totalPages > 1 && (
        <div className="flex flex-col sm:flex-row items-center justify-between gap-3 bg-white rounded-xl border border-slate-200/80 p-4 shadow-sm">
          <div className="text-xs text-slate-500">
            Page <strong className="text-slate-800">{page}</strong> of{" "}
            <strong className="text-slate-800">{totalPages}</strong>
          </div>

          <div className="flex items-center gap-1.5">
            <button
              type="button"
              disabled={page <= 1}
              onClick={() => setPage((prev) => Math.max(1, prev - 1))}
              className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 disabled:opacity-40 disabled:cursor-not-allowed text-slate-700 text-xs font-semibold rounded-lg transition-colors flex items-center gap-1"
            >
              <span className="material-symbols-outlined text-[16px]">chevron_left</span>
              <span>Previous</span>
            </button>

            {/* Quick page jumps */}
            <div className="hidden md:flex items-center gap-1">
              {Array.from({ length: Math.min(5, totalPages) }, (_, idx) => {
                let p = idx + 1;
                if (totalPages > 5 && page > 3) {
                  p = page - 3 + idx + 1;
                  if (p > totalPages) p = totalPages - (4 - idx);
                }
                return (
                  <button
                    key={p}
                    type="button"
                    onClick={() => setPage(p)}
                    className={`w-7 h-7 text-xs font-bold rounded-lg transition-colors ${
                      page === p
                        ? "bg-[#142D4E] text-white"
                        : "bg-slate-100 text-slate-700 hover:bg-slate-200"
                    }`}
                  >
                    {p}
                  </button>
                );
              })}
            </div>

            <button
              type="button"
              disabled={page >= totalPages}
              onClick={() => setPage((prev) => Math.min(totalPages, prev + 1))}
              className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 disabled:opacity-40 disabled:cursor-not-allowed text-slate-700 text-xs font-semibold rounded-lg transition-colors flex items-center gap-1"
            >
              <span>Next</span>
              <span className="material-symbols-outlined text-[16px]">chevron_right</span>
            </button>
          </div>
        </div>
      )}

      {/* ─── FOOD DETAILS & PRICING MODAL ─── */}
      {detailFood && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-2xl max-w-lg w-full border border-slate-200 overflow-hidden animate-in fade-in zoom-in-95 duration-150 max-h-[90vh] flex flex-col">
            {/* Modal Header */}
            <div className="p-5 border-b border-slate-100 flex items-start justify-between bg-slate-50 shrink-0">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="text-[11px] font-semibold text-slate-600 bg-slate-200 px-2 py-0.5 rounded-full">
                    {detailFood.food_category || "General"}
                  </span>
                  <span className="text-[11px] font-medium text-slate-500 bg-slate-100 px-2 py-0.5 rounded-full">
                    {detailFood.data_source || "Catalog"}
                  </span>
                </div>
                <h3 className="font-bold text-[#142D4E] text-lg leading-tight">
                  {detailFood.name}
                </h3>
                {detailFood.name_local && detailFood.name_local !== detailFood.name && (
                  <p className="text-xs text-slate-500 italic">{detailFood.name_local}</p>
                )}
              </div>
              <button
                type="button"
                onClick={() => setDetailFood(null)}
                className="text-slate-400 hover:text-slate-600 p-1 rounded-lg"
              >
                <span className="material-symbols-outlined text-[22px]">close</span>
              </button>
            </div>

            {/* Modal Scrollable Body */}
            <div className="p-5 space-y-5 overflow-y-auto">
              {detailLoading ? (
                <div className="py-12 text-center space-y-2">
                  <span className="material-symbols-outlined text-[32px] text-[#16A66A] animate-spin">
                    progress_activity
                  </span>
                  <p className="text-xs text-slate-500">Loading details & pricing...</p>
                </div>
              ) : (
                <>
                  {/* Indian Food Pricing Section */}
                  <div className="p-4 rounded-xl bg-gradient-to-br from-slate-50 to-[#F2FAF6] border border-slate-200 space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-1.5">
                        <span className="material-symbols-outlined text-[18px] text-[#16A66A]">
                          payments
                        </span>
                        <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700">
                          Indian Food Pricing
                        </h4>
                      </div>
                      {/* Region Selector */}
                      <select
                        value={detailRegion}
                        onChange={(e) => handleOpenDetailModal(detailFood, e.target.value)}
                        className="text-xs py-1 px-2 bg-white border border-slate-200 rounded text-slate-700 focus:outline-none focus:border-[#16A66A]"
                      >
                        <option value="National">National</option>
                        <option value="Delhi">Delhi</option>
                        <option value="Mumbai">Mumbai</option>
                        <option value="Bengaluru">Bengaluru</option>
                        <option value="Kolkata">Kolkata</option>
                      </select>
                    </div>

                    {foodDetailData?.price !== null && foodDetailData?.price !== undefined ? (
                      <div className="space-y-2.5">
                        <div className="flex items-baseline justify-between">
                          <div>
                            <span className="text-2xl font-black text-[#142D4E]">
                              {foodDetailData.price_formatted || `₹${foodDetailData.price}/${foodDetailData.price_unit || "kg"}`}
                            </span>
                            <span className="text-xs text-slate-500 ml-1.5">
                              ({foodDetailData.price_region || detailRegion})
                            </span>
                          </div>
                          <div>
                            {foodDetailData.price_type === "verified" ? (
                              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold bg-[#DDF5E8] text-[#0E6842] border border-[#16A66A]/30">
                                <span className="material-symbols-outlined text-[14px]">verified</span>
                                <span>Verified Market Price</span>
                              </span>
                            ) : (
                              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold bg-amber-50 text-amber-800 border border-amber-200">
                                <span className="material-symbols-outlined text-[14px]">info</span>
                                <span>Estimated Price</span>
                              </span>
                            )}
                          </div>
                        </div>

                        <div className="text-xs text-slate-600 space-y-1 bg-white/80 p-2.5 rounded-lg border border-slate-100">
                          <p>
                            <span className="font-semibold text-slate-700">Source:</span>{" "}
                            {foodDetailData.price_source || "Curated Market Index"}
                          </p>
                          {foodDetailData.price_last_updated && (
                            <p>
                              <span className="font-semibold text-slate-700">Last Updated:</span>{" "}
                              {foodDetailData.price_last_updated}
                            </p>
                          )}
                        </div>

                        {/* All Available Regional Prices */}
                        {foodDetailData.prices && foodDetailData.prices.length > 1 && (
                          <div className="pt-2">
                            <p className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-1.5">
                              Other Available Regions
                            </p>
                            <div className="grid grid-cols-2 gap-1.5">
                              {foodDetailData.prices.map((p: any) => (
                                <button
                                  key={p.price_id}
                                  type="button"
                                  onClick={() => handleOpenDetailModal(detailFood, p.region)}
                                  className={`text-left p-2 rounded-lg border text-xs transition-colors flex justify-between items-center ${
                                    p.region?.toLowerCase() === detailRegion.toLowerCase()
                                      ? "bg-[#DDF5E8] border-[#16A66A] text-[#0E6842] font-bold"
                                      : "bg-white border-slate-200 hover:bg-slate-50 text-slate-700"
                                  }`}
                                >
                                  <span>{p.region}</span>
                                  <span className="font-bold">{p.formatted_price || `₹${p.price}/${p.unit}`}</span>
                                </button>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    ) : (
                      <div className="p-3 bg-white/70 rounded-lg text-center text-xs text-slate-500">
                        <span className="material-symbols-outlined text-[20px] text-slate-400 block mx-auto mb-1">
                          money_off
                        </span>
                        Price unavailable for this food item.
                      </div>
                    )}
                  </div>

                  {/* Nutritional Composition per 100g */}
                  <div className="space-y-2">
                    <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500">
                      Nutritional Composition (per 100g)
                    </h4>
                    <div className="grid grid-cols-5 gap-2 text-center">
                      <div className="p-2 bg-slate-50 rounded-lg border border-slate-100">
                        <span className="text-[10px] text-slate-500 block uppercase">Energy</span>
                        <span className="font-bold text-sm text-slate-900">
                          {Math.round(detailFood.calories_kcal)}
                        </span>
                        <span className="text-[10px] text-slate-400 block">kcal</span>
                      </div>
                      <div className="p-2 bg-slate-50 rounded-lg border border-slate-100">
                        <span className="text-[10px] text-slate-500 block uppercase">Protein</span>
                        <span className="font-bold text-sm text-emerald-700">
                          {Number(detailFood.protein_g).toFixed(1)}
                        </span>
                        <span className="text-[10px] text-slate-400 block">g</span>
                      </div>
                      <div className="p-2 bg-slate-50 rounded-lg border border-slate-100">
                        <span className="text-[10px] text-slate-500 block uppercase">Carbs</span>
                        <span className="font-bold text-sm text-amber-700">
                          {Number(detailFood.carbohydrates_g).toFixed(1)}
                        </span>
                        <span className="text-[10px] text-slate-400 block">g</span>
                      </div>
                      <div className="p-2 bg-slate-50 rounded-lg border border-slate-100">
                        <span className="text-[10px] text-slate-500 block uppercase">Fat</span>
                        <span className="font-bold text-sm text-rose-700">
                          {Number(detailFood.fat_g).toFixed(1)}
                        </span>
                        <span className="text-[10px] text-slate-400 block">g</span>
                      </div>
                      <div className="p-2 bg-slate-50 rounded-lg border border-slate-100">
                        <span className="text-[10px] text-slate-500 block uppercase">Fiber</span>
                        <span className="font-bold text-sm text-indigo-700">
                          {detailFood.fiber_g ? Number(detailFood.fiber_g).toFixed(1) : "0"}
                        </span>
                        <span className="text-[10px] text-slate-400 block">g</span>
                      </div>
                    </div>
                  </div>

                  {/* Dietary & Allergen Attributes */}
                  <div className="flex flex-wrap items-center gap-1.5 pt-1">
                    {detailFood.is_vegetarian && (
                      <span className="text-xs font-semibold bg-emerald-50 text-emerald-800 px-2 py-0.5 rounded border border-emerald-200">
                        Vegetarian
                      </span>
                    )}
                    {detailFood.is_vegan && (
                      <span className="text-xs font-semibold bg-green-50 text-green-800 px-2 py-0.5 rounded border border-green-200">
                        Vegan
                      </span>
                    )}
                    {detailFood.is_gluten_free && (
                      <span className="text-xs font-semibold bg-amber-50 text-amber-800 px-2 py-0.5 rounded border border-amber-200">
                        Gluten-Free
                      </span>
                    )}
                    {detailFood.allergen_flags && detailFood.allergen_flags.length > 0 && (
                      <span className="text-xs font-medium bg-red-50 text-red-700 px-2 py-0.5 rounded border border-red-200">
                        Allergens: {detailFood.allergen_flags.join(", ")}
                      </span>
                    )}
                  </div>
                </>
              )}
            </div>

            {/* Modal Footer */}
            <div className="p-4 bg-slate-50 border-t border-slate-100 flex items-center justify-between shrink-0">
              <button
                type="button"
                onClick={() => setDetailFood(null)}
                className="px-4 py-2 text-xs md:text-sm font-semibold text-slate-600 hover:bg-slate-200 rounded-lg transition-colors"
              >
                Close
              </button>

              {detailFood.in_pantry ? (
                <div className="flex items-center gap-2">
                  <span className="text-xs font-semibold text-[#0E6842] bg-[#DDF5E8] px-2.5 py-1 rounded-md">
                    In Pantry ({detailFood.pantry_quantity || "1 unit"})
                  </span>
                  <button
                    type="button"
                    onClick={() => {
                      const food = detailFood;
                      setDetailFood(null);
                      handleOpenEditModal(food);
                    }}
                    className="px-4 py-2 text-xs md:text-sm font-semibold bg-[#142D4E] hover:bg-[#1b3d6a] text-white rounded-lg transition-colors flex items-center gap-1"
                  >
                    <span className="material-symbols-outlined text-[16px]">edit</span>
                    <span>Update Entry</span>
                  </button>
                </div>
              ) : (
                <button
                  type="button"
                  onClick={() => {
                    const food = detailFood;
                    setDetailFood(null);
                    handleOpenAddModal(food);
                  }}
                  className="px-5 py-2 text-xs md:text-sm font-semibold bg-[#16A66A] hover:bg-[#138e5b] text-white rounded-lg transition-colors flex items-center gap-1.5"
                >
                  <span className="material-symbols-outlined text-[16px]">add_circle</span>
                  <span>Add to Pantry</span>
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* ─── ADD TO PANTRY MODAL ─── */}
      {addModalFood && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-2xl max-w-md w-full border border-slate-200 overflow-hidden animate-in fade-in zoom-in-95 duration-150">
            <div className="p-5 border-b border-slate-100 flex items-center justify-between bg-slate-50">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-lg bg-[#DDF5E8] text-[#16A66A] flex items-center justify-center">
                  <span className="material-symbols-outlined text-[20px]">add_shopping_cart</span>
                </div>
                <h3 className="font-bold text-[#142D4E] text-base">Add to Pantry</h3>
              </div>
              <button
                type="button"
                onClick={() => setAddModalFood(null)}
                className="text-slate-400 hover:text-slate-600"
              >
                <span className="material-symbols-outlined text-[20px]">close</span>
              </button>
            </div>

            <div className="p-5 space-y-4">
              <div>
                <p className="text-xs text-slate-500 uppercase tracking-wider font-semibold">
                  Food Item
                </p>
                <p className="text-base font-bold text-slate-900 mt-0.5">{addModalFood.name}</p>
                <p className="text-xs text-slate-500">
                  {addModalFood.food_category} • {Math.round(addModalFood.calories_kcal)} kcal / 100g
                </p>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Quantity / Package Size
                </label>
                <input
                  type="text"
                  value={addQuantity}
                  onChange={(e) => setAddQuantity(e.target.value)}
                  placeholder="e.g. 500g, 1 kg, 2 packets, 1 unit"
                  className="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-200 rounded-lg text-slate-900 focus:outline-none focus:ring-2 focus:ring-[#16A66A]/40 focus:border-[#16A66A]"
                />
                {/* Quick quantity presets */}
                <div className="flex items-center gap-1.5 mt-2">
                  {["250g", "500g", "1 kg", "1 unit", "1 packet"].map((qty) => (
                    <button
                      key={qty}
                      type="button"
                      onClick={() => setAddQuantity(qty)}
                      className="px-2 py-0.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-[11px] rounded transition-colors"
                    >
                      {qty}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Optional Expiration Date
                </label>
                <input
                  type="date"
                  value={addExpiry}
                  onChange={(e) => setAddExpiry(e.target.value)}
                  className="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-200 rounded-lg text-slate-900 focus:outline-none focus:ring-2 focus:ring-[#16A66A]/40 focus:border-[#16A66A]"
                />
              </div>
            </div>

            <div className="p-4 bg-slate-50 border-t border-slate-100 flex items-center justify-end gap-2">
              <button
                type="button"
                onClick={() => setAddModalFood(null)}
                className="px-4 py-2 text-xs md:text-sm font-semibold text-slate-600 hover:bg-slate-200 rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={isSubmittingAdd}
                onClick={handleConfirmAdd}
                className="px-5 py-2 text-xs md:text-sm font-semibold bg-[#16A66A] hover:bg-[#138e5b] disabled:opacity-50 text-white rounded-lg transition-colors flex items-center gap-1.5"
              >
                {isSubmittingAdd && (
                  <span className="material-symbols-outlined text-[16px] animate-spin">
                    progress_activity
                  </span>
                )}
                <span>Confirm & Add</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ─── EDIT PANTRY ENTRY MODAL ─── */}
      {editModalFood && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-2xl max-w-md w-full border border-slate-200 overflow-hidden animate-in fade-in zoom-in-95 duration-150">
            <div className="p-5 border-b border-slate-100 flex items-center justify-between bg-slate-50">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-lg bg-blue-100 text-blue-700 flex items-center justify-center">
                  <span className="material-symbols-outlined text-[20px]">edit</span>
                </div>
                <h3 className="font-bold text-[#142D4E] text-base">Update Pantry Entry</h3>
              </div>
              <button
                type="button"
                onClick={() => setEditModalFood(null)}
                className="text-slate-400 hover:text-slate-600"
              >
                <span className="material-symbols-outlined text-[20px]">close</span>
              </button>
            </div>

            <div className="p-5 space-y-4">
              <div>
                <p className="text-xs text-slate-500 uppercase tracking-wider font-semibold">
                  Food Item
                </p>
                <p className="text-base font-bold text-slate-900 mt-0.5">{editModalFood.name}</p>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Available Quantity
                </label>
                <input
                  type="text"
                  value={editQuantity}
                  onChange={(e) => setEditQuantity(e.target.value)}
                  placeholder="e.g. 500g, 1 kg, 2 packets"
                  className="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-200 rounded-lg text-slate-900 focus:outline-none focus:ring-2 focus:ring-[#16A66A]/40 focus:border-[#16A66A]"
                />
              </div>

              <div className="flex items-center justify-between p-3 rounded-lg bg-slate-50 border border-slate-200">
                <div>
                  <p className="text-xs font-bold text-slate-800">In Stock Status</p>
                  <p className="text-[11px] text-slate-500">
                    Mark whether this ingredient is currently available
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => setEditInStock(!editInStock)}
                  className={`w-12 h-6 flex items-center rounded-full p-1 transition-colors ${
                    editInStock ? "bg-[#16A66A]" : "bg-slate-300"
                  }`}
                >
                  <div
                    className={`bg-white w-4 h-4 rounded-full shadow-md transform transition-transform ${
                      editInStock ? "translate-x-6" : "translate-x-0"
                    }`}
                  />
                </button>
              </div>
            </div>

            <div className="p-4 bg-slate-50 border-t border-slate-100 flex items-center justify-end gap-2">
              <button
                type="button"
                onClick={() => setEditModalFood(null)}
                className="px-4 py-2 text-xs md:text-sm font-semibold text-slate-600 hover:bg-slate-200 rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={isSubmittingEdit}
                onClick={handleConfirmEdit}
                className="px-5 py-2 text-xs md:text-sm font-semibold bg-[#142D4E] hover:bg-[#1b3d6a] disabled:opacity-50 text-white rounded-lg transition-colors flex items-center gap-1.5"
              >
                {isSubmittingEdit && (
                  <span className="material-symbols-outlined text-[16px] animate-spin">
                    progress_activity
                  </span>
                )}
                <span>Save Changes</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ─── DELETE / REMOVE CONFIRMATION MODAL ─── */}
      {deleteConfirmFood && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-2xl max-w-sm w-full border border-slate-200 overflow-hidden animate-in fade-in zoom-in-95 duration-150">
            <div className="p-5 text-center space-y-3">
              <div className="w-12 h-12 rounded-full bg-red-100 text-red-600 mx-auto flex items-center justify-center">
                <span className="material-symbols-outlined text-[28px]">delete</span>
              </div>
              <h3 className="font-bold text-slate-900 text-base">Remove from Pantry?</h3>
              <p className="text-xs text-slate-600">
                Are you sure you want to remove <strong>&quot;{deleteConfirmFood.name}&quot;</strong> from your pantry?
                The food will remain in the catalog and can be re-added anytime.
              </p>
            </div>

            <div className="p-4 bg-slate-50 border-t border-slate-100 flex items-center justify-end gap-2">
              <button
                type="button"
                onClick={() => setDeleteConfirmFood(null)}
                className="px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-200 rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={isSubmittingDelete}
                onClick={handleConfirmDelete}
                className="px-4 py-2 text-xs font-semibold bg-red-600 hover:bg-red-700 disabled:opacity-50 text-white rounded-lg transition-colors flex items-center gap-1.5"
              >
                {isSubmittingDelete && (
                  <span className="material-symbols-outlined text-[14px] animate-spin">
                    progress_activity
                  </span>
                )}
                <span>Remove Item</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
