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
    logger.info("🚀 Iniciando Bot de Salas Free Fire Profissional (V35 Square Cloud Final)...")
    
    # Inicializar Banco de Dados
    await init_db()

    # Configuração de FSM Storage (Redis para Escala, Memory para Fallback)
    storage = MemoryStorage()
    
    if settings.REDIS_URL:
        try:
            # Configuração robusta para Redis na Square Cloud
            # rediss:// força SSL, mas precisamos desabilitar a verificação de certificado
            redis_instance = Redis.from_url(
                settings.REDIS_URL, 
                decode_responses=True,
                socket_timeout=10,
                socket_connect_timeout=10,
                ssl_cert_reqs=None # Ignorar verificação SSL para Square Cloud
            )
            
            # Testa a conexão
            await redis_instance.ping()
            
            storage = RedisStorage(redis=redis_instance)
            logger.info(f"✅ FSM Storage: Redis conectado com sucesso.")
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
        # Fechar conexões de forma limpa
        await nix_api.close()
        await bot.session.close()
        if isinstance(storage, RedisStorage):
            await storage.redis.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("👋 Bot desligado.")
