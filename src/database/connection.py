from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from config.settings import settings
from src.database.models import Base
from loguru import logger
import ssl # Import ssl module

# Criar um contexto SSL que desabilita a verificação de certificado
# Isso é necessário para lidar com certificados autoassinados da Square Cloud
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

# Configuração do Engine com Pool de Conexões Robusto para Alta Escala
# pool_size: 20 conexões fixas abertas
# max_overflow: permite abrir até +30 conexões extras em picos (total 50)
# pool_recycle: recicla conexões a cada 30 min para evitar timeouts do banco
# pool_pre_ping: verifica se a conexão está viva antes de usar (evita Connection Reset)
engine = create_async_engine(
    settings.DATABASE_URL, 
    echo=False,
    pool_size=20,
    max_overflow=30,
    pool_recycle=1800,
    pool_pre_ping=True,
    connect_args={
        "server_settings": {"application_name": "FF_Room_Bot"},
        "command_timeout": 30,
        "ssl": ssl_context # Usar o contexto SSL personalizado
    }
)

async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def init_db():
    """Inicializa o banco de dados e cria as tabelas se não existirem."""
    try:
        async with engine.begin() as conn:
            # Em produção, usaríamos Alembic. Para este bot pronto para revenda, 
            # garantimos que as tabelas existam ao iniciar.
            await conn.run_sync(Base.metadata.create_all)
        logger.info("✅ Banco de dados inicializado com sucesso.")
    except Exception as e:
        logger.error(f"❌ Erro ao inicializar banco de dados: {str(e)}")
        raise e

async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session
