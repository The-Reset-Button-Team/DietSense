---
name: DietSense
colors:
  surface: '#fcf9f4'
  surface-dim: '#dcdad5'
  surface-bright: '#fcf9f4'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f6f3ee'
  surface-container: '#f0ede9'
  surface-container-high: '#ebe8e3'
  surface-container-highest: '#e5e2dd'
  on-surface: '#1c1c19'
  on-surface-variant: '#534344'
  inverse-surface: '#31302d'
  inverse-on-surface: '#f3f0eb'
  outline: '#867274'
  outline-variant: '#d9c1c2'
  surface-tint: '#934652'
  primary: '#3c0311'
  on-primary: '#ffffff'
  primary-container: '#581825'
  on-primary-container: '#d77d89'
  inverse-primary: '#ffb2bb'
  secondary: '#006c49'
  on-secondary: '#ffffff'
  secondary-container: '#6cf8bb'
  on-secondary-container: '#00714d'
  tertiary: '#00144f'
  on-tertiary: '#ffffff'
  tertiary-container: '#00257f'
  on-tertiary-container: '#7390ff'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#ffd9dc'
  primary-fixed-dim: '#ffb2bb'
  on-primary-fixed: '#3d0412'
  on-primary-fixed-variant: '#762f3b'
  secondary-fixed: '#6ffbbe'
  secondary-fixed-dim: '#4edea3'
  on-secondary-fixed: '#002113'
  on-secondary-fixed-variant: '#005236'
  tertiary-fixed: '#dce1ff'
  tertiary-fixed-dim: '#b7c4ff'
  on-tertiary-fixed: '#001551'
  on-tertiary-fixed-variant: '#0039b5'
  background: '#fcf9f4'
  on-background: '#1c1c19'
  surface-variant: '#e5e2dd'
typography:
  display-lg:
    fontFamily: Newsreader
    fontSize: 48px
    fontWeight: '400'
    lineHeight: 56px
    letterSpacing: -0.02em
  display-lg-mobile:
    fontFamily: Newsreader
    fontSize: 36px
    fontWeight: '400'
    lineHeight: 44px
    letterSpacing: -0.01em
  headline-lg:
    fontFamily: Newsreader
    fontSize: 32px
    fontWeight: '500'
    lineHeight: 40px
    letterSpacing: -0.01em
  headline-lg-mobile:
    fontFamily: Newsreader
    fontSize: 26px
    fontWeight: '500'
    lineHeight: 34px
    letterSpacing: 0em
  headline-md:
    fontFamily: Newsreader
    fontSize: 24px
    fontWeight: '500'
    lineHeight: 32px
  headline-sm:
    fontFamily: Newsreader
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
  body-lg:
    fontFamily: Hanken Grotesk
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Hanken Grotesk
    fontSize: 15px
    fontWeight: '400'
    lineHeight: 24px
  body-sm:
    fontFamily: Hanken Grotesk
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 20px
  label-lg:
    fontFamily: Hanken Grotesk
    fontSize: 14px
    fontWeight: '600'
    lineHeight: 20px
    letterSpacing: 0.01em
  label-md:
    fontFamily: Hanken Grotesk
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.04em
  label-sm:
    fontFamily: Hanken Grotesk
    fontSize: 11px
    fontWeight: '700'
    lineHeight: 14px
    letterSpacing: 0.06em
  metric-num:
    fontFamily: Hanken Grotesk
    fontSize: 28px
    fontWeight: '700'
    lineHeight: 32px
    letterSpacing: -0.02em
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  gutter: 1.5rem
  gutter-mobile: 1rem
  margin: 3rem
  margin-tablet: 2rem
  margin-mobile: 1.25rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 1rem
  space-lg: 1.5rem
  space-xl: 2.5rem
---

## Brand & Style
The design system balances the tactile authenticity of culinary journals with the rigor of nutritional science. It speaks to mindful health seekers, clinical nutritionists, and everyday wellness enthusiasts who value both holistic nourishment and empirical clarity.

Visually, the system operates as an **Artisanal Editorial Workspace**:
- **Warm Tactility:** Surfaces mirror uncoated culinary stock and natural grain linen, counteracting the sterile impersonality typical of clinical tracking apps.
- **Scientific Exactitude:** Metrics, macronutrient splits, and bio-markers are presented with precise, data-first typography and micro-visual structures.
- **Intentional Contrast:** Deep enological reds ground the reading experience, while lively botanical greens celebrate fresh vitality, accented by deliberate scientific blues for technical verification.

## Colors
The palette evokes an artisanal kitchen notebook layered over a clinical lab report.

- **Primary Wine Palette (`#581825`, `#421018`):** Anchors typographic hierarchy, high-priority interactive buttons, active tab states, and structural dividers. Deep wine communicates heritage, craft, and grounded authority.
- **Secondary Nutrition Greens (`#10B981`, `#059669`):** Represents biological health, daily targets achieved, positive glycemic responses, and fresh whole-food tags. Never used decoratively without semantic nutritional meaning.
- **Tertiary Scientific Accents (`#1D4ED8`, `#EFF6FF`):** Reserved for technical metrics, micronutrient data visualizations, clinical research citations, hydration indexes, and system notifications.
- **Parchment Neutrals (`#FAF7F2`, `#F3EAE0`, `#E2D6C9`):** `#FAF7F2` acts as the global canvas, `#F3EAE0` creates layered card elevations, and `#E2D6C9` defines hairline rules and tactile border definitions.

## Typography
The typographic pairing reflects the synthesis between editorial culinary literature and quantitative nutrition tracking:

