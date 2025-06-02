from typing import Dict, Any, List, Optional
from .. import schemas
from datetime import datetime, timedelta # Necessário para a lógica de espaçamento
import random # Pode ser útil no futuro, manter por enquanto

class ScoringService:
    def __init__(self, weights: Dict[str, Dict[str, float]]):
        # Pesos para combinar os scores
        self.weights = weights

    def calculate_learning_efficiency(self, candidate: schemas.ExerciseCandidate, user_state: schemas.UserCognitiveState, word_progress: Optional[schemas.UserProgress]) -> float:
        # TODO: Implementar lógica detalhada conforme proposto
        # print(f"Calculating learning efficiency for {candidate.word_text} ({candidate.exercise_type})") # Placeholder

        # 1. Zona de Desenvolvimento Proximal (Challenge Score)
        difficulty_gap = candidate.difficulty - user_state.vocabular_ability # Usar a habilidade vocabular do estado do usuário

        # Definir os limites do sweet spot empírico (ajustáveis no futuro)
        sweet_spot_min = 0.2
        sweet_spot_max = 0.8

        if sweet_spot_min <= difficulty_gap <= sweet_spot_max:
            challenge_score = 1.0 # Score máximo na zona proximal
        else:
            # Penaliza exercícios muito fáceis ou muito difíceis
            # A penalidade deve ser maior quanto mais longe do sweet spot
            # Diferenciar penalidade para muito fácil (< sweet_spot_min) e muito difícil (> sweet_spot_max)?

            if difficulty_gap < sweet_spot_min:
                # Muito fácil: penalizar mais acentuadamente abaixo de um certo limite
                # Ex: penalidade aumenta linearmente para gap < 0.2, talvez mais rápido abaixo de 0
                # Se gap = 0.2, score = 1.0 (limite). Se gap = -0.5, score = 0.1 (exemplo limite inferior)
                # Faixa de gap a penalizar: (-inf, 0.2)
                # Mapear essa faixa para (0.1, 1.0)
                # Usar uma função que diminui rapidamente abaixo de 0.2.
                # Simples linear: score = 1.0 - (sweet_spot_min - difficulty_gap) * fator_penalidade_facil
                # fator_penalidade_facil = (1.0 - 0.1) / (0.2 - (-0.5)) = 0.9 / 0.7 ~ 1.28
                # Penalidade mais simples: linear do sweet_spot_min até 0.1 em -0.5
                # score = 0.1 + (difficulty_gap - (-0.5)) * slope
                # Simplificação: queda linear de 1.0 em 0.2 para 0.1 em -0.5
                # score = 1.0 - (0.2 - difficulty_gap) * (0.9 / 0.7)
                # Garantir mínimo de 0.1
                challenge_score = max(0.1, 1.0 - (sweet_spot_min - difficulty_gap) * 1.5) # Exemplo: penalidade mais acentuada abaixo de 0.2

            else: # difficulty_gap > sweet_spot_max (Muito difícil)
                # Penalizar suavemente acima do sweet spot_max, talvez com um teto mínimo mais alto que exercícios muito fáceis
                # Faixa de gap a penalizar: (0.8, +inf)
                # Queda linear de 1.0 em 0.8 para 0.3 (exemplo limite inferior para muito difícil) em 1.5 (exemplo gap)
                # score_range = 1.0 - 0.3 = 0.7
                # gap_range = 1.5 - 0.8 = 0.7
                # slope = 0.7 / 0.7 = 1.0
                # score = 1.0 - (difficulty_gap - sweet_spot_max) * 1.0
                # Garantir mínimo de 0.3
                challenge_score = max(0.3, 1.0 - (difficulty_gap - sweet_spot_max) * 1.0) # Exemplo: penalidade mais suave acima de 0.8, com piso mais alto

            # Garantir que o score não ultrapasse 1.0 (embora as fórmulas acima comecem em 1.0)
            challenge_score = min(1.0, challenge_score)

        # TODO: Refinar os limites (sweet_spot_min, sweet_spot_max) e as funções de pontuação com base em dados empíricos no futuro.
        # Considerar diferentes funções (ex: sigmoid) para suavizar as transições.

        # 2. Retrieval Strength (Teoria do Esquecimento - Spacing)
        spacing_score = 0.0 # Valor padrão se não houver progresso ou lógica
        if word_progress and word_progress.last_seen_on_word:
            time_since_last_seen = datetime.utcnow() - word_progress.last_seen_on_word

            # TODO: Implementar cálculo do intervalo ótimo de forma adaptativa (curva de retenção) - **Este é um ponto chave de refinamento futuro.**
            # O intervalo ótimo deve depender da palavra (complexidade, histórico de acertos) e do usuário.
            # Por enquanto, usar um intervalo ótimo simplificado (ex: 3 dias)
            simplified_optimal_interval = timedelta(days=3) # Exemplo fixo

            # Lógica de pontuação de espaçamento (aumenta até o ótimo, diminui depois) - Manter por enquanto
            ratio = time_since_last_seen / simplified_optimal_interval
            if ratio <= 1.0:
                spacing_score = ratio # Aumenta linearmente até o ótimo
            else:
                spacing_score = 1.0 * (simplified_optimal_interval / time_since_last_seen) # Diminui suavemente após o ótimo (ex: 1/ratio)
            spacing_score = max(0.1, min(1.0, spacing_score)) # Limita entre 0.1 e 1.0

        # 3. Transfer Potential
        # Focar em palavras cuja complexidade composta está ligeiramente acima da expertise do usuário.
        # Isso maximiza a oportunidade de aplicar conhecimento existente (transferência positiva)
        # sem ser avassalador (minimiza transferência negativa ou interferência).

        word_composite_complexity = candidate.word_complexity_score # Usar o score composto
        # TODO: Refinar para usar a expertise específica do domínio relevante se domain_expertise se tornar granular
        user_expertise = user_state.domain_expertise.get('overall', user_state.vocabular_ability) # Usar 'overall' ou vocabular_ability como fallback

        # Definir a zona alvo para o potencial de transferência (ex: complexidade 1-2 pontos acima da expertise)
        target_complexity_min = user_expertise + 1.0
        target_complexity_max = user_expertise + 2.0

        transfer_score = 0.0 # Valor base

        if target_complexity_min <= word_composite_complexity <= target_complexity_max:
             # Score máximo na zona alvo
             transfer_score = 1.0
        else:
             # Penalizar palavras significativamente mais fáceis ou mais difíceis que a zona alvo
             # A penalidade aumenta quanto mais distante a complexidade da palavra estiver da zona alvo.

             if word_composite_complexity < target_complexity_min:
                  # Palavra muito mais fácil que a zona alvo
                  # Penalidade aumenta linearmente ou exponencialmente à medida que a complexidade diminui
                  # Exemplo: score cai de 1.0 em target_complexity_min para 0.1 em target_complexity_min - 3.0
                  penalty_range = 3.0 # A complexidade pode ser até 3 pontos abaixo da zona alvo antes de atingir o piso
                  score_range = 1.0 - 0.1 # De 1.0 a 0.1
                  slope = score_range / penalty_range # Inclinação da penalidade

                  transfer_score = max(0.1, 1.0 - (target_complexity_min - word_composite_complexity) * slope)

             else: # word_composite_complexity > target_complexity_max
                  # Palavra muito mais difícil que a zona alvo
                  # Penalidade semelhante, mas talvez com um piso um pouco mais alto
                  # Exemplo: score cai de 1.0 em target_complexity_max para 0.3 em target_complexity_max + 4.0
                  penalty_range = 4.0 # A complexidade pode ser até 4 pontos acima da zona alvo antes de atingir o piso
                  score_range = 1.0 - 0.3 # De 1.0 a 0.3
                  slope = score_range / penalty_range

                  transfer_score = max(0.3, 1.0 - (word_composite_complexity - target_complexity_max) * slope)

        # Garantir que o score esteja entre 0 e 1 (as funções max/min já ajudam, mas bom garantir)
        transfer_score = max(0.0, min(1.0, transfer_score))

        # TODO: Refinar a lógica de Transfer Potential significativamente.
        # Os limites (1-2 pontos acima da expertise) e as funções de penalidade são heurísticas iniciais.
        # A métrica domain_expertise é um proxy muito geral. Idealmente, usar expertise por domínio.

        # Combinar os scores com pesos
        learning_efficiency = (challenge_score * self.weights['learning_efficiency']['challenge'] +
                             spacing_score * self.weights['learning_efficiency']['spacing'] +
                             transfer_score * self.weights['learning_efficiency']['transfer'])

        # TODO: Refinar pesos e as funções de pontuação para cada fator (pesos já estruturados)

        return learning_efficiency

    def calculate_engagement_factor(self, candidate: schemas.ExerciseCandidate, user_history: List[schemas.UserProgress], user_state: schemas.UserCognitiveState) -> float:
        # TODO: Implementar lógica detalhada conforme proposto
        # print(f"Calculating engagement factor for {candidate.word_text} ({candidate.exercise_type})") # Placeholder

        # 1. Novelty Score - Manter lógica existente
        # Precisamos obter os tipos de exercício dos N exercícios mais recentes do user_history
        # Supondo que user_history está ordenado do mais antigo para o mais recente para este exemplo simplificado
        recent_exercise_types = [p.exercise_type for p in user_history[-10:]] # Pegar os últimos 10

        # Evitar divisão por zero se não houver histórico
        if not recent_exercise_types:
            novelty = 1.0 # Considerar alta novidade se não houver histórico recente
        else:
            novelty = 1.0 - (recent_exercise_types.count(candidate.exercise_type) / len(recent_exercise_types))


        # 2. Personal Interest
        # Usar a semantic_abstraction como um proxy para o interesse intelectual ou a novidade do conceito.
        # Combinar com a expertise do usuário no domínio geral (ou futuro: domínio específico).
        # TODO: Refinar Personal Interest.
        # user_state.domain_expertise é um proxy.

        # Mapear semantic_abstraction para um score de interesse.
        # Palavras com abstração média-alta podem ser mais interessantes, as muito baixas ou muito altas podem ser menos.
        # Exemplo simples: usar uma função quadrática invertida ou gaussiana centrada em um valor ideal (ex: 6.0 numa escala de 0-10)
        ideal_abstraction_for_interest = 6.0
        abstraction_deviation = abs(candidate.complexity_metrics.semantic_abstraction - ideal_abstraction_for_interest)
        # Score diminui quanto maior a deviation. Score máximo (1.0) na ideal_abstraction.
        # Função simples: score = 1.0 - (deviation / max_possible_deviation)
        max_abstraction_deviation = max(ideal_abstraction_for_interest - 0, 10 - ideal_abstraction_for_interest) # Considerar a maior distância possível
        personal_interest_by_abstraction = 1.0 - (abstraction_deviation / max_abstraction_deviation) if max_abstraction_deviation > 0 else 1.0
        personal_interest_by_abstraction = max(0.0, min(1.0, personal_interest_by_abstraction)) # Limitar entre 0 e 1

        # Ajustar o interesse pela expertise do usuário. Usuários com maior expertise podem se interessar por palavras mais complexas.
        # TODO: Refinar para usar a expertise específica do domínio relevante se domain_expertise se tornar granular
        user_expertise = user_state.domain_expertise.get('overall', user_state.vocabular_ability) # Usar 'overall' ou vocabular_ability como fallback

        # Exemplo: penalizar interesse se a palavra for muito fácil para a expertise do usuário.
        expertise_adjusted_interest = personal_interest_by_abstraction
        if candidate.word_complexity_score < user_expertise * 0.5: # Exemplo: se complexidade < metade da expertise
            expertise_adjusted_interest *= 0.5 # Reduzir o interesse

        personal_interest_score = expertise_adjusted_interest # Usar o score ajustado

        # 3. Achievement Proximity
        # Baseado na acurácia média do usuário (geral ou para exercícios similares).
        # TODO: Refinar Achievement Proximity.
        # A acurácia média geral pode ser um proxy, mas o ideal é acurácia em exercícios similares ou palavras de complexidade semelhante.
        
        # Calcular acurácia média geral do histórico (manter por enquanto)
        total_correct = sum(p.correct_attempts for p in user_history)
        total_attempts = sum(p.total_attempts for p in user_history)
        average_accuracy = total_correct / total_attempts if total_attempts > 0 else 0.5 # Acúrcia 50% se não houver histórico

        # Score aumenta quanto maior a acurácia média.
        achievement_proximity_score = average_accuracy # Mapeamento direto (0 a 1)

        # TODO: Considerar a acurácia em exercícios de *tipo similar* ou palavras de *complexidade similar*.

        # Combinar os scores com pesos
        engagement_factor = (novelty * self.weights['engagement_factor']['novelty'] +
                             personal_interest_score * self.weights['engagement_factor']['interest'] +
                             achievement_proximity_score * self.weights['engagement_factor']['achievement'])

        # TODO: Refinar pesos e as funções de pontuação para cada fator

        return engagement_factor

    def calculate_frustration_risk(self, candidate: schemas.ExerciseCandidate, recent_performance: List[schemas.UserProgress], user_state: schemas.UserCognitiveState) -> float:
        # TODO: Implementar lógica detalhada conforme proposto
        # print(f"Calculating frustration risk for {candidate.word_text} ({candidate.exercise_type})") # Placeholder

        # 1. Consecutive Failures - Manter lógica existente
        consecutive_failures = 0
        # Iterar do mais recente para o mais antigo para contar falhas consecutivas
        # TODO: Refinar Consecutive Failures.
        # Requer dados mais granulares sobre cada *tentativa* ou um indicador claro de sucesso/falha por exercício no UserProgress.
        # A lógica atual é simplificada e pode não refletir falhas reais de forma precisa.
        for progress in reversed(recent_performance):
             is_failure = False # Placeholder
             # Exemplo simplificado: considerar falha se acurácia for 0 na última tentativa para esta palavra/tipo
             # Isso pode não ser preciso. Uma falha pode ser 0 acertos em N tentativas em uma única sessão.
             # Idealmente, UserProgress rastrearia tentativas individuais dentro de uma sessão ou teria um flag de sucesso/falha.

             # Lógica temporária: Se a última entrada para ESTE candidato (palavra+tipo) teve acurácia 0 e total_attempts > 0
             # No entanto, recent_performance é uma lista geral. Precisamos encontrar a entrada específica para o candidato.
             # Uma abordagem mais simples: se a ÚLTIMA entrada no histórico geral foi uma falha geral.
             # Isso não é ideal pois pode ser falha em outra palavra/tipo.
             # Vamos manter a contagem simples baseada no histórico geral recente, mas reconhecer que é impreciso.
             if progress.total_attempts > 0 and progress.correct_attempts == 0: # Exemplo simplificado para qualquer exercício recente
                 is_failure = True
             # TODO: Implementar lógica mais robusta para falhas consecutivas para O CANDIDATO ESPECÍFICO ou para o usuário em geral em exercícios SIMILARES.

             if is_failure:
                 consecutive_failures += 1
             else:
                 # Considerar que um sucesso quebra a sequência de falhas.
                 # TODO: Isso só funciona se recent_performance for ordenado corretamente e incluir sucessos.
                 break # Quebra o loop se encontrar um sucesso (ou algo que não seja falha)

        failure_risk = min(consecutive_failures / 3.0, 1.0) # Risco aumenta com falhas, teto em 3 falhas (ajustar limite)
        # TODO: Ajustar limite de falhas consecutivas e a função de risco com base em dados empíricos.


        # 2. Complexity Jump
        # Aprimorar usando métricas de complexidade específicas e, idealmente, a complexidade do último exercício completo.
        # TODO: Refinar Complexity Jump.
        # Obter a complexidade (composite_score) do *último exercício completo* pelo usuário.
        # Isso requer armazenar a complexidade do exercício no UserProgress ou vincular o UserProgress a um registro de exercício detalhado.
        # Por enquanto, comparar com a habilidade vocabular do usuário e com métricas de complexidade específicas.

        # Comparação com habilidade vocabular (manter como fator base)
        complexity_jump_from_ability = candidate.difficulty - user_state.vocabular_ability
        jump_risk_ability = max(0.0, (complexity_jump_from_ability - 1.0) / 2.0) # Risco aumenta se > 1.0 acima, limitado a 1.0
        jump_risk_ability = min(jump_risk_ability, 1.0)

        # Considerar saltos em métricas específicas (ex: Sintaxe, Morfologia).
        # Se a complexidade sintática da candidata é muito maior que a média das palavras recentes do usuário (com sucesso), pode indicar risco.
        # Isso requer calcular médias de complexidade do histórico recente, o que é complexo agora.

        # Lógica simplificada: Se a complexidade SINTÁTICA ou MORFOLÓGICA do candidato é muito alta E a habilidade vocabular do usuário é baixa,
        # pode haver um risco maior de frustração.
        complexity_metric_jump_risk = 0.0
        # Exemplo: Se syntactic_complexity > 8 E vocabular_ability < 5
        if candidate.complexity_metrics.syntactic_complexity > 8 and user_state.vocabular_ability < 5:
            complexity_metric_jump_risk += 0.2 # Adiciona um risco base de 0.2
        # Exemplo: Se morphological_density > 7 E vocabular_ability < 6
        if candidate.complexity_metrics.morphological_density > 7 and user_state.vocabular_ability < 6:
             complexity_metric_jump_risk += 0.2 # Adiciona outro risco base

        complexity_metric_jump_risk = min(complexity_metric_jump_risk, 1.0) # Limita o risco máximo

        # Combinar os riscos de salto (geral vs. métricas específicas)
        jump_risk = max(jump_risk_ability, complexity_metric_jump_risk) # Usar o risco maior entre os dois cálculos
        # TODO: Refinar como combinar estes riscos ou focar em uma abordagem mais unificada.

        # 3. Fatigue Level - Manter lógica existente (contagem de exercícios recentes)
        # TODO: Implementar rastreamento de duração da sessão ou usar métricas de tempo dos exercícios recentes.
        num_recent_exercises = len(recent_performance)
        fatigue_risk = min(num_recent_exercises / 10.0, 1.0) # Exemplo: 10 exercícios recentes = 100% fadiga (ajustar limite)
        # TODO: Ajustar limite e função de fadiga.

        # 4. Error Pattern Analysis
        # Analisar a variância na acurácia dos exercícios recentes. Alta variância pode indicar padrão de erros ou dificuldade de consolidação.
        accuracies = []
        for progress in recent_performance:
            if progress.total_attempts > 0:
                accuracies.append(progress.correct_attempts / progress.total_attempts)

        error_pattern_risk = 0.0
        if len(accuracies) > 1:
            # Calcular a variância das acurácias
            mean_accuracy = sum(accuracies) / len(accuracies)
            variance = sum([(x - mean_accuracy) ** 2 for x in accuracies]) / len(accuracies)

            # Mapear a variância para um score de risco (quanto maior a variância, maior o risco)
            # Isso é uma heurística inicial e pode precisar de ajuste.
            # Exemplo: uma variância de 0.1 pode ser baixo risco, 0.5 alto risco.
            # Podemos usar uma função que aumenta com a variância, talvez com um teto.
            # Função simples: risco = variância * fator (ex: 2.0)
            error_pattern_risk = min(variance * 2.0, 1.0) # Limitar o risco a 1.0

        # TODO: Refinar Error Pattern Analysis.
        # Requer dados mais granulares sobre as *respostas individuais* do usuário (qual opção escolheu, quais erros cometeu).
        # Isso permitiria identificar padrões como confusão semântica, erros morfológicos recorrentes, etc.
        # A abordagem atual baseada em variância de acurácia é um proxy muito limitado.

        # TODO: Refinar a lógica de Error Pattern Analysis.
        # Considerar padrões de erros específicos por tipo de exercício ou complexidade.
        # Requer dados mais granulares sobre as tentativas e erros.

        # Combinar os scores com pesos (exemplo: 0.4 falhas, 0.4 salto, 0.2 fadiga/erro)
        # TODO: Definir estes pesos como atributos da classe ou em config. Usar nomes de pesos claros.
        frustration_risk = (failure_risk * self.weights['frustration_risk']['failures'] +
                             jump_risk * self.weights['frustration_risk']['jump'] +
                             fatigue_risk * self.weights['frustration_risk']['fatigue'] +
                             error_pattern_risk * self.weights['frustration_risk']['error_pattern'])

        # TODO: Refinar pesos e as funções de pontuação para cada fator

        return frustration_risk 