import os
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.background import BackgroundTasks
from typing import Optional, Dict, Any, Callable
import asyncio
import logging

# Importar schemas de schemas.py
from . import schemas
# Se o acima falhar em tempo de execução devido à forma como o FastAPI carrega, pode precisar de ajuste para o projeto
# from app import schemas # Alternativa se estiver executando de um diretório pai

from .services.word_complexity_analyzer import WordComplexityAnalyzer, ComplexityMetrics as ComplexityMetricsDataclass
# As instâncias dos serviços de API serão injetadas

class WordInfoService:

    """
    Serviço principal para obtenção e análise de palavras
    Integra todas as APIs e análises 
    """   
    def __init__(self, dictionary_api_service: Any, image_api_service: Any, tts_api_service: Any, static_files_dir: str):
        self.dictionary_api = dictionary_api_service
        self.image_api = image_api_service
        self.tts_service = tts_api_service
        self.complexity_analyzer = WordComplexityAnalyzer() # WordComplexityAnalyzer é instanciado aqui
        self.logger = logging.getLogger(__name__)
        self.static_files_dir = static_files_dir
        
        self.complexity_cache: Dict[str, ComplexityMetricsDataclass] = {}
        self._last_cache_hit = False # Para rastrear o hit do cache de complexidade
        self.logger.info("WordInfoService inicializado.")

    # Informações da request atual, a serem definidas pelo endpoint antes de chamar get_word_info
    # Isso é um work-around. Idealmente, seriam passadas como argumentos ou via dependência mais robusta.
    current_request_base_url: str = ""
    current_app_url_path_for: Optional[Callable] = None 

    async def get_word_info(self, word_text: str) -> schemas.WordInfoResponse:
        """
        Endpoint-facing method to get word info, including URL construction.
        """
        original_word_text = word_text # Manter o texto original para a resposta
        normalized_word_text = word_text.strip().lower()
        
        try:
            if not self._validate_word(normalized_word_text):
                self.logger.warning(f"Palavra inválida fornecida: '{original_word_text}'")
                raise HTTPException(status_code=400, detail=f"Palavra inválida: '{original_word_text}'. Deve ser alfabética e ter entre 2 e 30 caracteres.")
            
            self.logger.info(f"Iniciando processamento para: '{normalized_word_text}' (via endpoint)")
            
            # Chamada para o novo método interno para obter os dados base
            word_data_internal = await self._get_word_info_data_internal(normalized_word_text)
            
            # Constrói a URL do áudio AQUI, usando as informações da request
            audio_url = None
            # Obter o nome do ficheiro de áudio de forma segura
            audio_filename = word_data_internal.get('audio_filename')

            # Verificar se o nome do ficheiro e as dependências da request estão disponíveis
            if audio_filename and self.current_request_base_url and self.current_app_url_path_for:
                 try:
                      # Construir o caminho estático para o áudio
                      audio_path = f'audio/{audio_filename}'
                      # Construir a URL completa usando as informações da request e o caminho estático
                      audio_url = f"{self.current_request_base_url.rstrip('/')}{self.current_app_url_path_for('static', path=audio_path)}"
                      self.logger.info(f"Áudio URL para '{normalized_word_text}' (endpoint): {audio_url}")
                 except Exception as e:
                      self.logger.error(f"Erro ao construir URL de áudio para '{normalized_word_text}': {e}", exc_info=True)
            elif audio_filename:
                # Caso o nome do ficheiro exista mas as informações da request não
                self.logger.warning(f"Não foi possível construir URL completa para o áudio '{audio_filename}' de '{normalized_word_text}' (request_base_url ou app_url_path_for não definidos no serviço)")

            # Monta a resposta final para o endpoint
            response = schemas.WordInfoResponse(
                text=original_word_text,
                definition=word_data_internal['definition'],
                image_url=word_data_internal['image_url'],
                audio_url=audio_url, # Usar a URL construída
                inferred_complexity_score=word_data_internal['complexity_metrics'].composite_score,
                complexity_metrics=schemas.ComplexityBreakdownSchema(
                    lexical_length=word_data_internal['complexity_metrics'].lexical_length,
                    syllabic_complexity=word_data_internal['complexity_metrics'].syllabic_complexity,
                    morphological_density=word_data_internal['complexity_metrics'].morphological_density,
                    semantic_abstraction=word_data_internal['complexity_metrics'].semantic_abstraction,
                    definition_complexity=word_data_internal['complexity_metrics'].definition_complexity
                ),
                difficulty_level=self.complexity_analyzer.get_difficulty_level_from_metrics(word_data_internal['complexity_metrics']),
                processing_metadata=schemas.ProcessingMetadataSchema(**word_data_internal['processing_metadata'])
            )
            
            self.logger.info(f"Resposta endpoint completa para '{normalized_word_text}'.")
            return response
            
        except HTTPException as he:
            self.logger.error(f"HTTPException durante o processamento de '{original_word_text}' (endpoint): {he.detail}", exc_info=True)
            raise he
        except Exception as e:
            self.logger.critical(f"Erro crítico não tratado no endpoint '{original_word_text}': {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Erro interno no servidor ao processar a palavra '{original_word_text}'. Contate o suporte.")

    async def _get_word_info_data_internal(self, normalized_word_text: str) -> Dict[str, Any]:
        """
        Obtém dados da palavra (definição, imagem URL, áudio filename, complexidade) para uso interno.
        Não constrói URLs completas nem usa Request.
        """
        self.logger.info(f"Iniciando processamento interno para: '{normalized_word_text}'")

        definition_task = self._get_definition_safe(normalized_word_text)
        image_task = self._get_image_safe(normalized_word_text)
        audio_base_path_str = await asyncio.to_thread(self._get_audio_base_path) # síncrono, em thread

        results = await asyncio.gather(
            definition_task,
            image_task,
            return_exceptions=True
        )
        
        definition_res = results[0]
        image_url_res = results[1]
        
        definition = "" 
        if isinstance(definition_res, Exception):
            self.logger.error(f"Erro (interno) ao obter definição para '{normalized_word_text}': {definition_res}", exc_info=isinstance(definition_res, Exception))
        elif definition_res:
            definition = definition_res

        image_url = None
        if isinstance(image_url_res, Exception):
             self.logger.error(f"Erro (interno) ao obter imagem para '{normalized_word_text}': {image_url_res}", exc_info=isinstance(image_url_res, Exception))
        elif image_url_res:
             image_url = image_url_res

        audio_filename = None
        if audio_base_path_str: # Prossiga com áudio apenas se o path base foi obtido
            try:
                # Geração de áudio é assíncrona e usa o path base, retorna apenas o nome do arquivo
                audio_filename = await self._generate_audio_safe(normalized_word_text, audio_base_path_str)
                if audio_filename:
                     self.logger.info(f"Áudio filename gerado para '{normalized_word_text}' (interno): {audio_filename}")

            except Exception as e:
                self.logger.error(f"Erro (interno) ao gerar áudio para '{normalized_word_text}': {e}", exc_info=True)

        self.logger.debug(f"Analisando complexidade (interno) para '{normalized_word_text}' com definição: '{definition[:50]}...'")
        complexity_analysis_metrics = self._analyze_complexity_cached(normalized_word_text, definition)

        current_time = asyncio.get_event_loop().time() if asyncio.get_event_loop().is_running() else 0.0
        processing_metadata_dict = {
            'analysis_timestamp': current_time,
            'definition_available': bool(definition and definition != "Definição não disponível."),
            'image_available': bool(image_url),
            'audio_available': bool(audio_filename), # Verifica se o filename foi gerado
            'cache_hit': self._last_cache_hit, 
            'complexity_method': 'neuropsychological_inference'
        }

        # Retorna um dicionário com os dados relevantes
        return {
            'text': normalized_word_text,
            'definition': definition if definition else "Definição não disponível.",
            'image_url': image_url, # Retorna a URL da imagem, se disponível (pode ser útil internamente)
            'audio_filename': audio_filename, # Retorna apenas o nome do arquivo de áudio
            'complexity_metrics': complexity_analysis_metrics,
            'processing_metadata': processing_metadata_dict
        }

    def _get_audio_base_path(self) -> str:
        audio_dir = os.path.join(self.static_files_dir, "audio")
        if not os.path.exists(audio_dir):
            try:
                os.makedirs(audio_dir, exist_ok=True)
                self.logger.info(f"Diretório de áudio criado ou já existente: {audio_dir}")
            except OSError as e:
                self.logger.error(f"Falha ao criar diretório de áudio {audio_dir}: {e}", exc_info=True)
                raise
        return audio_dir

    def _validate_word(self, word: str) -> bool:
        return bool(word and word.isalpha() and 2 <= len(word) <= 30)
    
    async def _get_definition_safe(self, word: str) -> str:
        try:
            result = await self.dictionary_api.get_word_info(word) 
            return result.get('definition', '') if result else ''.strip()
        except Exception as e:
            self.logger.warning(f"Falha na API do dicionário para '{word}'. Erro: {e}", exc_info=True)
            return ""
    
    async def _get_image_safe(self, word: str) -> Optional[str]:
        try:
            return await self.image_api.get_image_for_word(word)
        except Exception as e:
            self.logger.warning(f"Falha na API de imagens para '{word}'. Erro: {e}", exc_info=True)
            return None
    
    async def _generate_audio_safe(self, word: str, audio_base_path: str) -> Optional[str]:
        """Gera o áudio e retorna apenas o nome do arquivo."""
        try:
            # tts_service.generate_audio_from_text deve ser async e retornar o nome do arquivo
            filename = await self.tts_service.generate_audio_from_text(word, audio_base_path)
            return filename
        except Exception as e:
            self.logger.warning(f"Falha no TTS para '{word}'. Erro: {e}", exc_info=True)
            return None

    def _analyze_complexity_cached(self, word: str, definition: str) -> ComplexityMetricsDataclass:
        definition_key_part = definition if definition else "<no_definition>"
        cache_key = f"{word}:{hash(definition_key_part)}"
        
        cached_metrics = self.complexity_cache.get(cache_key)
        if cached_metrics:
            self.logger.debug(f"Cache HIT para complexidade de '{word}'")
            self._last_cache_hit = True
            return cached_metrics
        
        self.logger.debug(f"Cache MISS para complexidade de '{word}'. Analisando...")
        self._last_cache_hit = False
        metrics = self.complexity_analyzer.infer_word_complexity_metrics(word, definition)
        self.complexity_cache[cache_key] = metrics
        
        if len(self.complexity_cache) > 1000:
            try:
                oldest_key = next(iter(self.complexity_cache))
                del self.complexity_cache[oldest_key]
                self.logger.info(f"Cache de complexidade atingiu o limite. Chave mais antiga removida: {oldest_key}")
            except StopIteration:
                pass
        return metrics

