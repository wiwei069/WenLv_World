#!/usr/bin/env python3
"""Initialize the database - create all tables."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.database import engine
from app.models import Base


async def init():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Database tables created successfully.")


if __name__ == "__main__":
    import asyncio
    asyncio.run(init())
