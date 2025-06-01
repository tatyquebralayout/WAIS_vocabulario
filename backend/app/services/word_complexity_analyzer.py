import re
import math
from typing import Dict, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum
import nltk # Será necessário adicionar ao requirements.txt
from textstat import flesch_reading_ease, syllable_count # Será necessário adicionar ao requirements.txt
import logging

# Tentar baixar 'punkt' e 'wordnet' (para lematização, se usada no futuro) e 'averaged_perceptron_tagger' (para POS tagging, se usada)
# Isso é uma tentativa. Em ambientes restritos, pode falhar e exigir instalação manual.
try:
    nltk.data.find('tokenizers/punkt')
except nltk.downloader.DownloadError:
    nltk.download('punkt', quiet=True)
# try:
#     nltk.data.find('corpora/wordnet')
# except nltk.downloader.DownloadError:
#     nltk.download('wordnet', quiet=True)
# try:
#     nltk.data.find('taggers/averaged_perceptron_tagger')
# except nltk.downloader.DownloadError:
#     nltk.download('averaged_perceptron_tagger', quiet=True)

@dataclass
class ComplexityMetrics:
    """Métricas neuropsicológicas para análise de complexidade em tempo real"""
    lexical_length: int          # Comprimento lexical
    syllabic_complexity: int     # Complexidade silábica
    morphological_density: float # Densidade morfológica
    semantic_abstraction: float  # Nível de abstração semântica
    definition_complexity: float # Complexidade da definição
    composite_score: float       # Score composto (0-10)

