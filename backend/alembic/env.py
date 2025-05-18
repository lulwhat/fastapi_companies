import asyncio
from logging.config import fileConfig

from alembic import context
from app.config import settings
from app.models import Base
from sqlalchemy import NullPool
from sqlalchemy.ext.asyncio import create_async_engine


config = context.config
config.set_main_option('sqlalchemy.url', settings.URL_DATABASE)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def include_name(name, type_, parent_names):
    """Filter out tables that are not in metadata
    so that PostGIS service tables are untouched"""
    if type_ == "table":
        return name in target_metadata.tables
    return True


def do_run_migrations(connection):
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
        include_schemas=True,
        include_name=include_name,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations():
    """Run migrations with async engine."""
    connectable = create_async_engine(
        settings.URL_DATABASE,
        poolclass=NullPool,
        echo=False
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_name=include_name,
    )

    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_async_migrations())
