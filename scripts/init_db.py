import asyncio
import sys
import os

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from src.infrastructure.database.session import database
from src.infrastructure.database.models import Base


async def init_database():
    """Инициализация базы данных"""
    print("🚀 Инициализация базы данных...")
    
    try:
        # Создаем таблицы
        async with database.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("✅ Таблицы созданы успешно")
        
        # Добавляем тестовые данные
        async with database.get_session() as session:
            # Проверяем, есть ли уже данные
            result = await session.execute(text("SELECT COUNT(*) FROM quotes"))
            count = result.scalar()
            
            if count == 0:
                print("📝 Добавление тестовых данных...")
                
                # Добавляем авторов
                await session.execute(text("""
                    INSERT INTO authors (name, birth_year, death_year, bio) VALUES
                    ('Аристотель', -384, -322, 'Древнегреческий философ'),
                    ('Фридрих Ницше', 1844, 1900, 'Немецкий философ'),
                    ('Лев Толстой', 1828, 1910, 'Русский писатель'),
                    ('Сократ', -470, -399, 'Древнегреческий философ'),
                    ('Конфуций', -551, -479, 'Китайский философ')
                    ON CONFLICT DO NOTHING
                """))
                
                # Добавляем категории
                await session.execute(text("""
                    INSERT INTO categories (name, description) VALUES
                    ('философия', 'Философские цитаты'),
                    ('литература', 'Литературные цитаты'),
                    ('наука', 'Научные цитаты'),
                    ('мудрость', 'Народная мудрость'),
                    ('юмор', 'Юмористические цитаты')
                    ON CONFLICT DO NOTHING
                """))
                
                # Добавляем эпохи
                await session.execute(text("""
                    INSERT INTO eras (name, start_year, end_year) VALUES
                    ('Античность', -800, 476),
                    ('Средневековье', 476, 1492),
                    ('Новое время', 1492, 1789),
                    ('Современность', 1789, 2024)
                    ON CONFLICT DO NOTHING
                """))
                
                await session.commit()
                print("✅ Тестовые данные добавлены")
            else:
                print(f"✅ В базе уже есть {count} цитат")
                
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        raise
    finally:
        await database.disconnect()


if __name__ == "__main__":
    asyncio.run(init_database())