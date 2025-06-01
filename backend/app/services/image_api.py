# backend/app/services/image_api.py
import os
import requests
from dotenv import load_dotenv

# Carrega variáveis do .env localizado em Palavras_project/backend/.env
# __file__ é Palavras_project/backend/app/services/image_api.py
# Queremos Palavras_project/backend/.env
dotenv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))
load_dotenv(dotenv_path=dotenv_path)
print(f"Tentando carregar .env de: {dotenv_path}") # Para depuração

PIXABAY_API_KEY = os.getenv("PIXABAY_API_KEY")
# Para depuração, vamos verificar se a chave foi carregada
if PIXABAY_API_KEY:
    print("Chave PIXABAY_API_KEY carregada com sucesso.")
else:
    print("ERRO: Chave PIXABAY_API_KEY não encontrada após carregar o .env.")

PIXABAY_API_URL = "https://pixabay.com/api/"

def get_image_for_word(word: str, lang: str = "pt", image_type: str = "photo", per_page: int = 3) -> str | None:
    """
    Busca uma imagem ilustrativa para a palavra no Pixabay.

    Args:
        word (str): A palavra para buscar.
        lang (str, optional): Código do idioma. Default é "pt".
        image_type (str, optional): Tipo de imagem ('photo', 'illustration'). Default é "photo".
        per_page (int, optional): Quantidade de imagens a solicitar (para ter uma pequena margem). Default é 3.

    Returns:
        str | None: A URL da imagem (webformatURL) ou None se não encontrada/erro.
    """
    if not PIXABAY_API_KEY:
        print("ERRO: Chave da API do Pixabay (PIXABAY_API_KEY) não está configurada no arquivo .env.")
        return None

    params = {
        'key': PIXABAY_API_KEY,
        'q': word,
        'lang': lang,
        'image_type': image_type,
        'safesearch': 'true',    # Essencial para ambiente educacional
        'order': 'popular',      # Traz as mais populares primeiro
        'per_page': per_page
    }

    try:
        response = requests.get(PIXABAY_API_URL, params=params)
        response.raise_for_status()  # Levanta um erro HTTP para status ruins (4xx ou 5xx)
        
        data = response.json()
        
        if data['hits'] and len(data['hits']) > 0:
            # Retorna a URL da imagem de tamanho médio da primeira imagem encontrada
            # 'webformatURL' é uma boa escolha para exibição geral.
            # Você poderia também pegar 'largeImageURL' se precisar de maior resolução.
            return data['hits'][0]['webformatURL']
        else:
            print(f"Nenhuma imagem encontrada para '{word}' no Pixabay com os filtros aplicados.")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"Erro na requisição à API do Pixabay: {e}")
        return None
    except KeyError as e:
        print(f"Erro ao processar a resposta JSON do Pixabay (campo faltando: {e}). Resposta: {response.text}")
        return None
    except Exception as e:
        print(f"Ocorreu um erro inesperado ao buscar imagem no Pixabay: {e}")
        return None

# Exemplo de como usar (você chamaria isso de outro lugar no seu backend):
if __name__ == "__main__":
    # Crie um arquivo .env na raiz do PROJETO (Palavras_project/.env) com:
    # PIXABAY_API_KEY=SUA_CHAVE_REAL_AQUI
    
    termo_busca = "elefante"
    url_imagem = get_image_for_word(termo_busca)
    
    if url_imagem:
        print(f"Imagem para '{termo_busca}': {url_imagem}")
    else:
        print(f"Não foi possível encontrar imagem para '{termo_busca}'.")

    termo_busca_inexistente = "xjqkbrz"
    url_imagem_inexistente = get_image_for_word(termo_busca_inexistente)
    if url_imagem_inexistente:
        print(f"Imagem para '{termo_busca_inexistente}': {url_imagem_inexistente}")
    else:
        print(f"Não foi possível encontrar imagem para '{termo_busca_inexistente}'.") 