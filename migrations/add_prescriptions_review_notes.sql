-- Add review_notes to prescriptions (for pharmacist approval notes)
-- Run once: psql -U your_user -d your_db -f add_prescriptions_review_notes.sql
-- Or execute in your DB client:
ALTER TABLE prescriptions
ADD COLUMN IF NOT EXISTS review_notes TEXT;
