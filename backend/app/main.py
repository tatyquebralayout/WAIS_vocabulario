# backend/app/main.py
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import Optional
from jose import JWTError, jwt

# Importações do projeto
from .services import dictionary_api, image_api, tts_service, ml_model
from . import schemas, models, crud
from .database import SessionLocal, engine
from .core import security # Módulo de segurança
from .core.config import ACCESS_TOKEN_EXPIRE_MINUTES, SECRET_KEY, ALGORITHM # Configurações

import os
import pandas as pd

# Criação das tabelas do banco de dados (deve ocorrer antes de qualquer operação de DB)
models.Base.metadata.create_all(bind=engine)

# Dependência para obter a sessão do DB (definida cedo para ser usada por get_current_user_from_token)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Esquema OAuth2 e dependências de autenticação
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token") # "token" é o path do nosso endpoint de login

async def get_current_user_from_token(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> models.User:
    credentials_exception = HTTPException(
        status_code=401, # HTTP_401_UNAUTHORIZED
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: Optional[str] = payload.get("sub")
        if username is None:
            raise credentials_exception
        # token_data = schemas.TokenData(username=username) # Opcional: validar com schema
    except JWTError:
        raise credentials_exception
    
    user = crud.get_user_by_username(db, username=username)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: models.User = Depends(get_current_user_from_token)) -> models.User:
    # Adicionar verificação de usuário ativo aqui se necessário (ex: current_user.is_active)
    # if not current_user.is_active:
    #     raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

# Inicialização da aplicação FastAPI (DEVE VIR DEPOIS DAS DEPENDÊNCIAS)
app = FastAPI(
    title="Programa Educacional Inclusivo",
    description="API para oferecer exercícios de vocabulário com acessibilidade.",
    version="1.0.0"
)

# Configuração do CORS 
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"], 
)

# Montar diretórios estáticos e templates
STATIC_FILES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "static")
if not os.path.exists(STATIC_FILES_DIR):
    os.makedirs(STATIC_FILES_DIR)
app.mount("/static", StaticFiles(directory=STATIC_FILES_DIR), name="static")
TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "templates")
templates = Jinja2Templates(directory=TEMPLATES_DIR)


# --- Endpoints Públicos / Sem Autenticação ---
@app.get("/")
def read_root():
    return {"message": "Bem-vindo à API do Programa Educacional Inclusivo!"}

