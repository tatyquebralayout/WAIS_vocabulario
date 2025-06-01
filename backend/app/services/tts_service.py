from gtts import gTTS
import os
import asyncio # Para rodar gTTS em uma thread separada
import logging
import re # Para sanitizar nomes de arquivos

logger = logging.getLogger(__name__)

# Não precisamos mais de BACKEND_ROOT_DIR ou AUDIO_DIR_FULL_PATH definidos globalmente aqui,
# já que o path base para salvar será passado para a função.

async def _generate_audio_from_text_func(text: str, audio_save_base_path: str, lang: str = 'pt') -> str | None:
    """
    Gera um áudio a partir do texto fornecido e o salva em um arquivo no diretório especificado.
    Retorna o nome do arquivo gerado (ex: palavra.mp3) ou None em caso de erro.
    Esta função agora é assíncrona e executa a parte bloqueante (gTTS) em uma thread.

    Args:
        text (str): O texto a ser convertido em áudio.
        audio_save_base_path (str): O diretório base para salvar o áudio.
        lang (str, optional): Idioma do áudio. Default é 'pt' (Português).

    Returns:
        str | None: O nome do arquivo gerado ou None em caso de erro.
    """
    if not text or not audio_save_base_path:
        logger.warning("Texto ou caminho base para salvar áudio não fornecido.")
        return None

    try:
        # Cria um nome de arquivo seguro removendo caracteres não alfanuméricos e substituindo espaços
        # Mantém acentos e cedilha se desejado, ou remove tudo que não for ASCII alfanumérico.
        # Versão mais restritiva para nomes de arquivo URL-friendly:
        safe_filename_base = re.sub(r'[^a-z0-9_.]', '', text.lower().replace(" ", "_"))
        if not safe_filename_base: # Se o texto for só caracteres especiais
            safe_filename_base = "audio" # Fallback
        safe_filename = f"{safe_filename_base[:50]}.mp3" # Limita o comprimento e adiciona extensão
        
        audio_full_save_path = os.path.join(audio_save_base_path, safe_filename)
        
        # Verificar se o diretório de destino existe, se não, tentar criar
        # Isso já é feito no WordInfoService, mas uma verificação dupla não faz mal
        if not os.path.exists(audio_save_base_path):
            try:
                os.makedirs(audio_save_base_path, exist_ok=True)
                logger.info(f"Diretório de áudio criado em tts_service: {audio_save_base_path}")
            except OSError as e:
                logger.error(f"Falha ao criar diretório de áudio {audio_save_base_path} em tts_service: {e}")
                return None # Não pode salvar se o diretório não puder ser criado

        # A geração e salvamento do áudio são operações bloqueantes
        # Vamos executá-las em uma thread separada para não bloquear o event loop do asyncio
        async def _blocking_tts_save():
            if not os.path.exists(audio_full_save_path):
                tts = gTTS(text=text, lang=lang, slow=False)
                tts.save(audio_full_save_path)
                logger.info(f"Áudio salvo em: {audio_full_save_path}")
                return True # Indica que o arquivo foi gerado
            else:
                logger.info(f"Áudio já existe (não sobrescrito): {audio_full_save_path}")
                return False # Indica que o arquivo já existia
        
        await asyncio.to_thread(_blocking_tts_save)
        
        # Retorna apenas o nome do arquivo para que o chamador construa a URL
        return safe_filename

    except Exception as e:
        logger.error(f"Erro ao gerar áudio para '{text}': {e}", exc_info=True)
        return None

class TTSService:
    async def generate_audio_from_text(self, text: str, audio_save_base_path: str, lang: str = 'pt') -> str | None:
        return await _generate_audio_from_text_func(text, audio_save_base_path, lang)

# Exemplo de uso (para teste local)
# async def main():
#     # Simular o path que seria passado pelo WordInfoService
#     # Palavras_project/backend/static/audio
#     test_audio_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "static", "audio"))
#     os.makedirs(test_audio_dir, exist_ok=True)
#     print(f"Testando com diretório de áudio: {test_audio_dir}")
#     
#     filename1 = await generate_audio_from_text("Olá mundo do TTS assíncrono", test_audio_dir)
#     if filename1:
#         print(f"Nome do arquivo de áudio 1: {filename1}")
#     
#     filename2 = await generate_audio_from_text("Café & Cachaça na Città!", test_audio_dir)
#     if filename2:
#         print(f"Nome do arquivo de áudio 2: {filename2}")
#
# if __name__ == "__main__":
#     logging.basicConfig(level=logging.INFO)
#     asyncio.run(main()) 