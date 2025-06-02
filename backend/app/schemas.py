# backend/app/schemas.py
from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, List, Dict, Any
from datetime import datetime # Importar datetime separadamente

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
    cognitive_state: Optional['UserCognitiveState'] = None # Adicionar relacionamento opcional

    model_config = {
        "from_attributes": True
    }

class UserProgressBase(BaseModel):
    word_text: str # Alterado de word_id
    exercise_type: str # Adicionar o tipo de exercício à base
    correct_attempts: int
    total_attempts: int
    average_time_seconds: float
    last_seen_on_word: datetime # Adicionar o novo campo

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
    exercise_type: str # Adicionar o tipo de exercício
    accuracy: float
    time_taken_seconds: float
    word_complexity_score: float = Field(..., description="Score de complexidade composto (0-10) da palavra do exercício")
    complexity_metrics: ComplexityBreakdownSchema # Métricas detalhadas da complexidade da palavra

class NextExerciseSuggestion(BaseModel):
    suggested_word_text: Optional[str] = None # Alterado de suggested_word: Optional[Word]
    suggested_exercise_type: Optional[str] = None # Adicionar o tipo de exercício sugerido
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

# Novo schema para exercício de Múltipla Escolha (Imagem)
class MultipleChoiceImageExercise(BaseModel):
    target_word_text: str
    image_url: str
    options: list[MultipleChoiceOption] # Reutiliza as opções de texto
    message: Optional[str] = None

# Novo schema para exercício de Definir Palavra
class DefineWordExercise(BaseModel):
    target_word_text: str
    # A definição correta não é incluída aqui para não dar a resposta no frontend.
    # A comparação será feita no backend na submissão.
    message: Optional[str] = None

# Novo schema para exercício de Completar Frase
class CompleteSentenceExercise(BaseModel):
    target_word_text: str
    sentence_with_placeholder: str # Ex: "A [____] está no jardim."
    # A palavra correta também não é incluída aqui.
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

# Schemas para o Estado Cognitivo do Usuário
class UserCognitiveStateBase(BaseModel):
    vocabular_ability: float = Field(default=0.0)
    processing_speed: float = Field(default=0.0)
    working_memory_load: float = Field(default=0.0)
    confidence_level: float = Field(default=0.0)
    fatigue_factor: float = Field(default=0.0)
    domain_expertise: Dict[str, Any] = Field(default_factory=dict)

class UserCognitiveState(UserCognitiveStateBase):
    id: int
    user_id: int

    model_config = {
        "from_attributes": True
    }

User.model_rebuild() 

# Schemas para o modelo MasterWord (lista de palavras mestras)
class MasterWordBase(BaseModel):
    word_text: str
    composite_score: float
    syntactic_complexity: float
    semantic_abstraction: float
    morphological_density: float
    # TODO: Adicionar outros campos de complexidade e metadados conforme o modelo MasterWord

class MasterWord(MasterWordBase):
    # No futuro, pode adicionar campos específicos do DB aqui, como 'id' se usarmos um ID.
    # Mas como word_text é a PK, talvez não precise de um ID separado no schema.
    # Por enquanto, manter simples.

    model_config = {
        "from_attributes": True
    }

# Estrutura para representar um candidato a exercício
class ExerciseCandidate(BaseModel): # Herdar de BaseModel para compatibilidade com Pydantic/schemas
    word_text: str
    exercise_type: str # Usar str para o tipo de exercício. Se for um Enum, mudar aqui.
    word_complexity_score: float
    complexity_metrics: ComplexityBreakdownSchema
    difficulty: float # A dificuldade calculada

    # O método _calculate_exercise_difficulty não é um método de BaseModel, movê-lo para onde é usado ou recalcular
    # Se a dificuldade for calculada na criação do candidato no serviço, o schema apenas a armazena.

    # Se a dificuldade precisa ser calculada com base nos dados no schema, pode ser uma computed_field ou @property
    # Por enquanto, assumir que é calculada externamente e armazenada.

    # Adicionar campos para os scores calculados (serão definidos dinamicamente no serviço, mas bom para visualização/depuração)
    learning_efficiency_score: float = 0.0
    engagement_factor_score: float = 0.0
    frustration_risk_score: float = 0.0
    final_composite_score: float = 0.0

    model_config = {
        "from_attributes": True
    } 