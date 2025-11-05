from sqlalchemy import text
from database.db import engine


async def init_db():
    with open("database/schema.sql", "r", encoding="utf-8") as f:
        raw = f.read()

    # Разбиваем по пустым строкам
    blocks = [b.strip() for b in raw.split("\n\n") if b.strip()]

    async with engine.begin() as conn:
        for block in blocks:
            print("Executing block:\n", block[:80], "...")
            await conn.exec_driver_sql(block)

    print("✅ Database initialized")
