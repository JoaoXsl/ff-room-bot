from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from config.settings import settings
from src.database.models import Base
from loguru import logger
import os

# Garante que a URL do banco de dados use o driver asyncpg, corrigindo o erro de driver síncrono.
db_url = settings.DATABASE_URL
if db_url.startswith("postgres://"):
    db_url = f"postgresql+asyncpg://{db_url[len("postgres://"):]}"
elif db_url.startswith("postgresql://"):
    db_url = f"postgresql+asyncpg://{db_url[len("postgresql://"):]}"

# Define os caminhos para os certificados SSL
# Assumimos que os arquivos ca.crt, client.crt e client.key estão na raiz do projeto
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CA_CERT_PATH = os.path.join(os.path.dirname(BASE_DIR), "ca.crt")
CLIENT_CERT_PATH = os.path.join(os.path.dirname(BASE_DIR), "client.crt")
CLIENT_KEY_PATH = os.path.join(os.path.dirname(BASE_DIR), "client.key")

# Configuração do Engine com Pool de Conexões Robusto e certificados SSL
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
        "sslmode": "require",
        "sslrootcert": CA_CERT_PATH,
        "sslcert": CLIENT_CERT_PATH,
        "sslkey": CLIENT_KEY_PATH
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
