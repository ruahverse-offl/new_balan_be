-- Store consultation windows as PostgreSQL TIME (slot start/end) instead of only free-text.
-- Legacy morning_timings / evening_timings VARCHAR columns remain for display / older clients.
ALTER TABLE "M_doctors" ADD COLUMN IF NOT EXISTS morning_start TIME WITHOUT TIME ZONE;
ALTER TABLE "M_doctors" ADD COLUMN IF NOT EXISTS morning_end TIME WITHOUT TIME ZONE;
ALTER TABLE "M_doctors" ADD COLUMN IF NOT EXISTS evening_start TIME WITHOUT TIME ZONE;
ALTER TABLE "M_doctors" ADD COLUMN IF NOT EXISTS evening_end TIME WITHOUT TIME ZONE;
