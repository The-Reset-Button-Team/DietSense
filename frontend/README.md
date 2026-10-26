# DietSense — Frontend (M1 Daksh Chaukhande)

Next.js 14/16 (App Router) · React 18 · TypeScript · Tailwind CSS · Recharts

---

## 🖥️ Screen & Route Structure

| Screen / Feature | Route / Tab | Description |
|------------------|-------------|-------------|
| **Landing & Dashboard** | `/` or `/?tab=today` | Today's recommendations, meal cards with score reasons, quick logging |
| **Login** | `/login` | Local backend-managed authentication with error messaging |
| **Signup** | `/signup` | User account creation with initial biometrics and targets |
| **Profile Studio** | `/?tab=profile` | Manage dietary preference, allergens, calories, budget, prep-time limits |
| **Pantry Scanner** | `/?tab=pantry` | OCR grocery receipt parsing (Blinkit/Instamart) and fridge snapshot analysis |
| **Meal Plans** | `/?tab=swap` or `/plans` | Meal swap view and saved daily meal plans |
| **Progress Analytics** | `/?tab=progress` or `/progress` | Adherence %, eaten/skipped ratio, skip reasons breakdown, daily trend |
| **Safety Shield** | `/?tab=safety` | Audit view explaining safety exclusions and non-medical notice |

---

## 🚀 Setup & Execution

```bash
cd frontend

# Copy local environment config (defaults to http://localhost:8000)
cp .env.example .env.local

# Install dependencies
npm install

# Start local Next.js dev server
npm run dev
# → Open: http://localhost:3000
```

---

## 🧪 Verification & Build Commands

```bash
# Type check TypeScript definitions across all components
npm run type-check

# Run TypeScript syntax and code check
npm run lint

# Build optimized production bundle
npm run build
```

---

## 🔑 Key Libraries & Integration

| Library | Version | Role in DietSense |
|---------|---------|-------------------|
| `next` | 14/16 | Next.js App Router, SSR, and production builds |
| `react` | 18.x | Reusable UI components, hooks (`useState`, `useEffect`, `useMemo`) |
| `typescript` | 5.x | End-to-end type safety for API requests, recommendations, and analytics |
| `tailwindcss` | 3.x | Utility classes for responsive, high-contrast layouts |
| `recharts` | 2.x | Real-time charts for adherence %, skip reason distribution, and trends |
| `lucide-react`| latest | System icons for meal categories, allergies, and navigation |

---

## 📂 Folder Structure

```
frontend/
├── src/
│   ├── app/                     # App Router pages (/login, /signup, /dashboard, etc.)
│   ├── components/              # Modular UI components
│   │   ├── Header.tsx           # Navigation bar with user status and logout
│   │   ├── MealCard.tsx         # Recommendation card with explainable reasons
│   │   ├── PantryScanner.tsx    # Receipt PDF/image upload & fridge detection
│   │   ├── ProgressAnalytics.tsx# Recharts integration for meal adherence
│   │   ├── ProfileStudio.tsx    # User preference and restriction controls
│   │   └── SafetyShield.tsx     # Allergy safety explanations
│   ├── context/
│   │   └── AuthContext.tsx      # Local FastAPI auth state & session handling
│   ├── lib/
│   │   ├── api-client.ts        # Typed fetch wrapper with Bearer token injection
│   │   └── nutrition.ts         # BMR, TDEE, macro target calculators
│   └── types/
│       └── index.ts             # Shared TypeScript interfaces (Recipe, Log, Profile)
├── public/
│   └── samples/                 # Sample receipt and fridge images for offline demo
└── package.json
```
