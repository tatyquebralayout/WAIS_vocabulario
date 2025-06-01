# WAIS Vocabulário: Expansão e Prática de Vocabulário

**WAIS Vocabulário** é uma aplicação web educacional inspirada nos subtestes de vocabulário frequentemente encontrados em avaliações de inteligência, como a Escala Wechsler de Inteligência para Adultos (WAIS). O projeto visa transcender a simples avaliação, oferecendo uma plataforma interativa e adaptativa onde os usuários podem ativamente **praticar, testar e expandir seu vocabulário**.

A intenção é criar uma ferramenta que não apenas auxilie no aprendizado de novas palavras, mas que também reforce o conhecimento existente através de exercícios variados e feedback, promovendo uma compreensão mais profunda e um uso mais eficaz da linguagem.

## Sobre o Projeto (Visão Geral Técnica)

Este projeto é uma aplicação web educacional desenvolvida em Python com FastAPI, projetada para auxiliar no aprendizado de vocabulário de forma inclusiva e adaptativa.

## Funcionalidades Principais

*   **Busca de Palavras Detalhada:** Obtém definição (via API Dicionario Aberto), uma imagem ilustrativa (via API Pixabay) e a pronúncia em áudio (gerada com gTTS) para palavras pesquisadas.
*   **Banco de Dados de Usuários e Palavras:** Armazena informações de usuários, palavras (incluindo seu nível de dificuldade) e o progresso de cada usuário com as palavras.
*   **API Backend Robusta:** Construída com FastAPI, utilizando Pydantic para validação de dados e SQLAlchemy para interações com um banco de dados SQLite.
*   **Endpoints CRUD:** Operações completas para criar, ler, atualizar e deletar usuários, palavras e o progresso dos usuários.
*   **Modelo de Aprendizado de Máquina (TGL-ML - Esboço):** Inclui uma estrutura para um modelo de classificação (usando scikit-learn e Logistic Regression) para prever o nível de dificuldade adequado para o próximo exercício do usuário, com base em seu desempenho (precisão, tempo médio, comprimento da palavra).
*   **Interface Simples:** Uma página HTML básica servida via Jinja2 que permite ao usuário buscar palavras e interagir com a API.
*   **Configuração de Ambiente:** Utiliza ambiente virtual Python e um arquivo `.env` para gerenciamento de chaves de API.

## Estrutura do Projeto

```
Palavras_project/
│
├── backend/
│   ├── app/                    # Core da aplicação FastAPI
│   │   ├── __init__.py
│   │   ├── main.py             # Definição da app FastAPI e endpoints principais
│   │   ├── models.py           # Modelos SQLAlchemy (User, Word, UserProgress)
│   │   ├── schemas.py          # Schemas Pydantic para validação e serialização
│   │   ├── crud.py             # Funções CRUD para o banco de dados
│   │   ├── database.py         # Configuração do SQLAlchemy (engine, SessionLocal)
│   │   └── services/           # Lógica de negócios e integração com APIs externas
│   │       ├── __init__.py
│   │       ├── dictionary_api.py # Integração com API de dicionário
│   │       ├── image_api.py      # Integração com API de imagens (Pixabay)
│   │       ├── tts_service.py    # Serviço de Text-to-Speech (gTTS)
│   │       └── ml_model.py       # Lógica do modelo de Machine Learning (TGL-ML)
│   ├── static/                 # Arquivos estáticos servidos pelo backend
│   │   └── audio/              # Áudios gerados pelo tts_service
│   │   └── (css/, js/ etc. se adicionados)
│   ├── templates/              # Templates HTML (para Jinja2)
│   │   └── index.html          # Página principal da aplicação
│   ├── .env                    # Arquivo para variáveis de ambiente (ex: API keys) - NÃO VERSIONADO
│   ├── app_data.db             # Banco de dados SQLite - NÃO VERSIONADO
│   └── difficulty_model.pkl    # Modelo de ML treinado salvo - NÃO VERSIONADO
│
├── frontend/                   # Reservado para um frontend SPA (ex: React, Vue)
│   └── src/
│
├── venv/                       # Ambiente virtual Python - NÃO VERSIONADO
├── .gitignore                  # Especifica arquivos e pastas a serem ignorados pelo Git
├── README.md                   # Este arquivo
└── requirements.txt            # Dependências Python do projeto
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
    *   No Windows (PowerShell):
        ```powershell
        .\venv\Scripts\Activate.ps1
        ```
    *   No macOS/Linux:
        ```bash
        source venv/bin/activate
        ```

3.  **Instale as Dependências**
    Certifique-se de que o arquivo `requirements.txt` está atualizado e na raiz do projeto.
    ```bash
    pip install -r requirements.txt
    ```
    Se o `requirements.txt` estiver desatualizado, você pode gerá-lo com (após instalar as dependências individualmente listadas abaixo, se for a primeira vez):
    ```bash
    # pip install fastapi uvicorn sqlalchemy requests gTTS scikit-learn python-dotenv pandas joblib
    # pip freeze > requirements.txt
    ```
    As dependências principais incluem: `fastapi`, `uvicorn[standard]`, `sqlalchemy`, `requests`, `gTTS`, `scikit-learn`, `python-dotenv`, `pandas`, `joblib`.

4.  **Configure as Variáveis de Ambiente**
    *   Crie um arquivo chamado `.env` dentro da pasta `Palavras_project/backend/`.
    *   Adicione sua chave da API Pixabay a este arquivo:
        ```env
        PIXABAY_API_KEY=SUA_CHAVE_DA_API_PIXABAY_AQUI
        ```

## Como Executar a Aplicação

1.  **Ative o Ambiente Virtual** (se ainda não estiver ativo):
    *   Windows (PowerShell): `.\venv\Scripts\Activate.ps1`
    *   macOS/Linux: `source venv/bin/activate`

2.  **Navegue até a Pasta do Backend**:
    ```bash
    cd backend
    ```

3.  **Inicie o Servidor FastAPI**:
    ```bash
    uvicorn app.main:app --reload
    ```
    O servidor estará rodando em `http://127.0.0.1:8000`. O `--reload` faz com que o servidor reinicie automaticamente após alterações no código.

