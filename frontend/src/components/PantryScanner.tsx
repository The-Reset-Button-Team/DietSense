"use client";

import React, { useState, useRef } from "react";
import { PantryItem } from "@/types";
import { apiClient } from "@/lib/api-client";

export interface DetectedItem {
  name: string;
  category: string;
  quantity: string;
  confidence?: number;
  selected?: boolean;
}

interface PantryScannerProps {
  pantryItems: PantryItem[];
  togglePantryItem: (id: string) => void;
  onAddManualItem: (name: string) => void;
  onAddBatchItems?: (items: Array<{ name: string; category?: string; quantity?: string }>) => void;
}

export const PantryScanner: React.FC<PantryScannerProps> = ({
  pantryItems,
  togglePantryItem,
  onAddManualItem,
  onAddBatchItems,
}) => {
  const [pantryInputText, setPantryInputText] = useState<string>("");
  const [isScanning, setIsScanning] = useState<boolean>(false);
  const [scanMessage, setScanMessage] = useState<string>("");
  const [errorMessage, setErrorMessage] = useState<string>("");
  const [scanMode, setScanMode] = useState<"auto" | "bill" | "fridge">("auto");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [detectedItems, setDetectedItems] = useState<DetectedItem[]>([]);
  const [isDragging, setIsDragging] = useState<boolean>(false);

  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const handleAdd = () => {
    if (!pantryInputText.trim()) return;
    onAddManualItem(pantryInputText.trim());
    setPantryInputText("");
  };

  // Handle file selection from input
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      processSelectedFile(file);
    }
  };

  const processSelectedFile = (file: File) => {
    setSelectedFile(file);
    setErrorMessage("");
    setScanMessage("");
    setDetectedItems([]);

    if (file.type.startsWith("image/")) {
      const url = URL.createObjectURL(file);
      setPreviewUrl(url);
    } else {
      setPreviewUrl(null);
    }
  };

  // Drag and drop handlers
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (file) {
      processSelectedFile(file);
    }
  };

  // Upload and process the selected file via local backend API
  const handleUploadAndScan = async () => {
    if (!selectedFile) {
      setErrorMessage("Please select an image or PDF bill first.");
      return;
    }

    setIsScanning(true);
    setErrorMessage("");
    setScanMessage("Uploading & analyzing file with local vision/receipt processor...");

    try {
      const formData = new FormData();
      formData.append("file", selectedFile);
      formData.append("scan_type", scanMode);

      const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
      const response = await fetch(`${API_BASE}/api/pantry/scan`, {
        method: "POST",
        body: formData,
        credentials: "include",
      });

      if (!response.ok) {
        let err = response.statusText;
        try {
          const json = await response.json();
          if (json.detail) err = json.detail;
        } catch {}
        throw new Error(err);
      }

      const data = await response.json();
      const items: DetectedItem[] = (data.detected_items || []).map((i: any) => ({
        ...i,
        selected: true,
      }));

      setDetectedItems(items);
      setScanMessage(data.summary || `✓ Successfully extracted ${items.length} items from ${selectedFile.name}!`);
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to process image. Falling back to local catalog parsing.");
    } finally {
      setIsScanning(false);
    }
  };

  // Instant sample presets
  const handlePresetScan = async (presetType: "blinkit" | "fridge") => {
    setIsScanning(true);
    setErrorMessage("");
    setSelectedFile(null);
    const sampleImg =
      presetType === "blinkit"
        ? "/samples/blinkit_sample_bill.png"
        : "/samples/fridge_sample_snapshot.png";
    setPreviewUrl(sampleImg);
    setScanMessage(`Analyzing sample ${presetType === "blinkit" ? "Blinkit bill" : "fridge photo"}...`);

    try {
      const data = await apiClient<any>(`/api/pantry/scan-sample?preset=${presetType}`);
      const items: DetectedItem[] = (data.detected_items || []).map((i: any) => ({
        ...i,
        selected: true,
      }));
      setDetectedItems(items);
      setScanMessage(data.summary);
    } catch {
      // Local fallback if backend is offline
      if (presetType === "blinkit") {
        setDetectedItems([
          { name: "Mother Dairy Paneer", category: "Dairy & Protein", quantity: "200g", confidence: 0.98, selected: true },
          { name: "Fresh Palak", category: "Fresh Veggies", quantity: "250g", confidence: 0.96, selected: true },
          { name: "Nestle Slim Dahi", category: "Dairy & Protein", quantity: "400g", confidence: 0.95, selected: true },
          { name: "Whole Wheat Bread", category: "Bakery & Essentials", quantity: "400g", confidence: 0.94, selected: true },
          { name: "Amul Taaza Milk", category: "Dairy & Protein", quantity: "1 L", confidence: 0.97, selected: true },
        ]);
        setScanMessage("✓ Blinkit Bill Extracted! 5 fresh items detected with units & quantities.");
      } else {
        setDetectedItems([
          { name: "Fresh Paneer", category: "Dairy & Protein", quantity: "250g", confidence: 0.94, selected: true },
          { name: "Curd / Dahi", category: "Dairy & Protein", quantity: "1 tub", confidence: 0.96, selected: true },
          { name: "Palak (Spinach Leaves)", category: "Fresh Veggies", quantity: "1 bunch", confidence: 0.91, selected: true },
          { name: "Tomatoes", category: "Fresh Veggies", quantity: "500g", confidence: 0.90, selected: true },
          { name: "Amul Milk Carton", category: "Dairy & Protein", quantity: "500 ml", confidence: 0.95, selected: true },
        ]);
        setScanMessage("✓ Fridge Snapshot Analyzed! Paneer, Palak & Dahi detected.");
      }
    } finally {
      setIsScanning(false);
    }
  };

  // Load sample image into the dropzone as a File so user can test the upload API
  const handleLoadSampleFile = async (presetType: "blinkit" | "fridge") => {
    setIsScanning(true);
    setErrorMessage("");
    setScanMessage("");
    setDetectedItems([]);

    const sampleUrl =
      presetType === "blinkit"
        ? "/samples/blinkit_sample_bill.png"
        : "/samples/fridge_sample_snapshot.png";
    const sampleName =
      presetType === "blinkit" ? "blinkit_sample_bill.png" : "fridge_sample_snapshot.png";

    try {
      const res = await fetch(sampleUrl);
      const blob = await res.blob();
      const file = new File([blob], sampleName, { type: "image/png" });
      processSelectedFile(file);
      setScanMode(presetType === "blinkit" ? "bill" : "fridge");
      setScanMessage(
        `Loaded ${presetType === "blinkit" ? "Blinkit bill" : "fridge snapshot"} sample file! Click "Process Selected File" to scan.`
      );
    } catch {
      setErrorMessage("Could not load sample image file. You can still use the direct scan button below.");
    } finally {
      setIsScanning(false);
    }
  };

  // Toggle item selection in detected preview
  const toggleItemSelection = (index: number) => {
    setDetectedItems((prev) =>
      prev.map((item, idx) => (idx === index ? { ...item, selected: !item.selected } : item))
    );
  };

  // Commit selected items into the pantry
  const handleAddSelectedToPantry = async () => {
    const selected = detectedItems.filter((i) => i.selected);
    if (selected.length === 0) return;

    if (onAddBatchItems) {
      onAddBatchItems(selected);
    } else {
      selected.forEach((item) => onAddManualItem(item.name));
    }

    // Persist to local backend if available
    try {
      await apiClient("/api/pantry", {
        method: "POST",
        body: JSON.stringify({ items: selected }),
      });
    } catch {}

    setScanMessage(`🎉 Added ${selected.length} items directly to your active pantry!`);
    setDetectedItems([]);
    setSelectedFile(null);
    setPreviewUrl(null);
  };

  const inStockCount = pantryItems.filter((i) => i.inStock).length;

  return (
    <div className="relative z-10 space-y-4">
      {/* Hidden File Input */}
      <input
        ref={fileInputRef}
        type="file"
        accept="image/png,image/jpeg,image/jpg,image/webp,application/pdf"
        onChange={handleFileChange}
        className="hidden"
      />

      {/* Image / Bill Upload Section */}
      <div className="rounded-2xl bg-white p-5 border border-[#e8ded3] shadow-sm space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-3">
          <div>
            <h3 className="text-base font-serif text-[#421018] font-semibold flex items-center gap-2">
              <span>📸</span> Grocery Bill &amp; Fridge Image Scanner
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Upload grocery bill photo ya fridge snapshot — AI items extract karke direct pantry me add karega!
            </p>
          </div>
          <span className="text-xs bg-emerald-50 text-emerald-800 px-2.5 py-1 rounded-full border border-emerald-200 font-semibold self-start sm:self-auto">
            Pantry-to-Plate AI
          </span>
        </div>

        {/* Upload Box / Scanner Dropzone */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            className={`md:col-span-2 p-5 border-2 border-dashed rounded-2xl flex flex-col items-center justify-center text-center space-y-3 transition-all ${
              isDragging
                ? "border-[#581825] bg-[#fdf2f4]"
                : "border-[#d8c8b8] bg-[#faf7f2] hover:border-[#bda897]"
            }`}
          >
            {previewUrl ? (
              <div className="relative w-32 h-32 rounded-xl overflow-hidden border border-[#d8c8b8] shadow-sm bg-black/5 mb-1">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={previewUrl}
                  alt="Upload Preview"
                  className="w-full h-full object-cover"
                />
                <button
                  onClick={() => {
                    setSelectedFile(null);
                    setPreviewUrl(null);
                  }}
                  className="absolute top-1 right-1 w-6 h-6 rounded-full bg-black/60 text-white text-xs flex items-center justify-center hover:bg-black/80"
                >
                  ✕
                </button>
              </div>
            ) : (
              <div
                onClick={() => fileInputRef.current?.click()}
                className="w-14 h-14 rounded-2xl bg-white border border-[#e2d6c9] flex items-center justify-center text-2xl shadow-sm cursor-pointer hover:scale-105 transition-all"
              >
                📷
              </div>
            )}

            <div>
              <h4 className="text-xs font-bold text-[#421018]">
                {selectedFile ? selectedFile.name : "Upload Grocery Receipt or Fridge Image"}
              </h4>
              <p className="text-[11px] text-slate-500 mt-0.5">
                {selectedFile
                  ? `${(selectedFile.size / 1024).toFixed(1)} KB · Ready to scan`
                  : "Supports PNG, JPG, Zepto/Blinkit PDF bills & camera snapshots"}
              </p>
            </div>

            {/* Mode Selector and File Upload Triggers */}
            <div className="flex gap-2 flex-wrap justify-center items-center pt-1">
              <button
                onClick={() => fileInputRef.current?.click()}
                className="px-3 py-1.5 rounded-xl bg-white border border-[#d8c8b8] hover:bg-slate-50 text-slate-700 text-xs font-medium shadow-sm transition-all flex items-center gap-1.5"
              >
                <span>📁</span> {selectedFile ? "Choose Different File" : "Choose File"}
              </button>

              {selectedFile && (
                <button
                  onClick={handleUploadAndScan}
                  disabled={isScanning}
                  className="px-3.5 py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold shadow-sm transition-all flex items-center gap-1.5"
                >
                  <span>✨</span> {isScanning ? "Processing..." : "Process Selected File"}
                </button>
              )}
            </div>

            {/* Sample Preset Buttons from the reference mockup */}
            <div className="flex flex-col items-center gap-2 pt-2 border-t border-slate-200/60 w-full max-w-md">
              <div className="flex items-center gap-1.5 text-[11px] text-slate-500 font-medium">
                <span>🧪 Test with Sample Images:</span>
              </div>
              <div className="flex gap-2 flex-wrap justify-center w-full">
                <button
                  onClick={() => handlePresetScan("blinkit")}
                  disabled={isScanning}
                  className="px-3 py-1.5 rounded-xl bg-[#581825] hover:bg-[#722230] text-white text-xs font-medium shadow-sm transition-all flex items-center gap-1"
                >
                  <span>⚡</span> Scan Blinkit Bill
                </button>
                <button
                  onClick={() => handlePresetScan("fridge")}
                  disabled={isScanning}
                  className="px-3 py-1.5 rounded-xl bg-white border border-[#d8c8b8] hover:bg-slate-50 text-slate-700 text-xs font-medium shadow-sm transition-all flex items-center gap-1"
                >
                  <span>📸</span> Scan Fridge Photo
                </button>
                <button
                  onClick={() => handleLoadSampleFile("blinkit")}
                  disabled={isScanning}
                  className="px-2.5 py-1.5 rounded-xl bg-amber-50 border border-amber-200 hover:bg-amber-100 text-amber-800 text-[11px] font-medium shadow-sm transition-all flex items-center gap-1"
                  title="Loads the sample Blinkit bill image into the dropzone to test upload"
                >
                  <span>📄</span> Load Bill File
                </button>
                <button
                  onClick={() => handleLoadSampleFile("fridge")}
                  disabled={isScanning}
                  className="px-2.5 py-1.5 rounded-xl bg-sky-50 border border-sky-200 hover:bg-sky-100 text-sky-800 text-[11px] font-medium shadow-sm transition-all flex items-center gap-1"
                  title="Loads the sample fridge snapshot into the dropzone to test upload"
                >
                  <span>🧊</span> Load Fridge File
                </button>
              </div>
            </div>

            {/* Status Messages */}
            {scanMessage && (
              <div className="p-2.5 px-3.5 rounded-xl bg-emerald-50 border border-emerald-200 text-xs text-emerald-800 font-medium mt-2 animate-fadeIn flex items-center gap-2">
                <span>✓</span>
                <span>{scanMessage}</span>
              </div>
            )}

            {errorMessage && (
              <div className="p-2.5 px-3.5 rounded-xl bg-red-50 border border-red-200 text-xs text-red-700 font-medium mt-2 animate-fadeIn flex items-center gap-2">
                <span>✕</span>
                <span>{errorMessage}</span>
              </div>
            )}
          </div>

          {/* Quick Manual Add Item */}
          <div className="p-4 rounded-2xl bg-[#eff6ff] border border-[#bfdbfe] flex flex-col justify-between space-y-3">
            <div>
              <h4 className="text-xs font-bold text-[#1d4ed8]">Quick Add Single Item</h4>
              <p className="text-[11px] text-slate-600 mt-0.5">Kuch extra khareeda? Direct add karo.</p>
            </div>

            <div className="space-y-2">
              <input
                type="text"
                placeholder="e.g. Tofu 200g, Dahi, Brown Bread"
                value={pantryInputText}
                onChange={(e) => setPantryInputText(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleAdd()}
                className="w-full bg-white border border-[#bfdbfe] rounded-xl px-3 py-2 text-xs text-slate-800 focus:outline-none"
              />
              <button
                onClick={handleAdd}
                className="w-full py-2 rounded-xl bg-[#1d4ed8] hover:bg-[#1e40af] text-white text-xs font-semibold shadow-sm transition-all"
              >
                + Add to My Pantry
              </button>
            </div>
          </div>
        </div>

        {/* Extracted Items Review & Confirmation Drawer */}
        {detectedItems.length > 0 && (
          <div className="p-4 rounded-2xl bg-[#faf7f2] border border-[#e2d6c9] mt-3 space-y-3 animate-fadeIn">
            <div className="flex items-center justify-between flex-wrap gap-2">
              <div>
                <h4 className="text-xs font-bold text-[#421018] flex items-center gap-1.5">
                  <span>🥗</span> Extracted Items Review ({detectedItems.filter((i) => i.selected).length} selected)
                </h4>
                <p className="text-[11px] text-slate-600">
                  Select which items you want to add to your in-stock pantry:
                </p>
              </div>

              <button
                onClick={handleAddSelectedToPantry}
                className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold shadow-sm transition-all flex items-center gap-1.5"
              >
                <span>✓</span> Add Selected ({detectedItems.filter((i) => i.selected).length}) to Pantry
              </button>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2 pt-1">
              {detectedItems.map((item, idx) => (
                <div
                  key={idx}
                  onClick={() => toggleItemSelection(idx)}
                  className={`p-2.5 rounded-xl border flex items-center justify-between cursor-pointer transition-all ${
                    item.selected
                      ? "bg-white border-emerald-400 shadow-xs"
                      : "bg-slate-50/80 border-slate-200 opacity-60"
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={item.selected}
                      onChange={() => {}}
                      className="w-4 h-4 accent-emerald-600 rounded cursor-pointer"
                    />
                    <div>
                      <p className="text-xs font-bold text-slate-800">{item.name}</p>
                      <p className="text-[10px] text-slate-500">
                        {item.category} · {item.quantity}
                      </p>
                    </div>
                  </div>
                  {item.confidence && (
                    <span className="text-[9px] bg-emerald-50 text-emerald-700 font-semibold px-1.5 py-0.5 rounded border border-emerald-200">
                      {Math.round(item.confidence * 100)}% match
                    </span>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Current Pantry Stock List */}
      <div className="rounded-2xl bg-white p-5 border border-[#e8ded3] shadow-sm space-y-3">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-base font-serif text-[#421018] font-semibold">
              My Pantry / Kitchen Stock ({inStockCount} In Stock)
            </h3>
            <p className="text-xs text-slate-500">
              Uncheck jo khatam ho gaya hai — recommendations automatically update honge.
            </p>
          </div>
          <span className="text-xs text-slate-600 font-medium">
            {inStockCount} / {pantryItems.length} Available
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2.5 pt-2">
          {pantryItems.map((item) => (
            <div
              key={item.id}
              onClick={() => togglePantryItem(item.id)}
              className={`p-3 rounded-xl border flex items-center justify-between cursor-pointer transition-all ${
                item.inStock
                  ? "bg-[#faf7f2] border-[#e2d6c9] text-slate-800"
                  : "bg-slate-50 border-slate-200 text-slate-400 opacity-60 line-through"
              }`}
            >
              <div>
                <p className="text-xs font-bold">{item.name}</p>
                <p className="text-[10px] text-slate-500 font-normal">
                  {item.category} · {item.quantity}
                </p>
              </div>
              <span
                className={`w-5 h-5 rounded-full flex items-center justify-center text-xs font-bold ${
                  item.inStock ? "bg-emerald-500 text-white" : "bg-slate-200 text-slate-400"
                }`}
              >
                {item.inStock ? "✓" : "✕"}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
