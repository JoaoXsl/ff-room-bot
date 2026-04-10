from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from src.services.user_service import UserService, KeyService
from src.database.models import User, Key, Room
from src.utils.keyboards import get_admin_menu, get_back_button
from config.settings import settings
from loguru import logger

router = Router()

class AdminStates(StatesGroup):
    waiting_for_gen_key = State()
    waiting_for_user_id = State()
    waiting_for_adj_balance = State()

def is_admin(user_id: int) -> bool:
    return user_id in settings.ADMIN_IDS

@router.message(Command("admin"))
async def cmd_admin(message: types.Message):
    if not is_admin(message.from_user.id):
        return
    
    await message.answer(
        "🛠️ <b>PAINEL ADMINISTRATIVO</b>\n\nBem-vindo ao controle central do bot.",
        reply_markup=get_admin_menu(),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "admin_gen_key")
async def admin_start_gen_key(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id): return
    
    await callback.message.edit_text(
        "🔑 <b>GERAR KEYS</b>\n\nEnvie a quantidade e o saldo no formato: <code>quantidade saldo</code>\nExemplo: <code>5 10</code> (Gera 5 keys de 10 salas cada)",
        reply_markup=get_back_button(),
        parse_mode="HTML"
    )
    await state.set_state(AdminStates.waiting_for_gen_key)

@router.message(AdminStates.waiting_for_gen_key)
async def admin_process_gen_key(message: types.Message, state: FSMContext, session: AsyncSession):
    if not is_admin(message.from_user.id): return
    
    try:
        parts = message.text.split()
        if len(parts) != 2:
            raise ValueError
            
        amount = int(parts[0])
        balance = int(parts[1])
        
        if amount <= 0 or amount > 50:
            await message.answer("❌ Quantidade deve ser entre 1 e 50.")
            return
            
        keys = []
        for _ in range(amount):
            key_code = await KeyService.generate_key(session, balance)
            keys.append(f"<code>{key_code}</code>")
        
        await session.commit()
        
        keys_text = "\n".join(keys)
        await message.answer(
            f"✅ <b>{amount} KEYS GERADAS (Saldo: {balance})</b>\n\n{keys_text}\n\n<i>Clique no código acima para copiar.</i>",
            reply_markup=get_admin_menu(),
            parse_mode="HTML"
        )
        await state.clear()
    except Exception as e:
        logger.error(f"Erro ao gerar keys: {e}")
        await message.answer("❌ Formato inválido. Use: <code>quantidade saldo</code>", reply_markup=get_back_button())

@router.callback_query(F.data == "admin_users")
async def admin_start_user_lookup(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id): return
    
    await callback.message.edit_text(
        "👥 <b>CONSULTAR USUÁRIO</b>\n\nEnvie o <b>ID do Telegram</b> do usuário:",
        reply_markup=get_back_button(),
        parse_mode="HTML"
    )
    await state.set_state(AdminStates.waiting_for_user_id)

@router.message(AdminStates.waiting_for_user_id)
async def admin_process_user_lookup(message: types.Message, state: FSMContext, session: AsyncSession):
    if not is_admin(message.from_user.id): return
    
    try:
        target_id = int(message.text.strip())
        user = await UserService.get_user(session, target_id)
        
        if not user:
            await message.answer("❌ Usuário não encontrado no banco de dados.", reply_markup=get_back_button())
            return
            
        # Estatísticas do usuário
        rooms_count = await session.scalar(select(func.count(Room.id)).where(Room.user_id == target_id))
        
        text = (
            "👤 <b>DADOS DO USUÁRIO</b>\n\n"
            f"ID: <code>{user.id}</code>\n"
            f"Nome: <b>{user.full_name}</b>\n"
            f"Username: @{user.username or 'N/A'}\n"
            f"Saldo: <b>{user.balance} salas</b>\n"
            f"Salas Criadas: <b>{rooms_count or 0}</b>\n"
            f"Cadastrado em: {user.created_at.strftime('%d/%m/%Y %H:%M')}"
        )
        
        await message.answer(text, reply_markup=get_admin_menu(), parse_mode="HTML")
        await state.clear()
    except ValueError:
        await message.answer("❌ ID inválido. Envie apenas números.", reply_markup=get_back_button())

@router.message(Command("gerarkey"))
async def cmd_gerarkey(message: types.Message, session: AsyncSession):
    if not is_admin(message.from_user.id):
        logger.warning(f"Usuário {message.from_user.id} tentou usar /gerarkey sem permissão.")
        return
    
    try:
        args = message.text.split()
        if len(args) != 3:
            await message.answer("❌ Use: <code>/gerarkey (quantidade) (saldo)</code>", parse_mode="HTML")
            return
            
        amount = int(args[1])
        balance = int(args[2])
        
        if amount <= 0 or amount > 50:
            await message.answer("❌ Quantidade deve ser entre 1 e 50.")
            return
            
        keys = []
        for _ in range(amount):
            key_code = await KeyService.generate_key(session, balance)
            keys.append(f"<code>{key_code}</code>")
            
        await session.commit()
        
        await message.answer(f"✅ <b>{amount} Keys Geradas (Saldo: {balance}):</b>\n\n" + "\n".join(keys) + "\n\n<i>Clique no código acima para copiar.</i>", parse_mode="HTML")
    except Exception as e:
        logger.error(f"Erro no comando /gerarkey: {e}")
        await message.answer(f"❌ Erro ao processar o comando. Verifique os parâmetros.")