4.  **Acesse a Aplicação/API**:
    *   **Interface Web Principal**: Abra seu navegador e vá para `http://127.0.0.1:8000/app`
    *   **Documentação Interativa da API (Swagger UI)**: `http://127.0.0.1:8000/docs`
    *   **API Health Check (Raiz)**: `http://127.0.0.1:8000/`

## Endpoints da API Principais

*   `GET /app`: Serve a página HTML principal da aplicação.
*   `GET /word/{word_text}`: Retorna dados detalhados de uma palavra (definição, imagem, áudio).
*   `POST /users/`: Cria um novo usuário.
*   `GET /users/{user_id}`: Obtém informações de um usuário específico.
*   `POST /words/`: Cria uma nova palavra no banco de dados (incluindo `difficulty_level`).
*   `GET /words/text/{word_text}`: Obtém informações de uma palavra do banco de dados.
*   `POST /progress/users/{user_id}/words/{word_text}`: Registra ou atualiza o progresso de um usuário para uma palavra específica.
*   `GET /progress/users/{user_id}/words/{word_text}`: Obtém o progresso de um usuário para uma palavra.

## Modelo de Machine Learning (TGL-ML)

*   **Localização:** `backend/app/services/ml_model.py`
*   **Objetivo:** Prever o próximo nível de dificuldade para um usuário.
*   **Features Utilizadas (exemplo):** `accuracy` (precisão do usuário), `avg_time` (tempo médio de resposta), `word_length` (comprimento da palavra).
*   **Treinamento:** A função `train_model` pode ser chamada (atualmente via script de exemplo ou futuramente por um endpoint administrativo) para treinar o modelo com dados da tabela `UserProgress`. O modelo treinado é salvo em `backend/difficulty_model.pkl`.
*   **Predição:** A função `predict_difficulty` carrega o modelo salvo e prevê um nível de dificuldade (0: Fácil, 1: Médio, 2: Difícil) com base no desempenho recente do usuário.

## Próximos Passos e Melhorias Potenciais

*   Implementar um endpoint administrativo ou script para facilitar o retreinamento do modelo de ML.
*   Integrar a predição de dificuldade do `ml_model.py` na lógica de seleção de próximos exercícios.
*   Desenvolver a "Seção de Exercícios" no `index.html` ou em um frontend SPA.
*   Implementar autenticação e autorização de usuários.
*   Expandir o frontend para uma Single Page Application (SPA) mais rica (ex: usando a pasta `frontend/`).
*   Adicionar testes unitários e de integração.
*   Considerar o uso de Alembic para migrações de banco de dados caso o esquema evolua significativamente. 