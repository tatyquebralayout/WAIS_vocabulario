# backend/app/crud.py
from sqlalchemy.orm import Session
from . import models, schemas
from .core.security import get_password_hash, verify_password
from typing import Optional

# CRUD para User
def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = models.User(username=user.username, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def authenticate_user(db: Session, username: str, password: str) -> Optional[models.User]:
    user = get_user_by_username(db, username=username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

# CRUD para Word
def get_word(db: Session, word_id: int):
    return db.query(models.Word).filter(models.Word.id == word_id).first()

def get_word_by_text(db: Session, text: str):
    return db.query(models.Word).filter(models.Word.text == text).first()

def get_words(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Word).offset(skip).limit(limit).all()

def create_word(db: Session, word: schemas.WordCreate) -> models.Word:
    db_word = models.Word(
        text=word.text,
        difficulty_level=word.difficulty_level,
        definition=word.definition
    )
    db.add(db_word)
    db.commit()
    db.refresh(db_word)
    return db_word

# Função para atualizar uma palavra existente, especialmente a definição
def update_word_definition(db: Session, word_obj: models.Word, definition: str) -> models.Word:
    word_obj.definition = definition
    db.commit()
    db.refresh(word_obj)
    return word_obj

def get_random_words_with_definitions(db: Session, exclude_word_id: Optional[int], limit: int = 3) -> list[models.Word]:
    query = db.query(models.Word).filter(models.Word.definition.isnot(None))
    if exclude_word_id is not None:
        query = query.filter(models.Word.id != exclude_word_id)
    
    # SQLAlchemy não tem um random() portável simples para todas as DBs direto no ORM query.
    # Uma forma é buscar todos, depois selecionar aleatoriamente. 
    # Para DBs maiores, isso é ineficiente.
    # Para SQLite, pode-se usar `from sqlalchemy.sql.expression import func` e `func.random()` na ordenação
    # from sqlalchemy.sql.expression import func
    # query = query.order_by(func.random()).limit(limit)
    # Por simplicidade e portabilidade inicial, vamos pegar mais e escolher no Python (cuidado com performance em DBs grandes)
    
    all_eligible_words = query.all()
    import random
    random.shuffle(all_eligible_words)
    return all_eligible_words[:limit]

# Função para buscar dados para exercício de Arrastar e Soltar (Palavra-Definição)
def get_drag_drop_word_definition_data(db: Session, num_pairs: int = 4) -> Optional[schemas.DragDropMatchExercise]:
    words_with_defs = db.query(models.Word).filter(models.Word.definition.isnot(None)).all()
    
    if len(words_with_defs) < num_pairs:
        return None # Não há palavras suficientes para criar o exercício

    import random
    selected_words = random.sample(words_with_defs, num_pairs)

    draggable_items_list = []
    drop_zones_list = []

    for word_obj in selected_words:
        # Usar o ID da palavra como string para os IDs dos itens e zonas
        word_id_str = str(word_obj.id)
        
        draggable_items_list.append(schemas.DraggableItem(
            id=word_id_str, # O ID do item arrastável é o ID da palavra (pois é a definição dela)
            content=word_obj.definition
        ))
        drop_zones_list.append(schemas.DropZone(
            id=word_id_str, # O ID da zona é o ID da palavra
            content=word_obj.text,
            correct_draggable_id=word_id_str # A zona da palavra X espera a definição da palavra X
        ))
    
    random.shuffle(draggable_items_list) # Embaralhar as definições
    # As palavras (drop_zones) podem ou não ser embaralhadas, dependendo do design do exercício.
    # Por agora, vamos manter a ordem das palavras (selected_words) e embaralhar apenas as definições.
    # Se quiser embaralhar as zonas também: random.shuffle(drop_zones_list)

    return schemas.DragDropMatchExercise(
        instruction="Arraste cada definição para a palavra correta.",
        draggable_items=draggable_items_list,
        drop_zones=drop_zones_list
    )

# CRUD para UserProgress
def get_user_progress_for_word(db: Session, user_id: int, word_id: int):
    return db.query(models.UserProgress).filter(
        models.UserProgress.user_id == user_id,
        models.UserProgress.word_id == word_id
    ).first()

def get_user_progress_list(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.UserProgress).filter(models.UserProgress.user_id == user_id).offset(skip).limit(limit).all()

def get_latest_user_progress_list(db: Session, user_id: int, limit: int = 5):
    return db.query(models.UserProgress)\
        .filter(models.UserProgress.user_id == user_id)\
        .order_by(models.UserProgress.id.desc())\
        .limit(limit)\
        .all()

def create_or_update_user_progress(db: Session, user_id: int, word_id: int, progress_update: schemas.UserProgressCreate) -> models.UserProgress:
    db_progress = get_user_progress_for_word(db=db, user_id=user_id, word_id=word_id)
    
    if db_progress:
        # Atualiza o progresso existente
        db_progress.total_attempts = (db_progress.total_attempts or 0) + (progress_update.total_attempts or 0)
        db_progress.correct_attempts = (db_progress.correct_attempts or 0) + (progress_update.correct_attempts or 0)
        # Lógica mais complexa para average_time_seconds pode ser necessária
        # Por exemplo, média ponderada ou apenas sobrescrever se fornecido.
        if progress_update.average_time_seconds is not None:
             db_progress.average_time_seconds = progress_update.average_time_seconds
    else:
        # Cria um novo registro de progresso
        db_progress = models.UserProgress(
            user_id=user_id, 
            word_id=word_id,
            total_attempts=progress_update.total_attempts or 0,
            correct_attempts=progress_update.correct_attempts or 0,
            average_time_seconds=progress_update.average_time_seconds or 0.0
        )
        db.add(db_progress)
    
    db.commit()
    db.refresh(db_progress)
    return db_progress

def create_user_progress(db: Session, user_progress: schemas.UserProgressCreate, user_id: int):
    db_item = models.UserProgress(
        **user_progress.model_dump(), 
        user_id=user_id
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

# Função para gerar o relatório de progresso do usuário
def get_user_progress_report_data(db: Session, user_id: int) -> Optional[schemas.UserProgressReport]:
    user_progress_records = db.query(models.UserProgress).filter(models.UserProgress.user_id == user_id).order_by(models.UserProgress.id.asc()).all()

    if not user_progress_records:
        return None # Ou um relatório vazio

    total_correct_attempts_overall = 0
    total_attempts_overall = 0
    sum_of_average_times = 0.0
    num_records_with_time = 0
    
    unique_word_ids_attempted = set()
    progress_trend_points = []
    cumulative_correct_for_trend = 0
    cumulative_attempts_for_trend = 0

    for i, progress in enumerate(user_progress_records):
        if progress.total_attempts > 0:
            total_correct_attempts_overall += progress.correct_attempts
            total_attempts_overall += progress.total_attempts
            sum_of_average_times += progress.average_time_seconds # Assumindo que average_time_seconds é por palavra
            num_records_with_time += 1
        
        unique_word_ids_attempted.add(progress.word_id)

        # Para o gráfico de tendência
        # Aqui, estamos recalculando a acurácia cumulativa a cada ponto. 
        # Isso pode ser simplificado ou tornado mais granular dependendo do que queremos mostrar.
        # Este cálculo de "accuracy_at_point" pode ser pesado se muitos registros. 
        # Uma alternativa é a acurácia daquela sessão/palavra específica, ou acurácia dos últimos N.
        # Por agora, vamos fazer uma acurácia geral até aquele ponto.
        
        # Vamos redefinir o cálculo do progress_trend para ser mais simples:
        # Acurácia da tentativa específica e número de palavras únicas tentadas até o momento.
        # Ou melhor, vamos pegar a acurácia da *sessão* (UserProgress individual)
        current_session_accuracy = (progress.correct_attempts / progress.total_attempts) if progress.total_attempts > 0 else 0.0
        progress_trend_points.append(schemas.ProgressPoint(
            progress_id_or_timestamp=progress.id, # Usando ID como "tempo"
            accuracy_at_point=current_session_accuracy, 
            cumulative_words_practiced=len(unique_word_ids_attempted) # Número de palavras únicas vistas até este ponto
        ))

    overall_accuracy_val = (total_correct_attempts_overall / total_attempts_overall) if total_attempts_overall > 0 else 0.0
    # A média de tempo aqui é a média dos "average_time_seconds" de cada registro de UserProgress.
    # Se um UserProgress é para uma única palavra e múltiplas tentativas, average_time_seconds já é a média para aquela palavra.
    # Esta métrica pode precisar de refinamento dependendo do significado exato desejado.
    average_time_per_attempt_val = (sum_of_average_times / num_records_with_time) if num_records_with_time > 0 else 0.0

    # TODO: Implementar lógica para top_challenging_words e top_mastered_words se desejado
    # Isso envolveria iterar pelos progressos, agrupar por palavra, calcular acurácia por palavra, etc.

    return schemas.UserProgressReport(
        total_words_attempted_unique=len(unique_word_ids_attempted),
        overall_accuracy=overall_accuracy_val,
        average_time_per_attempt=average_time_per_attempt_val,
        progress_trend=progress_trend_points,
        message="Relatório de progresso gerado."
    ) 