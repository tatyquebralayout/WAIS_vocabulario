import logging
import os
from fastapi import FastAPI

# Importações de serviços como classes
from .services.dictionary_api import DictionaryAPI
from .services.image_api import ImageAPI
from .services.tts_service import TTSService

# Importações do endpoint de informações da palavra
from .word_info_endpoint import router as word_info_router
from .word_info_endpoint import WordInfoService, configure_word_info_service

# Definição do diretório de arquivos estáticos para ser usado pelo WordInfoService
# e potencialmente por main.py para montar os arquivos estáticos.
# __file__ é backend/app/app_config.py
# queremos backend/static
STATIC_FILES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "static"))

def create_app_instance() -> FastAPI:
    """
    Cria e configura a instância da aplicação FastAPI.
    Isso inclui a configuração de logging, inicialização de serviços,
    configuração do WordInfoService e inclusão de seu router.
    """
    app = FastAPI(
        title="Programa Educacional Inclusivo (Config Centralizada)",
        description="API para oferecer exercícios de vocabulário com acessibilidade.",
        version="1.1.0",
    )

    # Configuração básica de logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    logger.info("Iniciando a configuração da aplicação FastAPI a partir de app_config.py...")

    # Garantir que o diretório de arquivos estáticos e o subdiretório de áudio existam
    if not os.path.exists(STATIC_FILES_DIR):
        os.makedirs(STATIC_FILES_DIR)
        logger.info(f"Diretório estático criado: {STATIC_FILES_DIR}")
    
    audio_dir = os.path.join(STATIC_FILES_DIR, "audio")
    if not os.path.exists(audio_dir):
        os.makedirs(audio_dir)
        logger.info(f"Diretório de áudio criado: {audio_dir}")

    # Inicializar instâncias dos serviços de API
    dictionary_service_instance = DictionaryAPI()
    image_service_instance = ImageAPI()
    tts_service_instance = TTSService() # TTSService é uma classe agora

    # Inicializar o WordInfoService
    word_info_service_instance = WordInfoService(
        dictionary_api_service=dictionary_service_instance,
        image_api_service=image_service_instance,
        tts_api_service=tts_service_instance,
        static_files_dir=STATIC_FILES_DIR # Passa o diretório estático configurado
    )

    # Configurar o router de informações de palavras com a instância do serviço
    configure_word_info_service(word_info_service_instance)
    logger.info("WordInfoService configurado e injetado no word_info_router.")

    # Incluir o router de informações de palavras na aplicação
    # O prefixo /api/v1 já está definido dentro do word_info_router
    app.include_router(word_info_router)

    logger.info("Configuração da aplicação FastAPI (a partir de app_config.py) concluída.")
    return app

# Nota: Este arquivo define a fábrica create_app_instance.
# O arquivo main.py importará esta função para obter a instância da app
# e então adicionará outros middlewares, montará arquivos estáticos (usando STATIC_FILES_DIR daqui),
# configurará templates e incluirá outros routers (auth, users, progress, etc.). 