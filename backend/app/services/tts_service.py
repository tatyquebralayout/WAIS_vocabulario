from gtts import gTTS
import os

# Define o diretório base do backend (Palavras_project/backend)
# __file__ é F:/aprendizado/Palavras_project/backend/app/services/tts_service.py
# Subimos três níveis para chegar em Palavras_project/backend
BACKEND_ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

# Define o caminho para a pasta de áudio DENTRO da pasta static do backend
# Resultado esperado: Palavras_project/backend/static/audio
AUDIO_DIR_FULL_PATH = os.path.join(BACKEND_ROOT_DIR, "static", "audio")

# Garante que o diretório de áudio exista ao carregar o módulo
os.makedirs(AUDIO_DIR_FULL_PATH, exist_ok=True)

def generate_audio_from_text(text: str, lang: str = 'pt') -> str | None:
    """
    Gera um áudio a partir do texto fornecido e o salva em um arquivo.
    O áudio é salvo em backend/static/audio/
    Retorna a URL relativa para o frontend (ex: /static/audio/filename.mp3)

    Args:
        text (str): O texto a ser convertido em áudio.
        lang (str, optional): Idioma do áudio. Default é 'pt' (Português).

    Returns:
        str | None: A URL relativa para o arquivo de áudio gerado ou None em caso de erro.
    """
    try:
        # Cria um nome de arquivo seguro removendo caracteres não alfanuméricos
        safe_filename = "".join(c if c.isalnum() else "_" for c in text.lower()) + ".mp3"
        
        # Caminho completo onde o arquivo de áudio será salvo
        audio_save_path = os.path.join(AUDIO_DIR_FULL_PATH, safe_filename)
        
        # Verifica se o arquivo já existe para não gerar novamente sem necessidade
        if not os.path.exists(audio_save_path):
            tts = gTTS(text=text, lang=lang, slow=False)
            tts.save(audio_save_path)
            print(f"Áudio salvo em: {audio_save_path}")
        else:
            print(f"Áudio já existe em: {audio_save_path}")
        
        # Retorna a URL relativa para o frontend
        # O servidor FastAPI está montado em /static para servir a pasta backend/static
        # Portanto, a URL deve ser /static/audio/nome_do_arquivo.mp3
        url_path = f"/static/audio/{safe_filename}"
        return url_path

    except Exception as e:
        print(f"Erro ao gerar áudio para '{text}': {e}")
        return None

# Exemplo de uso (será chamado de outros lugares, como o main.py):
if __name__ == '__main__':
    print(f"Diretório raiz do backend configurado como: {BACKEND_ROOT_DIR}")
    print(f"Diretório de áudio configurado como: {AUDIO_DIR_FULL_PATH}")

    # Testando a geração de áudio
    url1 = generate_audio_from_text("Olá mundo do teste")
    if url1:
        print(f"URL do áudio 1: {url1}")
        # Para verificar, você encontraria o arquivo em:
        # F:\aprendizado\Palavras_project\backend\static\audio\olá_mundo_do_teste.mp3

    url2 = generate_audio_from_text("Testando caracteres especiais: Olá? Mundo!")
    if url2:
        print(f"URL do áudio 2: {url2}")
        # Nome esperado do arquivo: testando_caracteres_especiais__olá__mundo_.mp3

    url3 = generate_audio_from_text("Olá mundo do teste") # Testando áudio já existente
    if url3:
        print(f"URL do áudio 3 (deve ser o mesmo): {url3}") 