@app.post("/token", response_model=schemas.Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = crud.authenticate_user(db, username=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token( # Usando security.create_access_token
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/users/", response_model=schemas.User) # Endpoint de criação de usuário (público)
def create_new_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    return crud.create_user(db=db, user=user)

@app.get("/word/{word_text}", response_model=schemas.WordData)
async def get_full_word_data(word_text: str, db: Session = Depends(get_db)):
    print(f"Buscando dados para a palavra: {word_text}")
    
    # Tenta buscar a palavra e sua definição no nosso DB primeiro
    db_word_obj = crud.get_word_by_text(db, text=word_text)
    definition_from_db = db_word_obj.definition if db_word_obj and db_word_obj.definition else None

    api_definition = None
    if not definition_from_db:
        word_info_from_api = dictionary_api.get_word_info(word_text)
        if not word_info_from_api:
            # Se não encontrou nem no DB (sem definição) nem na API, então 404
            if not db_word_obj: # Só 404 se a palavra não existe MESMO no nosso DB
                 raise HTTPException(status_code=404, detail=f"Palavra '{word_text}' não encontrada no dicionário externo nem no banco de dados.")
            # Se a palavra existe no DB mas sem definição, e API falhou, usamos o que temos (sem definição)
            api_definition = None 
        else:
            api_definition = word_info_from_api['definition']
            # Atualizar/criar a palavra no DB com a definição da API
            if db_word_obj:
                if not db_word_obj.definition: # Só atualiza se não tinha definição
                    crud.update_word_definition(db, word_obj=db_word_obj, definition=api_definition)
            else:
                # Palavra não existe no DB, criar com um nível de dificuldade padrão (ex: Médio)
                # ou deixar o nível de dificuldade para ser definido por um admin/processo posterior.
                # Por ora, vamos criar sem difficulty_level explícito aqui, ele pode ser None.
                # O ideal seria ter uma forma de atribuir dificuldade ao adicionar novas palavras.
                word_create_schema = schemas.WordCreate(text=word_text, definition=api_definition, difficulty_level=ml_model.DIFFICULTY_LEVELS["Médio"]) # Default para Médio
                crud.create_word(db, word=word_create_schema)
    else:
        # Usar a definição do DB
        api_definition = definition_from_db

    # Se mesmo após API e DB, não temos definição (palavra existe no DB mas sem def, e API falhou)
    # e a palavra existe no DB, retornamos os dados da palavra sem definição.
    # Se api_definition ainda é None e db_word_obj existe, word_text é válido.
    final_definition = api_definition
    if final_definition is None and db_word_obj:
        # Isso significa que a palavra está no DB, mas sem definição, e a API falhou em obter uma.
        # Não é um 404 completo, mas a definição estará ausente.
        pass # final_definition continua None
    elif final_definition is None and not db_word_obj:
        # Este caso já foi tratado pelo HTTPException acima (não achou na API e não estava no DB)
        # Mas por segurança, se chegar aqui, é um erro.
        raise HTTPException(status_code=404, detail=f"Palavra '{word_text}' não encontrada.")

    image_url_str = image_api.get_image_for_word(word_text)
    audio_url_str = tts_service.generate_audio_from_text(word_text)
    
    return schemas.WordData(
        word=word_text, # Usar o word_text da entrada, pois é o normalizado/buscado
        definition=final_definition if final_definition else "Definição não disponível.",
        image_url=image_url_str if image_url_str else None,
        audio_url=audio_url_str if audio_url_str else None
    )

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

# --- Endpoints Protegidos / Requerem Autenticação ---

@app.get("/users/me/", response_model=schemas.User)
async def read_users_me(current_user: models.User = Depends(get_current_active_user)):
    return current_user

# O endpoint /users/{user_id} é removido por agora, pois /users/me é suficiente para o usuário logado.
# Para funcionalidades de admin, seria reintroduzido com checagem de roles.

@app.post("/words/", response_model=schemas.Word)
def create_new_word(word: schemas.WordCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_active_user)):
    # Qualquer usuário logado pode criar palavras. Poderia ter roles aqui.
    db_word = crud.get_word_by_text(db, text=word.text)
    if db_word:
        raise HTTPException(status_code=400, detail=f"Word '{word.text}' already exists.")
    return crud.create_word(db=db, word=word)

@app.get("/words/text/{word_text}", response_model=schemas.Word) 
def read_word_from_db(word_text: str, db: Session = Depends(get_db)):
    # Mantido público por enquanto.
    db_word = crud.get_word_by_text(db, text=word_text)
    if db_word is None:
        raise HTTPException(status_code=404, detail=f"Word '{word_text}' not found in database.")
    return db_word

@app.post("/submit_exercise_data/", response_model=schemas.UserProgress)
def submit_exercise_data(
    submission_payload: schemas.ExerciseSubmissionData, # user_id não é mais esperado aqui diretamente
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    # O user_id vem de current_user.id
    # O submission_payload.user_id será ignorado se ainda estiver no schema (idealmente removê-lo de lá)
    db_word = crud.get_word_by_text(db, text=submission_payload.word_text)
    if not db_word:
        raise HTTPException(status_code=404, detail=f"Word '{submission_payload.word_text}' not found.")
    
    existing_progress = crud.get_user_progress_for_word(db, user_id=current_user.id, word_id=db_word.id)
    
    if existing_progress:
        existing_progress.total_attempts += 1
        if submission_payload.accuracy >= 0.5:
            existing_progress.correct_attempts += 1
        
        if existing_progress.total_attempts > 0: # Garante que não há divisão por zero
            # Recalcula a média de forma incremental
            if existing_progress.total_attempts == 1: # Se é a primeira tentativa após a criação (ou a primeira de todas)
                 existing_progress.average_time_seconds = submission_payload.time_taken_seconds
            else: # Para tentativas subsequentes
                 existing_progress.average_time_seconds = ((existing_progress.average_time_seconds * (existing_progress.total_attempts - 1)) + submission_payload.time_taken_seconds) / existing_progress.total_attempts
        else: # Caso de borda improvável
            existing_progress.average_time_seconds = submission_payload.time_taken_seconds

        db.commit()
        db.refresh(existing_progress)
        return existing_progress
    else:
        new_progress_data = schemas.UserProgressCreate(
            word_id=db_word.id,
            correct_attempts=1 if submission_payload.accuracy >= 0.5 else 0,
            total_attempts=1,
            average_time_seconds=submission_payload.time_taken_seconds
        )
        return crud.create_user_progress(db=db, user_progress=new_progress_data, user_id=current_user.id)

@app.post("/admin/train_model", response_class=JSONResponse)
def trigger_model_training(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_active_user)):
    # Idealmente, verificar se current_user é admin aqui.
    try:
        all_progress = db.query(models.UserProgress).all()
        if not all_progress:
            return JSONResponse(content={"message": "Nenhum dado de progresso para treinar."}, status_code=404)
        
        training_data = []
        for progress in all_progress:
            word = crud.get_word(db, progress.word_id)
            if not word or word.difficulty_level is None: 
                continue 
            accuracy = (progress.correct_attempts / progress.total_attempts) if progress.total_attempts > 0 else 0.0
            training_data.append({
                "accuracy": accuracy,
                "avg_time": progress.average_time_seconds,
                "word_length": len(word.text),
                "difficulty_level": word.difficulty_level 
            })
        
        if not training_data:
            return JSONResponse(content={"message": "Dados de treinamento insuficientes após filtro."}, status_code=400)
        
        df_train = pd.DataFrame(training_data)
        trained_model_path_or_obj = ml_model.train_model(df_train) # train_model retorna o caminho ou objeto do modelo
        
        if trained_model_path_or_obj is not None:
            # A função ml_model.train_model já imprime logs, então aqui só confirmamos.
            # Se MODEL_FILE_PATH é uma constante em ml_model, podemos usá-la.
            return JSONResponse(content={"message": "Modelo treinado com sucesso!", "model_info": str(trained_model_path_or_obj)})
        else:
            return JSONResponse(content={"message": "Falha no treinamento do modelo (dados insuficientes ou <2 classes)."}, status_code=500)
    except Exception as e:
        # Logar o erro e retornar uma mensagem genérica
        print(f"Erro durante o treinamento do modelo: {str(e)}") # Log para o servidor
        raise HTTPException(status_code=500, detail=f"Erro interno durante o treinamento do modelo.")

@app.get("/next_exercise/me", response_model=schemas.NextExerciseSuggestion)
def get_next_exercise(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_active_user)):
    NUM_RECENT_PROGRESS = 5
    DEFAULT_ACCURACY = 0.75
    DEFAULT_AVG_TIME = 10.0
    MIN_ATTEMPTS_FOR_MASTERY = 3
    MIN_ACCURACY_FOR_MASTERY = 0.8 # 80%
    TARGET_DIFFICULTY_NAME = "Médio"
    TARGET_DIFFICULTY_LEVEL = ml_model.DIFFICULTY_LEVELS[TARGET_DIFFICULTY_NAME]

    # 1. Calcular desempenho médio do usuário com base nos N últimos progressos
    recent_progress_list = crud.get_latest_user_progress_list(db, user_id=current_user.id, limit=NUM_RECENT_PROGRESS)
    
    user_avg_accuracy = DEFAULT_ACCURACY
    user_avg_time = DEFAULT_AVG_TIME
    last_word_id_attempted = None

    if recent_progress_list:
        total_accuracy_sum = 0
        total_time_sum = 0
        valid_progress_count = 0
        for prog in recent_progress_list:
            if prog.total_attempts > 0:
                total_accuracy_sum += (prog.correct_attempts / prog.total_attempts)
                total_time_sum += prog.average_time_seconds
                valid_progress_count += 1
        if valid_progress_count > 0:
            user_avg_accuracy = total_accuracy_sum / valid_progress_count
            user_avg_time = total_time_sum / valid_progress_count
        if recent_progress_list: # Pega o ID da última palavra tentada da lista ordenada
            last_word_id_attempted = recent_progress_list[0].word_id

    # 2. Obter todas as palavras candidatas e filtrar
    all_words_in_db = crud.get_words(db, limit=1000) # Limitar para performance
    if not all_words_in_db:
        return schemas.NextExerciseSuggestion(message="Nenhuma palavra no DB para sugerir.", suggested_word=None)

    candidate_words = []
    for word_obj in all_words_in_db:
        if word_obj.difficulty_level is None: # Pular palavras sem nível de dificuldade base
            continue
        if last_word_id_attempted and word_obj.id == last_word_id_attempted:
            continue # Não sugerir a última palavra tentada imediatamente

        # Verificar se a palavra foi "dominada"
        progress_on_word = crud.get_user_progress_for_word(db, user_id=current_user.id, word_id=word_obj.id)
        if progress_on_word:
            if progress_on_word.total_attempts >= MIN_ATTEMPTS_FOR_MASTERY and \
               (progress_on_word.correct_attempts / progress_on_word.total_attempts) >= MIN_ACCURACY_FOR_MASTERY:
                continue # Pular palavra dominada
        
        candidate_words.append(word_obj)

    if not candidate_words:
        # Se todas as palavras foram dominadas ou filtradas, tentar um fallback menos restritivo
        # Por exemplo, pegar uma palavra aleatória não dominada, mesmo que seja a última.
        # Ou simplesmente informar que não há novas palavras adequadas no momento.
        # Para este passo, vamos usar a lógica de fallback mais abaixo será acionada
        pass # A lógica de fallback mais abaixo será acionada

    # 3. Iterar sobre as palavras candidatas, prever dificuldade e selecionar
    best_candidate = None
    best_candidate_predicted_level = -1
    potential_fallback_candidates = [] # Para palavras que batem com o nível inerente

    for word_obj in candidate_words: # Iterar sobre as já filtradas
        performance_features = {
            "accuracy": user_avg_accuracy,
            "avg_time": user_avg_time,
            "word_length": len(word_obj.text)
        }
        predicted_difficulty = ml_model.predict_difficulty(performance_features)

        if predicted_difficulty == TARGET_DIFFICULTY_LEVEL:
            # Priorizar palavras com menos tentativas, se várias se encaixarem no alvo
            if best_candidate is None:
                best_candidate = word_obj
                best_candidate_predicted_level = predicted_difficulty
            else:
                # Lógica de desempate: preferir a com menos tentativas anteriores
                current_best_progress = crud.get_user_progress_for_word(db, user_id=current_user.id, word_id=best_candidate.id)
                new_candidate_progress = crud.get_user_progress_for_word(db, user_id=current_user.id, word_id=word_obj.id)
                
                attempts_current_best = current_best_progress.total_attempts if current_best_progress else 0
                attempts_new_candidate = new_candidate_progress.total_attempts if new_candidate_progress else 0

                if attempts_new_candidate < attempts_current_best:
                    best_candidate = word_obj
                    best_candidate_predicted_level = predicted_difficulty
            # Não dar break aqui, para permitir encontrar a com menos tentativas
        
        # Coletar para fallback, se o nível previsto bater com o nível inerente da palavra
        # e não for "Fácil" (a menos que SÓ haja fáceis)
        elif predicted_difficulty == word_obj.difficulty_level and \
             word_obj.difficulty_level != ml_model.DIFFICULTY_LEVELS["Fácil"]:
            potential_fallback_candidates.append((word_obj, predicted_difficulty))
    
    # Se encontramos um candidato ideal (nível alvo previsto)
    if best_candidate:
        return schemas.NextExerciseSuggestion(
            suggested_word=schemas.Word.model_validate(best_candidate),
            message=f"Palavra sugerida (prev: {ml_model.REVERSE_DIFFICULTY_LEVELS.get(best_candidate_predicted_level, 'N/A')}, alvo: {TARGET_DIFFICULTY_NAME})."
        )
    
    # Se não, tentar o fallback de nível correspondente (não fácil)
    if potential_fallback_candidates:
        # Ordenar fallbacks por menos tentativas
        potential_fallback_candidates.sort(key=lambda item: (crud.get_user_progress_for_word(db, user_id=current_user.id, word_id=item[0].id).total_attempts if crud.get_user_progress_for_word(db, user_id=current_user.id, word_id=item[0].id) else 0))
        fallback_word_obj, fallback_pred_level = potential_fallback_candidates[0]
        return schemas.NextExerciseSuggestion(
            suggested_word=schemas.Word.model_validate(fallback_word_obj),
            message=f"Fallback: Palavra com nível previsto ({ml_model.REVERSE_DIFFICULTY_LEVELS.get(fallback_pred_level, 'N/A')}) correspondente ao seu nível inerente."
        )

    # Fallback final: pegar qualquer palavra não dominada das candidatas, ou a primeira da lista geral se candidatas estiver vazia
    final_fallback_word = None
    if candidate_words: # Se ainda houver candidatas (ex: todas eram fáceis e o alvo era médio)
        # Ordenar por menos tentativas
        candidate_words.sort(key=lambda w: (crud.get_user_progress_for_word(db, user_id=current_user.id, word_id=w.id).total_attempts if crud.get_user_progress_for_word(db, user_id=current_user.id, word_id=w.id) else 0))
        final_fallback_word = candidate_words[0]
    else: # Se candidate_words estava vazia (ex: todas dominadas ou só a última tentada)
          # Tentar qualquer palavra da DB que não seja a última tentada (sem filtro de domínio)
        non_dominated_or_last_options = [w for w in all_words_in_db if (not last_word_id_attempted or w.id != last_word_id_attempted)]
        if non_dominated_or_last_options:
            # Ordenar por menos tentativas totais globais (ou aleatório)
            non_dominated_or_last_options.sort(key=lambda w: (crud.get_user_progress_for_word(db, user_id=current_user.id, word_id=w.id).total_attempts if crud.get_user_progress_for_word(db, user_id=current_user.id, word_id=w.id) else 0))
            final_fallback_word = non_dominated_or_last_options[0]

    if final_fallback_word:
         return schemas.NextExerciseSuggestion(
            suggested_word=schemas.Word.model_validate(final_fallback_word),
            message="Fallback: Sugerindo palavra alternativa com base na disponibilidade."
        )

    return schemas.NextExerciseSuggestion(message="Não foi possível sugerir uma próxima palavra no momento. Tente adicionar mais palavras ou variar seus exercícios!", suggested_word=None)

@app.get("/exercise/multiple_choice/{word_text}", response_model=schemas.MultipleChoiceExercise)
async def get_multiple_choice_exercise(
    word_text: str, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_active_user)
):
    num_distractors = 3 # Número de opções falsas

    target_word_obj = crud.get_word_by_text(db, text=word_text)
    if not target_word_obj or not target_word_obj.definition:
        # Se a palavra alvo não existe ou não tem definição, tentar buscar/criar via get_full_word_data
        # Isso garantirá que a definição seja buscada e salva se possível.
        try:
            await get_full_word_data(word_text, db) # Chama para popular/atualizar o DB
            target_word_obj = crud.get_word_by_text(db, text=word_text) # Tenta buscar novamente
            if not target_word_obj or not target_word_obj.definition:
                 raise HTTPException(status_code=404, detail=f"Palavra alvo '{word_text}' não encontrada ou sem definição após tentativa de busca.")
        except HTTPException as e:
            # Re-lançar a exceção se get_full_word_data já lançou (ex: palavra não existe em lugar nenhum)
            raise e 

    correct_option = schemas.MultipleChoiceOption(word_id=target_word_obj.id, definition=target_word_obj.definition)
    
    distractor_words = crud.get_random_words_with_definitions(db, exclude_word_id=target_word_obj.id, limit=num_distractors)
    
    if len(distractor_words) < num_distractors:
        # Não ideal, mas o exercício ainda pode ser gerado com menos opções
        # Poderia retornar uma mensagem indicando isso, ou lançar erro se for crítico ter N opções
        pass 

    options = [correct_option]
    for dw in distractor_words:
        options.append(schemas.MultipleChoiceOption(word_id=dw.id, definition=dw.definition))
    
    import random
    random.shuffle(options)

    return schemas.MultipleChoiceExercise(
        target_word_text=target_word_obj.text,
        target_word_id=target_word_obj.id,
        options=options,
        message=f"Selecione a definição correta para '{target_word_obj.text}'."
    )

