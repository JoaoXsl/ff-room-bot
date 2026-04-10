from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from config.settings import settings
from src.database.models import Base
from loguru import logger
import os
import ssl # Importação necessária para o SSL

# Garante que a URL do banco de dados use o driver asyncpg
db_url = settings.DATABASE_URL
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)
elif db_url.startswith("postgresql://") and "+asyncpg" not in db_url:
    db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

# Configuração do contexto SSL para Asyncpg
# Isso resolve o erro de [SSL: CERTIFICATE_VERIFY_FAILED]
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

# Configuração do Engine
engine = create_async_engine(
    db_url, 
    echo=False,
    pool_size=10,
    max_overflow=20,
    pool_recycle=1800,
    pool_pre_ping=True,
    connect_args={
        "server_settings": {"application_name": "FF_Room_Bot"},
        "command_timeout": 60,
        "ssl": ssl_context  # Aqui está a mudança chave!
    }
)

async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def init_db():
    """Inicializa o banco de dados e cria as tabelas se não existirem."""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("✅ Banco de dados inicializado com sucesso.")
    except Exception as e:
        logger.error(f"❌ Erro ao inicializar banco de dados: {str(e)}")
        raise e

async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session