from sqlalchemy import Column, Integer, String, Float, Text, create_engine, ForeignKey, DateTime, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    user_id = Column(BigInteger, primary_key=True)
    exp = Column(Integer, default=0)
    level = Column(Integer, default=1)
    Money = Column(Integer, default=0)
    last_daily_claim = Column(String(20), default='2000-01-01')
    ATK = Column(Integer, default=5)
    SPD = Column(Integer, default=5)
    DEF = Column(Integer, default=5)
    DEX = Column(Integer, default=5)
    CRIT = Column(Integer, default=5)
    MDMG = Column(Integer, default=5)
    HP = Column(Integer, default=100)
    MP = Column(Integer, default=50)
    inventory_slots = Column(Integer, default=10)
    equipped_weapon = Column(String(100), nullable=True)
    equipped_armor = Column(String(100), nullable=True)
    dice_rolls_today = Column(Integer, default=0)
    last_dice_reset = Column(String(20), default='2000-01-01')
    last_fight_time = Column(Float, default=0.0)
    hunt_count_today = Column(Integer, default=0)
    last_hunt_reset = Column(String(20), default='2000-01-01')

class Inventory(Base):
    __tablename__ = 'inventory'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False, index=True)
    item_name = Column(String(100), nullable=False)
    quantity = Column(Integer, default=0)

class Item(Base):
    __tablename__ = 'items'
    
    item_id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    type = Column(String(50), nullable=False)
    price = Column(Integer, default=0)
    bonus_atk = Column(Integer, default=0)
    bonus_def = Column(Integer, default=0)
    bonus_spd = Column(Integer, default=0)
    bonus_dex = Column(Integer, default=0)
    bonus_crit = Column(Integer, default=0)
    bonus_mdmg = Column(Integer, default=0)
    bonus_hp = Column(Integer, default=0)
    bonus_mp = Column(Integer, default=0)


class Role(Base):
    __tablename__ = 'roles'
    
    role_id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)
    price = Column(Integer, default=0)
    description = Column(Text, nullable=True)
    color = Column(String(7), default='#000000')  # Hex color code
    created_at = Column(DateTime, default=datetime.utcnow)
    is_buy = Column(Integer, default=1)
    
    # Relationship dengan user_roles
    users = relationship("UserRole", back_populates="role")

class UserRole(Base):
    __tablename__ = 'user_roles'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('users.user_id'), nullable=False)
    role_id = Column(BigInteger, ForeignKey('roles.role_id'), nullable=False)
    purchased_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Integer, default=1)  # 1 = active, 0 = inactive
    
    # Relationships
    role = relationship("Role", back_populates="users")
    
    # Composite unique constraint untuk mencegah duplikasi
    __table_args__ = (
        {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4'},
    )

class ShiftConfig(Base):
    __tablename__ = 'shift_config'
    
    guild_id = Column(BigInteger, primary_key=True)
    duration_minutes = Column(Integer, default=60)
    required_role_ids = Column(Text, default='')
    reward_money = Column(Integer, default=1000)
    reward_exp = Column(Integer, default=100)
    shift_detail = Column(Text, default='Shift Standar Harian')
    max_participants = Column(Integer, default=0)

class ActiveShift(Base):
    __tablename__ = 'active_shifts'
    
    user_id = Column(BigInteger, primary_key=True)
    start_time = Column(Float, nullable=False)
    end_time = Column(Float, nullable=False)
    reward_money = Column(Integer, nullable=False)
    reward_exp = Column(Integer, nullable=False)
    shift_detail = Column(Text, default='Shift Standar')


def get_mysql_url():
    host = os.getenv('MYSQL_HOST', 'localhost')
    port = os.getenv('MYSQL_PORT', '3306')
    user = os.getenv('MYSQL_USER', 'root')
    password = os.getenv('MYSQL_PASSWORD', '')
    database = os.getenv('MYSQL_DATABASE', 'aethbotgame')
    return f"mysql+mysqlconnector://{user}:{password}@{host}:{port}/{database}"

def get_engine():
    return create_engine(get_mysql_url(), pool_pre_ping=True)

def get_session():
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    return Session()

def create_all_tables():
    engine = get_engine()
    Base.metadata.create_all(engine)
