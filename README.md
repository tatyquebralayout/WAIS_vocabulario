# WAIS Vocabulário: Expansão e Prática de Vocabulário

**WAIS Vocabulário** é uma aplicação web educacional inspirada nos subtestes de vocabulário frequentemente encontrados em avaliações de inteligência, como a Escala Wechsler de Inteligência para Adultos (WAIS). O projeto visa transcender a simples avaliação, oferecendo uma plataforma interativa e adaptativa onde os usuários podem ativamente **praticar, testar e expandir seu vocabulário**.

A intenção é criar uma ferramenta que não apenas auxilie no aprendizado de novas palavras, mas que também reforce o conhecimento existente através de exercícios variados e feedback, promovendo uma compreensão mais profunda e um uso mais eficaz da linguagem.

## Sobre o Projeto (Visão Geral Técnica)

Este projeto é uma aplicação web educacional desenvolvida em Python com FastAPI. Ele foi reestruturado para obter informações sobre palavras dinamicamente de APIs externas e inferir sua complexidade em tempo real, em vez de depender de um banco de dados local de palavras.

## Funcionalidades Principais

*   **Busca Detalhada e Análise de Palavras em Tempo Real:**
    *   Obtém definição (via API Dicionario Aberto), uma imagem ilustrativa (via API Pixabay) e a pronúncia em áudio (gerada com gTTS e servida estaticamente) para qualquer palavra pesquisada.
    *   **Análise de Complexidade Avançada:** Utiliza o `WordComplexityAnalyzer` para inferir a complexidade da palavra com base em múltiplas métricas psicolinguísticas (comprimento lexical, complexidade silábica, densidade morfológica, abstração semântica, frequência, familiaridade e complexidade da definição), fornecendo um score e um rótulo de dificuldade (ex: "fácil", "média", "difícil").
*   **API Backend Robusta com FastAPI:**
    *   Construída com FastAPI, utilizando Pydantic para validação de dados.
    *   SQLAlchemy para interações com um banco de dados SQLite (focado em usuários e progresso).
    *   Serviços de API externos (dicionário, imagem) integrados com chamadas HTTP assíncronas (`httpx`).
    *   Serviço de TTS (`gTTS`) adaptado para execução assíncrona em thread separada.
*   **Gerenciamento de Usuários e Progresso:**
    *   Endpoints CRUD para criar, ler, atualizar e deletar usuários.
    *   Rastreamento do progresso do usuário com palavras específicas (identificadas por `word_text`).
*   **Configuração Centralizada:**
    *   O arquivo `backend/app/app_config.py` gerencia a criação da instância FastAPI, inicialização de serviços e configuração de roteadores.
*   **Interface Simples (Exemplo):** Uma página HTML básica (`index.html`) servida via Jinja2 demonstra a funcionalidade de busca de palavras.
*   **Gerenciamento de Ambiente:** Utiliza ambiente virtual Python e um arquivo `.env` para chaves de API.

## Estrutura do Projeto

```
Palavras_project/
│
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py             # Ponto de entrada principal, monta a app de app_config
│   │   ├── app_config.py       # Criação e configuração da instância FastAPI e serviços
│   │   ├── models.py           # Modelos SQLAlchemy (User, UserProgress)
│   │   ├── schemas.py          # Schemas Pydantic
│   │   ├── crud.py             # Funções CRUD (principalmente para User e UserProgress)
│   │   ├── database.py         # Configuração do SQLAlchemy
│   │   ├── core/
│   │   │   └── security.py     # Hashing de senha, JWT
│   │   ├── services/
│   │   │   ├── dictionary_api.py # Integração assíncrona com API de dicionário
│   │   │   ├── image_api.py      # Integração assíncrona com API de imagens
│   │   │   ├── tts_service.py    # Serviço de Text-to-Speech (gTTS adaptado)
│   │   │   ├── word_complexity_analyzer.py # Analisador de complexidade de palavras
│   │   │   └── ml_model.py       # Lógica do modelo de ML (requer revisão/adaptação)
│   │   ├── routers/              # Módulos de roteamento (substituído/integrado)
│   │   │   └── word_info_endpoint.py # Endpoint para informações e complexidade de palavras
│   │   # ... (outros routers para auth, users, progress, admin, exercises)
│   ├── static/
│   │   ├── audio/              # Áudios gerados
│   │   ├── css/
│   │   └── js/
│   ├── templates/
│   │   ├── index.html
│   │   └── partials/
│   ├── .env                    # Variáveis de ambiente (NÃO VERSIONADO)
│   └── app_data.db             # Banco de dados SQLite (NÃO VERSIONADO)
│
├── frontend/                   # (Reservado para futuro frontend SPA)
│   └── src/
├── venv/                       # Ambiente virtual (NÃO VERSIONADO)
├── .gitignore
├── README.md                   # Este arquivo
└── requirements.txt            # Dependências Python
```

## Configuração do Ambiente

1.  **Clone o Repositório (se aplicável)**
    ```bash
    # git clone <url_do_repositorio>
    # cd Palavras_project
    ```

2.  **Crie e Ative o Ambiente Virtual Python**
    ```bash
    python -m venv venv
    ```
    *   No Windows (PowerShell): `.\venv\Scripts\Activate.ps1`
    *   No macOS/Linux: `source venv/bin/activate`

3.  **Instale as Dependências**
    ```bash
    pip install -r requirements.txt
    ```
    As dependências principais incluem: `fastapi`, `uvicorn[standard]`, `sqlalchemy`, `httpx`, `gTTS`, `python-dotenv`, `jinja2`, `python-multipart`, `passlib[bcrypt]`, `nltk`, `textstat`, `pydantic`.

