import psycopg2
import sys # Optional: for handling exceptions

def connect_and_query():
    # Define connection parameters
    conn = None
    try:
        conn = psycopg2.connect(
            host="localhost",
            database="your_database_name",
            user="your_username",
            password="your_password",
            port=5432 # Default port for PostgreSQL
        )
        
        # Create a cursor object
        cur = conn.cursor()
        
        # Execute an SQL query (e.g., SELECT version())
        print('PostgreSQL database version:')
        cur.execute('SELECT version()')
        
        # Fetch the result
        db_version = cur.fetchone()
        print(db_version)

        # Example of creating a table and inserting data
        # Note: autocommit is False by default, so you must call conn.commit() for data-modifying queries
        cur.execute("""
-- Создание таблицы авторов
CREATE TABLE IF NOT EXISTS authors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    birth_year INTEGER,
    death_year INTEGER,
    bio TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Создание таблицы категорий
CREATE TABLE IF NOT EXISTS categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT
);

-- Создание таблицы эпох
CREATE TABLE IF NOT EXISTS eras (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    start_year INTEGER,
    end_year INTEGER
);

-- Создание таблицы цитат
CREATE TABLE IF NOT EXISTS quotes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    text TEXT NOT NULL,
    author_id UUID REFERENCES authors(id) ON DELETE SET NULL,
    category_id UUID REFERENCES categories(id) ON DELETE SET NULL,
    era_id UUID REFERENCES eras(id) ON DELETE SET NULL,
    source VARCHAR(500),
    language VARCHAR(10) DEFAULT 'ru',
    rating INTEGER DEFAULT 0 CHECK (rating >= 0),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT quote_text_length CHECK (length(text) >= 10)
);

-- Индексы для быстрого поиска
CREATE INDEX IF NOT EXISTS idx_quote_text ON quotes USING gin(to_tsvector('russian', text));
CREATE INDEX IF NOT EXISTS idx_quote_rating ON quotes(rating);
CREATE INDEX IF NOT EXISTS idx_quote_created ON quotes(created_at);
CREATE INDEX IF NOT EXISTS idx_author_name ON authors(name);

-- Уникальный индекс на текст и автора для избежания дубликатов
CREATE UNIQUE INDEX IF NOT EXISTS uq_quote_text_author 
ON quotes(text, author_id) 
WHERE author_id IS NOT NULL;

-- Создаем таблицу статистики
CREATE TABLE IF NOT EXISTS quote_stats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    quote_id UUID UNIQUE REFERENCES quotes(id) ON DELETE CASCADE,
    views INTEGER DEFAULT 0,
    shares INTEGER DEFAULT 0,
    likes INTEGER DEFAULT 0,
    last_viewed TIMESTAMP
);

-- Создаем таблицу логов обновлений
CREATE TABLE IF NOT EXISTS update_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_name VARCHAR(100) NOT NULL,
    quotes_added INTEGER DEFAULT 0,
    quotes_updated INTEGER DEFAULT 0,
    errors INTEGER DEFAULT 0,
    status VARCHAR(20) NOT NULL,
    error_message TEXT,
    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    duration_ms INTEGER
);

-- Создаем индекс для логов
CREATE INDEX IF NOT EXISTS idx_update_log_source ON update_logs(source_name);
CREATE INDEX IF NOT EXISTS idx_update_log_date ON update_logs(executed_at);

-- Вставляем тестовые данные
INSERT INTO authors (id, name, birth_year, death_year, bio) VALUES
(gen_random_uuid(), 'Аристотель', -384, -322, 'Древнегреческий философ'),
(gen_random_uuid(), 'Фридрих Ницше', 1844, 1900, 'Немецкий философ'),
(gen_random_uuid(), 'Лев Толстой', 1828, 1910, 'Русский писатель'),
(gen_random_uuid(), 'Сократ', -470, -399, 'Древнегреческий философ'),
(gen_random_uuid(), 'Конфуций', -551, -479, 'Китайский философ')
ON CONFLICT DO NOTHING;

INSERT INTO categories (id, name, description) VALUES
(gen_random_uuid(), 'философия', 'Философские цитаты'),
(gen_random_uuid(), 'литература', 'Литературные цитаты'),
(gen_random_uuid(), 'наука', 'Научные цитаты'),
(gen_random_uuid(), 'мудрость', 'Народная мудрость'),
(gen_random_uuid(), 'юмор', 'Юмористические цитаты')
ON CONFLICT DO NOTHING;

INSERT INTO eras (id, name, start_year, end_year) VALUES
(gen_random_uuid(), 'Античность', -800, 476),
(gen_random_uuid(), 'Средневековье', 476, 1492),
(gen_random_uuid(), 'Новое время', 1492, 1789),
(gen_random_uuid(), 'Современность', 1789, 2024)
ON CONFLICT DO NOTHING;

-- Вставляем тестовые цитаты
WITH author_ids AS (SELECT id FROM authors WHERE name = 'Аристотель'),
     category_ids AS (SELECT id FROM categories WHERE name = 'философия'),
     era_ids AS (SELECT id FROM eras WHERE name = 'Античность')
INSERT INTO quotes (id, text, author_id, category_id, era_id, source, rating) VALUES
(gen_random_uuid(), 'Мы есть то, что мы постоянно делаем. Совершенство, следовательно, не действие, а привычка.',
 (SELECT id FROM author_ids),
 (SELECT id FROM category_ids),
 (SELECT id FROM era_ids),
 'Никомахова этика', 15),

(gen_random_uuid(), 'Платон мне друг, но истина дороже.',
 (SELECT id FROM author_ids),
 (SELECT id FROM category_ids),
 (SELECT id FROM era_ids),
 NULL, 12);
                    """)

        # Close the cursor
        cur.close()
        
    except psycopg2.DatabaseError as e:
        print(f"Error connecting to PostgreSQL: {e}")
        if conn:
            conn.rollback() # Roll back the transaction in case of an error
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        # Close the connection
        if conn:
            conn.close()
            print("\nPostgreSQL connection is closed")

if __name__ == '__main__':
    connect_and_query()
