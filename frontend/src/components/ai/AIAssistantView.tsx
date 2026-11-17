"use client";

import React, { useState, useRef, useEffect } from "react";
import { aiApi } from "@/lib/ai-client";
import { ChatMessage, AIMealAssistantResponse } from "@/types/ai";
import { MealComparisonModal } from "./MealComparisonModal";
import { CookingInstructionsModal } from "./CookingInstructionsModal";

interface AIAssistantViewProps {
  initialMealContext?: { id: number; name: string } | null;
  onClearInitialContext?: () => void;
  availableFoods?: Array<{ id: number; name: string }>;
}

const STARTER_PROMPTS = [
  "🔥 Suggest high-protein dinner ideas under 500 kcal",
  "🌾 How should I balance carbohydrates across my meals?",
  "🥣 What quick breakfast will give me sustained energy?",
  "🥑 How to meet daily protein on a pure vegetarian diet?",
];

export const AIAssistantView: React.FC<AIAssistantViewProps> = ({
  initialMealContext,
  onClearInitialContext,
  availableFoods = [],
}) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedContextFoodId, setSelectedContextFoodId] = useState<number | undefined>(
    initialMealContext?.id
  );

  // Modals
  const [compareModalOpen, setCompareModalOpen] = useState<boolean>(false);
  const [cookingModalFood, setCookingModalFood] = useState<{ id: number; name: string } | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  useEffect(() => {
    if (initialMealContext) {
      setSelectedContextFoodId(initialMealContext.id);
      setInput(`Tell me more about ${initialMealContext.name} and how it fits my daily nutrition goals.`);
    }
  }, [initialMealContext]);

  const handleSend = async (customQuery?: string) => {
    const queryToSend = customQuery || input;
    if (!queryToSend.trim() || loading) return;

    const userMsg: ChatMessage = {
      id: `usr_${Date.now()}`,
      sender: "user",
      text: queryToSend.trim(),
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setError(null);
    setLoading(true);

    try {
      const res: AIMealAssistantResponse = await aiApi.askAssistant({
        query: queryToSend.trim(),
        context_food_ids: selectedContextFoodId ? [selectedContextFoodId] : undefined,
      });

      const aiMsg: ChatMessage = {
        id: `ai_${Date.now()}`,
        sender: "ai",
        text: res.reply,
        suggested_foods: res.suggested_foods,
        source: res.source,
        disclaimer: res.disclaimer,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };

      setMessages((prev) => [...prev, aiMsg]);
    } catch (err: any) {
      setError(err?.message || "Failed to reach AI assistant. Please try again.");
    } finally {
      setLoading(false);
      if (onClearInitialContext) {
        onClearInitialContext();
      }
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="relative z-10 flex flex-col h-[750px] max-h-[85vh] bg-white rounded-3xl border border-[#e8ded3] shadow-md overflow-hidden animate-fadeIn">
      {/* Assistant Header */}
      <div className="p-4 sm:p-5 border-b border-[#e9dfd5] bg-[#faf7f2] flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs uppercase font-bold text-[#581825] tracking-wider flex items-center gap-1.5">
              <span>✨</span> DietSense AI Assistant
            </span>
            <span className="text-[10px] bg-emerald-50 text-emerald-800 px-2 py-0.5 rounded-full border border-emerald-200 font-medium">
              USDA &amp; ICMR-NIN Grounded
            </span>
          </div>
          <h2 className="text-lg font-serif text-[#421018] font-bold mt-0.5">
            Evidence-Based Culinary &amp; Meal Coach
          </h2>
        </div>

        {/* Action Shortcuts */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => setCompareModalOpen(true)}
            className="px-3 py-1.5 rounded-xl bg-white border border-[#d8c8b8] hover:border-[#581825] text-slate-700 hover:text-[#581825] text-xs font-semibold transition-all shadow-xs flex items-center gap-1.5"
          >
            <span>⚖️</span> Compare Meals
          </button>
        </div>
      </div>

      {/* Grounding Context Selector Bar */}
      <div className="px-4 py-2 bg-[#f4ece3] border-b border-[#ebdcd0] flex items-center justify-between text-xs gap-2 flex-wrap">
        <div className="flex items-center gap-1.5 text-slate-700 font-medium">
          <span className="text-slate-500">Target Meal Context:</span>
          <select
            value={selectedContextFoodId || ""}
            onChange={(e) => setSelectedContextFoodId(e.target.value ? Number(e.target.value) : undefined)}
            className="bg-white border border-[#d8c8b8] rounded-lg px-2 py-1 text-xs text-slate-800 focus:outline-none focus:ring-1 focus:ring-[#581825]"
          >
            <option value="">None (General Advice)</option>
            {availableFoods.map((f) => (
              <option key={f.id} value={f.id}>
                {f.name}
              </option>
            ))}
          </select>
        </div>

        {selectedContextFoodId && (
          <button
            onClick={() => setSelectedContextFoodId(undefined)}
            className="text-[11px] text-[#581825] hover:underline"
          >
            Clear context ✕
          </button>
        )}
      </div>

      {/* Message Stream */}
      <div className="flex-1 p-4 sm:p-6 overflow-y-auto space-y-4 bg-slate-50/40">
        {/* Empty State */}
        {messages.length === 0 && (
          <div className="h-full flex flex-col items-center justify-center text-center p-6 space-y-4 max-w-lg mx-auto">
            <div className="w-14 h-14 rounded-3xl bg-[#faf7f2] border border-[#d8c8b8] flex items-center justify-center text-3xl shadow-sm">
              ✨
            </div>
            <div>
              <h3 className="text-base font-serif font-bold text-[#421018]">
                How can DietSense AI help you today?
              </h3>
              <p className="text-xs text-slate-500 mt-1 leading-relaxed">
                Ask questions about your daily nutrition targets, ingredient swaps,
                healthy cooking tips, or high-protein meals. Every answer is grounded
                in authoritative USDA and ICMR-NIN composition tables.
              </p>
            </div>

            {/* Quick Starters */}
            <div className="w-full space-y-2 pt-2">
              <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">
                Popular Inquiries:
              </span>
              <div className="flex flex-col gap-1.5">
                {STARTER_PROMPTS.map((prompt, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleSend(prompt)}
                    className="p-2.5 text-left text-xs bg-white border border-[#e8ded3] hover:border-[#581825] hover:bg-[#faf7f2] rounded-xl text-slate-700 transition-all font-medium shadow-2xs"
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Messages List */}
        {messages.map((msg) => {
          const isUser = msg.sender === "user";
          return (
            <div
              key={msg.id}
              className={`flex flex-col ${isUser ? "items-end" : "items-start"} space-y-1`}
            >
              <div className="flex items-center gap-1.5 text-[10px] text-slate-400 px-1">
                <span className="font-semibold">{isUser ? "You" : "DietSense AI"}</span>
                <span>·</span>
                <span>{msg.timestamp}</span>
                {!isUser && msg.source && (
                  <span className="text-[9px] bg-slate-200 text-slate-700 px-1.5 py-0.2 rounded font-mono">
                    {msg.source === "offline_fallback" ? "Evidence Engine" : "Gemini 3.8 Flash"}
                  </span>
                )}
              </div>

              <div
                className={`max-w-[85%] sm:max-w-[75%] rounded-2xl p-3.5 sm:p-4 text-xs leading-relaxed ${
                  isUser
                    ? "bg-[#581825] text-white shadow-sm rounded-tr-none"
                    : "bg-white border border-[#e8ded3] text-slate-800 shadow-sm rounded-tl-none"
                }`}
              >
                <p className="whitespace-pre-wrap">{msg.text}</p>

                {/* Suggested Foods Cards */}
                {msg.suggested_foods && msg.suggested_foods.length > 0 && (
                  <div className="mt-3 pt-3 border-t border-slate-100 space-y-2">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-[#581825] block">
                      Referenced Nutrition Context:
                    </span>
                    <div className="grid gap-2 sm:grid-cols-2">
                      {msg.suggested_foods.map((food, fIdx) => (
                        <div
                          key={fIdx}
                          className="p-2.5 rounded-xl bg-[#faf7f2] border border-[#e8ded3] text-[11px] space-y-1"
                        >
                          <div className="flex items-center justify-between">
                            <span className="font-bold text-[#421018]">{food.name}</span>
                            <button
                              onClick={() => setCookingModalFood({ id: food.id, name: food.name })}
                              className="text-[10px] text-[#581825] hover:underline font-semibold"
                            >
                              Cook 👨‍🍳
                            </button>
                          </div>
                          <div className="flex gap-2 text-slate-600 font-medium text-[10px]">
                            <span>🔥 {food.calories_kcal} kcal</span>
                            <span>·</span>
                            <span>💪 {food.protein_g}g Prot</span>
                            <span>·</span>
                            <span>🌾 {food.carbohydrates_g}g Carb</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Disclaimer */}
              {!isUser && msg.disclaimer && (
                <p className="text-[9px] text-slate-400 italic max-w-[85%] px-1">
                  {msg.disclaimer}
                </p>
              )}
            </div>
          );
        })}

        {/* Loading Indicator */}
        {loading && (
          <div className="flex items-start gap-2">
            <div className="p-3.5 bg-white border border-[#e8ded3] rounded-2xl rounded-tl-none shadow-xs text-xs text-slate-500 flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-[#581825] animate-ping" />
              <span>Consulting evidence database...</span>
            </div>
          </div>
        )}

        {/* Error Banner */}
        {error && (
          <div className="p-3 bg-red-50 border border-red-200 text-red-800 rounded-xl text-xs flex items-center justify-between">
            <span>⚠️ {error}</span>
            <button
              onClick={() => handleSend()}
              className="px-2 py-0.5 bg-red-800 text-white rounded font-medium text-[11px]"
            >
              Retry
            </button>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Tray */}
      <div className="p-3 sm:p-4 bg-white border-t border-[#e9dfd5] flex items-end gap-2">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask anything about nutrition, cooking steps, or meal planning..."
          rows={2}
          className="flex-1 p-2.5 bg-[#faf7f2] border border-[#d8c8b8] focus:border-[#581825] focus:ring-1 focus:ring-[#581825] rounded-xl text-xs text-slate-800 resize-none focus:outline-none transition-all placeholder:text-slate-400"
        />

        <button
          onClick={() => handleSend()}
          disabled={!input.trim() || loading}
          className="px-4 py-2.5 rounded-xl bg-[#581825] hover:bg-[#722230] text-white text-xs font-semibold shadow-sm transition-all disabled:opacity-40 h-[48px] flex items-center justify-center shrink-0"
        >
          {loading ? "..." : "Send ➔"}
        </button>
      </div>

      {/* Comparison Modal */}
      <MealComparisonModal
        isOpen={compareModalOpen}
        onClose={() => setCompareModalOpen(false)}
        availableFoods={availableFoods}
      />

      {/* Cooking Modal */}
      <CookingInstructionsModal
        isOpen={cookingModalFood !== null}
        foodId={cookingModalFood?.id || null}
        foodName={cookingModalFood?.name || ""}
        onClose={() => setCookingModalFood(null)}
      />
    </div>
  );
};
