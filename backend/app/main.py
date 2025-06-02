# backend/app/main.py
from fastapi import FastAPI, Depends, Request, HTTPException, status, APIRouter
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import Optional, List
from jose import JWTError, jwt
import os
import logging

# Importações do projeto
from . import schemas, models, crud
from .database import SessionLocal, engine
from .core import security
from .core.config import ACCESS_TOKEN_EXPIRE_MINUTES, SECRET_KEY, ALGORITHM

# Importar de app_config
from .app_config import create_app_instance, STATIC_FILES_DIR

# Importar o novo router de exercícios
from .api import exercises

# Incluir o novo router de palavras
from .api import words

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

models.Base.metadata.create_all(bind=engine)

# Obter a instância da app de app_config
app = create_app_instance()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

async def get_current_user_from_token(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> models.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: Optional[str] = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = crud.get_user_by_username(db, username=username)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: models.User = Depends(get_current_user_from_token)) -> models.User:
    return current_user

async def get_current_active_admin_user(current_user: models.User = Depends(get_current_active_user)) -> models.User:
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation not permitted. Requires admin privileges."
        )
    return current_user

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=STATIC_FILES_DIR), name="static")
TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "templates")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

auth_router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])

@auth_router.post("/token", response_model=schemas.Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = crud.authenticate_user(db, username=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

app.include_router(auth_router)

user_router = APIRouter(prefix="/api/v1/users", tags=["Users"])

@user_router.post("/", response_model=schemas.User, status_code=status.HTTP_201_CREATED)
def create_new_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already registered")
    new_user = crud.create_user(db=db, user=user)
    logger.info(f"Novo usuário criado: {new_user.username}")
    return new_user

@user_router.get("/me/", response_model=schemas.User)
async def read_users_me(current_user: models.User = Depends(get_current_active_user)):
    return current_user

app.include_router(user_router)

progress_router = APIRouter(prefix="/api/v1/progress", tags=["User Progress"])

@progress_router.post("/submit_exercise/", response_model=schemas.UserProgress)
def submit_exercise_data_legacy(
    submission_payload: schemas.ExerciseSubmissionData,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    progress_create_data = schemas.UserProgressCreate(
        word_text=submission_payload.word_text,
        correct_attempts=1 if submission_payload.accuracy >= 0.5 else 0,
        total_attempts=1,
        average_time_seconds=submission_payload.time_taken_seconds
    )
    existing_progress = crud.get_user_progress_for_word(db, user_id=current_user.id, word_text=submission_payload.word_text)
    if existing_progress:
        existing_progress.total_attempts += 1
        if submission_payload.accuracy >= 0.5:
            existing_progress.correct_attempts += 1
        if submission_payload.time_taken_seconds is not None:
            if existing_progress.total_attempts > 1:
                 existing_progress.average_time_seconds = ((existing_progress.average_time_seconds * (existing_progress.total_attempts - 1)) + submission_payload.time_taken_seconds) / existing_progress.total_attempts
            else:
                 existing_progress.average_time_seconds = submission_payload.time_taken_seconds
        db.commit()
        db.refresh(existing_progress)
        logger.info(f"Progresso atualizado para o usuário {current_user.username} na palavra '{submission_payload.word_text}'")
        return existing_progress
    else:
        new_progress = crud.create_user_progress(db=db, user_progress=progress_create_data, user_id=current_user.id)
        logger.info(f"Novo progresso criado para o usuário {current_user.username} na palavra '{submission_payload.word_text}'")
        return new_progress

@progress_router.get("/me/report/", response_model=schemas.UserProgressReport)
async def get_my_progress_report_legacy(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    report_data = crud.get_user_progress_report_data(db, user_id=current_user.id)
    if not report_data or report_data.total_words_attempted_unique == 0:
        logger.info(f"Nenhum progresso encontrado para o usuário {current_user.username}, retornando relatório vazio.")
        return schemas.UserProgressReport(
            total_words_attempted_unique=0,
            overall_accuracy=0.0,
            average_time_per_attempt=0.0,
            progress_trend=[],
            message="Nenhum progresso registrado ainda."
        )
    logger.info(f"Relatório de progresso gerado para o usuário {current_user.username}")
    return report_data

app.include_router(progress_router)

admin_router = APIRouter(prefix="/api/v1/admin", tags=["Admin"])

@admin_router.post("/train_model", response_class=JSONResponse)
def trigger_model_training_legacy(
    current_admin_user: models.User = Depends(get_current_active_admin_user)
):
    logger.info(f"Usuário admin {current_admin_user.username} tentou acionar o treinamento do modelo.")
    return JSONResponse(content={"message": "Funcionalidade de treinamento do modelo em desenvolvimento."}, status_code=status.HTTP_501_NOT_IMPLEMENTED)

app.include_router(admin_router)

# Remover o router placeholder existente e incluir o novo
# exercise_router = APIRouter(prefix="/api/v1/exercises", tags=["Exercises"])
# @exercise_router.get("/next_suggestion/me", response_model=schemas.NextExerciseSuggestion)
# def get_next_exercise_legacy(...):
#    ...
# @exercise_router.get("/multiple_choice/{word_text}", response_model=schemas.MultipleChoiceExercise)
# async def get_multiple_choice_exercise_legacy(...):
#    ...
# @exercise_router.get("/drag_drop_match/", response_model=schemas.DragDropMatchExercise)
# async def get_drag_drop_exercise_legacy(...):
#    ...

app.include_router(exercises.router, prefix="/api/v1/exercises") # Incluir o novo router com prefixo

# Incluir o novo router de palavras
app.include_router(words.router, prefix="/api/v1/words") # Incluir o router de palavras com prefixo

@app.get("/app", response_class=HTMLResponse)
async def main_app_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/app/partials/mcq", response_class=HTMLResponse)
async def get_mcq_partial(request: Request):
    return templates.TemplateResponse("partials/_mcq_exercise_partial.html", {"request": request})

@app.get("/app/partials/dictation", response_class=HTMLResponse)
async def get_dictation_partial(request: Request):
    return templates.TemplateResponse("partials/_dictation_exercise_partial.html", {"request": request})

@app.get("/app/partials/drag_drop", response_class=HTMLResponse)
async def get_drag_drop_partial(request: Request):
    return templates.TemplateResponse("partials/_drag_drop_exercise_partial.html", {"request": request})

# Endpoints para os novos templates parciais de exercício
@app.get("/app/partials/mcq_image", response_class=HTMLResponse)
async def get_mcq_image_partial(request: Request):
    return templates.TemplateResponse("partials/_mcq_image_exercise_partial.html", {"request": request})

@app.get("/app/partials/define_word", response_class=HTMLResponse)
async def get_define_word_partial(request: Request):
    return templates.TemplateResponse("partials/_define_word_exercise_partial.html", {"request": request})

@app.get("/app/partials/complete_sentence", response_class=HTMLResponse)
async def get_complete_sentence_partial(request: Request):
    return templates.TemplateResponse("partials/_complete_sentence_exercise_partial.html", {"request": request})

@app.get("/", response_class=JSONResponse)
def read_root_legacy():
    logger.info("Acessada a rota raiz da API.")
    return {"message": "Bem-vindo a API do Programa Educacional Inclusivo! Versao principal de endpoints em /api/v1/"}

# Se você tiver um bloco if __name__ == "__main__": para uvicorn, mantenha-o.
# Exemplo:
# if __name__ == "__main__":
#     import uvicorn
#     # Para rodar com este arquivo como principal: uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
#     uvicorn.run(app, host="0.0.0.0", port=8000) 