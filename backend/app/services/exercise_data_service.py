from typing import Dict, Any, List, Optional
from .. import schemas
import random # Necessário para embaralhar opções/distratores
import logging # Para logs

# Importar dependências necessárias
from sqlalchemy.orm import Session # Para interagir com o DB (se necessário)
from .word_info_service import WordInfoService # Para obter info das palavras
from ..crud import get_master_words # Para obter palavras mestras para distratores

logger = logging.getLogger(__name__)

class ExerciseDataService:
    def __init__(self, db: Session, word_info_service: WordInfoService):
        self.db = db
        self.word_info_service = word_info_service

    async def generate_multiple_choice_exercise_data(self, word_text: str) -> Optional[schemas.MultipleChoiceExercise]:
        """
        Gera os dados necessários para um exercício de Múltipla Escolha para a palavra especificada.
        """
        logger.info(f"Gerando dados para exercício de Múltipla Escolha para '{word_text}'")

        # 1. Obter a definição correta da palavra usando WordInfoService
        correct_word_info = await self.word_info_service._get_word_info_data_internal(word_text)
        if not correct_word_info or not correct_word_info.definition:
            logger.warning(f"No definition found for '{word_text}'. Cannot generate MCQ.")
            return None

        # 2. Gerar opções de distratores
        # TODO: Implementar lógica sofisticada para gerar distratores.
        # Ideias:
        # - Palavras com complexidade similar
        # - Palavras foneticamente similares
        # - Palavras do mesmo domínio semântico (se implementado)
        # - Palavras que o usuário confundiu anteriormente

        # Lógica placeholder: Usar palavras aleatórias do master list (exceto a correta)
        # Buscar algumas palavras aleatórias
        all_master_words = get_master_words(self.db, limit=100) # Buscar um pool maior para amostra
        distractor_words = [mw.word_text for mw in all_master_words if mw.word_text != word_text]

        num_distractors = 3 # Definir quantas opções falsas
        if len(distractor_words) < num_distractors:
            # Não há palavras suficientes para distratores
            logger.warning(f"Not enough words for distractors for '{word_text}'. Needed {num_distractors}, found {len(distractor_words)}.")
            return None # Ou gerar com menos distratores, dependendo da regra de negócio

        selected_distractor_texts = random.sample(distractor_words, num_distractors)

        # Obter definições para os distratores
        distractor_options: List[schemas.MultipleChoiceOption] = []
        for distractor_text in selected_distractor_texts:
             # TODO: O ideal é buscar a definição usando o WordInfoService, mas isso pode ser lento em massa.
             # Talvez o modelo MasterWord devesse incluir a definição básica ou um resumo.
             # Por enquanto, usar uma definição placeholder ou buscar individualmente (pode ser ineficiente).
             # Usar placeholder para evitar chamadas API em massa por enquanto.
             distractor_definition = f"Definição de {distractor_text} (placeholder)"
             # TODO: Buscar a definição real para os distratores.
             # distractor_info = await self.word_info_service._get_word_info_data_internal(distractor_text)
             # if distractor_info and distractor_info.definition:
             #      distractor_definition = distractor_info.definition

             distractor_options.append(schemas.MultipleChoiceOption(
                  word_text=distractor_text,
                  definition=distractor_definition
             ))

        # Criar a opção correta
        correct_option = schemas.MultipleChoiceOption(
             word_text=correct_word_info.text,
             definition=correct_word_info.definition
        )

        # Combinar e embaralhar todas as opções
        all_options = distractor_options + [correct_option]
        random.shuffle(all_options)

        # Construir o schema de resposta
        mcq_exercise_data = schemas.MultipleChoiceExercise(
            target_word_text=word_text,
            options=all_options,
            message="Selecione a definição correta." # Mensagem genérica, pode ser mais específica
        )

        logger.info(f"Dados de MCQ gerados para '{word_text}'.")
        return mcq_exercise_data

    async def generate_mcq_image_exercise_data(self, word_text: str) -> Optional[schemas.MultipleChoiceImageExercise]:
        """
        Gera os dados necessários para um exercício de Múltipla Escolha (Imagem) para a palavra especificada.
        """
        logger.info(f"Gerando dados para exercício de Múltipla Escolha (Imagem) para '{word_text}'")

        # 1. Obter a URL da imagem e a definição correta da palavra usando WordInfoService
        word_info = await self.word_info_service._get_word_info_data_internal(word_text)
        if not word_info or not word_info.image_url or not word_info.definition:
            logger.warning(f"No image URL or definition found for '{word_text}'. Cannot generate MCQ Image exercise.")
            return None

        # 2. Gerar opções de distratores (definições)
        # Reutilizar a lógica de geração de distratores do MCQ de Definição
        # TODO: Refinar a geração de distratores especificamente para Imagem (ex: palavras com imagens visualmente similares?)

        # Lógica placeholder: Usar palavras aleatórias do master list (exceto a correta)
        all_master_words = get_master_words(self.db, limit=100) # Buscar um pool maior para amostra
        distractor_words = [mw.word_text for mw in all_master_words if mw.word_text != word_text]

        num_distractors = 3 # Definir quantas opções falsas
        if len(distractor_words) < num_distractors:
            logger.warning(f"Not enough words for distractors for MCQ Image for '{word_text}'. Needed {num_distractors}, found {len(distractor_words)}.")
            return None

        selected_distractor_texts = random.sample(distractor_words, num_distractors)

        # Obter definições para os distratores (usando placeholder por enquanto)
        distractor_options: List[schemas.MultipleChoiceOption] = []
        for distractor_text in selected_distractor_texts:
             # TODO: Buscar a definição real para os distratores.
             distractor_definition = f"Definição de {distractor_text} (placeholder)"
             distractor_options.append(schemas.MultipleChoiceOption(
                  word_text=distractor_text,
                  definition=distractor_definition
             ))

        # Criar a opção correta (usando a definição real)
        correct_option = schemas.MultipleChoiceOption(
             word_text=word_text,
             definition=word_info.definition
        )

        # Combinar e embaralhar todas as opções
        all_options = distractor_options + [correct_option]
        random.shuffle(all_options)

        # Construir o schema de resposta
        mcq_image_exercise_data = schemas.MultipleChoiceImageExercise(
            target_word_text=word_text,
            image_url=word_info.image_url,
            options=all_options,
            message="Selecione a definição que melhor descreve a imagem."
        )

        logger.info(f"Dados de MCQ Imagem gerados para '{word_text}'.")
        return mcq_image_exercise_data

    async def generate_define_word_exercise_data(self, word_text: str) -> Optional[schemas.DefineWordExercise]:
        """
        Gera os dados necessários para um exercício de Definir Palavra.
        Este exercício pede ao usuário para fornecer a definição da palavra.
        """
        logger.info(f"Gerando dados para exercício de Definir Palavra para '{word_text}'")

        # Para este exercício, precisamos apenas da palavra alvo.
        # A validação da definição do usuário será feita no backend na submissão.
        # Poderíamos buscar a definição aqui para ter certeza que existe, mas não é estritamente necessário para gerar *os dados do exercício*.
        # No entanto, buscar a palavra info garante que a palavra é válida e que temos as métricas de complexidade.
        word_info = await self.word_info_service._get_word_info_data_internal(word_text)
        if not word_info:
             logger.warning(f"Word info not found for '{word_text}'. Cannot generate Define Word exercise.")
             return None

        define_word_data = schemas.DefineWordExercise(
            target_word_text=word_text,
            message="Forneça a definição da palavra."
        )

        logger.info(f"Dados de Definir Palavra gerados para '{word_text}'.")
        return define_word_data

    async def generate_complete_sentence_exercise_data(self, word_text: str) -> Optional[schemas.CompleteSentenceExercise]:
        """
        Gera os dados necessários para um exercício de Completar Frase.
        Este exercício fornece uma frase com um placeholder para a palavra alvo.
        """
        logger.info(f"Gerando dados para exercício de Completar Frase para '{word_text}'")

        # TODO: Implementar lógica para gerar frases com placeholder.
        # Isso é complexo e requer um corpus de frases ou um modelo de geração de linguagem.
        # Por enquanto, usar um placeholder.

        # Precisamos obter a palavra info para garantir que a palavra é válida e temos complexidade.
        word_info = await self.word_info_service._get_word_info_data_internal(word_text)
        if not word_info:
             logger.warning(f"Word info not found for '{word_text}'. Cannot generate Complete Sentence exercise.")
             return None

        # Lógica placeholder para gerar a frase
        sentence_with_placeholder = f"A palavra '{word_text}' é essencial para completar esta frase: 'O [____] da questão era complexo.'"
        # TODO: Substituir por lógica real de geração de frase.

        complete_sentence_data = schemas.CompleteSentenceExercise(
            target_word_text=word_text,
            sentence_with_placeholder=sentence_with_placeholder,
            message="Complete a frase com a palavra correta."
        )

        logger.info(f"Dados de Completar Frase gerados para '{word_text}'.")
        return complete_sentence_data 