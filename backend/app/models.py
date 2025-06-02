# backend/app/models.py
from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean, JSON, DateTime
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime # Importar datetime

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_admin = Column(Boolean, default=False)

    cognitive_state = relationship("UserCognitiveState", back_populates="user", uselist=False)


class UserCognitiveState(Base):
    __tablename__ = "user_cognitive_state"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)

    # Componentes do Vetor de Estado Cognitivo (θ)
    vocabular_ability = Column(Float, default=0.0) # Capacidade vocabular estimada
    processing_speed = Column(Float, default=0.0)  # Velocidade de processamento
    working_memory_load = Column(Float, default=0.0) # Carga atual de memória operacional
    confidence_level = Column(Float, default=0.0) # Nível de confiança metacognitiva
    fatigue_factor = Column(Float, default=0.0)  # Fator de fadiga cognitiva
    domain_expertise = Column(JSON, default={}) # Expertise por domínio semântico (usando JSON)

    user = relationship("User", back_populates="cognitive_state")


class UserProgress(Base):
    __tablename__ = "user_progress"
    # id = Column(Integer, primary_key=True, index=True) # Remover ID autoincremental
    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True) # Parte da chave composta
    word_text = Column(String, index=True, nullable=False, primary_key=True) # Parte da chave composta
    exercise_type = Column(String, primary_key=True) # Adicionar tipo de exercício como parte da chave
    correct_attempts = Column(Integer, default=0)
    total_attempts = Column(Integer, default=0)
    average_time_seconds = Column(Float, default=0.0)
    last_seen_on_word = Column(DateTime, default=datetime.utcnow) # Campo para spaced repetition

# Adicionar índice único explícito para a chave composta (pode ser útil dependendo do DB)
# from sqlalchemy import UniqueConstraint
# __table_args__ = (UniqueConstraint('user_id', 'word_text', 'exercise_type'),) 

# Novo modelo para a lista de palavras mestras
class MasterWord(Base):
    __tablename__ = "master_words"

    word_text = Column(String, primary_key=True, index=True, unique=True) # A palavra em si como chave primária
    # Campos para métricas de complexidade (copiados de ComplexityBreakdownSchema)
    composite_score = Column(Float, default=0.0)
    syntactic_complexity = Column(Float, default=0.0)
    semantic_abstraction = Column(Float, default=0.0)
    morphological_density = Column(Float, default=0.0)
    # TODO: Adicionar outros campos de complexidade conforme definidos no WordComplexityAnalyzer

    # Opcional: Adicionar campos para metadados (ex: fonte, data de adição, etc.)
    # source = Column(String, nullable=True)
    # added_at = Column(DateTime, default=datetime.utcnow)

# TODO: Definir como popular esta tabela (via script, API de admin, etc.) 