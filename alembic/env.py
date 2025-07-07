import asyncio
import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine

# Add project root to Python path
sys.path.append(os.getcwd())

from auth.db import DATABASE_URL, Base  # Ensure auth is a package

from startapp.models import Animal

from auth.models import User_Profile  # taaki Alembic is model ko load kar le


config = context.config
fileConfig(config.config_file_name)

target_metadata = [Base.metadata]
def run_migrations_offline():
    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()

async def run_async_migrations():
    async_engine = create_async_engine(DATABASE_URL)
    async with async_engine.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await async_engine.dispose()

def run_migrations_online():
    asyncio.run(run_async_migrations())

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()