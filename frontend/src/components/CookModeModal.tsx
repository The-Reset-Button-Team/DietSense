"use client";

import React, { useState, useEffect, useCallback, useRef } from "react";

// ─── Types ────────────────────────────────────────────────────────────────────

interface Ingredient {
  name: string;
  quantity: string;
  note?: string;
}

interface CookModeModalProps {
  isOpen: boolean;
  onClose: () => void;
  recipeName: string;
  recipeId?: number;
  steps?: string[];
  ingredients?: Ingredient[];
  prepTimeMins?: number;
  cookTimeMins?: number;
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
}

const DEFAULT_TIMER_SECONDS = 120; // 2 minutes

// ─── Component ────────────────────────────────────────────────────────────────

export const CookModeModal: React.FC<CookModeModalProps> = ({
  isOpen,
  onClose,
  recipeName,
  steps,
  ingredients,
  prepTimeMins,
  cookTimeMins,
}) => {
  // ── Ingredient checklist state ───────────────────────────────────────────
  const [checked, setChecked] = useState<boolean[]>([]);

  // ── Step navigation state ────────────────────────────────────────────────
  const [currentStep, setCurrentStep] = useState<number>(0);
  const [finished, setFinished] = useState<boolean>(false);

  // ── Timer state ──────────────────────────────────────────────────────────
  const [remainingSeconds, setRemainingSeconds] = useState<number>(DEFAULT_TIMER_SECONDS);
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [timerFinished, setTimerFinished] = useState<boolean>(false);
  const [timerFlash, setTimerFlash] = useState<boolean>(false);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Normalize data
  const safeIngredients: Ingredient[] = ingredients && ingredients.length > 0 ? ingredients : [];
  const safeSteps: string[] = steps && steps.length > 0 ? steps : [];
  const totalSteps = safeSteps.length;

  // ── Reset state when modal opens ─────────────────────────────────────────
  useEffect(() => {
    if (isOpen) {
      setChecked(new Array(safeIngredients.length).fill(false));
      setCurrentStep(0);
      setFinished(false);
      setRemainingSeconds(DEFAULT_TIMER_SECONDS);
      setIsRunning(false);
      setTimerFinished(false);
      setTimerFlash(false);
    }
  }, [isOpen]); // eslint-disable-line react-hooks/exhaustive-deps

  // ── Timer interval ───────────────────────────────────────────────────────
  useEffect(() => {
    if (isRunning && remainingSeconds > 0) {
      intervalRef.current = setInterval(() => {
        setRemainingSeconds((prev) => {
          if (prev <= 1) {
            clearInterval(intervalRef.current!);
            setIsRunning(false);
            setTimerFinished(true);
            setTimerFlash(true);
            setTimeout(() => setTimerFlash(false), 2000);
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    } else {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [isRunning]);

  // ── Close on Escape ──────────────────────────────────────────────────────
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    if (isOpen) window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  // ── Ingredient checklist handlers ────────────────────────────────────────
  const toggleIngredient = useCallback((index: number) => {
    setChecked((prev) => {
      const next = [...prev];
      next[index] = !next[index];
      return next;
    });
  }, []);

  const checkedCount = checked.filter(Boolean).length;

  // ── Step navigation handlers ─────────────────────────────────────────────
  const handlePrev = () => {
    if (currentStep > 0) setCurrentStep((s) => s - 1);
  };

  const handleNext = () => {
    if (currentStep < totalSteps - 1) {
      setCurrentStep((s) => s + 1);
    } else {
      setFinished(true);
    }
  };

  const stepProgress = totalSteps > 0 ? ((currentStep + 1) / totalSteps) * 100 : 0;

  // ── Timer handlers ───────────────────────────────────────────────────────
  const handleStartPause = () => {
    if (timerFinished) return;
    setIsRunning((r) => !r);
  };

  const handleReset = () => {
    setIsRunning(false);
    setRemainingSeconds(DEFAULT_TIMER_SECONDS);
    setTimerFinished(false);
    setTimerFlash(false);
  };

  const addMinutes = (mins: number) => {
    setRemainingSeconds((s) => s + mins * 60);
    setTimerFinished(false);
  };

  // ── Don't render if closed ───────────────────────────────────────────────
  if (!isOpen) return null;

  // ── Colors (DietSense warm palette) ─────────────────────────────────────
  const PRIMARY = "#581825";
  const PRIMARY_DARK = "#421018";

  return (
    <div
      className="fixed inset-0 z-50 flex flex-col"
      role="dialog"
      aria-modal="true"
      aria-label={`Cook Mode: ${recipeName}`}
    >
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/70 backdrop-blur-sm"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Modal panel */}
      <div className="relative z-10 flex flex-col h-full max-w-5xl mx-auto w-full bg-white shadow-2xl overflow-hidden">

        {/* ── Header ── */}
        <header
          className="flex items-center justify-between px-4 py-3 text-white flex-shrink-0"
          style={{ backgroundColor: PRIMARY }}
        >
          <div>
            <h2 className="text-lg font-bold leading-tight truncate max-w-xs sm:max-w-md">
              🍳 Cook Mode — {recipeName}
            </h2>
            {(prepTimeMins !== undefined || cookTimeMins !== undefined) && (
              <p className="text-xs opacity-80 mt-0.5">
                {prepTimeMins !== undefined && `Prep: ${prepTimeMins}m`}
                {prepTimeMins !== undefined && cookTimeMins !== undefined && " · "}
                {cookTimeMins !== undefined && `Cook: ${cookTimeMins}m`}
              </p>
            )}
          </div>
          <button
            onClick={onClose}
            aria-label="Close cook mode"
            className="ml-4 w-10 h-10 flex items-center justify-center rounded-full bg-white/20 hover:bg-white/30 transition-colors text-white text-xl font-bold flex-shrink-0"
          >
            ✕
          </button>
        </header>

        {/* ── Main content (scrollable) ── */}
        <div className="flex-1 overflow-y-auto">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-0 h-full">

            {/* ── Left column: Ingredients ── */}
            <section className="p-4 border-b md:border-b-0 md:border-r border-slate-200 bg-slate-50">
              <h3 className="text-base font-semibold mb-2" style={{ color: PRIMARY }}>
                🥦 Ingredients
              </h3>

              {safeIngredients.length === 0 ? (
                <p className="text-slate-500 text-sm italic">No ingredient list available.</p>
              ) : (
                <>
                  {/* Progress counter */}
                  <div className="mb-3">
                    <div className="flex items-center justify-between text-xs text-slate-600 mb-1">
                      <span>{checkedCount} of {safeIngredients.length} prepped</span>
                      <span className="font-medium">
                        {safeIngredients.length > 0
                          ? Math.round((checkedCount / safeIngredients.length) * 100)
                          : 0}%
                      </span>
                    </div>
                    <div className="h-1.5 w-full bg-slate-200 rounded-full overflow-hidden">
                      <div
                        className="h-full rounded-full transition-all duration-300"
                        style={{
                          width: safeIngredients.length > 0
                            ? `${(checkedCount / safeIngredients.length) * 100}%`
                            : "0%",
                          backgroundColor: PRIMARY,
                        }}
                      />
                    </div>
                  </div>

                  {/* Ingredient rows */}
                  <ul className="space-y-1">
                    {safeIngredients.map((ing, idx) => (
                      <li key={idx}>
                        <button
                          type="button"
                          onClick={() => toggleIngredient(idx)}
                          aria-label={`${checked[idx] ? "Uncheck" : "Check"} ${ing.name}`}
                          aria-pressed={checked[idx]}
                          className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-left transition-all min-h-[44px] border ${
                            checked[idx]
                              ? "bg-green-50 border-green-300 opacity-70"
                              : "bg-white border-slate-200 hover:border-slate-300 hover:bg-slate-50"
                          }`}
                        >
                          {/* Checkbox visual */}
                          <span
                            className={`w-5 h-5 flex-shrink-0 rounded border-2 flex items-center justify-center transition-colors ${
                              checked[idx]
                                ? "border-green-500 bg-green-500 text-white"
                                : "border-slate-300"
                            }`}
                            aria-hidden="true"
                          >
                            {checked[idx] && (
                              <svg className="w-3 h-3" viewBox="0 0 12 12" fill="none">
                                <path
                                  d="M2 6l3 3 5-5"
                                  stroke="currentColor"
                                  strokeWidth="2"
                                  strokeLinecap="round"
                                  strokeLinejoin="round"
                                />
                              </svg>
                            )}
                          </span>
                          <span className="flex-1">
                            <span
                              className={`text-sm font-medium ${
                                checked[idx] ? "line-through text-slate-400" : "text-slate-800"
                              }`}
                            >
                              {ing.name}
                            </span>
                            <span className="text-xs text-slate-500 ml-2">{ing.quantity}</span>
                            {ing.note && (
                              <span className="block text-xs text-slate-400 mt-0.5 italic">
                                {ing.note}
                              </span>
                            )}
                          </span>
                        </button>
                      </li>
                    ))}
                  </ul>
                </>
              )}
            </section>

            {/* ── Right column: Steps ── */}
            <section className="p-4 bg-white flex flex-col">
              <h3 className="text-base font-semibold mb-3" style={{ color: PRIMARY }}>
                📋 Steps
              </h3>

              {safeSteps.length === 0 ? (
                <p className="text-slate-500 text-sm italic">
                  No steps available. Follow the recipe card instructions.
                </p>
              ) : finished ? (
                /* Completion message */
                <div className="flex-1 flex flex-col items-center justify-center text-center px-4 py-10">
                  <div className="text-6xl mb-4">🎉</div>
                  <h4 className="text-2xl font-bold mb-2" style={{ color: PRIMARY }}>
                    You&apos;re done!
                  </h4>
                  <p className="text-slate-600 text-base">
                    {recipeName} is ready to serve. Enjoy your meal!
                  </p>
                  <button
                    onClick={() => { setFinished(false); setCurrentStep(0); }}
                    className="mt-6 px-6 py-2 rounded-lg text-white text-sm font-medium min-h-[44px] transition-opacity hover:opacity-90"
                    style={{ backgroundColor: PRIMARY }}
                    aria-label="Restart steps"
                  >
                    ↩ Start Over
                  </button>
                </div>
              ) : (
                <>
                  {/* Step progress bar */}
                  <div className="mb-3">
                    <div className="flex items-center justify-between text-xs text-slate-500 mb-1">
                      <span>Step {currentStep + 1} of {totalSteps}</span>
                      <span>{Math.round(stepProgress)}%</span>
                    </div>
                    <div className="h-1.5 w-full bg-slate-200 rounded-full overflow-hidden">
                      <div
                        className="h-full rounded-full transition-all duration-300"
                        style={{ width: `${stepProgress}%`, backgroundColor: PRIMARY }}
                      />
                    </div>
                  </div>

                  {/* Step card */}
                  <div className="flex-1 flex flex-col">
                    <div className="flex-1 bg-slate-50 rounded-xl p-4 border border-slate-200 mb-4">
                      {/* Step badge */}
                      <div
                        className="inline-flex items-center justify-center w-10 h-10 rounded-full text-white font-bold text-lg mb-3"
                        style={{ backgroundColor: PRIMARY }}
                      >
                        {currentStep + 1}
                      </div>
                      <p className="text-slate-800 text-base leading-relaxed">
                        {safeSteps[currentStep]}
                      </p>
                    </div>

                    {/* Navigation buttons */}
                    <div className="flex gap-3">
                      <button
                        onClick={handlePrev}
                        disabled={currentStep === 0}
                        aria-label="Previous step"
                        className={`flex-1 min-h-[44px] px-4 py-2 rounded-lg font-medium text-sm border transition-all ${
                          currentStep === 0
                            ? "border-slate-200 text-slate-300 cursor-not-allowed bg-slate-50"
                            : "border-slate-300 text-slate-700 hover:bg-slate-100 bg-white"
                        }`}
                      >
                        ← Prev
                      </button>
                      <button
                        onClick={handleNext}
                        aria-label={
                          currentStep === totalSteps - 1 ? "Finish cooking" : "Next step"
                        }
                        className="flex-1 min-h-[44px] px-4 py-2 rounded-lg font-medium text-sm text-white transition-opacity hover:opacity-90"
                        style={{ backgroundColor: PRIMARY }}
                      >
                        {currentStep === totalSteps - 1 ? "✓ Finish" : "Next →"}
                      </button>
                    </div>
                  </div>
                </>
              )}
            </section>
          </div>
        </div>

        {/* ── Sticky bottom: Timer ── */}
        <footer
          className={`flex-shrink-0 border-t border-slate-200 px-4 py-3 transition-colors duration-300 ${
            timerFlash ? "bg-amber-100" : "bg-white"
          }`}
        >
          <div className="flex flex-wrap items-center gap-3 max-w-5xl mx-auto">
            {/* Timer display */}
            <div
              className={`text-3xl font-mono font-bold tracking-wider min-w-[6rem] text-center transition-colors ${
                timerFinished
                  ? "text-red-600"
                  : timerFlash
                  ? "text-amber-700"
                  : "text-slate-800"
              }`}
              aria-live="polite"
              aria-label={`Timer: ${formatTime(remainingSeconds)}`}
            >
              {formatTime(remainingSeconds)}
              {timerFinished && (
                <span className="block text-xs font-normal text-red-500 mt-0.5">
                  ⏰ Time&apos;s up!
                </span>
              )}
            </div>

            {/* Timer controls */}
            <div className="flex flex-wrap gap-2 flex-1">
              {/* Start / Pause */}
              <button
                onClick={handleStartPause}
                disabled={timerFinished && remainingSeconds === 0}
                aria-label={isRunning ? "Pause timer" : "Start timer"}
                className="min-h-[44px] px-4 py-2 rounded-lg text-white text-sm font-medium transition-opacity hover:opacity-90 disabled:opacity-40"
                style={{ backgroundColor: isRunning ? PRIMARY_DARK : PRIMARY }}
              >
                {isRunning ? "⏸ Pause" : "▶ Start"}
              </button>

              {/* Reset */}
              <button
                onClick={handleReset}
                aria-label="Reset timer to 2 minutes"
                className="min-h-[44px] px-4 py-2 rounded-lg border border-slate-300 text-slate-700 text-sm font-medium hover:bg-slate-50 transition-colors bg-white"
              >
                ↺ Reset
              </button>

              {/* Preset buttons */}
              <button
                onClick={() => addMinutes(1)}
                aria-label="Add 1 minute to timer"
                className="min-h-[44px] px-3 py-2 rounded-lg border border-slate-200 text-slate-600 text-sm hover:bg-slate-50 transition-colors bg-white"
              >
                +1 min
              </button>
              <button
                onClick={() => addMinutes(3)}
                aria-label="Add 3 minutes to timer"
                className="min-h-[44px] px-3 py-2 rounded-lg border border-slate-200 text-slate-600 text-sm hover:bg-slate-50 transition-colors bg-white"
              >
                +3 min
              </button>
              <button
                onClick={() => addMinutes(5)}
                aria-label="Add 5 minutes to timer"
                className="min-h-[44px] px-3 py-2 rounded-lg border border-slate-200 text-slate-600 text-sm hover:bg-slate-50 transition-colors bg-white"
              >
                +5 min
              </button>
            </div>
          </div>
        </footer>
      </div>
    </div>
  );
};

export default CookModeModal;
