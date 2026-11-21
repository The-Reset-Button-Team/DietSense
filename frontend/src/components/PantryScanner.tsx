"use client";

import React, { useState, useRef, useMemo, useEffect } from "react";
import Image from "next/image";
import { PantryItem } from "@/types";
import { apiClient } from "@/lib/api-client";
import { RECIPE_CATALOG } from "@/data/recipes";
import { checkPantryMatch } from "@/lib/nutrition";

export interface DetectedItem {
  id?: string;
  name: string;
  category: string;
  quantity: string;
  expiry_date?: string;
  confidence?: number;
  needs_review?: boolean;
  matched_food?: {
    food_id?: number;
    name?: string;
    food_category?: string;
    calories_kcal?: number;
    protein_g?: number;
    is_vegetarian?: boolean;
  };
  selected?: boolean;
}

interface RecipeRecommendation {
  id: number;
  name: string;
  category: string;
  coverage_pct: number;
  can_cook_now: boolean;
  matched_ingredients: string[];
  missing_ingredients: string[];
  instructions: string;
}

interface ShoppingListItem {
  name: string;
  category: string;
  recipe: string;
  suggested_quantity: string;
}

interface ShoppingListResponse {
  total_required: number;
  in_pantry_count: number;
  missing_count: number;
  pantry_match_pct: number;
  recipes_evaluated: string[];
  missing_items: ShoppingListItem[];
  available_items: Array<{ name: string; recipe: string }>;
}

interface PantryScannerProps {
  pantryItems: PantryItem[];
  togglePantryItem: (id: string) => void;
  onAddManualItem: (name: string) => void;
  onAddBatchItems?: (items: Array<{ name: string; category?: string; quantity?: string; expiry_date?: string }>) => void;
  onApplyToMealPlan?: () => void;
  onClearPantry?: () => Promise<void> | void;
}

