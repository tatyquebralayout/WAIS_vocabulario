from typing import Dict, Any, List, Optional
from .. import schemas # Corrigir a importação relativa
from .word_complexity_analyzer import WordComplexityAnalyzer # Usar o analisador existente
from sqlalchemy.orm import Session # Para interagir com o DB
from datetime import datetime, timedelta # Importar datetime e timedelta
import random # Importar o módulo random
import logging

# Importar o novo ScoringService
from .scoring_service import ScoringService

from ..crud import get_user_cognitive_state, get_user_progress_list, create_initial_cognitive_state, get_user_progress_for_word, create_or_update_user_progress, update_user_cognitive_state as crud_update_cognitive_state # Importar funções CRUD
from ..crud import get_master_words # Importar função CRUD para MasterWord

logger = logging.getLogger(__name__)

# Definir os tipos de exercício
ExerciseType = str # Ou um Enum mais tarde: Enum('MCQ_image', 'MCQ_definition', 'dictation', 'define_word', 'complete_sentence')

# Estrutura para representar um candidato a exercício
# MOVIDO PARA schemas.py
# class ExerciseCandidate:
#     def __init__(self, word_text: str, exercise_type: ExerciseType, word_complexity_score: float, complexity_metrics: schemas.ComplexityBreakdownSchema):
#         self.word_text = word_text
#         self.exercise_type = exercise_type
#         self.word_complexity_score = word_complexity_score
#         self.complexity_metrics = complexity_metrics
#         self.difficulty = self._calculate_exercise_difficulty() # Calcula a dificuldade combinada

#     def _calculate_exercise_difficulty(self) -> float:
#         # Lógica inicial para a Matriz de Complexidade C(exercise_type, word_complexity)
#         # Pode ser mais sofisticado depois.
#         base_difficulty = {
#             'MCQ_image': 3.0,
#             'MCQ_definition': 4.0,
#             'dictation': 6.0,
#             'define_word': 8.0,
#             'complete_sentence': 7.0 # Exemplo de valores base
#         }.get(self.exercise_type, 5.0)

#         # Fator de interação simples: complexidade da palavra influencia a dificuldade final
#         interaction_factor = self.word_complexity_score * 0.5 # Exemplo: palavras mais complexas aumentam a dificuldade do exercício

#         return base_difficulty + interaction_factor


