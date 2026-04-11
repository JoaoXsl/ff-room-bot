from datetime import datetime
from typing import List, Optional
from sqlalchemy import BigInteger, String, DateTime, ForeignKey, Integer, Boolean, Index
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[Optional[str]] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(255))
    balance: Mapped[int] = mapped_column(Integer, default=0)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    notifications_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # lazy="noload" para evitar queries implícitas pesadas; carregar explicitamente quando necessário
    keys: Mapped[List["Key"]] = relationship(back_populates="user", lazy="noload")
    transactions: Mapped[List["Transaction"]] = relationship(back_populates="user", lazy="noload")
    rooms: Mapped[List["Room"]] = relationship(back_populates="user", lazy="noload")

class Key(Base):
    __tablename__ = "keys"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    value: Mapped[int] = mapped_column(Integer) # Quantidade de salas/saldo
    is_used: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    is_removed: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    used_by: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("users.id"), index=True)
    used_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    user: Mapped[Optional["User"]] = relationship(back_populates="keys")

    # Índice composto para busca rápida de chaves disponíveis
    __table_args__ = (
        Index('idx_key_code_unused', 'code', 'is_used'),
    )

class Transaction(Base):
    __tablename__ = "transactions"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), index=True)
    amount: Mapped[int] = mapped_column(Integer)
    type: Mapped[str] = mapped_column(String(50)) # 'deposit', 'usage', 'refund', 'admin_adjustment'
    description: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    
    user: Mapped["User"] = relationship(back_populates="transactions")

class Room(Base):
    __tablename__ = "rooms"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), index=True)
    session_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    room_id: Mapped[Optional[int]] = mapped_column(BigInteger, unique=True, index=True)
    room_name: Mapped[str] = mapped_column(String(255))
    password: Mapped[str] = mapped_column(String(50))
    config_type: Mapped[str] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(50), index=True) # 'active', 'expired', 'released'
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    
    user: Mapped["User"] = relationship(back_populates="rooms")
