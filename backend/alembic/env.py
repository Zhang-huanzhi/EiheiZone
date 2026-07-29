from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool

from app.core.config import get_settings
from app.db.base import Base
import app.modules.auth.models  # noqa: F401  # Register Auth tables with Base.metadata.
import app.modules.posts.models  # noqa: F401  # Register Post tables with Base.metadata.
import app.modules.qas.models  # noqa: F401  # Register QA tables with Base.metadata.
import app.modules.expenditures.models  # noqa: F401  # Register Expenditure tables.


config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


target_metadata = Base.metadata


def get_database_url() -> str:
    """Select the configured development or explicitly requested test database."""

    database = context.get_x_argument(as_dictionary=True).get("database")
    settings = get_settings()

    if database is None:
        return settings.database_url
    if database == "test" and settings.test_database_url is not None:
        return settings.test_database_url
    if database == "test":
        raise RuntimeError("TEST_DATABASE_URL is required for test migrations")

    message = "Only '-x database=test' is supported for Alembic migrations"
    raise ValueError(message)


def run_migrations_offline() -> None:
    """Generate migration SQL without opening a database connection."""

    context.configure(
        url=get_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations against the selected database."""

    connectable = create_engine(get_database_url(), poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
