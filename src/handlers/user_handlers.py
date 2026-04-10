import asyncio
import time
from datetime import datetime
from aiogram import Router, F, types
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from src.services.user_service import UserService, KeyService
from src.services.nix_api import nix_api
from src.utils.keyboards import (
    get_main_menu, get_back_button, get_time_config_keyboard, 
    get_mode_selection_keyboard, get_room_control_keyboard, get_config_menu
)
from src.database.connection import async_session
from src.database.models import Room
from sqlalchemy import select
from loguru import logger

router = Router()

class UserStates(StatesGroup):
    waiting_for_key = State()
    waiting_for_room_pass = State()
    waiting_for_room_time = State()
    waiting_for_kick_uid = State()

MODE_MAPPING = {
    "ap_padrao": "4x4 Padrão Apostado",
    "gelo_inf": "1x1 Gel Infinito",
    "tatico": "🛡️ Tático"
}

async def get_global_panel_text(session: AsyncSession):
    user_count, room_count = await UserService.get_global_stats(session)
    top_ranking = await UserService.get_top_ranking(session)
    
    now = datetime.now().strftime("%H:%M:%S")
    
    ranking_text = ""
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
    for i, rank in enumerate(top_ranking):
        name = rank.full_name
        if rank.username:
            name = f"@{rank.username}"
        ranking_text += f"{medals[i]} {name} - {rank.rooms_count} salas criadas\n"
    
    if not ranking_text:
        ranking_text = "<i>Nenhuma sala criada ainda.</i>\n"

    text = (
        "🟢 <b>SALAS FF — PAINEL GLOBAL</b>\n\n"
        "Sistema de salas automáticas.\n\n"
        f"🕐 Atualizado às <b>{now}</b>\n\n"
        f"👥 Usuários: <b>{user_count}</b>\n"
        f"🎮 Salas Criadas: <b>{room_count}</b>\n"
        f"🔌 API: 🟢 <b>Online</b>\n\n"
        "🏆 <b>Top 5 Ranking</b>\n"
        f"{ranking_text}\n"
        "⚡ <i>Clique nos botões abaixo para interagir</i>"
    )
    return text

@router.message(CommandStart())
async def cmd_start(message: types.Message, session: AsyncSession):
    await UserService.get_or_create_user(
        session, 
        message.from_user.id, 
        message.from_user.full_name, 
        message.from_user.username
    )
    
    text = await get_global_panel_text(session)
    await message.answer(text, reply_markup=get_main_menu(), parse_mode="HTML")

