from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from config.settings import settings
from src.database.models import Base
from loguru import logger
import os
import ssl

# 1. Tratamento da URL
db_url = settings.DATABASE_URL
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)
elif db_url.startswith("postgresql://") and "+asyncpg" not in db_url:
    db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

# 2. Caminhos dos Certificados (Ajustados para a raiz da aplicação na Square)
# Se os arquivos estiverem na raiz do seu projeto, use este caminho:
BASE_DIR = os.getcwd() 
CA_CERT = os.path.join(BASE_DIR, "ca.crt")
CLIENT_CERT = os.path.join(BASE_DIR, "client.crt")
CLIENT_KEY = os.path.join(BASE_DIR, "client.key")

# 3. Configuração do Contexto SSL para Asyncpg
def get_ssl_context():
    ctx = ssl.create_default_context(cafile=CA_CERT)
    # Carrega o certificado do cliente e a chave privada
    ctx.load_cert_chain(certfile=CLIENT_CERT, keyfile=CLIENT_KEY)
    # Como é autoassinado, desativamos a verificação de hostname se necessário
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_REQUIRED # O servidor exige o certificado
    return ctx

# 4. Criação do Engine
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
        "ssl": get_ssl_context() # Passamos o contexto completo aqui
    }
)

async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def init_db():
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