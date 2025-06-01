# backend/app/services/dictionary_api.py
import requests

API_URL = "https://api.dicionario-aberto.net/word"

def get_word_info(word: str):
    try:
        response = requests.get(f"{API_URL}/{word}")
        response.raise_for_status() # Lança erro para status 4xx/5xx
        data = response.json()
        # A API pode retornar uma lista, pegamos o primeiro resultado
        if data and isinstance(data, list):
            xml_definition = data[0].get('xml')
            # Simplificando a extração da definição (pode ser melhorada)
            if xml_definition:
                definition = xml_definition.split('<sense>')[1].split('</sense>')[0]
                # Limpa tags HTML simples
                definition = definition.replace('<def>', '').replace('</def>', '').strip()
                return {"word": word, "definition": definition}
        return None
    except requests.exceptions.RequestException:
        return None 