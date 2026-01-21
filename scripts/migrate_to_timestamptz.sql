-- Преобразование всех timestamp колонок в timestamptz
-- Сохраняем существующие данные, предполагая, что они в UTC

ALTER TABLE authors 
ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE 
USING created_at AT TIME ZONE 'UTC',
ALTER COLUMN updated_at TYPE TIMESTAMP WITH TIME ZONE 
USING updated_at AT TIME ZONE 'UTC';

ALTER TABLE quotes 
ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE 
USING created_at AT TIME ZONE 'UTC',
ALTER COLUMN updated_at TYPE TIMESTAMP WITH TIME ZONE 
USING updated_at AT TIME ZONE 'UTC';

ALTER TABLE quote_stats 
ALTER COLUMN last_viewed TYPE TIMESTAMP WITH TIME ZONE 
USING last_viewed AT TIME ZONE 'UTC';

ALTER TABLE update_logs 
ALTER COLUMN executed_at TYPE TIMESTAMP WITH TIME ZONE 
USING executed_at AT TIME ZONE 'UTC';

-- Обновляем дефолтные значения для будущих insert'ов
ALTER TABLE authors 
ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP,
ALTER COLUMN updated_at SET DEFAULT CURRENT_TIMESTAMP;

ALTER TABLE quotes 
ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP,
ALTER COLUMN updated_at SET DEFAULT CURRENT_TIMESTAMP;

ALTER TABLE update_logs 
ALTER COLUMN executed_at SET DEFAULT CURRENT_TIMESTAMP;