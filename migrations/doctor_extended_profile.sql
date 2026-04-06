-- Extended doctor profile: contact, bio, experience, education, specializations, sub-specialty
-- Run once against the DB that backs `M_doctors` (see app.db.models.Doctor).
ALTER TABLE "M_doctors" ADD COLUMN IF NOT EXISTS sub_specialty VARCHAR(255);
ALTER TABLE "M_doctors" ADD COLUMN IF NOT EXISTS bio TEXT;
ALTER TABLE "M_doctors" ADD COLUMN IF NOT EXISTS experience TEXT;
ALTER TABLE "M_doctors" ADD COLUMN IF NOT EXISTS education TEXT;
ALTER TABLE "M_doctors" ADD COLUMN IF NOT EXISTS specializations TEXT;
ALTER TABLE "M_doctors" ADD COLUMN IF NOT EXISTS phone VARCHAR(20);
ALTER TABLE "M_doctors" ADD COLUMN IF NOT EXISTS email VARCHAR(255);
ALTER TABLE "M_doctors" ADD COLUMN IF NOT EXISTS address TEXT;
