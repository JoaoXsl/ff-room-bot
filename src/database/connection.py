from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from config.settings import settings
from src.database.models import Base, User, Key
from loguru import logger
import os
import ssl
from sqlalchemy import text

# 1. Tratamento da URL
db_url = settings.DATABASE_URL
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)
elif db_url.startswith("postgresql://") and "+asyncpg" not in db_url:
    db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

# 2. Caminhos dos Certificados conforme a sua imagem
# O BASE_DIR os.getcwd() pega a raiz onde está o main.py
BASE_DIR = os.getcwd() 

CA_CERT = os.path.join(BASE_DIR, "ca-certificate.crt") # Ajustado
CLIENT_CERT = os.path.join(BASE_DIR, "certificate.pem") # Ajustado
CLIENT_KEY = os.path.join(BASE_DIR, "private-key.key") # Ajustado

# Verificação extra para o log da Square Cloud
for file in [CA_CERT, CLIENT_CERT, CLIENT_KEY]:
    if not os.path.exists(file):
        logger.error(f"❌ ARQUIVO FALTANDO NA SQUARE: {file}")

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
            
            # Migração: Adicionar coluna notifications_enabled à tabela users se não existir
            result = await conn.execute(text("SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name=\'users\' AND column_name=\'notifications_enabled\')"))
            if not result.scalar():
                logger.info("Migrando: Adicionando coluna 'notifications_enabled' à tabela 'users'.")
                await conn.execute(text(f"ALTER TABLE users ADD COLUMN notifications_enabled BOOLEAN DEFAULT {User.notifications_enabled.default.arg} NOT NULL"))

            # Migração: Adicionar coluna is_removed à tabela keys se não existir
            result = await conn.execute(text("SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name=\'keys\' AND column_name=\'is_removed\')"))
            if not result.scalar():
                logger.info("Migrando: Adicionando coluna 'is_removed' à tabela 'keys'.")
                await conn.execute(text(f"ALTER TABLE keys ADD COLUMN is_removed BOOLEAN DEFAULT {Key.is_removed.default.arg} NOT NULL"))

        logger.info("✅ Banco de dados inicializado e migrações aplicadas com sucesso.")
    except Exception as e:
        logger.error(f"❌ Erro ao inicializar banco de dados ou aplicar migrações: {str(e)}")
        raise e

async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session
