-- Store T_appointments.appointment_time as PostgreSQL TIME instead of VARCHAR(50).
-- Run after deploying code that expects a TIME column (SQLAlchemy model uses Time).

CREATE OR REPLACE FUNCTION tmp_migrate_appointment_time_varchar_to_time(s text)
RETURNS time
LANGUAGE plpgsql
IMMUTABLE
AS $$
DECLARE
  norm text;
BEGIN
  IF s IS NULL OR btrim(s) = '' THEN
    RETURN NULL;
  END IF;
  norm := upper(regexp_replace(btrim(s), '\s+', ' ', 'g'));

  -- 24-hour forms without AM/PM
  IF norm !~ '(AM|PM)' THEN
    BEGIN
      RETURN norm::time;
    EXCEPTION WHEN OTHERS THEN
      RETURN NULL;
    END;
  END IF;

  BEGIN
    RETURN to_timestamp(norm, 'HH12:MI:SS AM')::time;
  EXCEPTION WHEN OTHERS THEN
    BEGIN
      RETURN to_timestamp(norm, 'HH12:MI AM')::time;
    EXCEPTION WHEN OTHERS THEN
      BEGIN
        RETURN to_timestamp(replace(norm, ' ', ''), 'HH12:MIAM')::time;
      EXCEPTION WHEN OTHERS THEN
        RETURN NULL;
      END;
    END;
  END;
END;
$$;

ALTER TABLE "T_appointments"
  ALTER COLUMN appointment_time TYPE time
  USING tmp_migrate_appointment_time_varchar_to_time(appointment_time::text);

DROP FUNCTION tmp_migrate_appointment_time_varchar_to_time(text);