- **Editorial Serifs (Newsreader):** Used exclusively for headlines, reflective journal prompts, recipe titles, and narrative insights. Emphasizes warm authority and an unhurried, thoughtful cadence.
- **Precise Sans (Hanken Grotesk):** Deployed for all informational scaffolding, numeric reads, nutritional facts, tracking widgets, and micro-labels. Its geometric clarity prevents fatigue when scanning dense macro breakdowns.
- **Tabular Numerics:** All dynamic dietary figures and progress scores must implement `font-variant-numeric: tabular-nums` to maintain vertical alignment in tables and macro widgets.

## Layout & Spacing
The layout adheres to a classical editorial grid structure that gracefully downscales into focused single-column feeds:

- **Grid Architecture:** Desktop views employ a 12-column fluid grid system bounded by a max-width of `1280px`. Tablet transitions to an 8-column system, and mobile collapses to a 4-column column configuration.
- **Rhythm & Breathing Room:** Generous section spacing (`space-xl`) isolates primary metric cards from daily journal entries, recreating the spatial pacing of magazine spreads.
- **Split Dashboard Layouts:** Desktop screens split 8:4, placing daily logging, meals, and narrative digests on the broader 8-column canvas, while reserving the 4-column rail for persistent macro gauges, hydration tracking, and biomarker trends.

## Elevation & Depth
This design system avoids high-tech dropshadows and heavy blurs in favor of **Tonal Layering and Physical Paper Metaphors**:

- **Layer Tiers:** Elevation is achieved through tone rather than distance. The default canvas sits at `#FAF7F2`. Surface level 1 (cards, meal logs) rests on `#FFFFFF` with a 1px continuous hairline of `#E2D6C9`. Surface level 2 (expanded dialogs, flyout drawers) utilizes `#F3EAE0` bordered with `#D8C7B5`.
- **Soft Ambient Shadows:** When an interactive element rises on drag or modal display, use an organic, warm-tinted shadow: `0 8px 24px -4px rgba(66, 16, 24, 0.06), 0 2px 6px -1px rgba(66, 16, 24, 0.04)`.
- **Low-Contrast Ghost Outlines:** Cards and modules rely on subtle internal borders (`1px solid #E2D6C9`) to maintain crisp boundaries without computational visual weight.

## Shapes
A soft, restrained corner radius (`0.25rem` standard, scaling to `0.5rem` for cards) provides structural stability reminiscent of tailored stationery and index catalog cards.

- **Standard Elements (inputs, buttons, cards):** Built on `roundedness: 1` (`4px` / `0.25rem` for controls, `8px` / `0.5rem` for card bounds). This maintains an editorial crispness that distinguishes it from overly playful consumer trackers.
- **Specialized Pill Shapes:** Macronutrient badges (Carbs, Protein, Fat, Fiber) and filter chips leverage full pill geometry (`9999px`) to create an immediate tactile distinction between discrete data tags and structural cards.

## Components

### Buttons
- **Primary:** Background in `#581825` with text in `#FAF7F2`. Hover deepens to `#421018`. Active state scales subtly (`scale(0.99)`).
- **Secondary:** Transparent background with a `1px` border in `#581825` and text in `#581825`. Hover shifts background to `rgba(88, 24, 37, 0.05)`.
- **Subtle / Ghost:** Text in `#581825`, background transparent. Hover applies `#F3EAE0`.

### Macro Pills & Tags
- Compact, capsule-shaped tokens displaying dietary variables:
  - **Protein:** Tinted `#581825` at 8% fill, `#581825` text, hairline border.
  - **Carbohydrates:** Warm harvest tint (`#D97706` at 10% fill, `#B45309` text).
  - **Fats:** Soft ochre (`#CA8A04` at 10% fill, `#A16207` text).
  - **Fiber / Micronutrients:** Vibrant botanical green (`#10B981` at 10% fill, `#059669` text).
- Font is set in `label-sm` with letter spacing for instantaneous recognition.

### Input Fields & Selectors
- Constructed with `#FFFFFF` or `#FAF7F2` backgrounds enclosed by `1px solid #E2D6C9`.
- Focused state transitions border color to `#581825` with an offset outline ring: `0 0 0 1px #581825`.
- Placeholder text in `#8C7E72`, shifting to `#1C1917` when user input is active.

### Cards & Journal Containers
- Built on `#FFFFFF` with a `1px solid #E2D6C9` boundary. Padding is set to `space-md` or `space-lg`.
- Headers within cards use `headline-sm` in Newsreader, followed immediately by clean numeric or textual summaries in Hanken Grotesk.
- Interactive cards feature a subtle hover transition where the border darkens to `#CDBCAE`.

### Data Visualizations & Charts
- **Line & Area Curves (e.g., Glycemic Load, Caloric Intake):** Uses smooth spline curves. Stroke width set to `2.5px` in `#10B981` or `#1D4ED8` with a gradient falloff to `rgba(255, 255, 255, 0)`.
- **Grid Lines:** Muted dashed rules using `#E2D6C9` at 60% opacity.
- **Tooltip Flyouts:** Styled as miniature recipe cards: `#FAF7F2` parchment background, `#581825` header text, tabular metric numbers, and `1px solid #E2D6C9`.

### Status Badges
- Used for metabolic state, meal confirmation, and dietary alerts:
  - **Optimal / Logged:** `#10B981` fill at 12%, `#059669` text, paired with a solid 6px dot indicator.
  - **Clinical / Research Note:** `#EFF6FF` background, `#1D4ED8` text, `#BFDBFE` border.
  - **Attention / Deficit:** `#FEF2F2` background, `#991B1B` text, `#FECACA` border.