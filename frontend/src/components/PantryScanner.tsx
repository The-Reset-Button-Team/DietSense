import React, { useState } from "react";
import { PantryItem } from "@/types";

interface PantryScannerProps {
  pantryItems: PantryItem[];
  togglePantryItem: (id: string) => void;
  onAddManualItem: (name: string) => void;
}

export const PantryScanner: React.FC<PantryScannerProps> = ({
  pantryItems,
  togglePantryItem,
  onAddManualItem,
}) => {
  const [pantryInputText, setPantryInputText] = useState<string>("");
  const [isScanning, setIsScanning] = useState<boolean>(false);
  const [scanMessage, setScanMessage] = useState<string>("");

  const handleAdd = () => {
    if (!pantryInputText.trim()) return;
    onAddManualItem(pantryInputText.trim());
    setPantryInputText("");
  };

  const handleSimulateScan = (presetType: "blinkit" | "fridge") => {
    setIsScanning(true);
    setScanMessage("AI Image Extraction chal raha hai... Items detect ho rahe hain...");
    setTimeout(() => {
      setIsScanning(false);
      if (presetType === "blinkit") {
        setScanMessage("✓ Blinkit Bill Extracted! 6 fresh items cart me add ho gaye.");
      } else {
        setScanMessage("✓ Fridge Snapshot Analyzed! Paneer, Palak & Dahi detected.");
      }
    }, 900);
  };

  const inStockCount = pantryItems.filter((i) => i.inStock).length;

  return (
    <div className="relative z-10 space-y-4">
      {/* Image / Bill Upload Section */}
      <div className="rounded-2xl bg-white p-5 border border-[#e8ded3] shadow-sm space-y-4">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <div>
            <h3 className="text-base font-serif text-[#421018] font-semibold flex items-center gap-2">
              <span>📸</span> Grocery Bill &amp; Fridge Image Scanner
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Upload grocery bill photo ya fridge snapshot — AI items extract karke direct pantry me add karega!
            </p>
          </div>
          <span className="text-xs bg-emerald-50 text-emerald-800 px-2.5 py-1 rounded-full border border-emerald-200 font-semibold">
            Pantry-to-Plate AI
          </span>
        </div>

        {/* Upload Box / Scanner Simulator */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="md:col-span-2 p-5 border-2 border-dashed border-[#d8c8b8] rounded-2xl bg-[#faf7f2] flex flex-col items-center justify-center text-center space-y-3">
            <div className="w-12 h-12 rounded-2xl bg-white border border-[#e2d6c9] flex items-center justify-center text-2xl shadow-sm">
              📷
            </div>
            <div>
              <h4 className="text-xs font-bold text-[#421018]">Upload Grocery Receipt or Fridge Image</h4>
              <p className="text-[11px] text-slate-500 mt-0.5">
                Supports PNG, JPG, Zepto/Blinkit PDF bills &amp; camera snapshots
              </p>
            </div>

            <div className="flex gap-2 flex-wrap justify-center pt-1">
              <button
                onClick={() => handleSimulateScan("blinkit")}
                disabled={isScanning}
                className="px-3 py-1.5 rounded-xl bg-[#581825] hover:bg-[#722230] text-white text-xs font-medium shadow-sm transition-all"
              >
                {isScanning ? "Extracting..." : "⚡ Scan Sample Blinkit Bill"}
              </button>
              <button
                onClick={() => handleSimulateScan("fridge")}
                disabled={isScanning}
                className="px-3 py-1.5 rounded-xl bg-white border border-[#d8c8b8] hover:bg-slate-50 text-slate-700 text-xs font-medium transition-all"
              >
                📸 Scan Fridge Photo
              </button>
            </div>

            {scanMessage && (
              <div className="p-2 px-3 rounded-lg bg-emerald-50 border border-emerald-200 text-xs text-emerald-800 font-medium mt-2 animate-fadeIn">
                {scanMessage}
              </div>
            )}
          </div>

          {/* Manual Add Item */}
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
