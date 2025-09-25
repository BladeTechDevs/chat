# models.py - modelo ORM de SQLAlchemy
from sqlalchemy import Column, Integer, String, create_engine, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy_utils import database_exists, create_database
from config import DATABASE_URL
import datetime

# Verificar y crear la base de datos si no existe
if not database_exists(DATABASE_URL):
    create_database(DATABASE_URL)

# Crear motor de conexión
engine = create_engine(DATABASE_URL, echo=False)

# Clase base para los modelos
Base = declarative_base()

# Sesión de la base de datos
SessionLocal = sessionmaker(bind=engine)

# Modelo User
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(128), nullable=False)  # guardaremos hash
    
    # Relación con las salas creadas
    created_rooms = relationship("Room", back_populates="creator")

# Modelo Room para chat rooms
class Room(Base):
    __tablename__ = "rooms"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    room_id = Column(String(50), unique=True, nullable=False)  # ID único para compartir
    creator_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    description = Column(Text, nullable=True)
    
    # Relación con el creador
    creator = relationship("User", back_populates="created_rooms")
    
    # Relación con los miembros de la sala
    members = relationship("RoomMember", back_populates="room")

# Modelo RoomMember para trackear quién está en cada sala
class RoomMember(Base):
    __tablename__ = "room_members"
    
    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey('rooms.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    joined_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relaciones
    room = relationship("Room", back_populates="members")
    user = relationship("User")

# Crear tablas en la base de datos
Base.metadata.create_all(bind=engine)
