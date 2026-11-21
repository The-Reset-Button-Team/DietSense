-- Migration: 006_food_prices.sql
-- Description: Create food_prices table for Indian food pricing system in INR

CREATE TABLE IF NOT EXISTS public.food_prices (
    price_id TEXT PRIMARY KEY,
    food_id INTEGER NOT NULL REFERENCES public.foods(id) ON DELETE CASCADE,
    price NUMERIC(10, 2) NOT NULL CHECK (price >= 0),
    currency VARCHAR(10) NOT NULL DEFAULT 'INR',
    unit VARCHAR(50) NOT NULL,
    region VARCHAR(100) NOT NULL DEFAULT 'National',
    source TEXT NOT NULL,
    price_type VARCHAR(20) NOT NULL CHECK (price_type IN ('verified', 'estimated')),
    last_updated VARCHAR(50) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

CREATE INDEX IF NOT EXISTS idx_food_prices_food_id ON public.food_prices(food_id);
CREATE INDEX IF NOT EXISTS idx_food_prices_region ON public.food_prices(region);
CREATE INDEX IF NOT EXISTS idx_food_prices_type ON public.food_prices(price_type);

-- Enable RLS and public read policy
ALTER TABLE public.food_prices ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Public read food prices" ON public.food_prices;
CREATE POLICY "Public read food prices" ON public.food_prices FOR SELECT USING (true);
