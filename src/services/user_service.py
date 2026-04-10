import secrets
import string
from datetime import datetime
from typing import Optional, List, Tuple
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.models import User, Key, Transaction, Room
from loguru import logger

class UserService:
    @staticmethod
    async def get_user(session: AsyncSession, user_id: int, for_update: bool = False) -> Optional[User]:
        """Busca um usuário, opcionalmente com lock (FOR UPDATE) para evitar race conditions."""
        stmt = select(User).where(User.id == user_id)
        if for_update:
            stmt = stmt.with_for_update()
        
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_or_create_user(session: AsyncSession, user_id: int, full_name: str, username: str = None) -> User:
        user = await UserService.get_user(session, user_id)
        if not user:
            user = User(id=user_id, full_name=full_name, username=username)
            session.add(user)
            await session.commit()
            user = await UserService.get_user(session, user_id)
        else:
            # Atualiza nome/username se mudou
            if user.full_name != full_name or user.username != username:
                user.full_name = full_name
                user.username = username
                await session.commit()
        return user

    @staticmethod
    async def update_balance(session: AsyncSession, user_id: int, amount: int, trans_type: str, description: str) -> bool:
        """Atualiza o saldo do usuário com lock e registra a transação."""
        user = await UserService.get_user(session, user_id, for_update=True)
        if not user:
            return False
        
        if amount < 0 and user.balance + amount < 0:
            return False # Saldo insuficiente
            
        user.balance += amount
        
        transaction = Transaction(
            user_id=user_id,
            amount=amount,
            type=trans_type,
            description=description
        )
        session.add(transaction)
        return True

    @staticmethod
    async def get_global_stats(session: AsyncSession):
        user_count = await session.scalar(select(func.count(User.id)))
        room_count = await session.scalar(select(func.count(Room.id)))
        return user_count or 0, room_count or 0

    @staticmethod
    async def get_top_ranking(session: AsyncSession, limit: int = 5):
        # Ranking baseado em salas criadas
        stmt = (
            select(User.full_name, User.username, func.count(Room.id).label('rooms_count'))
            .join(Room, User.id == Room.user_id)
            .group_by(User.id)
            .order_by(desc('rooms_count'))
            .limit(limit)
        )
        result = await session.execute(stmt)
        return result.all()

class KeyService:
    @staticmethod
    async def generate_key(session: AsyncSession, value: int) -> str:
        # Prefixo solicitado: SALAS-ABCDE1234EFG56
        random_part = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(13))
        code = f"SALAS-{random_part}"
        
        new_key = Key(code=code, value=value)
        session.add(new_key)
        await session.commit()
        return code

    @staticmethod
    async def redeem_key(session: AsyncSession, user_id: int, code: str) -> Tuple[bool, str]:
        # Lock na chave para evitar uso duplo simultâneo
        stmt = select(Key).where(Key.code == code, Key.is_used == False).with_for_update()
        result = await session.execute(stmt)
        key = result.scalar_one_or_none()
        
        if not key:
            return False, "Key inválida ou já utilizada."
        
        # Lock no usuário para atualizar saldo
        user = await UserService.get_user(session, user_id, for_update=True)
        if not user:
            return False, "Usuário não encontrado."
            
        key.is_used = True
        key.used_by = user_id
        key.used_at = datetime.utcnow()
        
        user.balance += key.value
        
        transaction = Transaction(
            user_id=user_id,
            amount=key.value,
            type='deposit',
            description=f"Resgate de key: {code}"
        )
        session.add(transaction)
        
        await session.commit()
        return True, f"Key resgatada com sucesso! +{key.value} salas adicionadas."
