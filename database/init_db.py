from sqlalchemy import text
from database.db import engine


async def init_db():
    with open("database/schema.sql", "r", encoding="utf-8") as f:
        schema_sql = f.read()

    statements = [stmt.strip() for stmt in schema_sql.split(";") if stmt.strip()]

    async with engine.begin() as conn:
        for stmt in statements:
            await conn.execute(text(stmt))

    print("Database initialized")
