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

# CRUD para UserProgress
def get_user_progress_for_word(db: Session, user_id: int, word_text: str):
    return db.query(models.UserProgress).filter(
        models.UserProgress.user_id == user_id,
        models.UserProgress.word_text == word_text
    ).first()

def get_user_progress_list(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.UserProgress).filter(models.UserProgress.user_id == user_id).offset(skip).limit(limit).all()

def get_latest_user_progress_list(db: Session, user_id: int, limit: int = 5):
    return db.query(models.UserProgress)\
        .filter(models.UserProgress.user_id == user_id)\
        .order_by(models.UserProgress.id.desc())\
        .limit(limit)\
        .all()

def create_or_update_user_progress(db: Session, user_id: int, word_text: str, progress_update: schemas.UserProgressCreate) -> models.UserProgress:
    db_progress = get_user_progress_for_word(db=db, user_id=user_id, word_text=word_text)
    
    if db_progress:
        db_progress.total_attempts = (db_progress.total_attempts or 0) + (progress_update.total_attempts or 0)
        db_progress.correct_attempts = (db_progress.correct_attempts or 0) + (progress_update.correct_attempts or 0)
        if progress_update.average_time_seconds is not None:
             db_progress.average_time_seconds = progress_update.average_time_seconds
    else:
        db_progress = models.UserProgress(
            user_id=user_id, 
            word_text=word_text,
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
        user_id=user_id,
        word_text=user_progress.word_text,
        correct_attempts=user_progress.correct_attempts,
        total_attempts=user_progress.total_attempts,
        average_time_seconds=user_progress.average_time_seconds
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

# Função para gerar o relatório de progresso do usuário
def get_user_progress_report_data(db: Session, user_id: int) -> Optional[schemas.UserProgressReport]:
    user_progress_records = db.query(models.UserProgress).filter(models.UserProgress.user_id == user_id).order_by(models.UserProgress.id.asc()).all()
    if not user_progress_records:
        return None
    
    total_correct_attempts_overall = 0
    total_attempts_overall = 0
    sum_of_average_times = 0.0
    num_records_with_time = 0
    unique_words_attempted = set()
    progress_trend_points = []

    for progress in user_progress_records:
        if progress.total_attempts > 0:
            total_correct_attempts_overall += progress.correct_attempts
            total_attempts_overall += progress.total_attempts
            sum_of_average_times += progress.average_time_seconds
            num_records_with_time += 1
            
        unique_words_attempted.add(progress.word_text)
        
        current_session_accuracy = (progress.correct_attempts / progress.total_attempts) if progress.total_attempts > 0 else 0.0
        
        progress_trend_points.append(schemas.ProgressPoint(
            progress_id_or_timestamp=str(progress.id),
            accuracy_at_point=current_session_accuracy, 
            cumulative_words_practiced=len(unique_words_attempted)
        ))

    overall_accuracy_val = (total_correct_attempts_overall / total_attempts_overall) if total_attempts_overall > 0 else 0.0
    average_time_per_attempt_val = (sum_of_average_times / num_records_with_time) if num_records_with_time > 0 else 0.0
    
    return schemas.UserProgressReport(
        total_words_attempted_unique=len(unique_words_attempted),
        overall_accuracy=overall_accuracy_val,
        average_time_per_attempt=average_time_per_attempt_val,
        progress_trend=progress_trend_points,
        message="Relatório de progresso gerado."
    ) 