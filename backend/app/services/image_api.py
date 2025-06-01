# backend/app/services/image_api.py
import os
import httpx
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

# Carrega variáveis do .env localizado em Palavras_project/backend/.env
# __file__ é Palavras_project/backend/app/services/image_api.py
# Queremos Palavras_project/backend/.env
dotenv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))
load_dotenv(dotenv_path=dotenv_path)

PIXABAY_API_KEY = os.getenv("PIXABAY_API_KEY")
# Para depuração, vamos verificar se a chave foi carregada
if not PIXABAY_API_KEY:
    logger.error("CRÍTICO: Chave da API do Pixabay (PIXABAY_API_KEY) não está configurada.")
else:
    logger.info("Chave PIXABAY_API_KEY carregada.")

PIXABAY_API_URL = "https://pixabay.com/api/"

async def _get_image_for_word_func(word: str, lang: str = "pt", image_type: str = "photo", per_page: int = 3) -> str | None:
    """
    Busca uma imagem ilustrativa para a palavra no Pixabay de forma assíncrona.

    Args:
        word (str): A palavra para buscar.
        lang (str, optional): Código do idioma. Default é "pt".
        image_type (str, optional): Tipo de imagem ('photo', 'illustration'). Default é "photo".
        per_page (int, optional): Quantidade de imagens a solicitar (para ter uma pequena margem). Default é 3.

    Returns:
        str | None: A URL da imagem (webformatURL) ou None se não encontrada/erro.
    """
    if not PIXABAY_API_KEY:
        logger.error("API do Pixabay não pode ser usada: chave não configurada.")
        return None
    if not word:
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
        async with httpx.AsyncClient() as client:
            response = await client.get(PIXABAY_API_URL, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data.get('hits') and len(data['hits']) > 0:
                image_url = data['hits'][0].get('webformatURL')
                if image_url:
                    logger.info(f"Imagem encontrada para '{word}': {image_url}")
                    return image_url
                else:
                    logger.warning(f"Campo 'webformatURL' não encontrado no hit para '{word}': {data['hits'][0]}")
                    return None
            else:
                logger.info(f"Nenhuma imagem encontrada para '{word}' no Pixabay com filtros: lang={lang}, type={image_type}")
                return None
            
    except httpx.HTTPStatusError as e_http:
        logger.error(f"Erro HTTP ao buscar imagem para '{word}': {e_http.response.status_code} - {e_http.response.text}")
        return None
    except httpx.RequestError as e_req:
        logger.error(f"Erro de requisição à API do Pixabay para '{word}': {e_req}")
        return None
    except Exception as e_gen: # Captura outras exceções como JSONDecodeError se a resposta não for JSON válido
        logger.error(f"Erro inesperado ao buscar imagem no Pixabay para '{word}': {e_gen}", exc_info=True)
        return None

class ImageAPI:
    async def get_image_for_word(self, word: str, lang: str = "pt", image_type: str = "photo", per_page: int = 3) -> str | None:
        return await _get_image_for_word_func(word, lang, image_type, per_page)

# Exemplo de uso assíncrono
# import asyncio
# async def main():
#     termo_busca = "gato"
#     url_imagem = await get_image_for_word(termo_busca)
#     if url_imagem:
#         print(f"Imagem para '{termo_busca}': {url_imagem}")
#     else:
#         print(f"Não foi possível encontrar imagem para '{termo_busca}'.")
# if __name__ == "__main__":
#     logging.basicConfig(level=logging.INFO) # Configurar logging para ver os logs do serviço
#     asyncio.run(main()) 