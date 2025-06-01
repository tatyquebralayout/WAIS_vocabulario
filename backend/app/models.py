# backend/app/models.py
from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String) # Campo para a senha hasheada
    # Adicionar mais campos se houver sistema de login

class Word(Base):
    __tablename__ = "words"
    id = Column(Integer, primary_key=True, index=True)
    text = Column(String, unique=True, index=True, nullable=False)
    difficulty_level = Column(Integer, nullable=True) # Armazena o ID do nível, ex: 0 para Fácil, 1 para Médio, 2 para Difícil
    definition = Column(String, nullable=True) # Novo campo para armazenar a definição
    
    progress = relationship("UserProgress", back_populates="word")

class UserProgress(Base):
    __tablename__ = "user_progress"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    word_id = Column(Integer, ForeignKey("words.id"))
    correct_attempts = Column(Integer, default=0)
    total_attempts = Column(Integer, default=0)
    average_time_seconds = Column(Float, default=0.0) 

    # Relacionamento com Word
    word = relationship("Word", back_populates="progress")
    # Você também pode querer um relacionamento com User aqui, se necessário:
    # user = relationship("User", back_populates="progress_entries") # E adicionar 'progress_entries' em User 