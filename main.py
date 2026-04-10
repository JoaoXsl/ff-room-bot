import asyncio
import sys
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.redis import RedisStorage, Redis
from config.settings import settings
from src.handlers import user_handlers, admin_handlers
from src.database.connection import init_db
from src.middlewares.database import DatabaseMiddleware
from src.middlewares.throttling import ThrottlingMiddleware
from src.services.nix_api import nix_api
from loguru import logger

# Configuração de logs
logger.remove()
logger.add(sys.stdout, format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>")
logger.add("logs/bot.log", rotation="10 MB", retention="10 days", level="INFO")

async def main():
    logger.info("🚀 Iniciando Bot de Salas Free Fire Profissional (V19 Redis Final Fix)...")
    
    # Inicializar Banco de Dados
    try:
        await init_db()
    except Exception as e:
        logger.error(f"❌ Erro ao inicializar banco de dados: {e}")

    # Configuração de FSM Storage (Redis para Escala, Memory para Fallback)
    storage = MemoryStorage()
    
    # Prioriza REDIS_URL do Railway
    if settings.REDIS_URL:
        try:
            # Cria a instância do Redis explicitamente a partir da URL
            # Isso garante que ele não tente conectar ao localhost
            redis_instance = Redis.from_url(
                settings.REDIS_URL, 
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5
            )
            
            # Testa a conexão de forma real
            await redis_instance.ping()
            
            # Passa a instância já conectada para o RedisStorage
            storage = RedisStorage(redis=redis_instance)
            logger.info(f"✅ FSM Storage: Redis conectado com sucesso em {settings.REDIS_URL.split('@')[-1]}")
        except Exception as e:
            logger.warning(f"⚠️ FSM Storage: Falha ao conectar no Redis ({str(e)}). Usando Memória.")
    else:
        logger.info("ℹ️ FSM Storage: REDIS_URL não configurada. Usando Memória.")

    # Inicializar Bot e Dispatcher
    bot = Bot(token=settings.BOT_TOKEN)
    dp = Dispatcher(storage=storage)

    # Registrar Middlewares
    dp.update.middleware(DatabaseMiddleware())
    dp.message.middleware(ThrottlingMiddleware())

    # Registrar Handlers
    dp.include_router(user_handlers.router)
    dp.include_router(admin_handlers.router)

    # Iniciar Polling
    try:
        logger.info("🤖 Bot online e aguardando comandos.")
        await dp.start_polling(bot)
    finally:
        # Fechar cliente da API Nix de forma limpa
        await nix_api.close()
        await bot.session.close()
        # Fecha conexão com Redis se existir
        if isinstance(storage, RedisStorage):
            await storage.redis.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("👋 Bot desligado.")