# Router FastAPI
router = APIRouter(
    prefix="/api/v1", # Adicionando um prefixo para este router
    tags=["Word Information"]      # Agrupando endpoints na documentação Swagger/OpenAPI
)

# Instância global do serviço neste módulo, será configurada a partir de main.py
# Esta abordagem com uma instância global pode ter implicações em testes e concorrência
# se o estado (como current_request_base_url) não for gerenciado cuidadosamente.
word_service_instance_local: Optional[WordInfoService] = None

# Função para configurar a instância do serviço a partir de main.py
def configure_word_info_service(instance: WordInfoService):
    global word_service_instance_local
    word_service_instance_local = instance
    logging.info("Instância de WordInfoService configurada no router word_info_endpoint.")

@router.get("/word_info/{word_text}", response_model=schemas.WordInfoResponse)
async def get_word_info_endpoint_route(
    word_text: str, 
    request: Request, 
    background_tasks: BackgroundTasks
):
    if not word_service_instance_local:
        logging.critical("WordInfoService não inicializado antes da chamada do endpoint.")
        raise HTTPException(status_code=503, detail="Serviço de informações de palavras não inicializado.")
    
    # Atualizar o serviço com informações da request atual
    word_service_instance_local.current_request_base_url = str(request.base_url)
    word_service_instance_local.current_app_url_path_for = request.app.url_path_for

    result = await word_service_instance_local.get_word_info(word_text)
    
    background_tasks.add_task(
        log_analytics_word_request, 
        word_text,
        result.inferred_complexity_score,
        result.difficulty_level,
        bool(result.definition and result.definition != "Definição não disponível."),
        bool(result.image_url),
        bool(result.audio_url)
    )
    return result

async def log_analytics_word_request(word: str, complexity_score: float, level: str, def_ok: bool, img_ok: bool, aud_ok: bool):
    logging.info(f"ANALYTICS: Palavra='{word}', Score={complexity_score:.2f}, Nível='{level}', DefOK={def_ok}, ImgOK={img_ok}, AudOK={aud_ok}")

@router.get("/health", tags=["Word Information", "Health"])
async def word_info_health_check():
    return {"status": "WordInfoService router is operational"} 