from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from config.settings import settings
from src.database.models import Base
from loguru import logger
import ssl

def get_ssl_context():
    """
    Cria um contexto SSL para o asyncpg.
    Na Square Cloud, os certificados são autoassinados, então desabilitamos a verificação.
    """
    # Se a URL contiver 'localhost' ou '127.0.0.1', provavelmente é local e não precisa de SSL
    if "localhost" in settings.DATABASE_URL or "127.0.0.1" in settings.DATABASE_URL:
        return None
        
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx

# Configuração do Engine com Pool de Conexões Robusto
engine = create_async_engine(
    settings.DATABASE_URL, 
    echo=False,
    pool_size=10,
    max_overflow=20,
    pool_recycle=1800,
    pool_pre_ping=True,
    connect_args={
        "server_settings": {"application_name": "FF_Room_Bot"},
        "command_timeout": 60,
        "ssl": get_ssl_context()
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
        # Não levantamos o erro aqui para permitir que o bot tente iniciar 
        # mesmo se o banco falhar momentaneamente (o middleware tratará depois)

async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session