class ExerciseSelectionService:
    def __init__(self, db: Session, word_complexity_analyzer: WordComplexityAnalyzer, word_info_service: 'WordInfoService'):
        self.db = db
        self.word_complexity_analyzer = word_complexity_analyzer
        self.word_info_service = word_info_service
        # Pool de palavras a ser considerado para seleção. Inicialmente vazio ou baseado em algo.
        self.vocabulary_pool: List[str] = [] # TODO: Definir como popular este pool

        # Definir pesos para combinar os scores nos métodos de cálculo
        self.weights = {
            'learning_efficiency': {'challenge': 0.5, 'spacing': 0.3, 'transfer': 0.2},
            'engagement_factor': {'novelty': 0.4, 'interest': 0.4, 'achievement': 0.2},
            'frustration_risk': {'failures': 0.4, 'jump': 0.4, 'fatigue': 0.2, 'error_pattern': 0.0}
        }

        # Inicializar o serviço de scoring, passando os pesos
        self.scoring_service = ScoringService(weights=self.weights)

        # Parâmetro para a estratégia de exploração/explotação (epsilon-greedy)
        self.epsilon = 0.1 # 10% de chance de exploração (seleção aleatória)

    async def select_next_exercise(self, user_id: int) -> Optional[schemas.ExerciseCandidate]: # Usar o schema ExerciseCandidate importado
        # TODO: Implementar a lógica principal de seleção
        print(f"Selecting next exercise for user {user_id}") # Placeholder

        # Etapa 1: Calibração do Estado Atual
        # Precisamos do DB session para buscar o estado do usuário
        user_state = get_user_cognitive_state(self.db, user_id) # TODO: Importar get_user_cognitive_state do crud
        if not user_state:
             # TODO: Lidar com usuário sem estado cognitivo (criar um? erro?)
             print(f"User {user_id} does not have a cognitive state.")
             # Criar estado inicial se não existir
             user_state = create_initial_cognitive_state(self.db, user_id=user_id) # TODO: Importar create_initial_cognitive_state
             print(f"Created initial cognitive state for user {user_id}")
             
        # Precisamos do histórico de progresso recente para engagement e frustration
        # TODO: Definir quantos registros de progresso recente são necessários (ex: últimos 10-20)
        user_history = get_user_progress_list(self.db, user_id, limit=20) # TODO: Importar get_user_progress_list do crud
        recent_performance = user_history # Para simplificar por enquanto, usar o mesmo histórico para ambos

        # Etapa 2: Geração de Candidatos de Exercício
        candidates: List[schemas.ExerciseCandidate] = []
        # Exemplo simples: apenas algumas palavras de um pool fixo (manter por enquanto)
        # example_pool = ["complexidade", "algoritmo", "adaptativo", "vocabulario", "aprendizado"]
        # TODO: Substituir example_pool por um pool de palavras mais relevante (palavras vistas, novas, etc.)

        # --- Lógica para definir o pool de palavras dinâmico para o usuário ---
        # TODO: Implementar lógica para selecionar palavras com base no histórico (UserProgress) e estado cognitivo (UserCognitiveState)
        # Possibilidades:
        # - Palavras com baixo desempenho
        # - Palavras que precisam de revisão (spaced repetition)
        # - Novas palavras na zona de desenvolvimento proximal do usuário
        # - Palavras de domínios de interesse ou necessidade de reforço

        # Modificação: Priorizar palavras do histórico que precisam de reforço.
        # Primeiro, obter todo o histórico de progresso do usuário.
        full_user_history = get_user_progress_list(self.db, user_id, limit=None)

        # Identificar palavras únicas no histórico
        unique_attempted_words = {p.word_text for p in full_user_history}

        # Pool de palavras inicial focado em reforço
        reinforcement_pool: List[str] = []

        # Para cada palavra única tentada, verificar se precisa de reforço em *qualquer* tipo de exercício
        # Nota: A lógica needs_reinforcement atual verifica o progresso para um *tipo específico*. Precisamos adaptar.
        # Por enquanto, vamos iterar sobre os tipos de exercício e verificar se a palavra precisa de reforço em *algum* deles.
        available_exercise_types: List[ExerciseType] = ['MCQ_definition', 'dictation', 'MCQ_image', 'define_word', 'complete_sentence'] # Reutilizar a lista de tipos
        
        for word_text in unique_attempted_words:
            needs_reinforce_in_any_type = False
            for exercise_type in available_exercise_types:
                # Obter o progresso específico para esta combinação palavra-tipo
                word_progress_for_type = get_user_progress_for_word(self.db, user_id, word_text, exercise_type)
                # Verificar se precisa de reforço para este tipo específico
                if self.needs_reinforcement(word_text, word_progress_for_type, full_user_history): # Passar o progresso específico
                    needs_reinforce_in_any_type = True
                    break # Se precisar em um tipo, adicionamos a palavra ao pool de reforço

            if needs_reinforce_in_any_type:
                reinforcement_pool.append(word_text)

        # Definir o pool dinâmico. Inicialmente, apenas palavras que precisam de reforço.
        dynamic_word_pool = list(set(reinforcement_pool)) # Usar set para garantir unicidade e converter de volta para lista
        
        if len(dynamic_word_pool) < 5: # Exemplo: se menos de 5 palavras precisam de reforço
            logger.info(f"Pool de reforço pequeno ({len(dynamic_word_pool)}). Buscando novas palavras.")
            # --- Lógica para buscar e selecionar NOVAS palavras (preenchendo o TODO) ---
            
            # 1. Obter uma lista de palavras candidatas da fonte mestra (DB), filtrando pela zona proximal do usuário
            # TODO: Implementar filtros no get_master_words para buscar palavras na faixa de complexidade adequada -> FEITO
            
            # Calcular a faixa de complexidade desejada com base na habilidade vocabular do usuário e a dificuldade base de um exercício introdutório (ex: MCQ_definition)
            base_intro_exercise_difficulty = 4.0 # Dificuldade base para MCQ_definition (do _calculate_exercise_difficulty)
            # Relação: candidate_difficulty = word_complexity_score * 0.5 + base_exercise_difficulty * 0.5
            # Queremos candidate_difficulty ~ user_state.vocabular_ability + [0.2, 0.8]
            # user_state.vocabular_ability + 0.2 <= word_complexity_score * 0.5 + base_intro_exercise_difficulty * 0.5 <= user_state.vocabular_ability + 0.8
            # user_state.vocabular_ability + 0.2 <= word_complexity_score * 0.5 + 2.0 <= user_state.vocabular_ability + 0.8
            # user_state.vocabular_ability - 1.8 <= word_complexity_score * 0.5 <= user_state.vocabular_ability - 1.2
            # (user_state.vocabular_ability - 1.8) / 0.5 <= word_complexity_score <= (user_state.vocabular_ability - 1.2) / 0.5
            min_complexity_target = max(0.0, (user_state.vocabular_ability - 1.8) / 0.5) # Limitar mínimo a 0.0
            max_complexity_target = min(10.0, (user_state.vocabular_ability - 1.2) / 0.5) # Limitar máximo a 10.0
            
            logger.info(f"Buscando novas palavras com complexidade entre {min_complexity_target:.2f} e {max_complexity_target:.2f} (baseado em habilidade {user_state.vocabular_ability:.2f}).")

            # Buscar palavras mestras dentro da faixa de complexidade estimada
            all_possible_master_words = get_master_words(self.db, min_complexity=min_complexity_target, max_complexity=max_complexity_target, limit=50) # Usar filtros

            # Filtrar palavras que o usuário JÁ tentou do pool de novas palavras
            new_words_to_consider = [mw.word_text for mw in all_possible_master_words if mw.word_text not in unique_attempted_words]

            # TODO: Implementar lógica mais sofisticada de seleção de novas palavras (ex: balancear complexidade, diversidade)
            # Por enquanto, adicionar uma amostra aleatória à piscina dinâmica se necessário
            num_needed = 5 - len(dynamic_word_pool)
            if num_needed > 0 and new_words_to_consider:
                selected_new_words = random.sample(new_words_to_consider, min(num_needed, len(new_words_to_consider)))
                dynamic_word_pool.extend(selected_new_words)
                logger.info(f"Adicionando {len(selected_new_words)} novas palavras ao pool.")

        if not dynamic_word_pool:
             # TODO: Lidar com o caso onde não há palavras no pool (nem de reforço, nem novas)
             # Pode sugerir adicionar palavras manualmente ou tentar um pool mais amplo.
             logger.warning("Dynamic word pool is empty. Cannot suggest an exercise.")
             return None # Nenhum candidato disponível

        # Para cada palavra no pool dinâmico, gerar candidatos para todos os tipos de exercício disponíveis
        possible_candidates: List[schemas.ExerciseCandidate] = []
        for word_text in dynamic_word_pool:
             # Obter informações completas da palavra, incluindo métricas de complexidade detalhadas
             word_info = await self.word_info_service._get_word_info_data_internal(word_text)
             if word_info and word_info.complexity_metrics:
                  word_complexity_score = word_info.inferred_complexity_score
                  complexity_metrics = word_info.complexity_metrics
                  
                  # Obter o progresso da palavra para a lógica de scores (específico por palavra, não por tipo ainda)
                  # Precisamos do progresso para a palavra GERAL para alguns scores (como espaçamento geral)
                  # Mas alguns scores (como reinforcement) dependem do progresso por TIPO.
                  # A estrutura atual de UserProgress com PK composta (user_id, word_text, exercise_type) significa que
                  # não há um único registro de progresso para a *palavra* em si, apenas para combinações palavra-tipo.
                  # Precisamos adaptar a lógica de scores ou buscar todos os progressos para a palavra.
                  
                  # Por enquanto, vamos obter todos os progressos para esta palavra para o usuário
                  # TODO: Criar uma função CRUD para get_all_user_progress_for_word
                  all_progress_for_word = [] # Placeholder, precisa de nova função CRUD
                  # get_user_progress_list(self.db, user_id, word_text=word_text, limit=None) # Precisamos de um filtro por word_text no CRUD

                  # Lógica temporária: buscar progresso para um tipo padrão (ex: MCQ_definition) ou usar lista geral
                  # Isso não é ideal. Refinamento necessário na forma como os scores usam o histórico.
                  
                  # TODO: Refinar a passagem do histórico para os métodos de scoring.
                  # Alguns scores (engagement, frustration) usam histórico geral ou recente.
                  # O calculate_learning_efficiency usa o progresso específico da word_progress (para espaçamento).
                  # Precisamos garantir que os dados corretos (histórico geral, histórico recente, progresso específico do candidato) sejam passados.

                  # Gerar candidatos para tipos de exercício compatíveis com as informações disponíveis
                  # Ex: MCQ_image só se image_url estiver disponível.
                  # TODO: Definir quais tipos de exercício são possíveis dado word_info.

                  # Para simplificar por agora, gerar candidatos para TODOS os tipos disponíveis se a palavra tem info
                  for exercise_type in available_exercise_types:
                       # Obter progresso específico para este candidato (palavra + tipo)
                       # Esta chamada CRUD já existe e é necessária para a lógica needs_reinforcement e calculate_learning_efficiency (spacing)
                       word_progress_for_candidate = get_user_progress_for_word(self.db, user_id, word_text, exercise_type)

                       # Criar o candidato
                       candidate = schemas.ExerciseCandidate(
                           word_text=word_text,
                           exercise_type=exercise_type,
                           word_complexity_score=word_complexity_score,
                           complexity_metrics=complexity_metrics
                       )

                       # Etapa 3: Calcular Scores para Cada Candidato
                       # Usar o novo ScoringService
                       candidate.learning_efficiency_score = self.scoring_service.calculate_learning_efficiency(candidate, user_state, word_progress_for_candidate) # Passar progresso específico
                       candidate.engagement_factor_score = self.scoring_service.calculate_engagement_factor(candidate, user_history, user_state) # Passar histórico geral
                       candidate.frustration_risk_score = self.scoring_service.calculate_frustration_risk(candidate, recent_performance, user_state) # Passar performance recente

                       # TODO: Calcular o Score Composto Final para o Candidato usando os pesos (LE, EF, FR)
                       # Isso pode ser um método no ScoringService ou aqui.
                       # Formula: Composite = w_le*LE + w_ef*EF - w_fr*FR
                       
                       # Defina pesos para os scores combinados (estes são diferentes dos pesos internos do ScoringService)
                       combination_weights = {
                           'learning_efficiency': 0.4,
                           'engagement_factor': 0.4,
                           'frustration_risk': 0.2
                       } # TODO: Mover para self.weights ou config

                       # TODO: Normalizar/escalar os scores individuais (LE, EF, FR) para que tenham impacto comparável antes de combinar?
                       # Por enquanto, assumir que estão em escala 0-1.

                       candidate.final_composite_score = (
                           candidate.learning_efficiency_score * combination_weights['learning_efficiency'] +
                           candidate.engagement_factor_score * combination_weights['engagement_factor'] -
                           candidate.frustration_risk_score * combination_weights['frustration_risk']
                       ) # Subtrair risco de frustração

                       possible_candidates.append(candidate)

             else:
                  logger.warning(f"Could not get word info or complexity metrics for '{word_text}'. Skipping.")

        if not possible_candidates:
             logger.warning("No possible exercise candidates generated.")
             return None

        # Etapa 4: Seleção Final
        # Aplicar estratégia de exploração/explotação (epsilon-greedy)
        if random.random() < self.epsilon:
             # Exploração: selecionar um candidato aleatório
             selected_candidate = random.choice(possible_candidates)
             logger.info(f"Exploração: Selecionando candidato aleatório: {selected_candidate.word_text} ({selected_candidate.exercise_type})")
        else:
             # Explotação: selecionar o candidato com o maior Score Composto Final
             selected_candidate = max(possible_candidates, key=lambda c: c.final_composite_score)
             logger.info(f"Explotação: Selecionando candidato com maior score: {selected_candidate.word_text} ({selected_candidate.exercise_type}) - Score: {selected_candidate.final_composite_score:.2f}")

        return selected_candidate

    async def update_user_cognitive_state(self, user_id: int, exercise_result: schemas.ExerciseSubmissionData, completed_candidate: schemas.ExerciseCandidate): # Usar o schema ExerciseCandidate importado
        # Implementar lógica de atualização pós-exercício
        logger.info(f"Updating cognitive state for user {user_id} after exercise on '{exercise_result.word_text}' ({exercise_result.exercise_type})")

        # 1. Obter o estado cognitivo atual do usuário
        user_state = get_user_cognitive_state(self.db, user_id)
        if not user_state:
             logger.error(f"User cognitive state not found for user {user_id}. Cannot update.")
             return # Não pode atualizar se o estado não existe

        # 2. Obter o progresso da palavra específica para este tipo de exercício
        word_progress = get_user_progress_for_word(self.db, user_id, exercise_result.word_text, exercise_result.exercise_type)

        # Se não houver progresso existente, criar um novo (isso deve ser tratado idealmente na criação do pool ou na submissão do primeiro exercício)
        if not word_progress:
             logger.warning(f"No existing progress found for user {user_id} on '{exercise_result.word_text}' ({exercise_result.exercise_type}). Creating new.")
             # Criar um novo registro de progresso
             word_progress = create_or_update_user_progress(
                  self.db,
                  user_id=user_id,
                  word_text=exercise_result.word_text,
                  exercise_type=exercise_result.exercise_type,
                  correct_attempts=0,
                  total_attempts=0,
                  average_time_seconds=0.0,
                  last_seen_on_word=datetime.utcnow()
             )
             if not word_progress:
                  logger.error(f"Failed to create initial progress for user {user_id} on '{exercise_result.word_text}' ({exercise_result.exercise_type}). Cannot update.")
                  return

        # 3. Atualizar o registro de progresso da palavra com o resultado do exercício
        new_total_attempts = word_progress.total_attempts + 1
        new_correct_attempts = word_progress.correct_attempts + (1 if exercise_result.accuracy > 0.99 else 0) # Considerar acurácia > 0.99 como correto
        # Calcular nova média de tempo
        new_average_time = ((word_progress.average_time_seconds * word_progress.total_attempts) + exercise_result.time_taken_seconds) / new_total_attempts if new_total_attempts > 0 else 0.0

        # Atualizar o objeto de progresso existente
        word_progress.total_attempts = new_total_attempts
        word_progress.correct_attempts = new_correct_attempts
        word_progress.average_time_seconds = new_average_time
        word_progress.last_seen_on_word = datetime.utcnow() # Atualizar o timestamp da última vez visto

        # Persistir a atualização do progresso no DB
        create_or_update_user_progress(
             self.db,
             user_id=user_id,
             word_text=word_progress.word_text,
             exercise_type=word_progress.exercise_type,
             correct_attempts=word_progress.correct_attempts,
             total_attempts=word_progress.total_attempts,
             average_time_seconds=word_progress.average_time_seconds,
             last_seen_on_word=word_progress.last_seen_on_word # Passar o timestamp atualizado
        )
        # TODO: A função create_or_update_user_progress já lida com a criação e atualização.
        # Podemos simplificar chamando-a uma vez com os dados calculados.
        # A implementação atual chama create_or_update_user_progress mesmo para atualização, o que é correto, mas a lógica acima de atualizar o objeto e depois passar para o CRUD é redundante/confusa.
        # Simplificar:
        updated_progress = create_or_update_user_progress(
             self.db,
             user_id=user_id,
             word_text=exercise_result.word_text,
             exercise_type=exercise_result.exercise_type,
             correct_attempts=new_correct_attempts,
             total_attempts=new_total_attempts,
             average_time_seconds=new_average_time,
             last_seen_on_word=datetime.utcnow() # Atualizar timestamp
        )
        if not updated_progress:
              logger.error(f"Failed to update progress for user {user_id} on '{exercise_result.word_text}' ({exercise_result.exercise_type})")
              # Continuar com a atualização do estado cognitivo mesmo que o progresso falhe?
              # Decisão de design: Sim, tentar atualizar o estado cognitivo mesmo com falha no progresso.

        # 4. Atualizar o estado cognitivo do usuário com base no resultado do exercício completado
        # A lógica de atualização já está presente aqui e usa o completed_candidate e exercise_result.
        # Precisamos apenas garantir que a indentação esteja correta e que use as informações passadas.

        # Métricas do exercício completado
        accuracy = exercise_result.accuracy
        time_taken = exercise_result.time_taken_seconds
        exercise_type = exercise_result.exercise_type
        # completed_candidate já contém word_text, exercise_type, difficulty, composite_score, complexity_details
        complexity_metrics = completed_candidate.complexity_details # Usar as métricas detalhadas do candidato
        word_complexity_score = completed_candidate.word_complexity_score # Usar o score composto do candidato


        # 2a. vocabular_ability
        # Ajustar com base na acurácia, complexidade da palavra (detalhada) e tipo de exercício.
        # Sucesso em exercícios difíceis/complexos aumenta mais a habilidade.
        # Falha em exercícios fáceis/simples diminui mais a habilidade.

        # Calcular um 'impact_factor' baseado na complexidade da palavra e no tipo de exercício
        # Tipos de exercício mais complexos (definir, completar) devem ter um impacto maior
        exercise_type_impact = {
            'MCQ_image': 0.1,
            'MCQ_definition': 0.15,
            'dictation': 0.2,
            'define_word': 0.25,
            'complete_sentence': 0.2
        }.get(exercise_type, 0.15) # Default 0.15

        # Impacto da complexidade da palavra (usando o composite score ou métricas específicas)
        # Usar o composite score para um ajuste geral, mas considerar métricas específicas também.
        # Exemplo: Se a acurácia é alta, o ganho é maior se semantic_abstraction for alta.
        # Se a acurácia é baixa, a perda é menor se syntactic_complexity for alta.

        # Ajuste base baseado na acurácia: positivo para acertos (>0.5), negativo para erros (<0.5)
        base_accuracy_adjustment = (accuracy - 0.5) * 0.5 # Ajuste entre -0.25 e 0.25

        # Ajuste adicional baseado na complexidade e acurácia
        complexity_based_adjustment = 0.0
        if complexity_metrics:
             # Se acurácia alta, ganho é amplificado por complexidade (ex: semantic_abstraction, morphological_density)
             if accuracy > 0.75:
                  complexity_bonus = (complexity_metrics.semantic_abstraction / 10.0 * 0.4 + complexity_metrics.morphological_density / 10.0 * 0.3) * 0.1 # Bonus de 0-0.07
                  complexity_based_adjustment += complexity_bonus
             # Se acurácia baixa, perda é mitigada por complexidade (ex: syntactic_complexity)
             elif accuracy < 0.25:
                  complexity_mitigation = (complexity_metrics.syntactic_complexity / 10.0) * -0.05 # Mitigação de 0 a -0.05
                  complexity_based_adjustment += complexity_mitigation
        
        # Combinar ajustes e aplicar fator de impacto do tipo de exercício
        total_adjustment = (base_accuracy_adjustment + complexity_based_adjustment) * exercise_type_impact

        user_state.vocabular_ability += total_adjustment
        user_state.vocabular_ability = max(0.0, min(10.0, user_state.vocabular_ability)) # Limitar habilidade entre 0 e 10
        # TODO: Refinar a função de ajuste da habilidade significativamente.

        # 2b. processing_speed
        # Ajustar com base no tempo gasto vs. tempo esperado (agora usando complexidade detalhada)
        # TODO: Refinar a lógica de tempo esperado significativamente.
        # O tempo esperado deve depender da *dificuldade* do exercício completado e da *velocidade de processamento atual* do usuário.
        # Usar completed_candidate.difficulty e user_state.processing_speed para calcular um tempo esperado mais realista.

        # Exemplo simplificado de tempo esperado: Aumenta com a dificuldade do exercício e diminui com a velocidade do usuário.
        # Usar um valor base e ajustar:
        base_expected_time = 15.0 # Tempo esperado base em segundos para um exercício de dificuldade média (5.0) e velocidade média (5.0)
        
        # Ajustar pelo nível de dificuldade: exercícios mais difíceis levam mais tempo
        difficulty_adjustment = (completed_candidate.difficulty / 10.0) * base_expected_time # Ajuste proporcional à dificuldade (0-15)
        
        # Ajustar pela velocidade do usuário: usuários mais rápidos levam menos tempo
        # Inverter a velocidade: um score de 10 (rápido) deve reduzir o tempo, um score de 0 (lento) deve aumentar.
        speed_adjustment_factor = (10.0 - user_state.processing_speed) / 10.0 # Fator de 0 (vel 10) a 1 (vel 0)
        
        expected_time = (base_expected_time + difficulty_adjustment) * (1.0 + speed_adjustment_factor * 0.5) # Exemplo: velocidade mais baixa pode aumentar o tempo esperado em até 50%
        # Garantir um tempo mínimo esperado para evitar divisão por zero ou ajustes extremos
        expected_time = max(5.0, expected_time) # Tempo esperado mínimo de 5 segundos

        # A lógica de ajuste pode usar a proporção entre tempo gasto e tempo esperado

        speed_adjustment = 0.0
        if time_taken > 0 and expected_time > 0:
             # Se tempo gasto < esperado, speed aumenta. Se tempo gasto > esperado, speed diminui.
             speed_adjustment = (expected_time - time_taken) / max(expected_time, time_taken) * 0.5 # Ajuste entre -0.5 e 0.5
        
        user_state.processing_speed += speed_adjustment
        user_state.processing_speed = max(0.0, min(10.0, user_state.processing_speed)) # Limitar speed
        # TODO: Refinar a função de ajuste da velocidade de processamento.

        # 2c. confidence_level
        # Ajustar com base no sucesso/falha e na dificuldade relativa do exercício.
        # Sucesso em algo difícil aumenta mais a confiança. Falha em algo fácil diminui mais.

        # Dificuldade percebida do candidato vs. habilidade do usuário
        perceived_difficulty = completed_candidate.difficulty - user_state.vocabular_ability

        confidence_adjustment = 0.0
        # Ajustar com base na acurácia e na dificuldade percebida (gap entre dificuldade do exercício e habilidade do usuário)
        # Multiplicar a influência da acurácia pela dificuldade percebida
        # Sucesso (acurácia > 0.5) em exercício difícil (perceived_difficulty > 0) -> Ganho de confiança
        # Falha (acurácia < 0.5) em exercício fácil (perceived_difficulty < 0) -> Perda de confiança
        # Sucesso em exercício fácil ou falha em exercício difícil -> Ajuste menor

        # Acurácia normalizada em torno de 0: (accuracy - 0.5) * 2.0 -> Varia de -1 a 1
        normalized_accuracy = (accuracy - 0.5) * 2.0

        # Fator de ajuste: (normalized_accuracy) * (perceived_difficulty / 10.0) * scaling_factor
        # perceived_difficulty varia aprox de -10 a 10, mas a escala real é menor (0-10 - 0-10). Limitar o gap.
        capped_perceived_difficulty = max(-5.0, min(5.0, perceived_difficulty)) # Limitar o gap percebido para evitar ajustes extremos

        # Fator de escala para o ajuste de confiança
        scaling_factor = 0.05 # Exemplo: ajuste máximo de +/- 0.25 por exercício

        # Ajuste final: (normalized_accuracy) * (capped_perceived_difficulty / 5.0) * scaling_factor
        # Dividir por 5.0 para normalizar o gap limitado (-5 a 5) para -1 a 1 antes de multiplicar
        confidence_adjustment = normalized_accuracy * (capped_perceived_difficulty / 5.0) * scaling_factor

        # Garantir que o ajuste não seja excessivamente grande (embora a fórmula já limite)
        confidence_adjustment = max(-0.2, min(0.2, confidence_adjustment)) # Limitar o ajuste por exercício entre -0.2 e 0.2

        user_state.confidence_level += confidence_adjustment
        user_state.confidence_level = max(0.0, min(1.0, user_state.confidence_level)) # Limitar confiança entre 0 e 1
        # TODO: Refinar a lógica de ajuste da confiança significativamente.

        # 2d. fatigue_factor
        # Aumentar com base no tempo gasto e na complexidade/dificuldade do exercício.
        # Exercícios mais longos ou complexos causam mais fadiga.
        
        # Aumentar com base no tempo gasto, na dificuldade do exercício e no tipo de exercício.
        # Exercícios mais longos, mais difíceis ou de tipos mais exigentes causam mais fadiga.
        
        # Contribuição do tempo: tempo gasto em segundos, normalizado por um tempo de referência (ex: 30s)
        time_contribution = min(time_taken / 30.0, 1.0) # Limitar a contribuição máxima do tempo a 1.0
        
        # Contribuição da dificuldade: dificuldade do exercício (0-10), normalizada
        difficulty_contribution = completed_candidate.difficulty / 10.0 # Normalizar dificuldade para 0-1
        
        # Contribuição do tipo de exercício (usar o mesmo exercise_type_impact calculado anteriormente)
        # exercise_type_impact: 0.1 a 0.25 (aprox)
        
        # Exemplo de combinação: Média ponderada das contribuições
        # Pesos: tempo (0.4), dificuldade (0.4), tipo (0.2) - Ajustar conforme necessário
        fatigue_increase = (time_contribution * 0.4 + difficulty_contribution * 0.4 + exercise_type_impact * 0.2) * 0.1 # Multiplicar por um fator de escala (0.1) para controlar a magnitude
        # O fator de escala (0.1) garante que o aumento máximo por exercício seja em torno de 0.1
        
        user_state.fatigue_factor += fatigue_increase
        user_state.fatigue_factor = min(1.0, user_state.fatigue_factor) # Limitar fadiga a 1.0
        # TODO: Implementar lógica de *recuperação* de fadiga ao longo do tempo ou com pausas.

        # 2e. domain_expertise
        # TODO: Implementar lógica de atualização robusta por domínio.
        # Requer: 1) Associar palavras a domínios (via modelo MasterWord ou outro serviço/dado).
        #          2) Rastrear a expertise do usuário *por domínio* (campo no UserCognitiveState).
        #          3) Calcular ajuste baseado na acurácia, complexidade da palavra *e* o domínio relevante.
          # Por enquanto, manter a lógica existente (que é nula ou baseada em algo externo não implementado aqui).
          # Podemos adicionar um ajuste mínimo baseado em acurácia e complexidade geral como placeholder.
        if complexity_metrics:
             domain_expertise_adjustment = (accuracy - 0.5) * (complexity_metrics.composite_score / 10.0) * 0.01 # Ajuste muito pequeno
             # Aplicar o ajuste placeholder ao campo domain_expertise (assumindo que é um score geral por enquanto)
             # TODO: Mudar para atualizar expertise_por_dominio quando a estrutura estiver pronta.
             # Assumindo que domain_expertise é um float/int para este ajuste placeholder.
             # Se for um dicionário (como parece sugerir o TODO), esta lógica precisará ser ajustada.
             # Vamos manter a suposição de que é um float para aplicar o ajuste numérico simples.
             user_state.domain_expertise = max(0.0, min(10.0, user_state.domain_expertise + domain_expertise_adjustment)) # Limitar expertise entre 0 e 10

        # Salvar o estado cognitivo atualizado no DB usando a função CRUD
        # Criar um schema de atualização a partir do objeto modelo atualizado
        # TODO: O campo domain_expertise no schema UserCognitiveStateBase é definido como Dict[str, Any] | None.
        # A lógica acima está tratando user_state.domain_expertise como float/int para o ajuste.
        # Isso é uma inconsistência. Precisa ser decidido se domain_expertise é um score geral (float/int) ou uma estrutura granular (Dict).
        # Com base na proposta inicial e no modelo atual, é um JSON (Dict). A lógica de atualização precisa ser refeita para atualizar o dicionário.
        # Por enquanto, vou remover o ajuste numérico direto e manter o TODO original como prioridade.
        # user_state.domain_expertise = max(0.0, min(10.0, user_state.domain_expertise + domain_expertise_adjustment)) # REMOVER esta linha para evitar erro de tipo

        # TODO: Implementar a lógica correta para atualizar user_state.domain_expertise (que é um JSON Dict)
        # com base nos resultados do exercício completado, considerando o domínio relevante da palavra.
        # Isso provavelmente envolverá:
        # 1) Identificar o(s) domínio(s) da palavra (requer dados de domínio na palavra ou WordInfo).
        # 2) Calcular um ajuste específico para esse(s) domínio(s) baseado na acurácia e dificuldade.
        # 3) Atualizar o dicionário user_state.domain_expertise.
        # Manter o campo como está no schema/modelo (Dict[str, Any] | None) por enquanto.

        state_update_schema = schemas.UserCognitiveStateBase(
             vocabular_ability=user_state.vocabular_ability,
             processing_speed=user_state.processing_speed,
             working_memory_load=user_state.working_memory_load,
             confidence_level=user_state.confidence_level,
             fatigue_factor=user_state.fatigue_factor,
             domain_expertise=user_state.domain_expertise # Manter o dicionário como está ou com atualização placeholder se decidido
        )
        # TODO: Verificar se precisamos de um schema de atualização dedicado (UserCognitiveStateUpdate) que inclua apenas campos mutáveis.
        # A função CRUD crud_update_cognitive_state pode lidar com o objeto modelo diretamente ou um schema.
        # Vamos usar o objeto modelo atualizado diretamente com a função CRUD se ela suportar.

        # Assumindo que crud_update_cognitive_state espera o ID e o objeto UserCognitiveState
        # Corrigir a chamada, passando o ID do usuário e o objeto user_state (que já foi modificado in-place ou recriado)
        # Se crud_update_cognitive_state espera um schema, usar state_update_schema.
        # Se crud_update_cognitive_state espera o objeto model, usar user_state.
        # Olhando o CRUD, ele espera o user_id e o schema.

        crud_update_cognitive_state(self.db, user_id, state_update_schema) # Passar o schema de atualização

    # Métodos auxiliares para lógica de seleção
    def is_in_proximal_zone(self, candidate: schemas.ExerciseCandidate, user_state: schemas.UserCognitiveState) -> bool: # Usar o schema ExerciseCandidate importado
        """
        Verifica se a dificuldade do exercício está na zona de desenvolvimento proximal do usuário.
        Retorna True se a dificuldade estiver entre user_ability + 0.2 e user_ability + 0.8.
        """
        # TODO: Implementar lógica baseada em candidate.difficulty e user_state.vocabular_ability
        # print(f"Checking proximal zone for {candidate.word_text} ({candidate.exercise_type})") # Placeholder

        # A zona proximal está tipicamente um pouco acima do nível atual do usuário.
        # Usando a faixa empírica sugerida de 0.2 a 0.8 acima da habilidade atual.
        lower_bound = user_state.vocabular_ability + 0.2
        upper_bound = user_state.vocabular_ability + 0.8
        
        # Também considerar exercícios no nível do usuário ou ligeiramente abaixo para revisão
        # Podemos ajustar os limites ou ter uma faixa mais ampla que inclua o nível atual.
        # Vamos manter a faixa estrita acima por enquanto, mas isso é um ponto de ajuste futuro.

        return lower_bound <= candidate.difficulty <= upper_bound

    def needs_reinforcement(self, word_text: str, word_progress: Optional[schemas.UserProgress], user_history: List[schemas.UserProgress]) -> bool:
        """
        Verifica se uma palavra precisa de reforço para o usuário.
        Considera: se nunca foi tentada, baixa acurácia, e espaçamento de repetição.
        """
        # print(f"Checking reinforcement need for '{word_text}'") # Mover log para debug

        # 1. Palavra nunca tentada: Precisa de reforço (introdução)
        if word_progress is None:
             # TODO: A lógica de pool de palavras definirá QUANDO introduzir novas palavras.
             # Se uma palavra nunca vista chega aqui (pq o pool a incluiu), ela precisa de introdução.
             print(f"Word '{word_text}' has no progress. Needs reinforcement (introduction).")
             return True
            
        # 2. Palavra já tentada: Avaliar necessidade com base no progresso
        
        # 2a. Baixa Acurácia
        if word_progress.total_attempts > 0:
            accuracy = word_progress.correct_attempts / word_progress.total_attempts
            if accuracy < 0.5: # Limiar de baixa acurácia
                print(f"Word '{word_text}' needs reinforcement (low accuracy: {accuracy:.2f})")
                return True # Precisa de reforço por performance ruim
            
            # 2b. Zona de Esquecimento (Spaced Repetition Simplificado)
            # Para palavras com acurácia razoável (>= 0.5), verificar o espaçamento
            time_since_last_seen = datetime.utcnow() - word_progress.last_seen_on_word

            # TODO: Implementar cálculo do intervalo ótimo de forma adaptativa (curva de retenção)
            # Por enquanto, usar um intervalo ótimo simplificado (ex: 3 dias)
            simplified_optimal_interval = timedelta(days=3) # Exemplo: Palavras com acurácia >= 50% precisam de revisão a cada 3 dias
            # Este intervalo deveria aumentar com o número de revisões bem sucedidas (modelo SM-2)

            if time_since_last_seen > simplified_optimal_interval:
                 print(f"Word '{word_text}' needs reinforcement (spaced repetition - last seen {time_since_last_seen.total_seconds():.0f}s ago)")
                 return True # Precisa de reforço por espaçamento
                
            # TODO: Considerar Performance Inconsistente aqui
            # A lógica de inconsistência precisaria de mais dados (ex: histórico de tentativas individuais)
            # Para agora, vamos ignorar, mas é um ponto crucial para refinar este método.
            # Exemplo simplificado extremo: if word_progress.total_attempts > 5 and accuracy > 0.8 and accuracy < 1.0:
            #    return True # Alta tentativa com não 100% acurácia pode indicar inconsistência

            # Se chegou aqui: palavra tentada, acurácia >= 0.5, e dentro do intervalo ótimo simplificado
            print(f"Word '{word_text}' does not need reinforcement based on current logic (accuracy ok, spacing ok).")
            return False
        else:
             # Caso onde total_attempts é 0 mas o registro existe (imprevisto com a lógica atual)
             print(f"Word '{word_text}' has progress record but 0 attempts. Needs reinforcement?") # Log de alerta
             return True # Considerar que sim para segurança

    # TODO: Adicionar outros métodos auxiliares conforme necessário (ex: get_word_progress_for_user)

    # TODO: Adicionar métodos auxiliares como is_in_proximal_zone, needs_reinforcement, get_user_cognitive_state, etc.

    # async def generate_multiple_choice_exercise_data(self, word_text: str) -> Optional[schemas.MultipleChoiceExercise]:
    #     """
    #     Gera os dados necessários para um exercício de Múltipla Escolha para a palavra especificada.
    #     """
    #     logger.info(f"Gerando dados para exercício de Múltipla Escolha para '{word_text}'")

    #     # 1. Obter a definição correta da palavra usando WordInfoService
    #     correct_word_info = await self.word_info_service._get_word_info_data_internal(word_text)
    #     if not correct_word_info or not correct_word_info.definition:
    #         logger.warning(f"No definition found for '{word_text}'. Cannot generate MCQ.")
    #         return None

    #     # 2. Gerar opções de distratores
    #     # TODO: Implementar lógica sofisticada para gerar distratores.
    #     # Ideias:
    #     # - Palavras com complexidade similar
    #     # - Palavras foneticamente similares
    #     # - Palavras do mesmo domínio semântico (se implementado)
    #     # - Palavras que o usuário confundiu anteriormente

    #     # Lógica placeholder: Usar palavras aleatórias do master list (exceto a correta)
    #     # Buscar algumas palavras aleatórias
    #     all_master_words = get_master_words(self.db, limit=100) # Buscar um pool maior para amostra
    #     distractor_words = [mw.word_text for mw in all_master_words if mw.word_text != word_text]

    #     num_distractors = 3 # Definir quantas opções falsas
    #     if len(distractor_words) < num_distractors:
    #         # Não há palavras suficientes para distratores
    #         logger.warning(f"Not enough words for distractors for '{word_text}'. Needed {num_distractors}, found {len(distractor_words)}.")
    #         return None # Ou gerar com menos distratores, dependendo da regra de negócio

    #     selected_distractor_texts = random.sample(distractor_words, num_distractors)

    #     # Obter definições para os distratores
    #     distractor_options: List[schemas.MultipleChoiceOption] = []
    #     for distractor_text in selected_distractor_texts:
    #          # TODO: O ideal é buscar a definição usando o WordInfoService, mas isso pode ser lento em massa.
    #          # Talvez o modelo MasterWord devesse incluir a definição básica ou um resumo.
    #          # Por enquanto, usar uma definição placeholder ou buscar individualmente (pode ser ineficiente).
    #          # Usar placeholder para evitar chamadas API em massa por enquanto.
    #          distractor_definition = f"Definição de {distractor_text} (placeholder)"
    #          # TODO: Buscar a definição real para os distratores.
    #          # distractor_info = await self.word_info_service._get_word_info_data_internal(distractor_text)
    #          # if distractor_info and distractor_info.definition:
    #          #      distractor_definition = distractor_info.definition

    #          distractor_options.append(schemas.MultipleChoiceOption(
    #               word_text=distractor_text,
    #               definition=distractor_definition
    #          ))

    #     # Criar a opção correta
    #     correct_option = schemas.MultipleChoiceOption(
    #          word_text=correct_word_info.text,
    #          definition=correct_word_info.definition
    #     )

    #     # Combinar e embaralhar todas as opções
    #     all_options = distractor_options + [correct_option]
    #     random.shuffle(all_options)

    #     # Construir o schema de resposta
    #     mcq_exercise_data = schemas.MultipleChoiceExercise(
    #         target_word_text=word_text,
    #         options=all_options,
    #         message="Selecione a definição correta." # Mensagem genérica, pode ser mais específica
    #     )

    #     logger.info(f"Dados de MCQ gerados para '{word_text}'.")
    #     return mcq_exercise_data

    # async def generate_mcq_image_exercise_data(self, word_text: str) -> Optional[schemas.MultipleChoiceImageExercise]:
    #     """
    #     Gera os dados necessários para um exercício de Múltipla Escolha (Imagem) para a palavra especificada.
    #     """
    #     logger.info(f"Gerando dados para exercício de Múltipla Escolha (Imagem) para '{word_text}'")

    #     # 1. Obter a URL da imagem e a definição correta da palavra usando WordInfoService
    #     word_info = await self.word_info_service._get_word_info_data_internal(word_text)
    #     if not word_info or not word_info.image_url or not word_info.definition:
    #         logger.warning(f"No image URL or definition found for '{word_text}'. Cannot generate MCQ Image exercise.")
    #         return None

    #     # 2. Gerar opções de distratores (definições)
    #     # Reutilizar a lógica de geração de distratores do MCQ de Definição
    #     # TODO: Refinar a geração de distratores especificamente para Imagem (ex: palavras com imagens visualmente similares?)

    #     # Lógica placeholder: Usar palavras aleatórias do master list (exceto a correta)
    #     all_master_words = get_master_words(self.db, limit=100) # Buscar um pool maior para amostra
    #     distractor_words = [mw.word_text for mw in all_master_words if mw.word_text != word_text]

    #     num_distractors = 3 # Definir quantas opções falsas
    #     if len(distractor_words) < num_distractors:
    #         logger.warning(f"Not enough words for distractors for MCQ Image for '{word_text}'. Needed {num_distractors}, found {len(distractor_words)}.")
    #         return None

    #     selected_distractor_texts = random.sample(distractor_words, num_distractors)

    #     # Obter definições para os distratores (usando placeholder por enquanto)
    #     distractor_options: List[schemas.MultipleChoiceOption] = []
    #     for distractor_text in selected_distractor_texts:
    #          # TODO: Buscar a definição real para os distratores.
    #          distractor_definition = f"Definição de {distractor_text} (placeholder)"
    #          distractor_options.append(schemas.MultipleChoiceOption(
    #               word_text=distractor_text,
    #               definition=distractor_definition
    #          ))

    #     # Criar a opção correta (usando a definição real)
    #     correct_option = schemas.MultipleChoiceOption(
    #          word_text=word_text,
    #          definition=word_info.definition
    #     )

    #     # Combinar e embaralhar todas as opções
    #     all_options = distractor_options + [correct_option]
    #     random.shuffle(all_options)

    #     # Construir o schema de resposta
    #     mcq_image_exercise_data = schemas.MultipleChoiceImageExercise(
    #         target_word_text=word_text,
    #         image_url=word_info.image_url,
    #         options=all_options,
    #         message="Selecione a definição que melhor descreve a imagem."
    #     )

    #     logger.info(f"Dados de MCQ Imagem gerados para '{word_text}'.")
    #     return mcq_image_exercise_data

    # async def generate_define_word_exercise_data(self, word_text: str) -> Optional[schemas.DefineWordExercise]:
    #     """
    #     Gera os dados necessários para um exercício de Definir Palavra.
    #     Este exercício pede ao usuário para fornecer a definição da palavra.
    #     """
    #     logger.info(f"Gerando dados para exercício de Definir Palavra para '{word_text}'")

    #     # Para este exercício, precisamos apenas da palavra alvo.
    #     # A validação da definição do usuário será feita no backend na submissão.
    #     # Poderíamos buscar a definição aqui para ter certeza que existe, mas não é estritamente necessário para gerar *os dados do exercício*.
    #     # No entanto, buscar a palavra info garante que a palavra é válida e que temos as métricas de complexidade.
    #     word_info = await self.word_info_service._get_word_info_data_internal(word_text)
    #     if not word_info:
    #          logger.warning(f"Word info not found for '{word_text}'. Cannot generate Define Word exercise.")
    #          return None

    #     define_word_data = schemas.DefineWordExercise(
    #         target_word_text=word_text,
    #         message="Forneça a definição da palavra."
    #     )

    #     logger.info(f"Dados de Definir Palavra gerados para '{word_text}'.")
    #     return define_word_data

    # async def generate_complete_sentence_exercise_data(self, word_text: str) -> Optional[schemas.CompleteSentenceExercise]:
    #     """
    #     Gera os dados necessários para um exercício de Completar Frase.
    #     Este exercício fornece uma frase com um placeholder para a palavra alvo.
    #     """
    #     logger.info(f"Gerando dados para exercício de Completar Frase para '{word_text}'")

    #     # TODO: Implementar lógica para gerar frases com placeholder.
    #     # Isso é complexo e requer um corpus de frases ou um modelo de geração de linguagem.
    #     # Por enquanto, usar um placeholder.

    #     # Precisamos obter a palavra info para garantir que a palavra é válida e temos complexidade.
    #     word_info = await self.word_info_service._get_word_info_data_internal(word_text)
    #     if not word_info:
    #          logger.warning(f"Word info not found for '{word_text}'. Cannot generate Complete Sentence exercise.")
    #          return None

    #     # Lógica placeholder para gerar a frase
    #     sentence_with_placeholder = f"A palavra '{word_text}' é essencial para completar esta frase: 'O [____] da questão era complexo.'"
    #     # TODO: Substituir por lógica real de geração de frase.

    #     complete_sentence_data = schemas.CompleteSentenceExercise(
    #         target_word_text=word_text,
    #         sentence_with_placeholder=sentence_with_placeholder,
    #         message="Complete a frase com a palavra correta."
    #     )

    #     logger.info(f"Dados de Completar Frase gerados para '{word_text}'.")
    #     return complete_sentence_data 