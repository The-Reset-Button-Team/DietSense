// DietSense Landing Page
// Phase 5 (Frontend UI) will replace this with the full marketing/onboarding UI.
// Phase 1 placeholder: confirms Next.js routing works end-to-end.

export default function HomePage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8">
      <div className="max-w-2xl text-center space-y-6">
        {/* Logo / Brand */}
        <div className="flex items-center justify-center gap-3">
          <span className="text-5xl">🥗</span>
          <h1 className="text-5xl font-bold text-brand-600">DietSense</h1>
        </div>

        {/* Tagline */}
        <p className="text-xl text-gray-600">
          Adaptive, evidence-based meal planning for{" "}
          <span className="font-semibold text-brand-600">obesity prevention</span>.
        </p>

        {/* Pipeline summary */}
        <div className="rounded-xl border border-brand-200 bg-brand-50 p-6 text-left text-sm space-y-2">
          <p className="font-semibold text-brand-800 text-base">
            📌 How it works
          </p>
          <ol className="list-decimal list-inside space-y-1 text-gray-700">
            <li>Nutrition data sourced strictly from USDA &amp; ICMR-NIN datasets</li>
            <li>Hard safety gate checks allergies &amp; restrictions before scoring</li>
            <li>Hybrid scoring: Macro (30%) · Goal (20%) · Preference (20%) · Feedback (15%) · Diversity (10%) · Prep (5%)</li>
            <li>SHAP explainability shows <em>why</em> each meal was recommended</li>
            <li>Gemini API provides natural-language explanations only — never generates nutrition facts</li>
          </ol>
        </div>

        {/* Phase status */}
        <div className="rounded-lg bg-yellow-50 border border-yellow-200 px-4 py-3 text-sm text-yellow-800">
          <strong>Phase 1 — Requirements &amp; Specs</strong> · Scaffold only.
          Full UI arrives in Phase 5.
        </div>

        {/* CTA placeholders */}
        <div className="flex gap-4 justify-center pt-2">
          <a
            href="/register"
            className="rounded-lg bg-brand-600 px-6 py-3 text-white font-semibold hover:bg-brand-700 transition-colors"
          >
            Get Started
          </a>
          <a
            href="/login"
            className="rounded-lg border border-brand-300 px-6 py-3 text-brand-700 font-semibold hover:bg-brand-50 transition-colors"
          >
            Log In
          </a>
        </div>
      </div>
    </main>
  );
}
