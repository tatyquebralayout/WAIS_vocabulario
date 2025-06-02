from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List, Optional

from .. import crud, models, schemas
from ..dependencies import get_db, get_current_active_user # get_current_user foi renomeado
from ..services.word_info_service import WordInfoService # Importar o serviço de informação da palavra
from ..services.word_complexity_analyzer import WordComplexityAnalyzer # Importar o analisador de complexidade

import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Mover o endpoint /word/{word_text} para este router (originalmente em word_info_endpoint.py)
@router.get("/word/{word_text}", response_model=schemas.WordInfoResponse)
async def get_word_info(word_text: str, request: Request, db: Session = Depends(get_db)):
    """
    Obtém informações detalhadas (definição, complexidade, etc.) para uma palavra.
    Este endpoint é público (não requer autenticação).
    """
    word_complexity_analyzer = WordComplexityAnalyzer() # Inicializar o analisador
    # Passar request.url_for para o WordInfoService construir URLs estáticas (áudio)
    word_info_service = WordInfoService(db=db, complexity_analyzer=word_complexity_analyzer, current_request_base_url=str(request.base_url), current_app_url_path_for=request.app.url_path_for) # Passar DB session e request info

    try:
        word_info = await word_info_service.get_word_info(word_text)
        if not word_info:
             raise HTTPException(status_code=404, detail=f"Palavra '{word_text}' não encontrada ou sem informações essenciais.")
        return word_info
    except HTTPException as e:
        # Re-raise HTTPExceptions para que FastAPI as trate corretamente
        raise e
    except Exception as e:
        logger.error(f"Erro ao obter informações para a palavra '{word_text}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Erro interno do servidor ao buscar informações da palavra.")

# Esqueleto para o endpoint /learn/
@router.get("/learn/", response_model=List[schemas.WordInfoResponse]) # Definir schema de resposta como lista de WordInfoResponse (simplificado)
async def get_words_to_learn(
    level: Optional[str] = None, # Parâmetro de nível opcional (do frontend)
    limit: int = 10, # Limite de palavras a retornar
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user) # Requer autenticação
):
    """
    Endpoint para obter uma lista de palavras para o usuário aprender, opcionalmente filtradas por nível.
    """
    user_id = current_user.id
    user_state = crud.get_user_cognitive_state(db, user_id) # Precisamos do estado do usuário para a zona proximal

    if not user_state:
         # Lidar com usuário sem estado cognitivo
         logger.warning(f"Usuário {user_id} solicitou palavras para aprender sem estado cognitivo.")
         # TODO: Decidir como lidar: criar estado inicial? Retornar erro? Retornar palavras básicas?
         # Por enquanto, retornar lista vazia ou palavras muito fáceis
         return [] # Retorna lista vazia

    # --- Lógica temporária: usar uma lista Python estática como fonte --- #
    # TODO: Substituir por uma fonte de palavras real (DB, arquivo, API abrangente)
    # Exemplo de lista estática (apenas algumas palavras)
    all_possible_words_temp = [
        "casa", "bola", "gato", "cachorro", "flor",
        "montanha", "rio", "cidade", "rua", "árvore",
        "computador", "celular", "internet", "programação", "algoritmo",
        "abstração", "complexidade", "adaptativo", "cognitivo", "aprendizado"
    ]

    # 1. Filtrar palavras já tentadas pelo usuário (em qualquer tipo de exercício)
    # Precisamos de todas as palavras tentadas pelo usuário.
    all_user_progress_records = crud.get_user_progress_list(db, user_id, limit=None)
    attempted_words = {p.word_text for p in all_user_progress_records}

    untried_words = [word for word in all_possible_words_temp if word not in attempted_words]
    logger.info(f"Palavras não tentadas pelo usuário {user_id}: {len(untried_words)}")

    # 2. Selecionar palavras com base no nível ou zona proximal
    # Para usar a zona proximal, precisamos do score de complexidade e do user_state.
    
    words_in_proximal_zone: List[str] = []
    word_complexity_analyzer = WordComplexityAnalyzer() # Inicializar
    word_info_service = WordInfoService(db=db, complexity_analyzer=word_complexity_analyzer) # Inicializar
    
    # TODO: Refinar esta lógica para ser assíncrona e mais eficiente (obter complexidade em batch?)
    # A chamada a word_info_service._get_word_info_data_internal é assíncrona e deve ser awaited.

    # Para simplificar AGORA e evitar await em loop simples, VAMOS APENAS RETORNAR UM SUBSET DAS UNTRIED WORDS
    # A lógica de zona proximal e complexidade será implementada AO PREENCHER o placeholder no ExerciseSelectionService.
    # Este endpoint apenas fornecerá uma lista *inicial* de novas palavras candidatas.

    # Aplicar limite e retornar as palavras não tentadas (sem filtro de nível/zona por enquanto)
    words_to_return = untried_words[:limit]
    
    # Precisamos retornar WordInfoResponse, não apenas strings. Buscar info para cada palavra.
    result_words_info: List[schemas.WordInfoResponse] = []
    # TODO: Buscar info para cada word_text em words_to_return (requer await e WordInfoService)
    # Isso tornará o endpoint async.

    # TODO: Mover esta lógica de busca de info para DENTRO do loop abaixo quando implementado
    # Para agora, retornar apenas o nome da palavra como placeholder no schema (ajustar schema WordInfoResponse se necessário ou criar um novo)
    # Ou, melhor, fazer este endpoint *realmente* buscar as infos e torná-lo async.

    # Tornar endpoint async e buscar info para cada palavra a retornar
    # from fastapi import APIRouter, Depends, HTTPException, Request # Importar Request
    # import logging
    # from typing import List, Optional
    # from .. import crud, models, schemas
    # from ..dependencies import get_db, get_current_active_user
    # from ..services.word_info_service import WordInfoService
    # from ..services.word_complexity_analyzer import WordComplexityAnalyzer

    # logger = logging.getLogger(__name__)

    # router = APIRouter()

    # ... (endpoint get_word_info acima)

    # @router.get("/learn/", response_model=List[schemas.WordInfoResponse]) # Endpoint async
    # async def get_words_to_learn(
    #     level: Optional[str] = None,
    #     limit: int = 10,
    #     db: Session = Depends(get_db),
    #     current_user: models.User = Depends(get_current_active_user),
    #     request: Request = Depends() # Para WordInfoService
    # ):
    #     # ... (lógica de pool e filtragem untried_words)
    #     
    #     result_words_info: List[schemas.WordInfoResponse] = []
    #     word_complexity_analyzer = WordComplexityAnalyzer() # Inicializar
    #     word_info_service = WordInfoService(db=db, complexity_analyzer=word_complexity_analyzer, current_request_base_url=str(request.base_url), current_app_url_path_for=request.app.url_path_for)
    #
    #     for word_text in words_to_return:
    #         try:
    #             # Buscar info completa para cada palavra
    #             word_info = await word_info_service.get_word_info(word_text)
    #             if word_info:
    #                 result_words_info.append(word_info)
    #         except Exception as e:
    #             logger.error(f"Erro ao buscar info para palavra de aprendizado '{word_text}': {e}", exc_info=True)
    #
    #     logger.info(f"Retornando {len(result_words_info)} palavras para aprender para o usuário {user_id}")
    #     return result_words_info

    # Por enquanto, retornar lista vazia para evitar erros até implementar a busca async
    return []

# TODO: Mover o endpoint /words/autocomplete/ também para este router 