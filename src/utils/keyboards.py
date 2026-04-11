from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup

def get_main_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    # Linha 1: Resgatar key | Saldo | Ranking
    builder.button(text="🎟️ Resgatar Key", callback_data="add_key")
    builder.button(text="💰 Saldo", callback_data="balance")
    builder.button(text="🏆 Ranking", callback_data="ranking")
    
    # Linha 2: Configurar | Teste Grátis | Atualizar
    builder.button(text="⚙️ Configurar", callback_data="config_menu")
    builder.button(text="🎁 Teste Grátis", callback_data="free_trial")
    builder.button(text="🔄 Atualizar", callback_data="main_menu")
    
    # Linha 3: Criar Sala (Destaque)
    builder.button(text="🎮 CRIAR SALA AGORA", callback_data="create_room_start")
    
    builder.adjust(3, 3, 1)
    return builder.as_markup()

def get_config_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🔐 Config Senha", callback_data="config_pass")
    builder.button(text="⏱ Config Time", callback_data="config_time")
    builder.button(text="« Voltar", callback_data="main_menu")
    builder.adjust(2, 1)
    return builder.as_markup()

def get_mode_selection_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="💥 4x4 Padrão Apostado", callback_data="create_mode_ap_padrao")
    builder.button(text="⚔️ 1x1 Gel Infinito", callback_data="create_mode_gelo_inf")
    builder.button(text="🛡️ Tático", callback_data="create_mode_tatico")
    builder.button(text="« Voltar", callback_data="main_menu")
    builder.adjust(1)
    return builder.as_markup()

def get_room_control_keyboard(session_id: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🚀 Iniciar Sala", callback_data=f"room_start_{session_id}")
    builder.button(text="🚫 Expulsar Jogador", callback_data=f"room_kick_{session_id}")
    builder.button(text="« Voltar", callback_data="main_menu")
    builder.adjust(2, 1)
    return builder.as_markup()

def get_time_config_keyboard(current_time: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="➖", callback_data=f"time_adj_{current_time - 1}")
    builder.button(text=f"⏱ {current_time} min", callback_data="ignore")
    builder.button(text="➕", callback_data=f"time_adj_{current_time + 1}")
    builder.button(text="« Voltar", callback_data="config_menu")
    builder.adjust(3, 1)
    return builder.as_markup()

def get_admin_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🔑 Gerar Key", callback_data="admin_gen_key")
    builder.button(text="👥 Usuários", callback_data="admin_users")
    builder.button(text="💰 Ajustar Saldo", callback_data="admin_adj_balance")
    builder.button(text="📜 Logs Gerais", callback_data="admin_logs")
    builder.button(text="🏠 Menu Principal", callback_data="main_menu")
    builder.adjust(2, 2, 1)
    return builder.as_markup()

def get_back_button() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="« Voltar", callback_data="main_menu")
    return builder.as_markup()
