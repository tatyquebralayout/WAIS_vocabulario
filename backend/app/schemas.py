# backend/app/schemas.py
from pydantic import BaseModel, HttpUrl
from typing import Optional

class WordBase(BaseModel):
    text: str
    difficulty_level: Optional[int] = None # Permitir que seja opcional na base
    definition: Optional[str] = None # Adicionar definição

class WordCreate(WordBase):
    difficulty_level: int # Exigir ao criar, ou definir um padrão se apropriado
    definition: Optional[str] = None # Permitir opcional na criação, será preenchido depois

class Word(WordBase):
    id: int
    difficulty_level: Optional[int] # Pode ser None se nullable=True no modelo
    definition: Optional[str] = None # Adicionar definição também aqui
    # Se você for incluir definição, imagem e áudio direto do DB para este schema,
    # adicione os campos aqui. Por ora, vou manter simples como no seu exemplo.

    class Config:
        from_attributes = True

class WordData(BaseModel):
    word: str
    definition: str
    image_url: Optional[HttpUrl] = None # Mantido como HttpUrl se vier de uma URL externa válida
    audio_url: Optional[str] = None    # Alterado para str, pois é um caminho/URL relativa gerada localmente

    # Não precisa de orm_mode aqui se não for diretamente de um objeto ORM completo com todos esses campos

class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str # Campo para a senha em texto plano na criação

class User(UserBase):
    id: int
    # items: list[Item] = [] # Exemplo se houvesse relação com Itens

    class Config:
        from_attributes = True

class UserProgressBase(BaseModel):
    correct_attempts: Optional[int] = 0
    total_attempts: Optional[int] = 0
    average_time_seconds: Optional[float] = 0.0

class UserProgressCreate(UserProgressBase):
    word_id: int # Necessário ao criar um progresso
    # user_id será pego do usuário autenticado, por exemplo

class UserProgress(UserProgressBase):
    id: int
    user_id: int
    word_id: int
    word: Word # Para mostrar informações da palavra no progresso

    class Config:
        from_attributes = True

class WordInput(BaseModel):
    word_text: str

class ExerciseSubmissionData(BaseModel):
    user_id: int
    word_text: str
    accuracy: float  # Ex: 0.0 a 1.0 (ou 0 para incorreto, 1 para correto)
    time_taken_seconds: float # Tempo que o usuário levou para responder

class NextExerciseSuggestion(BaseModel):
    suggested_word: Optional[Word] = None
    message: str

# Schemas para autenticação
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None 

# Schema para o exercício de múltipla escolha
class MultipleChoiceOption(BaseModel):
    word_id: int # Para identificar a palavra se necessário, mas não mostrar ao usuário
    definition: str

class MultipleChoiceExercise(BaseModel):
    target_word_text: str
    target_word_id: int
    options: list[MultipleChoiceOption] # Incluirá a definição correta + N incorretas, embaralhadas
    message: Optional[str] = None 

# Schemas para o Relatório de Progresso do Usuário
class WordPerformance(BaseModel):
    word_text: str
    accuracy: float
    total_attempts: int
    average_time: float

class ProgressPoint(BaseModel):
    # Para simplicidade, usaremos o ID do progresso como uma espécie de "tempo"
    # Em um sistema real, seria melhor ter um timestamp no UserProgress
    progress_id_or_timestamp: int 
    accuracy_at_point: float
    cumulative_words_practiced: int

class UserProgressReport(BaseModel):
    total_words_attempted_unique: int
    overall_accuracy: float
    average_time_per_attempt: float # Média de todos os average_time_seconds dos UserProgress
    progress_trend: list[ProgressPoint] = []
    # top_challenging_words: list[WordPerformance] = [] # Palavras com menor acurácia
    # top_mastered_words: list[WordPerformance] = [] # Palavras com alta acurácia e múltiplas tentativas
    message: Optional[str] = None 

# Schemas para o Exercício de Arrastar e Soltar (Parear Palavra-Definição)
class DraggableItem(BaseModel): # Item que será arrastado (ex: uma definição)
    id: str # Um ID único para o item arrastável (pode ser o word_id se for uma definição)
    content: str # O texto da definição

class DropZone(BaseModel): # Zona onde o item será solto (ex: uma palavra)
    id: str # Um ID único para a zona (o word_id)
    content: str # O texto da palavra
    correct_draggable_id: str # O ID do DraggableItem que pertence aqui

class DragDropMatchExercise(BaseModel):
    exercise_id: str = "word_definition_match" # Tipo de exercício
    instruction: str
    draggable_items: list[DraggableItem] # Lista de definições (embaralhadas)
    drop_zones: list[DropZone] # Lista de palavras (ordem fixa ou embaralhada)
    message: Optional[str] = None 