from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from .. import crud, models, schemas
from ..dependencies import get_db, get_current_user # Dependência para obter o usuário logado
from ..services.exercise_selection_service import ExerciseSelectionService # Importar o serviço de seleção
from ..services.word_info_service import WordInfoService # Importar o serviço de informação da palavra
from ..services.word_complexity_analyzer import WordComplexityAnalyzer # Importar o analisador de complexidade
from ..services.exercise_data_service import ExerciseDataService # Importar o novo serviço de dados de exercício

router = APIRouter()

@router.get("/next_exercise/", response_model=schemas.NextExerciseSuggestion) # Definir schema de resposta
async def get_next_exercise(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """
    Endpoint para obter a sugestão do próximo exercício para o usuário autenticado.
    """
    user_id = current_user.id

    # Inicializar os serviços necessários com a sessão DB
    word_complexity_analyzer = WordComplexityAnalyzer() # O analisador não precisa do DB session aqui
    # O WordInfoService precisa do DB session para o cache
    word_info_service = WordInfoService(db=db, complexity_analyzer=word_complexity_analyzer) # Passar DB session
    exercise_selection_service = ExerciseSelectionService(db=db, word_complexity_analyzer=word_complexity_analyzer, word_info_service=word_info_service) # Passar todos

    # Chamar o serviço para selecionar o próximo exercício
    suggested_exercise_candidate = await exercise_selection_service.select_next_exercise(user_id=user_id) # Tornar a chamada assíncrona

    if suggested_exercise_candidate:
        # Construir a resposta com base no candidato sugerido
        response_data = schemas.NextExerciseSuggestion(
            suggested_word_text=suggested_exercise_candidate.word_text,
            suggested_exercise_type=suggested_exercise_candidate.exercise_type,
            message=f"Próximo exercício sugerido: {suggested_exercise_candidate.word_text} ({suggested_exercise_candidate.exercise_type})"
        ) # Adapte conforme a estrutura final de NextExerciseSuggestion
        return response_data
    else:
        # Lidar com o caso onde nenhum exercício foi sugerido (ex: usuário sem progresso)
        return schemas.NextExerciseSuggestion(
            suggested_word_text=None,
            message="Não foi possível sugerir um exercício no momento. Tente novamente mais tarde ou adicione novas palavras."
        ) # Retornar None ou um indicador no schema de resposta

@router.post("/submit_exercise_result/") # Usar POST para submissão de dados
async def submit_exercise_result(exercise_data: schemas.ExerciseSubmissionData, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """
    Endpoint para receber o resultado de um exercício completo e atualizar
    o estado cognitivo do usuário e o progresso da palavra.
    """
    user_id = current_user.id

    # Inicializar os serviços necessários (similar ao endpoint de sugestão)
    word_complexity_analyzer = WordComplexityAnalyzer()
    word_info_service = WordInfoService(db=db, complexity_analyzer=word_complexity_analyzer)
    exercise_selection_service = ExerciseSelectionService(db=db, word_complexity_analyzer=word_complexity_analyzer, word_info_service=word_info_service)

    # Criar um objeto ExerciseCandidate a partir dos dados de submissão
    # Nota: A criação do ExerciseCandidate aqui para passar para update_user_cognitive_state
    # pode ser simplificada se update_user_cognitive_state puder aceitar os dados brutos de submission.
    # Por enquanto, manter para compatibilidade com a assinatura atual.
    completed_candidate = ExerciseSelectionService.ExerciseCandidate(
        word_text=exercise_data.word_text,
        exercise_type=exercise_data.exercise_type,
        word_complexity_score=exercise_data.word_complexity_score, # Usar o score composto submetido
        complexity_metrics=exercise_data.complexity_metrics, # Usar as métricas detalhadas submetidas
        # Os scores LE, EF, FR e a dificuldade serão recalculados/usados dentro de update_user_cognitive_state
        # Adicionar outros campos relevantes do resultado se necessário para update_user_cognitive_state
        # acurácia e tempo já estão em exercise_data, passados separadamente.
    )

    # Chamar o serviço para atualizar o estado cognitivo e progresso, passando o candidato completado e os dados de resultado
    await exercise_selection_service.update_user_cognitive_state(user_id=user_id, completed_candidate=completed_candidate, exercise_result=exercise_data) # Passar exercise_data também para a lógica de progresso da palavra

    return {"message": "Resultado do exercício processado com sucesso."}

# Novo endpoint para obter dados de exercício de Múltipla Escolha
@router.get("/multiple_choice/{word_text}", response_model=schemas.MultipleChoiceExercise) # Define o schema de resposta
async def get_multiple_choice_exercise(
    word_text: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user) # Opcional: pode querer verificar se o usuário está logado para certos tipos de exercício
):
    """
    Endpoint para obter os dados de um exercício de Múltipla Escolha para a palavra especificada.
    """
    # user_id = current_user.id # Não é estritamente necessário para gerar os dados do exercício

    # Inicializar os serviços necessários
    word_complexity_analyzer = WordComplexityAnalyzer()
    word_info_service = WordInfoService(db=db, complexity_analyzer=word_complexity_analyzer) # Passar DB session
    # exercise_selection_service = ExerciseSelectionService(db=db, word_complexity_analyzer=word_complexity_analyzer, word_info_service=word_info_service) # Remover inicialização

    # Inicializar o ExerciseDataService
    exercise_data_service = ExerciseDataService(db=db, word_info_service=word_info_service) # Passar dependências

    # Chamar o método para gerar os dados do MCQ usando o novo serviço
    mcq_data = await exercise_data_service.generate_multiple_choice_exercise_data(word_text=word_text)

    if not mcq_data:
        raise HTTPException(status_code=404, detail=f"Não foi possível gerar exercício de Múltipla Escolha para a palavra '{word_text}'.")

    return mcq_data

# Novo endpoint para obter dados de exercício de Múltipla Escolha (Imagem)
@router.get("/multiple_choice_image/{word_text}", response_model=schemas.MultipleChoiceImageExercise)
async def get_multiple_choice_image_exercise(
    word_text: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Endpoint para obter os dados de um exercício de Múltipla Escolha (Imagem).
    """
    # Inicializar os serviços necessários
    word_complexity_analyzer = WordComplexityAnalyzer()
    word_info_service = WordInfoService(db=db, complexity_analyzer=word_complexity_analyzer) # Passar DB session
    # exercise_selection_service = ExerciseSelectionService(
    #     db=db,
    #     word_complexity_analyzer=WordComplexityAnalyzer(), # Remover inicialização e uso
    #     word_info_service=WordInfoService(db=db, complexity_analyzer=WordComplexityAnalyzer())
    # )

    # Inicializar o ExerciseDataService
    exercise_data_service = ExerciseDataService(db=db, word_info_service=word_info_service) # Passar dependências

    mcq_image_data = await exercise_data_service.generate_mcq_image_exercise_data(word_text) # Chamar do novo serviço

    if not mcq_image_data:
        raise HTTPException(status_code=404, detail=f"Não foi possível gerar exercício de Múltipla Escolha (Imagem) para '{word_text}'.")
    return mcq_image_data

# Novo endpoint para obter dados de exercício de Definir Palavra
@router.get("/define_word/{word_text}", response_model=schemas.DefineWordExercise)
async def get_define_word_exercise(
    word_text: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Endpoint para obter os dados de um exercício de Definir Palavra.
    """
    # Inicializar os serviços necessários
    word_complexity_analyzer = WordComplexityAnalyzer()
    word_info_service = WordInfoService(db=db, complexity_analyzer=word_complexity_analyzer) # Passar DB session
    # exercise_selection_service = ExerciseSelectionService(
    #     db=db,
    #     word_complexity_analyzer=WordComplexityAnalyzer(), # Remover inicialização e uso
    #     word_info_service=WordInfoService(db=db, complexity_analyzer=WordComplexityAnalyzer())
    # )

    # Inicializar o ExerciseDataService
    exercise_data_service = ExerciseDataService(db=db, word_info_service=word_info_service) # Passar dependências

    define_word_data = await exercise_data_service.generate_define_word_exercise_data(word_text) # Chamar do novo serviço

    if not define_word_data:
        raise HTTPException(status_code=404, detail=f"Não foi possível gerar exercício de Definir Palavra para '{word_text}'.")
    return define_word_data

# Novo endpoint para obter dados de exercício de Completar Frase
@router.get("/complete_sentence/{word_text}", response_model=schemas.CompleteSentenceExercise)
async def get_complete_sentence_exercise(
    word_text: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Endpoint para obter os dados de um exercício de Completar Frase.
    """
    # Inicializar os serviços necessários
    word_complexity_analyzer = WordComplexityAnalyzer()
    word_info_service = WordInfoService(db=db, complexity_analyzer=word_complexity_analyzer) # Passar DB session
    # exercise_selection_service = ExerciseSelectionService(
    #     db=db,
    #     word_complexity_analyzer=WordComplexityAnalyzer(), # Remover inicialização e uso
    #     word_info_service=WordInfoService(db=db, complexity_analyzer=WordComplexityAnalyzer())
    # )

    # Inicializar o ExerciseDataService
    exercise_data_service = ExerciseDataService(db=db, word_info_service=word_info_service) # Passar dependências

    complete_sentence_data = await exercise_data_service.generate_complete_sentence_exercise_data(word_text) # Chamar do novo serviço

    if not complete_sentence_data:
        raise HTTPException(status_code=404, detail=f"Não foi possível gerar exercício de Completar Frase para '{word_text}'.")
    return complete_sentence_data 