4.  **Baixe os Recursos do NLTK**
    Após instalar as dependências, execute um script Python ou um interpretador Python e baixe os pacotes necessários do NLTK:
    ```python
    import nltk
    nltk.download('punkt')
    nltk.download('wordnet')
    nltk.download('averaged_perceptron_tagger')
    nltk.download('cmudict') # Usado pelo WordComplexityAnalyzer
    # nltk.download('floresta') # Exemplo de corpus em português, se necessário para expansões futuras
    # nltk.download('mac_morpho') # Exemplo de etiquetador morfológico em português
    ```

5.  **Configure as Variáveis de Ambiente**
    *   Crie um arquivo chamado `.env` dentro da pasta `Palavras_project/backend/`.
    *   Adicione suas chaves de API:
        ```env
        PIXABAY_API_KEY=SUA_CHAVE_DA_API_PIXABAY_AQUI
        # DICIONARIO_ABERTO_API_TOKEN=SEU_TOKEN_AQUI (se aplicável no futuro)
        ```

## Como Executar a Aplicação

1.  **Ative o Ambiente Virtual** (se ainda não estiver ativo).

2.  **A partir da Raiz do Projeto (`Palavras_project/`)**, inicie o servidor FastAPI:
    ```bash
    uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
    ```
    O servidor estará rodando em `http://127.0.0.1:8000` (ou no IP da sua máquina na rede local).

3.  **Acesse a Aplicação/API**:
    *   **Interface Web Principal (Exemplo)**: `http://127.0.0.1:8000/app`
    *   **Documentação Interativa da API (Swagger UI)**: `http://127.0.0.1:8000/docs`
    *   **Endpoint Principal de Informações da Palavra**: `GET http://127.0.0.1:8000/api/v1/word_info/{word_text}`

## Endpoints da API Principais (Prefixo `/api/v1`)

*   **Informações da Palavra:**
    *   `GET /word_info/{word_text}`: Retorna dados detalhados de uma palavra, incluindo definição, imagem, áudio, score de complexidade inferido e métricas detalhadas.
*   **Autenticação (`/auth`):**
    *   `POST /token`: Gera um token JWT para autenticação.
*   **Usuários (`/users`):**
    *   `POST /`: Cria um novo usuário.
    *   `GET /me`: Obtém informações do usuário autenticado.
    *   `GET /{user_id}`: Obtém informações de um usuário específico (requer permissões adequadas).
*   **Progresso do Usuário (`/progress`):**
    *   `POST /users/{user_id}/words/{word_text}`: Registra ou atualiza o progresso de um usuário para uma palavra.
    *   `GET /users/{user_id}/words/{word_text}`: Obtém o progresso de um usuário para uma palavra.
*   **Endpoints de Administração e Exercícios (Alguns podem estar desabilitados ou em refatoração):**
    *   Verifique a documentação da API (`/docs`) para a lista atual de endpoints de admin e exercícios. Muitos endpoints relacionados ao gerenciamento de um banco de dados de palavras foram removidos ou desativados.

## Análise de Complexidade de Palavras

O `WordComplexityAnalyzer` (localizado em `backend/app/services/word_complexity_analyzer.py`) é um componente chave que estima a dificuldade de uma palavra. Ele considera:
*   Comprimento da palavra.
*   Número de sílabas (usando `pyphen` e `cmudict` como fallback).
*   Densidade morfológica (análise de afixos, se implementado).
*   Abstração semântica (contagem de synsets no WordNet, como proxy).
*   Frequência da palavra (requer integração com corpus de frequência).
*   Idade de aquisição (requer dados externos).
*   Complexidade da definição (usando métricas de legibilidade como Flesch-Kincaid no texto da definição).

As métricas são combinadas para produzir um score de complexidade e um rótulo (ex: "fácil", "média", "difícil").

## Modelo de Machine Learning (TGL-ML)

*   **Localização:** `backend/app/services/ml_model.py`
*   **Estado Atual:** A funcionalidade original de prever o nível de dificuldade de uma *palavra específica* foi largamente substituída pelo `WordComplexityAnalyzer`.
*   **Potencial Futuro:** O modelo de ML pode ser adaptado para:
    *   Sugerir a *próxima palavra ou tipo de exercício* com base no histórico de progresso do usuário e na complexidade inferida das palavras.
    *   Analisar padrões de aprendizagem do usuário.
*   O treinamento e a predição (`train_model`, `predict_difficulty`) precisam ser reavaliados e possivelmente refatorados para se alinharem com a nova arquitetura focada na análise dinâmica de complexidade e no `UserProgress` baseado em `word_text`.

## Próximos Passos e Melhorias Potenciais

*   Reativar e refatorar os endpoints de geração de exercícios (múltipla escolha, ditado, arrastar e soltar) para utilizarem o `WordInfoService` e a análise de complexidade dinâmica.
*   Implementar uma lógica robusta de sugestão de próximos exercícios baseada no progresso do usuário e na complexidade das palavras.
*   Aperfeiçoar o `WordComplexityAnalyzer` com mais métricas e melhor calibração (ex: frequência de palavras de um corpus em português, dados de idade de aquisição).
*   Implementar um sistema de cache mais sofisticado para o `WordInfoService` (ex: Redis).
*   Expandir o frontend para uma Single Page Application (SPA) mais rica.
*   Adicionar testes unitários e de integração abrangentes.
*   Melhorar o tratamento de erros e logging.
*   Considerar o uso de Alembic para migrações de banco de dados, caso o esquema de `User` ou `UserProgress` evolua.