@router.callback_query(F.data == "main_menu")
async def back_to_main(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    # Não limpamos o estado aqui para manter a senha e o tempo salvos
    text = await get_global_panel_text(session)
    try:
        await callback.message.edit_text(text, reply_markup=get_main_menu(), parse_mode="HTML")
    except Exception:
        await callback.answer()

@router.callback_query(F.data == "ranking")
async def show_ranking(callback: types.CallbackQuery, session: AsyncSession):
    top_ranking = await UserService.get_top_ranking(session, limit=10)
    
    ranking_text = "🏆 <b>TOP 10 RANKING GLOBAL</b>\n\n"
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    for i, rank in enumerate(top_ranking):
        name = rank.full_name
        if rank.username:
            name = f"@{rank.username}"
        ranking_text += f"{medals[i]} {name} - {rank.rooms_count} salas\n"
    
    if not top_ranking:
        ranking_text += "<i>Nenhuma sala criada ainda.</i>"
        
    await callback.message.edit_text(ranking_text, reply_markup=get_back_button(), parse_mode="HTML")

@router.callback_query(F.data == "balance")
async def show_balance(callback: types.CallbackQuery, session: AsyncSession):
    user = await UserService.get_user(session, callback.from_user.id)
    balance = user.balance if user else 0
    
    text = (
        "💰 <b>SEU SALDO</b>\n\n"
        f"Você possui: <b>{balance} salas</b>\n\n"
        "Adquira mais keys para continuar criando salas."
    )
    await callback.message.edit_text(text, reply_markup=get_back_button(), parse_mode="HTML")

@router.callback_query(F.data == "config_menu")
async def show_config_menu(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "⚙️ <b>CONFIGURAÇÕES</b>\n\nAjuste as preferências das suas salas abaixo:",
        reply_markup=get_config_menu(),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "free_trial")
async def show_free_trial(callback: types.CallbackQuery):
    await callback.answer("🎁 Teste grátis disponível em breve!", show_alert=True)

# --- CONFIGURAÇÃO DE SENHA ---
@router.callback_query(F.data == "config_pass")
async def start_config_pass(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    current_pass = data.get("room_pass", "123456")
    
    await callback.message.edit_text(
        f"🔐 <b>CONFIGURAR SENHA</b>\n\nSenha atual: <code>{current_pass}</code>\n\nEnvie a nova senha para suas salas:",
        reply_markup=get_back_button(),
        parse_mode="HTML"
    )
    await state.set_state(UserStates.waiting_for_room_pass)

@router.message(UserStates.waiting_for_room_pass)
async def process_new_pass(message: types.Message, state: FSMContext):
    new_pass = message.text.strip()
    if len(new_pass) > 20:
        await message.answer("❌ A senha deve ter no máximo 20 caracteres.", reply_markup=get_back_button())
        return
        
    await state.update_data(room_pass=new_pass)
    await message.answer(f"✅ Senha atualizada para: <code>{new_pass}</code>", reply_markup=get_main_menu(), parse_mode="HTML")
    await state.set_state(None)

# --- CONFIGURAÇÃO DE TEMPO ---
@router.callback_query(F.data == "config_time")
async def show_time_config(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    current_time = data.get("room_time", 3)
    
    text = (
        "⚙️ <b>CONFIG TIME</b>\n\n"
        f"<b>Auto-start: {current_time} minutos</b>\n\n"
        "Tempo para iniciar a partida automaticamente após criar a sala."
    )
    await callback.message.edit_text(text, reply_markup=get_time_config_keyboard(current_time), parse_mode="HTML")

@router.callback_query(F.data.startswith("time_adj_"))
async def set_room_time(callback: types.CallbackQuery, state: FSMContext):
    new_time = int(callback.data.replace("time_adj_", ""))
    if new_time < 1: new_time = 1
    if new_time > 7: new_time = 7
    
    await state.update_data(room_time=new_time)
    
    text = (
        "⚙️ <b>CONFIG TIME</b>\n\n"
        f"<b>Auto-start: {new_time} minutos</b>\n\n"
        "Tempo para iniciar a partida automaticamente após criar a sala."
    )
    try:
        await callback.message.edit_text(text, reply_markup=get_time_config_keyboard(new_time), parse_mode="HTML")
    except Exception:
        await callback.answer()

# --- RESGATE DE KEY ---
@router.callback_query(F.data == "add_key")
async def start_add_key(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "🎟️ <b>RESGATAR KEY</b>\n\nEnvie o código da sua key (Ex: SALAS-XXXXX):",
        reply_markup=get_back_button(),
        parse_mode="HTML"
    )
    await state.set_state(UserStates.waiting_for_key)

@router.message(UserStates.waiting_for_key)
async def process_key(message: types.Message, state: FSMContext, session: AsyncSession):
    code = message.text.strip()
    success, msg = await KeyService.redeem_key(session, message.from_user.id, code)
    
    if success:
        await message.answer(f"✅ {msg}", reply_markup=get_main_menu())
        await state.set_state(None) # Limpa apenas o estado de espera da key
    else:
        await message.answer(f"❌ {msg}\n\nTente novamente ou clique em voltar.", reply_markup=get_back_button())

# --- CRIAÇÃO DE SALA ---
@router.callback_query(F.data == "create_room_start")
async def start_create_room(callback: types.CallbackQuery, session: AsyncSession):
    user = await UserService.get_user(session, callback.from_user.id)
    
    if not user or user.balance <= 0:
        await callback.answer("❌ Você não possui saldo suficiente!", show_alert=True)
        return

    text = "🎮 <b>SELECIONE O MODO</b>"
    await callback.message.edit_text(text, reply_markup=get_mode_selection_keyboard(), parse_mode="HTML")

@router.callback_query(F.data.startswith("create_mode_"))
async def process_create_room_final(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    user_id = callback.from_user.id
    
    async with async_session() as db_session:
        success = await UserService.update_balance(
            db_session, user_id, -1, 'usage', "Criação de sala"
        )
        if not success:
            await callback.answer("❌ Saldo insuficiente!", show_alert=True)
            return
        await db_session.commit()

    mode_code = callback.data.replace("create_mode_", "")
    mode_name = MODE_MAPPING.get(mode_code, mode_code)
    
    data = await state.get_data()
    password = data.get("room_pass", "123456")
    time_delay = data.get("room_time", 3)
    
    await callback.message.answer("🎮 <b>Selecione o Modo para a próxima sala:</b>", 
                                  reply_markup=get_mode_selection_keyboard(), 
                                  parse_mode="HTML")
    
    processing_msg = await callback.message.edit_text("⏳ <b>Iniciando criação ultra-rápida...</b>", parse_mode="HTML")
    
    asyncio.create_task(
        background_room_creation(
            callback.message.bot, user_id, processing_msg.message_id, 
            password, time_delay, mode_code, mode_name
        )
    )

async def background_room_creation(bot, user_id, message_id, password, time_delay, mode_code, mode_name):
    start_time = time.time()
    try:
        room_data = await nix_api.create_room(
            password=password, start_delay=time_delay,
            config_type=mode_code, room_name=f"Sala FF"
        )
        
        session_id = room_data.get('session_id')
        if not session_id:
            raise Exception("API Error: Session ID not found")

        for i in range(120):
            status_data = await nix_api.get_room_status(session_id)
            if status_data and status_data.get("status") == "active" and status_data.get("room_id"):
                await deliver_room(bot, user_id, message_id, status_data, session_id, mode_name, time_delay, start_time)
                return
            await asyncio.sleep(1.5)
            
        raise Exception("Timeout na criação da sala.")

    except Exception as e:
        logger.error(f"Erro: {str(e)}")
        async with async_session() as db_session:
            await UserService.update_balance(db_session, user_id, 1, 'refund', "Falha na criação")
            await db_session.commit()
        try:
            await bot.edit_message_text(f"❌ <b>Erro ao criar sala.</b>\nSeu saldo foi reembolsado.", 
                                        chat_id=user_id, message_id=message_id, 
                                        reply_markup=get_back_button(), parse_mode="HTML")
        except: pass

async def deliver_room(bot, user_id, message_id, room_data, session_id, mode_name, time_delay, start_time):
    room_id = room_data.get("room_id")
    total_time = round(time.time() - start_time, 2)

    async with async_session() as db_session:
        new_room = Room(
            user_id=user_id, session_id=session_id, room_id=room_id,
            room_name="Sala FF", password=room_data['password'],
            config_type=mode_name, status="active"
        )
        db_session.add(new_room)
        await db_session.commit()

    text = (
        "✅ <b>SALA CRIADA COM SUCESSO!</b>\n\n"
        f"🆔 ID: <code>{room_id}</code>\n"
        f"🔐 Senha: <code>{room_data['password']}</code>\n"
        f"🎮 Modo: <b>{mode_name}</b>\n"
        f"⏱ Tempo: <b>{time_delay} min</b>\n\n"
        f"🔗 <b>Link de Convite:</b>\n{room_data['invite_link']}\n\n"
        f"⚡ <i>Criada em {total_time}s</i>"
    )
    
    await bot.edit_message_text(text, chat_id=user_id, message_id=message_id, 
                                reply_markup=get_room_control_keyboard(session_id), parse_mode="HTML")

# --- CONTROLES DE SALA ---
@router.callback_query(F.data.startswith("room_kick_"))
async def start_kick_player(callback: types.CallbackQuery, state: FSMContext):
    session_id = callback.data.replace("room_kick_", "")
    await state.update_data(kick_session_id=session_id)
    await callback.message.answer("🚫 <b>Expulsar Jogador</b>\n\nEnvie o <b>UID</b> do jogador:", parse_mode="HTML")
    await state.set_state(UserStates.waiting_for_kick_uid)

@router.message(UserStates.waiting_for_kick_uid)
async def process_kick_uid(message: types.Message, state: FSMContext):
    uid = message.text.strip()
    data = await state.get_data()
    session_id = data.get("kick_session_id")
    
    if not uid.isdigit():
        await message.answer("❌ UID inválido.")
        return
        
    success = await nix_api.kick_player(session_id, uid)
    if success:
        await message.answer(f"✅ Expulsão enviada para UID: <code>{uid}</code>", parse_mode="HTML")
    else:
        await message.answer("❌ Erro ao expulsar.")
    await state.set_state(None)

@router.callback_query(F.data.startswith("room_start_"))
async def process_start_room(callback: types.CallbackQuery):
    session_id = callback.data.replace("room_start_", "")
    success = await nix_api.start_room(session_id)
    if success:
        await callback.answer("🚀 Sala iniciada!", show_alert=True)
    else:
        await callback.answer("❌ Erro ao iniciar.", show_alert=True)
