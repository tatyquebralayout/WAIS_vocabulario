# backend/app/services/dictionary_api.py
import httpx
import xml.etree.ElementTree as ET
import logging

logger = logging.getLogger(__name__)

# A API pode retornar uma lista ou um único objeto para palavras muito específicas (ex: plurais)
API_URL_BASE = "https://api.dicionario-aberto.net"

async def _get_word_info_func(word: str) -> dict | None:
    """Busca a definição de uma palavra usando a API dicionario-aberto.net de forma assíncrona."""
    if not word:
        return None
    
    try:
        async with httpx.AsyncClient() as client:
            # Tenta buscar a palavra exata primeiro
            response = await client.get(f"{API_URL_BASE}/word/{word}")
            response.raise_for_status() # Levanta exceção para erros HTTP 4xx/5xx
            data = response.json()
            
            # O primeiro resultado da lista é geralmente o mais relevante
            if data and isinstance(data, list) and data[0].get('xml'):
                xml_string = data[0]["xml"]
                try:
                    root = ET.fromstring(xml_string)
                    # Encontrar a primeira definição dentro de <sense><def>
                    sense_element = root.find('.//sense/def')
                    if sense_element is not None and sense_element.text:
                        definition = sense_element.text.strip()
                        logger.info(f"Definição encontrada para '{word}' via API direta: {definition[:60]}...")
                        return {"word": word, "definition": definition}
                except ET.ParseError as e_xml:
                    logger.warning(f"Erro ao parsear XML da API para '{word}': {e_xml}. XML: {xml_string[:200]}")
                    # Fallback para extração manual se o XML for malformado mas contiver a tag
                    if "<def>" in xml_string:
                        try:
                            definition = xml_string.split('<def>')[1].split('</def>')[0].strip()
                            if definition:
                                logger.info(f"Definição encontrada para '{word}' via fallback de parse de string: {definition[:60]}...")
                                return {"word": word, "definition": definition}
                        except IndexError:
                            pass # Não foi possível extrair com split

            # Se não encontrou na busca direta ou não parseou, tenta /near/{word} (palavras próximas)
            # Isso pode ajudar com flexões verbais ou plurais que a API principal não retorna bem
            logger.info(f"Definição não encontrada diretamente para '{word}'. Tentando /near/{word}")
            response_near = await client.get(f"{API_URL_BASE}/near/{word}")
            response_near.raise_for_status()
            data_near = response_near.json()

            if data_near and isinstance(data_near, list):
                # Tentar encontrar a palavra original na lista de próximas
                for entry in data_near:
                    if isinstance(entry, str) and entry.lower() == word.lower(): # API /near pode retornar lista de strings
                        # Se encontrou a string exata, tentar buscar a definição dela novamente com /word/
                        # Isso evita um loop infinito se /word/ já foi tentado e falhou por outra razão
                        # Mas pode ser útil se a API /near confirma a existência da palavra
                        # Para evitar complexidade, simplesmente não faremos nada aqui se for só a string
                        # e dependeremos da próxima iteração que busca XML.
                        pass
                    elif isinstance(entry, dict) and entry.get('word', '').lower() == word.lower() and entry.get('xml'):
                        xml_string_near = entry["xml"]
                        try:
                            root_near = ET.fromstring(xml_string_near)
                            sense_element_near = root_near.find('.//sense/def')
                            if sense_element_near is not None and sense_element_near.text:
                                definition_near = sense_element_near.text.strip()
                                logger.info(f"Definição encontrada para '{word}' via API /near: {definition_near[:60]}...")
                                return {"word": word, "definition": definition_near}
                        except ET.ParseError as e_xml_near:
                            logger.warning(f"Erro ao parsear XML da API /near para '{word}': {e_xml_near}. XML: {xml_string_near[:200]}")
                            if "<def>" in xml_string_near:
                                try:
                                    definition_near = xml_string_near.split('<def>')[1].split('</def>')[0].strip()
                                    if definition_near:
                                        logger.info(f"Definição encontrada para '{word}' (via /near) por fallback de parse de string: {definition_near[:60]}...")
                                        return {"word": word, "definition": definition_near}
                                except IndexError:
                                    pass # Não conseguiu com split
            else:
                logger.warning(f"Nenhuma definição utilizável encontrada para '{word}' na API dicionario-aberto.net após todas as tentativas.")
                return None # Retorna None se nenhuma definição foi encontrada

    except httpx.HTTPStatusError as e_http:
        logger.error(f"Erro HTTP ao buscar definição para '{word}': {e_http.response.status_code} - {e_http.response.text}")
        return None
    except httpx.RequestError as e_req:
        logger.error(f"Erro de requisição ao buscar definição para '{word}': {e_req}")
        return None
    except Exception as e_gen:
        logger.error(f"Erro inesperado ao buscar definição para '{word}': {e_gen}", exc_info=True)
        return None

class DictionaryAPI:
    async def get_word_info(self, word: str) -> dict | None:
        return await _get_word_info_func(word)

# Exemplo de uso (para teste local)
# async def main():
#     palavras = ["casa", "felicidade", "correr", "correndo", "inconstitucionalissimamente", "xyzabc"]
#     for p in palavras:
#         info = await get_word_info(p)
#         if info and info.get("definition"):
#             print(f"Palavra: {info['word']}, Definição: {info['definition']}")
#         else:
#             print(f"Não foi possível encontrar definição para: {p}")

# if __name__ == "__main__":
#     logging.basicConfig(level=logging.INFO)
#     asyncio.run(main())