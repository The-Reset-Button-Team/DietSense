# DietSense — Frontend (Member 1)

Next.js 14 (App Router) · TypeScript · Tailwind CSS · Recharts

---

## Screens to Build

| Screen | Route | Description |
|--------|-------|-------------|
| Landing | `/` | Marketing/about page |
| Register | `/register` | Onboarding wizard — personal info, goals, restrictions |
| Login | `/login` | Supabase Auth login |
| Dashboard | `/dashboard` | Today`s meal plan, calorie summary, weight trend chart |
| Meal Detail | `/meal/[id]` | Recipe detail with SHAP explanation and macros |
| Progress | `/progress` | Weight trend line + macro distribution pie charts |
| Feedback | `/feedback/[id]` | Post-meal rating form (1–5 stars + comments) |
| Chat | `/chat` | Gemini-powered dietary counselling assistant |

---

## Setup

```bash
cp .env.example .env.local
npm install
npm run dev
```

## Environment Variables

See `.env.example` — copy to `.env.local` and fill in Supabase credentials.

## Key Libraries

| Library | Version | Use |
|---------|---------|-----|
| next | 14.x | App Router, SSR |
| typescript | 5.x | Type safety |
| tailwindcss | 3.x | Utility-first styling |
| recharts | 2.x | Weight trend charts, macro pie charts |
| @supabase/supabase-js | 2.x | Auth, API calls |
| @supabase/ssr | latest | Server-side session handling |
| react-hook-form | 7.x | Onboarding wizard forms |
| zod | 3.x | Schema validation on forms |

## Folder Structure

```
frontend/src/
├── app/                  # Next.js App Router pages
│   ├── layout.tsx        # Root layout with auth provider
│   ├── page.tsx          # Landing page
│   ├── dashboard/
│   ├── login/
│   ├── register/
│   ├── meal/[id]/
│   ├── progress/
│   ├── feedback/[id]/
│   └── chat/
├── components/           # Shared UI components
│   ├── ui/               # Base: Button, Card, Input, etc.
│   ├── charts/           # Recharts wrappers
│   └── layout/           # Navbar, Sidebar, Footer
├── lib/
│   └── supabaseClient.ts # Supabase browser + server clients
└── types/
    └── index.ts          # Shared TypeScript types
```

## Naming Conventions

- **Components**: PascalCase (`MealCard.tsx`)
- **Pages**: `page.tsx` (Next.js App Router convention)
- **Hooks**: camelCase prefixed with `use` (`useMealPlan.ts`)
- **Types**: PascalCase interfaces (`User`, `Recipe`, `MealPlan`)
