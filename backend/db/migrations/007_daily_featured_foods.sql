-- Migration: 007_daily_featured_foods.sql
-- Description: Creates daily_featured_foods table for Food of the Day feature in DietSense

CREATE TABLE IF NOT EXISTS daily_featured_foods (
    feature_date DATE PRIMARY KEY,
    food_id BIGINT NOT NULL REFERENCES foods(id) ON DELETE CASCADE,
    short_intro TEXT,
    description TEXT,
    common_usage TEXT,
    preparation_methods TEXT,
    image_url TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_daily_featured_food_id ON daily_featured_foods(food_id);
