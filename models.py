# # models.py - modelo ORM de SQLAlchemy
# from sqlalchemy import Column, Integer, String
# from sqlalchemy.ext.declarative import declarative_base
# from sqlalchemy.orm import sessionmaker
# from sqlalchemy import create_engine
# from config import DATABASE_URL

# Base = declarative_base()
# engine = create_engine(DATABASE_URL, echo=False)
# SessionLocal = sessionmaker(bind=engine)

# class User(Base):
#     __tablename__ = "users"
    
#     id = Column(Integer, primary_key=True, index=True)
#     username = Column(String(50), unique=True, nullable=False)
#     password = Column(String(128), nullable=False)  # guardaremos hash

# # Crear tablas si no existen
# Base.metadata.create_all(bind=engine)

# models.py - modelo ORM de SQLAlchemy

from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import database_exists, create_database
from config import DATABASE_URL

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

# Crear tablas en la base de datos
Base.metadata.create_all(bind=engine)