@app.get("/users/me/progress_report/", response_model=schemas.UserProgressReport)
async def get_my_progress_report(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    report_data = crud.get_user_progress_report_data(db, user_id=current_user.id)
    if not report_data:
        # Retornar um relatório vazio ou uma mensagem indicando que não há dados
        return schemas.UserProgressReport(
            total_words_attempted_unique=0,
            overall_accuracy=0.0,
            average_time_per_attempt=0.0,
            progress_trend=[],
            message="Nenhum dado de progresso encontrado para gerar um relatório."
        )
    return report_data

@app.get("/exercise/drag_drop_match/", response_model=schemas.DragDropMatchExercise)
async def get_drag_drop_exercise(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user) # Proteger endpoint
):
    num_pairs_for_exercise = 4 # Quantos pares palavra-definição
    exercise_data = crud.get_drag_drop_word_definition_data(db, num_pairs=num_pairs_for_exercise)
    if not exercise_data:
        raise HTTPException(
            status_code=404, 
            detail=f"Não há dados suficientes para gerar um exercício de arrastar e soltar com {num_pairs_for_exercise} pares."
        )
    return exercise_data

# Para rodar (da pasta backend/): uvicorn app.main:app --reload
# Lembre-se que após adicionar 'hashed_password' ao modelo User, 
# você precisará deletar o app_data.db existente para que a nova coluna seja criada,
# ou usar um sistema de migração como Alembic. 