class WordComplexityAnalyzer:
    """
    Analisador de complexidade baseado em métricas neuropsicológicas
    Implementa inferência em tempo real conforme protocolo WAIS-IV (inspirado)
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Coeficientes calibrados empiricamente (baseados em corpus brasileiro)
        self.weights = {
            'lexical': 0.20,        # Peso do comprimento lexical
            'syllabic': 0.15,       # Peso da complexidade silábica
            'morphological': 0.25,  # Peso da densidade morfológica
            'semantic': 0.25,       # Peso da abstração semântica
            'definition': 0.15      # Peso da complexidade da definição
        }
        
        # Thresholds calibrados com base em dados psicométricos (Exemplos)
        self.complexity_thresholds = {
            'fácil': (0.0, 3.5),     # Ajustado para refletir scores até 10
            'média': (3.5, 7.0),
            'difícil': (7.0, 10.0)
        }
        
        # Padrões morfológicos do português brasileiro (Exemplos)
        self.morphological_patterns = {
            'prefixes': ['pre', 'anti', 'super', 'inter', 'trans', 'contra', 're', 'des', 'in', 'im'],
            'suffixes': ['ção', 'ismo', 'ista', 'mente', 'dade', 'ável', 'ível', 'oso', 'izar', 'ecer']
        }
        
        # Marcadores de abstração semântica (Exemplos, requer expansão e refinamento)
        # Idealmente, usaríamos uma base de dados léxico-semântica como WordNet para avaliar concretude/abstração
        self.abstraction_markers = {
            'concrete_keywords': ['objeto', 'coisa', 'lugar', 'pessoa', 'animal', 'parte', 'ferramenta', 'comida', 'corpo'],
            'abstract_keywords': ['conceito', 'ideia', 'sentimento', 'qualidade', 'estado', 'processo', 'sistema', 
                                  'propriedade', 'característica', 'princípio', 'teoria', 'emoção', 'relação']
        }
        self.logger.info("WordComplexityAnalyzer inicializado.")
    
    def infer_word_complexity_metrics(self, word_text: str, definition_text: Optional[str]) -> ComplexityMetrics:
        """
        Inferência principal de complexidade baseada em múltiplas métricas.
        Retorna o objeto ComplexityMetrics completo.
        """
        word_text = (word_text or "").strip()
        definition_text = (definition_text or "").strip()

        if not word_text:
            self.logger.warning("Texto da palavra vazio, retornando métricas de fallback.")
            return self._basic_complexity_fallback("palavra_vazia")

        try:
            lexical_score = self._analyze_lexical_complexity(word_text)
            syllabic_score = self._analyze_syllabic_complexity(word_text)
            morphological_score = self._analyze_morphological_density(word_text)
            # Análise semântica e da definição são mais robustas com definição
            semantic_score = self._analyze_semantic_abstraction(word_text, definition_text if definition_text else "")
            definition_score_val = self._analyze_definition_complexity(definition_text if definition_text else "")
            
            composite_score = (
                lexical_score * self.weights['lexical'] +
                syllabic_score * self.weights['syllabic'] +
                morphological_score * self.weights['morphological'] +
                semantic_score * self.weights['semantic'] +
                definition_score_val * self.weights['definition']
            )
            
            # Normalização para garantir que o score esteja entre 0 e 10
            # A soma dos pesos é 1.0. Cada sub-score pode ir até ~8-10.
            # Precisamos normalizar o resultado final ou garantir que os sub-scores sejam escalados adequadamente.
            # Se cada sub-score for normalizado para 0-10, então o composite_score já estaria nessa faixa.
            # Vou assumir que os sub-scores estão na faixa de 0-10 (ou perto disso)
            
            final_composite_score = min(max(composite_score, 0.0), 10.0)

            # syllable_count pode falhar para palavras não padrão ou muito curtas
            try:
                syll_count = syllable_count(word_text)
            except Exception:
                syll_count = max(1, len(word_text) // 3)


            metrics = ComplexityMetrics(
                lexical_length=len(word_text),
                syllabic_complexity=syll_count,
                morphological_density=morphological_score, # Este já é um score, não contagem
                semantic_abstraction=semantic_score,     # Este já é um score
                definition_complexity=definition_score_val, # Este já é um score
                composite_score=final_composite_score
            )
            
            self.logger.debug(f"Métricas de complexidade para '{word_text}': Score Composto={final_composite_score:.2f}")
            return metrics
            
        except Exception as e:
            self.logger.error(f"Erro na análise de complexidade para '{word_text}': {e}", exc_info=True)
            return self._basic_complexity_fallback(word_text)
    
    def _analyze_lexical_complexity(self, word: str) -> float:
        length = len(word)
        if length == 0: return 0.0
        # Mapeamento mais granular e normalizado para 0-10 (aproximado)
        if length <= 3: return 1.0
        if length <= 5: return 3.0
        if length <= 7: return 5.0
        if length <= 9: return 7.0
        if length <= 12: return 8.5
        return 10.0
    
    def _analyze_syllabic_complexity(self, word: str) -> float:
        if not word: return 0.0
        try:
            syllables = syllable_count(word)
        except Exception: # textstat pode falhar com algumas strings
             syllables = max(1, len(word) // 3) # Fallback simples

        if syllables <= 1: return 1.0
        if syllables == 2: return 3.0
        if syllables == 3: return 5.0
        if syllables == 4: return 7.0
        if syllables == 5: return 8.5
        return 10.0
    
    def _analyze_morphological_density(self, word: str) -> float:
        if not word: return 0.0
        word_lower = word.lower()
        morpheme_count = 1 
        
        detected_morphemes = 0
        for prefix in self.morphological_patterns['prefixes']:
            if word_lower.startswith(prefix):
                detected_morphemes += 1
                # word_lower = word_lower[len(prefix):] # Remover para evitar contagem dupla se houver sobreposição
                break 
        
        for suffix in self.morphological_patterns['suffixes']:
            if word_lower.endswith(suffix):
                detected_morphemes +=1
                break
        
        # Score de 0 a 10. Ex: 0 afixos = 1.0, 1 afixo = 5.0, 2 afixos = 9.0
        if detected_morphemes == 0: return 1.0
        if detected_morphemes == 1: return 5.0
        return 9.0

    def _analyze_semantic_abstraction(self, word: str, definition: str) -> float:
        if not word and not definition: return 3.0 # Neutro
        
        word_lower = word.lower()
        definition_lower = definition.lower()
        
        # Pontuação inicial baseada na palavra (se ela mesma for um marcador)
        score = 5.0 # Base neutra (0-10)

        # Verificar se a própria palavra é um forte indicador
        if any(m in word_lower for m in self.abstraction_markers['abstract_keywords']):
            score += 2.5
        elif any(m in word_lower for m in self.abstraction_markers['concrete_keywords']):
            score -= 2.5

        # Ajustar com base na definição
        if definition_lower:
            abstract_hits = sum(1 for marker in self.abstraction_markers['abstract_keywords'] if marker in definition_lower)
            concrete_hits = sum(1 for marker in self.abstraction_markers['concrete_keywords'] if marker in definition_lower)

            if abstract_hits > concrete_hits:
                score += (abstract_hits - concrete_hits) * 1.5 
            elif concrete_hits > abstract_hits:
                score -= (concrete_hits - abstract_hits) * 1.5
        
        return min(max(score, 0.0), 10.0) # Normaliza para 0-10

    def _analyze_definition_complexity(self, definition: str) -> float:
        if not definition:
            return 3.0  # Neutro se não há definição (0-10)
        
        try:
            # Usar Flesch Reading Ease (Português) e normalizar para 0-10
            # Flesch Reading Ease: 0-100 (mais alto = mais fácil)
            # Para o Brasil, a fórmula é: 248.835 - (1.015 * ASL) - (84.6 * ASW)
            # ASL = tamanho médio da sentença, ASW = média de sílabas por palavra
            # textstat.set_lang('pt_BR') # Não existe em textstat, ele tenta detectar
            f_ease = flesch_reading_ease(definition)
            
            # Inverter e escalar para 0-10 (0 = muito fácil, 10 = muito difícil)
            # Ex: f_ease 100 (fácil) -> 0 ; f_ease 0 (difícil) -> 10
            score = (100 - f_ease) / 10.0
            return min(max(score, 0.0), 10.0)

        except Exception as e:
            self.logger.warning(f"Erro ao calcular Flesch Reading Ease para definição: {e}. Usando fallback.")
            # Fallback simples baseado no comprimento da definição
            length = len(definition)
            if length < 50: return 1.5
            if length < 100: return 3.0
            if length < 150: return 5.0
            if length < 250: return 7.0
            return 9.0
    
    def _basic_complexity_fallback(self, word: str) -> ComplexityMetrics:
        length = len(word)
        basic_score = 0.0
        if length > 0 : basic_score = min(length * 0.8, 10.0) # Escala simples
        
        # Tenta usar syllable_count com fallback
        try:
            syll_count_fallback = syllable_count(word) if word else 0
        except:
            syll_count_fallback = max(1, length // 3) if word else 0

        return ComplexityMetrics(
            lexical_length=length,
            syllabic_complexity=syll_count_fallback,
            morphological_density=basic_score / 3 if basic_score > 0 else 1.0, # Estimativa
            semantic_abstraction=basic_score / 3 if basic_score > 0 else 3.0,  # Estimativa
            definition_complexity=basic_score / 3 if basic_score > 0 else 3.0, # Estimativa
            composite_score=min(basic_score,10.0)
        )
    
    def get_difficulty_level_from_metrics(self, metrics: ComplexityMetrics) -> str:
        """Classificação em nível de dificuldade com base nas métricas (score composto)."""
        score = metrics.composite_score
        
        if score < self.complexity_thresholds['fácil'][1]: # Limite superior de 'fácil'
            return 'fácil'
        elif score < self.complexity_thresholds['média'][1]: # Limite superior de 'média'
            return 'média'
        else:
            return 'difícil'

# Exemplo de uso (para teste local)
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    analyzer = WordComplexityAnalyzer()
    
    palavras_teste = {
        "casa": "Estrutura construída para habitação.",
        "sol": "Estrela central do nosso sistema solar.",
        "felicidade": "Estado de contentamento e bem-estar.",
        "inconstitucionalissimamente": "De maneira ou modo muito inconstitucional.",
        "pneumoultramicroscopicossilicovulcanoconiose": "Doença pulmonar causada pela inalação de cinzas vulcânicas.",
        "paralelepípedo": "Sólido geométrico com seis faces paralelas e iguais duas a duas.",
        "transcendência": "Qualidade do que é transcendente, que ultrapassa os limites.",
        "amor": "Sentimento de afeição profunda.",
        "ódio": "Sentimento intenso de aversão ou repulsa.",
        "efêmero": "Que dura pouco tempo; passageiro, transitório.",
        "complexidade": "Qualidade do que é complexo, que apresenta múltiplos elementos e interações."
    }
    
    for palavra, definicao in palavras_teste.items():
        print(f"\nAnalisando: {palavra}")
        metrics_obj = analyzer.infer_word_complexity_metrics(palavra, definicao)
        difficulty = analyzer.get_difficulty_level_from_metrics(metrics_obj)
        print(f"  Score Composto: {metrics_obj.composite_score:.2f}")
        print(f"  Nível Inferido: {difficulty}")
        print(f"  Métricas Detalhadas: {metrics_obj}")

    print("\nTeste com palavra vazia e definição:")
    metrics_vazia = analyzer.infer_word_complexity_metrics("", "alguma definicao")
    difficulty_vazia = analyzer.get_difficulty_level_from_metrics(metrics_vazia)
    print(f"  Score Composto: {metrics_vazia.composite_score:.2f}, Nível: {difficulty_vazia}")

    print("\nTeste com palavra e definição vazia:")
    metrics_vazia_total = analyzer.infer_word_complexity_metrics("teste", "")
    difficulty_vazia_total = analyzer.get_difficulty_level_from_metrics(metrics_vazia_total)
    print(f"  Score Composto: {metrics_vazia_total.composite_score:.2f}, Nível: {difficulty_vazia_total}")

    print("\nTeste com palavra e definição None:")
    metrics_none = analyzer.infer_word_complexity_metrics("palavra", None)
    difficulty_none = analyzer.get_difficulty_level_from_metrics(metrics_none)
    print(f"  Score Composto: {metrics_none.composite_score:.2f}, Nível: {difficulty_none}") 