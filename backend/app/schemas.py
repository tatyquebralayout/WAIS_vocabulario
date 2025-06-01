# backend/app/schemas.py
from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, List, Dict, Any

# Schema para o detalhamento das métricas de complexidade (usado em WordInfoResponse)
class ComplexityBreakdownSchema(BaseModel):
    lexical_length: int
    syllabic_complexity: int
    morphological_density: float
    semantic_abstraction: float
    definition_complexity: float
    # Não incluímos o composite_score aqui pois ele já está no nível principal do WordInfoResponse
    model_config = {
        "from_attributes": True
    }

# Schema para os metadados de processamento (usado em WordInfoResponse)
class ProcessingMetadataSchema(BaseModel):
    analysis_timestamp: float
    definition_available: bool
    image_available: bool
    audio_available: bool
    cache_hit: bool # Para o cache de complexidade
    complexity_method: str

    model_config = {
        "from_attributes": True
    }

# Schema de resposta ajustado para o endpoint /word_info/{word_text}
class WordInfoResponse(BaseModel):
    text: str
    definition: str
    image_url: Optional[str] = None
    audio_url: Optional[str] = None
    inferred_complexity_score: float = Field(..., description="Score de complexidade composto (0-10)")
    difficulty_level: str = Field(..., description="Rótulo de dificuldade inferido (ex: fácil, média, difícil)")
    complexity_metrics: ComplexityBreakdownSchema # Usando o novo schema para o detalhamento
    processing_metadata: ProcessingMetadataSchema # Usando o novo schema para metadados

    model_config = {
        "from_attributes": True 
    }

class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    is_admin: bool

    model_config = {
        "from_attributes": True
    }

class UserProgressBase(BaseModel):
    word_text: str # Alterado de word_id
    correct_attempts: int
    total_attempts: int
    average_time_seconds: float

class UserProgressCreate(UserProgressBase):
    pass

class UserProgress(UserProgressBase):
    id: int
    user_id: int

    model_config = {
        "from_attributes": True
    }

class WordInput(BaseModel): # Este pode ser usado para o novo endpoint se o input for um JSON
    word_text: str

class ExerciseSubmissionData(BaseModel):
    word_text: str
    accuracy: float
    time_taken_seconds: float

class NextExerciseSuggestion(BaseModel):
    suggested_word_text: Optional[str] = None # Alterado de suggested_word: Optional[Word]
    message: str

# Schemas para autenticação
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None 

# Schema para o exercício de múltipla escolha
class MultipleChoiceOption(BaseModel):
    word_text: str # Alterado de word_id
    definition: str

class MultipleChoiceExercise(BaseModel):
    target_word_text: str # target_word_id removido
    options: list[MultipleChoiceOption]
    message: Optional[str] = None

# Schemas para o Relatório de Progresso do Usuário
class WordPerformance(BaseModel):
    word_text: str
    accuracy: float
    attempts: int

class ProgressPoint(BaseModel):
    progress_id_or_timestamp: str 
    accuracy_at_point: float 
    cumulative_words_practiced: int

class UserProgressReport(BaseModel):
    total_words_attempted_unique: int
    overall_accuracy: float
    average_time_per_attempt: float
    progress_trend: list[ProgressPoint]
    message: Optional[str] = None

# Schemas para o Exercício de Arrastar e Soltar (Parear Palavra-Definição)
class DraggableItem(BaseModel):
    id: str 
    content: str 

class DropZone(BaseModel):
    id: str 
    content: str 
    correct_draggable_id: str

class DragDropMatchExercise(BaseModel):
    instruction: str
    draggable_items: list[DraggableItem]
    drop_zones: list[DropZone]
    exercise_id: str = "word_definition_match"
    message: Optional[str] = None 