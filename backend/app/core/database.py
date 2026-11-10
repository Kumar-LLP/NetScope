from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from sqlalchemy import event, text
from app.core.config import settings

Base = declarative_base()

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False}
)

# Enable WAL (Write-Ahead Logging) mode in SQLite for concurrency
@event.listens_for(engine.sync_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        # Automatic schema upgrade for existing SQLite tables
        def _safe_migrate(sync_conn):
            try:
                # 1. network_devices columns
                res = sync_conn.execute(text("PRAGMA table_info(network_devices)"))
                d_cols = {row[1] for row in res.fetchall()}
                if "custom_name" not in d_cols:
                    sync_conn.execute(text("ALTER TABLE network_devices ADD COLUMN custom_name VARCHAR(128)"))
                if "notes" not in d_cols:
                    sync_conn.execute(text("ALTER TABLE network_devices ADD COLUMN notes TEXT"))
                if "category" not in d_cols:
                    sync_conn.execute(text("ALTER TABLE network_devices ADD COLUMN category VARCHAR(64) DEFAULT 'workstation'"))
                if "is_trusted" not in d_cols:
                    sync_conn.execute(text("ALTER TABLE network_devices ADD COLUMN is_trusted BOOLEAN DEFAULT 0"))

                # 2. security_findings columns
                res = sync_conn.execute(text("PRAGMA table_info(security_findings)"))
                s_cols = {row[1] for row in res.fetchall()}
                if "target" not in s_cols:
                    sync_conn.execute(text("ALTER TABLE security_findings ADD COLUMN target VARCHAR(255)"))
                if "confidence" not in s_cols:
                    sync_conn.execute(text("ALTER TABLE security_findings ADD COLUMN confidence VARCHAR(32) DEFAULT 'potential'"))
                if "acknowledged_at" not in s_cols:
                    sync_conn.execute(text("ALTER TABLE security_findings ADD COLUMN acknowledged_at DATETIME"))
                if "resolved_at" not in s_cols:
                    sync_conn.execute(text("ALTER TABLE security_findings ADD COLUMN resolved_at DATETIME"))
                if "updated_at" not in s_cols:
                    sync_conn.execute(text("ALTER TABLE security_findings ADD COLUMN updated_at DATETIME"))

                # 3. network_metrics columns
                res = sync_conn.execute(text("PRAGMA table_info(network_metrics)"))
                m_cols = {row[1] for row in res.fetchall()}
                if "interface_name" not in m_cols:
                    sync_conn.execute(text("ALTER TABLE network_metrics ADD COLUMN interface_name VARCHAR(128)"))
            except Exception:
                pass

        await conn.run_sync(_safe_migrate)