export const PantryScanner: React.FC<PantryScannerProps> = ({
  pantryItems,
  togglePantryItem,
  onAddManualItem,
  onAddBatchItems,
  onApplyToMealPlan,
  onClearPantry,
}) => {
  const [pantryInputText, setPantryInputText] = useState<string>("");
  const [pantryInputExpiry, setPantryInputExpiry] = useState<string>("");
  const [isScanning, setIsScanning] = useState<boolean>(false);
  const [scanMessage, setScanMessage] = useState<string>("");
  const [errorMessage, setErrorMessage] = useState<string>("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  // Clear Pantry Modal & Notification State
  const [isClearModalOpen, setIsClearModalOpen] = useState<boolean>(false);
  const [isClearing, setIsClearing] = useState<boolean>(false);
  const [clearSuccessToast, setClearSuccessToast] = useState<string | null>(null);
  const [clearError, setClearError] = useState<string | null>(null);

  // Active view tab: "inventory" | "shopping_list" | "cook_now"
  const [activeSubTab, setActiveSubTab] = useState<"inventory" | "shopping_list" | "cook_now">("inventory");

  // Shopping List & Recommendations State
  const [shoppingList, setShoppingList] = useState<ShoppingListResponse | null>(null);
  const [loadingShoppingList, setLoadingShoppingList] = useState<boolean>(false);
  const [pantryRecipes, setPantryRecipes] = useState<RecipeRecommendation[]>([]);
  const [loadingRecipes, setLoadingRecipes] = useState<boolean>(false);

  // Staged OCR queue items
  const [detectedItems, setDetectedItems] = useState<DetectedItem[]>([
    {
      id: "staged_1",
      name: "Amul Malai Paneer",
      category: "Dairy & Protein",
      quantity: "200g",
      expiry_date: new Date(Date.now() + 5 * 86400000).toISOString().split("T")[0],
      confidence: 0.98,
      needs_review: false,
      selected: true,
      matched_food: { name: "Paneer / Cottage Cheese", calories_kcal: 265, protein_g: 18.3 },
    },
    {
      id: "staged_2",
      name: "Fresh Palak (Spinach)",
      category: "Produce",
      quantity: "250g",
      expiry_date: new Date(Date.now() + 3 * 86400000).toISOString().split("T")[0],
      confidence: 0.94,
      needs_review: false,
      selected: true,
      matched_food: { name: "Spinach", calories_kcal: 23, protein_g: 2.9 },
    },
    {
      id: "staged_3",
      name: "Yellow Moong Dal",
      category: "Grains & Pulses",
      quantity: "500g",
      expiry_date: new Date(Date.now() + 90 * 86400000).toISOString().split("T")[0],
      confidence: 0.96,
      needs_review: false,
      selected: true,
      matched_food: { name: "Moong Dal", calories_kcal: 348, protein_g: 24.0 },
    },
    {
      id: "staged_4",
      name: "Roasted Makhana",
      category: "Pantry Staples",
      quantity: "100g",
      expiry_date: new Date(Date.now() + 60 * 86400000).toISOString().split("T")[0],
      confidence: 0.74,
      needs_review: true,
      selected: true,
    },
  ]);

  const fileReceiptRef = useRef<HTMLInputElement | null>(null);
  const fileFridgeRef = useRef<HTMLInputElement | null>(null);

  const inStockCount = useMemo(() => pantryItems.filter((i) => i.inStock).length, [pantryItems]);

  // Fetch Shopping List
  const fetchShoppingList = async () => {
    setLoadingShoppingList(true);
    try {
      const res = await apiClient<ShoppingListResponse>("/api/pantry/shopping-list", {
        method: "POST",
        body: JSON.stringify({}),
      });
      setShoppingList(res);
    } catch {
      // Offline fallback
    } finally {
      setLoadingShoppingList(false);
    }
  };

  // Fetch Pantry Recipe Recommendations
  const fetchPantryRecipes = async () => {
    setLoadingRecipes(true);
    try {
      const res = await apiClient<{ status: string; recipes: RecipeRecommendation[] }>("/api/pantry/recipe-recommendations");
      if (res && res.recipes) {
        setPantryRecipes(res.recipes);
      }
    } catch {
      // Offline fallback
    } finally {
      setLoadingRecipes(false);
    }
  };

  useEffect(() => {
    if (activeSubTab === "shopping_list") {
      fetchShoppingList();
    } else if (activeSubTab === "cook_now") {
      fetchPantryRecipes();
    }
  }, [activeSubTab, inStockCount]);

  useEffect(() => {
    if (clearSuccessToast) {
      const timer = setTimeout(() => {
        setClearSuccessToast(null);
      }, 4000);
      return () => clearTimeout(timer);
    }
  }, [clearSuccessToast]);

  const handleConfirmClear = async () => {
    setIsClearing(true);
    setClearError(null);
    try {
      if (onClearPantry) {
        await onClearPantry();
      } else {
        await apiClient("/api/pantry/clear", { method: "DELETE" });
      }

      setIsClearModalOpen(false);
      setClearSuccessToast("Pantry cleared successfully.");

      // Automatically refresh shopping list and recipe recommendations
      if (activeSubTab === "shopping_list") {
        fetchShoppingList();
      } else if (activeSubTab === "cook_now") {
        fetchPantryRecipes();
      }
    } catch (err: any) {
      setClearError(err?.message || "Failed to clear pantry. Please try again.");
    } finally {
      setIsClearing(false);
    }
  };

  const handleAddManual = () => {
    if (!pantryInputText.trim()) return;
    if (onAddBatchItems) {
      onAddBatchItems([
        {
          name: pantryInputText.trim(),
          category: "General",
          quantity: "1 unit",
          expiry_date: pantryInputExpiry || undefined,
        },
      ]);
    } else {
      onAddManualItem(pantryInputText.trim());
    }
    setPantryInputText("");
    setPantryInputExpiry("");
  };

  const handleFile = (file: File) => {
    setSelectedFile(file);
    setErrorMessage("");
    setScanMessage("");
    if (file.type.startsWith("image/")) {
      setPreviewUrl(URL.createObjectURL(file));
    } else {
      setPreviewUrl(null);
    }
    executeScan(file);
  };

  const executeScan = async (file: File) => {
    setIsScanning(true);
    setErrorMessage("");
    try {
      const formData = new FormData();
      formData.append("file", file);
      const isPdf = file.name.toLowerCase().endsWith(".pdf") || file.type === "application/pdf";
      formData.append("scan_type", isPdf ? "receipt" : "fridge");

      const res = await apiClient<{
        status: string;
        items: DetectedItem[];
        detected_items: DetectedItem[];
        message?: string;
        needs_review_count?: number;
      }>("/api/pantry/scan", {
        method: "POST",
        body: formData,
      });

      const extracted = res.detected_items || res.items || [];
      if (extracted.length > 0) {
        setDetectedItems(extracted.map((it) => ({ ...it, selected: true })));
        setScanMessage(res.message || `Detected ${extracted.length} items from OCR scan.`);
      } else {
        setScanMessage(res.message || "No ingredients found in document. You can add items manually.");
      }
    } catch (err: any) {
      setErrorMessage(err?.detail || err?.message || "Scan failed. Please upload a clear image or PDF receipt.");
    } finally {
      setIsScanning(false);
    }
  };

  const loadSampleBlinkit = () => {
    setDetectedItems([
      {
        id: "b_1",
        name: "Amul Cow Milk",
        category: "Dairy & Protein",
        quantity: "500ml",
        expiry_date: new Date(Date.now() + 2 * 86400000).toISOString().split("T")[0],
        confidence: 0.97,
        needs_review: false,
        selected: true,
      },
      {
        id: "b_2",
        name: "Organic Tofu",
        category: "Dairy & Protein",
        quantity: "200g",
        expiry_date: new Date(Date.now() + 7 * 86400000).toISOString().split("T")[0],
        confidence: 0.95,
        needs_review: false,
        selected: true,
      },
      {
        id: "b_3",
        name: "Broccoli Florets",
        category: "Produce",
        quantity: "300g",
        expiry_date: new Date(Date.now() + 4 * 86400000).toISOString().split("T")[0],
        confidence: 0.92,
        needs_review: false,
        selected: true,
      },
      {
        id: "b_4",
        name: "Rolled Oats",
        category: "Grains & Pulses",
        quantity: "1kg",
        expiry_date: new Date(Date.now() + 90 * 86400000).toISOString().split("T")[0],
        confidence: 0.98,
        needs_review: false,
        selected: true,
      },
    ]);
    setScanMessage("Loaded verified Blinkit invoice preset (4 items).");
  };

  const loadSampleFridge = () => {
    setDetectedItems([
      {
        id: "f_1",
        name: "Fresh Palak (Spinach)",
        category: "Produce",
        quantity: "1 bunch",
        expiry_date: new Date(Date.now() + 3 * 86400000).toISOString().split("T")[0],
        confidence: 0.96,
        needs_review: false,
        selected: true,
      },
      {
        id: "f_2",
        name: "Milk",
        category: "Dairy & Protein",
        quantity: "500 ml",
        expiry_date: new Date(Date.now() + 2 * 86400000).toISOString().split("T")[0],
        confidence: 0.95,
        needs_review: false,
        selected: true,
      },
      {
        id: "f_3",
        name: "Ginger Garlic Paste",
        category: "Pantry Staples",
        quantity: "100g",
        expiry_date: new Date(Date.now() + 20 * 86400000).toISOString().split("T")[0],
        confidence: 0.82,
        needs_review: true,
        selected: true,
      },
      {
        id: "f_4",
        name: "Cucumber",
        category: "Produce",
        quantity: "3 units",
        expiry_date: new Date(Date.now() + 5 * 86400000).toISOString().split("T")[0],
        confidence: 0.96,
        needs_review: false,
        selected: true,
      },
    ]);
    setScanMessage("Loaded smart fridge snapshot preset (4 items).");
  };

  // Inline correction handlers
  const updateStagedItem = (index: number, field: keyof DetectedItem, value: any) => {
    setDetectedItems((prev) => {
      const updated = [...prev];
      updated[index] = { ...updated[index], [field]: value };
      return updated;
    });
  };

  const removeStagedItem = (index: number) => {
    setDetectedItems((prev) => prev.filter((_, i) => i !== index));
  };

  const commitAllStaged = () => {
    const selected = detectedItems.filter((i) => i.selected);
    if (selected.length === 0) return;

    if (onAddBatchItems) {
      onAddBatchItems(
        selected.map((s) => ({
          name: s.name,
          category: s.category,
          quantity: s.quantity,
          expiry_date: s.expiry_date,
        }))
      );
    } else {
      selected.forEach((s) => onAddManualItem(s.name));
    }
    setDetectedItems([]);
    setScanMessage(`Committed ${selected.length} verified items to your active pantry ledger.`);
  };

  // Helper for freshness styling
  const renderFreshnessBadge = (item: PantryItem) => {
    const status = item.freshness_status || "unspecified";
    if (status === "expired") {
      return (
        <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-rose-50 text-rose-700 border border-rose-200 flex items-center gap-1">
          <span className="w-1.5 h-1.5 rounded-full bg-rose-600 animate-pulse" />
          {item.freshness_indicator || "Expired"}
        </span>
      );
    }
    if (status === "expiring_soon") {
      return (
        <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-50 text-amber-700 border border-amber-200 flex items-center gap-1">
          <span className="w-1.5 h-1.5 rounded-full bg-amber-600" />
          {item.freshness_indicator || "Expiring Soon"}
        </span>
      );
    }
    if (status === "fresh") {
      return (
        <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200 flex items-center gap-1">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-600" />
          {item.freshness_indicator || "Fresh"}
        </span>
      );
    }
    return (
      <span className="px-2 py-0.5 rounded-full text-[10px] bg-slate-50 text-slate-500 border border-slate-200">
        No expiry set
      </span>
    );
  };

  return (
    <div className="space-y-space-lg pb-16">
      {/* Top Editorial Header & Live Stats */}
      <div className="flex flex-col lg:flex-row lg:items-end justify-between gap-space-md pt-space-xs pb-space-sm border-b border-surface-container-highest">
        <div className="space-y-1">
          <div className="flex items-center gap-space-xs text-primary">
            <span className="material-symbols-outlined text-[18px]">inventory_2</span>
            <span className="font-label-sm text-label-sm uppercase tracking-wider text-primary font-bold">
              Inventory Ledger • Vision, OCR &amp; Freshness
            </span>
          </div>
          <h1 className="font-headline-lg text-headline-lg text-primary tracking-tight font-serif">
            Pantry Intelligence &amp; Scanner
          </h1>
          <p className="font-body-md text-body-md text-on-surface-variant max-w-2xl">
            OCR receipt parsing, expiry tracking, freshness indicators, and missing-ingredient shopping lists.
          </p>
        </div>

        {/* 3 Metric Capsules */}
        <div className="grid grid-cols-3 gap-2">
          <div className="bg-surface-container-low p-space-sm rounded-lg border border-surface-container text-center">
            <span className="font-label-sm text-label-sm uppercase text-on-surface-variant block">In Stock</span>
            <span className="font-metric-num text-[20px] text-primary font-bold">{inStockCount}</span>
          </div>
          <div className="bg-surface-container-low p-space-sm rounded-lg border border-surface-container text-center">
            <span className="font-label-sm text-label-sm uppercase text-on-surface-variant block">Staged</span>
            <span className="font-metric-num text-[20px] text-secondary font-bold">{detectedItems.length}</span>
          </div>
          <div className="bg-surface-container-low p-space-sm rounded-lg border border-surface-container text-center">
            <span className="font-label-sm text-label-sm uppercase text-on-surface-variant block">Catalog DB</span>
            <span className="font-metric-num text-[20px] text-on-surface font-bold">14,099</span>
          </div>
        </div>
      </div>

      {/* Sub Tabs: Inventory | Shopping List | Cook Now */}
      <div className="flex border-b border-surface-container gap-2">
        <button
          onClick={() => setActiveSubTab("inventory")}
          className={`px-4 py-2 font-label-md text-label-md border-b-2 font-semibold transition-all flex items-center gap-1.5 ${
            activeSubTab === "inventory"
              ? "border-primary text-primary"
              : "border-transparent text-on-surface-variant hover:text-on-surface"
          }`}
        >
          <span className="material-symbols-outlined text-[18px]">kitchen</span>
          Inventory &amp; Scanner
        </button>
        <button
          onClick={() => setActiveSubTab("shopping_list")}
          className={`px-4 py-2 font-label-md text-label-md border-b-2 font-semibold transition-all flex items-center gap-1.5 ${
            activeSubTab === "shopping_list"
              ? "border-primary text-primary"
              : "border-transparent text-on-surface-variant hover:text-on-surface"
          }`}
        >
          <span className="material-symbols-outlined text-[18px]">shopping_cart</span>
          Missing Ingredients Shopping List
        </button>
        <button
          onClick={() => setActiveSubTab("cook_now")}
          className={`px-4 py-2 font-label-md text-label-md border-b-2 font-semibold transition-all flex items-center gap-1.5 ${
            activeSubTab === "cook_now"
              ? "border-primary text-primary"
              : "border-transparent text-on-surface-variant hover:text-on-surface"
          }`}
        >
          <span className="material-symbols-outlined text-[18px]">restaurant</span>
          Pantry Recipe Match
        </button>
      </div>

      {/* TAB 1: Inventory & Scanner */}
      {activeSubTab === "inventory" && (
        <div className="space-y-space-lg">
          {/* Main Ingestion Dropzones */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-space-lg">
            {/* Dropzones & Presets (7 cols) */}
            <div className="lg:col-span-7 space-y-space-md">
              <div className="flex items-center justify-between">
                <span className="font-headline-sm text-headline-sm text-primary font-serif">
                  Document &amp; Photo Scanner
                </span>
                <span className="font-label-sm text-label-sm text-on-surface-variant">
                  Supports PDF receipts &amp; JPEG/PNG snaps
                </span>
              </div>

              {/* Ingestion Dual Drop Area */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-space-md">
                {/* Drop Area A: PDF / Invoice */}
                <div
                  onClick={() => fileReceiptRef.current?.click()}
                  className="relative group bg-surface-container-lowest p-space-lg rounded-xl shadow-sm border border-surface-container flex flex-col justify-between transition-all hover:bg-surface-container-low cursor-pointer"
                >
                  <input
                    ref={fileReceiptRef}
                    type="file"
                    accept="application/pdf,image/*"
                    className="hidden"
                    onChange={(e) => {
                      if (e.target.files?.[0]) handleFile(e.target.files[0]);
                    }}
                  />
                  <div className="space-y-space-sm">
                    <div className="w-12 h-12 rounded-lg bg-surface-container flex items-center justify-center text-primary group-hover:scale-105 transition-transform">
                      <span className="material-symbols-outlined text-[28px]">receipt_long</span>
                    </div>
                    <div>
                      <h3 className="font-headline-sm text-headline-sm text-on-surface font-serif">
                        PDF Receipt / Invoice
                      </h3>
                      <p className="font-body-sm text-body-sm text-on-surface-variant mt-1">
                        Blinkit, Instamart, Zepto, Swiggy grocery invoices.
                      </p>
                    </div>
                  </div>
                  <div className="pt-space-md mt-space-md flex items-center justify-between text-on-surface-variant border-t border-surface-container">
                    <span className="font-label-sm text-label-sm flex items-center gap-1 text-secondary font-semibold">
                      <span className="material-symbols-outlined text-[14px]">auto_awesome</span> PDF Parser
                    </span>
                    <span className="font-label-sm text-label-sm font-semibold text-primary underline underline-offset-4">
                      Browse Document
                    </span>
                  </div>
                </div>

                {/* Drop Area B: Fridge & Pantry Snapshot */}
                <div
                  onClick={() => fileFridgeRef.current?.click()}
                  className="relative group bg-surface-container-lowest p-space-lg rounded-xl shadow-sm border border-surface-container flex flex-col justify-between transition-all hover:bg-surface-container-low cursor-pointer"
                >
                  <input
                    ref={fileFridgeRef}
                    type="file"
                    accept="image/*"
                    className="hidden"
                    onChange={(e) => {
                      if (e.target.files?.[0]) handleFile(e.target.files[0]);
                    }}
                  />
                  <div className="space-y-space-sm">
                    <div className="w-12 h-12 rounded-lg bg-surface-container flex items-center justify-center text-secondary group-hover:scale-105 transition-transform">
                      <span className="material-symbols-outlined text-[28px]">photo_camera</span>
                    </div>
                    <div>
                      <h3 className="font-headline-sm text-headline-sm text-on-surface font-serif">
                        Fridge &amp; Pantry Photo
                      </h3>
                      <p className="font-body-sm text-body-sm text-on-surface-variant mt-1">
                        Crisper drawers, shelf snapshots, or countertop ingredients.
                      </p>
                    </div>
                  </div>
                  <div className="pt-space-md mt-space-md flex items-center justify-between text-on-surface-variant border-t border-surface-container">
                    <span className="font-label-sm text-label-sm flex items-center gap-1 text-secondary font-semibold">
                      <span className="material-symbols-outlined text-[14px]">bolt</span> Local OCR
                    </span>
                    <span className="font-label-sm text-label-sm font-semibold text-primary underline underline-offset-4">
                      Upload Snap
                    </span>
                  </div>
                </div>
              </div>

              {/* Status & Messages */}
              {isScanning && (
                <div className="p-3 rounded-lg bg-primary/10 border border-primary/20 flex items-center gap-2 text-primary text-xs font-medium">
                  <span className="material-symbols-outlined text-[18px] animate-spin">refresh</span>
                  Processing document OCR and verifying against food database...
                </div>
              )}

              {errorMessage && (
                <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-700 text-xs font-medium flex items-center gap-2">
                  <span className="material-symbols-outlined text-[18px]">error</span>
                  {errorMessage}
                </div>
              )}

              {scanMessage && !errorMessage && (
                <div className="p-3 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-medium flex items-center gap-2">
                  <span className="material-symbols-outlined text-[18px]">check_circle</span>
                  {scanMessage}
                </div>
              )}

              {/* Clinical Simulation Fast Triggers */}
              <div className="bg-surface-container-low p-space-md rounded-xl shadow-sm border border-surface-container space-y-space-xs">
                <div className="flex items-center justify-between">
                  <span className="font-label-md text-label-md text-on-surface font-semibold flex items-center gap-1.5">
                    <span className="material-symbols-outlined text-[16px] text-primary">science</span>
                    Demo Presets (Zero-Upload Testing)
                  </span>
                </div>
                <div className="flex flex-wrap gap-space-sm pt-space-xs">
                  <button
                    type="button"
                    onClick={loadSampleBlinkit}
                    className="flex items-center gap-space-xs px-space-md py-2 bg-surface-container-lowest hover:bg-surface-container-high text-primary rounded shadow-sm text-label-sm font-label-sm transition-all border border-surface-container"
                  >
                    <span className="material-symbols-outlined text-[16px] text-secondary">description</span>
                    Load Blinkit Receipt Preset
                  </button>
                  <button
                    type="button"
                    onClick={loadSampleFridge}
                    className="flex items-center gap-space-xs px-space-md py-2 bg-surface-container-lowest hover:bg-surface-container-high text-primary rounded shadow-sm text-label-sm font-label-sm transition-all border border-surface-container"
                  >
                    <span className="material-symbols-outlined text-[16px] text-secondary">image</span>
                    Load Fridge Snapshot Preset
                  </button>
                </div>
              </div>

              {/* Quick Manual Entry Input with Expiry Date */}
              <div className="flex flex-col sm:flex-row items-center gap-2 bg-surface-container-lowest p-3 rounded-xl border border-surface-container">
                <input
                  type="text"
                  value={pantryInputText}
                  onChange={(e) => setPantryInputText(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleAddManual()}
                  placeholder="Ingredient name (e.g., Paneer, Curd, Brown Bread)..."
                  className="flex-1 px-3 py-2 bg-surface-container-low border border-surface-container rounded-lg text-body-sm focus:outline-none focus:ring-1 focus:ring-primary"
                />
                <input
                  type="date"
                  value={pantryInputExpiry}
                  onChange={(e) => setPantryInputExpiry(e.target.value)}
                  className="px-3 py-2 bg-surface-container-low border border-surface-container rounded-lg text-body-sm text-on-surface-variant focus:outline-none focus:ring-1 focus:ring-primary"
                  title="Expiry Date"
                />
                <button
                  type="button"
                  onClick={handleAddManual}
                  className="w-full sm:w-auto px-4 py-2 bg-primary hover:bg-primary-container text-on-primary rounded-lg font-label-md text-label-md shrink-0"
                >
                  Add Item
                </button>
              </div>
            </div>

            {/* Diagnostic Monitor / Preview (5 cols) */}
            <div className="lg:col-span-5 bg-surface-container-lowest p-space-lg rounded-xl shadow-sm border border-surface-container flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between pb-space-xs border-b border-surface-container">
                  <div className="flex items-center gap-2">
                    <span className="w-2.5 h-2.5 rounded-full bg-secondary" />
                    <span className="font-headline-sm text-headline-sm text-primary font-serif">
                      OCR Engine &amp; DB Alignment
                    </span>
                  </div>
                  <span className="font-label-sm text-label-sm text-on-surface-variant font-mono">
                    SQLite Verified
                  </span>
                </div>

                <p className="font-body-sm text-body-sm text-on-surface-variant mt-2">
                  Extracted lines are fuzzy-matched against USDA &amp; ICMR-NIN food composition tables.
                  Items below 85% confidence are flagged for manual user correction.
                </p>

                <div className="mt-space-md relative overflow-hidden rounded-lg bg-surface-container-high h-44 flex items-center justify-center border border-surface-container">
                  <div className="relative w-full h-full">
                    <Image
                      src={previewUrl || "/stitch/assets/stitch_asset_09.png"}
                      alt="Pantry scan preview"
                      fill
                      className="object-cover"
                    />
                  </div>
                  <div className="absolute inset-0 bg-primary/20 backdrop-blur-[1px] flex flex-col justify-between p-3 pointer-events-none">
                    <div className="flex justify-between items-start">
                      <span className="bg-surface-container-lowest/90 px-2 py-0.5 rounded font-label-sm text-label-sm text-primary font-bold shadow-sm">
                        OCR Confidence Gated
                      </span>
                      <span className="bg-secondary-container text-on-secondary-container px-2 py-0.5 rounded font-label-sm text-label-sm font-bold shadow-sm">
                        {detectedItems.length} Staged
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Staged Ingestion Queue Table with Inline Corrections */}
          {detectedItems.length > 0 && (
            <div className="bg-surface-container-lowest p-space-lg rounded-xl shadow-sm border border-surface-container space-y-space-md animate-in fade-in">
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-space-sm pb-space-xs border-b border-surface-container">
                <div>
                  <div className="flex items-center gap-space-xs flex-wrap">
                    <span className="material-symbols-outlined text-[20px] text-primary">edit_note</span>
                    <h2 className="font-headline-sm text-headline-sm text-primary font-serif">
                      Review &amp; Correct Staged Ingredients
                    </h2>
                    <span className="px-2 py-0.5 rounded-full bg-primary/10 text-primary font-label-sm text-label-sm font-bold">
                      {detectedItems.length} Extracted
                    </span>
                    {detectedItems.some((i) => i.needs_review) && (
                      <span className="px-2 py-0.5 rounded-full bg-amber-50 text-amber-700 border border-amber-200 font-label-sm text-label-sm font-bold flex items-center gap-1">
                        ⚠️ Low Confidence Items Require Review
                      </span>
                    )}
                  </div>
                  <p className="font-body-sm text-body-sm text-on-surface-variant mt-0.5">
                    Edit names, quantities, and expiry dates directly before adding to your active inventory.
                  </p>
                </div>

                <div className="flex items-center gap-space-sm">
                  <button
                    type="button"
                    onClick={() => setDetectedItems([])}
                    className="px-space-md py-2 bg-surface-container hover:bg-surface-container-high text-on-surface-variant rounded font-label-sm text-label-sm"
                  >
                    Clear Queue
                  </button>
                  <button
                    type="button"
                    onClick={commitAllStaged}
                    className="flex items-center gap-space-xs px-space-lg py-2 bg-primary hover:bg-primary-container text-on-primary rounded font-label-sm text-label-sm shadow-md"
                  >
                    <span className="material-symbols-outlined text-[18px]">add_circle</span>
                    Confirm &amp; Add All to Pantry
                  </button>
                </div>
              </div>

              {/* Editable Staging Table */}
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="bg-surface-container-low text-on-surface-variant font-label-sm text-label-sm uppercase tracking-wider border-b border-surface-container">
                      <th className="py-3 px-3 font-semibold">Ingredient Name</th>
                      <th className="py-3 px-3 font-semibold">Category</th>
                      <th className="py-3 px-3 font-semibold">Quantity</th>
                      <th className="py-3 px-3 font-semibold">Expiry Date</th>
                      <th className="py-3 px-3 font-semibold">Database Match / Review</th>
                      <th className="py-3 px-3 font-semibold text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-surface-container font-body-sm text-body-sm text-on-surface">
                    {detectedItems.map((staged, idx) => (
                      <tr key={idx} className="hover:bg-surface-container-low/50">
                        <td className="py-2.5 px-3">
                          <input
                            type="text"
                            value={staged.name}
                            onChange={(e) => updateStagedItem(idx, "name", e.target.value)}
                            className="w-full px-2 py-1 bg-surface-container-lowest border border-surface-container rounded text-body-sm font-medium focus:ring-1 focus:ring-primary"
                          />
                        </td>
                        <td className="py-2.5 px-3">
                          <select
                            value={staged.category}
                            onChange={(e) => updateStagedItem(idx, "category", e.target.value)}
                            className="px-2 py-1 bg-surface-container-lowest border border-surface-container rounded text-body-sm text-on-surface-variant"
                          >
                            <option value="Dairy & Protein">Dairy &amp; Protein</option>
                            <option value="Grains & Pulses">Grains &amp; Pulses</option>
                            <option value="Produce">Produce</option>
                            <option value="Pantry Staples">Pantry Staples</option>
                            <option value="General">General</option>
                          </select>
                        </td>
                        <td className="py-2.5 px-3">
                          <input
                            type="text"
                            value={staged.quantity}
                            onChange={(e) => updateStagedItem(idx, "quantity", e.target.value)}
                            className="w-24 px-2 py-1 bg-surface-container-lowest border border-surface-container rounded text-body-sm font-semibold text-primary"
                          />
                        </td>
                        <td className="py-2.5 px-3">
                          <input
                            type="date"
                            value={staged.expiry_date || ""}
                            onChange={(e) => updateStagedItem(idx, "expiry_date", e.target.value)}
                            className="px-2 py-1 bg-surface-container-lowest border border-surface-container rounded text-body-sm text-on-surface-variant"
                          />
                        </td>
                        <td className="py-2.5 px-3">
                          {staged.needs_review ? (
                            <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-50 text-amber-700 border border-amber-200">
                              ⚠️ Check Confidence ({Math.round((staged.confidence || 0.7) * 100)}%)
                            </span>
                          ) : staged.matched_food ? (
                            <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                              ✓ {staged.matched_food.name} ({Math.round(staged.matched_food.calories_kcal || 0)} kcal)
                            </span>
                          ) : (
                            <span className="px-2 py-0.5 rounded-full text-[10px] bg-slate-50 text-slate-500 border border-slate-200">
                              Manual Match
                            </span>
                          )}
                        </td>
                        <td className="py-2.5 px-3 text-right">
                          <button
                            type="button"
                            onClick={() => removeStagedItem(idx)}
                            className="text-rose-600 hover:text-rose-800 text-xs font-semibold"
                          >
                            Remove
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Live Pantry Inventory Manager (Grid Cards with Freshness Indicators) */}
          <div className="bg-surface-container-lowest p-space-lg rounded-xl shadow-sm border border-surface-container space-y-space-md">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-space-xs border-b border-surface-container">
              <div>
                <h2 className="font-headline-sm text-headline-sm text-primary font-serif">
                  Live Pantry Inventory Ledger ({pantryItems.length} items)
                </h2>
                <p className="font-body-sm text-body-sm text-on-surface-variant">
                  Toggle items in/out of stock. Freshness indicators alert you before items expire.
                </p>
              </div>
              <div className="flex items-center gap-2 flex-wrap self-start sm:self-auto">
                <button
                  type="button"
                  id="clear-pantry-btn"
                  onClick={() => {
                    setClearError(null);
                    setIsClearModalOpen(true);
                  }}
                  className="px-space-md py-2 border border-red-200 bg-red-50 hover:bg-red-100 text-red-700 dark:border-red-800 dark:bg-red-950/40 dark:text-red-300 rounded font-label-md text-label-md transition-all flex items-center gap-1.5 shadow-sm"
                  title="Clear all items from your pantry"
                >
                  <span className="material-symbols-outlined text-[18px]">delete_sweep</span>
                  Clear Pantry
                </button>
                {onApplyToMealPlan && (
                  <button
                    type="button"
                    onClick={onApplyToMealPlan}
                    className="px-space-md py-2 bg-secondary text-on-secondary rounded font-label-md text-label-md hover:bg-secondary/90 transition-all flex items-center gap-1.5 shadow-sm"
                  >
                    <span className="material-symbols-outlined text-[18px]">sync</span>
                    Apply to Meal Plan
                  </button>
                )}
              </div>
            </div>

            {pantryItems.length === 0 ? (
              <div className="text-center py-12 px-4 bg-surface-container-low/50 rounded-xl border border-dashed border-outline-variant/60">
                <span className="material-symbols-outlined text-[42px] text-on-surface-variant/40 block mb-2">
                  inventory_2
                </span>
                <p className="font-label-lg text-label-lg font-bold text-on-surface">
                  Your pantry is empty
                </p>
                <p className="font-body-sm text-body-sm text-on-surface-variant max-w-sm mx-auto mt-1">
                  Add items using the quick adder above or scan a grocery receipt/fridge photo to populate your inventory.
                </p>
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-space-sm">
                {pantryItems.map((item) => (
                  <div
                    key={item.id}
                    className={`p-3 rounded-xl border transition-all flex flex-col justify-between gap-2 ${
                      item.inStock
                        ? "bg-surface-container-low border-surface-container text-on-surface"
                        : "bg-surface-container-lowest border-dashed border-outline-variant text-on-surface-variant opacity-60"
                    }`}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <h4 className="font-label-lg text-label-lg font-bold">{item.name}</h4>
                        <span className="text-[11px] font-label-sm text-on-surface-variant block">
                          {item.category} • {item.quantity}
                        </span>
                      </div>

                      <button
                        type="button"
                        onClick={() => togglePantryItem(item.id)}
                        className={`p-1.5 rounded-full transition-colors shrink-0 ${
                          item.inStock
                            ? "bg-secondary/15 text-secondary hover:bg-secondary/25"
                            : "bg-surface-container text-on-surface-variant hover:bg-surface-container-high"
                        }`}
                      >
                        <span className="material-symbols-outlined text-[18px]">
                          {item.inStock ? "check" : "add"}
                        </span>
                      </button>
                    </div>

                    <div className="pt-2 border-t border-surface-container/60 flex items-center justify-between">
                      {renderFreshnessBadge(item)}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB 2: Missing Ingredients Shopping List */}
      {activeSubTab === "shopping_list" && (
        <div className="bg-surface-container-lowest p-space-lg rounded-xl shadow-sm border border-surface-container space-y-space-md">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-space-xs border-b border-surface-container">
            <div>
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-primary text-[22px]">shopping_bag</span>
                <h2 className="font-headline-sm text-headline-sm text-primary font-serif">
                  Automated Grocery Shopping List
                </h2>
              </div>
              <p className="font-body-sm text-body-sm text-on-surface-variant mt-1">
                Comparing required meal plan ingredients with your in-stock pantry items.
              </p>
            </div>
            <button
              onClick={fetchShoppingList}
              className="px-3 py-1.5 rounded-lg border border-surface-container text-xs font-semibold text-primary hover:bg-surface-container flex items-center gap-1 self-start sm:self-auto"
            >
              <span className="material-symbols-outlined text-[16px]">refresh</span>
              Recalculate
            </button>
          </div>

          {loadingShoppingList ? (
            <div className="py-8 text-center text-xs text-on-surface-variant">Computing missing ingredients...</div>
          ) : shoppingList ? (
            <div className="space-y-4">
              {/* Coverage summary card */}
              <div className="grid grid-cols-3 gap-3">
                <div className="p-3 bg-surface-container-low rounded-xl text-center border border-surface-container">
                  <span className="text-[11px] text-on-surface-variant block uppercase">Pantry Match</span>
                  <span className="text-xl font-bold text-primary">{shoppingList.pantry_match_pct}%</span>
                </div>
                <div className="p-3 bg-surface-container-low rounded-xl text-center border border-surface-container">
                  <span className="text-[11px] text-on-surface-variant block uppercase">Available at Home</span>
                  <span className="text-xl font-bold text-emerald-600">{shoppingList.in_pantry_count}</span>
                </div>
                <div className="p-3 bg-surface-container-low rounded-xl text-center border border-surface-container">
                  <span className="text-[11px] text-on-surface-variant block uppercase">Need to Buy</span>
                  <span className="text-xl font-bold text-rose-600">{shoppingList.missing_count}</span>
                </div>
              </div>

              {/* Missing items list */}
              {shoppingList.missing_items.length > 0 ? (
                <div className="space-y-2">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-on-surface-variant">
                    Items to Buy ({shoppingList.missing_items.length})
                  </h4>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    {shoppingList.missing_items.map((item, idx) => (
                      <div
                        key={idx}
                        className="p-3 rounded-lg border border-rose-200 bg-rose-50/40 flex items-center justify-between"
                      >
                        <div>
                          <span className="font-semibold text-sm text-on-surface block">{item.name}</span>
                          <span className="text-[11px] text-on-surface-variant">
                            For {item.recipe} • {item.category}
                          </span>
                        </div>
                        <button
                          onClick={() => {
                            onAddManualItem(item.name);
                            fetchShoppingList();
                          }}
                          className="px-2.5 py-1 bg-surface-container-lowest border border-rose-200 text-rose-700 rounded text-xs font-semibold hover:bg-rose-100"
                        >
                          Mark Bought
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="py-6 text-center text-emerald-700 bg-emerald-50 rounded-xl border border-emerald-200">
                  <span className="text-2xl">🎉</span>
                  <p className="text-sm font-semibold mt-1">Pantry is 100% stocked!</p>
                  <p className="text-xs text-emerald-600 mt-0.5">All ingredients for planned recipes are available.</p>
                </div>
              )}
            </div>
          ) : null}
        </div>
      )}

      {/* TAB 3: Pantry Recipe Match */}
      {activeSubTab === "cook_now" && (
        <div className="bg-surface-container-lowest p-space-lg rounded-xl shadow-sm border border-surface-container space-y-space-md">
          <div className="flex items-center justify-between pb-space-xs border-b border-surface-container">
            <div>
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-primary text-[22px]">auto_fix_high</span>
                <h2 className="font-headline-sm text-headline-sm text-primary font-serif">
                  What You Can Cook Right Now
                </h2>
              </div>
              <p className="font-body-sm text-body-sm text-on-surface-variant mt-1">
                Recipes ranked by your available pantry ingredients to minimize waste.
              </p>
            </div>
            <button
              onClick={fetchPantryRecipes}
              className="px-3 py-1.5 rounded-lg border border-surface-container text-xs font-semibold text-primary hover:bg-surface-container flex items-center gap-1"
            >
              <span className="material-symbols-outlined text-[16px]">refresh</span>
              Refresh
            </button>
          </div>

          {loadingRecipes ? (
            <div className="py-8 text-center text-xs text-on-surface-variant">Matching pantry against recipes...</div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {pantryRecipes.map((recipe) => (
                <div
                  key={recipe.id}
                  className={`p-4 rounded-xl border transition-all ${
                    recipe.can_cook_now
                      ? "bg-emerald-50/40 border-emerald-300 shadow-sm"
                      : "bg-surface-container-low border-surface-container"
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <div className="flex items-center gap-2">
                        <h4 className="font-headline-sm text-base font-serif text-primary">{recipe.name}</h4>
                        {recipe.can_cook_now && (
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-600 text-white">
                            Cook Now
                          </span>
                        )}
                      </div>
                      <span className="text-[11px] text-on-surface-variant">{recipe.category}</span>
                    </div>
                    <span
                      className={`text-sm font-bold px-2 py-0.5 rounded-full border ${
                        recipe.coverage_pct >= 90
                          ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                          : "bg-amber-50 text-amber-700 border-amber-200"
                      }`}
                    >
                      {Math.round(recipe.coverage_pct)}% Match
                    </span>
                  </div>

                  <div className="mt-3 text-xs space-y-1">
                    <div className="flex flex-wrap gap-1">
                      <span className="text-on-surface-variant font-medium">Have:</span>
                      {recipe.matched_ingredients.map((ing) => (
                        <span key={ing} className="px-1.5 py-0.5 bg-emerald-100/70 text-emerald-800 rounded text-[11px]">
                          ✓ {ing}
                        </span>
                      ))}
                    </div>
                    {recipe.missing_ingredients.length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-1">
                        <span className="text-on-surface-variant font-medium">Missing:</span>
                        {recipe.missing_ingredients.map((ing) => (
                          <span key={ing} className="px-1.5 py-0.5 bg-rose-100/70 text-rose-800 rounded text-[11px]">
                            ✗ {ing}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>

                  <p className="mt-3 text-xs text-on-surface-variant line-clamp-2 italic border-t border-surface-container/60 pt-2">
                    {recipe.instructions}
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ─── Clear Pantry Confirmation Modal ────────────────────────────────────── */}
      {isClearModalOpen && (
        <div
          role="dialog"
          aria-modal="true"
          aria-labelledby="clear-pantry-title"
          className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm flex items-center justify-center p-space-md animate-in fade-in"
        >
          <div className="bg-[#FFFFFF] dark:bg-[#142D4E] text-on-surface max-w-md w-full rounded-2xl p-space-lg shadow-2xl border border-surface-container space-y-space-md animate-in zoom-in-95 duration-150">
            <div className="flex items-start gap-3">
              <div className="w-12 h-12 rounded-full bg-red-100 dark:bg-red-950/60 text-red-600 dark:text-red-400 flex items-center justify-center shrink-0">
                <span className="material-symbols-outlined text-[28px]">warning</span>
              </div>
              <div className="space-y-1">
                <h3 id="clear-pantry-title" className="font-headline-sm text-headline-sm font-bold text-[#142D4E] dark:text-[#FFFFFF] font-serif">
                  Clear Pantry
                </h3>
                <p className="font-body-md text-body-md text-on-surface font-semibold text-red-600 dark:text-red-400">
                  Are you sure you want to clear all items from your pantry?
                </p>
              </div>
            </div>

            <div className="p-3 bg-surface-container-low rounded-xl border border-surface-container text-body-sm text-on-surface-variant">
              <p className="text-xs text-on-surface-variant leading-relaxed">
                This will permanently remove all <strong className="text-on-surface">{pantryItems.length} item{pantryItems.length === 1 ? "" : "s"}</strong> from your inventory. Your food catalog, saved meal plans, and nutritional history will remain safe.
              </p>
            </div>

            {clearError && (
              <div className="p-2.5 rounded-lg bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-900/50 text-red-700 dark:text-red-300 text-xs">
                {clearError}
              </div>
            )}

            <div className="flex items-center justify-end gap-3 pt-2 border-t border-surface-container/60">
              <button
                type="button"
                id="cancel-clear-pantry-btn"
                onClick={() => {
                  if (!isClearing) {
                    setIsClearModalOpen(false);
                    setClearError(null);
                  }
                }}
                disabled={isClearing}
                className="px-4 py-2 rounded-lg border border-surface-container text-body-sm font-medium text-on-surface hover:bg-surface-container transition-colors disabled:opacity-50"
              >
                Cancel
              </button>

              <button
                type="button"
                id="confirm-clear-pantry-btn"
                onClick={handleConfirmClear}
                disabled={isClearing}
                className="px-4 py-2 rounded-lg bg-red-600 hover:bg-red-700 text-[#FFFFFF] text-body-sm font-semibold transition-colors flex items-center gap-2 shadow-sm disabled:opacity-50"
              >
                {isClearing ? (
                  <>
                    <span className="material-symbols-outlined animate-spin text-[18px]">progress_activity</span>
                    <span>Clearing Pantry...</span>
                  </>
                ) : (
                  <>
                    <span className="material-symbols-outlined text-[18px]">delete_sweep</span>
                    <span>Clear Pantry</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ─── Clear Pantry Success Notification ─────────────────────────────────── */}
      {clearSuccessToast && (
        <div
          role="status"
          aria-live="polite"
          className="fixed top-20 right-6 z-50 bg-[#FFFFFF] dark:bg-[#142D4E] p-4 rounded-xl shadow-xl border-2 border-[#16A66A] text-body-sm animate-in slide-in-from-top-4 flex items-center gap-3 max-w-sm"
        >
          <span className="w-8 h-8 rounded-full bg-[#DDF5E8] flex items-center justify-center text-[#16A66A] shrink-0">
            <span className="material-symbols-outlined text-[20px]">check_circle</span>
          </span>
          <div className="flex-1">
            <h5 className="font-label-md text-label-md text-[#142D4E] dark:text-[#FFFFFF] font-bold">
              Pantry Cleared
            </h5>
            <p className="text-body-sm text-on-surface-variant">
              {clearSuccessToast}
            </p>
          </div>
          <button
            type="button"
            onClick={() => setClearSuccessToast(null)}
            className="text-on-surface-variant hover:text-on-surface p-1"
            aria-label="Dismiss notification"
          >
            <span className="material-symbols-outlined text-[18px]">close</span>
          </button>
        </div>
      )}
    </div>
  );
};
